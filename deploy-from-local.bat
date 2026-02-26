@echo off
REM ===================================================================
REM Deploy Hybrid Redis from Local Windows Machine to All Servers
REM ===================================================================
REM This script runs on your LOCAL Windows machine and deploys
REM to all 3 servers via SSH (requires WSL or Git Bash)
REM
REM Usage: deploy-from-local.bat
REM ===================================================================

echo ========================================================================
echo Hybrid Redis Multi-Server Deployment (Windows)
echo ========================================================================
echo.

REM Check if running in WSL/Git Bash
where bash >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Bash not found. Please install Git for Windows or WSL.
    echo.
    echo Download Git for Windows: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Run PowerShell deployment script
powershell -ExecutionPolicy Bypass -File "%~dp0deploy-from-local.ps1"
