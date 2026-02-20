# Cookie Refresh Integration

## Overview

The backend now automatically detects when YouTube cookies are expired or missing and triggers a cookie refresh via the Redis-based cookie extractor system.

## How It Works

```
┌─────────────────────┐
│   User Request      │
│  Download Video     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  YouTube Service    │
│  Attempts Download  │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ Error Check  │
    └──────┬───────┘
           │
           ├─────► Missing cookies file?
           │       ├─► Trigger: "missing_cookies"
           │
           ├─────► "Sign in to confirm you're not a bot"?
           │       ├─► Trigger: "bot_detection"
           │
           └─────► Other errors
                   └─► Normal error handling

┌─────────────────────┐
│  Cookie Refresh     │
│  Service            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Redis Bull Queue   │
│  "cookie-refresh"   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Cookie Extractor   │
│  (Windows Machine)  │
│  - Extract cookies  │
│  - Upload via SCP   │
│  - Restart services │
└─────────────────────┘
```

## Features

### 1. Automatic Detection

The system automatically detects cookie-related errors:

- **Missing cookies file**: When `YT_DLP_COOKIES_FILE` doesn't exist
- **Bot detection**: "Sign in to confirm you're not a bot"
- **Authentication errors**: Login required, age-restricted, etc.
- **HTTP 403 Forbidden**: Request blocked by YouTube

### 2. Redis Bull Queue Integration

Uses the same Bull queue as your existing cookie extractor:
- Queue name: `cookie-refresh`
- Automatic retry with exponential backoff
- Job tracking and status monitoring

### 3. API Endpoints

#### Trigger Cookie Refresh
```bash
POST /api/cookies/trigger-refresh
Content-Type: application/json

{
  "reason": "manual_trigger"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Cookie refresh job triggered successfully",
  "reason": "manual_trigger"
}
```

#### Check Queue Status
```bash
GET /api/cookies/queue-status
```

**Response:**
```json
{
  "success": true,
  "queue": "cookie-refresh",
  "status": {
    "waiting": 0,
    "active": 1,
    "completed": 5,
    "failed": 0,
    "total": 6
  }
}
```

#### Check Cookies File Status
```bash
GET /api/cookies/cookies-status
```

**Response:**
```json
{
  "exists": true,
  "configured": true,
  "path": "/opt/ytdl/youtube_cookies.txt",
  "size_bytes": 1234,
  "last_modified": 1708473600.0,
  "message": "Cookies file found"
}
```

## Configuration

### Environment Variables

```bash
# Redis connection (required)
REDIS_URL=redis://localhost:6379

# YouTube cookies file path (optional)
YT_DLP_COOKIES_FILE=/opt/ytdl/youtube_cookies.txt
```

### Cookie Extractor Setup

Make sure your cookie extractor (Windows machine) is running:

```bash
# Start the Redis worker
npm run worker
```

## Error Detection Patterns

The system triggers cookie refresh when it detects:

```python
[
    "sign in to confirm you're not a bot",
    "sign in to confirm that you",
    "this helps protect our community",
    "confirm you're not a bot",
    "sign-in required",
    "login required",
    "please sign in",
    "age-restricted",
    "members-only",
    "private video",
    "http error 403",
    "forbidden",
    "request blocked",
]
```

## Files Modified/Created

### New Files
- `app/services/cookie_refresh_service.py` - Cookie refresh service
- `app/routes/cookie_routes.py` - Cookie management API endpoints
- `COOKIE_REFRESH_INTEGRATION.md` - This documentation

### Modified Files
- `app/services/youtube_service.py` - Added cookie error detection
- `app/main.py` - Registered cookie routes

## Testing

### 1. Test Cookie Status
```bash
curl http://localhost:3001/api/cookies/cookies-status
```

### 2. Manually Trigger Refresh
```bash
curl -X POST http://localhost:3001/api/cookies/trigger-refresh \
  -H "Content-Type: application/json" \
  -d '{"reason": "test"}'
```

### 3. Check Queue Status
```bash
curl http://localhost:3001/api/cookies/queue-status
```

### 4. Monitor Logs

