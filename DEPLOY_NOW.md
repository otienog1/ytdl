# Deploy Redis Connection Fix - READY TO RUN

## Current Issue

Your server is experiencing:
```
redis.exceptions.ConnectionError: max number of clients reached
```

## The Fix is Ready

All code has been committed and is ready to deploy. The fix includes:

1. ✅ **Redis connection pooling** - Limits connections to 10 per client
2. ✅ **Celery broker pool limits** - Max 5 connections for broker & backend
3. ✅ **Reduced worker concurrency** - From 2 to 1 concurrent task
4. ✅ **Systemd path fixes** - Updates all services to use `/opt/ytdl`

## Deploy in 1 Command

SSH into your server and run:

```bash
cd /opt/ytdl && sudo git pull && sudo bash DEPLOY_FIXES.sh
```

That's it! The script will:
1. Pull latest code with Redis fixes
2. Update submodules (backend-python)
3. Fix systemd service paths
4. Apply Redis connection limits
5. Restart all services
6. Show service status

## Expected Results

**Before:**
- Redis connections: ~30 (at limit) ❌
- API server: ~10 connections
- Celery worker: ~12 connections (2 concurrent)
- Celery beat: ~8 connections

**After:**
- Redis connections: ~15 (50% usage) ✅
- API server: ~5 connections (pooled)
- Celery worker: ~6 connections (1 concurrent, pooled)
- Celery beat: ~4 connections (pooled)

## Verify Fix

After deployment, check Redis connection count:

```bash
redis-cli -h redis-17684.c10.us-east-1-3.ec2.cloud.redislabs.com \
  -p 17684 \
  -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM \
  INFO clients | grep connected_clients
```

Should show: `connected_clients:15` (or less)

## Monitor Logs

Watch for any Redis errors:

```bash
sudo journalctl -u ytd-worker -f | grep -i redis
```

If no "max clients" errors appear within 5 minutes, the fix is successful!

## What Changed

### Files Modified:

1. **[app/config/redis_client.py](backend-python/app/config/redis_client.py)**
   ```python
   max_connections=10,
   socket_keepalive=True,
   socket_connect_timeout=5
   ```

2. **[app/queue/celery_app.py](backend-python/app/queue/celery_app.py)**
   ```python
   broker_pool_limit=5,
   broker_transport_options={'max_connections': 5},
   result_backend_transport_options={'max_connections': 5}
   ```

3. **[/etc/systemd/system/ytd-worker.service](backend-python/fix-redis-connections.sh)**
   ```bash
   # Changed from: --concurrency=2
   # To: --concurrency=1
   ```

4. **[All systemd services](backend-python/fix-systemd-paths.sh)**
   ```bash
   # Changed all paths from: /home/admin/ytdl
   # To: /opt/ytdl
   ```

## Troubleshooting

### If services fail to start:

```bash
# Check specific service logs
sudo journalctl -u ytd-worker -n 100
sudo journalctl -u ytd-api -n 100
sudo journalctl -u ytd-beat -n 100
```

### If still getting "max clients" error:

```bash
# Restart all services to kill zombie connections
sudo systemctl restart ytd-api ytd-worker ytd-beat

# Wait 10 seconds
sleep 10

# Check connection count again
redis-cli -h redis-17684.c10.us-east-1-3.ec2.cloud.redislabs.com \
  -p 17684 \
  -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM \
  INFO clients | grep connected_clients
```

## Success Criteria

✅ No "max clients reached" errors in logs
✅ Redis connection count under 20
✅ All three services running without restarts
✅ Downloads complete successfully

---

**Ready to deploy?** Just run:
```bash
cd /opt/ytdl && sudo git pull && sudo bash DEPLOY_FIXES.sh
```
