import re
from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional, Dict


YOUTUBE_SHORTS_PATTERNS = [
    r'^https?://(www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})(\?.*)?$',
    r'^https?://youtu\.be/([a-zA-Z0-9_-]{11})(\?.*)?$',
]


class DownloadRequest(BaseModel):
    url: HttpUrl
    cookies: Optional[Dict[str, str]] = None  # Optional YouTube cookies from frontend
    user_id: Optional[str] = None  # Firebase user ID for authenticated users

    @field_validator('url')
    @classmethod
    def validate_youtube_shorts_url(cls, v):
        url_str = str(v)
        if not any(re.match(pattern, url_str) for pattern in YOUTUBE_SHORTS_PATTERNS):
            raise ValueError('Please provide a valid YouTube Shorts URL')
        return v


def extract_video_id(url: str) -> str | None:
    """Extract video ID from YouTube Shorts URL"""
    for pattern in YOUTUBE_SHORTS_PATTERNS:
        match = re.match(pattern, url)
        if match:
            # For youtube.com/shorts/, video ID is in group 2 (after optional www. in group 1)
            # For youtu.be/, video ID is in group 1
            return match.group(2) if match.lastindex >= 2 and match.group(2) else match.group(1)
    return None


def is_valid_youtube_shorts_url(url: str) -> bool:
    """Check if URL is a valid YouTube Shorts URL"""
    try:
        DownloadRequest(url=url)
        return True
    except:
        return False
