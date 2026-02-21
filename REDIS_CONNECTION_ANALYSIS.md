# Redis Connection Analysis & Fix

## Problem Identified

You have **24 zombie Redis connections** remaining even after stopping servers. This is caused by:

1. **Connection leaks** - Services create Redis clients but never close them
2. **Free tier limit** - Redis Cloud free tier only supports **30 max connections** (not 100)
3. **Multiple unclosed clients** - CookieRefreshService, WebSocketManager, and per-WebSocket pub/sub clients

---

## Redis Cloud Free Tier Limits

**Confirmed for 2026:**
- **30 max concurrent connections** (NOT 100)
- 30 MB storage
- Single database

Source: [Redis Cloud Essentials Plan Details](https://redis.io/docs/latest/operate/rc/subscriptions/view-essentials-subscription/essentials-plan-details/)

To get 100+ connections, you need to upgrade to a paid plan:
- **Redis Cloud Flexible**: No connection limits, ~$5-10/month
- **Self-hosted Redis**: Unlimited connections, free but requires server maintenance

---

## Current Connection Usage (Before Fix)

### Backend-Python Connections per Server:

| Component | Count | Pool Size | Notes |
|-----------|-------|-----------|-------|
| Main Async Redis Client | 1 | 10 connections | ✅ Properly pooled |
| Celery Broker | 1 | 5 connections | ✅ Properly pooled |
| Celery Result Backend | 1 | 5 connections | ✅ Properly pooled |
| WebSocket Manager | 1 | No pool | ❌ **Never closed** |
| Cookie Refresh Service | 1 | No pool | ❌ **Never closed** |
| WebSocket Pub/Sub (per connection) | N | No pool | ⚠️ Closed in finally block, but creates many |

**Estimated per server:** 10 + 5 + 5 + 1 + 1 + N WebSocket = ~22+ connections

### Cookie-Extractor Connections:

| Component | Count | Notes |
|-----------|-------|-------|
| Bull Queue Worker | 1 | ✅ Uses ioredis with internal pooling |
| Trigger Script (when run) | 1 | ✅ Closes after use |

**Estimated:** ~2-3 connections

### Total (1 Backend Server + Cookie Extractor):
- **~25-30 connections** → At or over the 30 limit!

With 2 backend servers (multi-server setup):
- **~50-60 connections** → **WAY over the 30 limit!** ❌

---

## Fixes Applied

### 1. Added Connection Closing Methods

**File:** `app/services/cookie_refresh_service.py`
```python
def close(self):
    """Close Redis connection"""
    if self.redis_client:
        try:
            self.redis_client.close()
            logger.info("Cookie refresh service Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing cookie refresh Redis connection: {e}")
```

**File:** `app/websocket/__init__.py`
```python
def close(self):
    """Close Redis connection"""
    if self.redis_client:
        try:
            self.redis_client.close()
            logger.info("WebSocket manager Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing WebSocket manager Redis connection: {e}")
```

### 2. Call Close Methods on Shutdown

**File:** `app/main.py`
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... startup code ...

    yield

    # Shutdown - close all Redis connections
    from app.services.cookie_refresh_service import cookie_refresh_service
    from app.websocket import manager

    cookie_refresh_service.close()
    manager.close()
    await redis_client.close()
    await close_mongo_connection()
```

---

## Expected Results After Fix

### Single Backend Server + Cookie Extractor:

| Component | Connections | Notes |
|-----------|-------------|-------|
| Main Async Redis Client | ~5-8 | Pooled, fewer active connections |
| Celery Broker + Backend | ~5 | Pooled with max_connections=5 |
| WebSocket Manager | 1 | ✅ Now properly closed on shutdown |
| Cookie Refresh Service | 1 | ✅ Now properly closed on shutdown |
| Bull Queue Worker | ~2 | Pooled by ioredis |
| **Total** | **~14-16** | ✅ Well under 30 limit |

### With 2 Backend Servers:

| Setup | Connections |
|-------|-------------|
| Server 1 (Backend + Cookie Extractor) | ~14-16 |
| Server 2 (Backend only) | ~12-14 |
| **Total** | **~26-30** | ⚠️ At the limit |

---

## Recommendations

### Option 1: Keep Free Tier with Optimizations ✅ (Current Fix)

**Pros:**
- Free
- Sufficient for 1-2 servers with current fix

**Cons:**
- Limited to ~2 backend servers max
- No room for spikes in WebSocket connections
- Need to carefully monitor connection usage

**Best for:** Development, testing, low-traffic production

---

### Option 2: Upgrade to Redis Cloud Flexible ($7-10/month)

**Pros:**
- **No connection limits**
- More memory (1GB+)
- Better performance
- Can scale to many servers

**Cons:**
- Costs money
- Requires credit card

**Best for:** Production with multiple servers

---

### Option 3: Self-Host Redis on Your Server

**Pros:**
- **Unlimited connections**
- Free (uses existing server resources)
- Better latency (localhost vs remote)
- Full control

**Cons:**
- Requires server maintenance
- Uses server RAM
- Need to set up backups
- Another service to monitor

**Setup:**
```bash
# Install Redis on Debian
sudo apt update
sudo apt install redis-server

# Configure for production
sudo nano /etc/redis/redis.conf
# Set: maxmemory 256mb
# Set: maxmemory-policy allkeys-lru

# Update .env.production
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Restart services
sudo systemctl restart ytd-api ytd-worker ytd-beat
```

**Best for:** Production with cost constraints, multiple servers

---

### Option 4: Hybrid Approach (Recommended for Multi-Server)

Use **self-hosted Redis** on the main server for Celery queues, and keep **Redis Cloud** for Bull queue (cookie-extractor):

**Main server Redis (localhost):**
- Celery broker
- Celery result backend
- Main async client
- WebSocket pub/sub

**Redis Cloud (remote):**
- Bull queue (cookie-extractor)

**Connection usage:**
- Main server: ~20 connections to localhost (unlimited)
- Cookie extractor: ~2 connections to Redis Cloud (well under 30)

**Setup:**
```bash
# Backend .env.production
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Cookie-extractor .env
REDIS_HOST=redis-17684.c10.us-east-1-3.ec2.cloud.redislabs.com
REDIS_PORT=17684
REDIS_PASSWORD=tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM
```

---

## Next Steps

### 1. Deploy Current Fix (Immediate)

Run on server:
```bash
cd /opt/ytdl/backend-python
sudo git pull origin main
sudo systemctl restart ytd-api ytd-worker ytd-beat
```

Wait 30 seconds, then check connections:
```bash
redis-cli -h redis-17684.c10.us-east-1-3.ec2.cloud.redislabs.com \
  -p 17684 \
  -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM \
  INFO clients | grep connected_clients
```

**Expected:** ~14-16 connections (was 24-30)

### 2. Monitor for 24 Hours

Watch connection count every few hours:
```bash
# Check current connections
redis-cli -h ... -p ... -a ... INFO clients | grep connected_clients

# Watch for leaks
watch -n 5 'redis-cli -h ... -p ... -a ... INFO clients | grep connected_clients'
```

### 3. Decide on Long-Term Solution

Based on monitoring results:
- **If staying under 25 connections:** Keep free tier ✅
- **If approaching 30:** Upgrade to paid tier or self-host
- **If planning to add more servers:** Self-host Redis now

---

## Monitoring Commands

### Check Current Connections
```bash
redis-cli -h redis-17684.c10.us-east-1-3.ec2.cloud.redislabs.com \
  -p 17684 \
  -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM \
  INFO clients
```

### Watch Connections in Real-Time
```bash
watch -n 5 'redis-cli -h redis-17684.c10.us-east-1-3.ec2.cloud.redislabs.com -p 17684 -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM INFO clients | grep connected_clients'
```

### Check for Connection Leaks
```bash
# Stop all services
sudo systemctl stop ytd-api ytd-worker ytd-beat

# Wait 10 seconds
sleep 10

# Check connections (should be ~2-3 from cookie-extractor only)
redis-cli -h ... -p ... -a ... INFO clients | grep connected_clients
```

---

## Files Modified

1. ✅ `app/services/cookie_refresh_service.py` - Added close() method
2. ✅ `app/websocket/__init__.py` - Added close() method
3. ✅ `app/main.py` - Added connection cleanup on shutdown

---

## Summary

**Root Cause:** Connection leaks from unclosed Redis clients
**Free Tier Limit:** 30 connections (not 100)
**Fix Applied:** Added proper connection closing on shutdown
**Expected Result:** ~14-16 connections per server (was ~24-30)
**Recommendation:** Deploy fix now, monitor for 24h, then decide if upgrade needed
