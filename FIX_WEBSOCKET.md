# Fix WebSocket Connection Failures

## 🔴 Problem

WebSocket connections are failing with error:
```
WebSocket connection to 'wss://ytd.timobosafaris.com/ws/download/...' failed
WebSocket closed: 1006
```

## 🔍 Root Causes

1. **Backend services not running**
2. **Nginx config not deployed/reloaded**
3. **Firewall or network issues**

## ✅ Quick Fix (Run on ytd.timobosafaris.com)

```bash
# 1. SSH into server
ssh root@ytd.timobosafaris.com

# 2. Pull latest code (includes fixed nginx config)
cd /opt/ytdl
git pull origin master

# 3. Run diagnostic
bash diagnose-websocket.sh

# 4. Update nginx config with fixed GCP IP
sudo cp nginx-ytd-timobosafaris-updated.conf /etc/nginx/sites-available/ytd

# 5. Test nginx config
sudo nginx -t

# 6. Reload nginx
sudo systemctl reload nginx

# 7. Ensure backend services are running
sudo systemctl status ytd-api ytd-worker ytd-beat

# If not running, start them:
sudo systemctl start ytd-api ytd-worker ytd-beat

# 8. Test WebSocket from server
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test" \
  http://localhost:3001/ws/download/test
```

## 🧪 Verify Fix

### Test 1: Health Check
```bash
curl -I https://ytd.timobosafaris.com/api/health/
# Should return: HTTP/2 200
```

### Test 2: Backend Connectivity
```bash
# Test each backend server
curl -I http://127.0.0.1:3001/api/health/
curl -I http://35.193.12.77:3001/api/health/
curl -I http://13.60.71.187:3001/api/health/
# All should return: HTTP/1.1 200 OK
```

### Test 3: Frontend WebSocket
Open browser console on https://ytd.timobosafaris.com and try a download. Should see:
```
✅ Connecting to WebSocket: wss://ytd.timobosafaris.com/ws/download/...
✅ WebSocket connected
✅ Receiving progress updates
```

## 📋 What Was Fixed

### nginx-ytd-timobosafaris-updated.conf
```nginx
upstream ytd_backend {
    ip_hash;

    server 127.0.0.1:3001 max_fails=2 fail_timeout=30s;
    server 35.193.12.77:3001 max_fails=2 fail_timeout=30s;  # GCP server
    server 13.60.71.187:3001 max_fails=2 fail_timeout=30s;  # AWS server

    keepalive 32;
}
```

## 🔧 Troubleshooting

### Issue: Backend not responding
```bash
# Check backend logs
sudo journalctl -u ytd-api -n 50

# Check if service crashed
sudo systemctl status ytd-api

# Restart if needed
sudo systemctl restart ytd-api
```

### Issue: Nginx errors
```bash
# Check nginx error log
sudo tail -f /var/log/nginx/ytd-lb-error.log

# Test config syntax
sudo nginx -t

# Check if nginx is running
sudo systemctl status nginx
```

### Issue: Port 3001 not listening
```bash
# Check what's listening on port 3001
sudo netstat -tulpn | grep 3001

# Should show: python listening on 0.0.0.0:3001
```

### Issue: Firewall blocking
```bash
# Check firewall rules
sudo ufw status

# Ensure ports are open
sudo ufw allow 3001/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

## 🚀 After Fix

Once fixed, the download flow should work:
1. User enters YouTube URL
2. Frontend extracts cookies from browser
3. Frontend initiates download via `/api/download`
4. Frontend connects WebSocket to `/ws/download/{job_id}`
5. Backend sends real-time progress updates via WebSocket
6. Download completes, video URL returned

## 📞 Still Having Issues?

Run the diagnostic script and share output:
```bash
bash diagnose-websocket.sh > websocket-diagnostic.txt
cat websocket-diagnostic.txt
```

Common issues:
- ❌ Backend `.env.production` missing → Run deployment script
- ❌ Redis not installed → Run `bash install-local-redis.sh`
- ❌ Services failed to start → Check logs with `journalctl`
- ❌ Wrong nginx config → Copy updated config and reload
