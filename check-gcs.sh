#!/bin/bash
# Script to check Google Cloud Storage configuration

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
ENV_FILE="$APP_DIR/.env.production"

echo ""
echo "============================================================"
echo "  Google Cloud Storage Configuration Check"
echo "============================================================"
echo ""

# Check if .env.production exists
if [ ! -f "$ENV_FILE" ]; then
    error ".env.production not found at $ENV_FILE"
    exit 1
fi

# Source the environment file
set -a
source "$ENV_FILE"
set +a

info "Checking GCP configuration..."
echo ""

# Check if variables are set
if [ -z "$GCP_PROJECT_ID" ]; then
    error "GCP_PROJECT_ID is not set in .env.production"
else
    log "GCP_PROJECT_ID: $GCP_PROJECT_ID"
fi

if [ -z "$GCP_BUCKET_NAME" ]; then
    error "GCP_BUCKET_NAME is not set in .env.production"
else
    log "GCP_BUCKET_NAME: $GCP_BUCKET_NAME"
fi

if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    error "GOOGLE_APPLICATION_CREDENTIALS is not set in .env.production"
else
    log "GOOGLE_APPLICATION_CREDENTIALS: $GOOGLE_APPLICATION_CREDENTIALS"

    # Check if credentials file exists
    if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        log "Credentials file exists"

        # Check file permissions
        CREDS_OWNER=$(stat -c '%U' "$GOOGLE_APPLICATION_CREDENTIALS")
        CREDS_PERMS=$(stat -c '%a' "$GOOGLE_APPLICATION_CREDENTIALS")
        info "Credentials file owner: $CREDS_OWNER"
        info "Credentials file permissions: $CREDS_PERMS"

        # Check if ytd user can read it
        if sudo -u ytd test -r "$GOOGLE_APPLICATION_CREDENTIALS"; then
            log "ytd user can read credentials file"
        else
            error "ytd user CANNOT read credentials file"
            info "Fix with: sudo chmod 644 $GOOGLE_APPLICATION_CREDENTIALS"
        fi
    else
        error "Credentials file does NOT exist at: $GOOGLE_APPLICATION_CREDENTIALS"
        echo ""
        warn "Available JSON files in $APP_DIR:"
        find "$APP_DIR" -name "*.json" -type f 2>/dev/null || echo "  No JSON files found"
    fi
fi

echo ""
info "Testing GCS connection..."

# Test with Python
VENV_PATH=$(cd "$APP_DIR" && pipenv --venv)
TEST_RESULT=$("$VENV_PATH/bin/python" -c "
import os
import sys
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '$GOOGLE_APPLICATION_CREDENTIALS'
try:
    from google.cloud import storage
    client = storage.Client(project='$GCP_PROJECT_ID')
    bucket = client.bucket('$GCP_BUCKET_NAME')
    print(f'✓ Successfully connected to GCS bucket: {bucket.name}')
    sys.exit(0)
except Exception as e:
    print(f'✗ Failed to connect to GCS: {e}')
    sys.exit(1)
" 2>&1)

if [ $? -eq 0 ]; then
    log "$TEST_RESULT"
else
    error "$TEST_RESULT"
fi

echo ""
echo "============================================================"
echo "  Check complete"
echo "============================================================"
echo ""
