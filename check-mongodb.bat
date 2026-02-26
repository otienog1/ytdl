@echo off
echo ================================================
echo Checking MongoDB Status...
echo ================================================
echo.

REM Check if MongoDB service is running
sc query MongoDB | findstr "RUNNING" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] MongoDB service is RUNNING
) else (
    echo [WARNING] MongoDB service is NOT running
    echo.
    echo To start MongoDB service, run:
    echo   net start MongoDB
    echo.
    echo Or if MongoDB is not installed as a service, start it manually:
    echo   mongod --dbpath C:\data\db
    echo.
)

echo.
echo ================================================
echo Checking MongoDB Port (27017)...
echo ================================================
netstat -ano | findstr ":27017" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] MongoDB is listening on port 27017
) else (
    echo [WARNING] Port 27017 is not active
    echo MongoDB may not be running
)

echo.
echo ================================================
echo Testing Connection...
echo ================================================
echo Attempting to connect to mongodb://localhost:27017
echo.

REM Try to connect using mongosh (if available)
where mongosh >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    mongosh --eval "db.adminCommand('ping')" --quiet mongodb://localhost:27017
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Connection successful!
    ) else (
        echo [ERROR] Cannot connect to MongoDB
    )
) else (
    echo mongosh not found - skipping connection test
    echo Install mongosh from: https://www.mongodb.com/try/download/shell
)

echo.
echo ================================================
echo Summary
echo ================================================
echo Database: youtube_shorts_downloader
echo URI: mongodb://localhost:27017/youtube_shorts_downloader
echo.
pause
