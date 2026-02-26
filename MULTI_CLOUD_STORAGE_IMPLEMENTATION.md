# Multi-Cloud Storage Implementation

This document tracks the implementation of multi-cloud storage with Azure Blob Storage and AWS S3 alongside Google Cloud Storage, with random distribution, storage tracking, and email alerts.

## Completed Tasks

### 1. Dependencies Added
- **File:** `requirements.txt`
- Added: `azure-storage-blob==12.19.0`, `boto3==1.34.34`, `aiosmtplib==3.0.1`

### 2. Settings Configuration
- **File:** `app/config/settings.py`
- Added configuration for:
  - Azure Blob Storage (connection string, container name)
  - AWS S3 (access key, secret key, bucket name, region)
  - Mailgun SMTP (host, port, credentials)
  - Email alerts (from/to addresses)
  - Storage limit (5GB in bytes)

### 3. Environment Variables
- **File:** `.env.example`
- Added all new configuration variables with examples

### 4. Email Notification Service
- **File:** `app/services/email_service.py`
- Implements Mailgun SMTP email alerts
- Sends HTML/text emails when storage hits 5GB limit
- Includes storage details (provider, usage, limit)

### 5. Multi-Cloud Storage Configuration
- **File:** `app/config/multi_storage.py`
- Singleton class managing all three cloud providers
- Auto-detects and initializes configured providers
- Provides unified access to GCS, Azure, and S3 clients

### 6. Storage Statistics Models
- **File:** `app/models/storage_stats.py`
- `StorageStats`: Database model for tracking usage
- `StorageStatsResponse`: API response model for single provider
- `AllStorageStatsResponse`: API response model for all providers

### 7. Storage Tracking Service
- **File:** `app/services/storage_tracker.py`
- Tracks file uploads/deletions across all providers
- Monitors storage usage against 5GB limit per provider
- Triggers email alerts when limit reached
- Provides API for querying storage statistics

### 8. Multi-Provider Storage Service
- **File:** `app/services/storage_service.py` (replaced)
- **Backup:** `app/services/storage_service_old.py.backup`
- Random provider selection from available providers under limit
- Upload support for GCS, Azure Blob, S3
- Delete support for all providers
- Signed URL generation (24 hours)
- Automatic storage tracking integration
- Returns tuple: `(url, provider, file_size)`

## Remaining Tasks

### 1. Update Download Task
- **File:** `app/queue/tasks.py`
- **Line:** ~148 (upload_file call)
- **Current:** `download_url = await storage_service.upload_file(local_file_path, destination_filename)`
- **Change to:**
  ```python
  download_url, provider, file_size = await storage_service.upload_file(local_file_path, destination_filename)
  ```
- **Also update:** Store `provider` and `file_size` in database download record
- **Add fields to downloads collection:**
  - `storageProvider`: string ("gcs", "azure", "s3")
  - `fileSize`: integer (bytes)

### 2. Update Cleanup Tasks
- **File:** `app/queue/cleanup_tasks.py`
- **Line:** ~123 (delete_file call)
- **Current:** `await storage_service.delete_file(file_name)`
- **Change to:**
  ```python
  provider = download.get('storageProvider', 'gcs')  # Default to gcs for old records
  await storage_service.delete_file(file_name, provider)
  ```
- Update both:
  - `_cleanup_old_downloads_async()` function
  - File deletion logic

### 3. Update Regenerate URL Logic
- **File:** `app/queue/tasks.py`
- **Line:** ~79 (regenerate_signed_url call)
- **Current:** `download_url = await storage_service.regenerate_signed_url(file_name)`
- **Change to:**
  ```python
  provider = existing_download.get('storageProvider', 'gcs')
  download_url = await storage_service.regenerate_signed_url(file_name, provider)
  ```

### 4. Create Storage Stats API Endpoint
- **File:** `app/routes/storage_routes.py` (new file)
- **Add route:** `GET /api/storage/stats`
- **Response:** Returns storage usage for all providers
- **Example:**
  ```json
  {
    "providers": [
      {
        "provider": "gcs",
        "total_size_bytes": 2147483648,
        "total_size_gb": 2.0,
        "file_count": 42,
        "available_bytes": 3221225472,
        "available_gb": 3.0,
        "used_percentage": 40.0,
        "is_full": false,
        "last_updated": "2026-02-13T12:00:00"
      }
    ],
    "total_size_bytes": 4294967296,
    "total_size_gb": 4.0,
    "total_file_count": 84
  }
  ```

### 5. Register Storage Routes
- **File:** `app/main.py`
- Add import: `from app.routes import storage_routes`
- Add route: `app.include_router(storage_routes.router)`

