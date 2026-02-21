#!/bin/bash
# Diagnose why you have 26 Redis connections on one server

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "========================================================================"
echo -e "${CYAN}Redis Connection Diagnostics${NC}"
echo "========================================================================"
echo ""

echo -e "${BLUE}1. Checking Celery worker concurrency...${NC}"
if systemctl status ytd-worker | grep -q "concurrency=2"; then
    echo -e "   ${RED}⚠️  FOUND: --concurrency=2${NC}"
    echo -e "   ${YELLOW}This uses ~12 connections instead of ~6${NC}"
    echo -e "   ${YELLOW}Fix: Run fix-redis-connections.sh to reduce to concurrency=1${NC}"
elif systemctl status ytd-worker | grep -q "concurrency=1"; then
    echo -e "   ${GREEN}✓ OK: --concurrency=1${NC}"
else
    echo -e "   ${YELLOW}⚠️  Could not determine concurrency${NC}"
fi
echo ""

echo -e "${BLUE}2. Checking for multiple Celery worker processes...${NC}"
CELERY_COUNT=$(ps aux | grep -E "celery.*worker" | grep -v grep | wc -l)
echo -e "   Celery worker processes: ${CELERY_COUNT}"
if [ "$CELERY_COUNT" -gt 2 ]; then
    echo -e "   ${RED}⚠️  WARNING: More than 2 celery processes found!${NC}"
    echo -e "   ${YELLOW}Each process uses separate connections${NC}"
    ps aux | grep -E "celery.*worker" | grep -v grep
else
    echo -e "   ${GREEN}✓ OK: Normal process count${NC}"
fi
echo ""

echo -e "${BLUE}3. Checking active WebSocket connections...${NC}"
WS_COUNT=$(netstat -an 2>/dev/null | grep -E ":3001.*ESTABLISHED" | wc -l || ss -an 2>/dev/null | grep -E ":3001.*ESTAB" | wc -l)
echo -e "   Active WebSocket connections: ${WS_COUNT}"
if [ "$WS_COUNT" -gt 5 ]; then
    echo -e "   ${YELLOW}⚠️  Many WebSocket connections (each uses 1 Redis connection)${NC}"
else
    echo -e "   ${GREEN}✓ OK: Low WebSocket count${NC}"
fi
echo ""

echo -e "${BLUE}4. Checking running ytd services...${NC}"
for service in ytd-api ytd-worker ytd-beat; do
    if systemctl is-active --quiet $service; then
        echo -e "   ${GREEN}✓ $service is running${NC}"
    else
        echo -e "   ${RED}✗ $service is NOT running${NC}"
    fi
done
echo ""

echo -e "${BLUE}5. Checking code version (connection leak fix)...${NC}"
if grep -q "def close(self):" /opt/ytdl/backend-python/app/services/cookie_refresh_service.py 2>/dev/null; then
    echo -e "   ${GREEN}✓ Connection leak fix is present in code${NC}"
else
    echo -e "   ${RED}✗ Connection leak fix NOT found - need to git pull${NC}"
fi
echo ""

echo "========================================================================"
echo -e "${CYAN}CONNECTION BREAKDOWN ESTIMATE${NC}"
echo "========================================================================"
echo ""

# Calculate expected connections
MAIN_REDIS=5
CELERY_BROKER=5
CELERY_BACKEND=3
WEBSOCKET_MGR=2
COOKIE_SVC=1
WEBSOCKET_PUBSUB=$WS_COUNT

TOTAL=$((MAIN_REDIS + CELERY_BROKER + CELERY_BACKEND + WEBSOCKET_MGR + COOKIE_SVC + WEBSOCKET_PUBSUB))

echo "Estimated connection breakdown:"
echo -e "  Main async Redis client:       ~${MAIN_REDIS} connections"
echo -e "  Celery broker:                 ~${CELERY_BROKER} connections"
echo -e "  Celery result backend:         ~${CELERY_BACKEND} connections"
echo -e "  WebSocket manager:             ~${WEBSOCKET_MGR} connections ${RED}(LEAKED)${NC}"
echo -e "  Cookie refresh service:        ~${COOKIE_SVC} connection ${RED}(LEAKED)${NC}"
echo -e "  WebSocket pub/sub clients:     ~${WEBSOCKET_PUBSUB} connections"
echo "  ────────────────────────────────────────────"
echo -e "  ${CYAN}TOTAL ESTIMATE:                ~${TOTAL} connections${NC}"
echo ""

echo "========================================================================"
echo -e "${CYAN}RECOMMENDED ACTIONS${NC}"
echo "========================================================================"
echo ""

if ! grep -q "def close(self):" /opt/ytdl/backend-python/app/services/cookie_refresh_service.py 2>/dev/null; then
    echo -e "${YELLOW}1. DEPLOY CONNECTION LEAK FIX (HIGH PRIORITY)${NC}"
    echo "   $ cd /opt/ytdl/backend-python"
    echo "   $ sudo git pull origin main"
    echo "   $ sudo systemctl restart ytd-api ytd-worker ytd-beat"
    echo ""
    echo -e "   ${GREEN}Expected reduction: 26 → 16-20 connections${NC}"
    echo ""
fi

if systemctl status ytd-worker 2>/dev/null | grep -q "concurrency=2"; then
    echo -e "${YELLOW}2. REDUCE CELERY CONCURRENCY (HIGH PRIORITY)${NC}"
    echo "   $ cd /opt/ytdl/backend-python"
    echo "   $ sudo bash fix-redis-connections.sh"
    echo ""
    echo -e "   ${GREEN}Expected reduction: ~6 fewer connections${NC}"
    echo ""
fi

echo -e "${BLUE}3. MONITOR AFTER FIXES${NC}"
echo "   $ watch -n 5 'redis-cli -h redis-17684.c10.us-east-1-3.ec2.cloud.redislabs.com \\"
echo "     -p 17684 -a tAS7YHDkYRe3sOXjHagnZzFfw0bsY7YM \\"
echo "     INFO clients | grep connected_clients'"
echo ""

echo -e "${BLUE}4. LONG-TERM: SELF-HOST REDIS (RECOMMENDED)${NC}"
echo "   See REDIS_CONNECTION_ANALYSIS.md for setup instructions"
echo ""

echo "========================================================================"
echo -e "${CYAN}WHY 26 CONNECTIONS?${NC}"
echo "========================================================================"
echo ""

echo "Most likely causes:"
echo ""
echo "  1. ${RED}Connection leaks${NC} - CookieRefreshService and WebSocketManager"
echo "     never close their Redis clients (~2-3 leaked connections)"
echo ""
echo "  2. ${RED}Celery concurrency=2${NC} - Uses 2x the connections"
echo "     (~6 extra connections compared to concurrency=1)"
echo ""
echo "  3. ${YELLOW}Connection pools larger than needed${NC} - Celery broker pool"
echo "     limit is 5, but with concurrency=2, uses ~10 connections"
echo ""
echo "  4. ${YELLOW}Active WebSocket connections${NC} - Each frontend WebSocket"
echo "     creates 1 Redis pub/sub connection"
echo ""

echo "========================================================================"
echo ""
