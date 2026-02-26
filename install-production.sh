#!/bin/bash
# YouTube Shorts Downloader - Complete Backend Installation Script
# Run as root on a fresh Ubuntu/Debian server
# Usage: sudo bash install.sh
#
# This script combines functionality from:
# - start-dev.sh: Main installation and setup
# - check-gcs.sh: GCS configuration verification
# - fix-nodejs-path.sh: Node.js PATH configuration
# - deploy-files.sh: File deployment utilities
# - deploy-update.sh: Update deployment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
info()  { echo -e "${BLUE}[→]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

clear
echo ""
echo "============================================================"
echo "  YouTube Shorts Downloader - Backend Installation"
echo "============================================================"
echo ""

# ------------------------------------------------------------
# 1. Check root
# ------------------------------------------------------------
if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo bash install.sh"
fi

# ------------------------------------------------------------
# 2. Get configuration from user
# ------------------------------------------------------------
info "Please provide the following configuration details:"
echo ""

read -p "Domain name (e.g., ytd.timobosafaris.com): " DOMAIN_NAME
read -p "MongoDB URI: " MONGODB_URI
read -p "Redis URL: " REDIS_URL
read -p "GCP Project ID: " GCP_PROJECT_ID
read -p "GCP Bucket Name: " GCP_BUCKET_NAME
read -p "Frontend CORS Origins (comma-separated, e.g., https://ytd-bay.vercel.app): " CORS_ORIGINS

echo ""
read -p "Do you want to set up SSL with Let's Encrypt? (y/n): " SETUP_SSL
if [ "$SETUP_SSL" == "y" ]; then
    read -p "Email for Let's Encrypt notifications: " SSL_EMAIL
fi

echo ""
read -p "Do you have a proxy for YouTube downloads? (y/n): " HAS_PROXY
if [ "$HAS_PROXY" == "y" ]; then
    read -p "Proxy URL (e.g., socks5://user:pass@host:port or http://user:pass@host:port): " PROXY_URL
else
    PROXY_URL=""
fi

echo ""
info "Configuration summary:"
echo "  Domain: $DOMAIN_NAME"
echo "  SSL: $SETUP_SSL"
echo "  Proxy: ${PROXY_URL:-None}"
echo ""
read -p "Proceed with installation? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    error "Installation cancelled"
fi

# ------------------------------------------------------------
# 3. System Updates and Dependencies
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Step 1: Installing System Dependencies"
echo "============================================================"
echo ""

info "Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

info "Installing required packages..."
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    nginx \
    curl \
    git \
    wget \
    certbot \
    python3-certbot-nginx \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev

# Install Node.js 20 LTS (required for yt-dlp JavaScript runtime)
if ! command -v node &> /dev/null || [ "$(node -v | cut -d'.' -f1 | tr -d 'v')" -lt 18 ]; then
    info "Installing Node.js 20 LTS..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
fi

NODE_PATH=$(which node)
NODE_DIR=$(dirname "$NODE_PATH")
log "Node.js installed: $(node --version) at $NODE_PATH"

log "System dependencies installed"

# ------------------------------------------------------------
# 4. Install pipenv
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Step 2: Installing pipenv"
echo "============================================================"
echo ""

info "Installing pipenv..."
apt-get install -y -qq pipenv || pip3 install --break-system-packages pipenv
log "Pipenv installed"

# ------------------------------------------------------------
# 5. Create Application User
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Step 3: Creating Application User"
echo "============================================================"
echo ""

APP_USER="ytd"
if id "$APP_USER" &>/dev/null; then
    warn "User '$APP_USER' already exists"
else
    info "Creating user '$APP_USER'..."
    useradd -m -s /bin/bash "$APP_USER"
    log "User '$APP_USER' created"
fi

# ------------------------------------------------------------
# 6. Setup Application Directory
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Step 4: Setting Up Application"
echo "============================================================"
echo ""

APP_DIR="/opt/ytdl"
CURRENT_DIR=$(pwd)

info "Setting up application directory at $APP_DIR..."

# If current directory is not /opt/ytdl, copy files there
if [ "$CURRENT_DIR" != "$APP_DIR" ]; then
    if [ -d "$APP_DIR" ]; then
        warn "Directory $APP_DIR already exists, backing up..."
        mv "$APP_DIR" "${APP_DIR}.backup.$(date +%s)"
    fi

    mkdir -p "$APP_DIR"
    info "Copying application files..."
    cp -r . "$APP_DIR/"
    cd "$APP_DIR"
else
    info "Already in $APP_DIR"
fi

# Set permissions
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
chmod -R 755 "$APP_DIR"

log "Application directory set up"

# ------------------------------------------------------------
# 7. Install Python Dependencies
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Step 5: Installing Python Dependencies"
echo "============================================================"
echo ""

info "Installing Python dependencies with pipenv..."

# Force pipenv to create venv in project
export PIPENV_VENV_IN_PROJECT=1

# Remove old venv if exists
if [ -d ".venv" ]; then
    warn "Removing old virtual environment..."
    rm -rf .venv
fi

# Install dependencies as ytd user
sudo -u "$APP_USER" -E bash << 'EOFPIPENV'
export PIPENV_VENV_IN_PROJECT=1
cd /opt/ytdl

# Install dependencies
pipenv install --deploy
EOFPIPENV

# Get venv path
VENV_PATH=$(cd "$APP_DIR" && pipenv --venv)
log "Python dependencies installed at $VENV_PATH"

# Verify installations
info "Verifying installations..."
if "$VENV_PATH/bin/python" -c "import yt_dlp; print('yt-dlp version:', yt_dlp.version.__version__)" 2>/dev/null; then
    log "yt-dlp verified"
else
    warn "yt-dlp not found in virtualenv - check Pipfile"
fi

# Set venv permissions
chmod -R 755 .venv
chown -R "$APP_USER":"$APP_USER" .venv

log "Python dependencies installed"

# ------------------------------------------------------------
# 8. Create Environment File
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Step 6: Creating Environment Configuration"
echo "============================================================"
echo ""

ENV_FILE="$APP_DIR/.env.production"

info "Creating .env.production file..."

cat > "$ENV_FILE" << EOFENV
# Database
MONGODB_URI=$MONGODB_URI

# Redis
REDIS_URL=$REDIS_URL

# Celery (uses Redis)
CELERY_BROKER_URL=${REDIS_URL}/0
CELERY_RESULT_BACKEND=${REDIS_URL}/0

# Google Cloud Storage
GCP_PROJECT_ID=$GCP_PROJECT_ID
GCP_BUCKET_NAME=$GCP_BUCKET_NAME
GOOGLE_APPLICATION_CREDENTIALS=/opt/ytdl/gcp-credentials.json

# FastAPI Server
PORT=3001
ENVIRONMENT=production
CORS_ORIGINS=$CORS_ORIGINS

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=30

# File Cleanup
FILE_EXPIRY_HOURS=12

# System Paths
FFMPEG_PATH=/usr/bin/ffmpeg
FFPROBE_PATH=/usr/bin/ffprobe
YT_DLP_PATH=/opt/ytdl/.venv/bin/yt-dlp
EOFENV

# Add proxy if configured
if [ -n "$PROXY_URL" ]; then
    echo "YT_DLP_PROXY=$PROXY_URL" >> "$ENV_FILE"
fi

chmod 640 "$ENV_FILE"
chown "$APP_USER":"$APP_USER" "$ENV_FILE"

log "Environment configuration created"

warn "IMPORTANT: You need to upload your GCP credentials file to /opt/ytdl/gcp-credentials.json"
warn "Example: scp your-gcp-credentials.json root@server:/opt/ytdl/gcp-credentials.json"

# ------------------------------------------------------------
# 9. Create Required Directories
# ------------------------------------------------------------
info "Creating required directories..."
mkdir -p "$APP_DIR/downloads" "$APP_DIR/logs"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
log "Directories created"

# ------------------------------------------------------------
# 10. Create Systemd Services
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Step 7: Creating Systemd Services"
echo "============================================================"
echo ""

SERVICE_PREFIX="ytd"

info "Creating API service..."
cat > "/etc/systemd/system/${SERVICE_PREFIX}-api.service" << 'EOFAPI'
[Unit]
Description=YTD FastAPI Server
After=network.target

[Service]
Type=simple
User=ytd
Group=ytd
WorkingDirectory=/opt/ytdl
Environment="PATH=/opt/ytdl/.venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/opt/ytdl/.env.production
ExecStart=/opt/ytdl/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFAPI

info "Creating Celery worker service..."
cat > "/etc/systemd/system/${SERVICE_PREFIX}-worker.service" << 'EOFWORKER'
[Unit]
Description=YTD Celery Worker
After=network.target

[Service]
Type=simple
User=ytd
Group=ytd
WorkingDirectory=/opt/ytdl
Environment="PATH=/opt/ytdl/.venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/opt/ytdl/.env.production
ExecStart=/opt/ytdl/.venv/bin/celery -A app.queue.celery_app worker --loglevel=info --concurrency=1 --max-tasks-per-child=10
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFWORKER

info "Creating Celery beat service..."
cat > "/etc/systemd/system/${SERVICE_PREFIX}-beat.service" << 'EOFBEAT'
[Unit]
Description=YTD Celery Beat Scheduler
After=network.target

[Service]
Type=simple
User=ytd
Group=ytd
WorkingDirectory=/opt/ytdl
Environment="PATH=/opt/ytdl/.venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/opt/ytdl/.env.production
ExecStart=/opt/ytdl/.venv/bin/celery -A app.queue.celery_app beat --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFBEAT

log "Systemd services created"

# ------------------------------------------------------------
# 11. Configure Nginx
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Step 8: Configuring Nginx"
echo "============================================================"
echo ""

info "Creating Nginx configuration..."

cat > /etc/nginx/sites-available/ytd << EOFNGINX
server {
    listen 80;
    server_name $DOMAIN_NAME;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;

        # Timeout settings for long-running downloads
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        send_timeout 300;
    }
}
EOFNGINX

