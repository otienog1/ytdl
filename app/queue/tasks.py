import asyncio
from app.queue.celery_app import celery_app
from app.services.youtube_service import youtube_service
from app.services.storage_service import storage_service
from app.utils.validators import extract_video_id
from app.utils.logger import logger
from app.config.database import get_database, connect_to_mongo
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.websocket import manager

# Initialize database connection for Celery worker
_db_client = None
_db = None


@celery_app.task(bind=True, max_retries=3)
def process_download(self, url: str, job_id: str, cookies: dict | None = None):
    """Process video download task"""
    try:
        # Run async functions in sync context
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(_process_download_async(self, url, job_id, cookies))
    except Exception as e:
        logger.error(f"Download job failed: {job_id} - {str(e)}")
        # Update status to failed
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_update_status(job_id, 'failed', error=str(e)))
        raise


async def _process_download_async(task, url: str, job_id: str, cookies: dict | None = None):
    """Async download processing"""
    try:
        logger.info(f"Processing download job: {job_id}")

        # Update status to processing
        await _update_status(job_id, 'processing', progress=5)
        task.update_state(state='PROGRESS', meta={'progress': 5})

        # Extract video ID first
        video_id = extract_video_id(url)
        if not video_id:
            raise Exception("Invalid video URL")

        # Check if this video was already processed BEFORE fetching info
        # This avoids unnecessary YouTube API calls and downloads for duplicate videos
        db = await _get_db()
        existing_download = await db.downloads.find_one({
            'videoInfo.id': video_id,
            'status': 'completed',
            'downloadUrl': {'$exists': True, '$ne': None}
        })

        # Only fetch video info if we don't have it cached
        if not existing_download:
            logger.info(f"Fetching video info for new video: {video_id}")
            video_info = await youtube_service.get_video_info(url, cookies=cookies)

            await _update_status(
                job_id,
                'processing',
                progress=10
            )
            task.update_state(state='PROGRESS', meta={'progress': 10})
        else:
            # Use cached video info from existing download
            logger.info(f"Video {video_id} already exists - using cached info, skipping download")
            video_info_dict = existing_download.get('videoInfo')
            # Convert dict back to VideoInfo object
            from app.models.download import VideoInfo
            video_info = VideoInfo(**video_info_dict)

            await _update_status(
                job_id,
                'processing',
                progress=10
            )
            task.update_state(state='PROGRESS', meta={'progress': 10})

        if existing_download:

            # Progress: 30% - Extracting filename
            await _update_status(job_id, 'processing', progress=30)
            task.update_state(state='PROGRESS', meta={'progress': 30})

            # Extract filename from existing download URL
            old_url = existing_download.get('downloadUrl')
            file_name = _extract_filename_from_url(old_url)

            # Progress: 50% - Generating new signed URL
            await _update_status(job_id, 'processing', progress=50)
            task.update_state(state='PROGRESS', meta={'progress': 50})

            if file_name:
                # Get provider from existing download (default to gcs for old records)
                provider = existing_download.get('storageProvider', 'gcs')
                # Regenerate signed URL with proper Content-Disposition header
                # This ensures downloads work even for old files
                download_url = await storage_service.regenerate_signed_url(file_name, provider)
                logger.info(f"Regenerated signed URL for deduplicated video: {file_name} from {provider}")
            else:
                # Fallback to old URL if extraction fails
                download_url = old_url
                logger.warning(f"Could not extract filename from URL, using old URL")

            # Progress: 70% - Retrieving file metadata
            await _update_status(job_id, 'processing', progress=70)
            task.update_state(state='PROGRESS', meta={'progress': 70})

            # Get file size and provider from existing download for reuse
            storage_provider = existing_download.get('storageProvider', 'gcs')
            file_size = existing_download.get('fileSize', 0)

            # Progress: 90% - Preparing response
            await _update_status(job_id, 'processing', progress=90)
            task.update_state(state='PROGRESS', meta={'progress': 90})
        else:
            # Download video with real-time progress tracking
            logger.info(f"Downloading video: {video_id}")

            # Create a shared progress state that can be updated from thread
            import threading
            progress_lock = threading.Lock()
            current_progress = {'value': 10}

            # Create progress callback that updates from worker thread
            def progress_callback(progress: int):
                """Callback from worker thread - just update shared state"""
                try:
                    with progress_lock:
                        current_progress['value'] = progress
                    logger.info(f"Download progress: {progress}%")
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}", exc_info=True)

            # Start download in background
            import concurrent.futures
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            download_future = executor.submit(
                youtube_service.download_video_sync,
                url,
                video_id,
                progress_callback,
                cookies
            )

            # Poll progress while download is running
            last_reported_progress = 10
            while not download_future.done():
                await asyncio.sleep(0.5)  # Check every 500ms

                with progress_lock:
                    current_prog = current_progress['value']

                if current_prog > last_reported_progress:
                    logger.info(f"Progress update: {current_prog}% (job: {job_id})")
                    await _update_status(job_id, 'processing', progress=current_prog)
                    task.update_state(state='PROGRESS', meta={'progress': current_prog})
                    last_reported_progress = current_prog

            # Get result or raise exception
            local_file_path = download_future.result()
            executor.shutdown(wait=False)

            await _update_status(job_id, 'processing', progress=90)
            task.update_state(state='PROGRESS', meta={'progress': 90})

            # Upload to cloud storage with video title as filename
            logger.info(f"Uploading video to cloud storage: {video_id}")
            await _update_status(job_id, 'processing', progress=92)
            task.update_state(state='PROGRESS', meta={'progress': 92})

            # Create a safe filename from video title
            safe_title = "".join(c for c in video_info.title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title[:100]  # Limit length
            destination_filename = f"{safe_title}.mp4" if safe_title else f"{video_id}.mp4"

            # Upload to cloud storage (returns url, provider, file_size)
            download_url, storage_provider, file_size = await storage_service.upload_file(local_file_path, destination_filename)

            await _update_status(job_id, 'processing', progress=98)
            task.update_state(state='PROGRESS', meta={'progress': 98})

            # Clean up local file - ensure this always happens
            try:
                logger.info(f"Deleting local file: {local_file_path}")
                await youtube_service.delete_local_file(local_file_path)
                logger.info(f"Successfully deleted local file: {local_file_path}")
            except Exception as cleanup_error:
                logger.error(f"Failed to delete local file {local_file_path}: {cleanup_error}")

        # Update status to completed with all data
        video_info_dict = video_info.model_dump(by_alias=True)
        await _update_status(
            job_id,
            'completed',
            progress=100,
            downloadUrl=download_url,
            videoInfo=video_info_dict,
            storageProvider=storage_provider,
            fileSize=file_size
        )

        logger.info(f"Download job completed: {job_id}")

        return {
            'job_id': job_id,
            'status': 'completed',
            'download_url': download_url,
            'video_info': video_info_dict
        }
    except Exception as e:
        logger.error(f"Download job failed: {job_id} - {str(e)}")
        await _update_status(job_id, 'failed', error=str(e))
        raise


async def _get_db():
    """Get database instance for Celery worker with resource limits"""
    global _db_client, _db
    if _db is None:
        # Reduced pool size and increased timeouts for 1GB RAM stability
        _db_client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            maxPoolSize=10,             # Reduced from 50 to save RAM/CPU
            minPoolSize=1,              # Minimal idle connections
            maxIdleTimeMS=30000,
            connectTimeoutMS=20000,     # Longer timeout for SSL handshakes
            serverSelectionTimeoutMS=10000,
            # Ensure we don't leak threads in the background
            retryWrites=True
        )
        try:
            _db = _db_client.get_database()
        except:
            _db = _db_client[settings.MONGODB_DB_NAME]
            logger.info(f"Worker connected to: {settings.MONGODB_DB_NAME}")
    return _db


def _extract_filename_from_url(url: str) -> str | None:
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


async def _update_status(job_id: str, status: str, **kwargs):
    """Update download status in database and send WebSocket notification"""
    try:
        db = await _get_db()
        update_data = {'status': status, 'updatedAt': __import__('datetime').datetime.utcnow()}
        update_data.update(kwargs)

        await db.downloads.update_one(
            {'jobId': job_id},
            {'$set': update_data}
        )

        # Send WebSocket update
        try:
            progress = kwargs.get('progress')
            ws_data = {
                "type": "status",
                "data": {
                    "jobId": job_id,
                    "status": status,
                    "progress": progress,
                    **kwargs
                }
            }
            await manager.send_update(job_id, ws_data)
            logger.debug(f"WebSocket update sent for job {job_id}: {status} ({progress}%)")
        except Exception as ws_error:
            logger.error(f"Failed to send WebSocket update: {ws_error}")

    except Exception as e:
        logger.error(f"Error updating status: {e}")
