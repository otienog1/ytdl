# YouTube Shorts Downloader - Backend Installation Guide

This guide explains how to deploy the YouTube Shorts Downloader backend on a fresh Ubuntu/Debian server using the automated installation script.

## Prerequisites

- Fresh Ubuntu 20.04+ or Debian 11+ server
- Root or sudo access
- Domain name pointed to your server (optional but recommended for SSL)
- MongoDB URI (MongoDB Atlas or self-hosted)
- Redis URL (Redis Cloud or self-hosted)
- Google Cloud Platform account with:
  - Cloud Storage bucket created
  - Service account with Storage Admin permissions
  - Service account JSON key file downloaded

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ytd.git
cd ytd/backend-python
```

### 2. Run the Installation Script

```bash
sudo bash install.sh
```

The script will prompt you for:
- Domain name (e.g., `ytd.timobosafaris.com`)
- MongoDB URI
- Redis URL
- GCP Project ID
- GCP Bucket Name
- Frontend CORS origins (comma-separated)
- SSL setup preference (y/n)
- Proxy configuration (optional but recommended)

### 3. Upload GCP Credentials

After installation completes, upload your GCP service account credentials:

```bash
# From your local machine
scp your-gcp-credentials.json root@your-server:/opt/ytdl/gcp-credentials.json

# On the server
sudo chown ytd:ytd /opt/ytdl/gcp-credentials.json
sudo chmod 640 /opt/ytdl/gcp-credentials.json
sudo systemctl restart ytd-worker ytd-api ytd-beat
```

### 4. Verify Installation

```bash
# Check service status
sudo systemctl status ytd-api ytd-worker ytd-beat

# View logs
sudo journalctl -u ytd-worker -f

# Test API
curl http://your-domain/health
```

## What the Installation Script Does

The `install.sh` script automates the entire deployment process by combining functionality from multiple utility scripts:

### 1. System Setup
- Updates system packages
- Installs Python 3, pip, and system dependencies
- Installs FFmpeg for video processing
- Installs Node.js 20 LTS (required for yt-dlp JavaScript runtime)
- Installs Nginx web server
- Installs pipenv for Python dependency management

### 2. Application Setup
- Creates `ytd` system user for running services
- Sets up application directory at `/opt/ytdl`
- Copies application files with correct permissions
- Creates Python virtual environment using pipenv
- Installs all Python dependencies from Pipfile
- Verifies yt-dlp installation

### 3. Configuration
- Creates `.env.production` with your configuration
- Sets up proper file permissions (640 for env files)
- Configures paths for FFmpeg and yt-dlp
- Optionally configures proxy settings

### 4. Service Installation
- Creates systemd service files for:
  - `ytd-api`: FastAPI web server
  - `ytd-worker`: Celery worker for async downloads
  - `ytd-beat`: Celery beat scheduler for cleanup tasks
- Configures services with correct PATH including Node.js
- Enables services to start on boot

### 5. Web Server Setup
- Configures Nginx as reverse proxy
- Sets up proper headers and timeouts
- Optionally obtains SSL certificate from Let's Encrypt
- Configures automatic HTTP to HTTPS redirect

### 6. Verification
- Starts all services
- Checks service status
- Provides troubleshooting commands
- Displays next steps for GCS credentials

## Configuration

### Environment Variables

The script creates `/opt/ytdl/.env.production` with the following variables:

```bash
# Database
MONGODB_URI=mongodb+srv://...

# Redis
REDIS_URL=redis://...
CELERY_BROKER_URL=redis://.../0
CELERY_RESULT_BACKEND=redis://.../0

# Google Cloud Storage
GCP_PROJECT_ID=your-project
GCP_BUCKET_NAME=your-bucket
GOOGLE_APPLICATION_CREDENTIALS=/opt/ytdl/gcp-credentials.json

# Server
PORT=3001
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend.com

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=30

# File Cleanup
FILE_EXPIRY_HOURS=12

# System Paths
FFMPEG_PATH=/usr/bin/ffmpeg
FFPROBE_PATH=/usr/bin/ffprobe
YT_DLP_PATH=/opt/ytdl/.venv/bin/yt-dlp

# Optional: Proxy for YouTube downloads
YT_DLP_PROXY=socks5://user:pass@host:port
```

### Systemd Services

Three systemd services are created:

#### ytd-api
FastAPI web server that handles API requests.
- Listens on port 3001
- Accessible via Nginx reverse proxy

#### ytd-worker
Celery worker that processes download jobs asynchronously.
- Fetches video metadata
- Downloads videos
- Uploads to Google Cloud Storage

#### ytd-beat
Celery beat scheduler for periodic tasks.
- Cleans up old downloads
- Removes failed jobs

### Nginx Configuration

Nginx is configured as a reverse proxy at `/etc/nginx/sites-available/ytd`:
- Proxies requests to FastAPI on port 3001
- Sets appropriate headers
- Configures timeouts for long downloads
- Optionally enables SSL with Let's Encrypt

## Proxy Configuration

**IMPORTANT**: YouTube aggressively blocks downloads from cloud server IPs (AWS, DigitalOcean, Linode, etc). Using a residential proxy is highly recommended for reliable Shorts downloads.

### Recommended Proxy Services
- [Bright Data](https://brightdata.com/) - Residential proxies
- [Smartproxy](https://smartproxy.com/) - Residential and datacenter
- [Oxylabs](https://oxylabs.io/) - Premium residential proxies

### Adding a Proxy

During installation, answer "y" when asked about proxy configuration, or add it later:

```bash
# Edit environment file
sudo nano /opt/ytdl/.env.production

