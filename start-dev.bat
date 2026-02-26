@echo off
echo Starting YouTube Shorts Downloader Python Backend...
echo.

REM Check if using pipenv or venv
where pipenv >nul 2>nul
if %errorlevel% equ 0 (
    echo Using pipenv...
    set USE_PIPENV=1
) else (
    echo Using venv...
    set USE_PIPENV=0
)

if %USE_PIPENV% equ 0 (
    REM Standard venv setup
    if not exist "venv\" (
        echo Creating virtual environment...
        python -m venv venv
    )

    echo Activating virtual environment...
    call venv\Scripts\activate

    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    REM Pipenv setup
    echo Installing dependencies with pipenv...
    pipenv install
)

REM Setup local ffmpeg if not already done
if not exist "bin\ffmpeg.exe" (
    echo.
    echo Setting up local ffmpeg binaries...
    if %USE_PIPENV% equ 1 (
        pipenv run python setup_ffmpeg.py
    ) else (
        python setup_ffmpeg.py
    )
)

echo.
echo ========================================
echo Starting FastAPI server on port 3001...
echo ========================================
echo.

REM Start FastAPI server with hot reload
if %USE_PIPENV% equ 1 (
    start "FastAPI Server" cmd /k "pipenv run uvicorn app.main:app --reload --port 3001"
) else (
    start "FastAPI Server" cmd /k "venv\Scripts\activate && uvicorn app.main:app --reload --port 3001"
)

REM Wait a moment for server to start
timeout /t 3 /nobreak > nul

echo.
echo ========================================
echo Starting Celery worker...
echo ========================================
echo.

REM Start Celery worker in new window
if %USE_PIPENV% equ 1 (
    start "Celery Worker" cmd /k "pipenv run celery -A app.queue.celery_app worker --loglevel=info --pool=solo"
) else (
    start "Celery Worker" cmd /k "venv\Scripts\activate && celery -A app.queue.celery_app worker --loglevel=info --pool=solo"
)

REM Wait a moment for worker to start
timeout /t 2 /nobreak > nul

echo.
echo ========================================
echo Starting Celery Beat (Scheduler)...
echo ========================================
echo.

REM Start Celery Beat for scheduled cleanup tasks
if %USE_PIPENV% equ 1 (
    start "Celery Beat" cmd /k "pipenv run celery -A app.queue.celery_app beat --loglevel=info"
) else (
    start "Celery Beat" cmd /k "venv\Scripts\activate && celery -A app.queue.celery_app beat --loglevel=info"
)

echo.
echo ========================================
echo Backend services started!
echo ========================================
echo FastAPI Server: http://localhost:3001
echo API Docs: http://localhost:3001/docs
echo Celery Worker: Processing download tasks
echo Celery Beat: Running cleanup tasks every 6-12 hours
echo.
echo Press any key to stop all services...
pause > nul
