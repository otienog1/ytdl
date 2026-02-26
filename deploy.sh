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

# Parse JSON using Python (more portable than jq)
servers_json=$(python3 -c "
import json, sys, os
from pathlib import Path

# Handle both Windows and Unix paths
config_path = Path('$CONFIG_FILE')
if not config_path.exists():
    # Try with forward slashes for Git Bash on Windows
    config_path = Path('$CONFIG_FILE'.replace('/c/', 'C:/'))

with open(config_path) as f:
    config = json.load(f)
    for server in config['servers']:
        ssh_key = server.get('sshKey', '')
        if ssh_key:
            ssh_key = os.path.expandvars(ssh_key)
        print(f\"{server['host']}|{server['name']}|{ssh_key}\")
")

failed_servers=()

while IFS='|' read -r host name ssh_key; do

    print_server_header "$name"

    # Build the deployment commands
    deploy_commands="
set -e

# Set non-interactive mode for apt-get
export DEBIAN_FRONTEND=noninteractive

# Detect if running as root
if [ \"\$(id -u)\" = \"0\" ]; then
    SUDO=\"\"
else
    SUDO=\"sudo\"
fi

echo '  [1/10] Checking Python version...'
PYTHON_VERSION=\$(python3 --version 2>&1 | grep -oP '3\.\d+' || echo '0.0')
REQUIRED_VERSION='3.13'

if [ \"\$(printf '%s\n' \"\$REQUIRED_VERSION\" \"\$PYTHON_VERSION\" | sort -V | head -n1)\" != \"\$REQUIRED_VERSION\" ]; then
    echo '  Python version is \$PYTHON_VERSION, upgrading to 3.13...'

    # Update package list
    apt-get update -qq

    # Install software-properties-common for add-apt-repository
    apt-get install -y software-properties-common -qq

    # Add deadsnakes PPA for Python 3.13
    add-apt-repository -y ppa:deadsnakes/ppa
    apt-get update -qq

    # Install Python 3.13 and required packages
    apt-get install -y python3.13 python3.13-venv python3.13-dev python-is-python3 -qq

    # Update alternatives to make python3.13 the default python3
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1
    update-alternatives --set python3 /usr/bin/python3.13

    echo '  Python upgraded to 3.13'
else
    echo '  Python version \$PYTHON_VERSION is compatible'

    # Ensure python-is-python3 is installed
    if ! dpkg -l | grep -q python-is-python3; then
        echo '  Installing python-is-python3 package...'
        apt-get update -qq
        apt-get install -y python-is-python3 -qq
    fi
fi

echo '  [2/10] Navigating to deployment directory...'
cd $DEPLOY_PATH

echo '  [3/10] Configuring git safe directory...'
\$SUDO -u ytd git config --global --add safe.directory $DEPLOY_PATH

echo '  [4/10] Pulling latest code from GitHub...'
\$SUDO -u ytd git fetch origin
\$SUDO -u ytd git reset --hard origin/$BRANCH

echo '  [5/10] Fixing ownership and permissions...'
\$SUDO chown -R ytd:ytd $DEPLOY_PATH
\$SUDO chmod -R u+rwX,go+rX $DEPLOY_PATH

echo '  [6/10] Recreating virtual environment with Python 3.13...'
rm -rf $DEPLOY_PATH/.venv
\$SUDO -u ytd python3.13 -m venv $DEPLOY_PATH/.venv

echo '  [7/10] Upgrading pip...'
\$SUDO -u ytd $DEPLOY_PATH/.venv/bin/pip install --upgrade pip --quiet

echo '  [8/10] Installing/updating dependencies...'
\$SUDO -u ytd $DEPLOY_PATH/.venv/bin/pip install -r requirements.txt --quiet

echo '  [9/10] Restarting services...'
systemctl restart ytd-api ytd-worker ytd-beat

echo '  [10/10] Checking service status...'
sleep 3
if systemctl is-active --quiet ytd-api && systemctl is-active --quiet ytd-worker && systemctl is-active --quiet ytd-beat; then
    echo '  Services running successfully'
else
    echo '  ERROR: Services failed to start'
    systemctl status ytd-api ytd-worker ytd-beat --no-pager
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
done <<< "$servers_json"

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
