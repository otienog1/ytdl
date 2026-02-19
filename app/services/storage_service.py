"""
Multi-cloud storage service with random distribution across GCS, Azure, and AWS S3
"""
import os
import random
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Tuple, Optional
from app.config.multi_storage import multi_storage
from app.services.storage_tracker import storage_tracker
from app.utils.logger import logger
from app.exceptions import (
    StorageProviderNotAvailableError,
    FileUploadError,
    FileNotFoundError as StorageFileNotFoundError
)
from app.monitoring.metrics import metrics_tracker


class MultiStorageService:
    """Unified storage service supporting GCS, Azure Blob, and AWS S3"""

    def __init__(self):
        pass

    async def select_random_provider(self) -> str:
        """
        Select a random storage provider that is under the storage limit.
        Returns provider name ('gcs', 'azure', 's3')
        Raises StorageProviderNotAvailableError if all providers are full.
        """
        # Get providers that are available and under limit
        available_providers = await storage_tracker.get_available_providers_under_limit()

        if not available_providers:
            raise StorageProviderNotAvailableError()

        # Randomly select one
        selected = random.choice(available_providers)
        logger.info(f"Selected storage provider: {selected}")
        return selected

    async def upload_file(self, local_file_path: str, destination_file_name: str = None) -> Tuple[str, str, int]:
        """
        Upload file to a randomly selected storage provider.

        Returns:
            Tuple[url, provider, file_size]: Download URL, provider name, and file size in bytes
        """
        # Select provider (raises StorageProviderNotAvailableError if none available)
        provider = await self.select_random_provider()

        # Get file size
        file_size = os.path.getsize(local_file_path)

        # Generate unique filename
        file_name = self._generate_filename(destination_file_name)

        # Upload based on provider
        if provider == "gcs":
            url = await self._upload_to_gcs(local_file_path, file_name)
        elif provider == "azure":
            url = await self._upload_to_azure(local_file_path, file_name)
        elif provider == "s3":
            url = await self._upload_to_s3(local_file_path, file_name)
        else:
            raise FileUploadError(provider, f"Unknown provider: {provider}")

        # Track storage usage
        await storage_tracker.add_file_usage(provider, file_size, file_name)

        logger.info(f"File uploaded to {provider}: {file_name} ({file_size} bytes)")
        return url, provider, file_size

    def _generate_filename(self, destination_file_name: str = None) -> str:
        """Generate a unique filename"""
        if destination_file_name:
            # Extract name and extension
            name_parts = destination_file_name.rsplit('.', 1)
            if len(name_parts) == 2:
                base_name, ext = name_parts
                return f"{base_name}_{uuid.uuid4().hex[:8]}.{ext}"
            else:
                return f"{destination_file_name}_{uuid.uuid4().hex[:8]}.mp4"
        else:
            return f"{uuid.uuid4()}.mp4"

    async def _upload_to_gcs(self, local_file_path: str, file_name: str) -> str:
        """Upload file to Google Cloud Storage"""
        with metrics_tracker.track_upload("gcs"):
            try:
                bucket = multi_storage.get_gcs_bucket()
                if not bucket:
                    raise FileUploadError("gcs", "GCS not configured")

                blob = bucket.blob(file_name)
                blob.upload_from_filename(
                    local_file_path,
                    content_type='video/mp4',
                    timeout=300,
                    retry=None
                )

                # Generate signed URL with download disposition (1 hour)
                url = blob.generate_signed_url(
                    expiration=timedelta(hours=1),
                    method='GET',
                    response_disposition=f'attachment; filename="{file_name}"'
                )

                return url
            except FileUploadError:
                raise
            except Exception as e:
                raise FileUploadError("gcs", str(e))

    async def _upload_to_azure(self, local_file_path: str, file_name: str) -> str:
        """Upload file to Azure Blob Storage"""
        with metrics_tracker.track_upload("azure"):
            try:
                from azure.storage.blob import ContentSettings

                container_client = multi_storage.get_azure_container_client()
                if not container_client:
                    raise FileUploadError("azure", "Azure not configured")

                blob_client = container_client.get_blob_client(file_name)

                with open(local_file_path, "rb") as data:
                    blob_client.upload_blob(
                        data,
                        content_settings=ContentSettings(content_type="video/mp4"),
                        overwrite=True
                    )

                # Generate SAS URL for download (1 hour)
                from azure.storage.blob import generate_blob_sas, BlobSasPermissions
                from datetime import datetime, timedelta

                # Get connection info from container client
                account_name = blob_client.account_name
                container_name = container_client.container_name

                # Generate SAS token
                from app.config.settings import settings
                sas_token = generate_blob_sas(
                    account_name=account_name,
                    container_name=container_name,
                    blob_name=file_name,
                    account_key=self._extract_azure_account_key(),
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.utcnow() + timedelta(hours=1),
                    content_disposition=f'attachment; filename="{file_name}"'
                )

                url = f"{blob_client.url}?{sas_token}"
                return url
            except FileUploadError:
                raise
            except Exception as e:
                raise FileUploadError("azure", str(e))

    def _extract_azure_account_key(self) -> str:
        """Extract account key from Azure connection string"""
        from app.config.settings import settings
        conn_str = settings.AZURE_STORAGE_CONNECTION_STRING
        for part in conn_str.split(';'):
            if part.startswith('AccountKey='):
                return part.split('=', 1)[1]
        raise FileUploadError("azure", "Could not extract Azure account key from connection string")

    async def _upload_to_s3(self, local_file_path: str, file_name: str) -> str:
        """Upload file to AWS S3"""
        with metrics_tracker.track_upload("s3"):
            try:
                s3_client = multi_storage.get_s3_client()
                bucket_name = multi_storage.get_s3_bucket_name()
                if not s3_client or not bucket_name:
                    raise FileUploadError("s3", "S3 not configured")

                # Upload file
                s3_client.upload_file(
                    local_file_path,
                    bucket_name,
                    file_name,
                    ExtraArgs={
                        'ContentType': 'video/mp4',
                        'ContentDisposition': f'attachment; filename="{file_name}"'
                    }
                )

                # Generate presigned URL (1 hour)
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': bucket_name,
                        'Key': file_name,
                        'ResponseContentDisposition': f'attachment; filename="{file_name}"'
                    },
                    ExpiresIn=3600  # 1 hour
                )

                return url
            except FileUploadError:
                raise
            except Exception as e:
                raise FileUploadError("s3", str(e))

    async def delete_file(self, file_name: str, provider: str):
        """Delete file from specified storage provider"""
        try:
            # Get file size before deleting (for tracking)
            file_size = await self._get_file_size(file_name, provider)

            # Delete based on provider
            if provider == "gcs":
                await self._delete_from_gcs(file_name)
            elif provider == "azure":
                await self._delete_from_azure(file_name)
            elif provider == "s3":
                await self._delete_from_s3(file_name)
            else:
                raise StorageFileNotFoundError(file_name, provider)

            # Track storage usage
            if file_size:
                await storage_tracker.remove_file_usage(provider, file_size, file_name)

            logger.info(f"File deleted from {provider}: {file_name}")
        except StorageFileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting file from {provider}: {e}")
            # Don't raise - deletion is not critical for most flows

    async def _get_file_size(self, file_name: str, provider: str) -> Optional[int]:
        """Get file size from storage provider"""
        try:
            if provider == "gcs":
                bucket = multi_storage.get_gcs_bucket()
                blob = bucket.blob(file_name)
                blob.reload()
                return blob.size
            elif provider == "azure":
                container_client = multi_storage.get_azure_container_client()
                blob_client = container_client.get_blob_client(file_name)
                properties = blob_client.get_blob_properties()
                return properties.size
            elif provider == "s3":
                s3_client = multi_storage.get_s3_client()
                bucket_name = multi_storage.get_s3_bucket_name()
                response = s3_client.head_object(Bucket=bucket_name, Key=file_name)
                return response['ContentLength']
        except Exception as e:
            logger.warning(f"Could not get file size for {file_name} from {provider}: {e}")
            return None

    async def _delete_from_gcs(self, file_name: str):
        """Delete file from GCS"""
        bucket = multi_storage.get_gcs_bucket()
        blob = bucket.blob(file_name)
        blob.delete()

    async def _delete_from_azure(self, file_name: str):
        """Delete file from Azure"""
        container_client = multi_storage.get_azure_container_client()
        blob_client = container_client.get_blob_client(file_name)
        blob_client.delete_blob()

    async def _delete_from_s3(self, file_name: str):
        """Delete file from S3"""
        s3_client = multi_storage.get_s3_client()
        bucket_name = multi_storage.get_s3_bucket_name()
        s3_client.delete_object(Bucket=bucket_name, Key=file_name)

    async def regenerate_signed_url(self, file_name: str, provider: str) -> str:
        """Regenerate signed URL for an existing file (1 hour expiry)"""
        if provider == "gcs":
            bucket = multi_storage.get_gcs_bucket()
            blob = bucket.blob(file_name)
            return blob.generate_signed_url(
                expiration=timedelta(hours=1),
                method='GET',
                response_disposition=f'attachment; filename="{file_name}"'
            )
        elif provider == "azure":
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions
            from datetime import datetime
            container_client = multi_storage.get_azure_container_client()
            blob_client = container_client.get_blob_client(file_name)
            account_name = blob_client.account_name
            container_name = container_client.container_name

            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=container_name,
                blob_name=file_name,
                account_key=self._extract_azure_account_key(),
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=1),
                content_disposition=f'attachment; filename="{file_name}"'
            )
            return f"{blob_client.url}?{sas_token}"
        elif provider == "s3":
            s3_client = multi_storage.get_s3_client()
            bucket_name = multi_storage.get_s3_bucket_name()
            return s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': file_name,
                    'ResponseContentDisposition': f'attachment; filename="{file_name}"'
                },
                ExpiresIn=3600  # 1 hour
            )
        else:
            raise Exception(f"Unknown provider: {provider}")


storage_service = MultiStorageService()