**Backend:**
```bash
# Watch for cookie refresh triggers
sudo journalctl -u ytd-backend -f | grep "Cookie refresh"
```

**Cookie Extractor (Windows):**
```bash
# Check worker logs
npm run worker
```

## Workflow Example

1. **User tries to download a video**
   ```
   POST /api/download/
   {
     "url": "https://youtube.com/shorts/..."
   }
   ```

2. **YouTube returns bot detection error**
   ```
   yt-dlp error: "Sign in to confirm you're not a bot"
   ```

3. **Backend detects error and triggers refresh**
   ```
   [2026-02-20 12:00:00] WARNING: 🔄 Cookie refresh needed for video abc123
   [2026-02-20 12:00:00] INFO: ✅ Cookie refresh job created (ID: 42, reason: bot_detection)
   ```

4. **Cookie extractor (Windows) receives job**
   ```
   [2026-02-20 12:00:01] Processing job 42...
   [2026-02-20 12:00:02] Extracting cookies from Chrome
   [2026-02-20 12:00:03] Uploading to server via SCP
   [2026-02-20 12:00:04] Restarting services
   [2026-02-20 12:00:05] ✓ Job completed
   ```

5. **Backend automatically retries download**
   - Services restarted with fresh cookies
   - Next download attempt uses new cookies
   - Download succeeds ✓

## Production Deployment

### 1. Backend (Server)
```bash
# Ensure Redis is accessible
redis-cli ping

# Restart backend to load new code
sudo systemctl restart ytd-backend ytd-celery
```

### 2. Cookie Extractor (Windows)

**Option 1: Run as Windows Service (NSSM)**
```powershell
nssm install CookieRefreshWorker
nssm set CookieRefreshWorker Application "C:\Program Files\nodejs\node.exe"
nssm set CookieRefreshWorker AppParameters "redis-worker.js"
nssm set CookieRefreshWorker AppDirectory "C:\path\to\cookie-extractor"
nssm start CookieRefreshWorker
```

**Option 2: Run as Scheduled Task**
```powershell
# Create scheduled task that runs on startup
schtasks /create /tn "CookieRefreshWorker" /tr "npm run worker" /sc onstart
```

## Monitoring

### Dashboard Metrics

Add to your monitoring dashboard:

- Cookie refresh jobs triggered (counter)
- Cookie refresh success rate (gauge)
- Time since last cookie refresh (gauge)
- Cookie file age (gauge)

### Alerts

Set up alerts for:
- Cookie file missing for > 5 minutes
- Cookie refresh failures > 3 in 1 hour
- Queue backlog > 10 jobs

## Troubleshooting

### Issue: Cookie refresh not triggering

**Check:**
```bash
# Is Redis accessible?
redis-cli ping

# Are logs showing detection?
sudo journalctl -u ytd-backend -f | grep -i cookie
```

### Issue: Jobs created but not processed

**Check:**
```bash
# Is worker running?
# On Windows machine:
tasklist | findstr node

# Check queue
curl http://localhost:3001/api/cookies/queue-status
```

### Issue: Cookies uploaded but still getting errors

**Check:**
```bash
# Was file uploaded?
ls -la /opt/ytdl/youtube_cookies.txt

# Were services restarted?
sudo systemctl status ytd-backend

# Are cookies valid?
curl http://localhost:3001/api/cookies/cookies-status
```

## Security Considerations

1. **Secure the cookie routes**: Add authentication middleware for production
2. **Encrypt cookies during transfer**: SCP uses SSH encryption by default
3. **Limit cookie file permissions**: `chmod 600 youtube_cookies.txt`
4. **Monitor for abuse**: Rate limit the trigger endpoint
5. **Rotate cookies regularly**: Set up periodic refresh (e.g., weekly)

## Future Enhancements

- [ ] Add webhook notifications when cookies are refreshed
- [ ] Implement cookie health check endpoint
- [ ] Add metrics to Prometheus
- [ ] Create Grafana dashboard
- [ ] Add email alerts for repeated failures
- [ ] Implement automatic cookie validation
- [ ] Add support for multiple cookie sources
