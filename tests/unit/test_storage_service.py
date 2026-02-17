"""
Unit tests for storage service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.storage_service import MultiStorageService
import os
import tempfile

class TestMultiStorageService:
    """Test multi-cloud storage service"""

    @pytest.fixture
    def storage_service(self):
        """Create storage service instance"""
        return MultiStorageService()

    @pytest.mark.asyncio
    @patch('app.services.storage_service.storage_tracker')
    async def test_select_random_provider_all_available(
        self, mock_tracker, storage_service
    ):
        """Test provider selection when all providers are available"""
        mock_tracker.get_available_providers_under_limit = AsyncMock(
            return_value=['gcs', 'azure', 's3']
        )

        provider = await storage_service.select_random_provider()

        assert provider in ['gcs', 'azure', 's3']

    @pytest.mark.asyncio
    @patch('app.services.storage_service.storage_tracker')
    async def test_select_random_provider_one_available(
        self, mock_tracker, storage_service
    ):
        """Test provider selection when only one provider is available"""
        mock_tracker.get_available_providers_under_limit = AsyncMock(
            return_value=['gcs']
        )

        provider = await storage_service.select_random_provider()

        assert provider == 'gcs'

    @pytest.mark.asyncio
    @patch('app.services.storage_service.storage_tracker')
    async def test_select_random_provider_none_available(
        self, mock_tracker, storage_service
    ):
        """Test provider selection when no providers are available"""
        from app.exceptions import StorageProviderNotAvailableError

        mock_tracker.get_available_providers_under_limit = AsyncMock(
            return_value=[]
        )

        with pytest.raises(StorageProviderNotAvailableError) as exc_info:
            await storage_service.select_random_provider()

        assert exc_info.value.error_code == "STORAGE_FULL"

    def test_generate_filename_with_extension(self, storage_service):
        """Test filename generation with extension"""
        filename = storage_service._generate_filename("test_video.mp4")

        assert filename.startswith("test_video_")
        assert filename.endswith(".mp4")
        assert len(filename) > len("test_video_.mp4")  # Has unique ID

    def test_generate_filename_without_extension(self, storage_service):
        """Test filename generation without extension"""
        filename = storage_service._generate_filename("test_video")

        assert filename.startswith("test_video_")
        assert len(filename) > len("test_video_")  # Has unique ID

    def test_generate_filename_none(self, storage_service):
        """Test filename generation with None"""
        filename = storage_service._generate_filename(None)

        assert filename.endswith(".mp4")
        assert len(filename) > 4  # Has unique ID plus .mp4

    @pytest.mark.asyncio
    @patch('app.services.storage_service.storage_tracker')
    @patch('app.services.storage_service.multi_storage')
    async def test_delete_file_gcs_success(self, mock_multi, mock_tracker, storage_service):
        """Test successful GCS file deletion"""
        mock_blob = MagicMock()
        mock_blob.size = None  # No size tracking needed
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_multi.get_gcs_bucket.return_value = mock_bucket
        mock_tracker.remove_file_usage = AsyncMock()

        await storage_service.delete_file("test.mp4", "gcs")

        mock_blob.delete.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.storage_service.storage_tracker')
    @patch('app.services.storage_service.multi_storage')
    async def test_delete_file_with_tracking(self, mock_multi, mock_tracker, storage_service):
        """Test file deletion with storage tracking"""
        mock_blob = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_blob.size = 1048576  # 1 MB
        mock_multi.get_gcs_bucket.return_value = mock_bucket
        mock_tracker.remove_file_usage = AsyncMock()

        await storage_service.delete_file("test.mp4", "gcs")

        mock_tracker.remove_file_usage.assert_called()

    @pytest.mark.asyncio
    @patch('app.services.storage_service.storage_tracker')
    @patch('app.services.storage_service.multi_storage')
    async def test_upload_file_gcs(self, mock_multi, mock_tracker, storage_service):
        """Test file upload to GCS"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.mp4') as tf:
            tf.write("test content")
            temp_file = tf.name

        try:
            mock_blob = MagicMock()
            mock_blob.generate_signed_url.return_value = "https://storage.googleapis.com/test-bucket/video.mp4"
            mock_bucket = MagicMock()
            mock_bucket.blob.return_value = mock_blob
            mock_multi.get_gcs_bucket.return_value = mock_bucket

            mock_tracker.get_available_providers_under_limit = AsyncMock(
                return_value=['gcs']
            )
            mock_tracker.add_file_usage = AsyncMock()

            # Patch timedelta as well
            with patch('app.services.storage_service.timedelta'):
                url, provider, file_size = await storage_service.upload_file(temp_file, "video.mp4")

                assert provider == 'gcs'
                assert file_size > 0
                assert isinstance(url, str)
                mock_tracker.add_file_usage.assert_called_once()
        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.remove(temp_file)
