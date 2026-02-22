# Cookie Extractor Setup for Multi-Server Architecture

## Overview

Each server runs its own cookie extractor for its unique YouTube account:
- **Server 1 (ytd.timobosafaris.com):** Account A
- **Server 2 (GCP - 34.57.68.120):** Account B
- **Server 3 (AWS - 13.60.71.187):** Account C

All cookie extractors connect to the **same shared Redis** server to receive cookie refresh jobs.

---

## Architecture

```
Backend Server 1 (Account A)
    ↓ (triggers refresh job)
Redis (57.159.27.119:6379) ← Shared Bull Queue
    ↓ (receives job)
Cookie Extractor 1 (Account A)
    ↓ (generates cookies)
/opt/ytdl/youtube_cookies_account_a.txt

Backend Server 2 (Account B)
    ↓ (triggers refresh job)
Redis (57.159.27.119:6379) ← Shared Bull Queue
    ↓ (receives job)
Cookie Extractor 2 (Account B)
    ↓ (generates cookies)
/opt/ytdl/youtube_cookies_account_b.txt

Backend Server 3 (Account C)
    ↓ (triggers refresh job)
Redis (57.159.27.119:6379) ← Shared Bull Queue
    ↓ (receives job)
Cookie Extractor 3 (Account C)
    ↓ (generates cookies)
/opt/ytdl/youtube_cookies_account_c.txt
```

---

## Prerequisites

Each server needs:
1. ✅ Node.js 14+ installed
2. ✅ Chromium browser installed
3. ✅ Cookie extractor code deployed
4. ✅ Access to shared Redis server

---

## Server 1: ytd.timobosafaris.com (Account A)

### Step 1: Navigate to Cookie Extractor Directory

```bash
ssh admin@ytd.timobosafaris.com
cd /opt/ytdl/cookie-extractor
```

### Step 2: Configure Environment Variables

```bash
nano .env
```

**Paste this configuration:**

```bash
# ============================================
# Cookie Extractor Configuration - Account A
# ============================================

# Redis Configuration (Shared across all servers)
REDIS_HOST=57.159.27.119
REDIS_PORT=6379
REDIS_PASSWORD=tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM
REDIS_DB=0

# Account Configuration (UNIQUE PER SERVER)
ACCOUNT_ID=account_a
COOKIES_OUTPUT_PATH=/opt/ytdl/youtube_cookies_account_a.txt

# YouTube Account Credentials (UNIQUE PER SERVER)
# Replace with actual credentials for Account A
YT_EMAIL=your_account_a@gmail.com
YT_PASSWORD=password_for_account_a

# Browser Configuration
HEADLESS=true
CHROME_PATH=/usr/bin/chromium
CHROME_USER_DATA_DIR=/tmp/chrome-profile-account-a

# Cookie Extractor Settings
MAX_RETRIES=3
RETRY_DELAY=2000
COOKIE_EXPIRY_DAYS=30

# Logging
LOG_LEVEL=info

# Queue Settings
WORKER_CONCURRENCY=1
QUEUE_NAME=cookie-refresh
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

### Step 3: Install Dependencies

```bash
npm install
# or if using yarn
yarn install
```

### Step 4: Test Cookie Extractor

```bash
# Test single cookie extraction
npm run extract

# Or test with specific account
node extract-cookies.js --account account_a
```

### Step 5: Start Redis Worker

```bash
# Start worker in foreground (for testing)
npm run worker

# Or start in background with PM2 (recommended for production)
npm install -g pm2
pm2 start redis-worker.js --name cookie-worker-a
pm2 save
pm2 startup
```

### Step 6: Create Systemd Service (Production)

```bash
sudo nano /etc/systemd/system/cookie-extractor-a.service
```

**Paste this:**

```ini
[Unit]
Description=Cookie Extractor Worker - Account A
After=network.target redis.service

