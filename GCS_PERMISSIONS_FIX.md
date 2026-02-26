# Fix Google Cloud Storage Permissions

## Common Errors

### Error 1: Cannot Upload Files

```
ytdl-bkt@divine-actor-473706-k4.iam.gserviceaccount.com does not have
storage.objects.create access to the Google Cloud Storage object.
```

**Solution**: Grant "Storage Object Creator" role (see below)

### Error 2: Cannot Download Files (Access Denied)

```xml
<Error>
<Code>AccessDenied</Code>
<Message>Access denied.</Message>
<Details>ytdl-bkt@divine-actor-473706-k4.iam.gserviceaccount.com does not have
storage.objects.get access to the Google Cloud Storage object.</Details>
</Error>
```

**Root Cause**: The "Storage Object Creator" role only allows creating and deleting objects, but NOT reading them. You need additional permissions to download files via signed URLs.

**Solution**: Grant "Storage Object Viewer" role in addition to "Storage Object Creator", or use "Storage Admin" for full access during development (see below).

---

## Required Permissions

Your service account needs these permissions:

| Permission | Purpose | Included in Creator | Included in Viewer | Included in Admin |
|------------|---------|--------------------|--------------------|-------------------|
| **storage.objects.create** | Upload files | ✅ | ❌ | ✅ |
| **storage.objects.get** | Read/download files | ❌ | ✅ | ✅ |
| **storage.objects.delete** | Delete old files | ✅ | ❌ | ✅ |

**⚠️ IMPORTANT**:
- **Storage Object Creator** role allows uploads but NOT downloads
- **Storage Object Viewer** role allows downloads but NOT uploads
- You need BOTH roles, or use **Storage Admin** for full access

---

## Solution: Grant Both Upload and Download Permissions

### Option 1: Using Google Cloud Console (Recommended)

1. **Go to Google Cloud Console**:
   - Visit: https://console.cloud.google.com/storage/browser

2. **Select your bucket**:
   - Click on bucket: `ytdl_bkt`

3. **Open Permissions tab**:
   - Click the "PERMISSIONS" tab at the top

4. **Grant Access** (do this TWICE for two different roles):

   **First: Grant Creator Role (for uploads)**
   - Click "+ GRANT ACCESS"
   - In "New principals", enter: `ytdl-bkt@divine-actor-473706-k4.iam.gserviceaccount.com`
   - In "Select a role", choose: **Storage Object Creator**
   - Click "SAVE"

   **Second: Grant Viewer Role (for downloads)**
   - Click "+ GRANT ACCESS" again
   - In "New principals", enter: `ytdl-bkt@divine-actor-473706-k4.iam.gserviceaccount.com`
   - In "Select a role", choose: **Storage Object Viewer**
   - Click "SAVE"

### Option 2: Using gcloud CLI

Run both commands to grant both roles:

```bash
# Grant Storage Object Creator role (for uploads)
gcloud storage buckets add-iam-policy-binding gs://ytdl_bkt \
  --member=serviceAccount:ytdl-bkt@divine-actor-473706-k4.iam.gserviceaccount.com \
  --role=roles/storage.objectCreator

# Grant Storage Object Viewer role (for downloads)
gcloud storage buckets add-iam-policy-binding gs://ytdl_bkt \
  --member=serviceAccount:ytdl-bkt@divine-actor-473706-k4.iam.gserviceaccount.com \
  --role=roles/storage.objectViewer
```

### Option 3: Grant Full Storage Admin (Easiest for Development)

For development/testing, you can grant full admin access:

**Using Console:**
- Follow steps in Option 1, but choose **Storage Admin** role instead

**Using gcloud CLI:**
```bash
gcloud storage buckets add-iam-policy-binding gs://ytdl_bkt \
  --member=serviceAccount:ytdl-bkt@divine-actor-473706-k4.iam.gserviceaccount.com \
  --role=roles/storage.admin
```

⚠️ **Note**: Storage Admin gives full control. For production, use separate Creator and Viewer roles instead.

---

## Verify Permissions

After granting access, verify it worked:

```bash
# Check bucket permissions
gcloud storage buckets get-iam-policy gs://ytdl_bkt
```

You should see your service account with the appropriate roles:
- `roles/storage.objectCreator` (for uploads)
- `roles/storage.objectViewer` (for downloads)

OR

- `roles/storage.admin` (for everything)

---

## Test the Fix

1. **Wait 1-2 minutes** for IAM changes to propagate

2. **Restart Celery worker** to pick up new permissions:
   ```bash
   # Press Ctrl+C in the Celery worker window, then restart it
   pipenv run celery -A app.queue.celery_app worker --loglevel=info --pool=solo
   ```

3. **Try downloading a video** through the frontend

4. **Click the download button** - the file should now download successfully!

---

## Troubleshooting

### "Permission denied" still appears

1. Wait a few minutes for IAM changes to propagate (can take up to 5 minutes)
2. Restart the Celery worker to pick up new permissions
3. Verify the service account email is exactly correct
4. Check that the credentials file `divine-actor-473706-k4-fdec9ee56ba0.json` is valid

### Service account not found

If you get "service account not found":
1. Verify the service account exists in [IAM & Admin](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Check the spelling of the service account email: `ytdl-bkt@divine-actor-473706-k4.iam.gserviceaccount.com`
3. Make sure you're in the right GCP project: `divine-actor-473706-k4`

### "Principal already exists on the policy"

This means the role was already granted. The permission might already be set, or you need to:
1. Check which roles are already assigned in the Console
2. If only Creator role exists, add Viewer role
3. Or replace both with Admin role for simplicity

### Bucket doesn't exist

If bucket `ytdl_bkt` doesn't exist, create it:

```bash
gcloud storage buckets create gs://ytdl_bkt \
  --location=us-central1 \
  --uniform-bucket-level-access
```

---

## Current Status

✅ MongoDB connection - Working
✅ Redis connection - Working
✅ yt-dlp download - Working
✅ ffmpeg processing - Working
✅ GCS upload - Working (has storage.objects.create)
❌ GCS download - **Needs storage.objects.get permission**
✅ Database status updates - Working
✅ Progress tracking - Working
✅ Video info display - Working

**To fix the download issue**: Grant "Storage Object Viewer" role or "Storage Admin" role using one of the options above.

---

## Production Best Practices

For production deployments:

1. **Use least privilege** - Grant only necessary permissions
2. **Separate roles** - Use Storage Object Creator + Viewer instead of Admin
3. **Enable object versioning** for backup and recovery
4. **Set up lifecycle policies** to auto-delete old files after 24-48 hours
5. **Monitor bucket usage** and set up billing alerts
6. **Use signed URLs with short expiration** (currently 24 hours)
7. **Consider CDN** (Cloud CDN) for frequently accessed files
8. **Enable logging** to track access patterns

---

## Quick Reference: GCS Roles

| Role | Upload | Download | Delete | List | Use Case |
|------|--------|----------|--------|------|----------|
| **Storage Object Creator** | ✅ | ❌ | ✅ | ❌ | Upload-only service |
| **Storage Object Viewer** | ❌ | ✅ | ❌ | ✅ | Download-only service |
| **Storage Admin** | ✅ | ✅ | ✅ | ✅ | Full control (dev/test) |

For this app, you need: **Creator + Viewer** OR **Admin**
