# ===================================================================
# Deploy Hybrid Redis from Local Windows Machine to All Servers
# ===================================================================
# This script runs on your LOCAL Windows machine and deploys
# to all 3 servers via SSH (uses Windows native SSH client)
#
# Requirements:
#   - Windows 10/11 with OpenSSH client enabled
#   - SSH access to all servers (key-based auth recommended)
#
# Usage: powershell -ExecutionPolicy Bypass -File deploy-from-local.ps1
# ===================================================================

# Stop on errors
$ErrorActionPreference = "Stop"

# ===================================================================
# LOAD SERVER CONFIGURATION
# ===================================================================
$configPath = Join-Path $PSScriptRoot "deploy-config.json"

if (-not (Test-Path $configPath)) {
    Write-Host "ERROR: Configuration file not found: $configPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please create deploy-config.json from deploy-config.example.json"
    Write-Host "  1. Copy deploy-config.example.json to deploy-config.json"
    Write-Host "  2. Update the server details in deploy-config.json"
    Write-Host ""
    pause
    exit 1
}

$config = Get-Content $configPath | ConvertFrom-Json

# Build SERVERS hashtable from config
$SERVERS = @{}
foreach ($server in $config.servers) {
    $sshKey = if ($server.sshKey) {
        # Expand environment variables in the path
        [System.Environment]::ExpandEnvironmentVariables($server.sshKey)
    } else {
        $null
    }

    $SERVERS[$server.id] = @{
        Host = $server.host
        Account = $server.account
        Name = $server.name
        SSHKey = $sshKey
    }
}

# ===================================================================
# FUNCTIONS
# ===================================================================

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "========================================================================" -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Text)
    Write-Host ""
    Write-Host $Text -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Text)
    Write-Host "✅ $Text" -ForegroundColor Green
}

function Write-Error-Message {
    param([string]$Text)
    Write-Host "❌ $Text" -ForegroundColor Red
}

function Write-Warning-Message {
    param([string]$Text)
    Write-Host "⚠️  $Text" -ForegroundColor Yellow
}

function Invoke-SSHCommand {
    param(
        [string]$SSHHost,
        [string]$Command,
        [string]$SSHKey = $null,
        [bool]$UseSudo = $false
    )

    # Wrap command with sudo if needed
    $finalCommand = if ($UseSudo) { "sudo $Command" } else { $Command }

    if ($SSHKey) {
        ssh -o StrictHostKeyChecking=no -i "$SSHKey" $SSHHost $finalCommand
    } else {
        ssh -o StrictHostKeyChecking=no $SSHHost $finalCommand
    }
}

