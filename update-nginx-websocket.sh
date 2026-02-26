#!/bin/bash

# Script to update Nginx configuration for WebSocket support

set -e  # Exit on error

echo "=== Updating Nginx Configuration for WebSocket Support ==="
echo ""

# Backup existing config
NGINX_CONF="/etc/nginx/sites-available/ytd"
BACKUP_FILE="${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"

echo "1. Creating backup of existing config..."
sudo cp "$NGINX_CONF" "$BACKUP_FILE"
echo "   Backup created: $BACKUP_FILE"
echo ""

# Create new config with WebSocket support
echo "2. Creating new Nginx configuration..."
sudo tee "$NGINX_CONF" > /dev/null <<'EOF'
# YTD Nginx configuration with WebSocket support

server {
    server_name ytd.timobosafaris.com;

    # WebSocket endpoint - must be before general location block
    location /ws/ {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_connect_timeout 75s;
    }

    # General API endpoints
    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/ytd.timobosafaris.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/ytd.timobosafaris.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}

server {
    if ($host = ytd.timobosafaris.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

    listen 80;
    server_name ytd.timobosafaris.com;
    return 404; # managed by Certbot
}
EOF

echo "   ✓ New configuration created"
echo ""

# Test Nginx configuration
echo "3. Testing Nginx configuration..."
if sudo nginx -t; then
    echo "   ✓ Nginx configuration is valid"
    echo ""

    # Reload Nginx
    echo "4. Reloading Nginx..."
    sudo systemctl reload nginx
    echo "   ✓ Nginx reloaded successfully"
    echo ""

    echo "=== Update Complete ==="
    echo ""
    echo "WebSocket endpoint is now configured at: wss://ytd.timobosafaris.com/ws/"
    echo ""
    echo "To verify:"
    echo "  - Check Nginx status: sudo systemctl status nginx"
    echo "  - Check error logs: sudo tail -f /var/log/nginx/error.log"
    echo "  - Test WebSocket connection from frontend"
    echo ""
else
    echo "   ✗ Nginx configuration test failed!"
    echo ""
    echo "Restoring backup..."
    sudo cp "$BACKUP_FILE" "$NGINX_CONF"
    echo "   ✓ Backup restored"
    echo ""
    echo "Please check the error messages above and fix the configuration manually."
    exit 1
fi
