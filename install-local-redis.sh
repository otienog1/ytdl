#!/bin/bash

# ===================================================================
# Install Local Redis for Hybrid Redis Architecture
# ===================================================================
# This script installs and configures a local Redis instance on each
# server for fast, zero-latency Celery task processing.
#
# Usage: sudo bash install-local-redis.sh
# ===================================================================

set -e  # Exit on error

echo "============================================"
echo "Installing Local Redis for Celery"
echo "============================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (use sudo)"
    exit 1
fi

# Install Redis
echo ""
echo "[1/6] Installing Redis server..."
apt update
apt install -y redis-server

# Configure Redis to listen only on localhost (security)
echo ""
echo "[2/6] Configuring Redis for localhost-only access..."
sed -i 's/^bind .*/bind 127.0.0.1/' /etc/redis/redis.conf

# Disable Redis protected mode (safe since we're localhost-only)
sed -i 's/^protected-mode yes/protected-mode no/' /etc/redis/redis.conf

# Set max memory policy (optional but recommended)
echo "maxmemory 512mb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf

# Enable Redis systemd service
echo ""
echo "[3/6] Enabling Redis systemd service..."
systemctl enable redis-server

# Start Redis
echo ""
echo "[4/6] Starting Redis..."
systemctl restart redis-server

# Wait for Redis to start
sleep 2

# Test Redis connection
echo ""
echo "[5/6] Testing Redis connection..."
if redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis is running and responding!"
else
    echo "❌ ERROR: Redis is not responding"
    exit 1
fi

# Display Redis info
echo ""
echo "[6/6] Redis Information:"
echo "----------------------------------------"
redis-cli INFO server | grep "redis_version"
redis-cli INFO memory | grep "used_memory_human"
echo "Listening on: 127.0.0.1:6379"
echo "Max memory: 512MB"
echo "Eviction policy: allkeys-lru"
echo "----------------------------------------"

echo ""
echo "============================================"
echo "✅ Local Redis Installation Complete!"
echo "============================================"
echo ""
echo "Next Steps:"
echo "1. Copy the appropriate .env.server[1-3] file to .env:"
echo "   cd /opt/ytdl/backend-python"
echo "   sudo cp .env.server1 .env  # Or .env.server2/.env.server3"
echo ""
echo "2. Restart backend services:"
echo "   sudo systemctl restart ytd-api ytd-worker ytd-beat"
echo ""
echo "3. Verify services are using local Redis:"
echo "   sudo journalctl -u ytd-worker -f | grep 'Redis connected'"
echo ""
echo "4. Monitor local Redis connections:"
echo "   redis-cli INFO clients"
echo ""
