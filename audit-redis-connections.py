#!/usr/bin/env python3
"""
Redis Connection Audit Script

This script analyzes all Redis clients in the application to understand
where connections are being created.

Run: python3 audit-redis-connections.py
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.settings import settings

print("=" * 80)
print("REDIS CONNECTION AUDIT")
print("=" * 80)
print()

print("Environment Variables:")
print(f"  REDIS_URL: {settings.REDIS_URL}")
print(f"  CELERY_BROKER_URL: {settings.CELERY_BROKER_URL}")
print(f"  CELERY_RESULT_BACKEND: {settings.CELERY_RESULT_BACKEND}")
print()

print("=" * 80)
print("EXPECTED CONNECTION SOURCES (Before Fix):")
print("=" * 80)
print()

print("1. Main Async Redis Client (redis_client.py)")
print("   - Type: Async redis client")
print("   - Pool: max_connections=10")
print("   - Usage: FastAPI async operations")
print("   - Expected active connections: ~3-5")
print()

print("2. Celery Broker (celery_app.py)")
print("   - Type: Redis connection for message broker")
print("   - Pool: broker_pool_limit=5, max_connections=5")
print("   - Usage: Task queue")
print("   - Expected connections: ~3-5")
print()

print("3. Celery Result Backend (celery_app.py)")
print("   - Type: Redis connection for results")
print("   - Pool: result_backend max_connections=5")
print("   - Usage: Task results storage")
print("   - Expected connections: ~2-3")
print()

print("4. WebSocket Manager (websocket/__init__.py)")
print("   - Type: Sync redis client")
print("   - Pool: None (implicit connection pool)")
print("   - Usage: Publishing WebSocket updates")
print("   - Expected connections: ~1-2")
print("   - ⚠️  LEAKED - Never closed until fix deployed")
print()

print("5. Cookie Refresh Service (cookie_refresh_service.py)")
print("   - Type: Sync redis client")
print("   - Pool: None (implicit connection pool)")
print("   - Usage: Creating Bull queue jobs")
print("   - Expected connections: ~1")
print("   - ⚠️  LEAKED - Never closed until fix deployed")
print()

print("6. WebSocket Routes (routes/websocket_routes.py)")
print("   - Type: Sync redis client per WebSocket connection")
print("   - Pool: None")
print("   - Usage: Subscribing to Redis pub/sub")
print("   - Expected connections: 1 per active WebSocket")
print("   - ✅ Properly closed in finally block")
print()

print("=" * 80)
print("THEORETICAL CONNECTION MATH:")
print("=" * 80)
print()

print("WITHOUT Active WebSocket Connections:")
print("  Main Async Client:        ~3-5 connections")
print("  Celery Broker:             ~3-5 connections")
print("  Celery Result Backend:     ~2-3 connections")
print("  WebSocket Manager:         ~1-2 connections (LEAKED)")
print("  Cookie Refresh Service:    ~1 connection (LEAKED)")
print("  ─────────────────────────────────────────")
print("  TOTAL:                     ~10-16 connections")
print()

print("WITH Active WebSocket Connections (e.g., 5 clients):")
print("  Base connections:          ~10-16 connections")
print("  WebSocket pub/sub clients: ~5 connections (1 per client)")
print("  ─────────────────────────────────────────")
print("  TOTAL:                     ~15-21 connections")
print()

print("=" * 80)
print("YOUR ACTUAL COUNT: 26 connections")
print("=" * 80)
print()

print("ANALYSIS:")
print("  26 connections is HIGHER than expected (~10-16 base).")
print()
print("Possible causes:")
print("  1. ⚠️  Connection pool bloat - Celery may be using more connections")
print("     than configured due to worker concurrency")
print()
print("  2. ⚠️  Active WebSocket connections - Check if frontend has open")
print("     WebSocket connections (~10 active connections = 26 total)")
print()
print("  3. ⚠️  Celery worker concurrency - If concurrency=2, Celery uses")
print("     more connections (2x the pool)")
print()
print("  4. ⚠️  Multiple Celery processes - Check if multiple ytd-worker")
print("     services are running")
print()

print("=" * 80)
print("DIAGNOSTICS TO RUN ON SERVER:")
print("=" * 80)
print()

print("1. Check Celery worker concurrency:")
print("   $ sudo systemctl status ytd-worker | grep concurrency")
print("   Expected: --concurrency=1")
print()

print("2. Check for multiple worker processes:")
print("   $ ps aux | grep celery")
print("   Should see only 1-2 celery processes")
print()

print("3. Check active WebSocket connections:")
print("   $ sudo netstat -an | grep :3001 | grep ESTABLISHED | wc -l")
print("   Each WebSocket = 1 Redis pub/sub connection")
print()

print("4. Check if ytd services are running:")
print("   $ sudo systemctl status ytd-api ytd-worker ytd-beat")
print()

print("5. Count Redis CLIENT LIST (requires connection):")
print("   $ redis-cli -h ... -p ... -a ... CLIENT LIST | wc -l")
print("   Shows exact client count")
print()

print("=" * 80)
print("RECOMMENDED FIXES:")
print("=" * 80)
print()

print("SHORT-TERM FIX (Deploy connection leak fix):")
print("  $ cd /opt/ytdl/backend-python")
print("  $ sudo git pull origin main")
print("  $ sudo systemctl restart ytd-api ytd-worker ytd-beat")
print()
print("  Expected reduction: 26 → 14-18 connections")
print()

print("MEDIUM-TERM FIX (Reduce Celery pool sizes):")
print("  Edit app/queue/celery_app.py:")
print("    broker_pool_limit=3  # was 5")
print("    max_connections=3    # was 5")
print()
print("  Expected reduction: 14-18 → 10-14 connections")
print()

print("LONG-TERM FIX (Self-host Redis):")
print("  $ sudo apt install redis-server")
print("  $ sudo nano /opt/ytdl/.env.production")
print("    REDIS_URL=redis://localhost:6379/0")
print("    CELERY_BROKER_URL=redis://localhost:6379/0")
print("    CELERY_RESULT_BACKEND=redis://localhost:6379/0")
print("  $ sudo systemctl restart ytd-api ytd-worker ytd-beat")
print()
print("  Result: Unlimited connections ✅")
print()

print("=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print()
print("1. Run diagnostics on server (commands above)")
print("2. Deploy connection leak fix immediately")
print("3. Monitor connection count for 1 hour")
print("4. If still > 20, reduce Celery pool sizes")
print("5. If planning multi-server, self-host Redis")
print()
