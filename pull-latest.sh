#!/bin/bash

# ===================================================================
# Pull Latest Code from Git
# ===================================================================
# This script pulls the latest code from all repositories
#
# Usage: sudo bash pull-latest.sh
# ===================================================================

set -e  # Exit on error

echo "============================================"
echo "Pulling Latest Code from Git"
echo "============================================"

# Step 1: Pull main repository
echo ""
echo "[1/3] Pulling main repository..."
cd /opt/ytdl
git fetch origin
git pull origin master
echo "✅ Main repository updated"

# Step 2: Pull backend-python submodule
echo ""
echo "[2/3] Pulling backend-python submodule..."
cd /opt/ytdl/backend-python
git fetch origin
git pull origin main
echo "✅ Backend-python updated"

# Step 3: Pull frontend submodule
echo ""
echo "[3/3] Pulling frontend submodule..."
cd /opt/ytdl/frontend
git fetch origin
git pull origin main || echo "⚠️  Frontend update skipped (may not exist or no changes)"
echo "✅ Frontend updated"

echo ""
echo "============================================"
echo "✅ All repositories updated!"
echo "============================================"
echo ""
echo "Latest commits:"
echo "----------------------------------------"
echo "Main repo:"
cd /opt/ytdl
git log -1 --oneline

echo ""
echo "Backend-python:"
cd /opt/ytdl/backend-python
git log -1 --oneline

echo ""
echo "Frontend:"
cd /opt/ytdl/frontend
git log -1 --oneline || echo "(no changes)"

echo ""
echo "----------------------------------------"
echo ""
echo "Next steps:"
echo "1. Deploy hybrid Redis (if not done yet):"
echo "   sudo bash deploy-hybrid-redis.sh [1|2|3]"
echo ""
echo "2. Or manually restart services:"
echo "   sudo systemctl restart ytd-api ytd-worker ytd-beat"
echo ""
