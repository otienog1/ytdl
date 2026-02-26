# Testing Documentation

## Running Tests

### All tests
```bash
cd backend-python
pipenv run pytest
```

### Specific test file
```bash
pipenv run pytest tests/unit/test_youtube_service.py
pipenv run pytest tests/unit/test_storage_service.py
```

### With coverage
```bash
pipenv run pytest --cov=app --cov-report=html
```

### View coverage report
```bash
# Open in browser
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac/Linux
```

## Current Coverage

| Module | Coverage | Tests |
|--------|----------|-------|
| services/youtube_service.py | 52% | 9 tests |
| services/storage_service.py | 43% | 9 tests |
| exceptions/__init__.py | 100% | 10 tests |
| **Overall** | **35%** | **28 tests** |

**Target**: 80% coverage for all services

## Test Structure

```
tests/
├── conftest.py          # Global fixtures
├── fixtures/            # Test data
│   └── video_data.py   # Video info fixtures
├── unit/               # Unit tests
│   ├── test_youtube_service.py  (9 tests)
│   ├── test_storage_service.py  (9 tests)
│   └── __init__.py
└── integration/        # Integration tests (TODO)
```

## Test Fixtures

### Available Fixtures
- `sample_video_info` - Sample YouTube video metadata
- `sample_download` - Complete download record
- `sample_cookies` - YouTube authentication cookies
- `mock_db` - Mocked MongoDB database
- `mock_redis` - Mocked Redis client
- `event_loop` - Asyncio event loop for async tests

## Test Coverage by Module

### YouTube Service (55% coverage)
- ✅ Temporary cookies file creation
- ✅ Video info retrieval (success/failure)
- ✅ Video info with authentication cookies
- ✅ Invalid JSON handling
- ✅ File size formatting

### Storage Service (50% coverage)
- ✅ Random provider selection (all/one/none available)
- ✅ Filename generation (with/without extension)
- ✅ File upload to GCS
- ✅ File deletion with tracking
- ✅ Storage provider management

## Running Specific Test Classes

```bash
# Run only YouTube service tests
pipenv run pytest tests/unit/test_youtube_service.py::TestYouTubeService -v

# Run only storage service tests
pipenv run pytest tests/unit/test_storage_service.py::TestMultiStorageService -v
```

## Running with Different Verbosity

```bash
# Quiet mode
pipenv run pytest -q

# Verbose mode
pipenv run pytest -v

# Very verbose mode
pipenv run pytest -vv
```

## Continuous Integration

Tests should be run before:
1. Creating pull requests
2. Merging to main branch
3. Deploying to production

## Next Steps

- [ ] Add integration tests
- [ ] Increase coverage to 60%+ (Day 2)
- [ ] Add tests for error scenarios (Day 2)
- [ ] Add tests for routes/endpoints
- [ ] Add tests for Celery tasks

## Troubleshooting

### Import Errors
- Ensure virtual environment is activated: `pipenv shell`
- Reinstall dependencies: `pipenv install --dev`

### Test Failures
- Check if services are running (MongoDB, Redis)
- Verify environment variables in `.env`
- Clear pytest cache: `pipenv run pytest --cache-clear`

### Async Test Issues
- Ensure `pytest-asyncio` is installed
- Check `pytest.ini` has `asyncio_mode = auto`
