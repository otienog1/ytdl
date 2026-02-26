@echo off
REM Import data from dump to local MongoDB

echo ================================================
echo Importing to Local MongoDB...
echo ================================================

REM Check if dump directory exists
if not exist "mongodb_dump\ytdl_db" (
    echo Error: Export dump not found!
    echo Please run export-remote-db.bat first
    pause
    exit /b 1
)

REM Import to local MongoDB
mongorestore --db=ytdl_db mongodb_dump\ytdl_db

echo.
echo ================================================
echo Import complete!
echo ================================================
echo Database Name: ytdl_db
echo Connection String: mongodb://localhost:27017/ytdl_db
echo.
echo Next step: Update your .env file to use the local MongoDB connection
echo.
pause
