# Quick Start: Development Environment

## Prerequisites Check ✅

Both MongoDB and Redis are verified and running:

- **MongoDB**: Port 27017 ✅
- **Redis/Memurai**: Port 6379 ✅

Run verification anytime:
```bash
cd backend-python
pipenv run python test-connections.py
```

---

## Start All Services (3 Terminals)

### Terminal 1: Backend Server
```bash
cd backend-python
.\start-dev.bat
```

**What it does:**
- Starts FastAPI server on port 3001
- Connects to local MongoDB (ytdl_db)
- Connects to local Redis
- Enables CORS for localhost:3000
- Hot reload on code changes

**Verify:**
- Open http://localhost:3001/docs
- Should see "FastAPI - Swagger UI"

---

### Terminal 2: Celery Worker
```bash
cd backend-python
pipenv run celery -A app.queue.celery_app worker --loglevel=info --pool=solo
```

**What it does:**
- Starts Celery worker for background tasks
- Connects to Redis as message broker
- Connects to MongoDB for storing results
- Processes video download jobs

**Verify:**
- Look for: "Connected to redis://localhost:6379/0"
- Look for: "celery@[hostname] ready"

---

### Terminal 3: Frontend
```bash
cd frontend
npm run dev
```

**What it does:**
- Starts Next.js dev server on port 3000
- Hot reload on code changes
- Connects to backend API at localhost:3001

**Verify:**
- Open http://localhost:3000
- Should see YouTube downloader UI

---

## Quick Verification Checklist

After starting all services:

- [ ] Backend API docs accessible: http://localhost:3001/docs
- [ ] Backend health check: http://localhost:3001/health
- [ ] Frontend loads: http://localhost:3000
- [ ] WebSocket connection indicator shows green dot
- [ ] Storage stats display in navigation (top-right)
- [ ] Can navigate to History page

---

## Test Full Flow

1. **Download a video**:
   - Paste YouTube URL: `https://youtube.com/shorts/[video-id]`
   - Click "Download Video"
   - Watch progress bar update in real-time (WebSocket)
   - Download completes and saves to storage

2. **Check history**:
   - Navigate to http://localhost:3000/history
   - See downloaded video in list
   - Test filters and search

3. **Check storage**:
   - View storage indicator in navigation
   - Click to see detailed breakdown
   - Verify provider stats (GCS, Azure, S3)

---

## Troubleshooting

### MongoDB Not Running
```bash
# Check status
netstat -ano | findstr :27017

# Start service
net start MongoDB
```

### Redis/Memurai Not Running
```bash
# Check status
netstat -ano | findstr :6379

# Start service
net start Memurai

# Test connection
"C:\Program Files\Memurai\memurai-cli.exe" ping
```

### Port Already in Use

**Backend (3001):**
```bash
netstat -ano | findstr :3001
taskkill /PID [process_id] /F
```

**Frontend (3000):**
```bash
netstat -ano | findstr :3000
taskkill /PID [process_id] /F
```

### Clear Redis Queue
```bash
"C:\Program Files\Memurai\memurai-cli.exe" FLUSHALL
```

### Reset MongoDB Database
```bash
mongosh
use ytdl_db
db.dropDatabase()
```

---

## Stop All Services

1. **Backend**: Press `Ctrl+C` in Terminal 1
2. **Celery**: Press `Ctrl+C` in Terminal 2
3. **Frontend**: Press `Ctrl+C` in Terminal 3

MongoDB and Redis/Memurai will keep running as Windows services (this is normal).

---

## Environment Variables

All configuration in `backend-python/.env`:

```env
# Local Development
MONGODB_URI=mongodb://localhost:27017/ytdl_db
MONGODB_DB_NAME=ytdl_db
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

Frontend configuration in `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:3001
```

---

## Useful Commands

### Check All Services at Once
```bash
cd backend-python
.\check-all-services.bat
```

### Monitor Redis Activity
```bash
"C:\Program Files\Memurai\memurai-cli.exe" MONITOR
```

### Check Celery Queue Length
```bash
"C:\Program Files\Memurai\memurai-cli.exe" LLEN celery
```

### View MongoDB Data
- Use **MongoDB Compass**: mongodb://localhost:27017
- Database: `ytdl_db`
- Collections: `downloads`, `storage_stats`

---

## Need Help?

- **Backend Documentation**: [backend-python/README.md](backend-python/README.md)
- **Frontend Documentation**: [frontend/README.md](frontend/README.md)
- **Complete Setup Guide**: [LOCAL_DEV_READY.md](backend-python/LOCAL_DEV_READY.md)
- **Days 4-6 Summary**: [DAYS_4_5_6_COMPLETE.md](DAYS_4_5_6_COMPLETE.md)

---

**Happy Coding! 🚀**
