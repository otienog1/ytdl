# YouTube Downloader - Deployment Script (PowerShell)
# Deploys code from GitHub to production servers

$ErrorActionPreference = "Stop"

# ===================================================================
# LOAD SERVER CONFIGURATION
# ===================================================================
$configPath = Join-Path $PSScriptRoot "deploy-config.json"

if (-not (Test-Path $configPath)) {
    Write-Host "[ERROR] Configuration file not found: $configPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please create deploy-config.json with your server details"
    Write-Host ""
    pause
    exit 1
}

$config = Get-Content $configPath | ConvertFrom-Json

# Build servers array from config
$servers = @()
foreach ($server in $config.servers) {
    $sshKey = if ($server.sshKey) {
        # Expand environment variables in the path
        [System.Environment]::ExpandEnvironmentVariables($server.sshKey)
    } else {
        $null
    }

    $servers += @{
        Host = $server.host
        Name = $server.name
        SSHKey = $sshKey
    }
}

$deployPath = "/opt/ytdl"
$branch = "main"

# ===================================================================
# FUNCTIONS
# ===================================================================

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Text)
    Write-Host "[INFO] $Text" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Text)
    Write-Host "[OK] $Text" -ForegroundColor Green
}

function Write-Error-Message {
    param([string]$Text)
    Write-Host "[ERROR] $Text" -ForegroundColor Red
}

function Write-ServerHeader {
    param([string]$Name)
    Write-Host ""
    Write-Host ">>> Deploying to $Name..." -ForegroundColor Yellow
}

# Function to execute SSH command
function Invoke-SSHCommand {
    param(
        [string]$SSHHost,
        [string]$Command,
        [string]$SSHKey = $null
    )

    if ($SSHKey -and (Test-Path $SSHKey)) {
        $result = ssh -o StrictHostKeyChecking=no -i "$SSHKey" $SSHHost $Command 2>&1
    } else {
        $result = ssh -o StrictHostKeyChecking=no $SSHHost $Command 2>&1
    }

    return @{
        ExitCode = $LASTEXITCODE
        Output = $result
    }
}

# ===================================================================
# MAIN DEPLOYMENT
# ===================================================================

Write-Header "YouTube Downloader - Deployment Script"

$failedServers = @()

foreach ($server in $servers) {
    Write-ServerHeader -Name $server.Name

    try {
        # Build bash script content using single-quote here-string (no PowerShell expansion)
        $bashScript = @'
set -e
export DEBIAN_FRONTEND=noninteractive

if [ "$(id -u)" = "0" ]; then
    SUDO=""
else
    SUDO="sudo"
fi

echo '  [1/10] Checking Python version...'
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '3\.\d+' || echo '0.0')
REQUIRED_VERSION='3.13'

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "  Python version is $PYTHON_VERSION, upgrading to 3.13..."
    apt-get update -qq
    apt-get install -y software-properties-common -qq
    add-apt-repository -y ppa:deadsnakes/ppa
    apt-get update -qq
    apt-get install -y python3.13 python3.13-venv python3.13-dev python-is-python3 -qq
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1
    update-alternatives --set python3 /usr/bin/python3.13
    echo '  Python upgraded to 3.13'
else
    echo "  Python version $PYTHON_VERSION is compatible"
    if ! dpkg -l | grep -q python-is-python3; then
        echo '  Installing python-is-python3 package...'
        apt-get update -qq
        apt-get install -y python-is-python3 -qq
    fi
fi

echo '  [2/10] Navigating to deployment directory...'
cd DEPLOYPATH_PLACEHOLDER

echo '  [3/10] Configuring git safe directory...'
$SUDO -u ytd git config --global --add safe.directory DEPLOYPATH_PLACEHOLDER

echo '  [4/10] Pulling latest code from GitHub...'
$SUDO -u ytd git fetch origin
$SUDO -u ytd git reset --hard origin/BRANCH_PLACEHOLDER

echo '  [5/10] Fixing ownership and permissions...'
$SUDO chown -R ytd:ytd DEPLOYPATH_PLACEHOLDER
$SUDO chmod -R u+rwX,go+rX DEPLOYPATH_PLACEHOLDER

echo '  [6/10] Recreating virtual environment with Python 3.13...'
rm -rf DEPLOYPATH_PLACEHOLDER/.venv
$SUDO -u ytd python3.13 -m venv DEPLOYPATH_PLACEHOLDER/.venv

echo '  [7/10] Upgrading pip...'
$SUDO -u ytd DEPLOYPATH_PLACEHOLDER/.venv/bin/pip install --upgrade pip --quiet

echo '  [8/10] Installing/updating dependencies...'
$SUDO -u ytd DEPLOYPATH_PLACEHOLDER/.venv/bin/pip install -r requirements.txt --quiet

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
'@

        # Replace placeholders with actual PowerShell variables
        $bashScript = $bashScript.Replace('DEPLOYPATH_PLACEHOLDER', $deployPath).Replace('BRANCH_PLACEHOLDER', $branch)

        Write-Step "  Executing deployment commands..."

        $result = Invoke-SSHCommand -SSHHost $server.Host -Command "bash -c '$bashScript'" -SSHKey $server.SSHKey

        if ($result.ExitCode -eq 0) {
            Write-Success "  Deployment to $($server.Name) completed successfully"
        } else {
            Write-Error-Message "  Deployment to $($server.Name) FAILED"
            Write-Host $result.Output -ForegroundColor Red
            $failedServers += $server.Name
        }
    }
    catch {
        Write-Error-Message "  Deployment to $($server.Name) FAILED"
        Write-Host $_.Exception.Message -ForegroundColor Red
        $failedServers += $server.Name
    }

    Write-Host ""
}

# ===================================================================
# SUMMARY
# ===================================================================

Write-Header "Deployment Summary"

if ($failedServers.Count -eq 0) {
    Write-Success "All servers deployed successfully!"
    exit 0
} else {
    Write-Error-Message "Deployment failed on: $($failedServers -join ', ')"
    exit 1
}
