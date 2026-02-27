#!/bin/bash
# Manual deployment script for GCP server
# Run this on the GCP server (7plus8@35.193.12.77)

set -e

# Set non-interactive mode for apt-get
export DEBIAN_FRONTEND=noninteractive

# Detect if running as root
if [ "$(id -u)" = "0" ]; then
    SUDO=""
else
    SUDO="sudo"
fi

echo '[1/10] Checking Python version...'
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '3\.\d+' || echo '0.0')
REQUIRED_VERSION='3.13'

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Python version is $PYTHON_VERSION, upgrading to 3.13..."

    # Update package list
    $SUDO apt-get update -qq

    # Install software-properties-common for add-apt-repository
    $SUDO apt-get install -y software-properties-common -qq

    # Add deadsnakes PPA for Python 3.13
    $SUDO add-apt-repository -y ppa:deadsnakes/ppa
    $SUDO apt-get update -qq

    # Install Python 3.13 and required packages
    $SUDO apt-get install -y python3.13 python3.13-venv python3.13-dev python-is-python3 -qq

    # Update alternatives to make python3.13 the default python3
    $SUDO update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1
    $SUDO update-alternatives --set python3 /usr/bin/python3.13

    echo 'Python upgraded to 3.13'
else
    echo "Python version $PYTHON_VERSION is compatible"

    # Ensure python-is-python3 is installed
    if ! dpkg -l | grep -q python-is-python3; then
        echo 'Installing python-is-python3 package...'
        $SUDO apt-get update -qq
        $SUDO apt-get install -y python-is-python3 -qq
    fi
fi

echo '[2/10] Navigating to deployment directory...'
cd /opt/ytdl

echo '[3/10] Fixing ownership and permissions first...'
$SUDO chown -R ytd:ytd /opt/ytdl
$SUDO chmod -R u+rwX,go+rX /opt/ytdl

echo '[4/10] Configuring git safe directory...'
$SUDO -u ytd git config --global --add safe.directory /opt/ytdl

echo '[5/10] Pulling latest code from GitHub...'
$SUDO -u ytd bash -c "cd /opt/ytdl && git fetch origin && git reset --hard origin/main"

echo '[6/10] Re-fixing ownership after git pull...'
$SUDO chown -R ytd:ytd /opt/ytdl
$SUDO chmod -R u+rwX,go+rX /opt/ytdl

echo '[7/10] Installing pipenv...'
if ! command -v pipenv &> /dev/null; then
    echo 'pipenv not found, installing...'
    $SUDO -u ytd python3.13 -m pip install --user pipenv --quiet
fi

echo '[8/10] Removing existing virtual environment...'
$SUDO -u ytd bash -c "cd /opt/ytdl && PIPENV_VENV_IN_PROJECT=1 pipenv --rm || true"

echo '[9/10] Installing dependencies with pipenv...'
$SUDO -u ytd bash -c "cd /opt/ytdl && PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy --quiet"

echo '[10/12] Copying GCP credentials file...'
if [ -f ~/gcp-credentials.json ]; then
    $SUDO cp ~/gcp-credentials.json /opt/ytdl/gcp-credentials.json
    $SUDO chown ytd:ytd /opt/ytdl/gcp-credentials.json
    $SUDO chmod 600 /opt/ytdl/gcp-credentials.json
    echo 'GCP credentials copied successfully'
else
    echo 'WARNING: ~/gcp-credentials.json not found, skipping...'
fi

echo '[11/12] Restarting services...'
$SUDO systemctl restart ytd-api ytd-worker ytd-beat

echo '[12/12] Checking service status...'
sleep 3
if $SUDO systemctl is-active --quiet ytd-api && $SUDO systemctl is-active --quiet ytd-worker && $SUDO systemctl is-active --quiet ytd-beat; then
    echo 'Services running successfully'
else
    echo 'ERROR: Services failed to start'
    $SUDO systemctl status ytd-api ytd-worker ytd-beat --no-pager
    exit 1
fi

echo ''
echo '========================================='
echo '  GCP Deployment completed successfully!'
echo '========================================='