### 6. Install Dependencies on Server
```bash
cd /opt/ytdl
source .venv/bin/activate
pip install azure-storage-blob==12.19.0 boto3==1.34.34 aiosmtplib==3.0.1
```

### 7. Configure Environment Variables
- **File:** `/opt/ytdl/.env.production`
- Add all new environment variables:
  - Azure credentials (if using)
  - AWS credentials (if using)
  - Mailgun SMTP credentials
  - Alert email addresses

### 8. Restart Services
```bash
systemctl restart ytd-worker
systemctl restart ytd-beat
systemctl restart ytd-api
```

## How It Works

### Upload Flow
1. User requests video download
2. Video is downloaded locally
3. `storage_service.upload_file()` is called
4. Service queries `storage_tracker` for available providers under 5GB limit
5. Randomly selects one provider from available list
6. Uploads file to selected provider
7. Tracks usage in MongoDB `storage_stats` collection
8. If provider hits 5GB, sends email alert and marks as full
9. Returns `(url, provider, file_size)` tuple
10. Download task stores provider and file_size in database

### Storage Tracking
- Each upload: adds to provider's `total_size_bytes` and `file_count`
- Each deletion: subtracts from provider's `total_size_bytes` and `file_count`
- When `total_size_bytes` >= 5GB:
  - Set `is_full = true`
  - Send email alert (once)
  - Set `alert_sent = true`
- When usage drops below 5GB:
  - Reset `is_full = false`
  - Reset `alert_sent = false`

### Provider Selection
- Filters providers with `is_full = false`
- Randomly selects from available providers
- If all providers full, raises exception

### Email Alerts
- Sent via Mailgun SMTP
- HTML and plain text versions
- Includes provider name, current usage, and limit
- Only sent once per provider until usage drops below limit

## Database Schema

### New Collection: `storage_stats`
```javascript
{
  _id: ObjectId,
  provider: "gcs" | "azure" | "s3",
  total_size_bytes: 2147483648,
  file_count: 42,
  last_updated: ISODate("2026-02-13T12:00:00Z"),
  alert_sent: false,
  is_full: false
}
```

### Updated Collection: `downloads`
```javascript
{
  // ... existing fields ...
  storageProvider: "gcs" | "azure" | "s3",  // NEW
  fileSize: 50331648,  // NEW (bytes)
  // ... rest of fields ...
}
```

## Configuration Examples

### Azure Blob Storage (Free 5GB)
```bash
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=youraccount;AccountKey=yourkey==;EndpointSuffix=core.windows.net"
AZURE_CONTAINER_NAME="ytdl-videos"
```

### AWS S3 (Free 5GB)
```bash
AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
AWS_S3_BUCKET_NAME="ytdl-videos"
AWS_REGION="us-east-1"
```

### Mailgun SMTP
```bash
MAILGUN_SMTP_HOST="smtp.mailgun.org"
MAILGUN_SMTP_PORT=587
MAILGUN_SMTP_USER="postmaster@yourdomain.mailgun.org"
MAILGUN_SMTP_PASSWORD="your-mailgun-password"
ALERT_EMAIL_FROM="alerts@yourdomain.com"
ALERT_EMAIL_TO="admin@yourdomain.com"
```

## Testing

### Test Storage Upload
```python
from app.services.storage_service import storage_service
url, provider, file_size = await storage_service.upload_file("/path/to/video.mp4", "test_video.mp4")
print(f"Uploaded to {provider}: {url}, Size: {file_size} bytes")
```

### Test Storage Stats
```python
from app.services.storage_tracker import storage_tracker
stats = await storage_tracker.get_all_stats()
print(stats.model_dump())
```

### Test Email Alert
```python
from app.services.email_service import email_service
await email_service.send_storage_alert("gcs", 5.2, 5.0)
```

## Next Steps

1. Complete remaining tasks listed above (update download task, cleanup tasks, add API endpoint)
2. Test locally with all three providers
3. Deploy to server
4. Configure environment variables
5. Monitor storage usage via API endpoint
6. Verify email alerts when providers hit 5GB limit

## Files Modified/Created

### Modified
- `requirements.txt` - Added dependencies
- `app/config/settings.py` - Added settings
- `.env.example` - Added environment variables
- `app/services/storage_service.py` - Completely rewritten

### Created
- `app/services/email_service.py` - Email notifications
- `app/config/multi_storage.py` - Multi-cloud configuration
- `app/models/storage_stats.py` - Storage statistics models
- `app/services/storage_tracker.py` - Storage tracking service
- `app/services/storage_service_old.py.backup` - Backup of old service

### To Create
- `app/routes/storage_routes.py` - Storage stats API endpoint

### To Modify
- `app/queue/tasks.py` - Update upload/download logic
- `app/queue/cleanup_tasks.py` - Update cleanup logic
- `app/main.py` - Register storage routes
