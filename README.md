# YouTube Shorts Downloader - Python FastAPI Backend

FastAPI backend for YouTube Shorts downloader with Celery task queue.

## Prerequisites

- Python 3.11+
- Redis (using Redis Cloud - already configured)
- MongoDB (using MongoDB Atlas - already configured)
- Google Cloud Storage account (already configured)

**Note**: yt-dlp and ffmpeg will be installed **locally in the project** - no system-wide installation needed!

## Quick Start (Recommended)

The easiest way to get started - everything is automated:

### Windows
```powershell
cd c:\Users\7plus8\build\ytd\backend-python
.\start-dev.bat
```

### macOS/Linux
```bash
cd /path/to/backend-python
./start-dev.sh
```

This will automatically:
1. Create Python virtual environment
2. Install all dependencies (including yt-dlp)
3. Download and setup ffmpeg locally
4. Start FastAPI server on port 3001
5. Start Celery worker for background jobs

**See [LOCAL_INSTALL.md](LOCAL_INSTALL.md) for details on local installation.**

## Manual Installation

### 1. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Local yt-dlp and ffmpeg

**yt-dlp** is already included in `requirements.txt` and will be installed in your virtual environment.

**ffmpeg** can be set up locally (no system installation needed):

```bash
python setup_ffmpeg.py
```

This downloads ffmpeg binaries to `backend-python/bin/` and configures them automatically.

**Alternative**: Install system-wide (not recommended):
- Windows: `winget install Gyan.FFmpeg`
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

### 4. Configure Environment

Create `.env` file (use `.env.example` as template):

```env
MONGODB_URI=your_mongodb_uri
REDIS_URL=your_redis_url
GCP_PROJECT_ID=your_gcp_project
GCP_BUCKET_NAME=your_bucket_name
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
PORT=3001
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000
```

## Running the Application

### Start FastAPI Server

```bash
# Development
uvicorn app.main:app --reload --port 3001

# Or using Python
python -m app.main
```

### Start Celery Worker

In a separate terminal:

```bash
celery -A app.queue.celery_app worker --loglevel=info --pool=solo
```

Note: On Windows, use `--pool=solo` option.

### Optional: Start Flower (Celery Monitoring)

```bash
celery -A app.queue.celery_app flower
```

Access at: http://localhost:5555

## API Endpoints

### Health Check
```
GET /health
```

### Download Video
```
POST /api/download
Body: {"url": "https://youtube.com/shorts/VIDEO_ID"}
```

### Get Status
```
GET /api/status/{job_id}
```

### Get History
```
GET /api/history?limit=10
```

## Docker

### Build

```bash
docker build -t youtube-shorts-downloader-python .
```

### Run

```bash
docker run -p 3001:3001 --env-file .env youtube-shorts-downloader-python
```

## Project Structure

```
backend-python/
├── app/
│   ├── config/          # Configuration (settings, database, redis, storage)
│   ├── models/          # Pydantic models
│   ├── routes/          # API routes
│   ├── services/        # Business logic (YouTube, storage)
│   ├── queue/           # Celery tasks
│   ├── middleware/      # Rate limiting, CORS
│   ├── utils/           # Utilities (logger, validators)
│   └── main.py          # FastAPI application
├── downloads/           # Temporary video storage
├── logs/                # Application logs
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
└── .env                # Environment variables
```

## Differences from Node.js Version

1. **FastAPI** instead of Express.js
2. **Celery** instead of Bull for task queue
3. **Motor** (async MongoDB driver) instead of Mongoose
4. **Pydantic** for data validation instead of Zod
5. **Loguru** for logging instead of Winston
6. **SlowAPI** for rate limiting instead of express-rate-limit

## Features

- ✅ Async/await support throughout
- ✅ Celery task queue with Redis
- ✅ MongoDB async operations
- ✅ Type hints and Pydantic validation
- ✅ Rate limiting
- ✅ CORS support
- ✅ Google Cloud Storage integration
- ✅ Automatic API documentation (Swagger UI at /docs)
- ✅ Error handling and logging

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:3001/docs
- ReDoc: http://localhost:3001/redoc

## Troubleshooting

### Celery won't start on Windows
Use `--pool=solo` option:
```bash
celery -A app.queue.celery_app worker --loglevel=info --pool=solo
```

### ModuleNotFoundError
Make sure you're in the project root and virtual environment is activated.

### Redis connection error
Verify REDIS_URL in `.env` and ensure Redis is running.

## Production Deployment

See main [DEPLOYMENT.md](../DEPLOYMENT.md) for production deployment instructions.
