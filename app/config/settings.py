from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import ConfigDict


class Settings(BaseSettings):
    # Database
    MONGODB_URI: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Google Cloud Storage
    GCP_PROJECT_ID: str
    GCP_BUCKET_NAME: str
    GOOGLE_APPLICATION_CREDENTIALS: str

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
    FILE_EXPIRY_HOURS: int = 24

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Local binary paths (optional - set by setup_ffmpeg.py)
    FFMPEG_PATH: Optional[str] = None
    FFPROBE_PATH: Optional[str] = None
    YT_DLP_PATH: Optional[str] = None

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields instead of raising validation error
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
