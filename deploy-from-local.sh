#!/bin/bash

# ===================================================================
# Deploy Hybrid Redis from Local Machine to All Servers
# ===================================================================
# This script runs on your LOCAL machine (Windows/WSL or Linux)
# and deploys the hybrid Redis configuration to all 3 servers via SSH
#
# Requirements:
#   - SSH access to all servers (key-based auth recommended)
#   - Git repositories cloned locally
#
# Usage: bash deploy-from-local.sh
# ===================================================================

set -e  # Exit on error

# ===================================================================
# SERVER CONFIGURATION
# ===================================================================
declare -A SERVERS=(
    [1]="root@ytd.timobosafaris.com"
    [2]="root@34.57.68.120"
    [3]="root@13.60.71.187"
)

declare -A ACCOUNTS=(
    [1]="Account A (otienog1@yahoo.com)"
    [2]="Account B (otienog1@icluod.com)"
    [3]="Account C (7plus8studios@gmail.com)"
)

declare -A SERVER_NAMES=(
    [1]="ytd.timobosafaris.com"
    [2]="GCP 34.57.68.120"
    [3]="AWS 13.60.71.187"
)

# ===================================================================
# FUNCTIONS
# ===================================================================

deploy_to_server() {
    local server_num=$1
    local ssh_host="${SERVERS[$server_num]}"
    local account="${ACCOUNTS[$server_num]}"
    local server_name="${SERVER_NAMES[$server_num]}"

    echo ""
    echo "========================================================================"
    echo "Deploying to Server $server_num: $server_name"
    echo "Account: $account"
    echo "========================================================================"

    # Test SSH connection
    echo ""
    echo "[1/9] Testing SSH connection..."
    if ! ssh -o ConnectTimeout=10 "$ssh_host" "echo 'SSH connection successful'"; then
        echo "❌ ERROR: Cannot connect to $ssh_host"
        return 1
    fi
    echo "✅ SSH connection successful"

    # Pull main repository
    echo ""
    echo "[2/9] Pulling main repository on server..."
    ssh "$ssh_host" "cd /opt/ytdl && git fetch origin && git pull origin master"
    echo "✅ Main repository updated"

    # Pull backend-python submodule
    echo ""
    echo "[3/9] Pulling backend-python submodule..."
    ssh "$ssh_host" "cd /opt/ytdl/backend-python && git fetch origin && git pull origin main"
    echo "✅ Backend-python updated"

    # Check if local Redis is installed, if not install it
    echo ""
    echo "[4/9] Checking Redis installation..."
    if ! ssh "$ssh_host" "command -v redis-server &> /dev/null"; then
        echo "Redis not found. Installing..."
        ssh "$ssh_host" "cd /opt/ytdl && bash install-local-redis.sh"
    else
        echo "✅ Redis already installed"
        # Make sure it's running
        ssh "$ssh_host" "systemctl is-active redis-server || systemctl start redis-server"
    fi

    # Deploy backend .env.production configuration
    echo ""
    echo "[5/9] Deploying backend configuration..."
    ssh "$ssh_host" "cd /opt/ytdl/backend-python && \
        if [ -f .env.production ]; then cp .env.production .env.production.backup.\$(date +%Y%m%d_%H%M%S); fi && \
        cp .env.production.server${server_num} .env.production && \
        chown ytdl:ytdl .env.production && \
        chmod 600 .env.production"
    echo "✅ Backend .env.production deployed"

    # Deploy cookie extractor .env.production configuration
    echo ""
    echo "[6/9] Deploying cookie extractor configuration..."
    ssh "$ssh_host" "cd /opt/ytdl/cookie-extractor && \
        if [ -f .env.production ]; then cp .env.production .env.production.backup.\$(date +%Y%m%d_%H%M%S); fi && \
        cp .env.production.server${server_num} .env.production && \
        chown ytdl:ytdl .env.production && \
        chmod 600 .env.production"
    echo "✅ Cookie extractor .env.production deployed"

    # Restart backend services
    echo ""
    echo "[7/9] Restarting backend services..."
    ssh "$ssh_host" "systemctl restart ytd-api ytd-worker ytd-beat"
    sleep 3
    echo "✅ Backend services restarted"

    # Restart cookie extractor
    echo ""
    echo "[8/9] Restarting cookie extractor..."
    if ssh "$ssh_host" "systemctl list-units --full -all | grep -q ytd-cookie-extractor"; then
        ssh "$ssh_host" "systemctl restart ytd-cookie-extractor"
        echo "✅ Cookie extractor restarted"
    else
        echo "⚠️  Cookie extractor service not found"
    fi

    # Verification
    echo ""
    echo "[9/9] Running verification tests..."

    # Check local Redis
    if ssh "$ssh_host" "redis-cli ping &> /dev/null"; then
        echo "✅ Local Redis responding"
    else
        echo "❌ Local Redis NOT responding"
    fi

    # Check backend health
    sleep 2
    if ssh "$ssh_host" "curl -s http://localhost:3001/api/health/ | grep -q status"; then
        echo "✅ Backend API healthy"
    else
        echo "❌ Backend API NOT responding"
    fi

    # Check for errors
    ERROR_COUNT=$(ssh "$ssh_host" "journalctl -u ytd-worker --since '5 minutes ago' | grep -i 'error\|timeout' | wc -l")
    if [ "$ERROR_COUNT" -eq 0 ]; then
        echo "✅ No errors in worker logs"
    else
        echo "⚠️  Found $ERROR_COUNT errors/timeouts in logs"
    fi

    # Check service status
    echo ""
    echo "Service Status:"
    ssh "$ssh_host" "systemctl is-active ytd-api && echo '  ✅ ytd-api' || echo '  ❌ ytd-api'"
    ssh "$ssh_host" "systemctl is-active ytd-worker && echo '  ✅ ytd-worker' || echo '  ❌ ytd-worker'"
    ssh "$ssh_host" "systemctl is-active ytd-beat && echo '  ✅ ytd-beat' || echo '  ❌ ytd-beat'"

    echo ""
    echo "✅ Server $server_num deployment complete!"
    echo "========================================================================"
}

