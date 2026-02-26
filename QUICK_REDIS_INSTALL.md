# Quick Redis Installation (No Admin Rights Needed)

## Fastest Option: Download Portable Redis

Since you don't have Chocolatey and want to start immediately, use this method:

### Step 1: Download Redis for Windows

Download the portable version:
- **tporadowski/redis (Recommended)**: https://github.com/tporadowski/redis/releases
  - Download: `Redis-x64-5.0.14.1.zip` (or latest version)
  - Extract to: `C:\redis` or any folder you prefer

**Direct download link**: https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip

### Step 2: Extract and Start

```powershell
# Extract the ZIP file to C:\redis

# Start Redis (keeps running in terminal)
cd C:\redis
.\redis-server.exe
```

You should see:
```
                _._
           _.-``__ ''-._
      _.-``    `.  `_.  ''-._           Redis 5.0.14.1 (00000000/0) 64 bit
  .-`` .-```.  ```\/    _.,_ ''-._
 (    '      ,       .-`  | `,    )     Running in standalone mode
 |`-._`-...-` __...-.``-._|'` _.-'|     Port: 6379
 |    `-._   `._    /     _.-'    |
  `-._    `-._  `-./  _.-'    _.-'
 |`-._`-._    `-.__.-'    _.-'_.-'|
 |    `-._`-._        _.-'_.-'    |           http://redis.io
  `-._    `-._`-.__.-'_.-'    _.-'
 |`-._`-._    `-.__.-'    _.-'_.-'|
 |    `-._`-._        _.-'_.-'    |
  `-._    `-._`-.__.-'_.-'    _.-'
      `-._    `-.__.-'    _.-'
          `-._        _.-'
              `-.__.-'
```

**Keep this terminal window open!** Redis needs to keep running.

### Step 3: Verify It's Working

Open a **new terminal** and navigate to the Redis folder:

```powershell
cd C:\redis
.\redis-cli.exe ping
```

Should return: `PONG`

### Step 4: Restart Your Services

Now restart both:

**Terminal 1 - Redis** (already running)
**Terminal 2 - Backend**:
```bash
cd C:\Users\7plus8\build\ytd\backend-python
.\start-dev.bat
```

**Terminal 3 - Celery**:
```bash
cd C:\Users\7plus8\build\ytd\backend-python
pipenv run celery -A app.queue.celery_app worker --loglevel=info --pool=solo
```

## Alternative: Memurai (Best for Production-like Setup)

If you want Redis to run as a Windows service (so you don't need to keep a terminal open):

1. Download Memurai: https://www.memurai.com/get-memurai
2. Install (no admin rights needed)
3. It automatically starts as a service on port 6379
4. Done!

## Alternative: WSL2 (If You Have It)

If you have WSL2 Ubuntu installed:

```bash
# In WSL2 terminal
sudo apt update
sudo apt install redis-server -y

# Start Redis
sudo service redis-server start

# Test
redis-cli ping
```

## Stopping Redis

### Portable Version:
- Just close the terminal window running `redis-server.exe`
- Or press `Ctrl+C` in that terminal

### Memurai:
- It runs as a service, always available
- Stop: `net stop Memurai`
- Start: `net start Memurai`

---

## 🎯 Quick Summary

1. **Download**: https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip
2. **Extract** to `C:\redis`
3. **Run**: `C:\redis\redis-server.exe` (keep terminal open)
4. **Test**: Open new terminal → `C:\redis\redis-cli.exe ping`
5. **Restart** your backend and Celery

That's it! No installation, no admin rights, works immediately! 🚀
