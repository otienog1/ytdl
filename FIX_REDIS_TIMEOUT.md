# Fix Redis Timeout Errors

## Problem

```
redis.exceptions.TimeoutError: Timeout reading from socket
```

This error occurs when:
1. Redis server is slow to respond
2. Network latency between server and Redis
3. Redis server is overloaded
4. Connection pool exhausted

## Current Configuration

Your Redis server: `57.159.27.119:6379`

---

## Immediate Fixes

### Fix 1: Increase Redis Timeout in Backend

Edit `/opt/ytdl/.env.production` on **all servers**:

```bash
# Add these lines or update existing ones
REDIS_CONNECT_TIMEOUT=10
REDIS_SOCKET_TIMEOUT=10
```

Then restart services:
```bash
sudo systemctl restart ytd-api ytd-worker ytd-beat
```

### Fix 2: Update Celery Configuration

Edit `/opt/ytdl/backend-python/app/queue/celery_app.py`:

**Add longer timeouts:**

```python
celery_app.conf.update(
    # ... existing config ...

    # Increase Redis timeouts
    broker_transport_options={
        'max_connections': 5,
        'socket_keepalive': True,
        'socket_timeout': 30,  # Increase from 5 to 30
        'socket_connect_timeout': 30,  # Increase from 5 to 30
        'visibility_timeout': 43200,  # 12 hours
    },
    result_backend_transport_options={
        'max_connections': 5,
        'socket_keepalive': True,
        'socket_timeout': 30,  # Increase from 5 to 30
        'socket_connect_timeout': 30,  # Increase from 5 to 30
        'retry_on_timeout': True,
    },
)
```

Restart:
```bash
cd /opt/ytdl/backend-python
sudo git pull origin main  # If changes committed
sudo systemctl restart ytd-worker ytd-beat
```

### Fix 3: Update Redis Client Configuration

Edit `/opt/ytdl/backend-python/app/config/redis_client.py`:

```python
async def connect(self):
    """Connect to Redis with connection pooling"""
    try:
        self._client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=10,
            socket_keepalive=True,
            socket_connect_timeout=30,  # Increase from 5 to 30
            socket_timeout=30,  # Add this
            retry_on_timeout=True,
            retry_on_error=[redis.exceptions.TimeoutError],  # Add this
            health_check_interval=30,  # Add this
        )
        await self._client.ping()
        logger.info("Redis connected successfully with connection pooling")
    except Exception as e:
        logger.error(f"Redis connection error: {e}")
        raise
```

---

## Diagnostic Steps

### 1. Test Redis Connection from Server

```bash
# From ytd.timobosafaris.com
redis-cli -h 57.159.27.119 -p 6379 -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM PING

# Measure latency
redis-cli -h 57.159.27.119 -p 6379 -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM --latency

# Measure latency over time (Ctrl+C to stop)
redis-cli -h 57.159.27.119 -p 6379 -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM --latency-history
```

**Expected latency:**
- Good: < 10ms
- Acceptable: 10-50ms
- Poor: 50-100ms
- **Bad: > 100ms** (will cause timeouts)

### 2. Check Redis Server Status

```bash
# Connect to Redis server
ssh admin@57.159.27.119

# Check if Redis is running
sudo systemctl status redis

# Check Redis logs
sudo journalctl -u redis -n 100

# Check Redis stats
redis-cli INFO stats
redis-cli INFO clients
redis-cli INFO memory
```

### 3. Check Network Connectivity

```bash
# From ytd.timobosafaris.com to Redis server
ping -c 10 57.159.27.119

# Traceroute to see network path
traceroute 57.159.27.119

# Test port specifically
nc -zv 57.159.27.119 6379
```

### 4. Check Redis Server Load

```bash
# On Redis server (57.159.27.119)
redis-cli INFO stats | grep -E "instantaneous_ops_per_sec|total_commands_processed"
redis-cli INFO cpu
redis-cli SLOWLOG get 10  # Show slow queries
```

---

## Long-Term Solutions

### Solution 1: Use Local Redis (Recommended)

Instead of remote Redis, install Redis locally on **each** server:

#### On Each Server (ytd.timobosafaris.com, GCP, AWS)

```bash
# Install Redis
sudo apt update
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf

# Set these:
bind 127.0.0.1 ::1
maxmemory 512mb
maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis
sudo systemctl enable redis

# Test
redis-cli PING  # Should return PONG
```

#### Update Backend Configuration

**IMPORTANT:** Each server uses **LOCAL Redis** for Celery, but **SHARED Redis** for Bull queue (cookie-extractor).

Edit `/opt/ytdl/.env.production` on each server:

