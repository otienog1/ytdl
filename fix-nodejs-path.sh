#!/bin/bash
# Fix Node.js PATH for yt-dlp JavaScript runtime

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✓]${NC} $1"; }
info()  { echo -e "${BLUE}[→]${NC} $1"; }

echo ""
echo "============================================================"
echo "  Fixing Node.js PATH for yt-dlp"
echo "============================================================"
echo ""

# Find Node.js location
NODE_PATH=$(which node 2>/dev/null || echo "")

if [ -z "$NODE_PATH" ]; then
    echo "ERROR: Node.js not found. Installing..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
    NODE_PATH=$(which node)
fi

NODE_DIR=$(dirname "$NODE_PATH")
log "Node.js found at: $NODE_PATH"
log "Node.js directory: $NODE_DIR"

# Update systemd services to include Node.js path
info "Updating systemd services..."

for service in /etc/systemd/system/ytd-*.service; do
    if grep -q "Environment=\"PATH=" "$service"; then
        # Check if Node.js path is already there
        if ! grep -q "$NODE_DIR" "$service"; then
            info "Updating $service..."
            sed -i "s|Environment=\"PATH=\([^\"]*\)\"|Environment=\"PATH=\1:$NODE_DIR\"|g" "$service"
            log "Updated $service"
        else
            log "$service already has Node.js in PATH"
        fi
    fi
done

# Reload and restart
info "Reloading systemd..."
systemctl daemon-reload

info "Restarting services..."
systemctl restart ytd-worker ytd-api ytd-beat

sleep 2

systemctl is-active --quiet ytd-api    && log "API server is running" || echo "API server failed"
systemctl is-active --quiet ytd-worker && log "Celery worker is running" || echo "Celery worker failed"
systemctl is-active --quiet ytd-beat   && log "Celery beat is running" || echo "Celery beat failed"

echo ""
echo "============================================================"
echo -e "${GREEN}  Node.js PATH fixed!${NC}"
echo "============================================================"
echo ""
echo "Test with:"
echo "  sudo journalctl -u ytd-worker -f"
echo ""
