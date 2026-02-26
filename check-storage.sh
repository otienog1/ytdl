#!/bin/bash
# Script to check cloud storage configuration (GCS, Azure, AWS S3)

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
echo "  Cloud Storage Configuration Check"
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

# Get virtualenv path
VENV_PATH=$(cd "$APP_DIR" && ls -d .venv 2>/dev/null || echo "")
if [ -z "$VENV_PATH" ]; then
    error "Virtual environment not found in $APP_DIR"
    exit 1
fi
VENV_PATH="$APP_DIR/$VENV_PATH"

# ------------------------------------------------------------
# Check Google Cloud Storage
# ------------------------------------------------------------
if [ -n "$GCP_PROJECT_ID" ] || [ -n "$GCP_BUCKET_NAME" ]; then
    echo ""
    info "Checking Google Cloud Storage (GCS) configuration..."
    echo ""

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
        else
            error "Credentials file does NOT exist at: $GOOGLE_APPLICATION_CREDENTIALS"
        fi
    fi

    # Test GCS connection
    info "Testing GCS connection..."
    GCS_TEST=$("$VENV_PATH/bin/python" -c "
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '${GOOGLE_APPLICATION_CREDENTIALS}'
try:
    from google.cloud import storage
    client = storage.Client(project='${GCP_PROJECT_ID}')
    bucket = client.bucket('${GCP_BUCKET_NAME}')
    print('✓ Successfully connected to GCS bucket: ' + bucket.name)
except Exception as e:
    print('✗ Failed: ' + str(e))
    exit(1)
" 2>&1)

    if [ $? -eq 0 ]; then
        log "$GCS_TEST"
    else
        error "$GCS_TEST"
    fi
fi

# ------------------------------------------------------------
# Check Azure Blob Storage
# ------------------------------------------------------------
if [ -n "$AZURE_STORAGE_CONNECTION_STRING" ] || [ -n "$AZURE_CONTAINER_NAME" ]; then
    echo ""
    info "Checking Azure Blob Storage configuration..."
    echo ""

    if [ -z "$AZURE_STORAGE_CONNECTION_STRING" ]; then
        error "AZURE_STORAGE_CONNECTION_STRING is not set in .env.production"
    else
        log "AZURE_STORAGE_CONNECTION_STRING: [SET]"
    fi

    if [ -z "$AZURE_CONTAINER_NAME" ]; then
        error "AZURE_CONTAINER_NAME is not set in .env.production"
    else
        log "AZURE_CONTAINER_NAME: $AZURE_CONTAINER_NAME"
    fi

    # Test Azure connection
    info "Testing Azure Blob Storage connection..."
    AZURE_TEST=$("$VENV_PATH/bin/python" -c "
import os
os.environ['AZURE_STORAGE_CONNECTION_STRING'] = '${AZURE_STORAGE_CONNECTION_STRING}'
try:
    from azure.storage.blob import BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(os.environ['AZURE_STORAGE_CONNECTION_STRING'])
    container_client = blob_service_client.get_container_client('${AZURE_CONTAINER_NAME}')
    properties = container_client.get_container_properties()
    print('✓ Successfully connected to Azure container: ' + properties.name)
except Exception as e:
    print('✗ Failed: ' + str(e))
    exit(1)
" 2>&1)

    if [ $? -eq 0 ]; then
        log "$AZURE_TEST"
    else
        error "$AZURE_TEST"
    fi
fi

# ------------------------------------------------------------
# Check AWS S3
# ------------------------------------------------------------
if [ -n "$AWS_ACCESS_KEY_ID" ] || [ -n "$AWS_BUCKET_NAME" ]; then
    echo ""
    info "Checking AWS S3 configuration..."
    echo ""

    if [ -z "$AWS_ACCESS_KEY_ID" ]; then
        error "AWS_ACCESS_KEY_ID is not set in .env.production"
    else
        log "AWS_ACCESS_KEY_ID: [SET]"
    fi

    if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        error "AWS_SECRET_ACCESS_KEY is not set in .env.production"
    else
        log "AWS_SECRET_ACCESS_KEY: [SET]"
    fi

    if [ -z "$AWS_BUCKET_NAME" ]; then
        error "AWS_BUCKET_NAME is not set in .env.production"
    else
        log "AWS_BUCKET_NAME: $AWS_BUCKET_NAME"
    fi

    if [ -z "$AWS_REGION" ]; then
        warn "AWS_REGION is not set (will use default)"
    else
        log "AWS_REGION: $AWS_REGION"
    fi

    # Test S3 connection
    info "Testing AWS S3 connection..."
    S3_TEST=$("$VENV_PATH/bin/python" -c "
import os
os.environ['AWS_ACCESS_KEY_ID'] = '${AWS_ACCESS_KEY_ID}'
os.environ['AWS_SECRET_ACCESS_KEY'] = '${AWS_SECRET_ACCESS_KEY}'
try:
    import boto3
    s3_client = boto3.client('s3', region_name='${AWS_REGION:-us-east-1}')
    response = s3_client.head_bucket(Bucket='${AWS_BUCKET_NAME}')
    print('✓ Successfully connected to S3 bucket: ${AWS_BUCKET_NAME}')
except Exception as e:
    print('✗ Failed: ' + str(e))
    exit(1)
" 2>&1)

    if [ $? -eq 0 ]; then
        log "$S3_TEST"
    else
        error "$S3_TEST"
    fi
fi

# Summary
echo ""
echo "============================================================"
echo "  Check complete"
echo "============================================================"
echo ""

if [ -z "$GCP_PROJECT_ID" ] && [ -z "$AZURE_STORAGE_CONNECTION_STRING" ] && [ -z "$AWS_ACCESS_KEY_ID" ]; then
    warn "No cloud storage providers configured!"
    echo "  Configure at least one provider in .env.production:"
    echo "    - GCS: GCP_PROJECT_ID, GCP_BUCKET_NAME, GOOGLE_APPLICATION_CREDENTIALS"
    echo "    - Azure: AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME"
    echo "    - S3: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME, AWS_REGION"
fi