# Enable site
if [ -L /etc/nginx/sites-enabled/ytd ]; then
    rm /etc/nginx/sites-enabled/ytd
fi
ln -s /etc/nginx/sites-available/ytd /etc/nginx/sites-enabled/

# Remove default site
if [ -L /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Test nginx configuration
nginx -t

log "Nginx configured"

# ------------------------------------------------------------
# 12. Setup SSL (if requested)
# ------------------------------------------------------------
if [ "$SETUP_SSL" == "y" ]; then
    echo ""
    echo "============================================================"
    echo "  Step 9: Setting Up SSL with Let's Encrypt"
    echo "============================================================"
    echo ""

    info "Obtaining SSL certificate..."
    certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos -m "$SSL_EMAIL" --redirect || warn "SSL setup failed - run 'sudo certbot --nginx -d ${DOMAIN_NAME}' manually"

    log "SSL certificate obtained and configured"
fi

# ------------------------------------------------------------
# 13. Start Services
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Step 10: Starting Services"
echo "============================================================"
echo ""

info "Reloading systemd daemon..."
systemctl daemon-reload

info "Enabling services..."
systemctl enable ytd-api ytd-worker ytd-beat nginx

info "Starting services..."
systemctl restart nginx
systemctl restart ytd-api ytd-worker ytd-beat

sleep 3

# Check service status
echo ""
info "Checking service status..."
if systemctl is-active --quiet ytd-api; then
    log "API server is running"
else
    warn "API server failed to start"
fi

if systemctl is-active --quiet ytd-worker; then
    log "Celery worker is running"
else
    warn "Celery worker failed to start"
fi

if systemctl is-active --quiet ytd-beat; then
    log "Celery beat is running"
else
    warn "Celery beat failed to start"
fi

if systemctl is-active --quiet nginx; then
    log "Nginx is running"
else
    warn "Nginx failed to start"
fi

# ------------------------------------------------------------
# 14. Verify GCS Configuration (from check-gcs.sh)
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo "  Step 11: Verifying Configuration"
echo "============================================================"
echo ""

info "GCS configuration will be verified once you upload credentials..."
warn "Remember to upload: scp your-credentials.json root@server:/opt/ytdl/gcp-credentials.json"
warn "Then set permissions: sudo chown ytd:ytd /opt/ytdl/gcp-credentials.json && sudo chmod 640 /opt/ytdl/gcp-credentials.json"
warn "And restart services: sudo systemctl restart ytd-worker ytd-api ytd-beat"

# ------------------------------------------------------------
# Installation Complete
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo -e "${GREEN}  Installation Complete!${NC}"
echo "============================================================"
echo ""
echo "Application Details:"
echo "  - App Directory: $APP_DIR"
echo "  - Domain: $DOMAIN_NAME"
echo "  - API Port: 3001"
if [ "$SETUP_SSL" == "y" ]; then
    echo "  - SSL: Enabled (auto-renewal configured)"
    echo "  - URL: https://$DOMAIN_NAME"
else
    echo "  - SSL: Not configured"
    echo "  - URL: http://$DOMAIN_NAME"
fi
echo ""
echo "IMPORTANT NEXT STEPS:"
echo "  1. Upload GCP credentials:"
echo "     scp your-credentials.json root@server:/opt/ytdl/gcp-credentials.json"
echo "     sudo chown ytd:ytd /opt/ytdl/gcp-credentials.json"
echo "     sudo chmod 640 /opt/ytdl/gcp-credentials.json"
echo ""
echo "  2. After uploading credentials, restart services:"
echo "     sudo systemctl restart ytd-worker ytd-api ytd-beat"
echo ""
echo "  3. Verify GCS connection (optional):"
echo "     cd /opt/ytdl && sudo bash -c 'source .env.production && $VENV_PATH/bin/python -c \"from google.cloud import storage; client = storage.Client(); print(\\\"GCS Connected!\\\")\"'"
echo ""
echo "Useful Commands:"
echo "  - View API logs:    sudo journalctl -u ytd-api -f"
echo "  - View worker logs: sudo journalctl -u ytd-worker -f"
echo "  - View beat logs:   sudo journalctl -u ytd-beat -f"
echo "  - Restart services: sudo systemctl restart ytd-worker ytd-api ytd-beat"
echo "  - Check status:     sudo systemctl status ytd-worker ytd-api ytd-beat"
echo "  - Update code:      cd /opt/ytdl && git pull && sudo systemctl restart ytd-worker ytd-api ytd-beat"
echo ""
if [ -z "$PROXY_URL" ]; then
    warn "NO PROXY CONFIGURED: YouTube Shorts may be blocked on cloud server IPs"
    echo "  To add a proxy later, edit /opt/ytdl/.env.production and add:"
    echo "  YT_DLP_PROXY=socks5://user:pass@host:port"
    echo "  Then restart: sudo systemctl restart ytd-worker ytd-api"
    echo ""
fi
echo "============================================================"
echo ""
