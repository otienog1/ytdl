# Local Residential Proxy - Summary

## What Is This?

A **standalone Node.js application** that creates a SOCKS5 proxy server on your home computer. This allows your cloud server to route YouTube download requests through your residential IP address instead of the datacenter IP, bypassing YouTube's bot detection.

## Why You Need It

YouTube blocks datacenter/cloud server IPs from downloading Shorts videos. You see errors like:

```
Sign in to confirm you're not a bot
```

This proxy solves that problem by:
1. Running on YOUR home computer (residential IP)
2. Accepting connections from your cloud server
3. Forwarding requests to YouTube through your home internet
4. YouTube sees a residential user, not a datacenter

## Files Included

```
local-proxy/
├── simple-proxy.js      # Main SOCKS5 server (120 lines)
├── package.json         # Node.js dependencies
├── README.md            # Complete documentation
├── QUICKSTART.md        # 5-minute setup guide
├── SUMMARY.md           # This file
└── .gitignore          # Git ignore rules
```

## Quick Start

### 1. Install Dependencies

```bash
cd local-proxy
npm install
```

This installs the `socksv5` package.

### 2. Run the Proxy

```bash
node simple-proxy.js --port 1080 --auth myuser:mypass123
```

Replace `myuser:mypass123` with your own credentials.

**Keep this terminal open!** The proxy runs in the foreground.

### 3. Get Your Public IP

Open a new terminal:

```bash
curl ifconfig.me
```

Save this IP (e.g., `203.0.113.45`).

### 4. Setup Port Forwarding

1. Login to your router (usually http://192.168.1.1)
2. Find "Port Forwarding" settings
3. Forward external port `1080` to your computer's local IP on port `1080`
4. Save

### 5. Configure Your Cloud Server

SSH to your server and update the backend config:

```bash
ssh root@172.234.172.191
sudo nano /opt/ytd/backend-python/.env.production
```

Add this line:

```bash
YT_DLP_PROXY=socks5://myuser:mypass123@YOUR_PUBLIC_IP:1080
```

Example:
```bash
YT_DLP_PROXY=socks5://myuser:mypass123@203.0.113.45:1080
```

Save and restart:

```bash
sudo systemctl restart ytd-api ytd-worker
```

### 6. Test

Go to https://ytd.timobosafaris.com and try downloading a YouTube Short.

Watch the proxy terminal for connection logs.

## How It Works

```
User visits https://ytd.timobosafaris.com
    ↓
Frontend sends request to Backend
    ↓
Backend (172.234.172.191) connects to YOUR proxy
    ↓
YOUR home computer (This Proxy) forwards to YouTube
    ↓
YouTube sees residential IP ✓
    ↓
Download succeeds!
```

## Key Features

1. **Simple**: Just Node.js, no complex setup
2. **Secure**: Optional authentication (recommended)
3. **Standalone**: Completely separate from backend/frontend
4. **Portable**: Can use for other projects too
5. **Monitored**: Logs all connections

## Production Use

To keep it running 24/7, use PM2:

```bash
npm install -g pm2
pm2 start simple-proxy.js --name "ytd-proxy" -- --port 1080 --auth user:pass
pm2 save
pm2 startup  # Follow instructions
```

View logs:
```bash
pm2 logs ytd-proxy
```

## Alternative: Paid Services

If you can't run a local proxy, use paid residential proxy services:

1. **Bright Data**: ~$500/month
2. **Smartproxy**: ~$80/month for 8GB
3. **Oxylabs**: ~$300/month

Configure same way:
```bash
YT_DLP_PROXY=socks5://user:pass@proxy.provider.com:port
```

## Security Tips

1. **Always use authentication**: Never run without `--auth`
2. **Use strong passwords**: Generate with `openssl rand -base64 24`
3. **Firewall rules**: Only allow your server IP (172.234.172.191)
4. **Monitor logs**: Watch for suspicious activity

## Troubleshooting

### "Connection refused"
- Check proxy is running
- Verify port forwarding is correct
- Test locally: `curl --proxy socks5://127.0.0.1:1080 https://youtube.com`

### "Still getting bot detection"
- Wait 5-10 minutes after configuring
- Check backend logs: `sudo journalctl -u ytd-worker -f`
- Verify proxy URL in .env.production is correct

### "Address already in use"
- Use different port: `--port 1081`
- Update backend config to match

## Documentation Links

- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup
- [README.md](README.md) - Full documentation with all options
- [../README.md](../README.md) - Project overview

## Technical Details

- **Protocol**: SOCKS5 (industry standard proxy protocol)
- **Package**: socksv5 (npm package)
- **Port**: Default 1080 (configurable)
- **Authentication**: Username/password (optional but recommended)
- **Logging**: Connection count and destination addresses
- **Platform**: Cross-platform (Windows, macOS, Linux)

## What This Is NOT

- ❌ Not a VPN
- ❌ Not a browser extension
- ❌ Not part of the backend or frontend code
- ❌ Not hosted on the cloud server

## What This IS

- ✅ A standalone application
- ✅ Runs on YOUR computer
- ✅ Uses YOUR home internet
- ✅ Completely separate project
- ✅ Can be shared across multiple projects

## Cost

**FREE** - Just uses your existing home internet connection. No additional costs.

## Bandwidth Usage

Minimal - only the video downloads pass through your connection. For a 5MB YouTube Short, you use 5MB of upload bandwidth.

## Summary

This is a **simple, standalone proxy server** that solves YouTube's datacenter IP blocking by routing requests through your home internet. It's completely separate from the frontend and backend, and can be run independently.

**Time to setup**: 5-10 minutes
**Cost**: Free (uses your home internet)
**Complexity**: Low (just Node.js)
**Maintenance**: Minimal (can run 24/7 with PM2)

Get started: [QUICKSTART.md](QUICKSTART.md)
