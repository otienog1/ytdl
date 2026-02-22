# Nginx Load Balancer Setup Guide

## Architecture Overview

```
Internet
    ↓
Nginx Load Balancer (Port 80/443)
    ↓
    ├─→ Backend Server 1 (57.159.27.119:3001) - Account A
    ├─→ Backend Server 2 (xxx.xxx.xxx.xxx:3001) - Account B
    └─→ Backend Server N (xxx.xxx.xxx.xxx:3001) - Account N
         ↓
    Shared Redis (57.159.27.119:6379)
    Shared MongoDB (mongoatlas_user@...)
```

**Key Features:**
- ✅ Automatic failover when cookies expire (HTTP 503)
- ✅ Health checks on each backend
- ✅ WebSocket support for real-time progress
- ✅ Load distribution (least connections)
- ✅ Session persistence option (ip_hash)

---

## Prerequisites

1. **Multiple backend servers** running ytdl API on port 3001
2. **Each server** has unique YouTube account cookies
3. **Shared Redis** server accessible to all backends
4. **Nginx** installed on load balancer server

---

## Step 1: Configure Backend Servers

Each backend server needs a unique account ID and cookie file.

### Server 1 (Account A) - /opt/ytdl/.env.production

```bash
# Account Configuration
YT_ACCOUNT_ID=account_a
YT_DLP_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_a.txt

# Database (Shared)
MONGODB_URI=mongodb+srv://mongoatlas_user:yZNOgPARUbX5c20k@scrapperclusteraws.yhrl4e7.mongodb.net/ytdl_db?appName=ScrapperClusterAWS

# Redis (Shared)
REDIS_URL=redis://mdlworker:tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM@57.159.27.119:6379
CELERY_BROKER_URL=redis://mdlworker:tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM@57.159.27.119:6379/0
CELERY_RESULT_BACKEND=redis://mdlworker:tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM@57.159.27.119:6379/0

# Storage (Shared)
GCP_PROJECT_ID=divine-actor-473706-k4
GCP_BUCKET_NAME=ytdl_bkt
GOOGLE_APPLICATION_CREDENTIALS=gcp-credentials.json

# Server Configuration
PORT=3001
ENVIRONMENT=production
CORS_ORIGINS=https://ytshortsdownload.vercel.app,https://ytd-bay.vercel.app
```

### Server 2 (Account B) - /opt/ytdl/.env.production

```bash
# Account Configuration (DIFFERENT)
YT_ACCOUNT_ID=account_b
YT_DLP_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_b.txt

# Database (SAME as Server 1)
MONGODB_URI=mongodb+srv://mongoatlas_user:yZNOgPARUbX5c20k@scrapperclusteraws.yhrl4e7.mongodb.net/ytdl_db?appName=ScrapperClusterAWS

# Redis (SAME as Server 1)
REDIS_URL=redis://mdlworker:tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM@57.159.27.119:6379
CELERY_BROKER_URL=redis://mdlworker:tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM@57.159.27.119:6379/0
CELERY_RESULT_BACKEND=redis://mdlworker:tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM@57.159.27.119:6379/0

# Storage (SAME as Server 1)
GCP_PROJECT_ID=divine-actor-473706-k4
GCP_BUCKET_NAME=ytdl_bkt
GOOGLE_APPLICATION_CREDENTIALS=gcp-credentials.json

# Server Configuration (SAME)
PORT=3001
ENVIRONMENT=production
CORS_ORIGINS=https://ytshortsdownload.vercel.app,https://ytd-bay.vercel.app
```

**Important:** Only `YT_ACCOUNT_ID` and `YT_DLP_COOKIES_FILE` differ between servers!

---

## Step 2: Install and Configure Nginx

### On Load Balancer Server

```bash
# Install Nginx
sudo apt update
sudo apt install nginx

# Create configuration
sudo nano /etc/nginx/sites-available/ytd-loadbalancer
```

Paste the contents of `nginx-load-balancer.conf` (provided separately).

**Update these values:**
1. `server_name` - Your domain (e.g., api.ytshortsdownload.com)
2. `server` lines in `upstream ytd_backend` - Your backend server IPs

Example:
```nginx
upstream ytd_backend {
    least_conn;

    # Server 1 - Account A
    server 57.159.27.119:3001 max_fails=3 fail_timeout=30s;

    # Server 2 - Account B
    server 192.168.1.102:3001 max_fails=3 fail_timeout=30s;

    keepalive 32;
}
```

