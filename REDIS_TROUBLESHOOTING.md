# Redis Connection Troubleshooting

If you're seeing Redis connection errors, follow these steps to fix them.

## Common Error Messages

### "ECONNREFUSED"
Redis is not reachable at the configured URL.

### "Authentication failed"
Password or credentials are incorrect.

### "Connection timeout"
Network issue or wrong host/port.

## Solution 1: Verify Your Redis Cloud Connection

### Step 1: Check Your Redis Cloud Dashboard

1. Log into https://app.redislabs.com
2. Go to your database
3. Click "Connect"
4. Copy the **Redis URL** (should look like this):
   ```
   redis://default:YOUR_PASSWORD@redis-XXXXX.c10.us-east-1-3.ec2.cloud.redislabs.com:XXXXX
   ```

### Step 2: Update backend/.env

Make sure your `REDIS_URL` in `backend/.env` matches exactly:

```env
REDIS_URL=redis://default:YOUR_PASSWORD@redis-XXXXX.c10.us-east-1-3.ec2.cloud.redislabs.com:XXXXX
```

**Important:**
- No spaces
- Keep the `default:` prefix (that's the username)
- Include the password after `default:`
- Use the full hostname
- Include the port number at the end

### Step 3: Test the Connection

Before running the app, test Redis connection:

```bash
# Using redis-cli (if installed)
redis-cli -u "redis://default:YOUR_PASSWORD@redis-XXXXX.cloud.redislabs.com:XXXXX" ping

# Should return: PONG
```

Or test with Node.js:

```bash
# Create test-redis.js
cat > test-redis.js << 'EOF'
const Redis = require('ioredis');
require('dotenv').config();

const redis = new Redis(process.env.REDIS_URL, {
  tls: { rejectUnauthorized: false }
});

redis.on('connect', () => {
  console.log('✅ Redis connected!');
  process.exit(0);
});

redis.on('error', (err) => {
  console.error('❌ Redis error:', err);
  process.exit(1);
});
EOF

# Run test
cd backend
node ../test-redis.js
```

## Solution 2: Use Local Redis (Development Only)

If Redis Cloud isn't working, use local Redis:

### Windows

1. Download Redis for Windows:
   - https://github.com/tporadowski/redis/releases
   - Download `Redis-x64-5.0.14.1.zip`
   - Extract to `C:\Redis`

2. Start Redis:
   ```bash
   cd C:\Redis
   redis-server.exe
   ```

3. Update `backend/.env`:
   ```env
   REDIS_URL=redis://localhost:6379
   ```

### macOS

```bash
# Install
brew install redis

# Start
brew services start redis

# Update backend/.env
REDIS_URL=redis://localhost:6379
```

### Linux

```bash
# Install
sudo apt-get update
sudo apt-get install redis-server

# Start
sudo systemctl start redis
sudo systemctl enable redis

# Update backend/.env
REDIS_URL=redis://localhost:6379
```

## Solution 3: Check Firewall/Network

Redis Cloud requires outbound connections on the specified port.

### Test Network Access

```bash
# Windows
telnet redis-XXXXX.cloud.redislabs.com PORT

# Mac/Linux
nc -zv redis-XXXXX.cloud.redislabs.com PORT
```

If connection fails:
- Check firewall settings
- Check antivirus software
- Try from different network
- Contact your IT department

## Solution 4: Verify Code Changes

The latest code fixes include TLS support for Redis Cloud. Make sure you have the updated files:

### Check backend/src/config/redis.ts

Should include TLS configuration:

```typescript
const redisConfig = redisUrl.startsWith('rediss://') || redisUrl.includes('cloud.redislabs.com')
  ? {
      maxRetriesPerRequest: 3,
      enableReadyCheck: true,
      retryStrategy(times: number) {
        const delay = Math.min(times * 50, 2000);
        return delay;
      },
      tls: {
        rejectUnauthorized: false,
      },
    }
  : // ... rest of config
```

### Check backend/src/queue/downloadQueue.ts

Should parse URL properly:

```typescript
const redisUrlObj = new URL(redisUrl);

const redisOptions: any = {
  host: redisUrlObj.hostname,
  port: parseInt(redisUrlObj.port) || 6379,
};

if (redisUrlObj.password) {
  redisOptions.password = redisUrlObj.password;
}

// Enable TLS for Redis Cloud
if (redisUrl.startsWith('rediss://') || redisUrl.includes('cloud.redislabs.com')) {
  redisOptions.tls = {
    rejectUnauthorized: false,
  };
}
```

## Solution 5: Restart Everything

After making changes:

```bash
# Stop the backend (Ctrl+C)

# Clear node_modules and reinstall
cd backend
rm -rf node_modules
npm install

# Restart backend
npm run dev
```

## Quick Checklist

- [ ] Redis Cloud database is active (check dashboard)
- [ ] REDIS_URL in `.env` matches Redis Cloud connection string
- [ ] No typos in REDIS_URL (copy-paste from Redis Cloud)
- [ ] No extra spaces in `.env` file
- [ ] Backend code has TLS support (check files above)
- [ ] Firewall allows outbound connection to Redis Cloud
- [ ] Backend restarted after changes

## Still Not Working?

### Option A: Use a Different Redis Provider

**Upstash Redis (Alternative)**
1. Go to https://upstash.com
2. Create free account
3. Create Redis database
4. Copy connection string
5. Use in `REDIS_URL`

### Option B: Disable Redis Temporarily

For testing ONLY, you can comment out Redis in development:

**⚠️ WARNING:** This will disable job queue functionality!

```typescript
// backend/src/index.ts
// Comment out the download queue import
// import downloadQueue from './queue/downloadQueue';
```

This won't allow video downloads, but you can test other features.

## Getting Help

If none of these work:

1. **Check Backend Logs**
   ```bash
   # Look in backend/error.log
   # Or check terminal output
   ```

2. **Get Full Error Details**
   - Copy the complete error message
   - Check which file is throwing the error
   - Note the line number

3. **Verify Environment**
   ```bash
   # Check Node.js version
   node -v
   # Should be 18+

   # Check if .env is being loaded
   cd backend
   node -e "require('dotenv').config(); console.log(process.env.REDIS_URL)"
   ```

4. **Test Redis URL Format**
   ```bash
   # Should not return "undefined"
   cd backend
   node -e "const url = new URL('YOUR_REDIS_URL'); console.log('Host:', url.hostname, 'Port:', url.port, 'Has Password:', !!url.password)"
   ```

## Success!

When working correctly, you should see:

```
Redis connected successfully
MongoDB connected successfully
Google Cloud Storage initialized
Server is running on port 3001
```

No "ECONNREFUSED" or "Queue error" messages!
