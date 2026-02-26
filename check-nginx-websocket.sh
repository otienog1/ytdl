#!/bin/bash

# Script to check and display Nginx WebSocket configuration

echo "=== Checking Nginx Configuration for WebSocket Support ==="
echo ""

# Find Nginx config files
NGINX_CONF="/etc/nginx/sites-available/ytdl"
if [ ! -f "$NGINX_CONF" ]; then
    NGINX_CONF="/etc/nginx/conf.d/ytdl.conf"
fi

if [ ! -f "$NGINX_CONF" ]; then
    echo "ERROR: Could not find Nginx configuration file"
    echo "Please specify the location manually"
    exit 1
fi

echo "Found Nginx config: $NGINX_CONF"
echo ""

# Check if WebSocket upgrade headers are present
echo "=== Checking for WebSocket headers ==="
if grep -q "Upgrade.*http_upgrade" "$NGINX_CONF"; then
    echo "✓ Found Upgrade header configuration"
else
    echo "✗ Missing Upgrade header - WebSocket will not work!"
fi

if grep -q "Connection.*upgrade" "$NGINX_CONF"; then
    echo "✓ Found Connection upgrade header"
else
    echo "✗ Missing Connection upgrade header - WebSocket will not work!"
fi

echo ""
echo "=== Current /ws/ location block (if exists) ==="
grep -A 10 "location /ws/" "$NGINX_CONF" || echo "No /ws/ location block found"

echo ""
echo "=== Suggested WebSocket Configuration ==="
cat << 'EOF'

Add this to your Nginx configuration:

location /ws/ {
    proxy_pass http://localhost:3001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
}

EOF

echo ""
echo "=== To apply changes ==="
echo "1. Edit the Nginx config: sudo nano $NGINX_CONF"
echo "2. Test configuration: sudo nginx -t"
echo "3. Reload Nginx: sudo systemctl reload nginx"
echo "4. Restart backend: sudo systemctl restart ytdl-backend"
