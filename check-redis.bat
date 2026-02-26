@echo off
echo ================================================
echo Checking Redis Status...
echo ================================================
echo.

REM Check if redis-cli is available
where redis-cli >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] redis-cli not found!
    echo.
    echo Redis may not be installed or not in PATH.
    echo.
    echo Install Redis:
    echo   - Chocolatey: choco install redis-64
    echo   - Memurai: https://www.memurai.com/get-memurai
    echo   - WSL2: sudo apt install redis-server
    echo.
    pause
    exit /b 1
)

echo [OK] redis-cli found
echo.

echo ================================================
echo Testing Connection to localhost:6379...
echo ================================================
redis-cli -h localhost -p 6379 ping >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Redis is RUNNING and responding
    echo.

    echo ================================================
    echo Redis Info:
    echo ================================================
    redis-cli -h localhost -p 6379 INFO server | findstr "redis_version"
    redis-cli -h localhost -p 6379 INFO clients | findstr "connected_clients"

    echo.
    echo ================================================
    echo Celery Queues:
    echo ================================================
    echo Celery queue length:
    redis-cli -h localhost -p 6379 LLEN celery

    echo.
    echo [SUCCESS] Redis is ready for use!
) else (
    echo [ERROR] Cannot connect to Redis at localhost:6379
    echo.
    echo Redis may not be running. Try:
    echo   - Start Redis: redis-server
    echo   - Or if installed as service: net start Redis
    echo.
    echo Check if port 6379 is in use:
    netstat -ano | findstr :6379
)

echo.
echo ================================================
echo Configuration:
echo ================================================
echo REDIS_URL: redis://localhost:6379
echo CELERY_BROKER_URL: redis://localhost:6379/0
echo CELERY_RESULT_BACKEND: redis://localhost:6379/0
echo.
pause
