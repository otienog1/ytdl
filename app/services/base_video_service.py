"""
Base Video Service Interface

Abstract base class defining the interface for all platform-specific video services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Callable, Any
from app.models.download import VideoInfo


class BaseVideoService(ABC):
    """
    Abstract base class for video download services.

    All platform-specific services (YouTube, TikTok, Instagram) must implement
    this interface to ensure consistent behavior across the application.
    """

    @abstractmethod
    async def get_video_info(
        self,
        url: str,
        cookies: Optional[Dict[str, str]] = None
    ) -> VideoInfo:
        """
        Retrieve video metadata without downloading.

        Args:
            url: The video URL
            cookies: Optional cookies for authenticated access

        Returns:
            VideoInfo object with video metadata

        Raises:
            VideoNotFoundError: If video doesn't exist
            VideoUnavailableError: If video is private/restricted
            PlatformError: For platform-specific errors
        """
        pass

    @abstractmethod
    def download_video_sync(
        self,
        url: str,
        video_id: str,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        cookies: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Download video to local filesystem (synchronous for Celery).

        Args:
            url: The video URL
            video_id: Unique identifier for the video
            progress_callback: Optional callback(progress_percent, status_message)
            cookies: Optional cookies for authenticated access

        Returns:
            Path to the downloaded video file

        Raises:
            DownloadError: If download fails
            VideoUnavailableError: If video becomes unavailable during download
        """
        pass

    @abstractmethod
    def extract_video_id(self, url: str) -> str:
        """
        Extract the platform-specific video ID from a URL.

        Args:
            url: The video URL

        Returns:
            Video ID string

        Raises:
            InvalidURLError: If URL format is invalid
        """
        pass

    def get_platform_name(self) -> str:
        """
        Get the platform name for this service.

        Returns:
            Platform name (e.g., 'youtube', 'tiktok', 'instagram')
        """
        return self.__class__.__name__.replace('Service', '').lower()

    def supports_cookies(self) -> bool:
        """
        Check if this platform supports/requires cookies.

        Returns:
            True if cookies can be used for authenticated access
        """
        return True

    def get_yt_dlp_options(self, cookies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Get base yt-dlp options common to all platforms.

        Args:
            cookies: Optional cookies dict

        Returns:
            Dictionary of yt-dlp options
        """
        return {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
        }
