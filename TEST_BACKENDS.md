# Backend Server Testing Guide

## Test Commands for Each Backend

### Correct Endpoint: `/api/health` (NOT `/health`)

The backend health endpoint is at **`/api/health`**, not `/health`.

---

## Test Each Backend Server

### Server 1 - ytd.timobosafaris.com (Local - Account A)

```bash
# From ytd.timobosafaris.com
curl http://127.0.0.1:3001/api/health

# Expected response:
# {
#   "status": "healthy",
#   "cookies_available": true,
#   "refresh_in_progress": false,
#   "account_id": "account_a",
#   "can_process_downloads": true
# }
```

### Server 2 - GCP (34.57.68.120 - Account B)

```bash
# From any server
curl http://34.57.68.120:3001/api/health

# Expected response:
# {
#   "status": "healthy",
#   "cookies_available": true,
#   "refresh_in_progress": false,
#   "account_id": "account_b",
#   "can_process_downloads": true
# }
```

**If you get 404 Not Found:**
- Backend service is running but endpoint is wrong
- Try: `curl http://34.57.68.120:3001/api/docs` (should show API docs)

**If you get Connection Refused:**
- Backend service is not running
- Check: `ssh admin@34.57.68.120 "sudo systemctl status ytd-api"`

**If you get Timeout:**
- Firewall is blocking port 3001
- Fix: `ssh admin@34.57.68.120 "sudo ufw allow 3001/tcp"`

### Server 3 - AWS (13.60.71.187 - Account C)

```bash
# From any server
curl http://13.60.71.187:3001/api/health

# Expected response:
# {
#   "status": "healthy",
#   "cookies_available": true,
#   "refresh_in_progress": false,
#   "account_id": "account_c",
#   "can_process_downloads": true
# }
```

---

## Quick Test All Backends Script

```bash
#!/bin/bash
# test-all-backends.sh

echo "Testing all backend servers..."
echo ""

# Server 1 - Local
echo "=== Server 1 - ytd.timobosafaris.com (127.0.0.1) - Account A ==="
curl -s http://127.0.0.1:3001/api/health | jq '.account_id, .cookies_available, .can_process_downloads' || echo "FAILED"
echo ""

# Server 2 - GCP
echo "=== Server 2 - GCP (34.57.68.120) - Account B ==="
curl -s http://34.57.68.120:3001/api/health | jq '.account_id, .cookies_available, .can_process_downloads' || echo "FAILED"
echo ""

# Server 3 - AWS
echo "=== Server 3 - AWS (13.60.71.187) - Account C ==="
curl -s http://13.60.71.187:3001/api/health | jq '.account_id, .cookies_available, .can_process_downloads' || echo "FAILED"
echo ""

echo "Done!"
```

**Run it:**
```bash
chmod +x test-all-backends.sh
./test-all-backends.sh
```

---

## Check Backend Services are Running

### On Each Server

```bash
# Check if ytd-api is running
sudo systemctl status ytd-api

# Check if listening on port 3001
sudo netstat -tlnp | grep 3001
# Should show: 127.0.0.1:3001 or 0.0.0.0:3001

# Test locally on the server
curl http://127.0.0.1:3001/api/health
```

---

## If Backend is Not Running

### Start the Backend

```bash
# Navigate to backend directory
cd /opt/ytdl/backend-python

# Run deployment script
sudo bash start-dev.sh

# Or just restart services
sudo systemctl restart ytd-api ytd-worker ytd-beat

# Check status
sudo systemctl status ytd-api ytd-worker ytd-beat
```

### Check Logs if Failed

```bash
# API server logs
sudo journalctl -u ytd-api -n 50

# Worker logs
sudo journalctl -u ytd-worker -n 50

# Beat logs
sudo journalctl -u ytd-beat -n 50
```

---

## Configure Account ID on Each Server

Each backend server needs a unique account ID in `.env.production`:

### Server 1 (ytd.timobosafaris.com)

```bash
# Edit .env.production
sudo nano /opt/ytdl/.env.production

# Set these values:
YT_ACCOUNT_ID=account_a
YT_DLP_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_a.txt

# Restart services
sudo systemctl restart ytd-api ytd-worker ytd-beat
```

### Server 2 (GCP - 34.57.68.120)

```bash
# SSH to GCP server
ssh admin@34.57.68.120

# Edit .env.production
sudo nano /opt/ytdl/.env.production

# Set these values:
YT_ACCOUNT_ID=account_b
YT_DLP_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_b.txt

# Restart services
sudo systemctl restart ytd-api ytd-worker ytd-beat

# Test locally
curl http://127.0.0.1:3001/api/health
```

### Server 3 (AWS - 13.60.71.187)

```bash
# SSH to AWS server
ssh admin@13.60.71.187

# Edit .env.production
sudo nano /opt/ytdl/.env.production

# Set these values:
YT_ACCOUNT_ID=account_c
YT_DLP_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_c.txt

# Restart services
sudo systemctl restart ytd-api ytd-worker ytd-beat

# Test locally
curl http://127.0.0.1:3001/api/health
```

