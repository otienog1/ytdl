#!/bin/bash
set -e

# ============================================================
# YouTube Shorts Downloader - Production Setup (pipenv)
# Run as: sudo bash start-dev.sh
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_USER="ytd"
SERVICE_PREFIX="ytd"

log()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
info()  { echo -e "${BLUE}[→]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "============================================================"
echo "  YouTube Shorts Downloader - Production Setup"
echo "============================================================"
echo ""

# ------------------------------------------------------------
# 1. Check root
# ------------------------------------------------------------
if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo bash start-dev.sh"
fi

# Move app to /opt/ytdl if not already there — ensures consistent deployment location
if [[ "$APP_DIR" != "/opt/ytdl" ]]; then
    warn "App is at $APP_DIR, moving to /opt/ytdl for production deployment..."
    info "Moving app to /opt/ytdl..."
    mkdir -p /opt/ytdl

    # If /opt/ytdl already exists and has files, back it up
    if [ -d "/opt/ytdl" ] && [ "$(ls -A /opt/ytdl 2>/dev/null)" ]; then
        BACKUP_DIR="/opt/ytdl.backup.$(date +%Y%m%d_%H%M%S)"
        warn "Backing up existing /opt/ytdl to $BACKUP_DIR"
        mv /opt/ytdl "$BACKUP_DIR"
        mkdir -p /opt/ytdl
    fi

    # Copy app to /opt/ytdl
    cp -a "$APP_DIR/." /opt/ytdl/
    APP_DIR="/opt/ytdl"

    # Remove any copied .venv — it contains hardcoded paths that need to be rebuilt
    rm -rf "$APP_DIR/.venv"
    log "App moved to $APP_DIR"
fi

# ------------------------------------------------------------
# 2. System dependencies
# ------------------------------------------------------------
info "Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip \
    ffmpeg \
    nginx \
    curl wget git \
    build-essential \
    libssl-dev libffi-dev python3-dev

# Install Node.js (required for yt-dlp JavaScript runtime)
if ! command -v node &>/dev/null; then
    info "Installing Node.js for yt-dlp JavaScript runtime..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
    log "Node.js installed: $(node --version)"
else
    log "Node.js already installed: $(node --version)"
fi

log "System dependencies installed"

# ------------------------------------------------------------
# 3. Install pipenv
# ------------------------------------------------------------
if ! command -v pipenv &>/dev/null; then
    info "Installing pipenv..."
    apt-get install -y -qq pipenv || pip3 install --break-system-packages pipenv
    log "pipenv installed"
else
    log "pipenv already installed"
fi

# ------------------------------------------------------------
# 4. Create app user if not exists
# ------------------------------------------------------------
if ! id "$APP_USER" &>/dev/null; then
    info "Creating user '$APP_USER'..."
    useradd -m -s /bin/bash "$APP_USER"
    log "User '$APP_USER' created"
else
    log "User '$APP_USER' already exists"
fi

# ------------------------------------------------------------
# 5. Create virtualenv and install dependencies from Pipfile
# ------------------------------------------------------------
info "Creating virtualenv and installing dependencies from Pipfile..."
cd "$APP_DIR"

# Set PIPENV_VENV_IN_PROJECT so the .venv lives inside the project dir
export PIPENV_VENV_IN_PROJECT=1

# Create the virtualenv and install all packages listed in Pipfile
pipenv install --deploy
log "Python dependencies installed"

# Get pipenv virtualenv path for use in systemd services
# (pipenv shell is interactive; we use the venv path directly instead)
VENV_PATH=$(pipenv --venv)
log "Virtualenv: $VENV_PATH"

# ------------------------------------------------------------
# 5b. Verify ffmpeg and yt-dlp installations
# ------------------------------------------------------------
info "Verifying ffmpeg and yt-dlp..."

# Confirm system ffmpeg is available
if command -v ffmpeg &>/dev/null; then
    FFMPEG_BIN=$(which ffmpeg)
    FFPROBE_BIN=$(which ffprobe)
    log "ffmpeg: $FFMPEG_BIN"
    log "ffprobe: $FFPROBE_BIN"
else
    error "ffmpeg not found after installation. Aborting."
fi

# Verify yt-dlp is installed inside the virtualenv
if "$VENV_PATH/bin/python" -c "import yt_dlp; print('yt-dlp version:', yt_dlp.version.__version__)" 2>/dev/null; then
    log "yt-dlp verified"
else
    warn "yt-dlp not found in virtualenv - check Pipfile"
fi

# ------------------------------------------------------------
# 6. Configure environment
# ------------------------------------------------------------
ENV_FILE="$APP_DIR/.env.production"

if [ ! -f "$ENV_FILE" ]; then
    info "Creating .env.production..."
    echo ""
    warn "You need to provide your configuration values."
    echo ""

    read -p "MongoDB URI: " MONGODB_URI
    read -p "Redis URL: " REDIS_URL
    read -p "GCP Project ID [divine-actor-473706-k4]: " GCP_PROJECT_ID
    GCP_PROJECT_ID=${GCP_PROJECT_ID:-divine-actor-473706-k4}
    read -p "GCP Bucket Name [ytdl_bkt]: " GCP_BUCKET_NAME
    GCP_BUCKET_NAME=${GCP_BUCKET_NAME:-ytdl_bkt}
    read -p "GCP Credentials JSON path [$APP_DIR/divine-actor-473706-k4-fdec9ee56ba0.json]: " GCP_CREDS
    GCP_CREDS=${GCP_CREDS:-$APP_DIR/divine-actor-473706-k4-fdec9ee56ba0.json}
    read -p "CORS Origins (your frontend URL, e.g. https://yourdomain.com): " CORS_ORIGINS
    read -p "Port [3001]: " PORT
    PORT=${PORT:-3001}

    cat > "$ENV_FILE" <<EOF
# Database
MONGODB_URI=${MONGODB_URI}

# Redis
REDIS_URL=${REDIS_URL}

# Celery (uses Redis)
CELERY_BROKER_URL=${REDIS_URL}/0
CELERY_RESULT_BACKEND=${REDIS_URL}/0

# Google Cloud Storage
GCP_PROJECT_ID=${GCP_PROJECT_ID}
GCP_BUCKET_NAME=${GCP_BUCKET_NAME}
GOOGLE_APPLICATION_CREDENTIALS=${GCP_CREDS}

# FastAPI Server
PORT=${PORT}
ENVIRONMENT=production
CORS_ORIGINS=${CORS_ORIGINS}

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=30

# File Cleanup
FILE_EXPIRY_HOURS=12

# FFmpeg (system installation)
FFMPEG_PATH=${FFMPEG_BIN}
FFPROBE_PATH=${FFPROBE_BIN}

# yt-dlp (virtualenv installation)
YT_DLP_PATH=${VENV_PATH}/bin/yt-dlp
EOF

    log ".env.production created"
else
    warn ".env.production already exists, skipping"
fi

# Source the env to get PORT
set -a
source "$ENV_FILE"
set +a
PORT=${PORT:-3001}

# ------------------------------------------------------------
# 7. Create required directories
# ------------------------------------------------------------
info "Creating required directories..."
mkdir -p "$APP_DIR/downloads" "$APP_DIR/logs"
# Fix permissions on .venv so the service user can execute binaries
chmod -R 755 "$APP_DIR/.venv"
# Transfer ownership of entire app dir to service user
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
# Ensure root can still read/write app files for future updates
chmod 755 "$APP_DIR"
log "Directories created"

# ------------------------------------------------------------
# 8. Install systemd services (Optimized for 1GB RAM)
# ------------------------------------------------------------
info "Installing systemd services..."

cat > "/etc/systemd/system/${SERVICE_PREFIX}-api.service" <<EOF
[Unit]
Description=YTD FastAPI Server
After=network.target

[Service]
User=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${VENV_PATH}/bin:/usr/bin:/bin"
EnvironmentFile=${ENV_FILE}
# Reduced to 1 worker to save RAM
ExecStart=${VENV_PATH}/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

cat > "/etc/systemd/system/${SERVICE_PREFIX}-worker.service" <<EOF
[Unit]
Description=YTD Celery Worker
After=network.target

[Service]
User=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${VENV_PATH}/bin:/usr/bin:/bin"
EnvironmentFile=${ENV_FILE}
# Added max-tasks-per-child to prevent memory bloat
ExecStart=${VENV_PATH}/bin/celery -A app.queue.celery_app worker --loglevel=info --concurrency=1 --max-tasks-per-child=10
Restart=always
RestartSec=5
# Memory limits to prevent 100% Swap usage
MemoryHigh=700M
MemoryMax=850M
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE_PREFIX}-api" "${SERVICE_PREFIX}-worker" "${SERVICE_PREFIX}-beat"
log "Systemd services installed"

