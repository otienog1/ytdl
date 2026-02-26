# Day 3: Monitoring with Prometheus Metrics

**Goal**: Add comprehensive monitoring with Prometheus metrics
**Estimated Time**: 6-8 hours
**Priority**: HIGH - Essential for production visibility

---

## Morning Session (3-4 hours)

### Task 3.1: Install Prometheus dependencies (15 min)

```bash
cd backend-python
pipenv install prometheus-client prometheus-fastapi-instrumentator
```

---

### Task 3.2: Create metrics module (60 min)

**File: `backend-python/app/monitoring/metrics.py`**
```python
"""
Prometheus metrics for application monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import time

# Application info
app_info = Info('app', 'Application information')
app_info.info({
    'name': 'youtube_shorts_downloader',
    'version': '1.0.0'
})

# Download metrics
downloads_total = Counter(
    'downloads_total',
    'Total number of download requests',
    ['status', 'provider']
)

downloads_in_progress = Gauge(
    'downloads_in_progress',
    'Number of downloads currently in progress'
)

download_duration_seconds = Histogram(
    'download_duration_seconds',
    'Time spent downloading videos',
    buckets=[5, 10, 30, 60, 120, 300, 600, 1800]
)

# Storage metrics
storage_uploads_total = Counter(
    'storage_uploads_total',
    'Total number of file uploads',
    ['provider', 'status']
)

storage_upload_duration_seconds = Histogram(
    'storage_upload_duration_seconds',
    'Time spent uploading files to storage',
    ['provider'],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

storage_usage_bytes = Gauge(
    'storage_usage_bytes',
    'Current storage usage in bytes',
    ['provider']
)

storage_file_count = Gauge(
    'storage_file_count',
    'Number of files in storage',
    ['provider']
)

# Error metrics
errors_total = Counter(
    'errors_total',
    'Total number of errors',
    ['error_code', 'error_type']
)

# API metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# YouTube service metrics
youtube_api_calls_total = Counter(
    'youtube_api_calls_total',
    'Total YouTube API calls',
    ['operation', 'status']
)

youtube_api_duration_seconds = Histogram(
    'youtube_api_duration_seconds',
    'YouTube API call duration',
    ['operation'],
    buckets=[0.5, 1, 2, 5, 10, 30, 60]
)

# Queue metrics
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task execution time',
    ['task_name'],
    buckets=[5, 10, 30, 60, 120, 300, 600]
)

celery_queue_length = Gauge(
    'celery_queue_length',
    'Number of tasks in Celery queue'
)


class MetricsTracker:
    """Helper class for tracking metrics with context managers"""

    @staticmethod
    def track_download(provider: str):
        """Context manager for tracking download metrics"""
        class DownloadTracker:
            def __enter__(self):
                downloads_in_progress.inc()
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                downloads_in_progress.dec()
                duration = time.time() - self.start_time
                download_duration_seconds.observe(duration)

                status = 'failed' if exc_type else 'success'
                downloads_total.labels(status=status, provider=provider).inc()

        return DownloadTracker()

    @staticmethod
    def track_upload(provider: str):
        """Context manager for tracking upload metrics"""
        class UploadTracker:
            def __enter__(self):
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                storage_upload_duration_seconds.labels(provider=provider).observe(duration)

                status = 'failed' if exc_type else 'success'
                storage_uploads_total.labels(provider=provider, status=status).inc()

        return UploadTracker()

    @staticmethod
    def track_youtube_api(operation: str):
        """Context manager for tracking YouTube API calls"""
        class YouTubeAPITracker:
            def __enter__(self):
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                youtube_api_duration_seconds.labels(operation=operation).observe(duration)

                status = 'failed' if exc_type else 'success'
                youtube_api_calls_total.labels(operation=operation, status=status).inc()

        return YouTubeAPITracker()


# Singleton instance
metrics_tracker = MetricsTracker()
```

---

### Task 3.3: Add metrics middleware (45 min)

**File: `backend-python/app/middleware/metrics_middleware.py`**
```python
"""
Middleware for tracking HTTP metrics
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
from app.monitoring.metrics import (
    http_requests_total,
    http_request_duration_seconds
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP request metrics"""

    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Extract path pattern (remove IDs)
        path = request.url.path
        method = request.method
        status_code = response.status_code

        # Record metrics
        http_requests_total.labels(
            method=method,
            endpoint=path,
            status=status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=path
        ).observe(duration)

        # Add custom header
        response.headers["X-Process-Time"] = str(duration)

        return response
```

**File: `backend-python/app/main.py`** (Add middleware)
```python
from app.middleware.metrics_middleware import MetricsMiddleware
from prometheus_client import make_asgi_app

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

**Checkpoint**: Start app and verify `/metrics` endpoint works

---

### Task 3.4: Integrate metrics into services (90 min)

**File: `backend-python/app/services/youtube_service.py`** (Add metrics)
```python
from app.monitoring.metrics import metrics_tracker, youtube_api_calls_total

