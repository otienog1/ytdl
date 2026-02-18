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