# ------------------------------------------------------------
# 9. Configure Nginx
# ------------------------------------------------------------
info "Configuring Nginx..."

read -p "Domain name [timobosafaris.com]: " DOMAIN
DOMAIN=${DOMAIN:-timobosafaris.com}

cat > "/etc/nginx/sites-available/${SERVICE_PREFIX}" <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:${PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
    }
}
EOF

ln -sf "/etc/nginx/sites-available/${SERVICE_PREFIX}" "/etc/nginx/sites-enabled/${SERVICE_PREFIX}"
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
log "Nginx configured"

# ------------------------------------------------------------
# 10. SSL setup (optional)
# ------------------------------------------------------------
echo ""
read -p "Set up SSL with Let's Encrypt? (requires a valid domain) [y/N]: " SETUP_SSL

if [[ "$SETUP_SSL" =~ ^[Yy]$ ]]; then
    info "Installing Certbot..."
    apt-get install -y -qq certbot python3-certbot-nginx
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "admin@${DOMAIN}" || warn "SSL setup failed - run 'sudo certbot --nginx -d ${DOMAIN}' manually"
    log "SSL configured"
fi

# ------------------------------------------------------------
# 11. Start services
# ------------------------------------------------------------
info "Starting services..."
systemctl start "${SERVICE_PREFIX}-api" "${SERVICE_PREFIX}-worker" "${SERVICE_PREFIX}-beat"

