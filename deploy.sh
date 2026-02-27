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
GCP_CREDENTIALS_FILE="$SCRIPT_DIR/divine-actor-473706-k4-fdec9ee56ba0.json"

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

    if [ -n "$ssh_key" ]; then
        echo "$command" | ssh -o StrictHostKeyChecking=no \
            -o IdentitiesOnly=yes \
            -i "$ssh_key" \
            "$host" "bash -s"
    else
        echo "$command" | ssh -o StrictHostKeyChecking=no \
            "$host" "bash -s"
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

import re

with open(config_path) as f:
    config = json.load(f)
    for server in config['servers']:
        ssh_key = server.get('sshKey', '') or ''
        if ssh_key:
            ssh_key = os.path.expandvars(ssh_key)
            # Convert Windows path to Git Bash format: C:\\path -> /c/path
            # First convert backslashes to forward slashes
            ssh_key = ssh_key.replace(chr(92), '/')
            # Then convert drive letter: C:/ -> /c/
            match = re.match(r'^([A-Za-z]):/(.*)', ssh_key)
            if match:
                drive = match.group(1).lower()
                path = match.group(2)
                ssh_key = f'/{drive}/{path}'
        print(f\"{server['host']}|{server['name']}|{ssh_key}\")
")

failed_servers=()

while IFS='|' read -r host name ssh_key; do

    # Skip GCP server (deploy manually)
    if [[ "$name" == *"GCP"* ]]; then
        info "Skipping $name (use deploy-gcp-manual.sh for manual deployment)"
        echo ""
        continue
    fi

    print_server_header "$name"

    # Copy GCP credentials file to server
    info "  Copying GCP credentials..."
    if [ -f "$GCP_CREDENTIALS_FILE" ]; then
        if [ -n "$ssh_key" ]; then
            scp -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i "$ssh_key" "$GCP_CREDENTIALS_FILE" "$host:~/gcp-credentials.json"
        else
            scp -o StrictHostKeyChecking=no "$GCP_CREDENTIALS_FILE" "$host:~/gcp-credentials.json"
        fi
        log "  GCP credentials copied"
    else
        error "  GCP credentials file not found: $GCP_CREDENTIALS_FILE"
    fi

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
if [ -z \"\$SUDO\" ]; then
    su - ytd -c \"git config --global --add safe.directory $DEPLOY_PATH\"
else
    sudo -u ytd git config --global --add safe.directory $DEPLOY_PATH
fi

echo '  [4/10] Pulling latest code from GitHub...'
if [ -z \"\$SUDO\" ]; then
    su - ytd -c \"cd $DEPLOY_PATH && git fetch origin && git reset --hard origin/$BRANCH\"
else
    sudo -u ytd bash -c \"cd $DEPLOY_PATH && git fetch origin && git reset --hard origin/$BRANCH\"
fi

echo '  [5/10] Fixing ownership and permissions...'
\$SUDO chown -R ytd:ytd $DEPLOY_PATH
\$SUDO chmod -R u+rwX,go+rX $DEPLOY_PATH

echo '  [6/10] Installing pipenv...'
if ! command -v pipenv &> /dev/null; then
    echo '  pipenv not found, installing...'
    if [ -z \"\$SUDO\" ]; then
        su - ytd -c \"python3.13 -m pip install --user pipenv --quiet\"
    else
        sudo -u ytd python3.13 -m pip install --user pipenv --quiet
    fi
fi

echo '  [7/10] Removing existing virtual environment...'
if [ -z \"\$SUDO\" ]; then
    su - ytd -c \"cd $DEPLOY_PATH && PIPENV_VENV_IN_PROJECT=1 pipenv --rm || true\"
else
    sudo -u ytd bash -c \"cd $DEPLOY_PATH && PIPENV_VENV_IN_PROJECT=1 pipenv --rm || true\"
fi

echo '  [8/10] Installing dependencies with pipenv...'
if [ -z \"\$SUDO\" ]; then
    su - ytd -c \"cd $DEPLOY_PATH && PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy --quiet\"
else
    sudo -u ytd bash -c \"cd $DEPLOY_PATH && PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy --quiet\"
fi

echo '  [9/12] Copying GCP credentials file...'
if [ -f ~/gcp-credentials.json ]; then
    \$SUDO cp ~/gcp-credentials.json $DEPLOY_PATH/gcp-credentials.json
    \$SUDO chown ytd:ytd $DEPLOY_PATH/gcp-credentials.json
    \$SUDO chmod 600 $DEPLOY_PATH/gcp-credentials.json
    echo '  GCP credentials copied successfully'
else
    echo '  WARNING: ~/gcp-credentials.json not found, skipping...'
fi

echo '  [10/12] Restarting services...'
\$SUDO systemctl restart ytd-api ytd-worker ytd-beat

echo '  [11/12] Checking service status...'
sleep 3
if \$SUDO systemctl is-active --quiet ytd-api && \$SUDO systemctl is-active --quiet ytd-worker && \$SUDO systemctl is-active --quiet ytd-beat; then
    echo '  Services running successfully'
else
    echo '  ERROR: Services failed to start'
    \$SUDO systemctl status ytd-api ytd-worker ytd-beat --no-pager
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
