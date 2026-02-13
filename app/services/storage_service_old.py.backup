from datetime import timedelta
from pathlib import Path
from app.config.storage import gcs
from app.utils.logger import logger


class StorageService:
    def __init__(self):
        self.bucket = gcs.get_bucket()

    async def upload_file(self, local_file_path: str, destination_file_name: str = None) -> str:
        """Upload file to Google Cloud Storage"""
        try:
            import uuid

            # Always add UUID to filename to avoid conflicts
            # Even if we have a custom filename, make it unique
            if destination_file_name:
                # Extract name and extension
                name_parts = destination_file_name.rsplit('.', 1)
                if len(name_parts) == 2:
                    base_name, ext = name_parts
                    file_name = f"{base_name}_{uuid.uuid4().hex[:8]}.{ext}"
                else:
                    file_name = f"{destination_file_name}_{uuid.uuid4().hex[:8]}.mp4"
            else:
                file_name = f"{uuid.uuid4()}.mp4"

            blob = self.bucket.blob(file_name)

            # Upload file with timeout and retry configuration
            # Set timeout to 5 minutes (300 seconds) for large files
            blob.upload_from_filename(
                local_file_path,
                content_type='video/mp4',
                timeout=300,  # 5 minutes
                retry=None    # Use default retry strategy
            )

            logger.info(f"File uploaded to GCS: {file_name}")

            # Generate signed URL valid for 24 hours with Content-Disposition header
            # This forces the browser to download the file instead of playing it
            url = blob.generate_signed_url(
                expiration=timedelta(hours=24),
                method='GET',
                response_disposition=f'attachment; filename="{file_name}"'
            )

            return url
        except Exception as e:
            logger.error(f"Error uploading file to GCS: {e}")
            raise

    async def regenerate_signed_url(self, file_name: str) -> str:
        """Regenerate signed URL for an existing file with download disposition"""
        try:
            blob = self.bucket.blob(file_name)

            # Generate new signed URL with Content-Disposition header
            url = blob.generate_signed_url(
                expiration=timedelta(hours=24),
                method='GET',
                response_disposition=f'attachment; filename="{file_name}"'
            )

            logger.info(f"Regenerated signed URL for: {file_name}")
            return url
        except Exception as e:
            logger.error(f"Error regenerating signed URL: {e}")
            raise

    async def delete_file(self, file_name: str):
        """Delete file from Google Cloud Storage"""
        try:
            blob = self.bucket.blob(file_name)
            blob.delete()
            logger.info(f"File deleted from GCS: {file_name}")
        except Exception as e:
            logger.error(f"Error deleting file from GCS: {e}")
            raise

    async def cleanup_old_files(self, hours_old: int = 24):
        """Cleanup old files from Google Cloud Storage"""
        try:
            from datetime import datetime, timezone

            blobs = self.bucket.list_blobs()
            cutoff_date = datetime.now(timezone.utc) - timedelta(hours=hours_old)

            for blob in blobs:
                if blob.time_created < cutoff_date:
                    blob.delete()
                    logger.info(f"Cleaned up old file: {blob.name}")
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")


storage_service = StorageService()