# Add proxy line
YT_DLP_PROXY=socks5://username:password@proxy-host:port
# or
YT_DLP_PROXY=http://username:password@proxy-host:port

# Restart services
sudo systemctl restart ytd-worker ytd-api ytd-beat
```

## Useful Commands

### Service Management
```bash
# Start services
sudo systemctl start ytd-api ytd-worker ytd-beat

# Stop services
sudo systemctl stop ytd-api ytd-worker ytd-beat

# Restart services
sudo systemctl restart ytd-api ytd-worker ytd-beat

# Check status
sudo systemctl status ytd-api ytd-worker ytd-beat

# Enable on boot
sudo systemctl enable ytd-api ytd-worker ytd-beat
```

### Log Viewing
```bash
# View API logs (live)
sudo journalctl -u ytd-api -f

# View worker logs (live)
sudo journalctl -u ytd-worker -f

# View beat logs (live)
sudo journalctl -u ytd-beat -f

# View last 50 lines
sudo journalctl -u ytd-worker -n 50

# View logs since specific time
sudo journalctl -u ytd-worker --since "1 hour ago"
```

### Code Updates
```bash
# Pull latest code
cd /opt/ytdl
git pull

# If dependencies changed
export PIPENV_VENV_IN_PROJECT=1
pipenv install --deploy

# Fix permissions
sudo chown -R ytd:ytd /opt/ytdl
sudo chmod -R 755 /opt/ytdl/.venv

# Restart services
sudo systemctl restart ytd-worker ytd-api ytd-beat
```

### GCS Verification
```bash
# Check if GCS credentials are readable
sudo -u ytd test -r /opt/ytdl/gcp-credentials.json && echo "OK" || echo "FAILED"

# Test GCS connection
cd /opt/ytdl
source .env.production
.venv/bin/python -c "from google.cloud import storage; client = storage.Client(); print('Connected!')"
```

## Troubleshooting

### Services Won't Start

1. Check logs:
```bash
sudo journalctl -u ytd-worker -n 100
```

2. Verify permissions:
```bash
ls -la /opt/ytdl/.venv
ls -la /opt/ytdl/.env.production
```

3. Test manually:
```bash
cd /opt/ytdl
source .venv/bin/activate
python -m app.main
```

### YouTube Bot Detection

If downloads fail with "Sign in to confirm you're not a bot":

1. **Add a proxy** (recommended):
```bash
sudo nano /opt/ytdl/.env.production
# Add: YT_DLP_PROXY=socks5://user:pass@host:port
sudo systemctl restart ytd-worker
```

2. **Verify android client is being used**:
```bash
sudo journalctl -u ytd-worker | grep player_client
# Should show: youtube:player_client=android,ios
```

3. **Test yt-dlp directly**:
```bash
cd /opt/ytdl
.venv/bin/yt-dlp --extractor-args "youtube:player_client=android" --dump-json "https://www.youtube.com/shorts/VIDEO_ID"
```

### GCS Upload Failures

1. **Check credentials file**:
```bash
ls -la /opt/ytdl/gcp-credentials.json
sudo -u ytd cat /opt/ytdl/gcp-credentials.json | jq .
```

2. **Verify environment variable**:
```bash
sudo systemctl cat ytd-worker | grep GOOGLE_APPLICATION_CREDENTIALS
cat /opt/ytdl/.env.production | grep GOOGLE_APPLICATION_CREDENTIALS
```

3. **Test GCS connection**:
```bash
cd /opt/ytdl
source .env.production
.venv/bin/python << 'EOF'
from google.cloud import storage
client = storage.Client(project='your-project-id')
bucket = client.bucket('your-bucket-name')
print(f"Connected to bucket: {bucket.name}")
EOF
```

### Nginx 502 Bad Gateway

1. **Check if API is running**:
```bash
curl http://localhost:3001/health
```

2. **Check API logs**:
```bash
sudo journalctl -u ytd-api -n 50
```

3. **Verify Nginx configuration**:
```bash
sudo nginx -t
sudo systemctl status nginx
```

## SSL Certificate Renewal

If you set up SSL with Let's Encrypt, certificates auto-renew via cron. To manually renew:

```bash
sudo certbot renew
sudo systemctl reload nginx
```

## Security Best Practices

1. **Firewall**: Only expose ports 80, 443, and 22
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. **Credentials**: Never commit `.env.production` or GCP credentials to Git
3. **Updates**: Regularly update system packages
```bash
sudo apt-get update && sudo apt-get upgrade -y
```

4. **Monitoring**: Set up log monitoring and alerts for production

## Support

For issues or questions:
- Check logs: `sudo journalctl -u ytd-worker -f`
- Review this documentation
- Check GitHub issues

## File Structure

After installation:

```
/opt/ytdl/
├── .venv/                    # Python virtual environment (pipenv)
├── app/                      # Application code
│   ├── main.py              # FastAPI app
│   ├── services/            # Business logic
│   ├── queue/               # Celery tasks
│   └── models/              # Data models
├── downloads/               # Temporary download directory
├── logs/                    # Application logs
├── .env.production          # Environment configuration
├── gcp-credentials.json     # GCP service account key
├── Pipfile                  # Python dependencies
└── Pipfile.lock             # Locked dependency versions
```

## Next Steps

After successful installation:

1. Update frontend `NEXT_PUBLIC_API_URL` to point to your backend
2. Deploy frontend to Vercel
3. Add backend domain to frontend CORS configuration
4. Test end-to-end download flow
5. Monitor logs for any issues
6. Set up monitoring and alerts (optional)
