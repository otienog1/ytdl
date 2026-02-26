@echo off
REM YouTube Downloader - Deployment Script Launcher
REM Runs the PowerShell deployment script

echo.
echo Starting deployment...
echo.

REM Run the PowerShell deployment script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0deploy.ps1"

REM Capture exit code
set DEPLOY_EXIT_CODE=%ERRORLEVEL%

echo.
if %DEPLOY_EXIT_CODE% EQU 0 (
    echo Deployment completed successfully!
) else (
    echo Deployment failed with exit code %DEPLOY_EXIT_CODE%
)
echo.

pause
exit /b %DEPLOY_EXIT_CODE%
