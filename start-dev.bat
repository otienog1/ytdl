@echo off
REM YouTube Shorts Downloader - Start Development Servers
REM This script starts both backend and frontend servers

echo.
echo ============================================
echo YouTube Shorts Downloader - Development Mode
echo ============================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo Node.js found:
node -v
echo.

REM Check if npm is installed
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: npm is not installed or not in PATH
    pause
    exit /b 1
)

echo npm found:
npm -v
echo.

REM Check if yt-dlp is installed
where yt-dlp >nul 2>nul
if %errorlevel% neq 0 (
    echo WARNING: yt-dlp is not installed or not in PATH
    echo Video downloads will not work without yt-dlp
    echo Install from: https://github.com/yt-dlp/yt-dlp
    echo.
)

REM Check if ffmpeg is installed
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo WARNING: ffmpeg is not installed or not in PATH
    echo Video processing will not work without ffmpeg
    echo Install from: https://ffmpeg.org
    echo.
)

REM Check if backend dependencies are installed
if not exist "backend\node_modules\" (
    echo Installing backend dependencies...
    cd backend
    call npm install
    cd ..
    echo.
)

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules\" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
    echo.
)

REM Check if .env files exist
if not exist "backend\.env" (
    echo WARNING: backend\.env not found
    echo Creating from example...
    copy backend\.env.example backend\.env
    echo Please edit backend\.env with your configuration
    echo.
)

if not exist "frontend\.env.local" (
    echo WARNING: frontend\.env.local not found
    echo Creating from example...
    copy frontend\.env.example frontend\.env.local
    echo Please edit frontend\.env.local with your configuration
    echo.
)

echo.
echo Starting servers...
echo.
echo Backend will start on: http://localhost:3001
echo Frontend will start on: http://localhost:3000
echo.
echo Press Ctrl+C in each window to stop the servers
echo.
pause

REM Start backend in new window
start "YouTube Downloader - Backend" cmd /k "cd backend && npm run dev"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
start "YouTube Downloader - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================
echo Servers are starting in separate windows
echo ============================================
echo.
echo Backend: http://localhost:3001/health
echo Frontend: http://localhost:3000
echo.
echo Close those windows to stop the servers
echo.
pause
