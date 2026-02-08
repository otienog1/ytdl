# Video Deduplication System

## Overview

The YouTube Shorts downloader implements a **video deduplication system** to avoid re-downloading and re-processing the same video multiple times when different users (or the same user) request the same video.

## How It Works

### Before Deduplication
- User A downloads video `xyz123`
- User B downloads the same video `xyz123`
- Result: **2 downloads, 2 files in GCS, 2x bandwidth usage**

### After Deduplication
- User A downloads video `xyz123` → Full download and processing
- User B downloads the same video `xyz123` → **Instant completion, reuses User A's file**
- Result: **1 download, 1 file in GCS, 1x bandwidth usage**

## Implementation Details

### 1. Database Lookup

When a new download job starts, the system checks if this video was already processed:

```python
# Check if this video was already processed
existing_download = await db.downloads.find_one({
    'videoInfo.id': video_id,
    'status': 'completed',
    'downloadUrl': {'$exists': True, '$ne': None}
})
```

### 2. Reuse Existing File

If found, it reuses the existing GCS URL:

```python
if existing_download:
    logger.info(f"Video {video_id} already exists in GCS, reusing existing file")
    download_url = existing_download.get('downloadUrl')
    # Skip download and upload steps
```

### 3. Download New File

If not found, it performs the full download and upload:

```python
else:
    # Download from YouTube
    local_file_path = await youtube_service.download_video(url, video_id)

    # Upload to GCS
    download_url = await storage_service.upload_file(local_file_path, destination_filename)

    # Cleanup local file
    await youtube_service.delete_local_file(local_file_path)
```

## Benefits

### 1. Cost Savings
- **Storage**: Only one copy of each video in GCS
- **Bandwidth**: No redundant downloads from YouTube
- **Processing**: No redundant yt-dlp/ffmpeg operations

### 2. Performance
- **Faster response**: Existing videos complete almost instantly
- **Lower load**: Less CPU/memory usage for duplicate requests
- **Better UX**: Users get results immediately for popular videos

### 3. Resource Efficiency
- **GCS storage**: ~5GB for 100 videos instead of ~50GB for 1000 duplicate requests
- **YouTube API**: Fewer requests to YouTube (respectful scraping)
- **Server resources**: Less disk I/O and processing

## Database Indexes

For optimal performance, the following indexes are created automatically:

```python
# Compound index for deduplication lookups
downloads.create_index([("videoInfo.id", 1), ("status", 1)])

# Index for status checks
downloads.create_index("jobId")

# Index for cleanup operations
downloads.create_index("createdAt")
```

These indexes make the deduplication lookup extremely fast, even with millions of downloads in the database.

## Example Scenario

### Scenario: Viral Video

A popular YouTube Short goes viral and 100 users try to download it within an hour:

**Without Deduplication:**
- 100 downloads from YouTube
- 100 uploads to GCS
- 100 files in storage (e.g., 100 × 50MB = 5GB)
- ~10 minutes processing time per request
- Total processing: 1000 minutes (16.7 hours of CPU time)

**With Deduplication:**
- 1 download from YouTube (first user)
- 1 upload to GCS
- 1 file in storage (50MB)
- ~10 minutes for first user
- <1 second for remaining 99 users
- Total processing: 10 minutes

**Savings:**
- Storage: 4.95GB saved (99% reduction)
- Bandwidth: 4.95GB download + 4.95GB upload saved
- Processing time: 990 minutes saved (99% reduction)
- Cost: ~$0.50 saved in GCS costs alone

## Signed URL Considerations

### URL Expiration

Signed URLs expire after 24 hours. This means:

1. **Within 24 hours**: All users get the same signed URL
2. **After 24 hours**: The URL expires, but the file still exists in GCS

### Handling Expired URLs

Currently, if a signed URL expires, users would need to:
1. Request the video again
2. System finds existing file in GCS
3. **Issue**: Old downloadUrl is expired

**Future Enhancement**: Implement URL regeneration for expired links:

```python
# Check if URL is expired (pseudo-code)
if existing_download and is_url_expired(existing_download['downloadUrl']):
    # Regenerate signed URL for existing file
    blob_name = extract_blob_name(existing_download['downloadUrl'])
    download_url = await storage_service.regenerate_signed_url(blob_name)
else:
    download_url = existing_download['downloadUrl']
```

## File Naming and Deduplication

Videos are stored with their title as filename:
- `The Last of Us Brutal Survival Moment shorts.mp4`

**Important**: Deduplication is based on **video ID**, not filename. This means:
- If YouTube changes the video title, we still deduplicate correctly
- Different videos with same title are treated as different files
- The video ID is the source of truth

## Cleanup Strategy

Old files are cleaned up based on creation time (default: 24 hours):

```python
async def cleanup_old_files(self, hours_old: int = 24):
    blobs = self.bucket.list_blobs()
    cutoff_date = datetime.now(timezone.utc) - timedelta(hours=hours_old)

    for blob in blobs:
        if blob.time_created < cutoff_date:
            blob.delete()
```

**Note**: After cleanup, if a user requests the same video, it will be re-downloaded and re-uploaded. This is by design to balance storage costs with performance.

## Monitoring

To monitor deduplication effectiveness, you can query MongoDB:

```javascript
// Total unique videos
db.downloads.distinct("videoInfo.id").length

// Total download requests
db.downloads.count()

// Deduplication ratio
(total_requests - unique_videos) / total_requests * 100
```

Example output:
- Unique videos: 150
- Total requests: 500
- Deduplication ratio: 70% (350 requests saved)

## Future Enhancements

### 1. Cache Warming
Pre-download popular videos during off-peak hours

### 2. Smart Expiration
Extend expiration for frequently accessed videos

### 3. URL Regeneration
Automatically regenerate expired signed URLs

### 4. Analytics
Track which videos are most popular and cache them longer

### 5. CDN Integration
Use Cloud CDN for even faster delivery of popular videos

## Code Locations

- **Deduplication logic**: [app/queue/tasks.py:60-76](c:\Users\7plus8\build\ytd\backend-python\app\queue\tasks.py#L60-L76)
- **Index creation**: [app/config/database.py:40-55](c:\Users\7plus8\build\ytd\backend-python\app\config\database.py#L40-L55)
- **Storage service**: [app/services/storage_service.py](c:\Users\7plus8\build\ytd\backend-python\app\services\storage_service.py)

## Testing

To test deduplication:

1. Download a video (note the jobId)
2. Wait for completion
3. Download the same video again with a different request
4. Check logs for: `"Video {video_id} already exists in GCS, reusing existing file"`
5. Second request should complete much faster (seconds vs minutes)

## Conclusion

The deduplication system significantly improves:
- **Performance**: Instant results for duplicate requests
- **Cost efficiency**: 90%+ reduction in storage and bandwidth
- **User experience**: Faster downloads for popular videos
- **Scalability**: Handle viral videos without overwhelming resources

This implementation balances storage costs (24-hour cleanup) with performance benefits (instant deduplication within 24 hours).
