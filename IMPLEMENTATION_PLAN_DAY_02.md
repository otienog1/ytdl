# Day 2: Structured Error Handling & Custom Exceptions

**Goal**: Implement robust error handling with custom exceptions and error codes
**Estimated Time**: 6-8 hours
**Priority**: HIGH - Critical for production stability

---

## Morning Session (3-4 hours)

### Task 2.1: Create custom exception hierarchy (60 min)

**File: `backend-python/app/exceptions/__init__.py`**
```python
"""
Custom exception hierarchy for the application
"""
from typing import Optional, Dict, Any
from fastapi import status

class AppException(Exception):
    """Base exception for all application errors"""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response"""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details
            }
        }


class ValidationError(AppException):
    """Raised when input validation fails"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class YouTubeError(AppException):
    """Base exception for YouTube-related errors"""
    pass


class InvalidVideoURLError(YouTubeError):
    """Raised when YouTube URL is invalid"""

    def __init__(self, url: str):
        super().__init__(
            message=f"Invalid YouTube URL: {url}",
            error_code="INVALID_VIDEO_URL",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"url": url}
        )


class VideoNotFoundError(YouTubeError):
    """Raised when video is not found or unavailable"""

    def __init__(self, video_id: str, reason: Optional[str] = None):
        super().__init__(
            message=f"Video not found or unavailable: {video_id}",
            error_code="VIDEO_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"video_id": video_id, "reason": reason}
        )


class VideoDownloadError(YouTubeError):
    """Raised when video download fails"""

    def __init__(self, video_id: str, reason: str):
        super().__init__(
            message=f"Failed to download video: {reason}",
            error_code="VIDEO_DOWNLOAD_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"video_id": video_id, "reason": reason}
        )


class StorageError(AppException):
    """Base exception for storage-related errors"""
    pass


class StorageProviderNotAvailableError(StorageError):
    """Raised when no storage providers are available"""

    def __init__(self):
        super().__init__(
            message="All storage providers are at capacity",
            error_code="STORAGE_FULL",
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            details={"suggestion": "Please try again later"}
        )


class FileUploadError(StorageError):
    """Raised when file upload fails"""

    def __init__(self, provider: str, reason: str):
        super().__init__(
            message=f"Failed to upload file to {provider}: {reason}",
            error_code="FILE_UPLOAD_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"provider": provider, "reason": reason}
        )


class FileNotFoundError(StorageError):
    """Raised when file is not found in storage"""

    def __init__(self, file_name: str, provider: str):
        super().__init__(
            message=f"File not found: {file_name}",
            error_code="FILE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"file_name": file_name, "provider": provider}
        )


class RateLimitError(AppException):
    """Raised when rate limit is exceeded"""

    def __init__(self, retry_after: int):
        super().__init__(
            message="Rate limit exceeded",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after_seconds": retry_after}
        )


class DatabaseError(AppException):
    """Raised when database operation fails"""

    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Database operation failed: {operation}",
            error_code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"operation": operation, "reason": reason}
        )
```

**Checkpoint**: Import exceptions and verify they work

---

### Task 2.2: Update global exception handler (45 min)

**File: `backend-python/app/main.py`** (Update existing handler)
```python
from app.exceptions import AppException
from app.utils.logger import logger
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions"""
    logger.error(
        f"Application error: {exc.error_code}",
        extra={
            "error_code": exc.error_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(
        "Validation error",
        extra={
            "path": request.url.path,
            "errors": exc.errors()
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": exc.errors()
            }
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(
        "Unexpected error",
        extra={
            "path": request.url.path,
            "error": str(exc),
            "traceback": traceback.format_exc()
        }
    )

    # Don't expose internal errors in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {} if settings.ENVIRONMENT == "production" else {"error": str(exc)}
            }
        }
    )
```

---

### Task 2.3: Update YouTube service with custom exceptions (90 min)

