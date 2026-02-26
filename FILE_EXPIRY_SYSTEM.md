# File Expiry and Storage Management System

## Overview

The YouTube Shorts downloader implements a **smart file expiry system** that automatically deletes old files from Google Cloud Storage while handling the case where multiple users download the same video.

## Current Configuration

- **File Expiry Time**: 24 hours (configurable via `FILE_EXPIRY_HOURS` in .env)
- **Cleanup Schedule**: Every 6 hours
- **Failed Downloads Cleanup**: Every 12 hours

## How File Expiry Works

### 1. Reference Counting for Shared Files

When multiple users download the same video, the system uses **reference counting** to prevent premature deletion:

```
Timeline:
Hour 0:  User A downloads video "xyz123" → File created in GCS
Hour 2:  User B downloads same video → Reuses User A's file (deduplication)
Hour 6:  Cleanup runs → Checks references
         User A's download: 6 hours old (should expire)
         User B's download: 4 hours old (still valid)
         Decision: KEEP FILE (User B still has valid reference)
Hour 26: Cleanup runs → Checks references
         User A's download: 26 hours old (expired)
         User B's download: 24 hours old (expired)
         Decision: DELETE FILE (no valid references remain)
```

### 2. Database Record Management

Each download creates a database record with:
- `jobId`: Unique identifier for this download request
- `videoInfo.id`: YouTube video ID (used for deduplication)
- `createdAt`: When this download was requested
- `downloadUrl`: Signed URL (valid for 24 hours)
- `expired`: Boolean flag indicating if this record expired

### 3. Cleanup Process Flow

```
┌─────────────────────────────────────────────┐
│ Celery Beat triggers cleanup every 6 hours │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Find all downloads older than 24 hours     │
│ WHERE createdAt < (now - 24 hours)          │
│   AND status = 'completed'                  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │ For each old download│
         └─────────┬───────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ Check: Are there recent downloads           │
│ referencing the same video file?            │
│                                              │
│ Query: downloads where                       │
│   - videoInfo.id = same video               │
│   - createdAt >= (now - 24 hours)           │
│   - status = 'completed'                    │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
   ┌─────────┐         ┌─────────┐
   │ YES     │         │ NO      │
   │ (refs)  │         │ (none)  │
   └────┬────┘         └────┬────┘
        │                   │
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│ KEEP FILE     │   │ DELETE FILE   │
│               │   │ from GCS      │
│ - Mark record │   │               │
│   as expired  │   │ - Mark record │
│ - Remove URL  │   │   as expired  │
│               │   │ - Remove URL  │
└───────────────┘   └───────────────┘
```

## Example Scenarios

### Scenario 1: Single User Download

```
Day 1, 10:00 AM - User downloads "Epic Fail Compilation"
Day 1, 10:05 AM - Download completes, file stored in GCS
Day 2, 10:00 AM - 24 hours passed
Day 2, 04:00 PM - Cleanup runs (every 6 hours)
                  → No recent references
                  → File deleted from GCS
                  → Download record marked expired
```

### Scenario 2: Multiple Users, Same Video

```
Day 1, 10:00 AM - User A downloads "Trending Dance Video"
Day 1, 10:05 AM - File stored in GCS
Day 1, 02:00 PM - User B downloads same video (4 hours later)
                  → Deduplication: Reuses User A's file
Day 1, 06:00 PM - User C downloads same video (8 hours after A)
                  → Deduplication: Reuses User A's file

Day 2, 10:00 AM - 24 hours since User A
Day 2, 04:00 PM - Cleanup runs
                  → User A: 30 hours old (expired)
                  → User B: 26 hours old (expired)
                  → User C: 22 hours old (STILL VALID)
                  → Decision: KEEP FILE (User C has valid reference)
                  → Mark A and B as expired, remove their URLs

Day 2, 10:00 PM - 32 hours since User C
                  → Cleanup runs
                  → User C: 32 hours old (expired)
                  → No valid references remain
                  → Decision: DELETE FILE from GCS
                  → Mark User C as expired
```

### Scenario 3: Viral Video (100+ users)