async def get_video_info(self, url: str, cookies: dict = None) -> VideoInfo:
    """Get video information"""
    with metrics_tracker.track_youtube_api('get_video_info'):
        video_id = self._extract_video_id(url)

        try:
            # ... existing code ...
            return video_info
        except Exception as e:
            # Exception automatically tracked by context manager
            raise

async def download_video_sync(self, url: str, output_path: str, cookies: dict = None) -> str:
    """Download video"""
    with metrics_tracker.track_youtube_api('download_video'):
        try:
            # ... existing code ...
            return output_path
        except Exception as e:
            raise
```

**File: `backend-python/app/services/storage_service.py`** (Add metrics)
```python
from app.monitoring.metrics import metrics_tracker, storage_usage_bytes, storage_file_count

async def upload_file(self, local_file_path: str, destination_file_name: str = None) -> Tuple[str, str, int]:
    """Upload file with metrics tracking"""
    provider = await self.select_random_provider()
    file_size = os.path.getsize(local_file_path)
    file_name = self._generate_filename(destination_file_name)

    with metrics_tracker.track_upload(provider):
        if provider == "gcs":
            url = await self._upload_to_gcs(local_file_path, file_name)
        elif provider == "azure":
            url = await self._upload_to_azure(local_file_path, file_name)
        elif provider == "s3":
            url = await self._upload_to_s3(local_file_path, file_name)

    # Track storage usage
    await storage_tracker.add_file_usage(provider, file_size, file_name)

    return url, provider, file_size
```

**File: `backend-python/app/services/storage_tracker.py`** (Add metrics)
```python
from app.monitoring.metrics import storage_usage_bytes, storage_file_count

async def add_file_usage(self, provider: str, file_size_bytes: int, file_name: str):
    """Track file usage and update metrics"""
    # ... existing database update ...

    # Update Prometheus metrics
    storage_usage_bytes.labels(provider=provider).inc(file_size_bytes)
    storage_file_count.labels(provider=provider).inc()

async def remove_file_usage(self, provider: str, file_size_bytes: int):
    """Remove file usage and update metrics"""
    # ... existing database update ...

    # Update Prometheus metrics
    storage_usage_bytes.labels(provider=provider).dec(file_size_bytes)
    storage_file_count.labels(provider=provider).dec()
```

---

## Afternoon Session (3-4 hours)

### Task 3.5: Add Celery task metrics (60 min)

**File: `backend-python/app/queue/tasks.py`** (Add metrics)
```python
from app.monitoring.metrics import (
    celery_tasks_total,
    celery_task_duration_seconds,
    metrics_tracker,
    errors_total
)
import time

@celery_app.task(bind=True, name='app.queue.tasks.process_download', max_retries=3)
def process_download(self, url: str, job_id: str, cookies: dict = None):
    """Process download with metrics"""
    start_time = time.time()
    provider = None

    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            _process_download_async(self, url, job_id, cookies)
        )

        # Track success
        celery_tasks_total.labels(
            task_name='process_download',
            status='success'
        ).inc()

        return result

    except Exception as exc:
        # Track failure
        celery_tasks_total.labels(
            task_name='process_download',
            status='failed'
        ).inc()

        # Track error
        error_code = getattr(exc, 'error_code', 'UNKNOWN_ERROR')
        errors_total.labels(
            error_code=error_code,
            error_type=exc.__class__.__name__
        ).inc()

        raise

    finally:
        # Track duration
        duration = time.time() - start_time
        celery_task_duration_seconds.labels(
            task_name='process_download'
        ).observe(duration)
```

---

### Task 3.6: Add background job to update storage metrics (45 min)

**File: `backend-python/app/monitoring/update_metrics.py`**
```python
"""
Background job to update storage metrics from database
"""
import asyncio
from app.config.database import connect_to_mongo, get_database
from app.monitoring.metrics import storage_usage_bytes, storage_file_count
from app.utils.logger import logger


async def update_storage_metrics():
    """Update storage metrics from database"""
    try:
        await connect_to_mongo()
        db = get_database()

        # Get storage stats from database
        stats = await db.storage_stats.find().to_list(length=None)

        for stat in stats:
            provider = stat.get('provider')
            total_bytes = stat.get('total_size_bytes', 0)
            file_count = stat.get('file_count', 0)

            # Set metrics
            storage_usage_bytes.labels(provider=provider).set(total_bytes)
            storage_file_count.labels(provider=provider).set(file_count)

        logger.info("Storage metrics updated")

    except Exception as e:
        logger.error(f"Failed to update storage metrics: {e}")


