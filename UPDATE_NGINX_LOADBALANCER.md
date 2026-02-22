# Update Nginx to Load Balancer Configuration

## Current Setup

Your current nginx configuration on `ytd.timobosafaris.com`:
- ✅ SSL enabled (Let's Encrypt)
- ✅ WebSocket support at `/ws/`
- ✅ Proxies to local backend only (`127.0.0.1:3001`)
- ❌ No load balancing (single server)

## New Setup (Load Balanced)

After this update:
- ✅ SSL preserved (same certificates)
- ✅ WebSocket support preserved
- ✅ Load balances between 3 servers
- ✅ Automatic failover on cookie expiry (HTTP 503)
- ✅ Least connections load balancing

---

## Step-by-Step Update

### Step 1: Backup Current Configuration

```bash
# SSH into ytd.timobosafaris.com
ssh admin@ytd.timobosafaris.com

# Backup current config
sudo cp /etc/nginx/sites-available/ytd /etc/nginx/sites-available/ytd.backup.$(date +%Y%m%d)

# Verify backup
ls -la /etc/nginx/sites-available/ytd.backup.*
```

### Step 2: Update Configuration File

```bash
# Edit the nginx configuration
sudo nano /etc/nginx/sites-available/ytd
```

**Replace the entire contents** with the configuration from `nginx-ytd-timobosafaris-updated.conf`.

Or upload the new config:
```bash
# From your local machine
scp nginx-ytd-timobosafaris-updated.conf admin@ytd.timobosafaris.com:/tmp/

# On server
sudo mv /tmp/nginx-ytd-timobosafaris-updated.conf /etc/nginx/sites-available/ytd
```

### Step 3: Test Configuration

```bash
# Test nginx config for syntax errors
sudo nginx -t
```

**Expected output:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**If there are errors:**
- Check for typos
- Verify server IPs are correct
- Restore backup: `sudo cp /etc/nginx/sites-available/ytd.backup.YYYYMMDD /etc/nginx/sites-available/ytd`

### Step 4: Reload Nginx

```bash
# Reload nginx with new config (no downtime)
sudo systemctl reload nginx

# Or restart if reload doesn't work
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

### Step 5: Verify Load Balancer is Working

```bash
# Test that nginx is serving requests
curl -I https://ytd.timobosafaris.com/health

# Should return HTTP/1.1 200 OK
```

---

## Testing Load Balancing

### Test 1: Check Each Backend Individually

```bash
# Test local backend (Account A)
curl http://127.0.0.1:3001/api/health

# Test GCP backend (Account B)
curl http://34.57.68.120:3001/api/health

# Test AWS backend (Account C)
curl http://13.60.71.187:3001/api/health
```

**Expected response from each:**
```json
{
  "status": "healthy",
  "cookies_available": true,
  "refresh_in_progress": false,
  "account_id": "account_a",  // or account_b, account_c
  "can_process_downloads": true
}
```

**If any backend returns an error:**
- Check that the backend service is running: `sudo systemctl status ytd-api`
- Check firewall allows port 3001: `sudo ufw status`
- Check from load balancer server: `curl http://BACKEND_IP:3001/api/health`

### Test 2: Load Distribution Through Load Balancer

```bash
# Make 30 requests and count which account responds
for i in {1..30}; do
  curl -s https://ytd.timobosafaris.com/health | grep -o 'account_[a-c]'
done | sort | uniq -c
```

**Expected output (with least_conn):**
```
  10 account_a
  10 account_b
  10 account_c
```

Roughly equal distribution across all 3 servers.

### Test 3: WebSocket Connection

```bash
# Install wscat if not already installed
npm install -g wscat

# Test WebSocket through load balancer
wscat -c wss://ytd.timobosafaris.com/ws/test-job-id
```

Should connect successfully and show "Connected" message.

### Test 4: Automatic Failover

```bash
# Simulate cookie unavailability on local server
sudo mv /opt/ytdl/youtube_cookies_account_a.txt /opt/ytdl/youtube_cookies_account_a.txt.bak
sudo systemctl restart ytd-api

# Wait a few seconds
sleep 5

# Make download request
curl -X POST https://ytd.timobosafaris.com/api/download/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/shorts/xxxxx"}'

# Should succeed via GCP or AWS server!

# Check logs to verify failover
sudo tail -20 /var/log/nginx/ytd-lb-access.log

# Restore cookies
sudo mv /opt/ytdl/youtube_cookies_account_a.txt.bak /opt/ytdl/youtube_cookies_account_a.txt
sudo systemctl restart ytd-api
```

---

## What Changed

### Before (Single Server)

```nginx
location / {
    proxy_pass http://127.0.0.1:3001;
    # ... proxy settings
}
```

**Behavior:**
- All requests go to local backend only
- If local backend fails → entire service fails
- No automatic failover

### After (Load Balanced)

```nginx
upstream ytd_backend {
    least_conn;
    server 127.0.0.1:3001 max_fails=3 fail_timeout=30s;
    server 34.57.68.120:3001 max_fails=3 fail_timeout=30s;
    server 13.60.71.187:3001 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

location / {
    proxy_pass http://ytd_backend;
    proxy_next_upstream error timeout http_503;
    proxy_next_upstream_tries 3;
}
```

**Behavior:**
- Requests distributed across all 3 servers (least connections)
- If one server returns 503 (cookies unavailable) → automatic retry on another server
- If one server is down → traffic goes to remaining servers
- No single point of failure

---

## Key Features Added

### 1. Upstream Load Balancing

```nginx
upstream ytd_backend {
    least_conn;  # Send to server with fewest active connections
    server 127.0.0.1:3001 max_fails=3 fail_timeout=30s;
    server 34.57.68.120:3001 max_fails=3 fail_timeout=30s;
    server 13.60.71.187:3001 max_fails=3 fail_timeout=30s;
}
```

### 2. Automatic Failover

```nginx
location /api/ {
    proxy_pass http://ytd_backend;

    # Retry on next server if:
    # - Connection error
    # - Timeout
    # - HTTP 503 (cookies unavailable)
    proxy_next_upstream error timeout http_503;
    proxy_next_upstream_tries 3;
    proxy_next_upstream_timeout 10s;
}
```

### 3. WebSocket Load Balancing

```nginx
location /ws/ {
    proxy_pass http://ytd_backend;

    # WebSocket upgrade headers
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # Retry on errors
    proxy_next_upstream error timeout http_503;
    proxy_next_upstream_tries 3;
}
```

### 4. Monitoring Endpoint

```nginx
server {
    listen 8080;

    location /nginx_status {
        stub_status on;  # Shows nginx stats
    }
}
```

Access at: `http://ytd.timobosafaris.com:8080/nginx_status` (from allowed IPs)

---

## Monitoring

### Check Nginx Access Logs

```bash
# Real-time log viewing
sudo tail -f /var/log/nginx/ytd-lb-access.log

# See which backends are being used
sudo grep "upstream" /var/log/nginx/ytd-lb-access.log | tail -20
```

### Check Nginx Error Logs

```bash
# Check for upstream errors
sudo tail -f /var/log/nginx/ytd-lb-error.log

# Search for specific errors
sudo grep "upstream" /var/log/nginx/ytd-lb-error.log
sudo grep "503" /var/log/nginx/ytd-lb-error.log
```

### Monitor Nginx Status

```bash
# From allowed IP (localhost)
curl http://localhost:8080/nginx_status
```

**Output:**
```
Active connections: 12
server accepts handled requests
 1234 1234 5678
Reading: 0 Writing: 2 Waiting: 10
```

### Check Backend Health

```bash
# Quick script to check all backends
for ip in 127.0.0.1 34.57.68.120 13.60.71.187; do
  echo "=== Backend $ip ==="
  curl -s http://$ip:3001/api/health | jq '.account_id, .cookies_available'
  echo ""
done
```

---

## Troubleshooting

### Issue 1: Nginx fails to reload

**Error:** `nginx: [emerg] could not build upstream`

**Cause:** Syntax error in upstream block

**Fix:**
```bash
# Check syntax
sudo nginx -t

# Look for typo in server IP addresses
sudo nano /etc/nginx/sites-available/ytd
```

### Issue 2: Can't reach GCP/AWS backends

**Error in logs:** `connect() failed (113: No route to host)`

**Cause:** Firewall blocking connections

**Fix on backend servers:**
```bash
# On 34.57.68.120 and 13.60.71.187
sudo ufw allow from 172.234.172.191 to any port 3001

# Or allow from all
sudo ufw allow 3001/tcp
sudo ufw reload
```

### Issue 3: All requests go to one server

**Cause:** Other servers marked as down

**Check upstream status:**
```bash
# No built-in command, check error logs
sudo grep "upstream" /var/log/nginx/ytd-lb-error.log
```

**Fix:** Ensure all backends are healthy:
```bash
curl http://127.0.0.1:3001/api/health
curl http://34.57.68.120:3001/api/health
curl http://13.60.71.187:3001/api/health
```

### Issue 4: WebSocket connections drop

**Cause:** Timeout too short or backend server down

**Fix:** Already configured with long timeout (86400s = 24 hours)

**Verify WebSocket route:**
```bash
# Check if WebSocket location exists
sudo grep -A5 "location /ws/" /etc/nginx/sites-available/ytd
```

### Issue 5: SSL certificate warnings

**Cause:** Certificate paths wrong after update

**Fix:** Verify certificate paths:
```bash
sudo ls -la /etc/letsencrypt/live/ytd.timobosafaris.com/
```

Should show:
- fullchain.pem
- privkey.pem

If missing, regenerate:
```bash
sudo certbot --nginx -d ytd.timobosafaris.com
```

---

## Rollback Procedure

If anything goes wrong, quickly rollback:

```bash
# Restore backup
sudo cp /etc/nginx/sites-available/ytd.backup.YYYYMMDD /etc/nginx/sites-available/ytd

# Test
sudo nginx -t

# Reload
sudo systemctl reload nginx

# Verify
curl -I https://ytd.timobosafaris.com/health
```

---

## Summary

### Before Update
- ✅ Single server (127.0.0.1:3001)
- ❌ No load balancing
- ❌ No automatic failover
- ✅ SSL enabled
- ✅ WebSocket support

### After Update
- ✅ Three servers (load balanced)
- ✅ Automatic failover on cookie expiry
- ✅ Least connections distribution
- ✅ SSL preserved
- ✅ WebSocket preserved
- ✅ Monitoring endpoint added

### Performance Impact
- **Zero downtime** during update (using `nginx -s reload`)
- **Better reliability** (3 servers vs 1)
- **Better performance** (load distributed)
- **Automatic recovery** from cookie expiry

---

## Next Steps After Update

1. **Monitor for 1 hour** - Watch logs and check distribution
2. **Test download requests** - Ensure everything works
3. **Update other servers** - Deploy backend code to GCP/AWS if not done
4. **Configure monitoring** - Set up alerts for backend failures
5. **Update documentation** - Note which server has which account

---

**Ready to update?** Just run:

```bash
ssh admin@ytd.timobosafaris.com
sudo cp /etc/nginx/sites-available/ytd /etc/nginx/sites-available/ytd.backup.$(date +%Y%m%d)
sudo nano /etc/nginx/sites-available/ytd  # Paste new config
sudo nginx -t
sudo systemctl reload nginx
```

Check the result:
```bash
curl -I https://ytd.timobosafaris.com/health
```

Should return HTTP/1.1 200 OK ✅
