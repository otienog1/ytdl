#!/bin/bash

# YouTube Shorts Downloader - Start Development Servers
# This script starts both backend and frontend servers

set -e

echo ""
echo "============================================"
echo "YouTube Shorts Downloader - Development Mode"
echo "============================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}ERROR: Node.js is not installed${NC}"
    echo "Please install Node.js from https://nodejs.org"
    exit 1
fi

echo -e "${GREEN}Node.js found:${NC}"
node -v
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}ERROR: npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}npm found:${NC}"
npm -v
echo ""

# Check if yt-dlp is installed
if ! command -v yt-dlp &> /dev/null; then
    echo -e "${YELLOW}WARNING: yt-dlp is not installed${NC}"
    echo "Video downloads will not work without yt-dlp"
    echo "Install from: https://github.com/yt-dlp/yt-dlp"
    echo ""
fi

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}WARNING: ffmpeg is not installed${NC}"
    echo "Video processing will not work without ffmpeg"
    echo "Install from: https://ffmpeg.org"
    echo ""
fi

# Install backend dependencies if needed
if [ ! -d "backend/node_modules" ]; then
    echo "Installing backend dependencies..."
    cd backend
    npm install
    cd ..
    echo ""
fi

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    echo ""
fi

# Check if .env files exist
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}WARNING: backend/.env not found${NC}"
    echo "Creating from example..."
    cp backend/.env.example backend/.env
    echo "Please edit backend/.env with your configuration"
    echo ""
fi

if [ ! -f "frontend/.env.local" ]; then
    echo -e "${YELLOW}WARNING: frontend/.env.local not found${NC}"
    echo "Creating from example..."
    cp frontend/.env.example frontend/.env.local
    echo "Please edit frontend/.env.local with your configuration"
    echo ""
fi

echo ""
echo "============================================"
echo "Starting servers..."
echo "============================================"
echo ""
echo "Backend will start on: http://localhost:3001"
echo "Frontend will start on: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set up trap to catch Ctrl+C
trap cleanup INT TERM

# Start backend in background
cd backend
npm run dev &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend in background
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "============================================"
echo -e "${GREEN}Servers are running!${NC}"
echo "============================================"
echo ""
echo "Backend: http://localhost:3001/health"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