async def start_metrics_updater():
    """Start background task to update metrics"""
    while True:
        await update_storage_metrics()
        await asyncio.sleep(60)  # Update every minute
```

**File: `backend-python/app/main.py`** (Add startup event)
```python
import asyncio
from app.monitoring.update_metrics import start_metrics_updater

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    # Start metrics updater
    asyncio.create_task(start_metrics_updater())
```

---

### Task 3.7: Create Grafana dashboard configuration (60 min)

**File: `backend-python/monitoring/grafana-dashboard.json`**
```json
{
  "dashboard": {
    "title": "YouTube Downloader Metrics",
    "panels": [
      {
        "title": "Download Rate",
        "targets": [
          {
            "expr": "rate(downloads_total[5m])",
            "legendFormat": "{{status}} - {{provider}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Active Downloads",
        "targets": [
          {
            "expr": "downloads_in_progress"
          }
        ],
        "type": "stat"
      },
      {
        "title": "Download Duration",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(download_duration_seconds_bucket[5m]))",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.50, rate(download_duration_seconds_bucket[5m]))",
            "legendFormat": "p50"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Storage Usage",
        "targets": [
          {
            "expr": "storage_usage_bytes / 1024 / 1024 / 1024",
            "legendFormat": "{{provider}}"
          }
        ],
        "type": "graph",
        "yaxes": {
          "label": "GB"
        }
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(errors_total[5m])",
            "legendFormat": "{{error_code}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "API Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{endpoint}}"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

---

### Task 3.8: Create monitoring documentation (45 min)

**File: `backend-python/MONITORING.md`**
```markdown
# Monitoring Guide

## Metrics Endpoint

Access Prometheus metrics at: `http://localhost:3001/metrics`

## Available Metrics

### Download Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `downloads_total` | Counter | Total download requests (labels: status, provider) |
| `downloads_in_progress` | Gauge | Currently active downloads |
| `download_duration_seconds` | Histogram | Time to download videos |

### Storage Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `storage_uploads_total` | Counter | Total file uploads (labels: provider, status) |
| `storage_upload_duration_seconds` | Histogram | Upload duration by provider |
| `storage_usage_bytes` | Gauge | Current storage usage by provider |
| `storage_file_count` | Gauge | Number of files by provider |

### Error Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `errors_total` | Counter | Total errors (labels: error_code, error_type) |

### API Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | HTTP requests (labels: method, endpoint, status) |
| `http_request_duration_seconds` | Histogram | Request duration |

### Celery Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `celery_tasks_total` | Counter | Celery tasks (labels: task_name, status) |
| `celery_task_duration_seconds` | Histogram | Task execution time |

## Setting Up Prometheus

### Docker Compose

```yaml
version: '3'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
```

### Prometheus Configuration

**File: `monitoring/prometheus.yml`**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'youtube_downloader'
    static_configs:
      - targets: ['host.docker.internal:3001']
```

## Setting Up Grafana

### Import Dashboard

1. Start Grafana: `docker run -d -p 3000:3000 grafana/grafana`
2. Add Prometheus data source
3. Import dashboard from `monitoring/grafana-dashboard.json`

## Useful Queries

### Download success rate
```promql
rate(downloads_total{status="success"}[5m]) / rate(downloads_total[5m])
```

### Storage usage percentage
```promql
(storage_usage_bytes / (5 * 1024 * 1024 * 1024)) * 100
```

### Error rate
```promql
rate(errors_total[5m])
```

### p95 download time
```promql
histogram_quantile(0.95, rate(download_duration_seconds_bucket[5m]))
```
```

---

## End of Day Checklist

- [ ] Prometheus client installed
- [ ] Metrics module created with all key metrics
- [ ] Metrics middleware added to FastAPI
- [ ] Metrics integrated into YouTube service
- [ ] Metrics integrated into storage service
- [ ] Celery task metrics implemented
- [ ] Background job for metric updates
- [ ] Grafana dashboard configuration created
- [ ] Monitoring documentation written
- [ ] `/metrics` endpoint accessible
- [ ] Code committed to git

**Git Commit**:
```bash
git add .
git commit -m "Day 3: Add Prometheus monitoring

- Installed prometheus-client
- Created comprehensive metrics module
- Added HTTP metrics middleware
- Integrated metrics into all services
- Added Celery task metrics
- Created background job for metric updates
- Generated Grafana dashboard config
- Documented all metrics and queries"
```

---

## Success Metrics

✅ **Complete** if:
- 15+ metrics defined and tracking
- `/metrics` endpoint returns Prometheus format data
- All services emitting metrics
- Grafana dashboard configuration created
- Documentation complete

## Tomorrow Preview

**Day 4**: WebSocket implementation for real-time progress
- Replace polling with WebSocket connections
- Add WebSocket endpoint for download progress
- Update frontend to use WebSocket
- Handle connection management and reconnection
