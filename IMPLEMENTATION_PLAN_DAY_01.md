# Day 1: Testing Infrastructure & Basic Unit Tests

**Goal**: Set up testing infrastructure and create core unit tests
**Estimated Time**: 6-8 hours
**Priority**: HIGH - Foundation for all future improvements

---

## Morning Session (3-4 hours)

### Task 1.1: Set up pytest infrastructure (45 min)

**Step 1**: Install testing dependencies
```bash
cd backend-python
pipenv install --dev pytest pytest-asyncio pytest-cov pytest-mock httpx faker
```

**Step 2**: Create pytest configuration
```bash
# Create pytest.ini
touch pytest.ini
```

**File: `backend-python/pytest.ini`**
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=app
    --cov-report=html
    --cov-report=term-missing
```

**Step 3**: Create test directory structure
```bash
mkdir -p tests/{unit,integration,fixtures}
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/fixtures/__init__.py
```

**Checkpoint**: Run `pipenv run pytest` - should show "no tests collected"

---

### Task 1.2: Create test fixtures (30 min)

**File: `backend-python/tests/fixtures/video_data.py`**
```python
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
```

**File: `backend-python/tests/conftest.py`**
```python
"""
Global pytest configuration and fixtures
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from motor.motor_asyncio import AsyncIOMotorClient

@pytest.fixture
def mock_db():
    """Mock MongoDB database"""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_client.get_database.return_value = mock_db
    return mock_db

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock_redis = AsyncMock()
    return mock_redis

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
```

**Checkpoint**: Import fixtures in a test to verify they work

---

### Task 1.3: Write YouTube service tests (90 min)

**File: `backend-python/tests/unit/test_youtube_service.py`**
```python
"""
Unit tests for YouTube service
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.youtube_service import YouTubeService

class TestYouTubeService:
    """Test YouTube service functionality"""

    @pytest.fixture
    def youtube_service(self):
        """Create YouTube service instance"""
        return YouTubeService()

    def test_extract_video_id_valid_shorts_url(self, youtube_service):
        """Test extracting video ID from valid Shorts URL"""
        url = "https://youtube.com/shorts/abc123def"
        video_id = youtube_service._extract_video_id(url)
        assert video_id == "abc123def"

    def test_extract_video_id_valid_watch_url(self, youtube_service):
        """Test extracting video ID from valid watch URL"""
        url = "https://www.youtube.com/watch?v=xyz789ghi"
        video_id = youtube_service._extract_video_id(url)
        assert video_id == "xyz789ghi"

    def test_extract_video_id_invalid_url(self, youtube_service):
        """Test extracting video ID from invalid URL"""
        url = "https://notayoutubeurl.com/video"
        video_id = youtube_service._extract_video_id(url)
        assert video_id is None

    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_get_video_info_success(self, mock_run, youtube_service, sample_video_info):
        """Test successful video info retrieval"""
        # Mock subprocess response
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"id": "test_video_123", "title": "Test Video Title", "duration": 60}'
        )

        result = await youtube_service.get_video_info(
            "https://youtube.com/shorts/test_video_123"
        )

        assert result.id == "test_video_123"
        assert result.title == "Test Video Title"
        assert result.duration == 60

    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_get_video_info_failure(self, mock_run, youtube_service):
        """Test video info retrieval failure"""
        # Mock subprocess error
        mock_run.side_effect = Exception("yt-dlp error")

        with pytest.raises(Exception) as exc_info:
            await youtube_service.get_video_info(
                "https://youtube.com/shorts/invalid"
            )

        assert "Failed to fetch video info" in str(exc_info.value)
```

**Checkpoint**: Run `pipenv run pytest tests/unit/test_youtube_service.py -v`

---

## Afternoon Session (3-4 hours)

### Task 1.4: Write storage service tests (90 min)

**File: `backend-python/tests/unit/test_storage_service.py`**
```python
"""
Unit tests for storage service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.storage_service import MultiStorageService

class TestMultiStorageService:
    """Test multi-cloud storage service"""

    @pytest.fixture
    def storage_service(self):
        """Create storage service instance"""
        return MultiStorageService()

    @pytest.mark.asyncio
    @patch('app.services.storage_tracker.storage_tracker')
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
    @patch('app.services.storage_tracker.storage_tracker')
    async def test_select_random_provider_none_available(
        self, mock_tracker, storage_service
    ):
        """Test provider selection when no providers are available"""
        mock_tracker.get_available_providers_under_limit = AsyncMock(
            return_value=[]
        )

        provider = await storage_service.select_random_provider()

        assert provider is None

    @pytest.mark.asyncio
    @patch('app.config.multi_storage.multi_storage')
    async def test_regenerate_signed_url_gcs(self, mock_multi, storage_service):
        """Test GCS signed URL regeneration"""
        mock_blob = MagicMock()
        mock_blob.generate_signed_url.return_value = "https://storage.googleapis.com/signed-url"
        mock_multi.get_gcs_bucket.return_value.blob.return_value = mock_blob

        url = await storage_service.regenerate_signed_url("test.mp4", "gcs")

        assert url.startswith("https://storage.googleapis.com")
        mock_blob.generate_signed_url.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.config.multi_storage.multi_storage')
    async def test_delete_file_success(self, mock_multi, storage_service):
        """Test successful file deletion"""
        mock_blob = MagicMock()
        mock_multi.get_gcs_bucket.return_value.blob.return_value = mock_blob

        await storage_service.delete_file("test.mp4", "gcs")

        mock_blob.delete.assert_called_once()
```

**Checkpoint**: Run `pipenv run pytest tests/unit/test_storage_service.py -v`

---

### Task 1.5: Write storage tracker tests (60 min)

**File: `backend-python/tests/unit/test_storage_tracker.py`**
```python
"""
Unit tests for storage tracker
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.storage_tracker import StorageTracker

