# Deploy Redis Connection Fix

## Quick Fix on Server

SSH into your server and run these commands:

```bash
# 1. Pull latest code
cd /opt/ytdl
sudo git pull

# 2. Run the fix script
sudo bash fix-redis-connections.sh
```

The script will:
✅ Reduce Celery worker concurrency to 1
✅ Reload systemd services
✅ Restart all services with new configuration

## What Was Fixed

### Problem
```
redis.exceptions.ConnectionError: max number of clients reached
```

Redis Cloud free tier limits:
- **30 max connections**
- Your setup was using **30+ connections**

### Solution

**1. Redis Client Connection Pooling**
```python
# app/config/redis_client.py
max_connections=10,  # Limit per client
socket_keepalive=True,
socket_connect_timeout=5
```

**2. Celery Connection Pooling**
```python
# app/queue/celery_app.py
broker_pool_limit=5,
broker_transport_options={'max_connections': 5},
result_backend_transport_options={'max_connections': 5}
```

**3. Reduced Celery Worker Concurrency**
```bash
# Before: --concurrency=2 (uses more connections)
# After:  --concurrency=1 (uses fewer connections)
```

## Connection Usage

### Before Fix
```
API Server:      ~10 connections
Celery Worker:   ~12 connections (2 concurrent tasks)
Celery Beat:     ~8 connections
---
Total:           ~30 connections ❌ (at limit)
```

### After Fix
```
API Server:      ~5 connections (pooled)
Celery Worker:   ~6 connections (1 concurrent, pooled)
Celery Beat:     ~4 connections (pooled)
---
Total:           ~15 connections ✅ (50% usage)
```

## Verify Fix

### Check Redis Connection Count
```bash
redis-cli -h redis-17684.c10.us-east-1-3.ec2.cloud.redislabs.com \
  -p 17684 \
  -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM \
  INFO clients
```

Look for: `connected_clients:15` (should be under 20)

### Monitor Services
```bash
# Watch for connection errors
sudo journalctl -u ytd-worker -f | grep -i redis

# Check service status
sudo systemctl status ytd-api ytd-worker ytd-beat
```

### Test Download
```bash
curl -X POST http://localhost:3001/api/download/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/shorts/..."}'
```

## Alternative Solutions

### Option 1: Upgrade Redis Plan
If you need more connections in the future:
- Redis Cloud Standard: **100 connections** ($5/month)
- Redis Cloud Premium: **500+ connections** ($15/month)

### Option 2: Use Local Redis
```bash
# Install Redis locally on server
sudo apt install redis-server

# Update .env.production
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Restart services
sudo systemctl restart ytd-api ytd-worker ytd-beat
```

**Pros**: Unlimited connections, faster latency
**Cons**: Requires server maintenance

## Monitoring

Add this to cron to alert on high connection usage:

```bash
# /etc/cron.d/redis-monitor
*/5 * * * * root redis-cli -h ... -p ... -a ... INFO clients | \
  grep connected_clients | awk -F: '$2 > 25 {print "WARNING: Redis connections at", $2}'
```

## Troubleshooting

### Still Getting "Max Clients" Error

1. **Check actual connection count**:
   ```bash
   redis-cli INFO clients
   ```

2. **Kill zombie connections**:
   ```bash
   sudo systemctl restart ytd-api ytd-worker ytd-beat
   ```

3. **Check for connection leaks**:
   ```bash
   # Watch connection count in real-time
   watch -n 1 'redis-cli INFO clients | grep connected'
   ```

### Services Won't Start

1. **Check logs**:
   ```bash
   sudo journalctl -u ytd-worker -n 100
   ```

2. **Verify Redis is accessible**:
   ```bash
   redis-cli -h ... -p ... -a ... PING
   ```

3. **Check .env.production**:
   ```bash
   cat /opt/ytdl/.env.production | grep REDIS
   ```

## Files Changed

- ✅ `app/config/redis_client.py` - Connection pooling
- ✅ `app/queue/celery_app.py` - Broker/backend pool limits
- ✅ `fix-redis-connections.sh` - Deployment script
- ✅ `/etc/systemd/system/ytd-worker.service` - Reduced concurrency

## Success Criteria

✅ No "max clients reached" errors in logs
✅ Redis connection count stays under 20
✅ All services running without restarts
✅ Downloads complete successfully
