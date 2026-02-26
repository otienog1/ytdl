# Deploy Hybrid Redis - Start Here

## ✅ Server Git Issue Fixed

The server had a "divergent branches" error which has been fixed. The server is now synced with GitHub (commit 74b972c).

---

## 🚀 Deploy to All Servers

**Deployment scripts are now in the `backend-python/` directory**

You have **two options** to deploy:

### Option 1: PowerShell (Recommended for Windows)

**Just double-click:**
```
backend-python\deploy-from-local.bat
```

This will run the PowerShell deployment script which:
- Deploys to all 3 servers automatically
- Uses the config from `deploy-config.json`
- Shows colored status updates
- Verifies each deployment

### Option 2: Bash Script

If you prefer bash (Git Bash/WSL):
```bash
bash backend-python/deploy-from-local.sh
```

---

## 📋 What Gets Deployed

On each server, the deployment will:

1. ✅ Pull latest code from GitHub
2. ✅ Install local Redis (if not installed)
3. ✅ Copy `.env.production.server[N]` → `.env.production`
4. ✅ Restart all services (ytd-api, ytd-worker, ytd-beat)
5. ✅ Run verification tests

---

## ⚠️ Before You Deploy

Make sure you've created the production config files:

### Required Files (on your local machine):

```
backend-python/.env.production.server1
backend-python/.env.production.server2
backend-python/.env.production.server3

cookie-extractor/.env.production.server1
cookie-extractor/.env.production.server2
cookie-extractor/.env.production.server3
```

**Don't have these files?**

👉 See [PRODUCTION_CONFIG_SETUP.md](PRODUCTION_CONFIG_SETUP.md) for setup instructions

---

## 🎯 Expected Result

After deployment completes successfully, you should see:

```
✅ Successful Deployments (3):
   Server 1 : ytd.timobosafaris.com
   Server 2 : GCP 34.57.68.120
   Server 3 : AWS 13.60.71.187

🎉 All servers deployed successfully!
```

Each server will have:
- ✅ Local Redis running (zero latency)
- ✅ Backend services active
- ✅ Correct account configuration
- ✅ No timeout errors

---

## 🔍 WebSocket Issue

You also mentioned WebSocket connection errors (error 1006). After deployment, test the WebSocket fix:

### Run Diagnostic on Server 1:
```bash
ssh root@ytd.timobosafaris.com
cd /opt/ytdl
bash diagnose-websocket.sh
```

This will check:
- Nginx configuration
- Backend services status
- WebSocket endpoint connectivity
- Upstream server reachability

👉 See [FIX_WEBSOCKET.md](FIX_WEBSOCKET.md) for complete troubleshooting guide

---

## 🚨 If Deployment Fails

### Issue: Can't SSH to server
- Check your `deploy-config.json` has correct server IPs
- Make sure SSH keys are in the right location
- Test manually: `ssh root@ytd.timobosafaris.com`

### Issue: Missing .env.production.server* files
- The deployment script will fail if these don't exist
- Create them following [PRODUCTION_CONFIG_SETUP.md](PRODUCTION_CONFIG_SETUP.md)

### Issue: Services won't start
- SSH to the server: `ssh root@<server-ip>`
- Check logs: `sudo journalctl -u ytd-api -n 50`
- Check Redis: `redis-cli ping`

---

## 📞 Quick Commands

### Deploy to all servers:
```bash
backend-python\deploy-from-local.bat
```

### Check server status:
```bash
ssh root@ytd.timobosafaris.com "systemctl status ytd-api ytd-worker ytd-beat"
```

### Monitor worker logs:
```bash
ssh root@ytd.timobosafaris.com "journalctl -u ytd-worker -f"
```

### Test backend health:
```bash
curl https://ytd.timobosafaris.com/api/health/
```

---

## 🎉 Next Steps After Deployment

1. **Verify no timeout errors:**
   ```bash
   ssh root@ytd.timobosafaris.com "journalctl -u ytd-worker --since '10 minutes ago' | grep -i timeout"
   ```
   Should return nothing!

2. **Test a download** from the frontend at https://ytd.timobosafaris.com

3. **Check WebSocket connection** in browser console - should see:
   ```
   ✅ WebSocket connected
   ✅ Receiving progress updates
   ```

4. **Monitor performance** - local Redis should give <5ms response times

---

**Ready to deploy?** Just run:
```
backend-python\deploy-from-local.bat
```
