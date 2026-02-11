# Setup Without Docker - Local Development

This guide will help you run the YouTube Shorts Downloader without Docker.

## Prerequisites

Install these tools on your system:

### 1. Node.js and npm
- Download from https://nodejs.org (version 18 or higher)
- Verify installation:
  ```bash
  node -v
  npm -v
  ```

### 2. yt-dlp

**Windows:**
```bash
# Using winget
winget install yt-dlp

# Or download from: https://github.com/yt-dlp/yt-dlp/releases
# Place yt-dlp.exe in a folder and add to PATH
```

**macOS:**
```bash
brew install yt-dlp
```

**Linux:**
```bash
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp
```

Verify: `yt-dlp --version`

### 3. ffmpeg

**Windows:**
```bash
# Using winget
winget install Gyan.FFmpeg

# Or download from: https://ffmpeg.org/download.html
# Extract and add to PATH
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

Verify: `ffmpeg -version`

### 4. MongoDB

**Option A: MongoDB Atlas (Recommended - Free Cloud)**
1. Go to https://www.mongodb.com/cloud/atlas
2. Create free account
3. Create M0 Free Cluster
4. Create database user
5. Get connection string
6. No local installation needed!

**Option B: Local MongoDB**

**Windows:**
- Download from: https://www.mongodb.com/try/download/community
- Install and run as service

**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Linux:**
```bash
sudo apt-get install -y mongodb
sudo systemctl start mongod
sudo systemctl enable mongod
```

Verify: `mongosh` or check MongoDB Compass

### 5. Redis

**Option A: Redis Cloud (Recommended - Free)**
1. Go to https://redis.com/try-free
2. Create free account
3. Create 30MB free database
4. Get connection string
5. No local installation needed!

**Option B: Local Redis**

**Windows:**
- Download from: https://github.com/tporadowski/redis/releases
- Extract and run `redis-server.exe`

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

Verify: `redis-cli ping` (should return PONG)

### 6. Google Cloud Storage

1. Go to https://console.cloud.google.com
2. Create new project
3. Enable Cloud Storage API
4. Create a storage bucket
5. Create service account with Storage Admin role
6. Download JSON credentials file

## Installation Steps

### Step 1: Install Dependencies

```bash
# Navigate to project
cd c:\Users\7plus8\build\ytd

# Install backend dependencies
cd backend
npm install

# Install frontend dependencies
cd ../frontend
npm install
```

### Step 2: Configure Backend

Create `backend/.env` file:

```env
# Database (choose one)
# Option A: MongoDB Atlas (cloud)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/shorts-downloader

# Option B: Local MongoDB
# MONGODB_URI=mongodb://localhost:27017/shorts-downloader

# Redis (choose one)
# Option A: Redis Cloud
REDIS_URL=redis://default:password@redis-12345.cloud.redislabs.com:12345

# Option B: Local Redis
# REDIS_URL=redis://localhost:6379

# Google Cloud Storage
GCP_PROJECT_ID=your-project-id
GCP_BUCKET_NAME=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\credentials.json

# Server
PORT=3001
NODE_ENV=development
CORS_ORIGIN=http://localhost:3000

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=30

# File Cleanup
FILE_EXPIRY_HOURS=24
```

**Important for Windows:** Use double backslashes in paths or forward slashes:
- `C:\\Users\\7plus8\\credentials.json` or
- `C:/Users/7plus8/credentials.json`

### Step 3: Configure Frontend

Create `frontend/.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:3001
```

### Step 4: Verify Services

Check that all services are running:

```bash
# Test MongoDB connection
# If using Atlas: connection string should work
# If local:
mongosh

# Test Redis connection
redis-cli ping
# Should return: PONG

# Test yt-dlp
yt-dlp --version

# Test ffmpeg
ffmpeg -version
```

## Running the Application

### Start Backend (Terminal 1)

```bash
cd c:\Users\7plus8\build\ytd\backend
npm run dev
```

You should see:
```
MongoDB connected successfully
Redis connected successfully
Google Cloud Storage initialized
Server is running on port 3001
```

### Start Frontend (Terminal 2)

```bash
cd c:\Users\7plus8\build\ytd\frontend
npm run dev
```

You should see:
```
  ▲ Next.js 16.1.6
  - Local:        http://localhost:3000
  - Ready in 2.5s
