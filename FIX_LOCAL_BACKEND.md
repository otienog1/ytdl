# Fix Local Backend Server Issue

## Problem

Your backend servers have **different API routes**:

- **GCP (34.57.68.120) & AWS (13.60.71.187):** Working, but redirect `/api/health` → `/api/health/` (307)
- **Local (127.0.0.1):** Returns 404 for `/api/health` - **routes are different!**

## Diagnosis

### Remote Servers (GCP & AWS)
```bash
$ curl -I http://34.57.68.120:3001/api/health
HTTP/1.1 307 Temporary Redirect
location: http://34.57.68.120:3001/api/health/
```

**Cause:** FastAPI requires trailing slash for this endpoint.

**Fix:** Use `/api/health/` instead of `/api/health`

### Local Server (127.0.0.1)
```bash
$ curl http://127.0.0.1:3001/api/health
{"detail":"Not Found"}
```

**Cause:** Local backend has different code or routes not loaded.

---

## Solution 1: Check Local Backend Code

### Step 1: Check what routes are available

```bash
# Check API documentation
curl http://127.0.0.1:3001/docs

# Or check specific route file
cat /opt/ytdl/backend-python/app/routes/health.py
```

### Step 2: Check if health route exists

```bash
# Search for health endpoint in code
grep -r "health" /opt/ytdl/backend-python/app/routes/
```

**Expected file:** `/opt/ytdl/backend-python/app/routes/health.py`

**Expected content:**
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "cookies_available": True,
        # ...
    }
```

### Step 3: Check if health router is included in main.py

```bash
cat /opt/ytdl/backend-python/app/main.py | grep health
```

**Expected:**
```python
from app.routes import health

app.include_router(health.router, prefix="/api/health", tags=["health"])
```

---

## Solution 2: Update Local Backend Code

### Pull Latest Code

```bash
cd /opt/ytdl/backend-python
sudo git pull origin main
```

### Check Current Branch/Commit

```bash
cd /opt/ytdl/backend-python
git log --oneline -5
git status
```

### Compare with Remote Servers

```bash
# On GCP server
ssh admin@34.57.68.120
cd /opt/ytdl/backend-python
git log --oneline -1

# On AWS server
ssh admin@13.60.71.187
cd /opt/ytdl/backend-python
git log --oneline -1

# Compare with local
cd /opt/ytdl/backend-python
git log --oneline -1
```

**All should show same commit!** If not, pull latest code.

### Restart Services

```bash
sudo systemctl restart ytd-api ytd-worker ytd-beat

# Wait a few seconds
sleep 3

# Test
curl http://127.0.0.1:3001/api/health/
```

---

## Solution 3: Check Local Backend Logs

### View Recent Errors

```bash
sudo journalctl -u ytd-api -n 100 --no-pager
```

**Look for:**
- Import errors
- Route registration errors
- Port binding issues
- Module not found errors

### Check Service Status

```bash
sudo systemctl status ytd-api -l
```

### Check if Backend is Actually Running

```bash
# Check process
ps aux | grep uvicorn

# Check port
sudo netstat -tlnp | grep 3001
# Should show: 127.0.0.1:3001 or 0.0.0.0:3001

# Test root endpoint
curl http://127.0.0.1:3001/
```

---

## Solution 4: Rebuild Backend Environment

If code is correct but still not working:

### Reinstall Dependencies

```bash
cd /opt/ytdl/backend-python

# Rebuild virtual environment
sudo rm -rf .venv
pipenv install

# Or use start-dev.sh
sudo bash start-dev.sh
```

### Restart Services

```bash
sudo systemctl restart ytd-api ytd-worker ytd-beat
```

---

## Solution 5: Use Correct Endpoint with Trailing Slash

All backends require **trailing slash** for `/api/health/`:

### Test with Trailing Slash

```bash
# Local
curl http://127.0.0.1:3001/api/health/

# GCP
curl http://34.57.68.120:3001/api/health/

# AWS
curl http://13.60.71.187:3001/api/health/
```

**All should return 200 OK with JSON response.**

### Update Nginx to Use Trailing Slash

I've already updated `nginx-ytd-timobosafaris-updated.conf` to use `/api/health/` (with trailing slash).

---

## Quick Diagnosis Script

Run this to check all backends:

```bash
#!/bin/bash
echo "Testing all backends with trailing slash:"
echo ""

echo "Local (127.0.0.1):"
curl -s http://127.0.0.1:3001/api/health/ | jq '.status, .account_id' || echo "FAILED"

echo ""
echo "GCP (34.57.68.120):"
curl -s http://34.57.68.120:3001/api/health/ | jq '.status, .account_id' || echo "FAILED"

echo ""
echo "AWS (13.60.71.187):"
curl -s http://13.60.71.187:3001/api/health/ | jq '.status, .account_id' || echo "FAILED"
```

Save as `test-backends-slash.sh`, then:
```bash
chmod +x test-backends-slash.sh
./test-backends-slash.sh
```

---

## Expected Results After Fix

### All Backends Should Return:

```bash
$ curl http://127.0.0.1:3001/api/health/
{
  "status": "healthy",
  "cookies_available": true,
  "refresh_in_progress": false,
  "account_id": "account_a",
  "can_process_downloads": true
}

$ curl http://34.57.68.120:3001/api/health/
{
  "status": "healthy",
  "cookies_available": true,
  "refresh_in_progress": false,
  "account_id": "account_b",
  "can_process_downloads": true
}

$ curl http://13.60.71.187:3001/api/health/
{
  "status": "healthy",
  "cookies_available": true,
  "refresh_in_progress": false,
  "account_id": "account_c",
  "can_process_downloads": true
}
```

---

## Most Likely Issue

Based on your symptoms, **the local backend (127.0.0.1) is running older code** that doesn't have the health endpoint.

**Quick fix:**

```bash
cd /opt/ytdl/backend-python
sudo git pull origin main
sudo systemctl restart ytd-api ytd-worker ytd-beat
sleep 3
curl http://127.0.0.1:3001/api/health/
```

If that works ✅, then update nginx config and enable load balancing!

---

## After Everything Works

Once all 3 backends respond correctly to `/api/health/`:

1. **Update nginx configuration** (already done in updated config file)
2. **Test nginx config:** `sudo nginx -t`
3. **Reload nginx:** `sudo systemctl reload nginx`
4. **Test load balancer:** `curl https://ytd.timobosafaris.com/health`
5. **Test distribution:** Make 30 requests and check account IDs

**You're ready for production load balancing! 🚀**
