# Your Proxy Setup - Quick Reference

## Your Configuration

- **Your Public IP**: `197.237.3.52`
- **Proxy Port**: `1080`
- **Username**: `ytd_user`
- **Password**: `ytdlPass@123`

## Step 1: Run the Proxy on Your Computer

Open a terminal and run:

```bash
cd local-proxy
npm install
node simple-proxy.js --port 1080 --auth ytd_user:ytdlPass@123
```

**Keep this terminal open!** You should see:

```
============================================================
  SOCKS5 Residential Proxy Server
============================================================

✓ Server running on port 1080

Local Network:
  socks5://ytd_user:ytdlPass@123@192.168.x.x:1080

Localhost:
  socks5://ytd_user:ytdlPass@123@127.0.0.1:1080

Next Steps:
  1. Make sure your router forwards port 1080 to this machine
  2. Get your public IP: curl ifconfig.me
  3. Use this on your server:
     YT_DLP_PROXY=socks5://ytd_user:ytdlPass@123@YOUR_PUBLIC_IP:1080

============================================================

Press Ctrl+C to stop
```

## Step 2: Configure Router Port Forwarding

1. Login to your router (usually http://192.168.1.1)
2. Find "Port Forwarding" or "Virtual Server" settings
3. Add this rule:
   - **External Port**: 1080
   - **Internal Port**: 1080
   - **Internal IP**: [Your computer's local IP shown when proxy starts]
   - **Protocol**: TCP
4. Save the settings

## Step 3: Update Backend Server

SSH to your server:

```bash
ssh root@172.234.172.191
```

Edit the backend configuration:

```bash
sudo nano /opt/ytd/backend-python/.env.production
```

Add this line (**NOTE**: The `@` in the password is URL-encoded as `%40`):

```bash
YT_DLP_PROXY=socks5://ytd_user:ytdlPass%40123@197.237.3.52:1080
```

Save the file (Ctrl+X, then Y, then Enter).

Restart the services:

```bash
sudo systemctl restart ytd-api ytd-worker
```

Check the services are running:

```bash
sudo systemctl status ytd-api
sudo systemctl status ytd-worker
```

## Step 4: Test

1. Go to https://ytd.timobosafaris.com
2. Try downloading a YouTube Short
3. Watch your proxy terminal for connection logs like:

```
[2026-02-09T18:30:45.123Z] Connection #1: www.youtube.com:443
[2026-02-09T18:30:47.456Z] Connection #2: i.ytimg.com:443
```

## Troubleshooting

### Test Proxy Locally

From your computer:

```bash
curl --proxy socks5://ytd_user:ytdlPass@123@127.0.0.1:1080 https://www.youtube.com
```

Should return HTML content.

### Test From Server

SSH to server and run:

```bash
ssh root@172.234.172.191
curl --proxy socks5://ytd_user:ytdlPass@123@197.237.3.52:1080 https://www.youtube.com
```

Should return HTML content. If it fails:

- Check proxy is running on your computer
- Check router port forwarding is configured
- Check your firewall allows port 1080

### Check Backend Logs

```bash
ssh root@172.234.172.191
sudo journalctl -u ytd-worker -f
```

Look for proxy connection attempts and any errors.

## Keep Proxy Running 24/7 (Optional)

Install PM2:

```bash
npm install -g pm2
```

Start proxy with PM2:

```bash
pm2 start simple-proxy.js --name "ytd-proxy" -- --port 1080 --auth ytd_user:ytdlPass@123
pm2 save
pm2 startup
```

View logs:

```bash
pm2 logs ytd-proxy
```

Stop proxy:

```bash
pm2 stop ytd-proxy
```

## Your Proxy URL (for reference)

```
socks5://ytd_user:ytdlPass%40123@197.237.3.52:1080
```

**Important**: The `@` symbol in the password (`ytdlPass@123`) must be URL-encoded as `%40` when used in the proxy URL.

This is what you add to the backend's `.env.production` file as `YT_DLP_PROXY`.

## Security Notes

1. Your proxy is protected with authentication (ytd_user:ytdlPass@123)
2. Only your server (172.234.172.191) should connect to it
3. Monitor the connection logs for any suspicious activity
4. If you see unexpected connections, stop the proxy immediately

## Quick Commands

**Start proxy**:

```bash
cd local-proxy
node simple-proxy.js --port 1080 --auth ytd_user:ytdlPass@123
```

**Start with PM2 (background)**:

```bash
pm2 start simple-proxy.js --name "ytd-proxy" -- --port 1080 --auth ytd_user:ytdlPass@123
```

**View PM2 logs**:

```bash
pm2 logs ytd-proxy
```

**Restart backend services**:

```bash
ssh root@172.234.172.191
sudo systemctl restart ytd-api ytd-worker
```

**Check backend logs**:

```bash
ssh root@172.234.172.191
sudo journalctl -u ytd-worker -f
```

## Expected Behavior

When everything is working:

1. You run the proxy on your computer → See "Server running on port 1080"
2. User downloads video on frontend → Backend connects to your proxy
3. Your proxy terminal shows → "Connection #X: www.youtube.com:443"
4. Download succeeds → User gets the video file

If bot detection still occurs:

- Wait 5-10 minutes (YouTube may cache your IP's status)
- Verify proxy URL in backend .env.production is correct
- Check backend logs for connection errors
- Try a different YouTube Short video