### Enable and Test Configuration

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ytd-loadbalancer /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check status
sudo systemctl status nginx
```

---

## Step 3: Configure Cookie Extractors

Each server should run a cookie extractor for its account.

### Server 1 - Cookie Extractor .env

```bash
# Redis (Shared)
REDIS_HOST=57.159.27.119
REDIS_PORT=6379
REDIS_PASSWORD=tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM
REDIS_DB=0

# Account Configuration
ACCOUNT_ID=account_a
COOKIES_OUTPUT_PATH=/opt/ytdl/youtube_cookies_account_a.txt

# YouTube Account Credentials
YT_EMAIL=account_a@example.com
YT_PASSWORD=password_for_account_a

# Browser Configuration
HEADLESS=true
CHROME_PATH=/usr/bin/chromium
```

### Server 2 - Cookie Extractor .env

```bash
# Redis (SAME)
REDIS_HOST=57.159.27.119
REDIS_PORT=6379
REDIS_PASSWORD=tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM
REDIS_DB=0

# Account Configuration (DIFFERENT)
ACCOUNT_ID=account_b
COOKIES_OUTPUT_PATH=/opt/ytdl/youtube_cookies_account_b.txt

# YouTube Account Credentials (DIFFERENT)
YT_EMAIL=account_b@example.com
YT_PASSWORD=password_for_account_b

# Browser Configuration (SAME)
HEADLESS=true
CHROME_PATH=/usr/bin/chromium
```

---

## Step 4: Test Load Balancing

### Test 1: Basic Health Check

```bash
# Check each backend directly
curl http://57.159.27.119:3001/api/health
curl http://192.168.1.102:3001/api/health

# Check through load balancer
curl http://your-lb-domain/health
```

Expected response (when cookies available):
```json
{
  "status": "healthy",
  "cookies_available": true,
  "refresh_in_progress": false,
  "account_id": "account_a",
  "can_process_downloads": true
}
```

### Test 2: Automatic Failover

1. **Stop cookies on Server 1:**
   ```bash
   # On Server 1
   sudo mv /opt/ytdl/youtube_cookies_account_a.txt /opt/ytdl/youtube_cookies_account_a.txt.bak
   ```

2. **Make request through load balancer:**
   ```bash
   curl -X POST http://your-lb-domain/api/download/ \
     -H "Content-Type: application/json" \
     -d '{"url": "https://youtube.com/shorts/xxxxx"}'
   ```

3. **Observe:**
   - Server 1 returns 503 (cookies unavailable)
   - Nginx retries on Server 2
   - Server 2 processes the download
   - ✅ Request succeeds!

4. **Restore Server 1:**
   ```bash
   sudo mv /opt/ytdl/youtube_cookies_account_a.txt.bak /opt/ytdl/youtube_cookies_account_a.txt
   ```

### Test 3: Load Distribution

```bash
# Make 10 requests
for i in {1..10}; do
  curl -s -w "\nBackend: %{http_code}\n" \
    http://your-lb-domain/health | grep account_id
done
```

Expected: Requests distributed across servers (if using `least_conn`)

### Test 4: WebSocket Connection

```bash
# Test WebSocket through load balancer
wscat -c ws://your-lb-domain/api/ws/test-job-id
```

Expected: WebSocket connects and receives updates

---

## Step 5: Configure SSL (Optional but Recommended)

### Using Let's Encrypt (Free SSL)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.ytshortsdownload.com

# Auto-renewal test
sudo certbot renew --dry-run
```

Certbot will automatically update your nginx config to use HTTPS.

### Verify SSL

```bash
curl -I https://api.ytshortsdownload.com/health
```

---

## Step 6: Update Frontend Configuration

Update your frontend to use the load balancer URL:

### Vercel Environment Variables

```bash
NEXT_PUBLIC_API_URL=https://api.ytshortsdownload.com
NEXT_PUBLIC_WS_URL=wss://api.ytshortsdownload.com
```

---

## Monitoring and Troubleshooting

### Check Nginx Access Logs

```bash
tail -f /var/log/nginx/ytd-lb-access.log
```

### Check Nginx Error Logs

```bash
tail -f /var/log/nginx/ytd-lb-error.log
```

