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

# Set non-interactive mode for apt-get
export DEBIAN_FRONTEND=noninteractive

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
git config --global --add safe.directory $DEPLOY_PATH

echo '  [4/10] Pulling latest code from GitHub...'
git fetch origin
git reset --hard origin/$BRANCH

echo '  [5/10] Fixing ownership and permissions...'
chown -R ytd:ytd $DEPLOY_PATH
chmod -R u+rwX,go+rX $DEPLOY_PATH

echo '  [6/10] Recreating virtual environment with Python 3.13...'
rm -rf $DEPLOY_PATH/.venv
sudo -u ytd python3.13 -m venv $DEPLOY_PATH/.venv

echo '  [7/10] Upgrading pip...'
sudo -u ytd $DEPLOY_PATH/.venv/bin/pip install --upgrade pip --quiet

echo '  [8/10] Installing/updating dependencies...'
sudo -u ytd $DEPLOY_PATH/.venv/bin/pip install -r requirements.txt --quiet

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
