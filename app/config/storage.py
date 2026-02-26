from google.cloud import storage
from app.config.settings import settings
from app.utils.logger import logger


class GoogleCloudStorage:
    _instance = None
    _client: storage.Client = None
    _bucket: storage.Bucket = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GoogleCloudStorage, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._client:
            try:
                self._client = storage.Client(
                    project=settings.GCP_PROJECT_ID
                )
                self._bucket = self._client.bucket(settings.GCP_BUCKET_NAME)
                logger.info("Google Cloud Storage initialized")
            except Exception as e:
                logger.warning(f"GCP initialization error: {e}")
                logger.warning("Google Cloud Storage features will be limited")

    def get_bucket(self) -> storage.Bucket:
        """Get GCS bucket"""
        return self._bucket

    def get_client(self) -> storage.Client:
        """Get GCS client"""
        return self._client


gcs = GoogleCloudStorage()