### Check Upstream Status

```bash
# Basic status
curl http://localhost:8080/nginx_status

# Detailed backend health
for server in server1 server2; do
  echo "=== $server ==="
  curl http://$server:3001/api/health
done
```

### Monitor Redis Connections

```bash
# On Redis server
redis-cli -h 57.159.27.119 -p 6379 -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM INFO clients | grep connected_clients
```

With 2 backend servers, expect: **~24-32 connections** (12-16 per server)

### Check Backend Logs

```bash
# Server 1
ssh user@57.159.27.119
sudo journalctl -u ytd-api -f

# Server 2
ssh user@192.168.1.102
sudo journalctl -u ytd-api -f
```

---

## Common Issues

### Issue 1: All Requests Go to One Server

**Cause:** Using `ip_hash` with single client IP

**Fix:** Change to `least_conn` in nginx config:
```nginx
upstream ytd_backend {
    least_conn;  # Instead of ip_hash
    ...
}
```

### Issue 2: WebSocket Disconnects Frequently

**Cause:** Timeout too short

**Fix:** Increase WebSocket timeout in nginx:
```nginx
proxy_read_timeout 3600s;  # 1 hour
```

### Issue 3: 503 Errors Even with Cookies Available

**Cause:** Backend not responding to health checks

**Fix:**
1. Check backend is running: `systemctl status ytd-api`
2. Check cookies exist: `ls -la /opt/ytdl/youtube_cookies_*.txt`
3. Check health endpoint: `curl http://backend-ip:3001/api/health`

### Issue 4: Redis Connection Errors

**Cause:** Too many connections

**Fix:**
1. Check connection count (see monitoring above)
2. Increase Redis `maxclients` or upgrade to unlimited plan
3. Reduce Celery concurrency on each server

---

## Load Balancing Methods

### Method 1: Round Robin (Default)

```nginx
upstream ytd_backend {
    # No method specified = round robin
    server server1:3001;
    server server2:3001;
}
```

**Pros:** Simple, evenly distributes load
**Cons:** Doesn't account for server load differences

### Method 2: Least Connections (Recommended)

```nginx
upstream ytd_backend {
    least_conn;
    server server1:3001;
    server server2:3001;
}
```

**Pros:** Balances load based on active connections
**Cons:** Slightly more overhead

### Method 3: IP Hash (Session Persistence)

```nginx
upstream ytd_backend {
    ip_hash;
    server server1:3001;
    server server2:3001;
}
```

**Pros:** Same client always goes to same server
**Cons:** Uneven distribution if few clients

### Method 4: Weighted

```nginx
upstream ytd_backend {
    server server1:3001 weight=3;  # Gets 3x traffic
    server server2:3001 weight=1;
}
```

**Pros:** Useful if servers have different capacities
**Cons:** Manual weight tuning needed

---

## Scaling Up

### Adding More Servers

1. **Deploy new backend server** with unique account ID
2. **Add to nginx upstream** block:
   ```nginx
   server 192.168.1.103:3001 max_fails=3 fail_timeout=30s;
   ```
3. **Reload nginx:**
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```
4. **No downtime!** Existing connections continue

### Removing Servers

1. **Mark server as down** in nginx:
   ```nginx
   server 192.168.1.102:3001 down;
   ```
2. **Reload nginx:**
   ```bash
   sudo systemctl reload nginx
   ```
3. **Wait for connections to drain**
4. **Stop backend services** on old server
5. **Remove from nginx config**

---

## Summary

✅ **Nginx load balancer** distributes requests across multiple backend servers
✅ **Automatic failover** when cookies expire (HTTP 503)
✅ **Independent accounts** - each server has unique YouTube account
✅ **Shared infrastructure** - Redis, MongoDB, Cloud Storage
✅ **WebSocket support** - real-time progress updates
✅ **SSL ready** - Let's Encrypt integration
✅ **Scalable** - add/remove servers without downtime

**Your current setup:**
- Redis: Self-hosted at `57.159.27.119:6379` (unlimited connections ✅)
- MongoDB: Atlas cloud cluster
- Storage: GCP bucket `ytdl_bkt`
- Backend servers: Add as many as needed!

**Next steps:**
1. Deploy second backend server
2. Configure unique account ID and cookies
3. Set up nginx load balancer
4. Test automatic failover
5. Update frontend to use LB URL
