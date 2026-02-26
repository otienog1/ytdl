# Deployment Scripts

This directory contains all deployment scripts for the YouTube Downloader multi-server setup.

## 📂 Available Scripts

### 1. `deploy-from-local.bat` / `deploy-from-local.ps1` / `deploy-from-local.sh`
Deploy to all 3 servers from your local machine.

**Windows (PowerShell):**
```bash
.\deploy-from-local.bat
```

**Linux/Mac/WSL:**
```bash
bash deploy-from-local.sh
```

**Features:**
- Deploys to all 3 servers in sequence
- Pulls latest code on each server
- Installs local Redis if needed
- Copies `.env.production.server[N]` → `.env.production`
- Restarts all services
- Runs verification tests

### 2. `deploy-hybrid-redis.sh`
Server-side deployment script (run on the server itself).

**Usage:**
```bash
# On Server 1:
sudo bash deploy-hybrid-redis.sh 1

# On Server 2:
sudo bash deploy-hybrid-redis.sh 2

# On Server 3:
sudo bash deploy-hybrid-redis.sh 3
```

**What it does:**
- Pulls latest code from `/opt/ytdl` (main repo)
- Updates backend-python and frontend submodules
- Installs local Redis if not present
- Deploys server-specific .env files
- Restarts backend services
- Verifies deployment

### 3. `fix-server-git.sh`
Fixes git divergent branches issue on servers.

**Usage:**
```bash
bash fix-server-git.sh
```

**When to use:**
- When `git pull` fails with "divergent branches" error
- After force-pushing to GitHub
- To reset server to match GitHub exactly

## 📋 Server Configuration

| Server | IP | Account | Config Files |
|--------|----|---------| -------------|
| Server 1 | 172.234.172.191 | A (otienog1@yahoo.com) | `.env.production.server1` |
| Server 2 | 35.193.12.77 | B (otienog1@icluod.com) | `.env.production.server2` |
| Server 3 | 13.60.71.187 | C (7plus8studios@gmail.com) | `.env.production.server3` |

## 📁 Repository Structure

```
/opt/ytdl/                          # Main repository root
├── backend-python/                 # Backend submodule
│   ├── .env.production.server1    # Server 1 config (not in git)
│   ├── .env.production.server2    # Server 2 config (not in git)
│   ├── .env.production.server3    # Server 3 config (not in git)
│   ├── .env.production            # Active config (deployed by script)
│   ├── deploy-from-local.bat      # Windows deployment
│   ├── deploy-from-local.ps1      # PowerShell deployment
│   ├── deploy-from-local.sh       # Bash deployment
│   ├── deploy-hybrid-redis.sh     # Server-side deployment
│   └── fix-server-git.sh          # Git fix utility
├── cookie-extractor/
│   ├── .env.production.server1    # Server 1 config (not in git)
│   ├── .env.production.server2    # Server 2 config (not in git)
│   ├── .env.production.server3    # Server 3 config (not in git)
│   └── .env.production            # Active config (deployed by script)
└── frontend/                       # Frontend submodule
```

## ⚠️ Important Notes

1. **Scripts Location**: All deployment scripts are in `backend-python/` directory
2. **Main Repo**: Server git repo is at `/opt/ytdl` (NOT `/opt/ytdl/backend-python`)
3. **Submodules**: Backend and frontend are submodules within `/opt/ytdl`
4. **Branch**: All repos use `main` branch (not `master`)

## 🚀 Quick Start

### First Time Setup
1. Create `.env.production.server*` files locally (see [PRODUCTION_CONFIG_SETUP.md](../PRODUCTION_CONFIG_SETUP.md))
2. Run deployment: `.\deploy-from-local.bat`

### Regular Deployment
```bash
cd backend-python
.\deploy-from-local.bat
```

### Server-Side Deployment
```bash
ssh root@ytd.timobosafaris.com
cd /opt/ytdl/backend-python
sudo bash deploy-hybrid-redis.sh 1
```

## 🔧 Troubleshooting

### Issue: "Cannot find deploy script"
**Solution:** Scripts are now in `backend-python/` directory. Run from there.

### Issue: "Git divergent branches"
**Solution:** Run `bash fix-server-git.sh` to reset server to GitHub state.

### Issue: "Missing .env.production.server* files"
**Solution:** Create these files locally following [PRODUCTION_CONFIG_SETUP.md](../PRODUCTION_CONFIG_SETUP.md).

## 📚 Full Documentation

- [DEPLOY_NOW.md](../DEPLOY_NOW.md) - Quick deployment guide
- [PRODUCTION_CONFIG_SETUP.md](../PRODUCTION_CONFIG_SETUP.md) - Config file setup
- [FIX_WEBSOCKET.md](../FIX_WEBSOCKET.md) - WebSocket troubleshooting
