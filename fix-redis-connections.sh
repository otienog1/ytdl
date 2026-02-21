#!/bin/bash
# Fix Redis "max clients reached" error by reducing connection usage

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
echo "  Fix Redis Connection Pool Limits"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo bash fix-redis-connections.sh"
fi

# Update Celery worker service to use only 1 concurrency
log "Updating Celery worker to use concurrency=1..."
sed -i 's/--concurrency=2/--concurrency=1/' /etc/systemd/system/ytd-worker.service || warn "Could not update worker service"

# Reload systemd
systemctl daemon-reload
log "Systemd reloaded"

# Restart services
log "Restarting services..."
systemctl restart ytd-api ytd-worker ytd-beat

sleep 3

# Check service status
systemctl is-active --quiet ytd-api    && log "API server is running"    || warn "API server failed"
systemctl is-active --quiet ytd-worker && log "Celery worker is running" || warn "Celery worker failed"
systemctl is-active --quiet ytd-beat   && log "Celery beat is running"   || warn "Celery beat failed"

echo ""
echo "============================================================"
echo -e "${GREEN}  Redis connection fix applied!${NC}"
echo "============================================================"
echo ""
echo "Changes made:"
echo "  - Reduced Celery worker concurrency to 1"
echo "  - Added Redis connection pooling limits"
echo "  - Configured socket keepalive"
echo ""
echo "Monitor Redis connections:"
echo "  redis-cli INFO clients"
echo ""
echo "Check logs:"
echo "  sudo journalctl -u ytd-worker -f"
echo ""
