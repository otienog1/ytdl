# 🚀 Start Here - No Docker Setup

Quick guide to get your YouTube Shorts Downloader running locally without Docker.

## Prerequisites (Install These First)

1. **Node.js 18+** - Download from https://nodejs.org
2. **yt-dlp** - For downloading videos
3. **ffmpeg** - For processing videos
4. **MongoDB** - Use MongoDB Atlas (free cloud) OR install locally
5. **Redis** - Use Redis Cloud (free) OR install locally
6. **Google Cloud Storage** - Free tier available

## Installation Commands

### Windows

```powershell
# Install yt-dlp
winget install yt-dlp

# Install ffmpeg
winget install Gyan.FFmpeg

# Or download manually:
# yt-dlp: https://github.com/yt-dlp/yt-dlp/releases
# ffmpeg: https://ffmpeg.org/download.html
```

### macOS

```bash
# Install yt-dlp and ffmpeg
brew install yt-dlp ffmpeg
```

### Linux

```bash
# Install yt-dlp
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp

# Install ffmpeg
sudo apt update
sudo apt install ffmpeg
```

## Quick Setup (5 Steps)

### 1. Install Dependencies

```bash
# Backend
cd backend
npm install

# Frontend
cd ../frontend
npm install
```

### 2. Set Up MongoDB

**Recommended: MongoDB Atlas (Free Cloud)**
- Go to https://www.mongodb.com/cloud/atlas
- Create free account → Create M0 Free Cluster
- Create database user
- Whitelist IP: 0.0.0.0/0
- Get connection string

### 3. Set Up Redis

**Recommended: Redis Cloud (Free)**
- Go to https://redis.com/try-free
- Create free account → Create 30MB database
- Get connection string

### 4. Configure Backend

Create `backend/.env`:

```env
# Use MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/shorts-downloader

# Use Redis Cloud connection string
REDIS_URL=redis://default:password@your-redis-url.com:12345

# Google Cloud Storage (get from GCP Console)
GCP_PROJECT_ID=your-project-id
GCP_BUCKET_NAME=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=C:/path/to/credentials.json

# Server config
PORT=3001
NODE_ENV=development
CORS_ORIGIN=http://localhost:3000
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=30
FILE_EXPIRY_HOURS=24
```

### 5. Configure Frontend

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:3001
```

## Running the Application

### Option 1: Use Startup Scripts (Easiest)

**Windows:**
```bash
# Double-click or run:
start-dev.bat
```

**macOS/Linux:**
```bash
chmod +x start-dev.sh
./start-dev.sh
```

### Option 2: Manual Start (Two Terminals)

**Terminal 1 - Backend:**
```bash
cd backend
npm run dev
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Access the App

Open your browser: **http://localhost:3000**

## Verify It's Working

1. **Check Backend Health:**
   - Go to http://localhost:3001/health
   - Should see: `{"status":"ok","timestamp":"..."}`

2. **Test Download:**
   - Open http://localhost:3000
   - Paste a YouTube Shorts URL
   - Click "Download Video"
   - Wait for processing
   - Download your video!

## Troubleshooting

### Backend Won't Start

**"yt-dlp: command not found"**
- Install yt-dlp and add to PATH
- Windows: Check System Environment Variables
- Verify: `yt-dlp --version`

**"ffmpeg: command not found"**
- Install ffmpeg and add to PATH
- Verify: `ffmpeg -version`

**"MongoDB connection failed"**
- Check MONGODB_URI in `.env`
- For Atlas: verify IP whitelist and credentials
- For local: ensure MongoDB is running

**"Redis connection failed"**
- Check REDIS_URL in `.env`
- For cloud: verify connection string
- For local: ensure Redis is running (`redis-server`)

**"GCS credentials error"**
- Check file path in GOOGLE_APPLICATION_CREDENTIALS
- Windows: use `C:/` or `C:\\` format
- Verify file exists

### Frontend Won't Start

**"Port 3000 already in use"**
```bash
# Use different port
npm run dev -- -p 3001
```

**"Cannot connect to backend"**
- Check backend is running on port 3001
- Verify `NEXT_PUBLIC_API_URL` in `.env.local`

### CORS Errors

Check `backend/.env`:
```env
CORS_ORIGIN=http://localhost:3000
```

## Detailed Documentation

- **Complete Guide:** [SETUP_WITHOUT_DOCKER.md](./SETUP_WITHOUT_DOCKER.md)
- **Full Docs:** [README.md](./README.md)
- **Quick Start:** [QUICKSTART.md](./QUICKSTART.md)
- **Deployment:** [DEPLOYMENT.md](./DEPLOYMENT.md)

## Project Structure

```
c:\Users\7plus8\build\ytd\
│
├── backend/              # Express.js API
│   ├── src/             # Source code
│   ├── .env            # Your config (create this)
│   └── package.json
│
├── frontend/            # Next.js app
│   ├── app/            # Pages
│   ├── components/     # UI components
│   ├── .env.local      # Your config (create this)
│   └── package.json
│
├── START_HERE.md       # This file
├── start-dev.bat       # Windows startup script
└── start-dev.sh        # Mac/Linux startup script
```

## What You Need to Provide

1. **MongoDB connection string** - Get from MongoDB Atlas
2. **Redis connection string** - Get from Redis Cloud
3. **GCS credentials JSON** - Download from Google Cloud Console
4. **GCS project ID** - From Google Cloud Console
5. **GCS bucket name** - Create in Google Cloud Storage

## Free Tier Resources

All these have free tiers:

- ✅ **MongoDB Atlas** - 512MB free
- ✅ **Redis Cloud** - 30MB free
- ✅ **Google Cloud Storage** - 5GB free
- ✅ **Vercel** (for frontend deployment) - Free hobby tier
- ✅ **Google Cloud Run** (for backend deployment) - 2M requests/month free

## Next Steps

Once running successfully:

1. ✅ Test video download functionality
2. ✅ Check all pages (Terms, Privacy, FAQ)
3. ✅ Test on mobile browser
4. ✅ Review logs for errors
5. 🚀 Ready to deploy? See [DEPLOYMENT.md](./DEPLOYMENT.md)

## Need Help?

1. Check error messages in terminal
2. Review [SETUP_WITHOUT_DOCKER.md](./SETUP_WITHOUT_DOCKER.md)
3. Check [README.md](./README.md) troubleshooting section
4. Verify all prerequisites are installed

---

**Ready to start?** Run the setup commands above, then use the startup scripts!

**Questions?** All documentation is in this folder. Start with the files above. 📚