class TestStorageTracker:
    """Test storage tracking functionality"""

    @pytest.fixture
    def tracker(self):
        """Create storage tracker instance"""
        return StorageTracker()

    @pytest.mark.asyncio
    async def test_add_file_usage(self, tracker, mock_db):
        """Test adding file usage"""
        mock_db.storage_stats.update_one = AsyncMock()
        mock_db.storage_stats.find_one = AsyncMock(
            return_value={
                "provider": "gcs",
                "total_size_bytes": 1000000,
                "file_count": 1,
                "is_full": False
            }
        )

        with patch('app.services.storage_tracker.db', mock_db):
            await tracker.add_file_usage("gcs", 500000, "test.mp4")

        mock_db.storage_stats.update_one.assert_called()

    @pytest.mark.asyncio
    async def test_get_available_providers_under_limit(self, tracker, mock_db):
        """Test getting available providers under limit"""
        mock_db.storage_stats.find_one = AsyncMock(
            side_effect=[
                {"provider": "gcs", "is_full": False},
                {"provider": "azure", "is_full": True},
                {"provider": "s3", "is_full": False}
            ]
        )

        with patch('app.services.storage_tracker.db', mock_db):
            with patch('app.config.multi_storage.multi_storage.get_available_providers', return_value=['gcs', 'azure', 's3']):
                providers = await tracker.get_available_providers_under_limit()

        assert 'gcs' in providers
        assert 's3' in providers
        assert 'azure' not in providers
```

**Checkpoint**: Run `pipenv run pytest tests/unit/ -v --cov=app/services`

---

### Task 1.6: Run full test suite and generate coverage (30 min)

**Step 1**: Run all tests
```bash
cd backend-python
pipenv run pytest tests/ -v
```

**Step 2**: Generate coverage report
```bash
pipenv run pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

**Step 3**: View coverage report
```bash
# Open htmlcov/index.html in browser
start htmlcov/index.html  # Windows
# or
open htmlcov/index.html   # Mac/Linux
```

**Step 4**: Document coverage baseline
```bash
# Create TESTING.md
touch TESTING.md
```

**File: `backend-python/TESTING.md`**
```markdown
# Testing Documentation

## Running Tests

### All tests
```bash
pipenv run pytest
```

### Specific test file
```bash
pipenv run pytest tests/unit/test_youtube_service.py
```

### With coverage
```bash
pipenv run pytest --cov=app --cov-report=html
```

## Current Coverage

| Module | Coverage |
|--------|----------|
| services/youtube_service.py | XX% |
| services/storage_service.py | XX% |
| services/storage_tracker.py | XX% |

**Target**: 80% coverage for all services

## Test Structure

```
tests/
├── conftest.py          # Global fixtures
├── fixtures/            # Test data
│   └── video_data.py
├── unit/               # Unit tests
│   ├── test_youtube_service.py
│   ├── test_storage_service.py
│   └── test_storage_tracker.py
└── integration/        # Integration tests (TODO)
```
```

---

## End of Day Checklist

- [ ] pytest installed and configured
- [ ] Test directory structure created
- [ ] Global fixtures configured
- [ ] YouTube service tests written (5+ tests)
- [ ] Storage service tests written (4+ tests)
- [ ] Storage tracker tests written (2+ tests)
- [ ] All tests passing
- [ ] Coverage report generated
- [ ] TESTING.md documentation created
- [ ] Code committed to git

**Git Commit**:
```bash
git add .
git commit -m "Day 1: Add testing infrastructure and unit tests

- Set up pytest with asyncio support
- Created test fixtures for video data
- Added unit tests for YouTube service
- Added unit tests for storage service
- Added unit tests for storage tracker
- Generated coverage reports
- Current coverage: XX%

Target: 80% coverage"
```

---

## Success Metrics

✅ **Complete** if:
- At least 15 tests written and passing
- Coverage > 50% for tested modules
- Can run `pipenv run pytest` successfully
- Coverage HTML report generated

## Tomorrow Preview

**Day 2**: Structured error handling and custom exceptions
- Create custom exception hierarchy
- Add error codes and context
- Implement global exception handlers
- Add error logging with context
