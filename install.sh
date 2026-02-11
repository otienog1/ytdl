#!/bin/bash

# YouTube Shorts Downloader - Installation Script
# This script automates the setup process

set -e

echo "🚀 YouTube Shorts Downloader - Installation Script"
echo "=================================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on supported OS
if [[ "$OSTYPE" != "linux-gnu"* ]] && [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}⚠️  This script is designed for Linux and macOS${NC}"
    echo "For Windows, please follow the manual setup in README.md"
    exit 1
fi

echo "Step 1: Checking prerequisites..."
echo "=================================="

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    echo "Please install Node.js 18+ from https://nodejs.org"
    exit 1
else
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}✅ Node.js ${NODE_VERSION} installed${NC}"
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
else
    NPM_VERSION=$(npm -v)
    echo -e "${GREEN}✅ npm ${NPM_VERSION} installed${NC}"
fi

# Check yt-dlp
if ! command -v yt-dlp &> /dev/null; then
    echo -e "${YELLOW}⚠️  yt-dlp is not installed${NC}"
    echo "Installing yt-dlp..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install yt-dlp
        else
            echo -e "${RED}❌ Homebrew not found. Please install yt-dlp manually${NC}"
            exit 1
        fi
    else
        sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
        sudo chmod a+rx /usr/local/bin/yt-dlp
    fi
    echo -e "${GREEN}✅ yt-dlp installed${NC}"
else
    echo -e "${GREEN}✅ yt-dlp installed${NC}"
fi

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}⚠️  ffmpeg is not installed${NC}"
    echo "Installing ffmpeg..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install ffmpeg
        else
            echo -e "${RED}❌ Homebrew not found. Please install ffmpeg manually${NC}"
            exit 1
        fi
    else
        sudo apt-get update
        sudo apt-get install -y ffmpeg
    fi
    echo -e "${GREEN}✅ ffmpeg installed${NC}"
else
    echo -e "${GREEN}✅ ffmpeg installed${NC}"
fi

echo ""
echo "Step 2: Installing dependencies..."
echo "==================================="

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
npm install
echo -e "${GREEN}✅ Backend dependencies installed${NC}"

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd ../frontend
npm install
echo -e "${GREEN}✅ Frontend dependencies installed${NC}"

cd ..

echo ""
echo "Step 3: Setting up environment files..."
echo "========================================"

# Backend .env
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo -e "${YELLOW}⚠️  Created backend/.env from example${NC}"
    echo -e "${YELLOW}   Please edit backend/.env with your configuration${NC}"
else
    echo -e "${GREEN}✅ backend/.env already exists${NC}"
fi

# Frontend .env.local
if [ ! -f frontend/.env.local ]; then
    cp frontend/.env.example frontend/.env.local
    echo -e "${YELLOW}⚠️  Created frontend/.env.local from example${NC}"
    echo -e "${YELLOW}   Please edit frontend/.env.local with your configuration${NC}"
else
    echo -e "${GREEN}✅ frontend/.env.local already exists${NC}"
fi

echo ""
echo "Step 4: Checking optional services..."
echo "======================================"

# Check MongoDB
if command -v mongod &> /dev/null; then
    echo -e "${GREEN}✅ MongoDB installed locally${NC}"
else
    echo -e "${YELLOW}⚠️  MongoDB not found locally${NC}"
    echo "   You can use MongoDB Atlas (recommended for production)"
    echo "   Or install locally: https://www.mongodb.com/try/download/community"
fi

# Check Redis
if command -v redis-server &> /dev/null; then
    echo -e "${GREEN}✅ Redis installed locally${NC}"
else
    echo -e "${YELLOW}⚠️  Redis not found locally${NC}"
    echo "   You can use Redis Cloud (recommended for production)"
    echo "   Or install locally:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "   brew install redis"
    else
        echo "   sudo apt-get install redis-server"
    fi
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${YELLOW}⚠️  Docker not found${NC}"
    echo "   Docker is optional but recommended for deployment"
    echo "   Install from: https://www.docker.com/get-started"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Configure backend/.env with your MongoDB, Redis, and GCS credentials"
echo "2. Configure frontend/.env.local with your API URL"
echo "3. Start the services:"
echo ""
echo "   Terminal 1 - Backend:"
echo "   cd backend && npm run dev"
echo ""
echo "   Terminal 2 - Frontend:"
echo "   cd frontend && npm run dev"
echo ""
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "For detailed instructions, see:"
echo "- QUICKSTART.md for quick setup"
echo "- README.md for full documentation"
echo "- DEPLOYMENT.md for production deployment"
echo ""
echo "Happy coding! 🎉"
