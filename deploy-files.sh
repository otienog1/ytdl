#!/bin/bash
# Deploy updated files to server
# Run on server: bash deploy-files.sh

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

APP_DIR="/opt/ytdl"

echo ""
echo "============================================================"
echo "  Deploying Updated Files"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo bash deploy-files.sh"
fi

# Check if we're in the right directory
if [ ! -f "app/services/youtube_service.py" ]; then
    error "Please run this script from /opt/ytdl directory"
fi

info "Stopping services..."
systemctl stop ytd-worker ytd-api ytd-beat
log "Services stopped"

info "Updating file permissions..."
chown ytd:ytd app/services/youtube_service.py
chmod 644 app/services/youtube_service.py

if [ -f "divine-actor-473706-k4-fdec9ee56ba0.json" ]; then
    chown root:root divine-actor-473706-k4-fdec9ee56ba0.json
    chmod 644 divine-actor-473706-k4-fdec9ee56ba0.json
    log "GCP credentials file permissions updated"
fi

info "Verifying youtube_service.py content..."
if grep -q "player_client=ios,tv_embedded,android" app/services/youtube_service.py; then
    log "Multi-client fix detected in code ✓"
else
    warn "Multi-client fix NOT found in code!"
fi

info "Starting services..."
systemctl start ytd-worker ytd-api ytd-beat

sleep 3

# Check service status
systemctl is-active --quiet ytd-api    && log "API server is running"    || warn "API server failed"
systemctl is-active --quiet ytd-worker && log "Celery worker is running" || warn "Celery worker failed"
systemctl is-active --quiet ytd-beat   && log "Celery beat is running"   || warn "Celery beat failed"

echo ""
echo "============================================================"
echo -e "${GREEN}  Deployment complete!${NC}"
echo "============================================================"
echo ""
echo "Monitor logs with:"
echo "  sudo journalctl -u ytd-worker -f"
echo ""
