@echo off
echo ================================================
echo Checking All Services Status
echo ================================================
echo.

REM Check MongoDB
echo [1/3] Checking MongoDB...
netstat -ano | findstr :27017 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] MongoDB is RUNNING on port 27017
) else (
    echo [ERROR] MongoDB is NOT running
    echo Start MongoDB: net start MongoDB
)
echo.

REM Check Redis/Memurai
echo [2/3] Checking Redis/Memurai...
netstat -ano | findstr :6379 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Redis/Memurai is RUNNING on port 6379

    REM Test connection
    "C:\Program Files\Memurai\memurai-cli.exe" ping >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Redis is responding to commands

        REM Show queue length
        for /f %%i in ('"C:\Program Files\Memurai\memurai-cli.exe" LLEN celery') do set QUEUE_LEN=%%i
        echo [INFO] Celery queue length: %QUEUE_LEN%
    )
) else (
    echo [ERROR] Redis/Memurai is NOT running
    echo Start Memurai: net start Memurai
)
echo.

REM Check Backend Server
echo [3/3] Checking Backend Server...
netstat -ano | findstr :3001 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Backend server is RUNNING on port 3001
) else (
    echo [WARNING] Backend server is NOT running
    echo Start backend: cd backend-python ^&^& start-dev.bat
)
echo.

echo ================================================
echo Configuration Summary
echo ================================================
echo MongoDB: mongodb://localhost:27017/ytdl_db
echo Redis: redis://localhost:6379
echo Backend: http://localhost:3001
echo Frontend: http://localhost:3000
echo.

echo ================================================
echo All Systems Ready!
echo ================================================
echo.
echo Next Steps:
echo 1. Ensure backend is running: .\start-dev.bat
echo 2. Ensure Celery is running: pipenv run celery -A app.queue.celery_app worker --loglevel=info --pool=solo
echo 3. Ensure frontend is running: cd ..\frontend ^&^& npm run dev
echo.
pause
