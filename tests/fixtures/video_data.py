"""
Test fixtures for video data
"""
import pytest
from datetime import datetime

@pytest.fixture
def sample_video_info():
    """Sample YouTube video info"""
    return {
        "id": "test_video_123",
        "title": "Test Video Title",
        "thumbnail": "https://i.ytimg.com/vi/test_video_123/maxresdefault.jpg",
        "duration": 60,
        "quality": "1080p"
    }

@pytest.fixture
def sample_download():
    """Sample download record"""
    return {
        "jobId": "test-job-123",
        "url": "https://youtube.com/shorts/test_video_123",
        "status": "completed",
        "progress": 100,
        "videoInfo": {
            "id": "test_video_123",
            "title": "Test Video Title",
            "thumbnail": "https://i.ytimg.com/vi/test_video_123/maxresdefault.jpg",
            "duration": 60,
            "quality": "1080p"
        },
        "downloadUrl": "https://storage.googleapis.com/test-bucket/test_video.mp4",
        "storageProvider": "gcs",
        "fileSize": 10485760,  # 10MB
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }

@pytest.fixture
def sample_cookies():
    """Sample YouTube cookies"""
    return {
        "LOGIN_INFO": "test_login_info",
        "VISITOR_INFO1_LIVE": "test_visitor_info"
    }
