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

    def test_video_download_error(self):
        """Test VideoDownloadError"""
        exc = VideoDownloadError("xyz789", "Network timeout")

        assert exc.error_code == "VIDEO_DOWNLOAD_FAILED"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.details["video_id"] == "xyz789"
        assert exc.details["reason"] == "Network timeout"

    def test_storage_provider_not_available_error(self):
        """Test StorageProviderNotAvailableError"""
        exc = StorageProviderNotAvailableError()

        assert exc.error_code == "STORAGE_FULL"
        assert exc.status_code == status.HTTP_507_INSUFFICIENT_STORAGE
        assert "capacity" in exc.message.lower()

    def test_file_upload_error(self):
        """Test FileUploadError"""
        exc = FileUploadError("gcs", "Permission denied")

        assert exc.error_code == "FILE_UPLOAD_FAILED"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.details["provider"] == "gcs"
        assert exc.details["reason"] == "Permission denied"

    def test_file_not_found_error(self):
        """Test FileNotFoundError"""
        exc = FileNotFoundError("video.mp4", "s3")

        assert exc.error_code == "FILE_NOT_FOUND"
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.details["file_name"] == "video.mp4"
        assert exc.details["provider"] == "s3"

    def test_rate_limit_error(self):
        """Test RateLimitError"""
        exc = RateLimitError(60)

        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc.details["retry_after_seconds"] == 60

    def test_database_error(self):
        """Test DatabaseError"""
        exc = DatabaseError("insert", "Connection refused")

        assert exc.error_code == "DATABASE_ERROR"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.details["operation"] == "insert"
        assert exc.details["reason"] == "Connection refused"

    def test_exception_to_dict(self):
        """Test exception serialization"""
        exc = InvalidVideoURLError("https://test.com")
        result = exc.to_dict()

        assert "error" in result
        assert result["error"]["code"] == "INVALID_VIDEO_URL"
        assert result["error"]["message"]
        assert result["error"]["details"]
        assert result["error"]["details"]["url"] == "https://test.com"

    def test_validation_error(self):
        """Test ValidationError"""
        exc = ValidationError("Invalid input", {"field": "url", "issue": "required"})

        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.details["field"] == "url"
        assert exc.details["issue"] == "required"