```
Hour 0  - User 1 downloads viral video
Hour 1  - Users 2-20 download (deduplicated)
Hour 2  - Users 21-50 download (deduplicated)
Hour 3  - Users 51-100 download (deduplicated)

Hour 24 - User 1's reference expires
Hour 25 - Users 2-20's references expire
Hour 26 - Users 21-50's references expire
Hour 27 - Users 51-100's references expire

Hour 28 - Cleanup runs
          → All references expired
          → File deleted
          → 100 database records marked expired
```

**Result**: Single file served 100 users, deleted only after all expired.

## Configuration

### Environment Variables

```env
# .env file
FILE_EXPIRY_HOURS=24    # Files older than 24 hours are eligible for cleanup
```

### Cleanup Schedule

In [celery_app.py](c:\Users\7plus8\build\ytd\backend-python\app\queue\celery_app.py):

```python
celery_app.conf.beat_schedule = {
    'cleanup-old-downloads': {
        'task': 'app.queue.cleanup_tasks.cleanup_old_downloads',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    'cleanup-failed-downloads': {
        'task': 'app.queue.cleanup_tasks.cleanup_failed_downloads',
        'schedule': crontab(hour='*/12'),  # Every 12 hours
    },
}
```

### Customizing Cleanup Schedule

**Option 1: More Frequent (Every 4 hours)**
```python
'schedule': crontab(hour='*/4'),
```

**Option 2: Daily at Specific Time (3 AM)**
```python
'schedule': crontab(hour=3, minute=0),
```

**Option 3: Twice Daily (3 AM and 3 PM)**
```python
'schedule': crontab(hour='3,15', minute=0),
```

## Manual Cleanup

You can manually trigger cleanup from Python:

```python
from app.queue.cleanup_tasks import cleanup_old_downloads

# Trigger cleanup immediately
result = cleanup_old_downloads.delay()

# Wait for result
print(result.get())
# Output: {'files_deleted': 25, 'files_kept': 10, 'records_updated': 35}
```

Or from command line:

```bash
# Using pipenv
pipenv run celery -A app.queue.celery_app call app.queue.cleanup_tasks.cleanup_old_downloads

# Using venv
celery -A app.queue.celery_app call app.queue.cleanup_tasks.cleanup_old_downloads
```

## Storage Cost Analysis

### Without Cleanup (Infinite Growth)

```
Assumptions:
- 1000 downloads per month
- Average video size: 50MB
- 50% duplicate downloads (deduplication)

Storage per month:
- Unique videos: 500 videos × 50MB = 25GB
- Month 1: 25GB
- Month 2: 50GB (cumulative)
- Month 3: 75GB (cumulative)
- Year 1: 300GB

GCS Costs (Standard Storage):
- $0.020 per GB per month
- Month 1: 25GB × $0.020 = $0.50
- Month 12: 300GB × $0.020 = $6.00
- Total Year 1: ~$42.00
```

### With 24-Hour Cleanup

```
Assumptions:
- Same 1000 downloads per month
- 50% duplicate downloads
- Average concurrent storage: ~3GB (24-hour window)

Storage per month:
- Peak storage: ~5GB (during high traffic)
- Average storage: ~3GB

GCS Costs:
- Month 1-12: 3GB × $0.020 = $0.06 per month
- Total Year 1: ~$0.72

Savings: $41.28 per year (98% reduction!)
```

### Production at Scale (10,000 downloads/month)

```
Without cleanup:
- Year 1 storage: 3TB
- Year 1 cost: ~$420

With 24-hour cleanup:
- Average storage: 30GB
- Year 1 cost: ~$7.20

Savings: $412.80 per year (98% reduction!)
```

## Monitoring Cleanup

### Check Cleanup Logs

Look for these log messages in Celery Beat and Worker:

```
[INFO] Starting cleanup job...
[INFO] Found 150 downloads older than 24 hours
[INFO] Keeping file for video xyz123: Referenced by 5 recent downloads
[INFO] Deleted file: Epic Video.mp4 (video: abc456)
[INFO] Cleanup completed: 45 files deleted, 10 files kept (active references), 55 records updated
```

