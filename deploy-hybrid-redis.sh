#!/bin/bash

# ===================================================================
# Hybrid Redis Deployment Script
# ===================================================================
# This script pulls the latest code and deploys the hybrid Redis
# configuration on a server.
#
# Usage:
#   Server 1: sudo bash deploy-hybrid-redis.sh 1
#   Server 2: sudo bash deploy-hybrid-redis.sh 2
#   Server 3: sudo bash deploy-hybrid-redis.sh 3
# ===================================================================

set -e  # Exit on error

# Check if server number is provided
if [ -z "$1" ]; then
    echo "ERROR: Server number required"
    echo "Usage: sudo bash deploy-hybrid-redis.sh [1|2|3]"
    echo "  1 = ytd.timobosafaris.com (Account A)"
    echo "  2 = GCP 34.57.68.120 (Account B)"
    echo "  3 = AWS 13.60.71.187 (Account C)"
    exit 1
fi

SERVER_NUM=$1

# Validate server number
if [[ ! "$SERVER_NUM" =~ ^[1-3]$ ]]; then
    echo "ERROR: Invalid server number. Must be 1, 2, or 3"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (use sudo)"
    exit 1
fi

echo "============================================"
echo "Deploying Hybrid Redis to Server $SERVER_NUM"
echo "============================================"

# Step 1: Pull latest code from main repo
echo ""
echo "[1/8] Pulling latest code from main repository..."
cd /opt/ytdl
git fetch origin
git pull origin master

# Step 2: Pull latest code from backend-python submodule
echo ""
echo "[2/8] Updating backend-python submodule..."
cd /opt/ytdl/backend-python
git fetch origin
git pull origin main

# Step 3: Pull latest code from frontend submodule (optional)
echo ""
echo "[3/8] Updating frontend submodule..."
cd /opt/ytdl/frontend
git fetch origin
git pull origin main || echo "⚠️  Frontend pull skipped (no changes or errors)"

# Step 4: Install local Redis if not already installed
echo ""
echo "[4/8] Checking Redis installation..."
if ! command -v redis-server &> /dev/null; then
    echo "Redis not found. Installing local Redis..."
    cd /opt/ytdl
    bash install-local-redis.sh
else
    echo "✅ Redis already installed"
    # Verify Redis is running
    if ! redis-cli ping &> /dev/null; then
        echo "Starting Redis..."
        systemctl start redis-server
        sleep 2
    fi
    echo "✅ Redis is running"
fi

# Step 5: Deploy backend .env configuration
echo ""
echo "[5/8] Deploying backend configuration..."
cd /opt/ytdl/backend-python

# Backup existing .env if it exists
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backed up existing .env"
fi

# Copy server-specific config
cp .env.production.server${SERVER_NUM} .env
chown ytdl:ytdl .env
chmod 600 .env
echo "✅ Deployed .env.production.server${SERVER_NUM} to .env"

# Step 6: Deploy cookie extractor .env configuration
echo ""
echo "[6/8] Deploying cookie extractor configuration..."
cd /opt/ytdl/cookie-extractor

# Backup existing .env if it exists
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backed up existing .env"
fi

# Copy server-specific config
cp .env.production.server${SERVER_NUM} .env
chown ytdl:ytdl .env
chmod 600 .env
echo "✅ Deployed .env.production.server${SERVER_NUM} to .env"

# Step 7: Restart backend services
echo ""
echo "[7/8] Restarting backend services..."
systemctl restart ytd-api
systemctl restart ytd-worker
systemctl restart ytd-beat
echo "✅ Restarted ytd-api, ytd-worker, ytd-beat"

# Wait for services to start
sleep 3

# Check service status
echo ""
echo "Service Status:"
echo "----------------------------------------"
systemctl is-active ytd-api && echo "✅ ytd-api: RUNNING" || echo "❌ ytd-api: FAILED"
systemctl is-active ytd-worker && echo "✅ ytd-worker: RUNNING" || echo "❌ ytd-worker: FAILED"
systemctl is-active ytd-beat && echo "✅ ytd-beat: RUNNING" || echo "❌ ytd-beat: FAILED"
echo "----------------------------------------"

# Step 8: Restart cookie extractor (if exists)
echo ""
echo "[8/8] Restarting cookie extractor..."
if systemctl list-units --full -all | grep -q ytd-cookie-extractor; then
    systemctl restart ytd-cookie-extractor
    sleep 2
    systemctl is-active ytd-cookie-extractor && echo "✅ ytd-cookie-extractor: RUNNING" || echo "❌ ytd-cookie-extractor: FAILED"
else
    echo "⚠️  ytd-cookie-extractor service not found (may need manual setup)"
fi

# Verification
echo ""
echo "============================================"
echo "Deployment Verification"
echo "============================================"

# Check local Redis
echo ""
echo "[TEST 1] Local Redis connection:"
if redis-cli ping &> /dev/null; then
    echo "✅ Local Redis responding"
    redis-cli INFO server | grep redis_version
    redis-cli INFO clients | grep connected_clients
else
    echo "❌ Local Redis NOT responding"
fi

# Check backend health
echo ""
echo "[TEST 2] Backend health check:"
sleep 2
if curl -s http://localhost:3001/api/health/ | grep -q "status"; then
    echo "✅ Backend API responding"
    curl -s http://localhost:3001/api/health/ | head -3
else
    echo "❌ Backend API NOT responding"
fi

# Check for errors in logs
echo ""
echo "[TEST 3] Recent error check (last 5 minutes):"
ERROR_COUNT=$(journalctl -u ytd-worker --since "5 minutes ago" | grep -i "error\|timeout" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "✅ No errors found in worker logs"
else
    echo "⚠️  Found $ERROR_COUNT errors/timeouts in worker logs"
    echo "Run: sudo journalctl -u ytd-worker --since '5 minutes ago' | grep -i error"
fi

# Display account configuration
echo ""
echo "============================================"
echo "Server Configuration"
echo "============================================"
case $SERVER_NUM in
    1)
        echo "Server: ytd.timobosafaris.com"
        echo "Account: A (otienog1@yahoo.com)"
        echo "Cookies: /opt/ytdl/youtube_cookies_account_a.txt"
        ;;
    2)
        echo "Server: GCP 34.57.68.120"
        echo "Account: B (otienog1@icluod.com)"
        echo "Cookies: /opt/ytdl/youtube_cookies_account_b.txt"
        ;;
    3)
        echo "Server: AWS 13.60.71.187"
        echo "Account: C (7plus8studios@gmail.com)"
        echo "Cookies: /opt/ytdl/youtube_cookies_account_c.txt"
        ;;
esac

echo ""
echo "Redis Configuration:"
echo "  Local Redis: 127.0.0.1:6379 (Celery)"
echo "  Shared Redis: 57.159.27.119:6379 (Bull queue)"

echo ""
echo "============================================"
echo "✅ Deployment Complete!"
echo "============================================"
echo ""
echo "Next Steps:"
echo "1. Monitor logs for any errors:"
echo "   sudo journalctl -u ytd-worker -f"
echo ""
echo "2. Test a download from the frontend"
echo ""
echo "3. Verify no timeout errors occur"
echo ""
echo "If issues occur, check logs:"
echo "  Backend API:  sudo journalctl -u ytd-api -n 100"
echo "  Worker:       sudo journalctl -u ytd-worker -n 100"
echo "  Beat:         sudo journalctl -u ytd-beat -n 100"
echo "  Cookies:      sudo journalctl -u ytd-cookie-extractor -n 100"
echo ""
