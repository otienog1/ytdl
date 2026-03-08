"""
URL Validation Module

Validates video URLs and extracts video IDs for all supported platforms.
"""

import re
from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional, Dict

from app.utils.platform_detector import (
    Platform,
    detect_platform,
    is_supported_url,
    extract_video_id as platform_extract_video_id
)


class DownloadRequest(BaseModel):
    """Request model for video downloads."""
    url: HttpUrl
    cookies: Optional[Dict[str, str]] = None  # Optional cookies for authenticated content
    user_id: Optional[str] = None  # Firebase user ID for authenticated users

    @field_validator('url')
    @classmethod
    def validate_video_url(cls, v):
        """Validate that URL is from a supported platform."""
        url_str = str(v)
        if not is_supported_url(url_str):
            raise ValueError(
                'Please provide a valid video URL (YouTube Shorts, TikTok, or Instagram)'
            )
        return v


def extract_video_id(url: str) -> str | None:
    """
    Extract video ID from URL (any supported platform).

    Args:
        url: The video URL

    Returns:
        Video ID string or None if extraction fails
    """
    return platform_extract_video_id(url)


def is_valid_video_url(url: str) -> bool:
    """
    Check if URL is valid for any supported platform.

    Args:
        url: The video URL to check

    Returns:
        True if the URL is from a supported platform
    """
    return is_supported_url(url)


def get_platform(url: str) -> Platform:
    """
    Get the platform for a URL.

    Args:
        url: The video URL

    Returns:
        Platform enum value
    """
    return detect_platform(url)


# Legacy aliases for backwards compatibility
YOUTUBE_SHORTS_PATTERNS = [
    r'^https?://(www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})(\?.*)?$',
    r'^https?://youtu\.be/([a-zA-Z0-9_-]{11})(\?.*)?$',
]


def is_valid_youtube_shorts_url(url: str) -> bool:
    """Legacy function for YouTube Shorts validation."""
    platform = detect_platform(url)
    return platform == Platform.YOUTUBE
