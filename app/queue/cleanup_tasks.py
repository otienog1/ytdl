"""
Scheduled cleanup tasks for removing old files and database records.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from app.queue.celery_app import celery_app
from app.services.storage_service import storage_service
from app.utils.logger import logger
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

# Initialize database connection for Celery worker
_db_client = None
_db = None


async def _get_db():
    """Get database instance for Celery worker"""
    global _db_client, _db
    if _db is None:
        _db_client = AsyncIOMotorClient(settings.MONGODB_URI)
        try:
            _db = _db_client.get_database()
        except:
            _db = _db_client["ytdl_db"]
    return _db


@celery_app.task
def cleanup_old_downloads():
    """
    Scheduled task to cleanup old downloads and files from GCS.

    This task runs periodically (recommended: every 6 hours) to:
    1. Find downloads older than FILE_EXPIRY_HOURS
    2. Check if the file is still referenced by other downloads
    3. Delete file from GCS only if no other downloads reference it
    4. Mark download records as expired in database

    This prevents deleting files that are still being used by other users
    who downloaded the same video.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(_cleanup_old_downloads_async())
    except Exception as e:
        logger.error(f"Cleanup job failed: {str(e)}")
        raise


async def _cleanup_old_downloads_async():
    """Async cleanup using a cursor to prevent memory exhaustion"""
    try:
        logger.info("Starting memory-efficient cleanup job...")
        db = await _get_db()
        expiry_hours = settings.FILE_EXPIRY_HOURS
        cutoff_date = datetime.utcnow() - timedelta(hours=expiry_hours)

        # Find downloads older than cutoff
        # We use a cursor instead of to_list() to process one by one
        cursor = db.downloads.find({
            'createdAt': {'$lt': cutoff_date},
            'status': 'completed',
            'downloadUrl': {'$exists': True, '$ne': None}
        })

        files_deleted = 0
        records_updated = 0
        files_kept = 0

        async for download in cursor:
            video_id = download.get('videoInfo', {}).get('id')
            download_url = download.get('downloadUrl')
            
            if not video_id or not download_url:
                continue

            # Check if this video is referenced by other non-expired downloads
            # This handles the case where multiple users downloaded the same video
            recent_downloads = await db.downloads.count_documents({
                'videoInfo.id': video_id,
                'createdAt': {'$gte': cutoff_date},
                'status': 'completed',
                'downloadUrl': {'$exists': True, '$ne': None}
            })

            if recent_downloads > 0:
                # File is still being used by recent downloads, keep it
                logger.info(
                    f"Keeping file for video {video_id}: "
                    f"Referenced by {recent_downloads} recent downloads"
                )
                files_kept += 1

                # Mark this old download as expired but don't delete the file
                await db.downloads.update_one(
                    {'_id': download['_id']},
                    {
                        '$set': {
                            'expired': True,
                            'expiredAt': datetime.utcnow()
                        },
                        '$unset': {'downloadUrl': ''}  # Remove expired URL
                    }
                )
                records_updated += 1
            else:
                # No recent references, safe to delete the file
                try:
                    # Extract filename from URL
                    # URL format: https://storage.googleapis.com/bucket/filename.mp4?params...
                    file_name = _extract_filename_from_url(download_url)

                    if file_name:
                        # Get provider from download record (default to gcs for old records)
                        provider = download.get('storageProvider', 'gcs')

                        # Delete from cloud storage
                        await storage_service.delete_file(file_name, provider)
                        files_deleted += 1
                        logger.info(f"Deleted file: {file_name} from {provider} (video: {video_id})")

                    # Mark download as expired and remove URL
                    await db.downloads.update_one(
                        {'_id': download['_id']},
                        {
                            '$set': {
                                'expired': True,
                                'expiredAt': datetime.utcnow()
                            },
                            '$unset': {'downloadUrl': ''}
                        }
                    )
                    records_updated += 1

                except Exception as e:
                    logger.error(f"Error deleting file for video {video_id}: {e}")

        logger.info(
            f"Cleanup completed: {files_deleted} files deleted, "
            f"{files_kept} files kept (active references), "
            f"{records_updated} records updated"
        )

        return {'files_deleted': files_deleted, 'records_updated': records_updated}

    except Exception as e:
        logger.error(f"Cleanup job failed: {str(e)}")
        raise


def _extract_filename_from_url(url: str) -> Optional[str]:
    """
    Extract filename from GCS signed URL.

    Example:
    https://storage.googleapis.com/bucket/My%20Video.mp4?Expires=...
    Returns: My Video.mp4 (URL decoded)
    """
    try:
        from urllib.parse import urlparse, unquote

        # Parse URL
        parsed = urlparse(url)
        path = parsed.path

        # Path format: /bucket_name/filename.mp4
        # Split and get the filename (last part)
        parts = path.split('/')
        if len(parts) >= 2:
            filename = parts[-1]  # Last part is the filename
            return unquote(filename)  # URL decode

        return None
    except Exception as e:
        logger.error(f"Error extracting filename from URL: {e}")
        return None


@celery_app.task
def cleanup_failed_downloads():
    """
    Cleanup failed/stuck downloads that are older than 24 hours.

    This removes database clutter from failed download attempts.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(_cleanup_failed_downloads_async())
    except Exception as e:
        logger.error(f"Failed download cleanup job failed: {str(e)}")
        raise


async def _cleanup_failed_downloads_async():
    """Remove old failed/queued downloads from database"""
    try:
        logger.info("Starting failed downloads cleanup...")

        db = await _get_db()
        cutoff_date = datetime.utcnow() - timedelta(hours=24)

        # Delete failed and stuck queued downloads older than 24 hours
        result = await db.downloads.delete_many({
            'createdAt': {'$lt': cutoff_date},
            'status': {'$in': ['failed', 'queued']}
        })

        logger.info(f"Cleaned up {result.deleted_count} failed/stuck download records")

        return {'deleted_count': result.deleted_count}

    except Exception as e:
        logger.error(f"Failed download cleanup job failed: {str(e)}")
        raise
