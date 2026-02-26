#!/bin/bash
# Script to test if YouTube cookies are valid

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
info()  { echo -e "${BLUE}[→]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

APP_DIR="/opt/ytdl"
COOKIES_FILE="$APP_DIR/youtube_cookies.txt"
TEST_URL="https://www.youtube.com/shorts/Y2c_QxlVK0Y"

echo ""
echo "============================================================"
echo "  YouTube Cookies Validation Test"
echo "============================================================"
echo ""

# Check if cookies file exists
if [ ! -f "$COOKIES_FILE" ]; then
    error "Cookies file not found at: $COOKIES_FILE"
    echo ""
    echo "Please upload your cookies file:"
    echo "  scp youtube_cookies.txt root@server:/opt/ytdl/youtube_cookies.txt"
    echo ""
    exit 1
fi

log "Cookies file exists: $COOKIES_FILE"

# Check file permissions
COOKIES_OWNER=$(stat -c '%U:%G' "$COOKIES_FILE")
COOKIES_PERMS=$(stat -c '%a' "$COOKIES_FILE")

info "Owner: $COOKIES_OWNER"
info "Permissions: $COOKIES_PERMS"

if [ "$COOKIES_OWNER" != "ytd:ytd" ]; then
    warn "Cookies file should be owned by ytd:ytd"
    info "Fix with: sudo chown ytd:ytd $COOKIES_FILE"
fi

if [ "$COOKIES_PERMS" != "640" ] && [ "$COOKIES_PERMS" != "644" ]; then
    warn "Cookies file permissions should be 640 or 644"
    info "Fix with: sudo chmod 640 $COOKIES_FILE"
fi

# Check if ytd user can read it
if sudo -u ytd test -r "$COOKIES_FILE"; then
    log "ytd user can read cookies file"
else
    error "ytd user CANNOT read cookies file"
    info "Fix with: sudo chown ytd:ytd $COOKIES_FILE && sudo chmod 640 $COOKIES_FILE"
    exit 1
fi

# Get venv path
cd "$APP_DIR"
VENV_PATH=$(pipenv --venv)

# Test cookies with yt-dlp
echo ""
info "Testing cookies with yt-dlp..."
echo ""

TEST_OUTPUT=$("$VENV_PATH/bin/yt-dlp" \
    --dump-json \
    --no-playlist \
    --cookies "$COOKIES_FILE" \
    --extractor-args "youtube:player_client=web" \
    "$TEST_URL" 2>&1)

if [ $? -eq 0 ]; then
    echo ""
    log "✓ COOKIES ARE VALID!"
    echo ""

    # Extract video title from JSON output
    VIDEO_TITLE=$(echo "$TEST_OUTPUT" | "$VENV_PATH/bin/python" -c "import sys, json; data = json.load(sys.stdin); print(data.get('title', 'Unknown'))" 2>/dev/null || echo "Unknown")

    info "Successfully fetched video: $VIDEO_TITLE"
    echo ""
    echo "Your cookies are working correctly. Downloads should succeed."
    echo ""
else
    echo ""
    error "COOKIES ARE INVALID OR EXPIRED"
    echo ""

    # Check if the error mentions cookies specifically
    if echo "$TEST_OUTPUT" | grep -q "cookies are no longer valid"; then
        warn "YouTube says: Cookies are no longer valid (rotated as security measure)"
        echo ""
        echo "You need to export fresh cookies from your browser."
        echo "See EXPORT_COOKIES_GUIDE.md for detailed instructions."
    elif echo "$TEST_OUTPUT" | grep -q "Sign in to confirm you're not a bot"; then
        warn "YouTube bot detection is still blocking requests"
        echo ""
        echo "Possible causes:"
        echo "  1. Cookies are expired - export fresh cookies"
        echo "  2. Server IP is heavily blocked - may need residential proxy"
    else
        warn "Unexpected error:"
        echo "$TEST_OUTPUT"
    fi
    echo ""
    exit 1
fi

echo "============================================================"
echo ""
