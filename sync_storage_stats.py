"""
Utility script to sync storage stats with actual cloud storage
Run this to fix discrepancies between MongoDB stats and actual files in cloud storage
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.config.multi_storage import multi_storage
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
        print(f"Error getting GCS stats: {e}")
        return None, None


async def get_actual_azure_stats():
    """Get actual file count and size from Azure blob storage"""
    try:
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
        print(f"Error getting Azure stats: {e}")
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
        print(f"Error getting S3 stats: {e}")
        return None, None


async def sync_storage_stats():
    """Sync MongoDB storage stats with actual cloud storage"""

    print("=" * 80)
    print("Storage Stats Sync Utility")
    print("=" * 80)
    print()

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

    for provider in available_providers:
        print(f"\n{provider.upper()} Storage:")
        print("-" * 40)

        # Get current MongoDB stats
        db_stats = await db.storage_stats.find_one({"provider": provider})
        if db_stats:
            db_count = db_stats.get('file_count', 0)
            db_size = db_stats.get('total_size_bytes', 0)
            print(f"  MongoDB stats: {db_count} files, {db_size / (1024**2):.2f} MB")
        else:
            db_count = 0
            db_size = 0
            print(f"  MongoDB stats: No record found")

        # Get actual cloud storage stats
        if provider in providers_config:
            actual_count, actual_size = await providers_config[provider]()

            if actual_count is not None:
                print(f"  Actual cloud:  {actual_count} files, {actual_size / (1024**2):.2f} MB")

                # Check for discrepancy
                if db_count != actual_count or db_size != actual_size:
                    print(f"  [!] MISMATCH DETECTED!")
                    print(f"     Updating MongoDB to match actual cloud storage...")

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

                    print(f"     [OK] Updated successfully!")
                else:
                    print(f"  [OK] Stats match - no sync needed")

    client.close()

    print()
    print("=" * 80)
    print("Sync complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(sync_storage_stats())
