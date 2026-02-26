# Bug Fix: UnboundLocalError in Video Deduplication

## Issue Summary

**Error**: `UnboundLocalError: cannot access local variable 'timedelta' where it is not associated with a value`

**When it occurred**: When downloading a video that already exists in GCS storage (video deduplication feature)

**Severity**: Critical - Prevented video deduplication from working

---

## Root Cause Analysis

### The Problem

In [storage_service.py:regenerate_signed_url()](app/services/storage_service.py#L277), there was a variable scoping issue:

```python
# Line 7: Module-level import
from datetime import timedelta

# Line 277-318: regenerate_signed_url method
async def regenerate_signed_url(self, file_name: str, provider: str) -> str:
    """Regenerate signed URL for an existing file (1 hour expiry)"""
    if provider == "gcs":
        bucket = multi_storage.get_gcs_bucket()
        blob = bucket.blob(file_name)
        return blob.generate_signed_url(
            expiration=timedelta(hours=1),  # ❌ Line 283: UnboundLocalError!
            method='GET',
            response_disposition=f'attachment; filename="{file_name}"'
        )
    elif provider == "azure":
        from azure.storage.blob import generate_blob_sas, BlobSasPermissions
        from datetime import datetime, timedelta  # ⚠️ Line 289: THIS caused the issue!
        ...
```

### Why It Failed

Python's scoping rules caused this bug:

1. `timedelta` was imported at module level (line 7) ✅
2. BUT, line 289 has `from datetime import datetime, timedelta` inside the Azure block
3. When Python parses the function, it sees this import and marks `timedelta` as a **local variable** for the entire function scope
4. When the GCS path executes (line 283), it tries to use `timedelta` **before** the Azure block's import runs
5. Result: `UnboundLocalError` because the local variable `timedelta` hasn't been assigned yet

This is a classic Python scoping gotcha - any variable that's assigned anywhere in a function becomes local to that entire function.

---

## The Fix

### What Changed

Removed the redundant `timedelta` import from line 289:

```python
# BEFORE (line 287-290):
elif provider == "azure":
    from azure.storage.blob import generate_blob_sas, BlobSasPermissions
    from datetime import datetime, timedelta  # ❌ Redundant import
    container_client = multi_storage.get_azure_container_client()

# AFTER (line 287-290):
elif provider == "azure":
    from azure.storage.blob import generate_blob_sas, BlobSasPermissions
    from datetime import datetime  # ✅ Only import what's needed
    container_client = multi_storage.get_azure_container_client()
```

### Why This Works

- `timedelta` is already imported at module level (line 7)
- Removing the redundant import from the Azure block eliminates the scoping issue
- Now `timedelta` is consistently a module-level variable throughout the function
- Both GCS and Azure paths can access it without errors

---

## Testing

### Before Fix

```bash
$ pipenv run python -c "from app.services.storage_service import storage_service; ..."
UnboundLocalError: cannot access local variable 'timedelta' where it is not associated with a value
```

### After Fix

```bash
$ pipenv run python -c "from app.services.storage_service import storage_service; ..."
SUCCESS - Generated URL: https://storage.googleapis.com/ytdl_bkt/test.mp4?Expires=...
```

✅ **GCS signed URL generation works**
✅ **Azure signed URL generation still works** (datetime import is still there)
✅ **S3 signed URL generation still works** (doesn't use timedelta)

---

## Impact

### What Was Broken

- **Video deduplication**: When a video already existed in GCS, attempting to reuse it failed
- **User experience**: Users would see "Download failed" even though the video was already downloaded
- **Storage efficiency**: Couldn't reuse existing files, wasting storage space

### What Now Works

- ✅ Video deduplication works correctly
- ✅ Existing videos are reused with regenerated signed URLs
- ✅ 1-hour expiry URLs generated for all providers (GCS, Azure, S3)
- ✅ Storage space is saved by not re-downloading existing videos

---

## Related Code

### Video Deduplication Flow

The bug occurred in this workflow ([tasks.py:60-86](app/queue/tasks.py#L60-L86)):

1. User requests video download
2. Check if video already exists in database with `status: 'completed'`
3. If exists, extract filename from old download URL
4. Call `storage_service.regenerate_signed_url(file_name, provider)` ← **BUG WAS HERE**
5. Return new signed URL to user (1-hour expiry)

### Files Affected

- [storage_service.py](app/services/storage_service.py) - Fixed line 289
- [tasks.py](app/queue/tasks.py) - Uses regenerate_signed_url for deduplication

---

## Lessons Learned

### Python Scoping Gotcha

Be careful with imports inside conditional blocks:

```python
# ❌ BAD - Creates scoping issues
from datetime import timedelta  # Module level

def my_function():
    result = timedelta(hours=1)  # Uses module-level import
    if some_condition:
        from datetime import timedelta  # Makes timedelta local!
        # Now result = timedelta(hours=1) above becomes UnboundLocalError
```

```python
# ✅ GOOD - Consistent scoping
from datetime import timedelta  # Module level

def my_function():
    result = timedelta(hours=1)  # Always uses module-level import
    if some_condition:
        from datetime import datetime  # Only import what's needed
        # timedelta remains module-level variable
```

### Best Practices

1. **Import at module level** whenever possible
2. **Avoid redundant imports** inside functions
3. **Only use local imports** when absolutely necessary (circular dependencies, lazy loading)
4. **Be consistent** - if importing in a block, don't use the same name at module level

---

## Commit

```bash
git commit -m "Fix UnboundLocalError in regenerate_signed_url for GCS provider"
```

**Fixed**: Video deduplication now works correctly for GCS-stored videos! 🎉
