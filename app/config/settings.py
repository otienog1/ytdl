from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import ConfigDict


class Settings(BaseSettings):
    # Database
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "ytdl_db"  # Default database name

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Google Cloud Storage
    GCP_PROJECT_ID: str
    GCP_BUCKET_NAME: str
    GOOGLE_APPLICATION_CREDENTIALS: str

    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_CONTAINER_NAME: Optional[str] = None

    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET_NAME: Optional[str] = None
    AWS_REGION: Optional[str] = "us-east-1"

    # Email (Mailgun SMTP)
    MAILGUN_SMTP_HOST: str = "smtp.mailgun.org"
    MAILGUN_SMTP_PORT: int = 587
    MAILGUN_SMTP_USER: Optional[str] = None
    MAILGUN_SMTP_PASSWORD: Optional[str] = None
    ALERT_EMAIL_FROM: Optional[str] = None
    ALERT_EMAIL_TO: Optional[str] = None

    # Storage limits (in bytes)
    STORAGE_LIMIT_BYTES: int = 5 * 1024 * 1024 * 1024  # 5GB

    # Server
    PORT: int = 3001
    ENVIRONMENT: str = "development"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Rate Limiting
    RATE_LIMIT_WINDOW: int = 900  # 15 minutes in seconds
    RATE_LIMIT_MAX_REQUESTS: int = 30
    RATE_LIMIT_WINDOW_MS: Optional[int] = None  # Legacy Node.js format (milliseconds)

    # File Cleanup
    FILE_EXPIRY_HOURS: int = 1  # Delete files 1 hour after download

    # Timeouts (in seconds)
    YTDLP_INFO_TIMEOUT: int = 60  # seconds
    YTDLP_DOWNLOAD_TIMEOUT: int = 300  # 5 minutes
    STORAGE_UPLOAD_TIMEOUT: int = 180  # 3 minutes

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Local binary paths (optional - set by setup_ffmpeg.py)
    FFMPEG_PATH: Optional[str] = None
    FFPROBE_PATH: Optional[str] = None
    YT_DLP_PATH: Optional[str] = None

    # YouTube Account Configuration (for multi-server setup)
    YT_ACCOUNT_ID: str = "default"  # Unique identifier for this server's YouTube account
    YT_DLP_COOKIES_FILE: Optional[str] = None  # Path to cookies file for this account

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields instead of raising validation error
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
