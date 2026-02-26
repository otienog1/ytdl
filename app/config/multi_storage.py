"""
Multi-cloud storage configuration for GCS, Azure Blob, and AWS S3
"""
from google.cloud import storage as gcs_storage
from azure.storage.blob import BlobServiceClient
import boto3
from app.config.settings import settings
from app.utils.logger import logger
from typing import Optional, List


class MultiCloudStorage:
    _instance = None

    # GCS
    _gcs_client: Optional[gcs_storage.Client] = None
    _gcs_bucket: Optional[gcs_storage.Bucket] = None

    # Azure
    _azure_client: Optional[BlobServiceClient] = None
    _azure_container: Optional[str] = None

    # AWS S3
    _s3_client: Optional[any] = None
    _s3_bucket: Optional[str] = None

    # Available providers list
    _available_providers: List[str] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MultiCloudStorage, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._available_providers:  # Only initialize once
            self._initialize_providers()

    def _initialize_providers(self):
        """Initialize all configured storage providers"""

        # Initialize Google Cloud Storage
        try:
            self._gcs_client = gcs_storage.Client(
                project=settings.GCP_PROJECT_ID
            )
            self._gcs_bucket = self._gcs_client.bucket(settings.GCP_BUCKET_NAME)
            self._available_providers.append("gcs")
            logger.info("Google Cloud Storage initialized")
        except Exception as e:
            logger.warning(f"GCS initialization failed: {e}")

        # Initialize Azure Blob Storage
        if settings.AZURE_STORAGE_CONNECTION_STRING and settings.AZURE_CONTAINER_NAME:
            try:
                self._azure_client = BlobServiceClient.from_connection_string(
                    settings.AZURE_STORAGE_CONNECTION_STRING
                )
                self._azure_container = settings.AZURE_CONTAINER_NAME
                # Test connection
                self._azure_client.get_container_client(self._azure_container).exists()
                self._available_providers.append("azure")
                logger.info("Azure Blob Storage initialized")
            except Exception as e:
                logger.warning(f"Azure initialization failed: {e}")

        # Initialize AWS S3
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.AWS_S3_BUCKET_NAME:
            try:
                from botocore.config import Config

                self._s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION,
                    config=Config(signature_version='s3v4')
                )
                self._s3_bucket = settings.AWS_S3_BUCKET_NAME
                # Test connection
                self._s3_client.head_bucket(Bucket=self._s3_bucket)
                self._available_providers.append("s3")
                logger.info("AWS S3 Storage initialized")
            except Exception as e:
                logger.warning(f"S3 initialization failed: {e}")

        if not self._available_providers:
            logger.error("No storage providers initialized!")
        else:
            logger.info(f"Available storage providers: {', '.join(self._available_providers)}")

    def get_available_providers(self) -> List[str]:
        """Get list of available storage providers"""
        return self._available_providers.copy()

    def get_gcs_bucket(self) -> Optional[gcs_storage.Bucket]:
        """Get GCS bucket"""
        return self._gcs_bucket

    def get_gcs_client(self) -> Optional[gcs_storage.Client]:
        """Get GCS client"""
        return self._gcs_client

    def get_azure_container_client(self):
        """Get Azure container client"""
        if self._azure_client and self._azure_container:
            return self._azure_client.get_container_client(self._azure_container)
        return None

    def get_azure_client(self) -> Optional[BlobServiceClient]:
        """Get Azure Blob Service client"""
        return self._azure_client

    def get_s3_client(self):
        """Get S3 client"""
        return self._s3_client

    def get_s3_bucket_name(self) -> Optional[str]:
        """Get S3 bucket name"""
        return self._s3_bucket


multi_storage = MultiCloudStorage()