---

## Open Firewall on Remote Servers

### On GCP Server (34.57.68.120)

```bash
# Allow port 3001 from load balancer
sudo ufw allow from 172.234.172.191 to any port 3001

# Or allow from anywhere (less secure)
sudo ufw allow 3001/tcp

# Reload firewall
sudo ufw reload

# Check firewall status
sudo ufw status
```

### On AWS Server (13.60.71.187)

```bash
# Allow port 3001 from load balancer
sudo ufw allow from 172.234.172.191 to any port 3001

# Or allow from anywhere (less secure)
sudo ufw allow 3001/tcp

# Reload firewall
sudo ufw reload

# Check firewall status
sudo ufw status
```

---

## Verify Network Connectivity

### From ytd.timobosafaris.com to Other Servers

```bash
# Test network connectivity to GCP
ping -c 3 34.57.68.120

# Test port 3001 is reachable
nc -zv 34.57.68.120 3001
# Should say: Connection to 34.57.68.120 3001 port [tcp/*] succeeded!

# Test network connectivity to AWS
ping -c 3 13.60.71.187

# Test port 3001 is reachable
nc -zv 13.60.71.187 3001
# Should say: Connection to 13.60.71.187 3001 port [tcp/*] succeeded!
```

---

## Common Issues & Fixes

### Issue 1: 404 Not Found

**Symptom:** `HTTP/1.1 404 Not Found`

**Cause:** Using wrong endpoint (`/health` instead of `/api/health`)

**Fix:** Use `/api/health`:
```bash
curl http://34.57.68.120:3001/api/health  # ✅ Correct
curl http://34.57.68.120:3001/health      # ❌ Wrong
```

### Issue 2: Connection Refused

**Symptom:** `curl: (7) Failed to connect to 34.57.68.120 port 3001: Connection refused`

**Cause:** Backend service not running

**Fix:**
```bash
ssh admin@34.57.68.120
sudo systemctl status ytd-api
sudo systemctl start ytd-api
```

### Issue 3: Connection Timeout

**Symptom:** Request hangs, then times out

**Cause:** Firewall blocking port 3001

**Fix:**
```bash
ssh admin@34.57.68.120
sudo ufw allow 3001/tcp
sudo ufw reload
```

### Issue 4: Wrong Account ID in Response

**Symptom:** Response shows `account_id: "default"` instead of `account_a`, `account_b`, `account_c`

**Cause:** `.env.production` not configured with `YT_ACCOUNT_ID`

**Fix:**
```bash
ssh admin@34.57.68.120
sudo nano /opt/ytdl/.env.production
# Add: YT_ACCOUNT_ID=account_b
sudo systemctl restart ytd-api
```

### Issue 5: Cookies Not Available

**Symptom:** Response shows `cookies_available: false`

**Cause:** Cookie file doesn't exist

**Fix:**
```bash
ssh admin@34.57.68.120
ls -la /opt/ytdl/youtube_cookies_account_b.txt

# If missing, create or run cookie extractor
cd /opt/ytdl/cookie-extractor
npm run worker
```

---

## Test Load Balancer After Backend Setup

Once all backends are confirmed working, test through the load balancer:

### Test 1: Health Endpoint

```bash
# Through load balancer (should work after nginx update)
curl https://ytd.timobosafaris.com/health

# Direct to backend
curl https://ytd.timobosafaris.com/api/health
```

### Test 2: Load Distribution

```bash
# Make 30 requests and see distribution
for i in {1..30}; do
  curl -s https://ytd.timobosafaris.com/api/health | jq -r '.account_id'
done | sort | uniq -c

# Expected output:
#   10 account_a
#   10 account_b
#   10 account_c
```

---

## Summary Checklist

Before enabling load balancing, ensure:

### Server 1 (ytd.timobosafaris.com - 172.234.172.191)
- [ ] Backend running: `sudo systemctl status ytd-api`
- [ ] Responds to health check: `curl http://127.0.0.1:3001/api/health`
- [ ] Has account ID: `account_a`
- [ ] Has cookies: `/opt/ytdl/youtube_cookies_account_a.txt`

### Server 2 (GCP - 34.57.68.120)
- [ ] Backend running: `ssh admin@34.57.68.120 "sudo systemctl status ytd-api"`
- [ ] Firewall open: `nc -zv 34.57.68.120 3001`
- [ ] Responds to health check: `curl http://34.57.68.120:3001/api/health`
- [ ] Has account ID: `account_b`
- [ ] Has cookies: `/opt/ytdl/youtube_cookies_account_b.txt`

### Server 3 (AWS - 13.60.71.187)
- [ ] Backend running: `ssh admin@13.60.71.187 "sudo systemctl status ytd-api"`
- [ ] Firewall open: `nc -zv 13.60.71.187 3001`
- [ ] Responds to health check: `curl http://13.60.71.187:3001/api/health`
- [ ] Has account ID: `account_c`
- [ ] Has cookies: `/opt/ytdl/youtube_cookies_account_c.txt`

**Once all checks pass ✅, update nginx configuration to enable load balancing!**
