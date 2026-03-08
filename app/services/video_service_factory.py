"""
Video Service Factory

Factory pattern to get the appropriate video service based on URL/platform.
"""

from typing import Union

from app.utils.platform_detector import Platform, detect_platform
from app.services.base_video_service import BaseVideoService
from app.services.youtube_service import youtube_service
from app.services.tiktok_service import tiktok_service
from app.services.instagram_service import instagram_service
from app.exceptions import InvalidVideoURLError


class VideoServiceFactory:
    """
    Factory class to get the appropriate video service based on platform.

    Uses singleton instances of each service to avoid redundant initialization.
    """

    _services = {
        Platform.YOUTUBE: youtube_service,
        Platform.TIKTOK: tiktok_service,
        Platform.INSTAGRAM: instagram_service,
    }

    @classmethod
    def get_service(cls, url: str) -> BaseVideoService:
        """
        Get the appropriate video service for a URL.

        Args:
            url: The video URL

        Returns:
            The appropriate video service instance

        Raises:
            InvalidVideoURLError: If the URL is not from a supported platform
        """
        platform = detect_platform(url)

        if platform == Platform.UNKNOWN:
            raise InvalidVideoURLError(
                url,
                "URL not supported. Please provide a YouTube Shorts, TikTok, or Instagram URL."
            )

        return cls._services[platform]

    @classmethod
    def get_service_by_platform(cls, platform: Platform) -> BaseVideoService:
        """
        Get service by platform enum directly.

        Args:
            platform: The Platform enum value

        Returns:
            The appropriate video service instance

        Raises:
            InvalidVideoURLError: If the platform is not supported
        """
        if platform == Platform.UNKNOWN or platform not in cls._services:
            raise InvalidVideoURLError(
                "",
                f"Platform '{platform}' is not supported."
            )

        return cls._services[platform]

    @classmethod
    def get_platform(cls, url: str) -> Platform:
        """
        Get the platform for a URL without getting the service.

        Args:
            url: The video URL

        Returns:
            The Platform enum value
        """
        return detect_platform(url)

    @classmethod
    def is_supported(cls, url: str) -> bool:
        """
        Check if a URL is from a supported platform.

        Args:
            url: The video URL

        Returns:
            True if the URL is supported, False otherwise
        """
        return detect_platform(url) != Platform.UNKNOWN


# Convenience function for direct import
def get_video_service(url: str) -> BaseVideoService:
    """Get the appropriate video service for a URL."""
    return VideoServiceFactory.get_service(url)


def get_platform(url: str) -> Platform:
    """Get the platform for a URL."""
    return VideoServiceFactory.get_platform(url)