function Deploy-ToServer {
    param([int]$ServerNum)

    $server = $SERVERS[$ServerNum]
    $sshHost = $server.Host
    $account = $server.Account
    $serverName = $server.Name
    $sshKey = $server.SSHKey

    # Determine if we need sudo (servers with SSH keys need sudo)
    $useSudo = $sshKey -ne $null

    # Build SSH options
    $sshOptions = "-o ConnectTimeout=10 -o StrictHostKeyChecking=no"
    if ($sshKey) {
        $sshOptions += " -i `"$sshKey`""
    }

    Write-Header "Deploying to Server $ServerNum : $serverName"
    Write-Host "Account: $account"
    Write-Host "========================================================================" -ForegroundColor Cyan

    try {
        # Test SSH connection
        Write-Step "[1/8] Testing SSH connection..."
        if ($sshKey) {
            $testResult = ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -i "$sshKey" $sshHost "echo 'SSH connection successful'" 2>&1
        } else {
            $testResult = ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no $sshHost "echo 'SSH connection successful'" 2>&1
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Message "Cannot connect to $sshHost"
            return $false
        }
        Write-Success "SSH connection successful"

        # Pull main repository
        Write-Step "[2/8] Pulling main repository on server..."
        # Git pull (using main branch)
        Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -UseSudo $useSudo -Command "bash -c 'cd /opt/ytdl && git config --global --add safe.directory /opt/ytdl && git fetch origin && git reset --hard origin/main'"
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Message "Failed to pull main repository"
            return $false
        }
        Write-Success "Main repository updated (including backend-python)"

        # Check if local Redis is installed
        Write-Step "[3/8] Checking Redis installation..."
        $redisCheck = Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -UseSudo $useSudo -Command "command -v redis-server &> /dev/null && echo 'installed' || echo 'notinstalled'" 2>&1
        if ($redisCheck -match "notinstalled") {
            Write-Host "Redis not found. Installing..."
            Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -UseSudo $useSudo -Command "bash -c 'cd /opt/ytdl && bash install-local-redis.sh'"
        } else {
            Write-Success "Redis already installed"
            # Make sure it's running
            Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -UseSudo $useSudo -Command "systemctl is-active redis-server || systemctl start redis-server"
        }

        # Deploy backend .env.production configuration
        Write-Step "[4/8] Deploying backend configuration..."
        $backupDate = Get-Date -Format "yyyyMMdd_HHmmss"
        Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -UseSudo $useSudo -Command "bash -c 'cd /opt/ytdl/backend-python && if [ -f .env.production ]; then cp .env.production .env.production.backup.$backupDate; fi && cp .env.production.server$ServerNum .env.production && chown ytdl:ytdl .env.production && chmod 600 .env.production'"
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Message "Failed to deploy backend configuration"
            return $false
        }
        Write-Success "Backend .env.production deployed"

        # Deploy cookie extractor .env.production configuration
        Write-Step "[5/8] Deploying cookie extractor configuration..."
        Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -UseSudo $useSudo -Command "bash -c 'cd /opt/ytdl/cookie-extractor && if [ -f .env.production ]; then cp .env.production .env.production.backup.$backupDate; fi && cp .env.production.server$ServerNum .env.production && chown ytdl:ytdl .env.production && chmod 600 .env.production'"
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Message "Failed to deploy cookie extractor configuration"
            return $false
        }
        Write-Success "Cookie extractor .env.production deployed"

        # Restart backend services
        Write-Step "[6/8] Restarting backend services..."
        Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -UseSudo $useSudo -Command "systemctl restart ytd-api ytd-worker ytd-beat"
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Message "Failed to restart backend services"
            return $false
        }
        Start-Sleep -Seconds 3
        Write-Success "Backend services restarted"

        # Restart cookie extractor
        Write-Step "[7/8] Restarting cookie extractor..."
        $serviceCheck = Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -UseSudo $useSudo -Command "systemctl list-units --full -all | grep -q ytd-cookie-extractor && echo 'found' || echo 'notfound'" 2>&1
        if ($serviceCheck -match "found") {
            Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -UseSudo $useSudo -Command "systemctl restart ytd-cookie-extractor"
            Write-Success "Cookie extractor restarted"
        } else {
            Write-Warning-Message "Cookie extractor service not found"
        }

        # Verification
        Write-Step "[8/8] Running verification tests..."

        # Check local Redis
        $redisStatus = Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -UseSudo $useSudo -Command "redis-cli ping &> /dev/null && echo 'ok' || echo 'fail'" 2>&1
        if ($redisStatus -match "ok") {
            Write-Success "Local Redis responding"
        } else {
            Write-Error-Message "Local Redis NOT responding"
        }

        # Check backend health
        Start-Sleep -Seconds 2
        $healthCheck = Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -Command "curl -s http://localhost:3001/api/health/ | grep -q status && echo 'healthy' || echo 'unhealthy'" 2>&1
        if ($healthCheck -match "healthy") {
            Write-Success "Backend API healthy"
        } else {
            Write-Error-Message "Backend API NOT responding"
        }

        # Check for errors
        $errorCount = Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -UseSudo $useSudo -Command "bash -c 'journalctl -u ytd-worker --since \"5 minutes ago\" | grep -i \"error\|timeout\" | wc -l'" 2>&1
        if ([int]$errorCount -eq 0) {
            Write-Success "No errors in worker logs"
        } else {
            Write-Warning-Message "Found $errorCount errors/timeouts in logs"
        }

        # Check service status
        Write-Host ""
        Write-Host "Service Status:" -ForegroundColor Cyan

        $apiStatus = Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -UseSudo $useSudo -Command "systemctl is-active ytd-api" 2>&1
        if ($apiStatus -match "active") {
            Write-Host "  ✅ ytd-api" -ForegroundColor Green
        } else {
            Write-Host "  ❌ ytd-api" -ForegroundColor Red
        }

        $workerStatus = Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -UseSudo $useSudo -Command "systemctl is-active ytd-worker" 2>&1
        if ($workerStatus -match "active") {
            Write-Host "  ✅ ytd-worker" -ForegroundColor Green
        } else {
            Write-Host "  ❌ ytd-worker" -ForegroundColor Red
        }

        $beatStatus = Invoke-SSHCommand -SSHHost $sshHost -SSHKey $sshKey -UseSudo $useSudo -Command "systemctl is-active ytd-beat" 2>&1
        if ($beatStatus -match "active") {
            Write-Host "  ✅ ytd-beat" -ForegroundColor Green
        } else {
            Write-Host "  ❌ ytd-beat" -ForegroundColor Red
        }

        Write-Host ""
        Write-Success "Server $ServerNum deployment complete!"
        Write-Host "========================================================================" -ForegroundColor Cyan

        return $true

    } catch {
        Write-Error-Message "Deployment failed with error: $_"
        return $false
    }
}

# ===================================================================
# MAIN SCRIPT
# ===================================================================

Write-Header "Hybrid Redis Multi-Server Deployment"
Write-Host ""
Write-Host "This script will deploy hybrid Redis configuration to:"
Write-Host "  Server 1: $($SERVERS[1].Name) - $($SERVERS[1].Account)"
Write-Host "  Server 2: $($SERVERS[2].Name) - $($SERVERS[2].Account)"
Write-Host "  Server 3: $($SERVERS[3].Name) - $($SERVERS[3].Account)"
Write-Host ""

# Check if SSH is available
$sshPath = Get-Command ssh -ErrorAction SilentlyContinue
if (-not $sshPath) {
    Write-Error-Message "SSH client not found!"
    Write-Host ""
    Write-Host "Please enable OpenSSH Client in Windows:"
    Write-Host "1. Open Settings > Apps > Optional Features"
    Write-Host "2. Click 'Add a feature'"
    Write-Host "3. Find and install 'OpenSSH Client'"
    Write-Host ""
    Write-Host "Or install from PowerShell (as Administrator):"
    Write-Host "  Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0"
    Write-Host ""
    pause
    exit 1
}

$response = Read-Host "Continue? (y/n)"
if ($response -notmatch "^[Yy]$") {
    Write-Host "Deployment cancelled"
    exit 0
}

# Track deployment results
$successfulDeployments = @()
$failedDeployments = @()

# Deploy to each server
foreach ($serverNum in 1..3) {
    if (Deploy-ToServer -ServerNum $serverNum) {
        $successfulDeployments += $serverNum
    } else {
        $failedDeployments += $serverNum
        Write-Host ""
        Write-Error-Message "Failed to deploy to Server $serverNum"
        $continue = Read-Host "Continue with remaining servers? (y/n)"
        if ($continue -notmatch "^[Yy]$") {
            break
        }
    }
}

# Summary
Write-Host ""
Write-Header "DEPLOYMENT SUMMARY"
Write-Host ""

if ($successfulDeployments.Count -gt 0) {
    Write-Host "✅ Successful Deployments ($($successfulDeployments.Count)):" -ForegroundColor Green
    foreach ($serverNum in $successfulDeployments) {
        Write-Host "   Server $serverNum : $($SERVERS[$serverNum].Name)" -ForegroundColor Green
    }
}

if ($failedDeployments.Count -gt 0) {
    Write-Host ""
    Write-Host "❌ Failed Deployments ($($failedDeployments.Count)):" -ForegroundColor Red
    foreach ($serverNum in $failedDeployments) {
        Write-Host "   Server $serverNum : $($SERVERS[$serverNum].Name)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan

if ($successfulDeployments.Count -eq 3) {
    Write-Host "🎉 All servers deployed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Monitor logs on each server for errors"
    Write-Host "2. Test downloads from the frontend"
    Write-Host "3. Verify no timeout errors occur"
    Write-Host ""
    Write-Host "Monitor commands:"
    Write-Host "  ssh $($SERVERS[1].Host) 'journalctl -u ytd-worker -f'"
    Write-Host "  ssh $($SERVERS[2].Host) 'journalctl -u ytd-worker -f'"
    Write-Host "  ssh $($SERVERS[3].Host) 'journalctl -u ytd-worker -f'"
} else {
    Write-Host "⚠️  Deployment completed with errors" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Check failed servers manually:"
    foreach ($serverNum in $failedDeployments) {
        Write-Host "  ssh $($SERVERS[$serverNum].Host)"
    }
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
pause