```bash
# Local Redis for Celery (Fast, no network latency)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Keep using remote Redis for async client if needed
# Or also use localhost:
# REDIS_URL=redis://localhost:6379/0
```

**For Cookie Extractor** (still uses shared Redis):

Keep in `cookie-extractor/.env`:
```bash
REDIS_HOST=57.159.27.119  # Keep shared Redis for Bull queue
REDIS_PORT=6379
REDIS_PASSWORD=tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM
REDIS_DB=0
```

**Restart services:**
```bash
sudo systemctl restart ytd-api ytd-worker ytd-beat
```

**Benefits:**
- ✅ Zero network latency (localhost)
- ✅ Unlimited connections
- ✅ No timeout errors
- ✅ Each server independent
- ✅ Bull queue still shared for cookie coordination

### Solution 2: Optimize Remote Redis

If you must use remote Redis (57.159.27.119):

#### On Redis Server (57.159.27.119)

```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Optimize for network usage
tcp-backlog 511
tcp-keepalive 300
timeout 0

# Increase client connections
maxclients 10000

# Memory optimization
maxmemory 2gb
maxmemory-policy allkeys-lru

# Disable slow commands if not needed
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""

# Restart
sudo systemctl restart redis
```

#### Enable Redis Persistence (Optional)

```bash
# In /etc/redis/redis.conf
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
```

### Solution 3: Add Redis Sentinel (High Availability)

For production, consider Redis Sentinel for automatic failover:

```bash
# Install on 3 servers
sudo apt install redis-sentinel

# Configure sentinel.conf
# ... (complex setup, consult Redis docs)
```

---

## Quick Fix Script

Create and run this on the server:

```bash
#!/bin/bash
# fix-redis-timeout.sh

echo "Fixing Redis timeout issues..."

# Increase timeouts in celery config
sudo sed -i 's/socket_timeout.*5/socket_timeout: 30/' /opt/ytdl/backend-python/app/queue/celery_app.py
sudo sed -i 's/socket_connect_timeout.*5/socket_connect_timeout: 30/' /opt/ytdl/backend-python/app/queue/celery_app.py

# Increase timeouts in redis client
sudo sed -i 's/socket_connect_timeout=5/socket_connect_timeout=30/' /opt/ytdl/backend-python/app/config/redis_client.py

# Restart services
sudo systemctl restart ytd-api ytd-worker ytd-beat

echo "Done! Services restarted with longer timeouts."
echo "Monitor logs: sudo journalctl -u ytd-worker -f"
```

Run it:
```bash
chmod +x fix-redis-timeout.sh
sudo ./fix-redis-timeout.sh
```

---

## Monitoring After Fix

### Watch for Timeout Errors

```bash
# Real-time monitoring
sudo journalctl -u ytd-worker -f | grep -i timeout

# Check if errors persist
sudo journalctl -u ytd-worker --since "10 minutes ago" | grep "TimeoutError" | wc -l
```

### Check Redis Latency

```bash
# Continuous latency monitoring
redis-cli -h 57.159.27.119 -p 6379 -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM --latency-history

# Stop with Ctrl+C
```

### Check Connection Count

```bash
redis-cli -h 57.159.27.119 -p 6379 -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM CLIENT LIST | wc -l
```

---

## Recommended Architecture

**Hybrid Approach (Best for your setup):**

```
Server 1 (ytd.timobosafaris.com):
  - Celery → Local Redis (127.0.0.1:6379)  ← Fast, no network
  - Cookie Extractor → Shared Redis (57.159.27.119:6379)  ← Coordination

Server 2 (GCP):
  - Celery → Local Redis (127.0.0.1:6379)  ← Fast, no network
  - Cookie Extractor → Shared Redis (57.159.27.119:6379)  ← Coordination

Server 3 (AWS):
  - Celery → Local Redis (127.0.0.1:6379)  ← Fast, no network
  - Cookie Extractor → Shared Redis (57.159.27.119:6379)  ← Coordination
```

**Benefits:**
- ✅ Celery has zero latency (local Redis)
- ✅ No timeout errors for task queue
- ✅ Cookie extractors still coordinate via shared Redis
- ✅ Best of both worlds

---

## Summary

**Immediate action:**
1. Increase timeouts to 30 seconds in Celery and Redis client configs
2. Restart services
3. Monitor for errors

**Long-term solution:**
1. Install local Redis on each server for Celery
2. Keep shared Redis for cookie extractor coordination
3. Update `.env.production` to use `localhost:6379` for Celery

**Check if timeout errors stop:**
```bash
sudo journalctl -u ytd-worker --since "1 hour ago" | grep TimeoutError
# Should return nothing after fix
```
