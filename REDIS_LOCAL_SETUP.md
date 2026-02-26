# Local Redis Setup for Development

You're hitting "max number of clients reached" on Redis Cloud (free tier). Let's set up local Redis to eliminate this issue.

## Quick Install: Redis on Windows

### Option 1: Using Chocolatey (Recommended - Fastest)

```powershell
# Run PowerShell as Administrator
choco install redis-64

# Start Redis
redis-server
```

### Option 2: Using Memurai (Redis-compatible for Windows)

Memurai is a native Windows port of Redis that's easier to run as a service.

1. Download from: https://www.memurai.com/get-memurai
2. Install (it will run as a Windows service automatically)
3. Default port: 6379

### Option 3: Using WSL2 (Windows Subsystem for Linux)

```bash
# In WSL2 Ubuntu terminal
sudo apt update
sudo apt install redis-server

# Start Redis
sudo service redis-server start
```

## Verify Redis is Running

```bash
# Check if Redis is responding
redis-cli ping
# Should return: PONG
```

## Update Configuration

Your `.env` file has already been updated to use local Redis:

```env
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Restart Services

After Redis is running, restart both:

```bash
# Terminal 1 - Backend
cd backend-python
.\start-dev.bat

# Terminal 2 - Celery
cd backend-python
pipenv run celery -A app.queue.celery_app worker --loglevel=info --pool=solo
```

## Verify It's Working

You should see in Celery logs:
```
Connected to redis://localhost:6379/0
```

No more "max number of clients reached" errors!

## Benefits of Local Redis

- ✅ **No connection limits** - unlimited connections
- ✅ **Faster** - no network latency
- ✅ **Works offline** - develop anywhere
- ✅ **Free** - no cost concerns
- ✅ **Better debugging** - use redis-cli to inspect queues

## Useful Redis Commands

```bash
# Connect to Redis CLI
redis-cli

# View all keys
KEYS *

# Monitor real-time commands
MONITOR

# Check Celery queue length
LLEN celery

# Flush all data (careful!)
FLUSHALL
```

## Switching Back to Redis Cloud

To switch back to Redis Cloud for production:

Edit `.env`:
```env
REDIS_URL=redis://default:password@redis-17684.c10.us-east-1-3.ec2.cloud.redislabs.com:17684
CELERY_BROKER_URL=redis://default:password@redis-17684.c10.us-east-1-3.ec2.cloud.redislabs.com:17684/0
CELERY_RESULT_BACKEND=redis://default:password@redis-17684.c10.us-east-1-3.ec2.cloud.redislabs.com:17684/0
```

## Troubleshooting

### "redis-server not found"
- Add Redis to PATH: `C:\Program Files\Redis` (or wherever installed)
- Or use full path: `"C:\Program Files\Redis\redis-server.exe"`

### "Could not connect to Redis at localhost:6379"
- Check if Redis is running: `redis-cli ping`
- Start Redis service: `net start Redis` (if installed as service)

### Port 6379 already in use
- Find process: `netstat -ano | findstr :6379`
- Or use different port and update `.env`

---

**Ready?** Install Redis, update `.env`, and restart your services! 🚀
