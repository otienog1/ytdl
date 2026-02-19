@echo off
REM Quick command to run storage stats sync
REM This can be scheduled with Windows Task Scheduler

echo ================================================================================
echo Storage Stats Sync Utility
echo ================================================================================
echo.

cd /d "%~dp0"

REM Run the sync script
pipenv run python sync_storage_stats.py

echo.
echo Press any key to exit...
pause >nul
