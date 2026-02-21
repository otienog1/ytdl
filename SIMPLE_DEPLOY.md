# Simple Deployment Guide - Redis Fix

## Your Repository Structure

Your project has **backend-python as a separate git repository** inside the main ytd folder. Here's how to deploy the fixes:

## Step 1: Deploy Backend-Python Fixes (ALREADY DONE ✅)

The backend-python repository already has all fixes pushed to GitHub:
- Redis connection pooling
- Celery broker limits
- Fix scripts (fix-redis-connections.sh, fix-systemd-paths.sh)

**These are already live on GitHub:** `https://github.com/otienog1/ytdl.git`

## Step 2: Deploy on Server (DO THIS NOW)

SSH into your server and run:

```bash
# Navigate to backend-python directory
cd /opt/ytdl/backend-python

# Pull latest fixes from GitHub
sudo git pull origin main

# Apply all fixes in one command
sudo bash fix-systemd-paths.sh && sudo bash fix-redis-connections.sh
```

That's it! The scripts will:
1. ✅ Update systemd service paths to /opt/ytdl
2. ✅ Apply Redis connection pooling limits
3. ✅ Reduce Celery worker concurrency to 1
4. ✅ Restart all services
5. ✅ Show service status

## Verify Fix

After deployment, check Redis connections:

```bash
redis-cli -h redis-17684.c10.us-east-1-3.ec2.cloud.redislabs.com \
  -p 17684 \
  -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM \
  INFO clients | grep connected_clients
```

**Expected result:** `connected_clients:15` (was 30)

## Monitor for Errors

Watch logs for 2-3 minutes:

```bash
sudo journalctl -u ytd-worker -f | grep -i redis
```

If you see no "max clients reached" errors, **the fix is successful!**

## What Changed

### Code Changes (Already Pushed to GitHub):

1. **Redis Connection Pooling** - [app/config/redis_client.py](https://github.com/otienog1/ytdl/blob/main/app/config/redis_client.py)
   - Max 10 connections per client
   - Socket keepalive enabled
   - Connection timeout: 5 seconds

2. **Celery Connection Limits** - [app/queue/celery_app.py](https://github.com/otienog1/ytdl/blob/main/app/queue/celery_app.py)
   - Broker pool limit: 5 connections
   - Backend pool limit: 5 connections
   - Socket keepalive enabled

3. **Worker Concurrency** - [fix-redis-connections.sh](https://github.com/otienog1/ytdl/blob/main/fix-redis-connections.sh)
   - Reduced from 2 to 1 concurrent task
   - Saves ~6 Redis connections

### Connection Usage:

**Before Fix:**
```
API Server:      ~10 connections
Celery Worker:   ~12 connections (2 concurrent)
Celery Beat:     ~8 connections
------------------------
Total:           ~30 connections ❌ (at limit)
```

**After Fix:**
```
API Server:      ~5 connections (pooled)
Celery Worker:   ~6 connections (1 concurrent, pooled)
Celery Beat:     ~4 connections (pooled)
------------------------
Total:           ~15 connections ✅ (50% usage)
```

## Troubleshooting

### If services fail after deployment:

```bash
# Check service logs
sudo journalctl -u ytd-worker -n 100
sudo journalctl -u ytd-api -n 100

# Restart services
sudo systemctl restart ytd-api ytd-worker ytd-beat

# Check status
sudo systemctl status ytd-api ytd-worker ytd-beat
```

### If still getting "max clients" after 5 minutes:

```bash
# Manually restart all services to clear connections
sudo systemctl stop ytd-api ytd-worker ytd-beat
sleep 5
sudo systemctl start ytd-api ytd-worker ytd-beat

# Verify connection count
redis-cli -h redis-17684.c10.us-east-1-3.ec2.cloud.redislabs.com \
  -p 17684 \
  -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM \
  INFO clients | grep connected_clients
```

## Success Criteria

✅ Redis connections under 20
✅ No "max clients reached" errors in logs
✅ All three services running (api, worker, beat)
✅ Downloads work successfully

---

## Quick Command (Copy & Paste)

```bash
cd /opt/ytdl/backend-python && \
sudo git pull origin main && \
sudo bash fix-systemd-paths.sh && \
sudo bash fix-redis-connections.sh
```

**Deployment time:** ~30 seconds
