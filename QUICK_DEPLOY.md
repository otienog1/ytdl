# Quick Deployment Guide - Hybrid Redis

## 🚀 Deploy from Local Machine (Recommended)

Run this on your **local Windows machine** to deploy to all servers at once:

```bash
# Windows (double-click or run from cmd)
deploy-from-local.bat

# Or using Git Bash / WSL
bash deploy-from-local.sh
```

This will automatically:
- Deploy to all 3 servers in sequence
- Pull latest code
- Install local Redis
- Deploy configurations
- Restart services
- Run verification tests

## 🔧 Deploy on Individual Server

If you prefer to deploy on each server individually:

### Server 1 (ytd.timobosafaris.com)
```bash
cd /opt/ytdl && sudo bash deploy-hybrid-redis.sh 1
```

### Server 2 (GCP 34.57.68.120)
```bash
cd /opt/ytdl && sudo bash deploy-hybrid-redis.sh 2
```

### Server 3 (AWS 13.60.71.187)
```bash
cd /opt/ytdl && sudo bash deploy-hybrid-redis.sh 3
```

## 📥 Just Pull Code (No Deployment)

```bash
cd /opt/ytdl && sudo bash pull-latest.sh
```

## 🔄 Manual Deployment Steps

If you prefer manual deployment:

```bash
# 1. Pull latest code
cd /opt/ytdl
git pull origin master
cd backend-python && git pull origin main
cd ../frontend && git pull origin main
cd ..

# 2. Install local Redis (if not installed)
bash install-local-redis.sh

# 3. Deploy config (replace '1' with '2' or '3' for other servers)
cd backend-python
sudo cp .env.production.server1 .env.production
sudo chown ytdl:ytdl .env.production

cd ../cookie-extractor
sudo cp .env.production.server1 .env.production
sudo chown ytdl:ytdl .env.production

# 4. Restart services
sudo systemctl restart ytd-api ytd-worker ytd-beat ytd-cookie-extractor

# 5. Verify
redis-cli ping
curl -I http://localhost:3001/api/health/
sudo journalctl -u ytd-worker --since "5 minutes ago" | grep -i error
```

## ✅ Post-Deployment Checks

**1. Check Services:**
```bash
sudo systemctl status ytd-api ytd-worker ytd-beat
```

**2. Check Local Redis:**
```bash
redis-cli ping  # Should return: PONG
redis-cli INFO clients | grep connected_clients
```

**3. Check Backend:**
```bash
curl http://localhost:3001/api/health/
```

**4. Check for Errors:**
```bash
sudo journalctl -u ytd-worker --since "10 minutes ago" | grep -i error
# Should return nothing if deployment successful!
```

**5. Monitor Logs:**
```bash
# Watch worker logs in real-time
sudo journalctl -u ytd-worker -f
```

## 📊 Expected Results

✅ **No timeout errors**
✅ **Services start successfully**
✅ **Local Redis responding**
✅ **Backend API healthy**
✅ **<5ms task processing**

## 🔧 Troubleshooting

### Services Won't Start
```bash
sudo journalctl -u ytd-api -n 50
sudo journalctl -u ytd-worker -n 50
```

### Redis Issues
```bash
sudo systemctl status redis-server
redis-cli ping
```

### Wrong Configuration
```bash
cd /opt/ytdl/backend-python
cat .env.production | grep YT_ACCOUNT_ID
# Server 1: account_a
# Server 2: account_b
# Server 3: account_c
```

## 📝 Server Mapping

| Server | IP | Account | Config Files |
|--------|----|---------| -------------|
| Server 1 | 172.234.172.191 | A (otienog1@yahoo.com) | `.env.production.server1` |
| Server 2 | 34.57.68.120 | B (otienog1@icluod.com) | `.env.production.server2` |
| Server 3 | 13.60.71.187 | C (7plus8studios@gmail.com) | `.env.production.server3` |

## 🔄 Rollback

If something goes wrong:

```bash
# Restore backup .env.production
cd /opt/ytdl/backend-python
sudo cp .env.production.backup.* .env.production

# Restart services
sudo systemctl restart ytd-api ytd-worker ytd-beat
```

## 📚 Full Documentation

- [DEPLOY_HYBRID_REDIS.md](DEPLOY_HYBRID_REDIS.md) - Complete deployment guide
- [HYBRID_REDIS_SUMMARY.md](HYBRID_REDIS_SUMMARY.md) - Architecture overview
- [install-local-redis.sh](install-local-redis.sh) - Redis installation script
- [deploy-hybrid-redis.sh](deploy-hybrid-redis.sh) - Automated deployment
- [pull-latest.sh](pull-latest.sh) - Pull code only
