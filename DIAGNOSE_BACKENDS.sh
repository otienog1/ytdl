#!/bin/bash
# Diagnose backend server issues

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "Backend Server Diagnostics"
echo "=========================================="
echo ""

# Function to test endpoint
test_endpoint() {
    local server=$1
    local endpoint=$2
    local name=$3

    echo -e "${BLUE}Testing $name - $server$endpoint${NC}"

    # Test with curl
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$server$endpoint")
    http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE/d')

    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ Success (200 OK)${NC}"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    elif [ "$http_code" = "307" ]; then
        echo -e "${YELLOW}⚠ Redirect (307) - trying with trailing slash${NC}"
        curl -s "$server$endpoint/" | jq '.' 2>/dev/null || curl -s "$server$endpoint/"
    else
        echo -e "${RED}✗ Failed (HTTP $http_code)${NC}"
        echo "$body"
    fi
    echo ""
}

# Test local backend
echo -e "${BLUE}=== Server 1: Local Backend (127.0.0.1:3001) ===${NC}"
echo ""

# Check if service is running
if systemctl is-active --quiet ytd-api 2>/dev/null; then
    echo -e "${GREEN}✓ ytd-api service is running${NC}"
else
    echo -e "${RED}✗ ytd-api service is NOT running${NC}"
    echo "  Start with: sudo systemctl start ytd-api"
fi

# Check port
if netstat -tlnp 2>/dev/null | grep -q ":3001" || ss -tlnp 2>/dev/null | grep -q ":3001"; then
    echo -e "${GREEN}✓ Port 3001 is listening${NC}"
    netstat -tlnp 2>/dev/null | grep ":3001" || ss -tlnp 2>/dev/null | grep ":3001"
else
    echo -e "${RED}✗ Port 3001 is NOT listening${NC}"
fi
echo ""

# Test various endpoints
test_endpoint "http://127.0.0.1:3001" "/api/health" "Health endpoint (no slash)"
test_endpoint "http://127.0.0.1:3001" "/api/health/" "Health endpoint (with slash)"
test_endpoint "http://127.0.0.1:3001" "/health" "Root health endpoint"
test_endpoint "http://127.0.0.1:3001" "/" "Root endpoint"

# Check what routes are available
echo -e "${BLUE}Available API routes (from /docs):${NC}"
curl -s http://127.0.0.1:3001/docs 2>/dev/null | grep -o 'path="[^"]*"' | head -10 || echo "Could not fetch /docs"
echo ""
echo ""

# Test GCP backend
echo -e "${BLUE}=== Server 2: GCP Backend (34.57.68.120:3001) ===${NC}"
echo ""
test_endpoint "http://34.57.68.120:3001" "/api/health" "Health endpoint (no slash)"
test_endpoint "http://34.57.68.120:3001" "/api/health/" "Health endpoint (with slash)"

# Test AWS backend
echo -e "${BLUE}=== Server 3: AWS Backend (13.60.71.187:3001) ===${NC}"
echo ""
test_endpoint "http://13.60.71.187:3001" "/api/health" "Health endpoint (no slash)"
test_endpoint "http://13.60.71.187:3001" "/api/health/" "Health endpoint (with slash)"

echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "Correct endpoint appears to be: /api/health/"
echo "(Note the trailing slash)"
echo ""
echo "Local backend (127.0.0.1) seems to have different routes."
echo "Check: sudo journalctl -u ytd-api -n 50"
echo ""
