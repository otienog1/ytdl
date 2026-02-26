#!/bin/bash
# YouTube Downloader - Deployment Script (Bash)
# Deploys code from GitHub to production servers

set -e

# ===================================================================
# LOAD SERVER CONFIGURATION
# ===================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/deploy-config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "[ERROR] Configuration file not found: $CONFIG_FILE"
    echo ""
    echo "Please create deploy-config.json with your server details"
    echo ""
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "[ERROR] jq is required but not installed."
    echo "Install it with: sudo apt-get install jq (Debian/Ubuntu) or brew install jq (macOS)"
    exit 1
fi

DEPLOY_PATH="/opt/ytdl"
BRANCH="main"

# ===================================================================
# FUNCTIONS
# ===================================================================

log()   { echo -e "\033[0;32m[OK]\033[0m $1"; }
info()  { echo -e "\033[0;34m[INFO]\033[0m $1"; }
error() { echo -e "\033[0;31m[ERROR]\033[0m $1"; }

print_header() {
    echo ""
    echo "========================================="
    echo "  $1"
    echo "========================================="
    echo ""
}

print_server_header() {
    echo ""
    echo ">>> Deploying to $1..."
}

# Function to execute SSH command
ssh_exec() {
    local host=$1
    local command=$2
    local ssh_key=$3

    if [ -n "$ssh_key" ] && [ -f "$ssh_key" ]; then
        ssh -o StrictHostKeyChecking=no -i "$ssh_key" "$host" "$command"
    else
        ssh -o StrictHostKeyChecking=no "$host" "$command"
    fi
}

# ===================================================================
# MAIN DEPLOYMENT
# ===================================================================

print_header "YouTube Downloader - Deployment Script"

# Read number of servers
server_count=$(jq '.servers | length' "$CONFIG_FILE")

failed_servers=()

for ((i=0; i<server_count; i++)); do
    # Extract server details
    host=$(jq -r ".servers[$i].host" "$CONFIG_FILE")
    name=$(jq -r ".servers[$i].name" "$CONFIG_FILE")
    ssh_key=$(jq -r ".servers[$i].sshKey // empty" "$CONFIG_FILE")

    # Expand environment variables in SSH key path
    if [ -n "$ssh_key" ]; then
        ssh_key=$(eval echo "$ssh_key")
    fi

    print_server_header "$name"

    # Build the deployment commands
    deploy_commands="
set -e

echo '  [1/6] Navigating to deployment directory...'
cd $DEPLOY_PATH

echo '  [2/6] Pulling latest code from GitHub...'
git fetch origin
git reset --hard origin/$BRANCH

echo '  [3/6] Fixing ownership...'
chown -R ytd:ytd $DEPLOY_PATH

echo '  [4/6] Installing/updating dependencies...'
sudo -u ytd $DEPLOY_PATH/.venv/bin/pip install -r requirements.txt --quiet

echo '  [5/6] Restarting services...'
systemctl restart ytd-api ytd-worker

echo '  [6/6] Checking service status...'
sleep 3
if systemctl is-active --quiet ytd-api && systemctl is-active --quiet ytd-worker; then
    echo '  Services running successfully'
else
    echo '  ERROR: Services failed to start'
    systemctl status ytd-api ytd-worker --no-pager
    exit 1
fi
"

    info "  Executing deployment commands..."

    if ssh_exec "$host" "$deploy_commands" "$ssh_key"; then
        log "  Deployment to $name completed successfully"
    else
        error "  Deployment to $name FAILED"
        failed_servers+=("$name")
    fi

    echo ""
done

# ===================================================================
# SUMMARY
# ===================================================================

print_header "Deployment Summary"

if [ ${#failed_servers[@]} -eq 0 ]; then
    log "All servers deployed successfully!"
    exit 0
else
    error "Deployment failed on: ${failed_servers[*]}"
    exit 1
fi
