#!/bin/bash

# ===================================================================
# WebSocket Connection Diagnostic Script
# ===================================================================
# This script diagnoses WebSocket connection issues
#
# Usage: bash diagnose-websocket.sh
# ===================================================================

echo "========================================================================"
echo "WebSocket Connection Diagnostics"
echo "========================================================================"

# Check nginx configuration
echo ""
echo "[1/6] Checking nginx configuration..."
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx configuration valid"
else
    echo "❌ Nginx configuration has errors:"
    nginx -t
fi

# Check nginx is running
echo ""
echo "[2/6] Checking nginx status..."
if systemctl is-active nginx &> /dev/null; then
    echo "✅ Nginx is running"
else
    echo "❌ Nginx is NOT running"
    systemctl status nginx
fi

# Check backend services
echo ""
echo "[3/6] Checking backend services..."
for service in ytd-api ytd-worker ytd-beat; do
    if systemctl is-active $service &> /dev/null; then
        echo "✅ $service is running"
    else
        echo "❌ $service is NOT running"
    fi
done

# Check if backend responds to HTTP
echo ""
echo "[4/6] Testing HTTP health endpoint..."
if curl -s -I http://localhost:3001/api/health/ | grep -q "200 OK"; then
    echo "✅ Backend HTTP responding"
else
    echo "❌ Backend HTTP NOT responding"
    curl -I http://localhost:3001/api/health/
fi

# Check WebSocket endpoint from localhost
echo ""
echo "[5/6] Testing WebSocket upgrade on localhost..."
response=$(curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
    -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test" \
    http://localhost:3001/ws/download/test 2>&1)

if echo "$response" | grep -q "101 Switching Protocols\|426 Upgrade Required"; then
    echo "✅ Backend WebSocket endpoint responding"
else
    echo "❌ Backend WebSocket endpoint NOT responding"
    echo "$response" | head -20
fi

# Check nginx upstream configuration
echo ""
echo "[6/6] Checking nginx upstream servers..."
echo "Configured servers:"
grep -A 10 "upstream ytd_backend" /etc/nginx/sites-available/ytd | grep "server "

echo ""
echo "Testing connectivity to each backend:"
for server in "127.0.0.1:3001" "34.57.68.120:3001" "13.60.71.187:3001"; do
    if timeout 5 bash -c "echo > /dev/tcp/${server%:*}/${server#*:}" 2>/dev/null; then
        echo "✅ $server is reachable"
    else
        echo "❌ $server is NOT reachable"
    fi
done

echo ""
echo "========================================================================"
echo "Diagnostic Summary"
echo "========================================================================"

# Provide recommendations
echo ""
echo "Common Issues:"
echo "1. Backend not running → sudo systemctl start ytd-api"
echo "2. Wrong nginx config → Check /etc/nginx/sites-available/ytd"
echo "3. Backend IP changed → Update upstream ytd_backend in nginx"
echo "4. Firewall blocking → Check ufw/iptables"
echo ""
echo "Check logs:"
echo "  Backend: sudo journalctl -u ytd-api -n 50"
echo "  Nginx:   sudo tail -f /var/log/nginx/ytd-lb-error.log"
echo ""
