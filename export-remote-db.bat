@echo off
REM Export data from remote MongoDB Atlas to local dump

echo ================================================
echo Installing MongoDB Database Tools (if needed)...
echo ================================================
echo.
echo MongoDB Database Tools are required for mongodump/mongorestore.
echo.
echo Option 1: Install with Chocolatey (Recommended)
echo   choco install mongodb-database-tools
echo.
echo Option 2: Download manually from:
echo   https://www.mongodb.com/try/download/database-tools
echo.
echo After installation, run this script again.
echo.
echo ================================================
echo Checking if mongodump is available...
echo ================================================

where mongodump >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: mongodump not found!
    echo Please install MongoDB Database Tools first.
    echo.
    echo Quick install with Chocolatey:
    echo   choco install mongodb-database-tools
    echo.
    pause
    exit /b 1
)

echo mongodump found! Proceeding with export...
echo.

REM Create dump directory if it doesn't exist
if not exist "mongodb_dump" mkdir mongodb_dump

echo ================================================
echo Exporting from MongoDB Atlas...
echo ================================================

REM Export from Atlas (this will create a dump folder)
mongodump --uri="mongodb+srv://mongoatlas_user:yZNOgPARUbX5c20k@scrapperclusteraws.yhrl4e7.mongodb.net/ytdl_db?appName=ScrapperClusterAWS" --out=mongodb_dump

echo.
echo ================================================
echo Export complete!
echo ================================================
echo Data exported to: mongodb_dump\ytdl_db
echo.
echo Next step: Run import-to-local-db.bat to import this data to your local MongoDB
echo.
pause
