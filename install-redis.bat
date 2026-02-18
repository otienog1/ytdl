@echo off
echo ================================================
echo Redis Installation for Windows
echo ================================================
echo.
echo This script will guide you through installing Redis for local development.
echo.
echo Option 1: Install Redis using Chocolatey (Recommended)
echo   Requires: Chocolatey package manager
echo   Command: choco install redis-64
echo.
echo Option 2: Install Memurai (Redis for Windows)
echo   Download: https://www.memurai.com/get-memurai
echo   Native Windows Redis with service support
echo.
echo Option 3: Use WSL2 with Redis
echo   Install in WSL2: sudo apt install redis-server
echo.
echo ================================================
echo Checking if Chocolatey is available...
echo ================================================

where choco >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Chocolatey is installed!
    echo.
    echo Would you like to install Redis now? (Y/N)
    set /p INSTALL_CHOICE=

    if /i "%INSTALL_CHOICE%"=="Y" (
        echo.
        echo Installing Redis using Chocolatey...
        choco install redis-64 -y

        if %ERRORLEVEL% EQU 0 (
            echo.
            echo ================================================
            echo Redis installed successfully!
            echo ================================================
            echo.
            echo Starting Redis server...
            start "Redis Server" redis-server

            echo.
            echo Testing Redis connection...
            timeout /t 2 >nul
            redis-cli ping

            if %ERRORLEVEL% EQU 0 (
                echo.
                echo [SUCCESS] Redis is running!
                echo.
                echo Your .env file has been updated to use local Redis.
                echo Restart your backend and Celery worker now.
            ) else (
                echo.
                echo [WARNING] Could not connect to Redis
                echo Try starting it manually: redis-server
            )
        )
    )
) else (
    echo [INFO] Chocolatey not found
    echo.
    echo Install Chocolatey from: https://chocolatey.org/install
    echo Or download Memurai from: https://www.memurai.com/get-memurai
)

echo.
echo ================================================
echo Next Steps:
echo ================================================
echo 1. Ensure Redis is running (redis-cli ping should return PONG)
echo 2. Restart backend server: .\start-dev.bat
echo 3. Restart Celery worker: pipenv run celery -A app.queue.celery_app worker --loglevel=info --pool=solo
echo.
pause
