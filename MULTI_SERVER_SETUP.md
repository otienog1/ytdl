# Multi-Server Setup Guide

## Overview

This guide explains how to deploy the YouTube downloader across multiple servers with independent YouTube accounts for high availability and automatic failover.

## Architecture

```
                    ┌─────────────────┐
                    │ Load Balancer   │
                    │  (nginx/haproxy)│
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼─────┐       ┌────▼─────┐       ┌────▼─────┐
    │ Server 1 │       │ Server 2 │       │ Server 3 │
    │ Account A│       │ Account B│       │ Account C│
    │ Cookies A│       │ Cookies B│       │ Cookies C│
    └────┬─────┘       └────┬─────┘       └────┬─────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Shared Redis   │
                    │  - Queue Jobs   │
                    │  - Cookie Status│
                    │                 │
                    │  Shared MongoDB │
                    │  - Downloads    │
                    │  - History      │
                    └─────────────────┘
```

## Key Features

✅ **Independent YouTube Accounts** - Each server uses a different YouTube account
✅ **Automatic Failover** - Load balancer retries failed requests on healthy servers
✅ **Zero Downtime** - Cookie refresh on one server doesn't affect others
✅ **Scalable** - Add more servers = more capacity
✅ **Redundant** - If one account gets banned, others continue working

## Setup Instructions

### 1. Server Configuration

Each server needs a unique account ID and cookie file path.

#### Server 1 (.env)
```bash
# YouTube Account
YT_ACCOUNT_ID=account_a
YT_DLP_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_a.txt

# Shared resources
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/ytdl_db
REDIS_URL=redis://shared-redis-server:6379
```

#### Server 2 (.env)
```bash
# YouTube Account
YT_ACCOUNT_ID=account_b
YT_DLP_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_b.txt

# Shared resources (same as Server 1)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/ytdl_db
REDIS_URL=redis://shared-redis-server:6379
```

#### Server 3 (.env)
```bash
# YouTube Account
YT_ACCOUNT_ID=account_c
YT_DLP_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_c.txt

# Shared resources (same as Server 1)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/ytdl_db
REDIS_URL=redis://shared-redis-server:6379
```

### 2. Cookie Extractor Configuration

Your Windows cookie extractor needs to support multiple accounts. Update `redis-worker.js`:

```javascript
// Map account IDs to YouTube accounts and server IPs
const ACCOUNT_CONFIG = {
    'account_a': {
        email: 'user1@gmail.com',
        server: 'server1.example.com',
        cookiePath: '/opt/ytdl/youtube_cookies_account_a.txt'
    },
    'account_b': {
        email: 'user2@gmail.com',
        server: 'server2.example.com',
        cookiePath: '/opt/ytdl/youtube_cookies_account_b.txt'
    },
    'account_c': {
        email: 'user3@gmail.com',
        server: 'server3.example.com',
        cookiePath: '/opt/ytdl/youtube_cookies_account_c.txt'
    }
};

queue.process(async (job) => {
    const { account_id, reason } = job.data;
    const config = ACCOUNT_CONFIG[account_id];

    if (!config) {
        throw new Error(`Unknown account: ${account_id}`);
    }

    console.log(`Processing refresh for ${config.email} → ${config.server}`);

    // Extract cookies from specific Chrome profile
    const cookies = await extractCookiesForAccount(config.email);

    // Upload to specific server
    await uploadCookies(cookies, config.server, config.cookiePath);

    // Restart services on specific server
    await restartService(config.server);

    console.log(`✓ Refreshed cookies for ${account_id}`);
});
```

### 3. Load Balancer Configuration

#### Nginx Configuration

```nginx
upstream ytd_backend {
    # Servers with health checks
    server server1.example.com:3001 max_fails=1 fail_timeout=10s;
    server server2.example.com:3001 max_fails=1 fail_timeout=10s;
    server server3.example.com:3001 max_fails=1 fail_timeout=10s;
}

server {
    listen 80;
    server_name ytd.example.com;

    # Main application
    location / {
        proxy_pass http://ytd_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # Automatic retry on failure (including 503)
        proxy_next_upstream error timeout http_503;
        proxy_next_upstream_tries 3;
        proxy_connect_timeout 5s;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://ytd_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # Health check endpoint
    location /api/health {
        proxy_pass http://ytd_backend;
        access_log off;
    }
}
```

