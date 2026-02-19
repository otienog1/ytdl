# Storage Stats Sync Guide

## Overview

The storage stats sync utility keeps MongoDB tracking records in sync with actual cloud storage (GCS, Azure, S3). This prevents discrepancies caused by:
- Manual file deletions from cloud console
- Upload failures after tracking was added
- External modifications to cloud storage

## Running Methods

### 1. Manual Execution (Immediate)

**Option A: Python Script**
```bash
cd backend-python
pipenv run python sync_storage_stats.py
```

**Option B: Batch File (Windows)**
```bash
cd backend-python
run_storage_sync.bat
```

**Option C: Celery Command**
```bash
cd backend-python
pipenv run celery -A app.queue.celery_app call sync_storage_stats
```

### 2. API Endpoint (Trigger via HTTP)

**Trigger sync:**
```bash
curl -X POST http://localhost:3001/api/admin/sync-storage-stats
```

Response:
```json
{
  "message": "Storage sync task queued successfully",
  "task_id": "abc123-def456",
  "status": "Task will run in the background. Check logs for results."
}
```

**Check status:**
```bash
curl http://localhost:3001/api/admin/sync-storage-stats/status/abc123-def456
```

### 3. Automatic Scheduling (Recommended)

The sync task runs automatically **daily at 3 AM UTC** via Celery Beat.

**View scheduled tasks:**
```bash
cd backend-python
pipenv run celery -A app.queue.celery_app beat --loglevel=info
```

**Current schedule:**
- `cleanup-old-downloads`: Every 30 minutes
- `cleanup-failed-downloads`: Every 12 hours
- **`sync-storage-stats`: Daily at 3 AM UTC** ← New!

## Customizing Schedule

Edit `app/queue/celery_app.py`:

```python
'sync-storage-stats': {
    'task': 'sync_storage_stats',
    'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
},
```

**Schedule Options:**
```python
# Every 6 hours
crontab(hour='*/6')

# Every Sunday at midnight
crontab(hour=0, minute=0, day_of_week=0)

# Every hour
crontab(minute=0)

# Twice daily (6 AM and 6 PM)
crontab(hour='6,18', minute=0)
```

## What the Sync Does

1. **Connects to Cloud Storage**: GCS, Azure, S3
2. **Lists All Files**: Counts files and calculates total size
3. **Compares with MongoDB**: Checks database tracking records
4. **Auto-Fixes Mismatches**: Updates MongoDB to match reality
5. **Logs Results**: Reports all changes made

**Example Output:**
```
============================================================
GCS Storage:
------------------------------------------------------------
  MongoDB stats: 1 files, 0.02 MB
  Actual cloud:  0 files, 0.00 MB
  [!] MISMATCH DETECTED!
     Updating MongoDB to match actual cloud storage...
     [OK] Updated successfully!

AZURE Storage:
------------------------------------------------------------
  MongoDB stats: 1 files, 5.70 MB
  Actual cloud:  1 files, 5.70 MB
  [OK] Stats match - no sync needed
```

## Windows Task Scheduler Setup

To run sync automatically on Windows without Celery Beat:

1. **Open Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create Task**
   - Click "Create Basic Task..."
   - Name: "Storage Stats Sync"
   - Trigger: Daily at 3:00 AM
   - Action: Start a program
   - Program: `C:\Users\7plus8\build\ytd\backend-python\run_storage_sync.bat`

3. **Configure Settings**
   - ✓ Run whether user is logged on or not
   - ✓ Run with highest privileges
   - ✓ Wake computer to run this task (optional)

## Monitoring

**Check Celery logs:**
```bash
cd backend-python
pipenv run celery -A app.queue.celery_app worker --loglevel=info
```

**Look for:**
- `"Storage stats sync task started"`
- `"MISMATCH DETECTED"` (if discrepancies found)
- `"Storage sync complete: X providers synced"`

## Troubleshooting

### Sync Not Running
- **Check Celery Beat is running:**
  ```bash
  pipenv run celery -A app.queue.celery_app beat
  ```
- **Check Celery Worker is running:**
  ```bash
  pipenv run celery -A app.queue.celery_app worker
  ```
- **Check Redis is running:**
  ```bash
  redis-cli ping  # Should return PONG
  ```

### Mismatches Not Fixed
- Check logs for error messages
- Verify cloud storage credentials are valid
- Ensure MongoDB connection is working

### Task Not Scheduled
- Verify `app/queue/celery_app.py` includes `'app.queue.storage_sync_task'` in `include`
- Check Beat schedule configuration
- Restart Celery Beat after configuration changes

## Best Practices

1. **Run sync after manual cloud operations** (deleted files, etc.)
2. **Schedule during low-traffic hours** (e.g., 3 AM)
3. **Monitor logs for patterns** of mismatches
4. **Investigate frequent discrepancies** (may indicate bugs)
5. **Keep credentials secure** (never commit to git)

## Safety

The sync utility is **safe to run anytime**:
- ✅ Read-only on cloud storage (never deletes files)
- ✅ Only updates MongoDB stats collection
- ✅ Backs up existing stats before update
- ✅ Can be run multiple times safely

## Files

- `sync_storage_stats.py` - Standalone script
- `app/queue/storage_sync_task.py` - Celery task
- `app/routes/admin_routes.py` - API endpoints
- `app/queue/celery_app.py` - Celery configuration
- `run_storage_sync.bat` - Windows batch file

## API Documentation

See API docs at: `http://localhost:3001/docs#/admin`

Endpoints:
- `POST /api/admin/sync-storage-stats` - Trigger sync
- `GET /api/admin/sync-storage-stats/status/{task_id}` - Check status