# ===================================================================
# MAIN SCRIPT
# ===================================================================

echo "========================================================================"
echo "Hybrid Redis Multi-Server Deployment"
echo "========================================================================"
echo ""
echo "This script will deploy hybrid Redis configuration to:"
echo "  Server 1: ${SERVER_NAMES[1]} - ${ACCOUNTS[1]}"
echo "  Server 2: ${SERVER_NAMES[2]} - ${ACCOUNTS[2]}"
echo "  Server 3: ${SERVER_NAMES[3]} - ${ACCOUNTS[3]}"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Track deployment results
SUCCESSFUL_DEPLOYMENTS=()
FAILED_DEPLOYMENTS=()

# Deploy to each server
for server_num in 1 2 3; do
    if deploy_to_server $server_num; then
        SUCCESSFUL_DEPLOYMENTS+=($server_num)
    else
        FAILED_DEPLOYMENTS+=($server_num)
        echo ""
        echo "❌ Failed to deploy to Server $server_num"
        echo "Continue with remaining servers? (y/n)"
        read -p "" -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            break
        fi
    fi
done

# Summary
echo ""
echo "========================================================================"
echo "DEPLOYMENT SUMMARY"
echo "========================================================================"
echo ""

if [ ${#SUCCESSFUL_DEPLOYMENTS[@]} -gt 0 ]; then
    echo "✅ Successful Deployments (${#SUCCESSFUL_DEPLOYMENTS[@]}):"
    for server_num in "${SUCCESSFUL_DEPLOYMENTS[@]}"; do
        echo "   Server $server_num: ${SERVER_NAMES[$server_num]}"
    done
fi

if [ ${#FAILED_DEPLOYMENTS[@]} -gt 0 ]; then
    echo ""
    echo "❌ Failed Deployments (${#FAILED_DEPLOYMENTS[@]}):"
    for server_num in "${FAILED_DEPLOYMENTS[@]}"; do
        echo "   Server $server_num: ${SERVER_NAMES[$server_num]}"
    done
fi

echo ""
echo "========================================================================"

if [ ${#SUCCESSFUL_DEPLOYMENTS[@]} -eq 3 ]; then
    echo "🎉 All servers deployed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Monitor logs on each server for errors"
    echo "2. Test downloads from the frontend"
    echo "3. Verify no timeout errors occur"
    echo ""
    echo "Monitor commands:"
    echo "  ssh ${SERVERS[1]} 'journalctl -u ytd-worker -f'"
    echo "  ssh ${SERVERS[2]} 'journalctl -u ytd-worker -f'"
    echo "  ssh ${SERVERS[3]} 'journalctl -u ytd-worker -f'"
else
    echo "⚠️  Deployment completed with errors"
    echo ""
    echo "Check failed servers manually:"
    for server_num in "${FAILED_DEPLOYMENTS[@]}"; do
        echo "  ssh ${SERVERS[$server_num]}"
    done
fi

echo "========================================================================"