```

### Access the Application

Open your browser and go to: **http://localhost:3000**

## Testing the Setup

1. **Test Health Check:**
   ```bash
   curl http://localhost:3001/health
   # Should return: {"status":"ok","timestamp":"..."}
   ```

2. **Test Video Download:**
   - Open http://localhost:3000
   - Paste a YouTube Shorts URL
   - Click "Download Video"
   - Wait for processing
   - Download should complete!

## Troubleshooting

### Backend won't start

**MongoDB connection error:**
```bash
# Check if MongoDB is running
# Local: mongosh
# Atlas: verify connection string and IP whitelist (use 0.0.0.0/0)
```

**Redis connection error:**
```bash
# Check if Redis is running
redis-cli ping

# Windows: make sure redis-server.exe is running
# Mac/Linux: brew services start redis
```

**yt-dlp not found:**
```bash
# Check if in PATH
yt-dlp --version

# Windows: add to PATH in System Environment Variables
# Mac/Linux: verify /usr/local/bin is in PATH
```

**ffmpeg not found:**
```bash
# Check if in PATH
ffmpeg -version

# Windows: add to PATH in System Environment Variables
# Mac/Linux: verify installation
```

**GCS credentials error:**
```bash
# Verify file path in .env
# Windows: use double backslashes or forward slashes
# Make sure file exists at that path
```

### Frontend won't start

**Port 3000 already in use:**
```bash
# Use different port
npm run dev -- -p 3001

# Or kill process using port 3000
# Windows: netstat -ano | findstr :3000
# Mac/Linux: lsof -ti:3000 | xargs kill
```

**Can't connect to backend:**
- Check `NEXT_PUBLIC_API_URL` in `frontend/.env.local`
- Make sure backend is running on port 3001
- Check CORS settings in backend

### CORS errors

Make sure in `backend/.env`:
```env
CORS_ORIGIN=http://localhost:3000
```

### Downloads fail

**Video info fetch fails:**
- Test yt-dlp manually: `yt-dlp --dump-json <youtube-url>`
- Check YouTube URL format
- Some videos may be restricted

**Upload to GCS fails:**
- Verify GCS credentials
- Check bucket exists
- Verify service account permissions

## Development Tips

### Auto-restart on changes

Both frontend and backend support hot-reload:
- Frontend: automatically reloads on file changes
- Backend: uses `ts-node-dev` for auto-restart

### View logs

**Backend logs:**
- Console output shows all requests
- Check `backend/error.log` for errors
- Check `backend/combined.log` for all logs

**Frontend logs:**
- Console output in terminal
- Browser console for client-side errors

### Stop the application

Press `Ctrl+C` in both terminals to stop frontend and backend.

## Project Structure

```
c:\Users\7plus8\build\ytd\
├── backend/
│   ├── src/              # Source code
│   ├── downloads/        # Temporary video storage (auto-created)
│   ├── .env             # Your configuration
│   └── package.json
│
├── frontend/
│   ├── app/             # Next.js pages
│   ├── components/      # React components
│   ├── .env.local       # Your configuration
│   └── package.json
│
└── README.md            # Documentation
```

## Next Steps

Once running successfully:

1. **Test all features:**
   - URL validation
   - Video download
   - Progress tracking
   - Error handling

2. **Customize:**
   - Adjust rate limits in `backend/.env`
   - Modify UI in `frontend/components/`
   - Change styling in `frontend/app/globals.css`

3. **Prepare for production:**
   - Follow [DEPLOYMENT.md](./DEPLOYMENT.md)
   - Use [CHECKLIST.md](./CHECKLIST.md)
   - Set up monitoring

## Quick Command Reference

```bash
# Start backend
cd backend && npm run dev

# Start frontend
cd frontend && npm run dev

# Install new dependency (backend)
cd backend && npm install <package-name>

# Install new dependency (frontend)
cd frontend && npm install <package-name>

# Build for production
cd backend && npm run build
cd frontend && npm run build

# Check for errors
cd backend && npm run lint
cd frontend && npm run lint
```

## Getting Help

1. Check error messages in terminal
2. Review logs in `backend/*.log`
3. Check browser console (F12)
4. Verify all services are running
5. Review [README.md](./README.md) for detailed docs
6. Check [QUICKSTART.md](./QUICKSTART.md)

---

**You're all set!** The application runs entirely locally without Docker. 🎉
