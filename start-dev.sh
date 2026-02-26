#!/bin/bash
# YouTube Downloader - Local Development Setup
# This script sets up and starts the development environment

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
info()  { echo -e "${BLUE}[→]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "============================================================"
echo "  YouTube Downloader - Local Development"
echo "============================================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    error "Python 3 is not installed. Please install Python 3.11+"
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
info "Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    info "Creating virtual environment..."
    python3 -m venv venv
    log "Virtual environment created"
else
    log "Virtual environment exists"
fi

# Activate virtual environment
info "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
info "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
log "Dependencies installed"

# Check .env file
if [ ! -f ".env" ]; then
    warn ".env file not found!"
    if [ -f ".env.example" ]; then
        info "Copying .env.example to .env..."
        cp .env.example .env
        echo ""
        warn "Please edit .env file with your configuration before continuing"
        echo "  Press Enter when ready..."
        read
    else
        error ".env file is required. Create one based on the README"
    fi
fi

# Start services
echo ""
info "Starting development services..."
echo ""

# Kill any existing processes on port 3001
if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    warn "Port 3001 is in use, killing existing process..."
    kill $(lsof -t -i:3001) 2>/dev/null || true
    sleep 2
fi

# Start FastAPI server in background
info "Starting FastAPI server on http://localhost:3001..."
uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload &
API_PID=$!

# Wait for API to start
sleep 3

# Start Celery worker in background
info "Starting Celery worker..."
celery -A app.queue.celery_app worker --loglevel=info --pool=solo &
CELERY_PID=$!

# Give services time to start
sleep 2

echo ""
log "Development environment is running!"
echo ""
echo "  API Server:    http://localhost:3001"
echo "  API Docs:      http://localhost:3001/docs"
echo "  Health Check:  http://localhost:3001/api/health/"
echo ""
echo "  API PID:       $API_PID"
echo "  Celery PID:    $CELERY_PID"
echo ""
echo "  Press Ctrl+C to stop all services"
echo ""

# Trap Ctrl+C to cleanup
cleanup() {
    echo ""
    info "Stopping services..."
    kill $API_PID 2>/dev/null || true
    kill $CELERY_PID 2>/dev/null || true
    log "Services stopped"
    exit 0
}
trap cleanup INT TERM

# Wait for user interrupt
wait