[Service]
Type=simple
User=admin
WorkingDirectory=/opt/ytdl/cookie-extractor
Environment="NODE_ENV=production"
ExecStart=/usr/bin/node redis-worker.js
Restart=always
RestartSec=10
StandardOutput=append:/var/log/cookie-extractor-a.log
StandardError=append:/var/log/cookie-extractor-a-error.log

# Resource limits
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable cookie-extractor-a
sudo systemctl start cookie-extractor-a
sudo systemctl status cookie-extractor-a
```

---

## Server 2: GCP (34.57.68.120) - Account B

### Step 1: SSH and Navigate

```bash
ssh admin@34.57.68.120
cd /opt/ytdl/cookie-extractor
```

### Step 2: Configure Environment Variables

```bash
nano .env
```

**Paste this configuration:**

```bash
# ============================================
# Cookie Extractor Configuration - Account B
# ============================================

# Redis Configuration (SAME as Account A)
REDIS_HOST=57.159.27.119
REDIS_PORT=6379
REDIS_PASSWORD=tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM
REDIS_DB=0

# Account Configuration (DIFFERENT from Account A)
ACCOUNT_ID=account_b
COOKIES_OUTPUT_PATH=/opt/ytdl/youtube_cookies_account_b.txt

# YouTube Account Credentials (DIFFERENT from Account A)
# Replace with actual credentials for Account B
YT_EMAIL=your_account_b@gmail.com
YT_PASSWORD=password_for_account_b

# Browser Configuration (SAME)
HEADLESS=true
CHROME_PATH=/usr/bin/chromium
CHROME_USER_DATA_DIR=/tmp/chrome-profile-account-b

# Cookie Extractor Settings (SAME)
MAX_RETRIES=3
RETRY_DELAY=2000
COOKIE_EXPIRY_DAYS=30

# Logging
LOG_LEVEL=info

# Queue Settings (SAME)
WORKER_CONCURRENCY=1
QUEUE_NAME=cookie-refresh
```

### Step 3-6: Same as Server 1

Follow the same installation, testing, and systemd setup steps as Server 1, but use:
- Service name: `cookie-extractor-b.service`
- PM2 name: `cookie-worker-b`
- Log files: `/var/log/cookie-extractor-b.log`

---

## Server 3: AWS (13.60.71.187) - Account C

### Step 1: SSH and Navigate

```bash
ssh admin@13.60.71.187
cd /opt/ytdl/cookie-extractor
```

### Step 2: Configure Environment Variables

```bash
nano .env
```

**Paste this configuration:**

```bash
# ============================================
# Cookie Extractor Configuration - Account C
# ============================================

# Redis Configuration (SAME as others)
REDIS_HOST=57.159.27.119
REDIS_PORT=6379
REDIS_PASSWORD=tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM
REDIS_DB=0

# Account Configuration (DIFFERENT)
ACCOUNT_ID=account_c
COOKIES_OUTPUT_PATH=/opt/ytdl/youtube_cookies_account_c.txt

# YouTube Account Credentials (DIFFERENT)
# Replace with actual credentials for Account C
YT_EMAIL=your_account_c@gmail.com
YT_PASSWORD=password_for_account_c

# Browser Configuration (SAME)
HEADLESS=true
CHROME_PATH=/usr/bin/chromium
CHROME_USER_DATA_DIR=/tmp/chrome-profile-account-c

# Cookie Extractor Settings (SAME)
MAX_RETRIES=3
RETRY_DELAY=2000
COOKIE_EXPIRY_DAYS=30

# Logging
LOG_LEVEL=info

