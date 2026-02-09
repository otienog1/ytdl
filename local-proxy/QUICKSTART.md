# Quick Start - Residential Proxy Setup

Get your proxy running in 5 minutes.

## 1. Install Dependencies

```bash
cd local-proxy
npm install
```

## 2. Start the Proxy

```bash
node simple-proxy.js --port 1080 --auth myuser:mypass123
```

Replace `myuser:mypass123` with your own credentials.

**Keep this terminal open!** The proxy runs in the foreground.

## 3. Get Your Public IP

Open a new terminal and run:

```bash
curl ifconfig.me
```

Save this IP address (e.g., `203.0.113.45`).

## 4. Setup Port Forwarding

1. Go to your router admin (usually http://192.168.1.1)
2. Find "Port Forwarding" settings
3. Forward external port `1080` to your local machine's IP on port `1080`
4. Save the settings

**Your local IP is shown when the proxy starts** (e.g., `192.168.1.100`).

## 5. Configure Backend Server

SSH into your cloud server:

```bash
ssh root@172.234.172.191
```

Edit the backend config:

```bash
sudo nano /opt/ytd/backend-python/.env.production
```

Add this line (replace with your values):

```bash
YT_DLP_PROXY=socks5://myuser:mypass123@YOUR_PUBLIC_IP:1080
```

Example:
```bash
YT_DLP_PROXY=socks5://myuser:mypass123@203.0.113.45:1080
```

Save (Ctrl+X, Y, Enter) and restart services:

```bash
sudo systemctl restart ytd-api ytd-worker
```

## 6. Test

Go to your frontend (https://ytd.timobosafaris.com) and try downloading a YouTube Short.

Check proxy terminal for connection logs.

## Troubleshooting

**"Connection refused"**:
- Check port forwarding is correct
- Verify proxy is running
- Test locally: `curl --proxy socks5://127.0.0.1:1080 https://youtube.com`

**"Still getting bot detection"**:
- Wait 5-10 minutes after configuring
- Check backend logs: `sudo journalctl -u ytd-worker -f`
- Verify proxy URL in .env.production is correct

**"Address already in use"**:
- Use different port: `node simple-proxy.js --port 1081 --auth user:pass`
- Update backend .env.production to match

## Keep Proxy Running in Background

Install PM2:

```bash
npm install -g pm2
pm2 start simple-proxy.js --name "ytd-proxy" -- --port 1080 --auth myuser:mypass123
pm2 save
pm2 startup  # Follow instructions
```

View logs:
```bash
pm2 logs ytd-proxy
```

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Set up firewall rules for additional security
- Monitor connection logs for suspicious activity

---

That's it! Your residential proxy should now be routing YouTube requests through your home internet connection.
