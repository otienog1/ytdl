#!/bin/bash
# Fix systemd service paths from /home/admin/ytdl to /opt/ytdl

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "============================================================"
echo "  Fix Systemd Service Paths"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo bash fix-systemd-paths.sh"
fi

# Update all ytd service files to use /opt/ytdl
log "Updating systemd service paths..."

for service in /etc/systemd/system/ytd-*.service; do
    if [ -f "$service" ]; then
        log "Updating $(basename $service)..."
        sed -i 's|WorkingDirectory=/home/admin/ytdl|WorkingDirectory=/opt/ytdl|g' "$service"
        sed -i 's|/home/admin/ytdl/.venv|/opt/ytdl/.venv|g' "$service"
        sed -i 's|EnvironmentFile=/home/admin/ytdl/.env.production|EnvironmentFile=/opt/ytdl/.env.production|g' "$service"
    fi
done

# Reload systemd
log "Reloading systemd daemon..."
systemctl daemon-reload

# Restart all ytd services
log "Restarting services..."
systemctl restart ytd-api ytd-worker ytd-beat

sleep 3

# Check service status
echo ""
log "Service Status:"
systemctl is-active --quiet ytd-api    && log "  API server is running"    || warn "  API server failed - check: sudo journalctl -u ytd-api -n 50"
systemctl is-active --quiet ytd-worker && log "  Celery worker is running" || warn "  Celery worker failed - check: sudo journalctl -u ytd-worker -n 50"
systemctl is-active --quiet ytd-beat   && log "  Celery beat is running"   || warn "  Celery beat failed - check: sudo journalctl -u ytd-beat -n 50"

echo ""
echo "============================================================"
echo -e "${GREEN}  Systemd paths fixed!${NC}"
echo "============================================================"
echo ""
echo "All services now use: /opt/ytdl"
echo ""
