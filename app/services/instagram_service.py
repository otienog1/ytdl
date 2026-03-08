"""
Instagram Video Service

Handles Instagram Reels, Posts, and Stories video downloading using yt-dlp.
"""

import os
import subprocess
import json
import tempfile
import uuid
import re
import asyncio
from pathlib import Path
from typing import Dict, Optional, Callable

from app.utils.logger import logger
from app.models.download import VideoInfo
from app.config.settings import settings
from app.exceptions import (
    InvalidVideoURLError,
    VideoNotFoundError,
    VideoDownloadError,
)
from app.monitoring.metrics import metrics_tracker
from app.services.base_video_service import BaseVideoService
from app.services.instagram_cookie_refresh_service import instagram_cookie_refresh_service


class InstagramService(BaseVideoService):
    """
    Instagram video download service.

    Instagram-specific considerations:
    - Login cookies often required (sessionid, csrftoken)
    - Aggressive rate limiting
    - Stories expire after 24 hours
    - Private accounts require authentication
    - Supports: Reels, Posts with video, Stories, IGTV
    """

    def __init__(self):
        self.download_dir = Path("downloads")
        self.download_dir.mkdir(exist_ok=True)
        self.yt_dlp_path = settings.YT_DLP_PATH or os.getenv('YT_DLP_PATH', 'yt-dlp')
        self.ffmpeg_path = settings.FFMPEG_PATH or os.getenv('FFMPEG_PATH', 'ffmpeg')
        self.cookies_file = getattr(settings, 'INSTAGRAM_COOKIES_FILE', None)

    def extract_video_id(self, url: str) -> str:
        """
        Extract Instagram shortcode/ID from URL.

        Instagram uses shortcodes (alphanumeric strings) for posts/reels
        and numeric IDs for stories.
        """
        # Posts and Reels: /p/{shortcode} or /reel/{shortcode}
        match = re.search(r'/(p|reel|reels|tv)/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(2)

        # Stories: /stories/{username}/{story_id}
        match = re.search(r'/stories/[\w.-]+/(\d+)', url)
        if match:
            return match.group(1)

        # Fallback: hash the URL
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:16]

    def _create_temp_cookies_file(self, cookies: Dict[str, str]) -> Optional[str]:
        """Create temporary Netscape cookies file for Instagram."""
        try:
            fd, temp_path = tempfile.mkstemp(suffix='.txt', prefix='ig_cookies_')
            with os.fdopen(fd, 'w') as f:
                f.write("# Netscape HTTP Cookie File\n")
                for name, value in cookies.items():
                    f.write(f".instagram.com\tTRUE\t/\tTRUE\t0\t{name}\t{value}\n")
            return temp_path
        except Exception as e:
            logger.error(f"Error creating temp cookies: {e}")
            return None

    async def get_video_info(
        self,
        url: str,
        cookies: Optional[Dict[str, str]] = None
    ) -> VideoInfo:
        """
        Retrieve Instagram video metadata.

        Instagram often requires authentication cookies for:
        - Private accounts
        - Age-restricted content
        - Stories
        - Some reels depending on account settings
        """
        with metrics_tracker.track_youtube_api('instagram_get_video_info'):
            video_id = self.extract_video_id(url)
            temp_cookies_file = None

            try:
                # Build yt-dlp command for metadata extraction
                cmd = ['nice', '-n', '10', self.yt_dlp_path, '--dump-json', '--no-playlist']

                # Instagram-specific options
                cmd.extend([
                    '--retries', '3',
                    '--fragment-retries', '3',
                    '--socket-timeout', '30',
                    # Instagram-specific: limit requests to avoid rate limiting
                    '--sleep-interval', '1',
                ])

                if self.ffmpeg_path != 'ffmpeg':
                    cmd.extend(['--ffmpeg-location', os.path.dirname(self.ffmpeg_path)])

                # Cookie handling - Instagram usually requires cookies
                cookies_used = False
                if self.cookies_file and os.path.exists(self.cookies_file):
                    cmd.extend(['--cookies', self.cookies_file])
                    cookies_used = True
                elif cookies:
                    temp_cookies_file = self._create_temp_cookies_file(cookies)
                    if temp_cookies_file:
                        cmd.extend(['--cookies', temp_cookies_file])
                        cookies_used = True

                cmd.append(url)

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env={**os.environ, "UV_THREADPOOL_SIZE": "1"}
                )

                try:
                    stdout, stderr = process.communicate(timeout=60)
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, stderr = process.communicate()
                    raise VideoDownloadError(video_id, "Instagram metadata fetch timed out")

                if process.returncode != 0:
                    logger.error(f"yt-dlp Instagram error: {stderr}")

                    # Handle common Instagram errors
                    stderr_lower = stderr.lower()

                    # Instagram login/auth errors - most common issue
                    if any(phrase in stderr_lower for phrase in [
                        "login required",
                        "not authorized",
                        "login page",
                        "rate-limit reached or login",
                        "requested content is not available"
                    ]):
                        # Trigger Instagram cookie refresh
                        if instagram_cookie_refresh_service.is_cookie_refresh_needed(stderr):
                            logger.info("Triggering Instagram cookie refresh due to auth error")
                            instagram_cookie_refresh_service.trigger_cookie_refresh(reason="login_required")

                        raise VideoNotFoundError(
                            video_id,
                            "Instagram requires login to access this content. Cookie refresh has been triggered."
                        )

                    if "private" in stderr_lower:
                        raise VideoNotFoundError(video_id, "Instagram content is private")

                    if "not available" in stderr_lower or "page not found" in stderr_lower:
                        raise VideoNotFoundError(video_id, "Instagram content not found or expired")

                    if "rate" in stderr_lower and "limit" in stderr_lower:
                        raise VideoDownloadError(
                            video_id,
                            "Instagram rate limit reached. Please try again later."
                        )

                    raise VideoDownloadError(
                        video_id,
                        f"Instagram error: {stderr.splitlines()[-1] if stderr else 'Unknown error'}"
                    )

                info = json.loads(stdout)

                # Instagram metadata structure
                title = info.get('title') or info.get('description', '')[:100] or 'Instagram Video'

                # Extract thumbnail - Instagram may have it in 'thumbnail' or 'thumbnails' array
                thumbnail = info.get('thumbnail')
                if not thumbnail and info.get('thumbnails'):
                    # Get highest quality thumbnail from array
                    thumbnails = info.get('thumbnails', [])
                    if thumbnails:
                        thumbnail = thumbnails[-1].get('url') if isinstance(thumbnails[-1], dict) else thumbnails[-1]

                return VideoInfo(
                    id=info.get('id', video_id),
                    title=title,
                    thumbnail=thumbnail or '',
                    duration=info.get('duration', 0),
                    quality=f"{info.get('height', 'N/A')}p" if info.get('height') else None,
                    file_size=self._format_file_size(info.get('filesize')) if info.get('filesize') else None
                )

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Instagram metadata: {e}")
                raise VideoDownloadError(video_id, "Failed to parse Instagram video metadata")
            except Exception as e:
                logger.error(f"Instagram get_video_info error: {str(e)}")
                raise
            finally:
                if temp_cookies_file and os.path.exists(temp_cookies_file):
                    os.remove(temp_cookies_file)

    def download_video_sync(
        self,
        url: str,
        video_id: str,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        cookies: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Download Instagram video synchronously.

        Instagram videos are typically high quality but may require
        authentication for access.
        """
        with metrics_tracker.track_youtube_api('instagram_download_video'):
            temp_cookies_file = None
            try:
                file_name = f"instagram_{video_id}_{uuid.uuid4().hex[:8]}.mp4"
                output_path = self.download_dir / file_name

                cmd = ['nice', '-n', '15', self.yt_dlp_path]
                cmd.extend([
                    '--retries', '3',
                    '--fragment-retries', '3',
                    '--socket-timeout', '30',
                    '-f', 'best[ext=mp4]/best',  # Instagram format selection
                    '--merge-output-format', 'mp4',
                    '--newline', '--no-part',
                    # Rate limit protection
                    '--sleep-interval', '1',
                    '-o', str(output_path),
                ])

                # Cookie handling
                if self.cookies_file and os.path.exists(self.cookies_file):
                    cmd.extend(['--cookies', self.cookies_file])
                elif cookies:
                    temp_cookies_file = self._create_temp_cookies_file(cookies)
                    if temp_cookies_file:
                        cmd.extend(['--cookies', temp_cookies_file])

                cmd.append(url)

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    env={**os.environ, "FFMPEG_THREADS": "1"}
                )

                last_progress = 0
                output_lines = []

                if process.stdout:
                    for line in process.stdout:
                        output_lines.append(line.strip())
                        if '[download]' in line and '%' in line:
                            match = re.search(r'(\d+\.?\d*)%', line)
                            if match:
                                percentage = float(match.group(1))
                                # Scale progress to 20-80% range
                                scaled = int(20 + (percentage * 0.6))
                                if scaled > last_progress and progress_callback:
                                    progress_callback(scaled)
                                    last_progress = scaled

                process.wait()

                if process.returncode != 0:
                    error_output = '\n'.join(output_lines[-10:])
                    logger.error(f"yt-dlp Instagram failed for {video_id}:\n{error_output}")

                    # Check for specific error patterns
                    error_msg = "Instagram download failed"
                    output_lower = error_output.lower()

                    if "login required" in output_lower or instagram_cookie_refresh_service.is_cookie_refresh_needed(error_output):
                        # Trigger cookie refresh
                        logger.info("Triggering Instagram cookie refresh due to download auth error")
                        instagram_cookie_refresh_service.trigger_cookie_refresh(reason="download_login_required")
                        error_msg = "Instagram login required for this content. Cookie refresh has been triggered."
                    elif "rate limit" in output_lower:
                        error_msg = "Instagram rate limit reached. Please try again later"
                    elif "not available" in output_lower:
                        error_msg = "Instagram content not available"

                    raise VideoDownloadError(video_id, error_msg)

                if not output_path.exists():
                    raise VideoDownloadError(video_id, "Downloaded Instagram file not found")

                return str(output_path)

            except Exception as e:
                logger.error(f"Instagram download error: {e}")
                raise
            finally:
                if temp_cookies_file and os.path.exists(temp_cookies_file):
                    os.remove(temp_cookies_file)

    async def download_video(
        self,
        url: str,
        video_id: str,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """Async wrapper for download_video_sync."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.download_video_sync,
            url, video_id, progress_callback, None
        )

    async def delete_local_file(self, file_path: str):
        """Clean up local file after upload."""
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Instagram cleanup error: {e}")

    def _format_file_size(self, bytes_val: float) -> str:
        """Format file size for display."""
        if not bytes_val:
            return "N/A"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024:
                return f"{round(bytes_val, 2)} {unit}"
            bytes_val /= 1024
        return f"{round(bytes_val, 2)} GB"


# Singleton instance
instagram_service = InstagramService()
