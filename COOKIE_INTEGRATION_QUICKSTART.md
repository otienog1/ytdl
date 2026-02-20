# Cookie Refresh Integration - Quick Start

## 🎯 What This Does

When YouTube blocks downloads with "Sign in to confirm you're not a bot", the backend automatically triggers your Windows machine to:
1. Extract fresh cookies from Chrome
2. Upload them to the server
3. Restart the backend services
4. Resume downloads

## 🚀 Quick Setup

### Step 1: Start Cookie Worker (Windows Machine)

```bash
cd C:\Users\7plus8\build\ytd\cookie-extractor
npm run worker
```

**Keep this running!** It listens for cookie refresh requests from the server.

### Step 2: Verify Integration (On Server)

```bash
# Check cookies status
curl http://localhost:3001/api/cookies/cookies-status

# Check queue status
curl http://localhost:3001/api/cookies/queue-status
```

### Step 3: Test It Works

```bash
# Manually trigger a refresh
curl -X POST http://localhost:3001/api/cookies/trigger-refresh \
  -H "Content-Type: application/json" \
  -d '{"reason": "test"}'

# Watch the logs
# Windows: Check your worker console
# Server: sudo journalctl -u ytd-backend -f | grep -i cookie
```

## 📊 Monitor It

### Check Cookie File
```bash
# On server
ls -lh /opt/ytdl/youtube_cookies.txt
stat /opt/ytdl/youtube_cookies.txt
```

### Check Queue
```bash
curl http://localhost:3001/api/cookies/queue-status
```

### Watch Logs
```bash
# Backend (server)
sudo journalctl -u ytd-backend -f | grep "Cookie refresh"

# Worker (Windows)
# Just watch your console where you ran "npm run worker"
```

## 🔄 How It Works Automatically

1. **User downloads video** → Backend tries
2. **YouTube blocks** → "Sign in to confirm..."
3. **Backend detects error** → Triggers cookie refresh job
4. **Redis queue** → Sends job to Windows machine
5. **Windows worker** → Extracts cookies, uploads, restarts services
6. **Next download** → Uses fresh cookies, succeeds! ✓

## 🛠️ Troubleshooting

### "Cookie refresh not working"
```bash
# Is Redis running?
redis-cli ping  # Should return PONG

# Is worker running on Windows?
# Check your console

# Check queue
curl http://localhost:3001/api/cookies/queue-status
```

### "Jobs created but not processed"
```bash
# Windows: Is worker running?
# Check the console where you ran npm run worker

# Check for errors in worker logs
```

### "Cookies uploaded but still getting errors"
```bash
# Check file exists
ls -la /opt/ytdl/youtube_cookies.txt

# Check services restarted
sudo systemctl status ytd-backend

# Check cookie file isn't empty
wc -l /opt/ytdl/youtube_cookies.txt
```

## 📝 Environment Variables

Make sure these are set in your `.env`:

```bash
# Required
REDIS_URL=redis://localhost:6379

# Optional (but recommended)
YT_DLP_COOKIES_FILE=/opt/ytdl/youtube_cookies.txt
```

## 🔐 Production Tips

### Run Worker as Windows Service

**Using NSSM:**
```powershell
# Install NSSM
choco install nssm

# Create service
nssm install CookieWorker "C:\Program Files\nodejs\node.exe"
nssm set CookieWorker AppDirectory "C:\Users\7plus8\build\ytd\cookie-extractor"
nssm set CookieWorker AppParameters "redis-worker.js"
nssm start CookieWorker
```

### Monitor Queue Health
```bash
# Add to cron (every 5 minutes)
*/5 * * * * curl -s http://localhost:3001/api/cookies/queue-status | \
  jq '.status.failed' | \
  awk '$1 > 5 { print "Cookie queue has failures!" }'
```

### Set Up Alerts
```bash
# Email alert if cookies missing
if [ ! -f /opt/ytdl/youtube_cookies.txt ]; then
  echo "Cookies file missing!" | mail -s "Alert" admin@example.com
fi
```

## 🎓 API Endpoints

### Trigger Refresh
```bash
POST /api/cookies/trigger-refresh
{
  "reason": "manual_trigger"
}
```

### Check Queue
```bash
GET /api/cookies/queue-status
```

### Check Cookies File
```bash
GET /api/cookies/cookies-status
```

## ✅ Success Indicators

You'll know it's working when you see:

**In backend logs:**
```
🔄 Cookie refresh needed for video abc123
✅ Cookie refresh job created (ID: 42, reason: bot_detection)
```

**In worker console:**
```
Processing job 42...
Extracted 2 cookies from browser
Uploading to 172.234.172.191
Restarting services
✓ Job completed successfully
```

**In download flow:**
```
First attempt: ❌ "Sign in to confirm you're not a bot"
Cookies refreshed: 🔄 Automatic trigger
Second attempt: ✅ Download successful!
```

That's it! Your system will now automatically handle cookie expiration. 🎉
