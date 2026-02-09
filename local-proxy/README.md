# Local Residential Proxy for YouTube Shorts Downloader

This SOCKS5 proxy server runs on your local machine (home computer) and forwards requests from your cloud server through your residential internet connection. This bypasses YouTube's datacenter IP blocking.

## Why This is Needed

YouTube blocks downloads from datacenter/cloud IPs but allows residential IPs. By running this proxy on your home computer, your cloud server can route requests through your home internet connection.

## Prerequisites

- Node.js (v14 or higher) installed on your local machine
- Your local machine can accept incoming connections (port forwarding configured)
- Your public IP address (get it with: `curl ifconfig.me`)

## Installation

1. Navigate to the local-proxy directory:
```bash
cd local-proxy
```

2. Install dependencies:
```bash
npm install
```

## Usage

### Basic (No Authentication - NOT RECOMMENDED)

```bash
node simple-proxy.js
```

**WARNING**: This leaves your proxy open to anyone! Only use for testing.

### Recommended (With Authentication)

```bash
node simple-proxy.js --port 1080 --auth yourusername:yourpassword
```

Replace `yourusername` and `yourpassword` with secure credentials.

### Using npm scripts

```bash
# Start without auth (testing only)
npm start

# Start with auth (edit package.json to set your credentials first)
npm run start:auth
```

## Port Forwarding Setup

You need to configure your router to forward the proxy port to your local machine.

### Steps:

1. **Find your local IP address**: The proxy will display this when it starts
   - Usually something like `192.168.1.100` or `10.0.0.50`

2. **Access your router admin panel**:
   - Usually at `http://192.168.1.1` or `http://192.168.0.1`
   - Login with your router credentials

3. **Find Port Forwarding settings**:
   - Look for "Port Forwarding", "Virtual Servers", or "NAT"
   - Different routers have different names for this

4. **Create forwarding rule**:
   ```
   External Port: 1080 (or your chosen port)
   Internal Port: 1080 (same as external)
   Internal IP: [Your local machine IP from step 1]
   Protocol: TCP
   ```

5. **Save and apply** the settings

### Common Router Interfaces:

- **TP-Link**: Advanced → NAT Forwarding → Virtual Servers
- **Netgear**: Advanced → Port Forwarding / Port Triggering
- **Linksys**: Security → Apps and Gaming → Single Port Forwarding
- **ASUS**: WAN → Virtual Server / Port Forwarding
- **D-Link**: Advanced → Port Forwarding

## Get Your Public IP

Run this command to get your public IP address:

```bash
curl ifconfig.me
```

Or visit: https://whatismyipaddress.com

## Configure Your Backend Server

Once your proxy is running, configure your backend to use it:

1. SSH into your cloud server (172.234.172.191):
```bash
ssh root@172.234.172.191
```

2. Edit the backend environment file:
```bash
sudo nano /opt/ytd/backend-python/.env.production
```

3. Add this line (replace with your values):
```bash
YT_DLP_PROXY=socks5://yourusername:yourpassword@YOUR_PUBLIC_IP:1080
```

Example:
```bash
YT_DLP_PROXY=socks5://myuser:mypass@203.0.113.45:1080
```

4. Save the file (Ctrl+X, then Y, then Enter)

5. Restart the backend services:
```bash
sudo systemctl restart ytd-api
sudo systemctl restart ytd-worker
```

6. Test a download from your frontend

## Security Considerations

### 1. Use Authentication

Always use `--auth username:password` to prevent unauthorized access:

```bash
node simple-proxy.js --port 1080 --auth securename:securepass123
```

### 2. Use Strong Passwords

Generate a strong password:
```bash
# On Linux/Mac
openssl rand -base64 24

# On Windows (PowerShell)
[Convert]::ToBase64String((1..24 | ForEach-Object { Get-Random -Maximum 256 }))
```

### 3. Firewall Rules (Optional but Recommended)

Only allow connections from your cloud server IP:

**Windows Firewall**:
```powershell
# Run as Administrator in PowerShell
New-NetFirewallRule -DisplayName "SOCKS5 Proxy" -Direction Inbound -LocalPort 1080 -Protocol TCP -RemoteAddress 172.234.172.191 -Action Allow
```

**Linux (UFW)**:
```bash
sudo ufw allow from 172.234.172.191 to any port 1080
```

