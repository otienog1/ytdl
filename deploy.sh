#!/bin/bash
# Deployment script for YouTube Downloader Backend
# Deploys code from GitHub to production servers

set -e  # Exit on error

# Server configurations
SERVERS=(
    "ytd.timobosafaris.com"
    "35.193.12.77"
    "13.60.71.187"
)

SERVER_NAMES=(
    "Linode"
    "GCP"
    "AWS"
)

DEPLOY_PATH="/opt/ytdl"
REPO_URL="https://github.com/otienog1/ytdl.git"
BRANCH="main"

echo "========================================="
echo "YouTube Downloader - Deployment Script"
echo "========================================="
echo ""

# Function to deploy to a single server
deploy_to_server() {
    local server=$1
    local server_name=$2

    echo ">>> Deploying to $server_name ($server)..."

    ssh root@$server << 'ENDSSH'
set -e

echo "  [1/6] Navigating to deployment directory..."
cd /opt/ytdl

echo "  [2/6] Pulling latest code from GitHub..."
git fetch origin
git reset --hard origin/main

echo "  [3/6] Fixing ownership..."
chown -R ytd:ytd /opt/ytdl

echo "  [4/6] Installing/updating dependencies..."
sudo -u ytd /opt/ytdl/.venv/bin/pip install -r requirements.txt --quiet

echo "  [5/6] Restarting services..."
systemctl restart ytd-api ytd-worker

echo "  [6/6] Checking service status..."
sleep 3
if systemctl is-active --quiet ytd-api && systemctl is-active --quiet ytd-worker; then
    echo "  ✓ Services running successfully"
else
    echo "  ✗ ERROR: Services failed to start"
    systemctl status ytd-api ytd-worker --no-pager
    exit 1
fi

ENDSSH

    if [ $? -eq 0 ]; then
        echo "  ✓ Deployment to $server_name completed successfully"
    else
        echo "  ✗ Deployment to $server_name FAILED"
        return 1
    fi
    echo ""
}

# Deploy to all servers
failed_servers=()

for i in "${!SERVERS[@]}"; do
    if ! deploy_to_server "${SERVERS[$i]}" "${SERVER_NAMES[$i]}"; then
        failed_servers+=("${SERVER_NAMES[$i]}")
    fi
done

# Summary
echo "========================================="
echo "Deployment Summary"
echo "========================================="

if [ ${#failed_servers[@]} -eq 0 ]; then
    echo "✓ All servers deployed successfully!"
    exit 0
else
    echo "✗ Deployment failed on: ${failed_servers[*]}"
    exit 1
fi
