# Multi-Cloud Storage Deployment Guide

## Implementation Complete! ✅

All code changes have been completed locally. Follow this guide to deploy to your server.

---

## Quick Summary

**What was implemented:**
- Multi-cloud storage with GCS, Azure Blob, and AWS S3
- Random provider selection from available providers under 5GB limit
- Storage usage tracking per provider
- Email alerts via Mailgun when providers hit 5GB
- API endpoint to query storage statistics
- 1-hour URL expiration for downloads

---

## Step 1: Commit and Push Local Changes

```bash
cd c:\Users\7plus8\build\ytd\backend-python

# Review changes
git status
git diff

# Add all changes
git add .

# Commit
git commit -m "Add multi-cloud storage support with Azure Blob and AWS S3

- Add random provider selection across GCS, Azure, S3
- Track storage usage per provider (5GB limit each)
- Send email alerts via Mailgun when limit reached
- Add storage stats API endpoint (GET /api/storage/stats)
- Update URLs to expire after 1 hour
- Store provider and file_size in download records

🤖 Generated with Claude Code

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push to GitHub
git push origin main
```

---

## Step 2: Pull Changes on Server

```bash
ssh root@172.234.172.191

cd /opt/ytdl
git pull origin main
```

---

## Step 3: Install New Dependencies

```bash
cd /opt/ytdl
source .venv/bin/activate

# Install new cloud storage and email libraries
pip install azure-storage-blob==12.19.0 boto3==1.34.34 aiosmtplib==3.0.1
```

---

## Step 4: Configure Environment Variables

Edit `/opt/ytdl/.env.production`:

```bash
nano /opt/ytdl/.env.production
```

Add these new variables:

```bash
# Azure Blob Storage (Optional - only if using Azure)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=youraccount;AccountKey=yourkey==;EndpointSuffix=core.windows.net
AZURE_CONTAINER_NAME=ytdl-videos

# AWS S3 (Optional - only if using AWS)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_S3_BUCKET_NAME=ytdl-videos
AWS_REGION=us-east-1

# Email Notifications (Mailgun SMTP)
MAILGUN_SMTP_HOST=smtp.mailgun.org
MAILGUN_SMTP_PORT=587
MAILGUN_SMTP_USER=postmaster@yourdomain.mailgun.org
MAILGUN_SMTP_PASSWORD=your-mailgun-password
ALERT_EMAIL_FROM=alerts@yourdomain.com
ALERT_EMAIL_TO=admin@yourdomain.com

# Storage Limits (Optional - defaults to 5GB)
STORAGE_LIMIT_BYTES=5368709120
```

**Notes:**
- You must have at least GCS configured (already set up)
- Azure and AWS are optional - configure only the ones you want to use
- Each provider you configure gets 5GB of free storage
- System will randomly distribute uploads across configured providers

---

## Step 5: Set Up Cloud Storage (if using Azure or AWS)

### For Azure Blob Storage (Free 5GB)

1. Go to https://portal.azure.com
2. Create a Storage Account
3. Create a container named `ytdl-videos` (or your preferred name)
4. Get the connection string from "Access Keys"
5. Add to `.env.production`

### For AWS S3 (Free 5GB with AWS Free Tier)

1. Go to https://console.aws.amazon.com/s3
2. Create a bucket named `ytdl-videos` (or your preferred name)
3. Create IAM user with S3 permissions
4. Get Access Key ID and Secret Access Key
5. Add to `.env.production`

### For Mailgun SMTP (Email Alerts)

1. Sign up at https://mailgun.com (free tier available)
2. Verify your domain or use sandbox domain
3. Get SMTP credentials from Settings → SMTP credentials
4. Add to `.env.production`

---

## Step 6: Restart Services

```bash
# Restart all services to load new code and environment variables
systemctl restart ytd-api
systemctl restart ytd-worker
systemctl restart ytd-beat

# Check status
systemctl status ytd-api
systemctl status ytd-worker
systemctl status ytd-beat
```

---

## Step 7: Verify Installation

### Check Logs

```bash
# Check API logs
journalctl -u ytd-api -n 50 --no-pager

# Check worker logs for storage initialization
journalctl -u ytd-worker -n 50 --no-pager | grep -i storage

# You should see lines like:
# Google Cloud Storage initialized
# Azure Blob Storage initialized (if configured)
# AWS S3 Storage initialized (if configured)
# Available storage providers: gcs, azure, s3
```

### Test Storage API

```bash
# Query storage statistics
curl http://172.234.172.191:3001/api/storage/stats | python3 -m json.tool
```

**Expected Response:**
```json
{
  "providers": [
    {
      "provider": "gcs",
      "total_size_bytes": 0,
      "total_size_gb": 0.0,
      "file_count": 0,
      "available_bytes": 5368709120,
      "available_gb": 5.0,
      "used_percentage": 0.0,
      "is_full": false,
      "last_updated": "2026-02-13T12:00:00"
    }
  ],
  "total_size_bytes": 0,
  "total_size_gb": 0.0,
  "total_file_count": 0
}
```

### Test a Download

Download a video and check:
1. Which provider was used (check worker logs)
2. Storage stats updated (call `/api/storage/stats` again)
3. Download URL works

```bash
# Watch logs during download
journalctl -u ytd-worker -f | grep -E '(Selected storage provider|uploaded|File uploaded)'
```

---

## How the System Works

### Upload Flow

1. User requests video download
2. Video downloaded to server locally
3. **Random provider selection:**
   - System queries MongoDB `storage_stats` collection
   - Gets list of providers with `is_full = false`
   - Randomly selects one provider
4. **File upload:**
   - Uploads to selected provider (GCS, Azure, or S3)
   - Gets signed URL (expires in 1 hour)
