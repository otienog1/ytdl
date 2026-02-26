#!/usr/bin/env python3
"""
Setup script to download and configure ffmpeg locally in the project.
This avoids the need for system-wide installation.
"""

import os
import sys
import platform
from pathlib import Path


def download_static_ffmpeg():
    """Download static ffmpeg binaries to local bin directory."""
    try:
        from static_ffmpeg import run

        # Create local bin directory
        bin_dir = Path(__file__).parent / "bin"
        bin_dir.mkdir(exist_ok=True)

        print("Downloading static ffmpeg binaries...")
        print(f"Platform: {platform.system()}")
        print(f"Installing to: {bin_dir.absolute()}")

        # Download ffmpeg and ffprobe
        ffmpeg_path, ffprobe_path = run.get_or_fetch_platform_executables_else_raise()

        print(f"\nFFmpeg binary: {ffmpeg_path}")
        print(f"FFprobe binary: {ffprobe_path}")

        # Copy to local bin directory
        import shutil

        if platform.system() == "Windows":
            local_ffmpeg = bin_dir / "ffmpeg.exe"
            local_ffprobe = bin_dir / "ffprobe.exe"
        else:
            local_ffmpeg = bin_dir / "ffmpeg"
            local_ffprobe = bin_dir / "ffprobe"

        shutil.copy2(ffmpeg_path, local_ffmpeg)
        shutil.copy2(ffprobe_path, local_ffprobe)

        # Make executable on Unix-like systems
        if platform.system() != "Windows":
            os.chmod(local_ffmpeg, 0o755)
            os.chmod(local_ffprobe, 0o755)

        print(f"\nFFmpeg installed successfully!")
        print(f"Local ffmpeg: {local_ffmpeg}")
        print(f"Local ffprobe: {local_ffprobe}")

        # Update .env to point to local ffmpeg
        update_env_file(str(local_ffmpeg.absolute()), str(local_ffprobe.absolute()))

        return True

    except ImportError:
        print("Error: static-ffmpeg package not found.")
        print("Please install it first: pip install static-ffmpeg")
        return False
    except Exception as e:
        print(f"Error downloading ffmpeg: {e}")
        return False


def update_env_file(ffmpeg_path, ffprobe_path):
    """Update .env file with local ffmpeg paths."""
    env_file = Path(__file__).parent / ".env"

    if not env_file.exists():
        print("\nWarning: .env file not found. Please create it manually.")
        return

    # Read existing .env
    with open(env_file, 'r') as f:
        lines = f.readlines()

    # Check if FFMPEG_PATH already exists
    has_ffmpeg = any(line.startswith('FFMPEG_PATH=') for line in lines)
    has_ffprobe = any(line.startswith('FFPROBE_PATH=') for line in lines)

    # Add or update paths
    with open(env_file, 'a') as f:
        if not has_ffmpeg:
            f.write(f"\n# Local FFmpeg binary\n")
            f.write(f"FFMPEG_PATH={ffmpeg_path}\n")
        if not has_ffprobe:
            f.write(f"FFPROBE_PATH={ffprobe_path}\n")

    print(f"\nUpdated .env file with local ffmpeg paths")


def check_yt_dlp():
    """Check if yt-dlp is available in the virtual environment."""
    try:
        import yt_dlp
        version = yt_dlp.version.__version__
        print(f"\nyt-dlp is installed: version {version}")
        return True
    except ImportError:
        print("\nWarning: yt-dlp not found in virtual environment")
        print("It should be installed automatically via requirements.txt")
        return False


def main():
    print("=" * 60)
    print("FFmpeg Local Setup for YouTube Shorts Downloader")
    print("=" * 60)
    print()

    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if not in_venv:
        print("Warning: Not running in a virtual environment")
        print("It's recommended to activate your virtual environment first:")
        if platform.system() == "Windows":
            print("  venv\\Scripts\\activate")
        else:
            print("  source venv/bin/activate")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return

    # Check yt-dlp
    check_yt_dlp()

    # Download and setup ffmpeg
    if download_static_ffmpeg():
        print("\n" + "=" * 60)
        print("Setup completed successfully!")
        print("=" * 60)
        print("\nYou can now run the backend server:")
        if platform.system() == "Windows":
            print("  .\\start-dev.bat")
        else:
            print("  ./start-dev.sh")
    else:
        print("\nSetup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
