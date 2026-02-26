@echo off
REM YouTube Downloader - Local Development Setup (Windows)
REM This script sets up and starts the development environment

echo.
echo ============================================================
echo   YouTube Downloader - Local Development
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.11+
    pause
    exit /b 1
)

echo [OK] Python is installed

REM Create virtual environment
if not exist "venv\" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)

REM Activate virtual environment and install dependencies
echo [INFO] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo [OK] Dependencies installed

REM Check .env file
if not exist ".env" (
    echo [WARNING] .env file not found!
    if exist ".env.example" (
        echo [INFO] Copying .env.example to .env...
        copy .env.example .env
        echo.
        echo [WARNING] Please edit .env file with your configuration
        echo Press any key to continue...
        pause >nul
    ) else (
        echo [ERROR] .env file is required. Create one based on the README
        pause
        exit /b 1
    )
)

REM Kill existing processes on port 3001
echo [INFO] Checking for processes on port 3001...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3001') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Start services
echo.
echo [INFO] Starting development services...
echo.

REM Start FastAPI server
echo [INFO] Starting FastAPI server on http://localhost:3001...
start "FastAPI Server" cmd /c "venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload"

REM Wait a bit for API to start
timeout /t 3 /nobreak >nul

REM Start Celery worker
echo [INFO] Starting Celery worker...
start "Celery Worker" cmd /c "venv\Scripts\activate && celery -A app.queue.celery_app worker --loglevel=info --pool=solo"

REM Wait for services to fully start
timeout /t 2 /nobreak >nul

echo.
echo [OK] Development environment is running!
echo.
echo   API Server:    http://localhost:3001
echo   API Docs:      http://localhost:3001/docs
echo   Health Check:  http://localhost:3001/api/health/
echo.
echo   Close the command windows to stop the services
echo.
pause