### Database Queries

Check expired downloads:

```javascript
// MongoDB shell
db.downloads.count({ expired: true })
// Returns count of expired records

db.downloads.find({
  expired: true,
  expiredAt: { $gte: new Date(Date.now() - 24*60*60*1000) }
})
// Returns downloads that expired in last 24 hours
```

Check active storage usage:

```javascript
// Count files still in use
db.downloads.count({
  status: 'completed',
  downloadUrl: { $exists: true },
  $or: [
    { expired: { $exists: false } },
    { expired: false }
  ]
})
```

## Troubleshooting

### Cleanup Not Running

**Problem**: No cleanup logs in Celery Beat

**Solution**:
1. Check if Celery Beat is running:
   ```bash
   # You should see a "Celery Beat" window
   # If not, start it manually:
   pipenv run celery -A app.queue.celery_app beat --loglevel=info
   ```

2. Check beat schedule:
   ```python
   from app.queue.celery_app import celery_app
   print(celery_app.conf.beat_schedule)
   ```

### Files Not Deleting

**Problem**: Old files still in GCS after 24+ hours

**Possible Causes**:

1. **Active references**: Check if recent downloads reference the file
   ```javascript
   db.downloads.find({ 'videoInfo.id': 'xyz123', status: 'completed' })
   ```

2. **Celery Beat not running**: Ensure beat scheduler is active

3. **GCS permissions**: Ensure service account has delete permission
   ```bash
   # Check permissions
   gcloud storage buckets get-iam-policy gs://ytdl_bkt
   ```

### Database Growing Too Large

**Problem**: MongoDB size keeps growing

**Solution**: Run failed downloads cleanup more frequently
```python
# Change from every 12 hours to every 6 hours
'schedule': crontab(hour='*/6'),
```

Or manually trigger:
```bash
pipenv run celery -A app.queue.celery_app call app.queue.cleanup_tasks.cleanup_failed_downloads
```

## Best Practices

### 1. Balance Expiry Time vs User Experience

- **24 hours**: Good balance (recommended)
- **12 hours**: More aggressive cleanup, lower costs
- **48 hours**: Better UX for returning users, higher costs

### 2. Monitor Storage Costs

Set up billing alerts in Google Cloud:
```bash
gcloud alpha billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="GCS Storage Alert" \
  --budget-amount=10.00 \
  --threshold-rule=percent=80
```

### 3. Archive Popular Videos

For viral videos, consider permanently caching:
```python
# Add a 'permanent' flag to prevent deletion
db.downloads.update_one(
    {'videoInfo.id': 'viral_video_id'},
    {'$set': {'permanent': true}}
)

# Update cleanup logic to skip permanent files
```

### 4. Use Lifecycle Policies (Alternative)

GCS supports automatic lifecycle policies:
```bash
# Set bucket lifecycle (alternative to Celery cleanup)
gcloud storage buckets update gs://ytdl_bkt \
  --lifecycle-file=lifecycle.json
```

lifecycle.json:
```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 1,
          "matchesPrefix": ["temp/"]
        }
      }
    ]
  }
}
```

## Code Locations

- **Cleanup tasks**: [app/queue/cleanup_tasks.py](c:\Users\7plus8\build\ytd\backend-python\app\queue\cleanup_tasks.py)
- **Celery schedule**: [app/queue/celery_app.py](c:\Users\7plus8\build\ytd\backend-python\app\queue\celery_app.py)
- **Startup script**: [start-dev.bat](c:\Users\7plus8\build\ytd\backend-python\start-dev.bat)

## Summary

The file expiry system provides:

✅ **Automatic cleanup** every 6 hours
✅ **Reference counting** prevents deleting files still in use
✅ **Cost optimization** (98% storage cost reduction)
✅ **Smart deduplication** works seamlessly with expiry
✅ **Configurable** expiry time and schedule
✅ **Production-ready** with monitoring and error handling

Files are kept as long as at least one user has a valid reference, then automatically deleted to minimize storage costs.