**File: `backend-python/app/services/youtube_service.py`** (Update methods)
```python
from app.exceptions import (
    InvalidVideoURLError,
    VideoNotFoundError,
    VideoDownloadError
)

class YouTubeService:

    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        # ... existing code ...

        if not video_id:
            raise InvalidVideoURLError(url)

        return video_id

    async def get_video_info(self, url: str, cookies: dict = None) -> VideoInfo:
        """Get video information"""
        video_id = self._extract_video_id(url)  # Can raise InvalidVideoURLError

        try:
            # ... existing yt-dlp code ...
            result = subprocess.run(cmd, ...)

            if result.returncode != 0:
                stderr = result.stderr.decode('utf-8') if result.stderr else ""

                # Parse yt-dlp errors
                if "Video unavailable" in stderr:
                    raise VideoNotFoundError(video_id, "Video is unavailable")
                elif "Private video" in stderr:
                    raise VideoNotFoundError(video_id, "Video is private")
                elif "This video is no longer available" in stderr:
                    raise VideoNotFoundError(video_id, "Video has been removed")
                else:
                    raise VideoDownloadError(video_id, stderr)

            # ... process result ...

        except subprocess.TimeoutExpired:
            raise VideoDownloadError(
                video_id,
                "Request timed out after 60 seconds"
            )
        except FileNotFoundError:
            raise VideoDownloadError(
                video_id,
                "yt-dlp binary not found"
            )
        except Exception as e:
            if isinstance(e, (InvalidVideoURLError, VideoNotFoundError, VideoDownloadError)):
                raise
            raise VideoDownloadError(video_id, str(e))

    async def download_video_sync(self, url: str, output_path: str, cookies: dict = None) -> str:
        """Download video"""
        video_id = self._extract_video_id(url)

        try:
            # ... existing download code ...

            if result.returncode != 0:
                stderr = result.stderr.decode('utf-8') if result.stderr else ""
                raise VideoDownloadError(video_id, stderr)

            return output_path

        except subprocess.TimeoutExpired:
            raise VideoDownloadError(
                video_id,
                "Download timed out after 5 minutes"
            )
        except Exception as e:
            if isinstance(e, VideoDownloadError):
                raise
            raise VideoDownloadError(video_id, str(e))
```

**Checkpoint**: Test YouTube service with invalid URLs

---

## Afternoon Session (3-4 hours)

### Task 2.4: Update storage service with custom exceptions (90 min)

**File: `backend-python/app/services/storage_service.py`** (Update methods)
```python
from app.exceptions import (
    StorageProviderNotAvailableError,
    FileUploadError,
    FileNotFoundError as StorageFileNotFoundError
)

class MultiStorageService:

    async def select_random_provider(self) -> str:
        """Select random available provider"""
        available = await storage_tracker.get_available_providers_under_limit()

        if not available:
            raise StorageProviderNotAvailableError()

        return random.choice(available)

    async def _upload_to_gcs(self, local_file_path: str, file_name: str) -> str:
        """Upload to Google Cloud Storage"""
        try:
            blob = self._get_gcs_blob(file_name)
            blob.upload_from_filename(local_file_path, content_type='video/mp4')

            url = blob.generate_signed_url(
                expiration=timedelta(hours=1),
                method='GET',
                response_disposition=f'attachment; filename="{file_name}"'
            )
            return url

        except Exception as e:
            raise FileUploadError("gcs", str(e))

    async def _upload_to_azure(self, local_file_path: str, file_name: str) -> str:
        """Upload to Azure Blob Storage"""
        try:
            from azure.storage.blob import ContentSettings

            container_client = multi_storage.get_azure_container_client()
            blob_client = container_client.get_blob_client(file_name)

            with open(local_file_path, "rb") as data:
                blob_client.upload_blob(
                    data,
                    content_settings=ContentSettings(content_type="video/mp4"),
                    overwrite=True
                )

            # Generate SAS token
            # ... existing code ...

            return f"{blob_client.url}?{sas_token}"

        except Exception as e:
            raise FileUploadError("azure", str(e))

    async def _upload_to_s3(self, local_file_path: str, file_name: str) -> str:
        """Upload to AWS S3"""
        try:
            s3_client = multi_storage.get_s3_client()
            bucket_name = multi_storage.get_s3_bucket_name()

            s3_client.upload_file(
                local_file_path,
                bucket_name,
                file_name,
                ExtraArgs={
                    'ContentType': 'video/mp4',
                    'ContentDisposition': f'attachment; filename="{file_name}"'
                }
            )

            # Generate presigned URL
            # ... existing code ...

            return url

        except Exception as e:
            raise FileUploadError("s3", str(e))

    async def delete_file(self, file_name: str, provider: str):
        """Delete file from storage"""
        try:
            if provider == "gcs":
                blob = self._get_gcs_blob(file_name)
                if not blob.exists():
                    raise StorageFileNotFoundError(file_name, provider)
                blob.delete()

            elif provider == "azure":
                container_client = multi_storage.get_azure_container_client()
                blob_client = container_client.get_blob_client(file_name)
                blob_client.delete_blob()

            elif provider == "s3":
                s3_client = multi_storage.get_s3_client()
                bucket_name = multi_storage.get_s3_bucket_name()
                s3_client.delete_object(Bucket=bucket_name, Key=file_name)

        except StorageFileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete file {file_name} from {provider}: {e}")
            # Don't raise - deletion is not critical
```

