# YouTube Downloader - Deployment Script (PowerShell)
# Deploys code from GitHub to production servers

param(
    [string]$SSHKey = ""
)

$ErrorActionPreference = "Stop"

# Server configurations
$servers = @(
    @{
        ServerHost = "ytd.timobosafaris.com"
        Name = "Linode"
        User = "root"
    },
    @{
        ServerHost = "35.193.12.77"
        Name = "GCP"
        User = "root"
    },
    @{
        ServerHost = "13.60.71.187"
        Name = "AWS"
        User = "root"
    }
)

$deployPath = "/opt/ytdl"
$branch = "main"

# Colors for output
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
    param([string]$Name, [string]$ServerHost)
    Write-Host ""
    Write-Host ">>> Deploying to $Name ($ServerHost)..." -ForegroundColor Yellow
}

# Function to execute SSH command
function Invoke-SSHCommand {
    param(
        [string]$SSHHost,
        [string]$Command,
        [string]$SSHKey = ""
    )

    $sshArgs = if ($SSHKey) {
        @("-i", $SSHKey, $SSHHost, $Command)
    } else {
        @($SSHHost, $Command)
    }

    $result = & ssh @sshArgs 2>&1
    $exitCode = $LASTEXITCODE

    return @{
        ExitCode = $exitCode
        Output = $result
    }
}

# Main deployment
Write-Header "YouTube Downloader - Deployment Script"

$failedServers = @()

foreach ($server in $servers) {
    Write-ServerHeader -Name $server.Name -ServerHost $server.ServerHost

    $sshHost = "$($server.User)@$($server.ServerHost)"

    try {
        # Build the deployment commands
        $deployCommands = @"
set -e

echo '  [1/6] Navigating to deployment directory...'
cd $deployPath

echo '  [2/6] Pulling latest code from GitHub...'
git fetch origin
git reset --hard origin/$branch

echo '  [3/6] Fixing ownership...'
chown -R ytd:ytd $deployPath

echo '  [4/6] Installing/updating dependencies...'
sudo -u ytd $deployPath/.venv/bin/pip install -r requirements.txt --quiet

echo '  [5/6] Restarting services...'
systemctl restart ytd-api ytd-worker

echo '  [6/6] Checking service status...'
sleep 3
if systemctl is-active --quiet ytd-api && systemctl is-active --quiet ytd-worker; then
    echo '  [OK] Services running successfully'
else
    echo '  [ERROR] Services failed to start'
    systemctl status ytd-api ytd-worker --no-pager
    exit 1
fi
"@

        Write-Step "  [1/6] Navigating to deployment directory..."
        Write-Step "  [2/6] Pulling latest code from GitHub..."
        Write-Step "  [3/6] Fixing ownership..."
        Write-Step "  [4/6] Installing/updating dependencies..."
        Write-Step "  [5/6] Restarting services..."
        Write-Step "  [6/6] Checking service status..."

        $result = Invoke-SSHCommand -SSHHost $sshHost -Command $deployCommands -SSHKey $SSHKey

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

# Summary
Write-Header "Deployment Summary"

if ($failedServers.Count -eq 0) {
    Write-Success "All servers deployed successfully!"
    exit 0
} else {
    Write-Error-Message "Deployment failed on: $($failedServers -join ', ')"
    exit 1
}