sleep 3

systemctl is-active --quiet "${SERVICE_PREFIX}-api"    && log "API server is running"    || warn "API server failed - check: sudo journalctl -u ${SERVICE_PREFIX}-api -n 50"
systemctl is-active --quiet "${SERVICE_PREFIX}-worker" && log "Celery worker is running" || warn "Celery worker failed - check: sudo journalctl -u ${SERVICE_PREFIX}-worker -n 50"
systemctl is-active --quiet "${SERVICE_PREFIX}-beat"   && log "Celery beat is running"   || warn "Celery beat failed - check: sudo journalctl -u ${SERVICE_PREFIX}-beat -n 50"

# ------------------------------------------------------------
# Done
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo -e "${GREEN}  Setup complete!${NC}"
echo "============================================================"
echo ""
echo "  API:           http://${DOMAIN}"
echo "  Health:        http://${DOMAIN}/health"
echo "  Docs:          http://${DOMAIN}/docs"
echo ""
echo "  Useful commands:"
echo "    sudo systemctl status ${SERVICE_PREFIX}-api"
echo "    sudo systemctl restart ${SERVICE_PREFIX}-api ${SERVICE_PREFIX}-worker ${SERVICE_PREFIX}-beat"
echo "    sudo journalctl -u ${SERVICE_PREFIX}-api -f"
echo "    sudo journalctl -u ${SERVICE_PREFIX}-worker -f"
echo ""
