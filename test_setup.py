#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify local installation of yt-dlp and ffmpeg.
Run this after setup to ensure everything is working.
"""

import sys
import os
import subprocess
from pathlib import Path


def test_virtual_env():
    """Check if running in virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if in_venv:
        print(" Running in virtual environment")
        print(f"  Location: {sys.prefix}")
        return True
    else:
        print(" NOT running in virtual environment")
        print("  Please activate: venv\\Scripts\\activate (Windows) or source venv/bin/activate (Unix)")
        return False


def test_yt_dlp():
    """Check if yt-dlp is available"""
    try:
        result = subprocess.run(
            ['yt-dlp', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.strip()
        print(f" yt-dlp is installed: version {version}")

        # Show where yt-dlp is located
        which_result = subprocess.run(
            ['where' if os.name == 'nt' else 'which', 'yt-dlp'],
            capture_output=True,
            text=True
        )
        if which_result.returncode == 0:
            location = which_result.stdout.strip().split('\n')[0]
            print(f"  Location: {location}")

        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(" yt-dlp is NOT installed or not in PATH")
        print("  Install with: pip install yt-dlp")
        return False


def test_ffmpeg():
    """Check if ffmpeg is available (local or system)"""
    # Check for local ffmpeg first
    local_ffmpeg = Path(__file__).parent / "bin" / ("ffmpeg.exe" if os.name == 'nt' else "ffmpeg")

    if local_ffmpeg.exists():
        print(f" Local ffmpeg found: {local_ffmpeg}")
        try:
            result = subprocess.run(
                [str(local_ffmpeg), '-version'],
                capture_output=True,
                text=True,
                check=True
            )
            version_line = result.stdout.split('\n')[0]
            print(f"  {version_line}")
            return True
        except subprocess.CalledProcessError:
            print("  Warning: ffmpeg exists but failed to run")
            return False

    # Check for system ffmpeg
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            check=True
        )
        version_line = result.stdout.split('\n')[0]
        print(f" System ffmpeg found: {version_line}")

        which_result = subprocess.run(
            ['where' if os.name == 'nt' else 'which', 'ffmpeg'],
            capture_output=True,
            text=True
        )
        if which_result.returncode == 0:
            location = which_result.stdout.strip().split('\n')[0]
            print(f"  Location: {location}")

        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(" ffmpeg is NOT installed")
        print("  Run: python setup_ffmpeg.py (for local install)")
        print("  Or install system-wide")
        return False


def test_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path(__file__).parent / ".env"

    if not env_file.exists():
        print(" .env file NOT found")
        print("  Copy .env.example to .env and configure it")
        return False

    print(" .env file exists")

    # Check for important variables
    required_vars = ['MONGODB_URI', 'REDIS_URL', 'GCP_BUCKET_NAME']
    optional_vars = ['FFMPEG_PATH', 'FFPROBE_PATH']

    with open(env_file, 'r') as f:
        content = f.read()

    missing = []
    for var in required_vars:
        if var not in content or f"{var}=" not in content:
            missing.append(var)

    if missing:
        print(f"  Warning: Missing required variables: {', '.join(missing)}")

    for var in optional_vars:
        if var in content:
            print(f"   {var} is configured (using local binary)")

    return len(missing) == 0


def test_dependencies():
    """Check if Python dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'celery',
        'motor',
        'redis',
        'pydantic',
        'yt_dlp'
    ]

    missing = []
    installed = []

    for package in required_packages:
        try:
            __import__(package)
            installed.append(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f" Missing Python packages: {', '.join(missing)}")
        print("  Install with: pip install -r requirements.txt")
        return False
    else:
        print(f" All required Python packages installed ({len(installed)} packages)")
        return True


def main():
    print("=" * 60)
    print("YouTube Shorts Downloader - Setup Verification")
    print("=" * 60)
    print()

    results = {
        "Virtual Environment": test_virtual_env(),
        "Python Dependencies": test_dependencies(),
        "yt-dlp": test_yt_dlp(),
        "ffmpeg": test_ffmpeg(),
        "Environment File": test_env_file(),
    }

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = " PASS" if result else " FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Result: {passed}/{total} checks passed")

    if passed == total:
        print()
        print("<� All checks passed! You're ready to run the application.")
        print()
        print("Start the server:")
        if os.name == 'nt':
            print("  .\\start-dev.bat")
        else:
            print("  ./start-dev.sh")
        print()
        print("Or manually:")
        print("  Terminal 1: uvicorn app.main:app --reload --port 3001")
        print("  Terminal 2: celery -A app.queue.celery_app worker --loglevel=info --pool=solo")
    else:
        print()
        print("L Some checks failed. Please resolve the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
