# YouTube Downloader - Python Backend

FastAPI backend for YouTube video downloader with Celery task queue, multi-cloud storage, and cookie-based authentication.

## Features

- ✅ FastAPI async/await support
- ✅ Celery task queue with Redis
- ✅ Multi-cloud storage (GCS, Azure, AWS S3)
- ✅ Cookie-based YouTube authentication
- ✅ WebSocket real-time progress updates
- ✅ MongoDB for metadata storage
- ✅ Rate limiting and CORS
- ✅ Auto-generated API docs (Swagger)

## Quick Start

### Development (Local)

```bash
# Clone the repository
git clone https://github.com/otienog1/ytdl.git
cd ytdl

# Run automated setup (Windows)
.\start-dev.bat

# Or (macOS/Linux)
./start-dev.sh
```

This automatically:
1. Creates Python virtual environment
2. Installs all dependencies
3. Starts FastAPI server (port 3001)
4. Starts Celery worker

### Production (Server)

```bash
# Run installation script
sudo bash install.sh
```

See [INSTALLATION.md](INSTALLATION.md) for detailed production setup.

## Prerequisites

- Python 3.11+
- Redis server
- MongoDB
- Cloud storage (GCS/Azure/S3)

## Manual Setup

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file (copy from `.env.example`):

```env
# Server
PORT=3001
ENVIRONMENT=development

# Database
MONGODB_URI=mongodb://localhost:27017/ytdl
REDIS_URL=redis://localhost:6379/0

# Storage (choose one or multiple)
GCP_PROJECT_ID=your-project-id
GCP_BUCKET_NAME=your-bucket
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# AZURE_STORAGE_CONNECTION_STRING=your-connection-string
# AZURE_CONTAINER_NAME=your-container

# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
# AWS_BUCKET_NAME=your-bucket
# AWS_REGION=us-east-1

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### 3. Run Services

```bash
# Start FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload

# Start Celery worker (separate terminal)
celery -A app.queue.celery_app worker --loglevel=info --pool=solo

# Optional: Celery monitoring
celery -A app.queue.celery_app flower
```

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /api/health/` - Detailed health with cookies status

### Downloads
- `POST /api/download` - Start download
  ```json
  {"url": "https://youtube.com/watch?v=VIDEO_ID"}
  ```
- `GET /api/status/{job_id}` - Get download status
- `GET /api/history?limit=10` - Download history

### Storage
- `GET /api/storage/stats` - Storage statistics
- `POST /api/storage/sync` - Sync storage across clouds

### Cookies
- `GET /api/cookies/status` - Cookie status
- `POST /api/cookies/refresh` - Refresh cookies

### WebSocket
- `WS /ws/{client_id}` - Real-time progress updates

## Project Structure

```
backend-python/
├── app/
│   ├── config/          # Settings, database, redis, storage
│   ├── models/          # Pydantic models
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic
│   ├── queue/           # Celery tasks
│   ├── middleware/      # Rate limiting, metrics
│   ├── utils/           # Utilities
│   ├── websocket/       # WebSocket handlers
│   └── main.py          # Application entry
├── tests/               # Unit & integration tests
├── requirements.txt     # Python dependencies
├── Pipfile              # Pipenv configuration
└── .env                 # Environment variables
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_youtube_service.py
```

## Production Deployment

### Using systemd

The installation script creates systemd services:

```bash
# Check status
sudo systemctl status ytd-api
sudo systemctl status ytd-celery

# View logs
sudo journalctl -u ytd-api -f
sudo journalctl -u ytd-celery -f

# Restart services
sudo systemctl restart ytd-api ytd-celery
```

### Environment-Specific Configuration

For multi-server setups, use environment-specific config:
- `.env.production.server1` for Server 1
- `.env.production.server2` for Server 2
- `.env.production.server3` for Server 3

## Documentation

- [INSTALLATION.md](INSTALLATION.md) - Production installation guide
- [LOCAL_DEVELOPMENT_SETUP.md](LOCAL_DEVELOPMENT_SETUP.md) - Local dev setup
- [COOKIE_REFRESH_INTEGRATION.md](COOKIE_REFRESH_INTEGRATION.md) - Cookie management
- [DATABASE_CONFIG.md](DATABASE_CONFIG.md) - Database configuration
- [MONITORING.md](MONITORING.md) - Monitoring & metrics
- [SECURITY.md](SECURITY.md) - Security best practices
- [TESTING.md](TESTING.md) - Testing guide

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:3001/docs
- ReDoc: http://localhost:3001/redoc

## Troubleshooting

### Celery won't start on Windows
Use `--pool=solo`:
```bash
celery -A app.queue.celery_app worker --loglevel=info --pool=solo
```

### Redis connection errors
Verify `REDIS_URL` in `.env` and ensure Redis is running:
```bash
redis-cli ping  # Should return PONG
```

### MongoDB connection errors
Check `MONGODB_URI` and network connectivity:
```bash
mongosh "your-mongodb-uri"
```

### Storage upload failures
Verify credentials and bucket permissions for your cloud provider.

## License

MIT
