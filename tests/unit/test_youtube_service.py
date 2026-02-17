"""
Unit tests for YouTube service
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.youtube_service import YouTubeService
from app.models.download import VideoInfo
import json

class TestYouTubeService:
    """Test YouTube service functionality"""

    @pytest.fixture
    def youtube_service(self):
        """Create YouTube service instance"""
        return YouTubeService()

    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_authentication_with_valid_cookies(self, mock_run, youtube_service):
        """Test that valid cookies enable successful authentication"""
        # Simulate successful authentication with cookies
        valid_cookies = {
            "LOGIN_INFO": "valid_session_token",
            "VISITOR_INFO1_LIVE": "valid_visitor_token"
        }

        mock_stdout = json.dumps({
            "id": "authenticated_video",
            "title": "Members Only Video",
            "thumbnail": "https://i.ytimg.com/vi/test/maxresdefault.jpg",
            "duration": 120,
            "height": 1080
        })

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_stdout
        )

        result = await youtube_service.get_video_info(
            "https://youtube.com/shorts/authenticated_video",
            cookies=valid_cookies
        )

        assert result.id == "authenticated_video"
        # Verify cookies were used in the command
        call_args = mock_run.call_args[0][0]
        assert any('--cookies' in str(arg) for arg in call_args)

    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_fallback_without_cookies(self, mock_run, youtube_service):
        """Test that system falls back to mobile clients without cookies"""
        mock_stdout = json.dumps({
            "id": "public_video",
            "title": "Public Video",
            "thumbnail": "https://i.ytimg.com/vi/test/maxresdefault.jpg",
            "duration": 60,
            "height": 720
        })

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_stdout
        )

        result = await youtube_service.get_video_info(
            "https://youtube.com/shorts/public_video"
        )

        assert result.id == "public_video"
        # Verify mobile client extractor args were used when no cookies
        call_args = mock_run.call_args[0][0]
        assert any('youtube:player_client=android,ios' in str(arg) for arg in call_args)

    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_get_video_info_success(self, mock_run, youtube_service):
        """Test successful video info retrieval"""
        # Mock subprocess response with all required fields
        mock_stdout = json.dumps({
            "id": "test_video_123",
            "title": "Test Video Title",
            "thumbnail": "https://i.ytimg.com/vi/test_video_123/maxresdefault.jpg",
            "duration": 60,
            "height": 1080,
            "filesize": 10485760
        })

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_stdout,
            stderr=""
        )

        result = await youtube_service.get_video_info(
            "https://youtube.com/shorts/test_video_123"
        )

        assert isinstance(result, VideoInfo)
        assert result.id == "test_video_123"
        assert result.title == "Test Video Title"
        assert result.duration == 60
        assert result.quality == "1080p"
        assert mock_run.called

    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_get_video_info_with_cookies(self, mock_run, youtube_service):
        """Test video info retrieval with cookies"""
        cookies = {"LOGIN_INFO": "test_value"}

        mock_stdout = json.dumps({
            "id": "test_video_456",
            "title": "Test Video",
            "thumbnail": "https://example.com/thumb.jpg",
            "duration": 30,
            "height": 720
        })

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_stdout
        )

        result = await youtube_service.get_video_info(
            "https://youtube.com/shorts/test_video_456",
            cookies=cookies
        )

        assert result.id == "test_video_456"
        # Verify --cookies was passed in command
        call_args = mock_run.call_args[0][0]
        assert any('--cookies' in str(arg) for arg in call_args)

    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_get_video_info_failure(self, mock_run, youtube_service):
        """Test video info retrieval failure"""
        from app.exceptions import VideoDownloadError

        # Mock subprocess error
        mock_run.side_effect = Exception("yt-dlp command failed")

        with pytest.raises(VideoDownloadError) as exc_info:
            await youtube_service.get_video_info(
                "https://youtube.com/shorts/dQw4w9WgXcQ"
            )

        assert exc_info.value.error_code == "VIDEO_DOWNLOAD_FAILED"
        assert "dQw4w9WgXcQ" in exc_info.value.details["video_id"]

    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_get_video_info_invalid_json(self, mock_run, youtube_service):
        """Test handling of invalid JSON response"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="invalid json {{{",
            stderr=""
        )

        with pytest.raises(Exception):
            await youtube_service.get_video_info(
                "https://youtube.com/shorts/test"
            )

    def test_format_file_size_bytes(self, youtube_service):
        """Test file size formatting"""
        assert youtube_service._format_file_size(0) == "0 Bytes"
        assert youtube_service._format_file_size(1023) == "1023.0 Bytes"

    def test_format_file_size_kb(self, youtube_service):
        """Test KB formatting"""
        size = youtube_service._format_file_size(1024)
        assert "1.0 KB" in size or "1024.0 Bytes" in size

    def test_format_file_size_mb(self, youtube_service):
        """Test MB formatting"""
        size = youtube_service._format_file_size(1048576)  # 1 MB
        assert "1.0 MB" in size or "1024.0 KB" in size
