#!/bin/bash
echo "=== Checking LB Server Status ==="
ssh root@172.234.172.191 << 'EOFSSH'
echo "Latest worker logs:"
sudo journalctl -u ytd-worker --since "5 minutes ago" -n 50 --no-pager | tail -20

echo ""
echo "Active tasks:"
sudo systemctl status ytd-worker --no-pager | grep -A 5 "Main PID"

echo ""
echo "Redis connection test:"
redis-cli -h localhost -p 6379 ping 2>&1 || echo "Local Redis not responding"
EOFSSH

echo ""
echo "=== Checking AWS Server Status ==="
ssh root@13.60.71.187 << 'EOFSSH'
echo "Latest worker logs:"
sudo journalctl -u ytd-worker --since "5 minutes ago" -n 50 --no-pager | tail -20

echo ""
echo "Redis connection test:"
redis-cli -h localhost -p 6379 ping 2>&1 || echo "Local Redis not responding"
EOFSSH
