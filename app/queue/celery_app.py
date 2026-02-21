from celery import Celery
from celery.schedules import crontab
from app.config.settings import settings

celery_app = Celery(
    "youtube_shorts_downloader",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.queue.tasks', 'app.queue.cleanup_tasks', 'app.queue.storage_sync_task']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes

    # Redis connection pool settings to prevent "max clients reached" error
    broker_connection_max_retries=3,
    broker_pool_limit=5,  # Limit connection pool size
    broker_transport_options={
        'max_connections': 5,
        'socket_keepalive': True,
        'socket_timeout': 5,
        'socket_connect_timeout': 5,
    },
    result_backend_transport_options={
        'max_connections': 5,
        'socket_keepalive': True,
        'socket_timeout': 5,
        'socket_connect_timeout': 5,
    },
)

# Configure periodic cleanup tasks using Celery Beat
celery_app.conf.beat_schedule = {
    'cleanup-old-downloads': {
        'task': 'app.queue.cleanup_tasks.cleanup_old_downloads',
        'schedule': crontab(minute='*/30'),  # Run every 30 minutes (for 1-hour expiry)
    },
    'cleanup-failed-downloads': {
        'task': 'app.queue.cleanup_tasks.cleanup_failed_downloads',
        'schedule': crontab(hour='*/12'),  # Run every 12 hours
    },
    'sync-storage-stats': {
        'task': 'sync_storage_stats',
        'schedule': crontab(hour=3, minute=0),  # Run daily at 3 AM UTC
    },
}