5. **Usage tracking:**
   - Adds file size to provider's `total_size_bytes`
   - Increments `file_count`
   - Checks if >= 5GB limit
6. **Alert if limit reached:**
   - Marks provider as `is_full = true`
   - Sends email alert via Mailgun
   - Won't use this provider until space freed
7. **Database record:**
   - Stores `downloadUrl`, `storageProvider`, and `fileSize`

### Cleanup Flow

1. Runs every 30 minutes (configured in Celery Beat)
2. Finds downloads older than 1 hour
3. Checks if file still referenced by recent downloads
4. If not, deletes from cloud storage (using stored `storageProvider`)
5. Updates storage stats (subtracts file size, decrements count)
6. If usage drops below 5GB, resets `is_full = false`

### API Endpoints

- `GET /api/storage/stats` - Returns usage for all providers
- `GET /api/download` - Download video (existing)
- `GET /api/status/{job_id}` - Check status (existing)
- `GET /api/history` - Download history (existing)

---

## Monitoring

### Check Storage Usage

```bash
# Via API
curl http://172.234.172.191:3001/api/storage/stats

# Or from frontend, add to your app:
fetch('http://your-server:3001/api/storage/stats')
  .then(r => r.json())
  .then(data => {
    data.providers.forEach(p => {
      console.log(`${p.provider}: ${p.used_percentage.toFixed(1)}% (${p.total_size_gb.toFixed(2)}GB / 5GB)`)
    })
  })
```

### Check Email Alerts

When a provider reaches 5GB, you'll receive an email like:

**Subject:** Storage Alert: gcs has reached 5.02GB

**Body:**
```
The gcs storage provider has reached its limit.

Provider: gcs
Current Usage: 5.02 GB
Limit: 5.00 GB

No new files will be uploaded to this provider until space is freed up.
The system will automatically use other available storage providers.
```

### Monitor Logs

```bash
# Watch for provider selection
journalctl -u ytd-worker -f | grep "Selected storage provider"

# Watch for storage tracking
journalctl -u ytd-worker -f | grep "Storage tracking"

# Watch for email alerts
journalctl -u ytd-worker -f | grep "Storage alert"

# Watch for cleanup
journalctl -u ytd-worker -f | grep -i cleanup
```

---

## Troubleshooting

### Problem: No providers available

**Error:** "No storage providers available"

**Solution:**
1. Check logs: `journalctl -u ytd-worker -n 100 | grep -i storage`
2. Verify environment variables are set correctly
3. For GCS: Check `GOOGLE_APPLICATION_CREDENTIALS` path exists
4. For Azure: Test connection string
5. For S3: Verify credentials have proper permissions

### Problem: Email alerts not sending

**Check:**
1. Mailgun credentials correct in `.env.production`
2. `ALERT_EMAIL_FROM` and `ALERT_EMAIL_TO` are set
3. Check logs: `journalctl -u ytd-worker | grep -i email`

### Problem: Storage stats not updating

**Check:**
1. MongoDB connection working
2. Check `storage_stats` collection exists:
   ```bash
   mongosh "your-mongodb-uri" --eval "db.storage_stats.find().pretty()"
   ```

### Problem: Files not deleting after 1 hour

**Check:**
1. FILE_EXPIRY_HOURS=1 in `.env.production`
2. Celery beat running: `systemctl status ytd-beat`
3. Check cleanup logs: `journalctl -u ytd-worker | grep cleanup`

---

## Database Schema

### New Collection: `storage_stats`

```javascript
{
  _id: ObjectId("..."),
  provider: "gcs",  // "gcs" | "azure" | "s3"
  total_size_bytes: 2147483648,  // Current usage in bytes
  file_count: 42,  // Number of files
  last_updated: ISODate("2026-02-13T12:00:00Z"),
  alert_sent: false,  // Email alert sent?
  is_full: false  // Reached 5GB limit?
}
```

### Updated Collection: `downloads`

```javascript
{
  // ... existing fields ...
  storageProvider: "gcs",  // NEW: which provider
  fileSize: 50331648,  // NEW: file size in bytes
  downloadUrl: "https://...",
  videoInfo: {...},
  // ... rest of fields ...
}
```

---

##Files Changed

### Created:
- `app/services/email_service.py` - Mailgun SMTP email notifications
- `app/config/multi_storage.py` - Multi-cloud storage initialization
- `app/models/storage_stats.py` - Storage statistics models
- `app/services/storage_tracker.py` - Usage tracking service
- `app/routes/storage_routes.py` - Storage stats API
- `MULTI_CLOUD_STORAGE_IMPLEMENTATION.md` - Implementation doc
- `DEPLOYMENT_GUIDE.md` - This file

### Modified:
- `requirements.txt` - Added azure-storage-blob, boto3, aiosmtplib
- `app/config/settings.py` - Added Azure, S3, Email settings
- `.env.example` - Added new environment variables
- `app/services/storage_service.py` - Complete rewrite for multi-cloud
- `app/queue/tasks.py` - Handle (url, provider, file_size) tuple
- `app/queue/cleanup_tasks.py` - Delete from correct provider
- `app/main.py` - Register storage routes

---

## Next Steps

1. ✅ Complete local implementation
2. ⏳ Commit and push changes to GitHub
3. ⏳ Pull changes on server
4. ⏳ Install new dependencies
5. ⏳ Configure environment variables
6. ⏳ Set up Azure/AWS (optional)
7. ⏳ Set up Mailgun for alerts
8. ⏳ Restart services
9. ⏳ Test and verify

---

## Support

For issues or questions, refer to:
- Implementation details: `MULTI_CLOUD_STORAGE_IMPLEMENTATION.md`
- This deployment guide: `DEPLOYMENT_GUIDE.md`
- Logs: `journalctl -u ytd-worker -n 100`