#### HAProxy Configuration (Alternative)

```haproxy
frontend ytd_frontend
    bind *:80
    default_backend ytd_backend

backend ytd_backend
    option httpchk GET /api/health
    http-check expect status 200

    server server1 server1.example.com:3001 check inter 5s fall 2 rise 2
    server server2 server2.example.com:3001 check inter 5s fall 2 rise 2
    server server3 server3.example.com:3001 check inter 5s fall 2 rise 2
```

### 4. Shared Resources Setup

#### MongoDB (Shared Database)

All servers connect to the same MongoDB instance:

```bash
# MongoDB Atlas or self-hosted
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/ytdl_db
```

#### Redis (Shared Queue & Cache)

All servers connect to the same Redis instance:

```bash
# Redis Cloud or self-hosted
REDIS_URL=redis://redis.example.com:6379
```

## How It Works

### Normal Operation

```
1. User Request → Load Balancer
2. Routes to Server 2 (round-robin)
3. Server 2: Cookies valid ✓
4. Download succeeds
5. User gets file
```

### Failover Scenario

```
1. User Request → Load Balancer
2. Routes to Server 1
3. Server 1: Cookies expired! ❌
   ├─ Triggers refresh for account_a
   ├─ Returns HTTP 503
   └─ Load balancer sees 503
4. Load Balancer: Auto-retry
   └─ Routes SAME request to Server 2
5. Server 2: Cookies valid ✓
6. Download succeeds immediately
7. User gets file (never knew Server 1 failed)

Meanwhile:
8. Windows Worker: Extracts cookies for account_a
9. Uploads to Server 1
10. Restarts Server 1 services
11. Server 1: Back online ✓
```

### Refresh Prevention

To prevent duplicate refresh jobs:

```
Server 1: Cookies expired
├─ Check Redis: cookie:refresh:account_a:in_progress
│  └─ Not set → Proceed
├─ Set flag in Redis (TTL 5 min)
├─ Create refresh job
└─ Return 503

Server 3: Also tries account_a download (different request)
├─ Cookies also expired
├─ Check Redis: cookie:refresh:account_a:in_progress
│  └─ Already set → Skip
└─ Return 503 (without creating duplicate job)
```

## API Endpoints

### Health Check

```bash
GET /api/health
```

**Response (Healthy):**
```json
{
  "status": "healthy",
  "cookies_available": true,
  "refresh_in_progress": false,
  "account_id": "account_a",
  "can_process_downloads": true
}
```

**Response (Degraded):**
```json
{
  "status": "degraded",
  "cookies_available": false,
  "refresh_in_progress": true,
  "account_id": "account_a",
  "can_process_downloads": false
}
```

### Cookies Health

```bash
GET /api/health/cookies
```

**Response:**
```json
{
  "configured": true,
  "exists": true,
  "account_id": "account_a",
  "refresh_in_progress": false,
  "file_info": {
    "size_bytes": 1234,
    "last_modified": 1708473600.0,
    "path": "/opt/ytdl/youtube_cookies_account_a.txt"
  },
  "message": "Cookies available"
}
```

## Monitoring

### Redis Keys to Monitor

```bash
# Refresh status per account
GET cookie:refresh:account_a:in_progress
GET cookie:refresh:account_b:in_progress
GET cookie:refresh:account_c:in_progress

# Queue length
LLEN bull:cookie-refresh:wait
LLEN bull:cookie-refresh:active
LLEN bull:cookie-refresh:failed
```

### Prometheus Metrics

The backend exposes metrics at `/metrics`:

```
# Cookies availability per server
cookies_available{account_id="account_a"} 1
cookies_available{account_id="account_b"} 1
cookies_available{account_id="account_c"} 0

# Refresh jobs triggered
cookie_refresh_triggered_total{account_id="account_a",reason="bot_detection"} 5
cookie_refresh_triggered_total{account_id="account_b",reason="missing_cookies"} 2
```

### Grafana Dashboard

Create alerts for:
- `cookies_available == 0` for > 5 minutes
- `cookie_refresh_failed` count > 3 in 1 hour
- All servers degraded simultaneously

## Testing

### 1. Test Individual Server

```bash
# Check health
curl http://server1.example.com:3001/api/health

# Try download
curl -X POST http://server1.example.com:3001/api/download/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/shorts/..."}'
```

### 2. Test Failover

