# YouTube Shorts Downloader

A complete YouTube Shorts downloader solution with frontend, backend, and residential proxy components.

## Quick Start

**Just need the proxy?** → [local-proxy/QUICKSTART.md](local-proxy/QUICKSTART.md) (5-minute setup)

**Full deployment guide:** → [START_HERE.md](START_HERE.md)

## Architecture Overview

This project consists of **three separate applications** that work together:

```
┌─────────────────┐
│   Frontend      │  Next.js web app (users interact here)
│  (Next.js/React)│  https://ytd.timobosafaris.com
└────────┬────────┘
         │ API requests
         ↓
┌─────────────────┐
│   Backend       │  FastAPI + Celery (cloud server)
│ (Python/FastAPI)│  172.234.172.191
└────────┬────────┘
         │ SOCKS5 proxy
         ↓
┌─────────────────┐
│  Local Proxy    │  SOCKS5 server (YOUR home computer)
│   (Node.js)     │  Residential IP
└────────┬────────┘
         │
         ↓
    YouTube Servers
```

## Why Three Separate Applications?

### 1. Frontend ([frontend/](frontend/))
- **Technology**: Next.js 14, React, TypeScript, TailwindCSS
- **Deployment**: Vercel or cloud server
- **Purpose**: User-facing web application
- **URL**: https://ytd.timobosafaris.com

[→ Frontend README](frontend/README.md)

### 2. Backend ([backend-python/](backend-python/))
- **Technology**: Python, FastAPI, Celery, Redis, MongoDB
- **Deployment**: Cloud server (172.234.172.191)
- **Purpose**: API server and video processing with yt-dlp

[→ Backend README](backend-python/README.md) | [→ Deployment Guide](backend-python/DEPLOYMENT.md)

### 3. Local Proxy ([local-proxy/](local-proxy/)) ⭐ REQUIRED FOR SHORTS
- **Technology**: Node.js, SOCKS5
- **Deployment**: YOUR home computer
- **Purpose**: Route requests through residential IP to bypass YouTube's datacenter IP blocking

This is a **standalone application** - you run it on your home computer, completely separate from the backend and frontend.

[→ Proxy README](local-proxy/README.md) | [→ Quick Start](local-proxy/QUICKSTART.md)

## Quick Setup Guide

### Option A: Just the Proxy (Backend Already Running)

If your backend is already deployed but facing YouTube bot detection errors:

1. **Run the proxy on your computer:**
   ```bash
   cd local-proxy
   npm install
   node simple-proxy.js --port 1080 --auth myuser:mypass123
   ```

2. **Configure router port forwarding** (forward port 1080)

3. **Update backend to use proxy:**
   ```bash
   ssh root@172.234.172.191
   sudo nano /opt/ytd/backend-python/.env.production
   # Add: YT_DLP_PROXY=socks5://myuser:mypass123@YOUR_PUBLIC_IP:1080
   sudo systemctl restart ytd-api ytd-worker
   ```

See [local-proxy/QUICKSTART.md](local-proxy/QUICKSTART.md) for detailed instructions.

### Option B: Full Stack Deployment

See [START_HERE.md](START_HERE.md) for complete deployment of all three components.

## Technology Stack

**Frontend:**
- Next.js 14, React 18, TypeScript
- TailwindCSS, Shadcn/ui
- React Query, Axios

**Backend:**
- Python 3.11, FastAPI, Celery
- Redis, MongoDB Atlas
- yt-dlp, ffmpeg
- Google Cloud Storage

**Proxy:**
- Node.js
- socksv5 (SOCKS5 protocol)

## Project Structure

```
ytd/
├── frontend/              # Next.js web application
│   ├── app/              # Next.js 14 app directory
│   ├── components/       # React components
│   ├── lib/             # API client and utilities
│   └── README.md
│
├── backend-python/       # Python backend API
│   ├── app/
│   │   ├── routes/      # FastAPI endpoints
│   │   ├── services/    # Business logic (yt-dlp, GCS)
│   │   ├── queue/       # Celery tasks
│   │   └── utils/       # Utilities
│   ├── DEPLOYMENT.md    # Deployment guide
│   └── README.md
│
└── local-proxy/          # ⭐ Residential proxy (STANDALONE)
    ├── simple-proxy.js  # SOCKS5 server
    ├── package.json
    ├── QUICKSTART.md    # 5-minute setup guide
    └── README.md        # Full documentation
```

## Important: Bypassing YouTube Bot Detection

YouTube **blocks datacenter/cloud server IPs** from downloading Shorts videos. You'll see errors like:

```
Sign in to confirm you're not a bot
```

**You have TWO solutions:**

### Option 1: Cookie Authentication ⭐ RECOMMENDED

Use the **standalone cookie extractor** to extract your YouTube cookies:

1. Run cookie extractor on your computer
2. Upload cookies to server
3. yt-dlp uses your cookies for authentication

**Pros:** Simple, no port forwarding, no network issues
**Cons:** Cookies expire every 30-90 days (just re-run the tool)

[→ Cookie Extractor Quick Start](cookie-extractor/QUICKSTART.md)

### Option 2: Residential Proxy

Use the **local proxy** to route requests through your home internet:

1. Run proxy on your home computer
2. Configure router port forwarding
3. Server connects through your residential IP

**Pros:** Longer lasting solution
**Cons:** Requires port forwarding, network configuration, may be blocked by ISP

[→ Local Proxy Quick Start](local-proxy/QUICKSTART.md)

## Common Issues & Solutions

### "Bot detection" / "Sign in to confirm"
**Solution 1 (Easier)**: Use cookie extractor → [cookie-extractor/QUICKSTART.md](cookie-extractor/QUICKSTART.md)
**Solution 2 (Advanced)**: Setup local proxy → [local-proxy/QUICKSTART.md](local-proxy/QUICKSTART.md)

### "Connection refused" from backend to proxy
**Causes**: Proxy not running, port forwarding not configured, wrong IP/credentials
**Solution**: Switch to cookie authentication or see [local-proxy/README.md#troubleshooting](local-proxy/README.md#troubleshooting)

### Cookies expire
**Solution**: Re-run cookie extractor (takes 2 minutes)

## Documentation

Each component has detailed setup instructions:

### Frontend
- [Frontend README](frontend/README.md) - React/Next.js setup and development

### Backend
- [Backend README](backend-python/README.md) - Python/FastAPI setup
- [Deployment Guide](backend-python/DEPLOYMENT.md) - Production deployment

### Cookie Extractor ⭐ RECOMMENDED
- [Cookie Extractor Quick Start](cookie-extractor/QUICKSTART.md) - 3-minute setup
- [Cookie Extractor README](cookie-extractor/README.md) - Full documentation

### Local Proxy (Alternative)
- [Proxy Quick Start](local-proxy/QUICKSTART.md) - 5-minute setup
- [Proxy README](local-proxy/README.md) - Complete documentation

### General
- [START_HERE.md](START_HERE.md) - Complete setup guide for all components

## Legal Considerations

This tool should only be used for:
- Downloading your own content
- Content you have permission to download
- Educational and personal use

**Do not use this tool to:**
- Violate YouTube's Terms of Service
- Infringe on copyright
- Redistribute downloaded content
- Commercial purposes without proper licensing

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Support

For issues and questions, please open an issue on GitHub.
