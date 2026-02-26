@echo off
REM Script to copy GCP credentials to server
REM Usage: copy-credentials.bat root@your-server-ip

if "%1"=="" (
    echo Usage: copy-credentials.bat root@your-server-ip
    echo Example: copy-credentials.bat root@123.45.67.89
    exit /b 1
)

set SERVER=%1
set CREDS_FILE=divine-actor-473706-k4-fdec9ee56ba0.json

echo.
echo ============================================================
echo   Copying GCP Credentials to Server
echo ============================================================
echo.
echo Target server: %SERVER%
echo Credentials file: %CREDS_FILE%
echo.

REM Copy credentials file
echo [1/3] Copying credentials file...
scp "%CREDS_FILE%" %SERVER%:/opt/ytdl/

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to copy credentials file
    exit /b 1
)

echo [2/3] Setting file permissions...
ssh %SERVER% "sudo chmod 644 /opt/ytdl/%CREDS_FILE% && sudo chown root:root /opt/ytdl/%CREDS_FILE%"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to set permissions
    exit /b 1
)

echo [3/3] Verifying .env.production has correct path...
ssh %SERVER% "grep GOOGLE_APPLICATION_CREDENTIALS /opt/ytdl/.env.production"

echo.
echo ============================================================
echo   Credentials copied successfully!
echo ============================================================
echo.
echo Next steps:
echo   1. SSH into server: ssh %SERVER%
echo   2. Restart services: sudo systemctl restart ytd-worker ytd-api ytd-beat
echo   3. Monitor logs: sudo journalctl -u ytd-worker -f
echo.