# Queue Settings (SAME)
WORKER_CONCURRENCY=1
QUEUE_NAME=cookie-refresh
```

### Step 3-6: Same as Server 1

Follow the same installation, testing, and systemd setup steps, but use:
- Service name: `cookie-extractor-c.service`
- PM2 name: `cookie-worker-c`
- Log files: `/var/log/cookie-extractor-c.log`

---

## Configuration Summary

### What's SHARED Across All Servers

```bash
# Same on all servers
REDIS_HOST=57.159.27.119
REDIS_PORT=6379
REDIS_PASSWORD=tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM
REDIS_DB=0
QUEUE_NAME=cookie-refresh
HEADLESS=true
CHROME_PATH=/usr/bin/chromium
MAX_RETRIES=3
WORKER_CONCURRENCY=1
```

### What's DIFFERENT Per Server

| Setting | Server 1 (Account A) | Server 2 (Account B) | Server 3 (Account C) |
|---------|---------------------|---------------------|---------------------|
| `ACCOUNT_ID` | `account_a` | `account_b` | `account_c` |
| `COOKIES_OUTPUT_PATH` | `/opt/ytdl/youtube_cookies_account_a.txt` | `/opt/ytdl/youtube_cookies_account_b.txt` | `/opt/ytdl/youtube_cookies_account_c.txt` |
| `YT_EMAIL` | `your_account_a@gmail.com` | `your_account_b@gmail.com` | `your_account_c@gmail.com` |
| `YT_PASSWORD` | `password_for_account_a` | `password_for_account_b` | `password_for_account_c` |
| `CHROME_USER_DATA_DIR` | `/tmp/chrome-profile-account-a` | `/tmp/chrome-profile-account-b` | `/tmp/chrome-profile-account-c` |

---

## Testing the Setup

### Test Cookie Extraction Manually

```bash
# On each server
cd /opt/ytdl/cookie-extractor
npm run extract
```

**Expected output:**
```
✓ Cookies extracted successfully
✓ Saved to: /opt/ytdl/youtube_cookies_account_a.txt
✓ Cookie count: 25
```

### Test Redis Worker

```bash
# On each server
cd /opt/ytdl/cookie-extractor
npm run worker

# Should output:
# [YYYY-MM-DD HH:MM:SS] Worker started for account: account_a
# [YYYY-MM-DD HH:MM:SS] Listening to queue: cookie-refresh
```

### Trigger Cookie Refresh from Backend

```bash
# From any server, trigger a cookie refresh
curl -X POST http://127.0.0.1:3001/api/cookies/refresh \
  -H "Content-Type: application/json" \
  -d '{"account_id": "account_a", "reason": "manual_test"}'
```

**Expected:**
1. Backend creates job in Redis Bull queue
2. Cookie extractor worker picks up job
3. Chromium launches and extracts cookies
4. Cookies saved to file
5. Backend detects new cookies and resumes operations

### Check Cookie Extractor Logs

```bash
# Systemd logs
sudo journalctl -u cookie-extractor-a -f

# Or file logs
tail -f /var/log/cookie-extractor-a.log

# PM2 logs
pm2 logs cookie-worker-a
```

---

## Monitoring

### Check Cookie Extractor Status

```bash
# Systemd
sudo systemctl status cookie-extractor-a

# PM2
pm2 status cookie-worker-a
```

### Check Redis Queue Status

```bash
redis-cli -h 57.159.27.119 -p 6379 -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM

# In redis-cli:
LLEN "bull:cookie-refresh:wait"      # Waiting jobs
LLEN "bull:cookie-refresh:active"    # Active jobs
LLEN "bull:cookie-refresh:completed" # Completed jobs
LLEN "bull:cookie-refresh:failed"    # Failed jobs
```

### Check Cookie File Age

```bash
# On each server
ls -lh /opt/ytdl/youtube_cookies_*.txt
stat /opt/ytdl/youtube_cookies_account_a.txt | grep Modify
```

---

## Troubleshooting

### Issue 1: Cookie Extractor Won't Start

**Check logs:**
```bash
sudo journalctl -u cookie-extractor-a -n 50
```

**Common causes:**
- Chromium not installed: `sudo apt install chromium-browser`
- Missing dependencies: `cd /opt/ytdl/cookie-extractor && npm install`
- Permission issues: `sudo chown -R admin:admin /opt/ytdl/cookie-extractor`

### Issue 2: Can't Connect to Redis

**Test connection:**
```bash
redis-cli -h 57.159.27.119 -p 6379 -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM PING
# Should return: PONG
```

**Check .env:**
```bash
cat /opt/ytdl/cookie-extractor/.env | grep REDIS
```

### Issue 3: Chromium Crashes

**Run in non-headless mode for debugging:**
```bash
# In .env, change:
HEADLESS=false

