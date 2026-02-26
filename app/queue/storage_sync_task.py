"""
Celery task for syncing storage stats with actual cloud storage
Can be run manually or scheduled with Celery Beat
"""
import asyncio
from app.queue.celery_app import celery_app
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.config.multi_storage import multi_storage
from app.utils.logger import logger
from google.cloud import storage as gcs_storage
from azure.storage.blob import BlobServiceClient
import boto3
from datetime import datetime


async def get_actual_gcs_stats():
    """Get actual file count and size from GCS bucket"""
    try:
        storage_client = gcs_storage.Client()
        bucket = storage_client.bucket(settings.GCP_BUCKET_NAME)
        blobs = list(bucket.list_blobs())
        total_size = sum(blob.size for blob in blobs)
        return len(blobs), total_size
    except Exception as e:
        logger.error(f"Error getting GCS stats: {e}")
        return None, None


async def get_actual_azure_stats():
    """Get actual file count and size from Azure blob storage"""
    try:
        if not settings.AZURE_STORAGE_CONNECTION_STRING:
            logger.error("Azure storage connection string is not configured")
            return None, None
        
        if not settings.AZURE_CONTAINER_NAME:
            logger.error("Azure container name is not configured")
            return None, None
        
        blob_service_client = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
        container_client = blob_service_client.get_container_client(
            settings.AZURE_CONTAINER_NAME
        )
        blobs = list(container_client.list_blobs())
        total_size = sum(blob.size for blob in blobs)
        return len(blobs), total_size
    except Exception as e:
        logger.error(f"Error getting Azure stats: {e}")
        return None, None


async def get_actual_s3_stats():
    """Get actual file count and size from S3 bucket"""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        response = s3_client.list_objects_v2(Bucket=settings.AWS_S3_BUCKET_NAME)

        if 'Contents' not in response:
            return 0, 0

        total_size = sum(obj['Size'] for obj in response['Contents'])
        return len(response['Contents']), total_size
    except Exception as e:
        logger.error(f"Error getting S3 stats: {e}")
        return None, None


async def sync_storage_stats_async():
    """Sync MongoDB storage stats with actual cloud storage"""

    logger.info("=" * 60)
    logger.info("Starting storage stats sync")
    logger.info("=" * 60)

    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    try:
        db = client.get_database()
    except:
        db = client['ytdl_db']

    # Get available providers
    providers_config = {
        'gcs': get_actual_gcs_stats,
        'azure': get_actual_azure_stats,
        's3': get_actual_s3_stats
    }

    available_providers = multi_storage.get_available_providers()

    total_synced = 0
    total_errors = 0

    for provider in available_providers:
        logger.info(f"Checking {provider.upper()} storage...")

        try:
            # Get current MongoDB stats
            db_stats = await db.storage_stats.find_one({"provider": provider})
            if db_stats:
                db_count = db_stats.get('file_count', 0)
                db_size = db_stats.get('total_size_bytes', 0)
                logger.info(f"  MongoDB: {db_count} files, {db_size / (1024**2):.2f} MB")
            else:
                db_count = 0
                db_size = 0
                logger.info(f"  MongoDB: No record found")

            # Get actual cloud storage stats
            if provider in providers_config:
                actual_count, actual_size = await providers_config[provider]()

                if actual_count is not None:
                    logger.info(f"  Cloud:   {actual_count} files, {actual_size / (1024**2):.2f} MB")

                    # Check for discrepancy
                    if db_count != actual_count or db_size != actual_size:
                        logger.warning(f"  MISMATCH DETECTED - Updating MongoDB...")

                        # Update MongoDB to match reality
                        await db.storage_stats.update_one(
                            {"provider": provider},
                            {
                                "$set": {
                                    "file_count": actual_count,
                                    "total_size_bytes": actual_size,
                                    "last_updated": datetime.utcnow(),
                                    "is_full": actual_size >= settings.STORAGE_LIMIT_BYTES
                                }
                            },
                            upsert=True
                        )

                        logger.info(f"  ✓ Updated successfully!")
                        total_synced += 1
                    else:
                        logger.info(f"  ✓ Stats match - no sync needed")
                else:
                    logger.error(f"  Failed to get actual stats for {provider}")
                    total_errors += 1
        except Exception as e:
            logger.error(f"Error syncing {provider}: {e}", exc_info=True)
            total_errors += 1

    client.close()

    logger.info("=" * 60)
    logger.info(f"Storage sync complete: {total_synced} providers synced, {total_errors} errors")
    logger.info("=" * 60)

    return {
        'synced': total_synced,
        'errors': total_errors,
        'providers_checked': len(available_providers)
    }


@celery_app.task(name='sync_storage_stats')
def sync_storage_stats():
    """
    Celery task to sync storage stats with actual cloud storage

    This task can be:
    1. Run manually: celery -A app.queue.celery_app call sync_storage_stats
    2. Triggered via API endpoint
    3. Scheduled with Celery Beat (see celery_beat_schedule)

    Returns:
        dict: Stats about the sync operation
    """
    try:
        logger.info("Storage stats sync task started")

        # Run async function in sync context
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(sync_storage_stats_async())

        logger.info(f"Storage stats sync task completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Storage stats sync task failed: {e}", exc_info=True)
        raise
