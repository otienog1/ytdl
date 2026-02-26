# Quick Reference Card

**Server**: 172.234.172.191 | **Domain**: ytd.timobosafaris.com

---

## 🔑 Access

```bash
ssh root@172.234.172.191
cd /opt/ytdl
```

---

## 📋 Most Common Commands

### 1️⃣ Upload Fresh YouTube Cookies

```bash
# From your local machine
scp youtube_cookies.txt root@172.234.172.191:/opt/ytdl/youtube_cookies.txt

# On the server
ssh root@172.234.172.191
sudo chown ytd:ytd /opt/ytdl/youtube_cookies.txt
sudo chmod 640 /opt/ytdl/youtube_cookies.txt
sudo systemctl restart ytd-worker ytd-api ytd-beat
```

### 2️⃣ Test If Cookies Are Valid

```bash
sudo bash /opt/ytdl/test-cookies.sh
```

### 3️⃣ View Worker Logs (Live)

```bash
sudo journalctl -u ytd-worker -f
```

Press `Ctrl+C` to stop.

### 4️⃣ View Last 50 Log Lines

```bash
sudo journalctl -u ytd-worker -n 50
```

### 5️⃣ Restart All Services

```bash
sudo systemctl restart ytd-worker ytd-api ytd-beat
```

### 6️⃣ Check Service Status

```bash
sudo systemctl status ytd-api ytd-worker ytd-beat
```

### 7️⃣ Pull Latest Code from GitHub

```bash
cd /opt/ytdl
sudo -u ytd git pull
sudo systemctl restart ytd-worker ytd-api ytd-beat
```

### 8️⃣ Check API Health

```bash
curl https://ytd.timobosafaris.com/health
```

### 9️⃣ View Environment Configuration

```bash
cat /opt/ytdl/.env.production
```

### 🔟 Fix File Permissions (If Needed)

```bash
sudo chown -R ytd:ytd /opt/ytdl
sudo chmod -R 755 /opt/ytdl/.venv
sudo chmod 640 /opt/ytdl/.env.production
sudo chmod 640 /opt/ytdl/youtube_cookies.txt
```

---

## 🚨 Emergency Troubleshooting

### Downloads Failing?

**Check worker logs**:
```bash
sudo journalctl -u ytd-worker -n 100
```

**Look for**:
- ❌ "cookies are no longer valid" → Need fresh cookies
- ❌ "Sign in to confirm you're not a bot" → Cookies expired or proxy needed
- ❌ "Failed to fetch video information" → Check yt-dlp/ffmpeg installation

### Services Not Running?

**Restart services**:
```bash
sudo systemctl restart ytd-worker ytd-api ytd-beat
sleep 5
sudo systemctl status ytd-worker ytd-api ytd-beat
```

**Check for errors**:
```bash
sudo journalctl -u ytd-worker -n 50
sudo journalctl -u ytd-api -n 50
```

### Can't Access Website?

**Check Nginx**:
```bash
sudo systemctl status nginx
sudo nginx -t
sudo systemctl restart nginx
```

**Check SSL**:
```bash
sudo certbot certificates
```

**Check API locally**:
```bash
curl http://localhost:3001/health
```

### GCS Upload Failing?

**Test GCS connection**:
```bash
cd /opt/ytdl
source .env.production
.venv/bin/python -c "from google.cloud import storage; client = storage.Client(); print('Connected!')"
```

**Check credentials**:
```bash
ls -la /opt/ytdl/gcp-credentials.json
sudo -u ytd test -r /opt/ytdl/gcp-credentials.json && echo "OK" || echo "FAIL"
```

---

## 📚 Full Documentation

- `CURRENT_STATUS.md` - Current system status
- `INSTALLATION.md` - Complete installation guide
- `EXPORT_COOKIES_GUIDE.md` - How to export YouTube cookies
- `REDIS_TROUBLESHOOTING.md` - Redis connection issues

---

## 🔗 URLs

- **Frontend**: https://ytd-bay.vercel.app
- **Backend API**: https://ytd.timobosafaris.com
- **API Docs**: https://ytd.timobosafaris.com/docs
- **Health**: https://ytd.timobosafaris.com/health

---

## ⚡ Quick Diagnostics

Run this one-liner to check everything:

```bash
echo "=== Services ===" && \
sudo systemctl is-active ytd-api ytd-worker ytd-beat nginx && \
echo "=== API Health ===" && \
curl -s https://ytd.timobosafaris.com/health | head -3 && \
echo "=== Cookies File ===" && \
ls -lh /opt/ytdl/youtube_cookies.txt && \
echo "=== Last Worker Error ===" && \
sudo journalctl -u ytd-worker --since "5 min ago" | grep ERROR | tail -3
```

---

## 🎯 Current Action Required

**⚠️ YouTube cookies are expired**

1. Export fresh cookies (see `EXPORT_COOKIES_GUIDE.md`)
2. Upload: `scp youtube_cookies.txt root@172.234.172.191:/opt/ytdl/`
3. Fix permissions: `sudo chown ytd:ytd /opt/ytdl/youtube_cookies.txt`
4. Restart: `sudo systemctl restart ytd-worker ytd-api ytd-beat`
5. Test: `sudo bash /opt/ytdl/test-cookies.sh`

---

*Last updated: 2026-02-09*