---

### Task 2.5: Add timeout handling to subprocess calls (60 min)

**File: `backend-python/app/config/settings.py`** (Add timeout settings)
```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Timeouts
    YTDLP_INFO_TIMEOUT: int = 60  # seconds
    YTDLP_DOWNLOAD_TIMEOUT: int = 300  # 5 minutes
    STORAGE_UPLOAD_TIMEOUT: int = 180  # 3 minutes
```

**File: `backend-python/app/services/youtube_service.py`** (Add timeouts)
```python
from app.config.settings import settings

async def get_video_info(self, url: str, cookies: dict = None) -> VideoInfo:
    """Get video information with timeout"""
    video_id = self._extract_video_id(url)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=settings.YTDLP_INFO_TIMEOUT  # ← Add timeout
        )

        # ... rest of code ...

    except subprocess.TimeoutExpired:
        raise VideoDownloadError(
            video_id,
            f"Request timed out after {settings.YTDLP_INFO_TIMEOUT} seconds"
        )
```

---

### Task 2.6: Write tests for error handling (60 min)

**File: `backend-python/tests/unit/test_exceptions.py`**
```python
"""
Unit tests for custom exceptions
"""
import pytest
from app.exceptions import *
from fastapi import status

class TestCustomExceptions:
    """Test custom exception hierarchy"""

    def test_invalid_video_url_error(self):
        """Test InvalidVideoURLError"""
        exc = InvalidVideoURLError("https://invalid.com")

        assert exc.error_code == "INVALID_VIDEO_URL"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid.com" in exc.message
        assert exc.details["url"] == "https://invalid.com"

    def test_video_not_found_error(self):
        """Test VideoNotFoundError"""
        exc = VideoNotFoundError("abc123", "Video is private")

        assert exc.error_code == "VIDEO_NOT_FOUND"
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.details["video_id"] == "abc123"
        assert exc.details["reason"] == "Video is private"

    def test_storage_provider_not_available_error(self):
        """Test StorageProviderNotAvailableError"""
        exc = StorageProviderNotAvailableError()

        assert exc.error_code == "STORAGE_FULL"
        assert exc.status_code == status.HTTP_507_INSUFFICIENT_STORAGE

    def test_exception_to_dict(self):
        """Test exception serialization"""
        exc = InvalidVideoURLError("https://test.com")
        result = exc.to_dict()

        assert "error" in result
        assert result["error"]["code"] == "INVALID_VIDEO_URL"
        assert result["error"]["message"]
        assert result["error"]["details"]
```

**File: `backend-python/tests/unit/test_error_handling.py`**
```python
"""
Integration tests for error handling
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestErrorHandling:
    """Test API error responses"""

    def test_invalid_url_returns_400(self):
        """Test invalid URL returns 400 error"""
        response = client.post(
            "/api/download",
            json={"url": "https://invalid.com"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_VIDEO_URL"

    def test_validation_error_returns_422(self):
        """Test missing required field returns 422"""
        response = client.post(
            "/api/download",
            json={}
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
```

**Checkpoint**: Run `pipenv run pytest tests/unit/test_exceptions.py -v`

---

## End of Day Checklist

- [ ] Custom exception hierarchy created
- [ ] All exception classes defined with error codes
- [ ] Global exception handlers updated
- [ ] YouTube service using custom exceptions
- [ ] Storage service using custom exceptions
- [ ] Timeout handling added to subprocess calls
- [ ] Tests for exceptions written (8+ tests)
- [ ] All tests passing
- [ ] Code committed to git

**Git Commit**:
```bash
git add .
git commit -m "Day 2: Implement structured error handling

- Created custom exception hierarchy
- Added error codes for all error types
- Updated global exception handlers
- Refactored YouTube service to use custom exceptions
- Refactored storage service to use custom exceptions
- Added timeout handling to subprocess calls
- Added tests for error handling
- Improved error logging with context"
```

---

## Success Metrics

✅ **Complete** if:
- 10+ custom exception classes defined
- All services using custom exceptions
- Global exception handlers working
- Error responses include error codes
- Timeouts configured for all long-running operations
- Tests passing

## Tomorrow Preview

**Day 3**: Add monitoring with Prometheus metrics
- Install prometheus-client
- Create metrics middleware
- Add custom metrics for downloads, storage, errors
- Create Grafana dashboard configuration
