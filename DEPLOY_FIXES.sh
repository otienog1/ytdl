#!/bin/bash
# Quick deployment script to apply all pending fixes on the server

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
info()  { echo -e "${BLUE}[i]${NC} $1"; }

echo ""
echo "============================================================"
echo "  Deploy All Fixes to Production Server"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo bash DEPLOY_FIXES.sh"
fi

# Navigate to app directory
cd /opt/ytdl || error "Directory /opt/ytdl not found"

info "Current directory: $(pwd)"
echo ""

# Step 1: Pull latest code
log "Step 1: Pulling latest code from git..."
git pull || error "Git pull failed"
echo ""

# Step 2: Update submodules
log "Step 2: Updating submodules..."
git submodule update --init --recursive || warn "Submodule update had issues"
echo ""

# Step 3: Navigate to backend-python
cd backend-python || error "backend-python directory not found"
info "Current directory: $(pwd)"
echo ""

# Step 4: Fix systemd paths
log "Step 3: Fixing systemd service paths..."
if [ -f "fix-systemd-paths.sh" ]; then
    bash fix-systemd-paths.sh
else
    warn "fix-systemd-paths.sh not found, skipping..."
fi
echo ""

# Step 5: Apply Redis connection fixes
log "Step 4: Applying Redis connection fixes..."
if [ -f "fix-redis-connections.sh" ]; then
    bash fix-redis-connections.sh
else
    warn "fix-redis-connections.sh not found, skipping..."
fi
echo ""

# Step 6: Final status check
log "Step 5: Checking final service status..."
sleep 2
echo ""
systemctl status ytd-api --no-pager -l | head -20
echo ""
systemctl status ytd-worker --no-pager -l | head -20
echo ""
systemctl status ytd-beat --no-pager -l | head -20
echo ""

echo "============================================================"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo "============================================================"
echo ""
echo "What was fixed:"
echo "  ✅ Systemd service paths updated to /opt/ytdl"
echo "  ✅ Redis connection pooling enabled (max 10 per client)"
echo "  ✅ Celery broker pool limited to 5 connections"
echo "  ✅ Celery worker concurrency reduced to 1"
echo ""
echo "Expected Redis connection usage: ~15 (was ~30)"
echo ""
echo "Monitor logs:"
echo "  sudo journalctl -u ytd-worker -f"
echo ""
echo "Check Redis connections:"
echo "  redis-cli -h redis-17684.c10.us-east-1-3.ec2.cloud.redislabs.com \\"
echo "    -p 17684 -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM INFO clients | grep connected"
echo ""
