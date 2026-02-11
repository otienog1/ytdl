# Quick Start Guide

Get the YouTube Shorts Downloader running in minutes!

## Prerequisites Checklist

- [ ] Node.js 18+ installed
- [ ] yt-dlp installed
- [ ] ffmpeg installed
- [ ] MongoDB running (local or Atlas)
- [ ] Redis running (local or cloud)
- [ ] Google Cloud Storage bucket created

## 5-Minute Setup

### 1. Install Dependencies

```bash
# Install yt-dlp
# macOS
brew install yt-dlp

# Ubuntu/Debian
sudo apt install yt-dlp

# Windows - Download from: https://github.com/yt-dlp/yt-dlp#installation

# Install ffmpeg
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows - Download from: https://ffmpeg.org/download.html
```

### 2. Clone and Install

```bash
# Clone repository
git clone <repository-url>
cd youtube-shorts-downloader

# Install backend dependencies
cd backend
npm install

# Install frontend dependencies
cd ../frontend
npm install
```

### 3. Configure Environment

**Backend (.env)**
```bash
cd backend
cp .env.example .env
# Edit .env with your values
```

Minimum required:
```env
MONGODB_URI=mongodb://localhost:27017/shorts-downloader
REDIS_URL=redis://localhost:6379
GCP_PROJECT_ID=your-project
GCP_BUCKET_NAME=your-bucket
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
CORS_ORIGIN=http://localhost:3000
```

**Frontend (.env.local)**
```bash
cd ../frontend
cp .env.example .env.local
# Edit .env.local
```

```env
NEXT_PUBLIC_API_URL=http://localhost:3001
```

### 4. Start Services

**Terminal 1 - Start MongoDB (if local)**
```bash
mongod
```

**Terminal 2 - Start Redis (if local)**
```bash
redis-server
```

**Terminal 3 - Start Backend**
```bash
cd backend
npm run dev
```

**Terminal 4 - Start Frontend**
```bash
cd frontend
npm run dev
```

### 5. Test the Application

1. Open http://localhost:3000 in your browser
2. Paste a YouTube Shorts URL: `https://youtube.com/shorts/VIDEO_ID`
3. Click "Download Video"
4. Wait for processing
5. Download your video!

## Using Docker (Alternative)

If you prefer Docker:

```bash
cd backend
docker-compose up -d
```

Then start the frontend:
```bash
cd ../frontend
npm run dev
```

## Common Issues

### "yt-dlp: command not found"
Install yt-dlp and ensure it's in your PATH.

### "ffmpeg: command not found"
Install ffmpeg and ensure it's in your PATH.

### "MongoDB connection failed"
- Check if MongoDB is running: `mongod`
- Verify MONGODB_URI in .env

### "Redis connection failed"
- Check if Redis is running: `redis-server`
- Verify REDIS_URL in .env

### "GCS upload failed"
- Verify Google Cloud credentials
- Check if bucket exists
- Ensure service account has permissions

## Next Steps

- Read the full [README.md](./README.md) for detailed documentation
- Configure rate limiting in backend/.env
- Set up production deployment on Vercel and Cloud Run
- Customize the UI in frontend/components

## Need Help?

- Check the [README.md](./README.md) for detailed documentation
- Open an issue on GitHub
- Review the troubleshooting section

## Production Checklist

Before deploying to production:

- [ ] Set NODE_ENV=production
- [ ] Use production MongoDB (MongoDB Atlas)
- [ ] Use production Redis (Redis Cloud)
- [ ] Configure proper CORS_ORIGIN
- [ ] Set up file cleanup schedule
- [ ] Configure rate limiting
- [ ] Add monitoring and logging
- [ ] Review security settings
- [ ] Test error handling
- [ ] Set up SSL/HTTPS
