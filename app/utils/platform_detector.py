"""
Platform Detection Module

Detects the video platform (YouTube, TikTok, Instagram) from a URL.
"""

import re
from enum import Enum
from typing import Optional


class Platform(str, Enum):
    """Supported video platforms."""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    UNKNOWN = "unknown"


# URL patterns for each platform
PLATFORM_PATTERNS = {
    Platform.YOUTUBE: [
        # YouTube Shorts
        r'^https?://(www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})(\?.*)?$',
        # Short youtu.be links
        r'^https?://youtu\.be/([a-zA-Z0-9_-]{11})(\?.*)?$',
    ],
    Platform.TIKTOK: [
        # Standard TikTok video URL
        r'^https?://(www\.)?tiktok\.com/@[\w.-]+/video/(\d+)(\?.*)?$',
        # Short vm.tiktok.com links
        r'^https?://vm\.tiktok\.com/[\w]+/?(\?.*)?$',
        # Mobile t.tiktok.com links
        r'^https?://(www\.)?tiktok\.com/t/[\w]+/?(\?.*)?$',
        # Generic tiktok.com with video
        r'^https?://(www\.)?tiktok\.com/.*/video/(\d+)(\?.*)?$',
    ],
    Platform.INSTAGRAM: [
        # Instagram posts
        r'^https?://(www\.)?instagram\.com/p/[\w-]+/?(\?.*)?$',
        # Instagram reels (singular)
        r'^https?://(www\.)?instagram\.com/reel/[\w-]+/?(\?.*)?$',
        # Instagram reels (plural)
        r'^https?://(www\.)?instagram\.com/reels/[\w-]+/?(\?.*)?$',
        # Instagram stories
        r'^https?://(www\.)?instagram\.com/stories/[\w.-]+/\d+/?(\?.*)?$',
        # Instagram TV (IGTV)
        r'^https?://(www\.)?instagram\.com/tv/[\w-]+/?(\?.*)?$',
    ],
}


def detect_platform(url: str) -> Platform:
    """
    Detect the video platform from a URL.

    Args:
        url: The video URL to analyze

    Returns:
        Platform enum value (YOUTUBE, TIKTOK, INSTAGRAM, or UNKNOWN)
    """
    if not url:
        return Platform.UNKNOWN

    url = url.strip()

    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return platform

    return Platform.UNKNOWN


def is_supported_url(url: str) -> bool:
    """
    Check if a URL is from a supported platform.

    Args:
        url: The video URL to check

    Returns:
        True if the URL is from YouTube, TikTok, or Instagram
    """
    return detect_platform(url) != Platform.UNKNOWN


def get_supported_platforms() -> list[str]:
    """
    Get list of supported platform names.

    Returns:
        List of platform names (lowercase)
    """
    return [p.value for p in Platform if p != Platform.UNKNOWN]


def extract_video_id(url: str, platform: Optional[Platform] = None) -> Optional[str]:
    """
    Extract video ID from URL based on platform.

    Args:
        url: The video URL
        platform: Optional platform (will be detected if not provided)

    Returns:
        Video ID string or None if extraction fails
    """
    if platform is None:
        platform = detect_platform(url)

    if platform == Platform.YOUTUBE:
        # YouTube Shorts: youtube.com/shorts/{ID}
        match = re.search(r'/shorts/([a-zA-Z0-9_-]{11})', url)
        if match:
            return match.group(1)
        # youtu.be/{ID}
        match = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', url)
        if match:
            return match.group(1)

    elif platform == Platform.TIKTOK:
        # TikTok: /video/{numeric_id}
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)
        # For short URLs, return a hash (yt-dlp will resolve)
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:16]

    elif platform == Platform.INSTAGRAM:
        # Instagram: /p/{shortcode} or /reel/{shortcode}
        match = re.search(r'/(p|reel|reels|tv)/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(2)
        # Stories: /stories/{username}/{story_id}
        match = re.search(r'/stories/[\w.-]+/(\d+)', url)
        if match:
            return match.group(1)

    return None
