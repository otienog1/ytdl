# Setup .env.production.server* Files

## 🚨 Missing Configuration Files

The deployment failed because `.env.production.server*` files don't exist on the servers.

**These files must be created on your LOCAL machine first**, then the deployment script will copy them to the servers.

---

## 📋 Required Files

You need to create these files **on your local machine** in the `backend-python/` directory:

```
backend-python/.env.production.server1
backend-python/.env.production.server2
backend-python/.env.production.server3
```

And in the `cookie-extractor/` directory:

```
cookie-extractor/.env.production.server1
cookie-extractor/.env.production.server2
cookie-extractor/.env.production.server3
```

---

## ✅ Quick Setup

### Option 1: Copy from Server (If Files Exist There)

If the servers already have `.env.production` files, copy them locally:

```powershell
# Server 1
scp root@ytd.timobosafaris.com:/opt/ytdl/backend-python/.env.production backend-python/.env.production.server1
scp root@ytd.timobosafaris.com:/opt/ytdl/cookie-extractor/.env.production cookie-extractor/.env.production.server1

# Server 2
scp 7plus8@35.193.12.77:/opt/ytdl/backend-python/.env.production backend-python/.env.production.server2
scp 7plus8@35.193.12.77:/opt/ytdl/cookie-extractor/.env.production cookie-extractor/.env.production.server2

# Server 3
scp admin@13.60.71.187:/opt/ytdl/backend-python/.env.production backend-python/.env.production.server3
scp admin@13.60.71.187:/opt/ytdl/cookie-extractor/.env.production cookie-extractor/.env.production.server3
```

### Option 2: Create from Template

Use the example files as templates:

```bash
# Backend
cd backend-python
cp .env.production.server1.example .env.production.server1
cp .env.production.server1.example .env.production.server2
cp .env.production.server1.example .env.production.server3

# Cookie extractor
cd ../cookie-extractor
cp .env.production.server1.example .env.production.server1
cp .env.production.server1.example .env.production.server2
cp .env.production.server1.example .env.production.server3
```

Then edit each file to set the correct values for each server.

---

## 🔧 What Each Server Needs

### Server 1 (ytd.timobosafaris.com)
```bash
# backend-python/.env.production.server1
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
YT_ACCOUNT_ID=account_a
YOUTUBE_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_a.txt
```

### Server 2 (GCP 35.193.12.77)
```bash
# backend-python/.env.production.server2
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
YT_ACCOUNT_ID=account_b
YOUTUBE_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_b.txt
```

### Server 3 (AWS 13.60.71.187)
```bash
# backend-python/.env.production.server3
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
YT_ACCOUNT_ID=account_c
YOUTUBE_COOKIES_FILE=/opt/ytdl/youtube_cookies_account_c.txt
```

---

## ⚠️ Important Notes

1. **Don't commit these files to git** - They contain sensitive credentials
   - They're already in `.gitignore`
   - Keep them local only

2. **Each server uses local Redis** - `localhost:6379` (not remote Redis)
   - This eliminates network latency
   - No more timeout errors

3. **Different YouTube accounts per server**:
   - Server 1: account_a (otienog1@yahoo.com)
   - Server 2: account_b (otienog1@icluod.com)
   - Server 3: account_c (7plus8studios@gmail.com)

---

## 🚀 After Creating Files

Once you've created all 6 files, run the deployment again:

```powershell
cd backend-python
.\deploy-from-local.bat
```

The deployment should now succeed and copy the files to each server!

---

## 📞 Need Help?

If the files exist on the servers but you can't copy them:

```bash
# Check if files exist on server
ssh root@ytd.timobosafaris.com "ls -la /opt/ytdl/backend-python/.env.production"

# Show contents (be careful - contains secrets!)
ssh root@ytd.timobosafaris.com "cat /opt/ytdl/backend-python/.env.production"
```

See [PRODUCTION_CONFIG_SETUP.md](../PRODUCTION_CONFIG_SETUP.md) for detailed setup instructions.