```bash
# Delete cookies on Server 1
ssh server1 "rm /opt/ytdl/youtube_cookies_account_a.txt"

# Try download through load balancer
curl -X POST http://ytd.example.com/api/download/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/shorts/..."}'

# Should succeed (failover to Server 2 or 3)
# Check logs to verify failover occurred
```

### 3. Test Cookie Refresh

```bash
# Trigger refresh manually
curl -X POST http://server1.example.com:3001/api/cookies/trigger-refresh \
  -H "Content-Type: application/json" \
  -d '{"reason": "test"}'

# Check queue
curl http://server1.example.com:3001/api/cookies/queue-status

# Watch worker logs (Windows)
# Should see: "Processing refresh for account_a"
```

## Scaling

### Adding a New Server (Server 4)

1. **Create new YouTube account** (user4@gmail.com)

2. **Deploy backend** on Server 4 with:
```bash
YT_ACCOUNT_ID=account_d
YT_DLP_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_d.txt
```

3. **Update cookie extractor** config:
```javascript
'account_d': {
    email: 'user4@gmail.com',
    server: 'server4.example.com',
    cookiePath: '/opt/ytdl/youtube_cookies_account_d.txt'
}
```

4. **Update load balancer**:
```nginx
upstream ytd_backend {
    server server1.example.com:3001 max_fails=1 fail_timeout=10s;
    server server2.example.com:3001 max_fails=1 fail_timeout=10s;
    server server3.example.com:3001 max_fails=1 fail_timeout=10s;
    server server4.example.com:3001 max_fails=1 fail_timeout=10s; # New
}
```

5. **Reload load balancer**:
```bash
sudo nginx -s reload
```

## Troubleshooting

### All Servers Showing Degraded

**Problem:** All servers report `cookies_available: false`

**Solution:**
```bash
# Check if cookie files exist on each server
ssh server1 "ls -lh /opt/ytdl/youtube_cookies_account_a.txt"
ssh server2 "ls -lh /opt/ytdl/youtube_cookies_account_b.txt"
ssh server3 "ls -lh /opt/ytdl/youtube_cookies_account_c.txt"

# Check if refresh jobs are stuck
curl http://server1:3001/api/cookies/queue-status

# Check Redis
redis-cli KEYS "cookie:refresh:*"

# Manually trigger refresh for all accounts
curl -X POST http://server1:3001/api/cookies/trigger-refresh -H "Content-Type: application/json" -d '{"reason":"manual"}'
curl -X POST http://server2:3001/api/cookies/trigger-refresh -H "Content-Type: application/json" -d '{"reason":"manual"}'
curl -X POST http://server3:3001/api/cookies/trigger-refresh -H "Content-Type: application/json" -d '{"reason":"manual"}'
```

### Requests Not Failing Over

**Problem:** Downloads fail instead of retrying on another server

**Solution:**
```nginx
# Ensure nginx has retry configuration
proxy_next_upstream error timeout http_503;
proxy_next_upstream_tries 3;
```

### Duplicate Refresh Jobs

**Problem:** Multiple refresh jobs created for the same account

**Solution:**
```bash
# Check Redis TTL
redis-cli TTL cookie:refresh:account_a:in_progress

# Should show ~300 seconds after trigger
# If -2 (doesn't exist), flag expired too early
# Increase TTL in cookie_refresh_service.py
```

## Best Practices

1. **Stagger Cookie Refresh** - Don't refresh all accounts at once
2. **Monitor Cookie Age** - Alert if cookies haven't been refreshed in 7+ days
3. **Use Different Gmail Accounts** - Don't use same account across servers
4. **Keep Logs** - Track which account triggered which download
5. **Backup Cookie Files** - Store encrypted backups of working cookies
6. **Rate Limit Per Account** - YouTube may flag accounts with excessive usage

## Security

1. **Encrypt Cookie Files**:
```bash
# Use restricted permissions
chmod 600 /opt/ytdl/youtube_cookies_*.txt
```

2. **Secure Redis**:
```bash
# Enable authentication
REDIS_URL=redis://:password@redis.example.com:6379
```

3. **Network Isolation**:
- Backend servers in private subnet
- Only load balancer exposed to internet
- Redis/MongoDB only accessible from backend subnet

4. **Rotate Accounts**:
- Change YouTube account passwords monthly
- Refresh cookies after password change
