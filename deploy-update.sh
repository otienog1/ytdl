#!/bin/bash
# Quick deployment script to update code on server and restart services

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
SERVICE_PREFIX="ytd"

echo ""
echo "============================================================"
echo "  Deploying Code Update"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo bash deploy-update.sh"
fi

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    error "App directory $APP_DIR does not exist. Run start-dev.sh first."
fi

info "Stopping services..."
systemctl stop "${SERVICE_PREFIX}-api" "${SERVICE_PREFIX}-worker" "${SERVICE_PREFIX}-beat"
log "Services stopped"

info "Updating application code..."
# Copy updated Python files (preserving existing .env, downloads, logs)
cd "$(dirname "${BASH_SOURCE[0]}")"
rsync -av --exclude='.venv' --exclude='downloads' --exclude='logs' --exclude='.env.production' \
    ./app/ "$APP_DIR/app/"
log "Code updated"

info "Fixing permissions..."
chown -R ytd:ytd "$APP_DIR/app"
log "Permissions fixed"

info "Starting services..."
systemctl start "${SERVICE_PREFIX}-api" "${SERVICE_PREFIX}-worker" "${SERVICE_PREFIX}-beat"

sleep 3

# Check service status
systemctl is-active --quiet "${SERVICE_PREFIX}-api"    && log "API server is running"    || warn "API server failed - check: sudo journalctl -u ${SERVICE_PREFIX}-api -n 50"
systemctl is-active --quiet "${SERVICE_PREFIX}-worker" && log "Celery worker is running" || warn "Celery worker failed - check: sudo journalctl -u ${SERVICE_PREFIX}-worker -n 50"
systemctl is-active --quiet "${SERVICE_PREFIX}-beat"   && log "Celery beat is running"   || warn "Celery beat failed - check: sudo journalctl -u ${SERVICE_PREFIX}-beat -n 50"

echo ""
echo "============================================================"
echo -e "${GREEN}  Code deployment complete!${NC}"
echo "============================================================"
echo ""
echo "  Monitor logs:"
echo "    sudo journalctl -u ${SERVICE_PREFIX}-worker -f"
echo "    sudo journalctl -u ${SERVICE_PREFIX}-api -f"
echo ""
