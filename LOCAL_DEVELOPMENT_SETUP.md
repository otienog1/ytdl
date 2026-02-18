# Local Development Setup - Complete Guide

You're experiencing "max number of clients reached" errors on **both MongoDB Atlas and Redis Cloud** because you're using free tier services with connection limits.

**Solution**: Use local MongoDB and Redis for development!

## 🎯 Quick Start (TL;DR)

1. **MongoDB**: Already installed and running ✅
2. **Redis**: Install and start (see below)
3. **Configuration**: Already updated ✅
4. **Restart**: Backend and Celery worker

## 📦 Install Redis (Choose One Method)

### Method 1: Chocolatey (Fastest - Recommended)

```powershell
# Run PowerShell as Administrator
choco install redis-64

# Start Redis
redis-server
```

### Method 2: Memurai (Best for Windows)

1. Download: https://www.memurai.com/get-memurai
2. Install (runs as Windows service automatically)
3. Done! It's already running on port 6379

### Method 3: WSL2

```bash
# In WSL2 Ubuntu
sudo apt update && sudo apt install redis-server
sudo service redis-server start
```

## ✅ Verify Redis

```bash
redis-cli ping
# Should return: PONG
```

Or run: `.\check-redis.bat`

## 📝 Configuration (Already Done!)

Your `.env` is already configured for local development:

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017/ytdl_db
MONGODB_DB_NAME=ytdl_db

# Redis
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 🚀 Start Everything

### 1. Ensure Services Are Running

```bash
# Check MongoDB
.\check-mongodb.bat

# Check Redis
.\check-redis.bat
```

### 2. Start Backend (Terminal 1)

```bash
cd backend-python
.\start-dev.bat
```

You should see:
```
MongoDB connected successfully to database: ytdl_db
Redis connected successfully
```

### 3. Start Celery (Terminal 2)

```bash
cd backend-python
pipenv run celery -A app.queue.celery_app worker --loglevel=info --pool=solo
```

You should see:
```
Connected to redis://localhost:6379/0
```

## ✨ Benefits

### Before (Cloud Services)
- ❌ "max number of clients reached" errors
- ❌ Connection limits (MongoDB Atlas M0: 500, Redis Cloud Free: varies)
- ❌ Network latency
- ❌ Requires internet connection
- ❌ Can't debug easily

### After (Local Services)
- ✅ **No connection limits** - unlimited!
- ✅ **Faster** - no network latency
- ✅ **Works offline** - develop anywhere
- ✅ **Free** - no cost concerns
- ✅ **Better debugging** - full access to data
- ✅ **Clean slate** - fresh database for testing

## 🔍 Useful Commands

### MongoDB
```bash
# Connect with mongosh
mongosh mongodb://localhost:27017/ytdl_db

# View collections
show collections

# Query downloads
db.downloads.find().pretty()

# Count documents
db.downloads.countDocuments()
```

### Redis
```bash
# Connect to Redis CLI
redis-cli

# View all keys
KEYS *

# Check Celery queue
LLEN celery

# Monitor real-time
MONITOR

# Flush all data (careful!)
FLUSHALL
```

## 🔄 Switching to Production

When deploying to production, update `.env`:

```env
# MongoDB Atlas
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/ytdl_db

# Redis Cloud
REDIS_URL=redis://default:pass@redis-server.com:17684
CELERY_BROKER_URL=redis://default:pass@redis-server.com:17684/0
CELERY_RESULT_BACKEND=redis://default:pass@redis-server.com:17684/0
```

## 📊 Architecture

```
┌─────────────────────────────────────────┐
│          Your Application               │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐    ┌──────────────┐  │
│  │   FastAPI   │    │    Celery    │  │
│  │   Backend   │    │    Worker    │  │
│  └──────┬──────┘    └──────┬───────┘  │
│         │                   │          │
│         └────────┬──────────┘          │
│                  │                     │
└──────────────────┼─────────────────────┘
                   │
       ┌───────────┴───────────┐
       │                       │
┌──────▼──────┐      ┌────────▼────────┐
│   MongoDB   │      │     Redis       │
│ localhost   │      │  localhost      │
│   :27017    │      │    :6379        │
└─────────────┘      └─────────────────┘
```

## 🐛 Troubleshooting

### "max number of clients reached" still appears

**Check which service**:
- MongoDB error → Check MongoDB connection in logs
- Redis error → Check Redis connection in logs

**Ensure services are running**:
```bash
.\check-mongodb.bat
.\check-redis.bat
```

**Verify .env is loaded**:
- Restart both backend and Celery
- Check logs for "MongoDB connected to database: ytdl_db"
- Check logs for "Connected to redis://localhost:6379"

### Services won't start

**MongoDB**:
```bash
# Check service
sc query MongoDB

# Start service
net start MongoDB
```

**Redis**:
```bash
# Start manually
redis-server

# Or if installed as service
net start Redis
```

### Port conflicts

**MongoDB (27017)**:
```bash
netstat -ano | findstr :27017
```

**Redis (6379)**:
```bash
netstat -ano | findstr :6379
```

---

## 🎉 You're All Set!

Once both MongoDB and Redis are running locally, you'll have:
- ✅ No connection limit errors
- ✅ Fast, reliable local development
- ✅ Full control over your data
- ✅ Better debugging capabilities

**Ready to code!** 🚀
