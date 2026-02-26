#!/bin/bash
# ===================================================================
# Fix Git Divergent Branches on Server
# ===================================================================
# This script fixes the "divergent branches" issue on the server
# by doing a hard reset to match the remote main branch
# ===================================================================

echo "========================================================================"
echo "Fixing Git Divergent Branches on ytd.timobosafaris.com"
echo "========================================================================"
echo ""

ssh root@ytd.timobosafaris.com << 'ENDSSH'
cd /opt/ytdl

echo "[1/4] Fetching latest from origin..."
git fetch origin

echo ""
echo "[2/4] Checking current branch..."
git branch -v

echo ""
echo "[3/4] Hard reset to origin/main (discarding local changes)..."
git reset --hard origin/main

echo ""
echo "[4/4] Verifying..."
git log -1 --oneline

echo ""
echo "✅ Server git is now synced with GitHub"
ENDSSH

echo ""
echo "========================================================================"
echo "Now you can run: bash deploy-from-local.sh"
echo "========================================================================"
