#!/bin/bash

echo "Starting YouTube Shorts Downloader Python Backend..."
echo ""

# Check if using pipenv or venv
if command -v pipenv &> /dev/null; then
    echo "Using pipenv..."
    USE_PIPENV=1
else
    echo "Using venv..."
    USE_PIPENV=0
fi

if [ $USE_PIPENV -eq 0 ]; then
    # Standard venv setup
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    echo "Activating virtual environment..."
    source venv/bin/activate

    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    # Pipenv setup
    echo "Installing dependencies with pipenv..."
    pipenv install
fi

# Setup local ffmpeg if not already done
if [ ! -f "bin/ffmpeg" ]; then
    echo ""
    echo "Setting up local ffmpeg binaries..."
    if [ $USE_PIPENV -eq 1 ]; then
        pipenv run python setup_ffmpeg.py
    else
        python setup_ffmpeg.py
    fi
fi

echo ""
echo "========================================"
echo "Starting FastAPI server on port 3001..."
echo "========================================"
echo ""

# Start FastAPI server in background
if [ $USE_PIPENV -eq 1 ]; then
    pipenv run uvicorn app.main:app --reload --port 3001 &
else
    uvicorn app.main:app --reload --port 3001 &
fi
FASTAPI_PID=$!

# Wait a moment for server to start
sleep 3

echo ""
echo "========================================"
echo "Starting Celery worker..."
echo "========================================"
echo ""

# Start Celery worker in background
if [ $USE_PIPENV -eq 1 ]; then
    pipenv run celery -A app.queue.celery_app worker --loglevel=info &
else
    celery -A app.queue.celery_app worker --loglevel=info &
fi
CELERY_PID=$!

echo ""
echo "========================================"
echo "Backend services started!"
echo "========================================"
echo "FastAPI Server: http://localhost:3001"
echo "API Docs: http://localhost:3001/docs"
echo "FastAPI PID: $FASTAPI_PID"
echo "Celery PID: $CELERY_PID"
echo ""
echo "Press Ctrl+C to stop all services..."

# Handle shutdown
trap "echo 'Stopping services...'; kill $FASTAPI_PID $CELERY_PID; exit" INT TERM

# Wait for processes
wait