# Restart worker
sudo systemctl restart cookie-extractor-a
```

**Install dependencies:**
```bash
# Debian/Ubuntu
sudo apt install chromium-browser chromium-chromedriver

# Install missing libraries
sudo apt install libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2
```

### Issue 4: Cookies Not Generated

**Check YouTube credentials:**
```bash
cat /opt/ytdl/cookie-extractor/.env | grep YT_
```

**Test login manually:**
```bash
cd /opt/ytdl/cookie-extractor
node youtube-login.js
```

### Issue 5: Wrong Account ID in Jobs

**Check backend .env.production:**
```bash
cat /opt/ytdl/.env.production | grep YT_ACCOUNT_ID
```

**Should match cookie extractor ACCOUNT_ID:**
- Backend: `YT_ACCOUNT_ID=account_a`
- Cookie Extractor: `ACCOUNT_ID=account_a`

---

## Security Notes

### Protect Credentials

```bash
# Set proper permissions
chmod 600 /opt/ytdl/cookie-extractor/.env
chmod 600 /opt/ytdl/youtube_cookies_*.txt

# Only owner can read
ls -la /opt/ytdl/cookie-extractor/.env
# Should show: -rw------- 1 admin admin
```

### Use Environment Variables Instead of .env (Optional)

```bash
# In systemd service file
[Service]
Environment="ACCOUNT_ID=account_a"
Environment="YT_EMAIL=your_email@gmail.com"
Environment="YT_PASSWORD=your_password"
EnvironmentFile=/opt/ytdl/cookie-extractor/.env.production
```

### Never Commit .env to Git

Already in `.gitignore`:
```
.env
.env.*
!.env.example
```

---

## Summary Checklist

### Server 1 (ytd.timobosafaris.com - Account A)
- [ ] Cookie extractor code deployed to `/opt/ytdl/cookie-extractor`
- [ ] `.env` configured with `ACCOUNT_ID=account_a`
- [ ] YouTube credentials for Account A set
- [ ] Dependencies installed (`npm install`)
- [ ] Worker running (`systemctl status cookie-extractor-a`)
- [ ] Cookie file exists: `/opt/ytdl/youtube_cookies_account_a.txt`
- [ ] Backend configured with `YT_ACCOUNT_ID=account_a`

### Server 2 (GCP - 34.57.68.120 - Account B)
- [ ] Cookie extractor code deployed
- [ ] `.env` configured with `ACCOUNT_ID=account_b`
- [ ] YouTube credentials for Account B set
- [ ] Dependencies installed
- [ ] Worker running (`systemctl status cookie-extractor-b`)
- [ ] Cookie file exists: `/opt/ytdl/youtube_cookies_account_b.txt`
- [ ] Backend configured with `YT_ACCOUNT_ID=account_b`

### Server 3 (AWS - 13.60.71.187 - Account C)
- [ ] Cookie extractor code deployed
- [ ] `.env` configured with `ACCOUNT_ID=account_c`
- [ ] YouTube credentials for Account C set
- [ ] Dependencies installed
- [ ] Worker running (`systemctl status cookie-extractor-c`)
- [ ] Cookie file exists: `/opt/ytdl/youtube_cookies_account_c.txt`
- [ ] Backend configured with `YT_ACCOUNT_ID=account_c`

**Once all checked ✅, your multi-server cookie extraction is ready!** 🎉