### 4. Monitor Connections

The proxy logs all connections. Watch for unusual activity:
- Connections from unexpected IPs
- High connection volume
- Connections to non-YouTube domains

## Troubleshooting

### "Address already in use"

Port 1080 is already being used. Either:
1. Stop the other service using port 1080
2. Use a different port: `node simple-proxy.js --port 1081`

### "Connection refused" from backend

1. **Check proxy is running**: Look for "Server running on port" message
2. **Check port forwarding**: Verify router configuration
3. **Check firewall**: Make sure port is open
4. **Test locally first**:
   ```bash
   curl --proxy socks5://127.0.0.1:1080 https://www.youtube.com
   ```

### Backend still getting bot detection

1. **Verify proxy is being used**: Check backend logs for proxy connection attempts
2. **Test your IP**: Visit https://whatismyipaddress.com from the proxy
3. **Clear YouTube cookies**: Your residential IP might already be flagged
4. **Try a different network**: Use mobile hotspot or different ISP

### Proxy crashes or disconnects

1. **Run with process manager** (keeps it running):
   ```bash
   npm install -g pm2
   pm2 start simple-proxy.js -- --port 1080 --auth user:pass
   pm2 save
   pm2 startup  # Follow the instructions
   ```

2. **Check system resources**: Proxy might run out of memory
3. **Monitor logs**: Look for error patterns

## Testing

### Test Local Connection

From your local machine:

```bash
# Install curl with socks support
# Then test:
curl --proxy socks5://127.0.0.1:1080 https://www.youtube.com
```

### Test Remote Connection

From your cloud server:

```bash
# Replace with your values
curl --proxy socks5://username:password@YOUR_PUBLIC_IP:1080 https://www.youtube.com
```

### Test Download

Try downloading a YouTube Short from your frontend. Check:
1. Backend logs show proxy connection
2. Download succeeds without bot detection
3. Proxy logs show connection to YouTube

## Running in Background

### Option 1: Using screen (simple)

```bash
screen -S proxy
node simple-proxy.js --port 1080 --auth user:pass
# Press Ctrl+A then D to detach
# Reconnect with: screen -r proxy
```

### Option 2: Using PM2 (recommended)

```bash
npm install -g pm2
pm2 start simple-proxy.js --name "ytd-proxy" -- --port 1080 --auth user:pass
pm2 save
pm2 startup  # Follow instructions to run on boot
```

View logs:
```bash
pm2 logs ytd-proxy
```

### Option 3: Using systemd (Linux)

Create `/etc/systemd/system/ytd-proxy.service`:

```ini
[Unit]
Description=YouTube Downloader Residential Proxy
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/local-proxy
ExecStart=/usr/bin/node simple-proxy.js --port 1080 --auth user:pass
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ytd-proxy
sudo systemctl start ytd-proxy
sudo systemctl status ytd-proxy
```

## Performance Tips

1. **Use wired connection**: More stable than WiFi
2. **Check bandwidth**: Proxy will use your upload bandwidth
3. **Monitor router**: Some routers throttle proxies
4. **Limit connections**: Add connection limits if needed

## Alternative: Cloud Residential Proxy Services

If you can't run a local proxy, consider paid services:

1. **Bright Data** (formerly Luminati): https://brightdata.com
   - Residential proxies with YouTube support
   - ~$500/month for basic plan

2. **Smartproxy**: https://smartproxy.com
   - Residential proxies
   - ~$80/month for 8GB

3. **Oxylabs**: https://oxylabs.io
   - Residential proxies
   - ~$300/month

Configure same way:
```bash
YT_DLP_PROXY=socks5://username:password@proxy.provider.com:port
```

## Support

If you encounter issues:

1. Check the proxy logs (visible in terminal)
2. Check backend logs: `sudo journalctl -u ytd-worker -f`
3. Verify router port forwarding
4. Test with curl commands above
5. Try a different port or network

## How It Works

```
User Browser (Frontend)
    ↓
Cloud Server (172.234.172.191)
    ↓ SOCKS5 connection
Your Home Computer (This Proxy) [Residential IP]
    ↓
YouTube Servers
```

The cloud server connects to your home proxy, which forwards requests to YouTube using your residential IP address. YouTube sees the request as coming from a residential user, not a datacenter.
