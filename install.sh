#!/bin/bash
set -e

# ============================================================
# YouTube Shorts Downloader - Production Install Script
# Run as: bash install.sh
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_USER="ytd"
SERVICE_PREFIX="ytd"

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
info() { echo -e "${BLUE}[→]${NC} $1"; }
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
    error "Please run as root: sudo bash install.sh"
fi

# ------------------------------------------------------------
# 2. System dependencies
# ------------------------------------------------------------
info "Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv \
    ffmpeg \
    nginx \
    curl wget git \
    build-essential \
    libssl-dev libffi-dev python3-dev
log "System dependencies installed"

# ------------------------------------------------------------
# 3. Create app user if not exists
# ------------------------------------------------------------
if ! id "$APP_USER" &>/dev/null; then
    info "Creating user '$APP_USER'..."
    useradd -m -s /bin/bash "$APP_USER"
    log "User '$APP_USER' created"
else
    log "User '$APP_USER' already exists"
fi

# ------------------------------------------------------------
# 4. Set up virtual environment
# ------------------------------------------------------------
info "Setting up Python virtual environment..."
cd "$APP_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
log "Python dependencies installed"

# ------------------------------------------------------------
# 5. Configure environment
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

# System FFmpeg (installed via apt)
FFMPEG_PATH=/usr/bin/ffmpeg
FFPROBE_PATH=/usr/bin/ffprobe
EOF

    log ".env.production created"
else
    warn ".env.production already exists, skipping"
fi

# Source the env to get PORT for nginx config
set -a
source "$ENV_FILE"
set +a
PORT=${PORT:-3001}

# ------------------------------------------------------------
# 6. Create required directories
# ------------------------------------------------------------
info "Creating required directories..."
mkdir -p "$APP_DIR/downloads" "$APP_DIR/logs"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
log "Directories created"

# ------------------------------------------------------------
# 7. Install systemd services
# ------------------------------------------------------------
info "Installing systemd services..."

# FastAPI service
cat > "/etc/systemd/system/${SERVICE_PREFIX}-api.service" <<EOF
[Unit]
Description=YTD FastAPI Server
After=network.target

[Service]
User=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin:/usr/bin:/bin"
EnvironmentFile=${ENV_FILE}
ExecStart=${APP_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Celery worker service
cat > "/etc/systemd/system/${SERVICE_PREFIX}-worker.service" <<EOF
[Unit]
Description=YTD Celery Worker
After=network.target

[Service]
User=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin:/usr/bin:/bin"
EnvironmentFile=${ENV_FILE}
ExecStart=${APP_DIR}/venv/bin/celery -A app.queue.celery_app worker --loglevel=info --concurrency=2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Celery beat service
cat > "/etc/systemd/system/${SERVICE_PREFIX}-beat.service" <<EOF
[Unit]
Description=YTD Celery Beat Scheduler
After=network.target

[Service]
User=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin:/usr/bin:/bin"
EnvironmentFile=${ENV_FILE}
ExecStart=${APP_DIR}/venv/bin/celery -A app.queue.celery_app beat --loglevel=info
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE_PREFIX}-api" "${SERVICE_PREFIX}-worker" "${SERVICE_PREFIX}-beat"
log "Systemd services installed"

# ------------------------------------------------------------
# 8. Configure Nginx
# ------------------------------------------------------------
info "Configuring Nginx..."

read -p "Enter your domain name (or server IP if no domain): " DOMAIN

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

# Enable site
ln -sf "/etc/nginx/sites-available/${SERVICE_PREFIX}" "/etc/nginx/sites-enabled/${SERVICE_PREFIX}"

# Remove default site if exists
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl restart nginx
log "Nginx configured"

# ------------------------------------------------------------
# 9. SSL setup (optional)
# ------------------------------------------------------------
echo ""
read -p "Set up SSL with Let's Encrypt? (requires a valid domain) [y/N]: " SETUP_SSL

if [[ "$SETUP_SSL" =~ ^[Yy]$ ]]; then
    info "Installing Certbot..."
    apt-get install -y -qq certbot python3-certbot-nginx
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "admin@${DOMAIN}" || warn "SSL setup failed - you can run 'sudo certbot --nginx -d ${DOMAIN}' manually later"
    log "SSL configured"
fi

# ------------------------------------------------------------
# 10. Start services
# ------------------------------------------------------------
info "Starting services..."
systemctl start "${SERVICE_PREFIX}-api" "${SERVICE_PREFIX}-worker" "${SERVICE_PREFIX}-beat"

sleep 3

# Check status
if systemctl is-active --quiet "${SERVICE_PREFIX}-api"; then
    log "API server is running"
else
    warn "API server failed to start - check: sudo journalctl -u ${SERVICE_PREFIX}-api -n 50"
fi

if systemctl is-active --quiet "${SERVICE_PREFIX}-worker"; then
    log "Celery worker is running"
else
    warn "Celery worker failed to start - check: sudo journalctl -u ${SERVICE_PREFIX}-worker -n 50"
fi

if systemctl is-active --quiet "${SERVICE_PREFIX}-beat"; then
    log "Celery beat is running"
else
    warn "Celery beat failed to start - check: sudo journalctl -u ${SERVICE_PREFIX}-beat -n 50"
fi

# ------------------------------------------------------------
# Done
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo -e "${GREEN}  Installation complete!${NC}"
echo "============================================================"
echo ""
echo "  API Server:    http://${DOMAIN}"
echo "  Health Check:  http://${DOMAIN}/health"
echo "  API Docs:      http://${DOMAIN}/docs"
echo ""
echo "  Useful commands:"
echo "    sudo systemctl status ${SERVICE_PREFIX}-api"
echo "    sudo systemctl restart ${SERVICE_PREFIX}-api ${SERVICE_PREFIX}-worker ${SERVICE_PREFIX}-beat"
echo "    sudo journalctl -u ${SERVICE_PREFIX}-api -f"
echo "    sudo journalctl -u ${SERVICE_PREFIX}-worker -f"
echo ""
