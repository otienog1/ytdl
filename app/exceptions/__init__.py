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


class CookieUnavailableError(YouTubeError):
    """Raised when cookies are unavailable on this server - triggers load balancer failover"""

    def __init__(self, account_id: str, reason: str = "cookies_unavailable"):
        super().__init__(
            message="Authentication cookies unavailable on this server. Please retry your request.",
            error_code="COOKIES_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={
                "account_id": account_id,
                "reason": reason,
                "retry": True,
                "message": "This server is refreshing authentication. Your request will be automatically retried on another server."
            }
        )
