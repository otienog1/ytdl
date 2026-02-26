# Deployment Scripts

This directory contains deployment scripts for the hybrid Redis multi-server setup.

## Setup

### 1. Configure Server Details

1. Copy the example configuration file:
   ```bash
   copy deploy-config.example.json deploy-config.json
   ```

2. Edit `deploy-config.json` with your server details:
   - **host**: SSH connection string (username@hostname-or-ip)
   - **name**: Descriptive name for the server
   - **account**: Associated account information
   - **sshKey**: Path to SSH private key (null for password auth)

### 2. Windows Deployment

#### Prerequisites
- Windows 10/11 with OpenSSH Client enabled
- PowerShell (built-in)

#### Run Deployment
```cmd
.\deploy-from-local.bat
```

The batch file will automatically use PowerShell (preferred) or fall back to Bash if available.

### 3. Linux/macOS/WSL Deployment

#### Prerequisites
- Bash shell
- `jq` command-line JSON processor
  - Ubuntu/Debian: `sudo apt-get install jq`
  - macOS: `brew install jq`
- SSH client

#### Run Deployment
```bash
bash deploy-from-local.sh
```

## Security Notes

⚠️ **IMPORTANT**:
- `deploy-config.json` contains sensitive server information and is **automatically excluded** from git
- Only `deploy-config.example.json` should be committed to the repository
- Never commit actual server IPs, usernames, or SSH key paths

## What the Deployment Does

1. Tests SSH connection to each server
2. Pulls latest code from git repositories (main and backend-python)
3. Checks and installs Redis if needed
4. Deploys `.env.production` configurations
5. Restarts backend services (ytd-api, ytd-worker, ytd-beat)
6. Restarts cookie extractor service (if present)
7. Runs verification tests:
   - Redis connectivity
   - Backend API health
   - Service status
   - Recent error logs

## Deployment Order

Servers are deployed sequentially:
1. Server 1: Primary server (ytd.timobosafaris.com)
2. Server 2: GCP server
3. Server 3: AWS server

If a deployment fails, you can choose to continue with remaining servers or abort.

## Troubleshooting

### SSH Connection Issues
- Verify server IP and port are correct
- Check firewall rules allow SSH (port 22)
- Ensure SSH keys have correct permissions (600)
- Test manual SSH: `ssh user@host`

### Git Pull Failures
- Check repository access permissions
- Verify the correct branch exists (main vs master)
- Ensure git credentials are configured on the server

### Service Restart Failures
- Check service status manually: `systemctl status ytd-api`
- Review service logs: `journalctl -u ytd-worker -n 50`
- Verify .env.production files exist and are valid

## Files

- `deploy-from-local.bat` - Windows batch launcher
- `deploy-from-local.ps1` - PowerShell deployment script
- `deploy-from-local.sh` - Bash deployment script
- `deploy-config.json` - Server configuration (git-ignored)
- `deploy-config.example.json` - Configuration template (committed)
