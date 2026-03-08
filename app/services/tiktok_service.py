"""
TikTok Video Service

Handles TikTok video metadata retrieval and downloading using yt-dlp.
"""

import os
import subprocess
import json
import tempfile
import uuid
import re
import hashlib
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


class TikTokService(BaseVideoService):
    """
    TikTok video download service.

    TikTok-specific considerations:
    - Video IDs are 19-digit numbers
    - Short URLs (vm.tiktok.com) are resolved automatically by yt-dlp
    - Most public videos don't require cookies
    - Rate limiting can be aggressive
    """

    def __init__(self):
        self.download_dir = Path("downloads")
        self.download_dir.mkdir(exist_ok=True)
        self.yt_dlp_path = settings.YT_DLP_PATH or os.getenv('YT_DLP_PATH', 'yt-dlp')
        self.ffmpeg_path = settings.FFMPEG_PATH or os.getenv('FFMPEG_PATH', 'ffmpeg')
        self.cookies_file = getattr(settings, 'TIKTOK_COOKIES_FILE', None)

    def extract_video_id(self, url: str) -> str:
        """
        Extract TikTok video ID from URL.

        TikTok video IDs are 19-digit numbers found in /video/{id} URLs.
        For short URLs, we generate a hash since yt-dlp resolves them.
        """
        # Standard URL: tiktok.com/@user/video/7123456789012345678
        match = re.search(r'/video/(\d{15,25})', url)
        if match:
            return match.group(1)

        # For short URLs (vm.tiktok.com, tiktok.com/t/), generate hash
        # yt-dlp will resolve the actual video ID
        return hashlib.md5(url.encode()).hexdigest()[:16]

    def _create_temp_cookies_file(self, cookies: Dict[str, str]) -> Optional[str]:
        """Create temporary Netscape cookies file for TikTok."""
        try:
            fd, temp_path = tempfile.mkstemp(suffix='.txt', prefix='tiktok_cookies_')
            with os.fdopen(fd, 'w') as f:
                f.write("# Netscape HTTP Cookie File\n")
                for name, value in cookies.items():
                    f.write(f".tiktok.com\tTRUE\t/\tTRUE\t0\t{name}\t{value}\n")
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
        Retrieve TikTok video metadata.

        TikTok videos are usually accessible without authentication,
        but cookies may help with region-locked or private content.
        """
        with metrics_tracker.track_youtube_api('tiktok_get_video_info'):
            video_id = self.extract_video_id(url)
            temp_cookies_file = None

            try:
                # Build yt-dlp command for metadata extraction
                cmd = ['nice', '-n', '10', self.yt_dlp_path, '--dump-json', '--no-playlist']

                # TikTok-specific options
                cmd.extend([
                    '--retries', '5',
                    '--fragment-retries', '5',
                    '--socket-timeout', '30',
                ])

                if self.ffmpeg_path != 'ffmpeg':
                    cmd.extend(['--ffmpeg-location', os.path.dirname(self.ffmpeg_path)])

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
                    stderr=subprocess.PIPE,
                    text=True,
                    env={**os.environ, "UV_THREADPOOL_SIZE": "1"}
                )

                try:
                    stdout, stderr = process.communicate(timeout=60)
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, stderr = process.communicate()
                    raise VideoDownloadError(video_id, "TikTok metadata fetch timed out")

                if process.returncode != 0:
                    logger.error(f"yt-dlp TikTok error: {stderr}")

                    if "Video unavailable" in stderr or "not available" in stderr.lower():
                        raise VideoNotFoundError(video_id, "TikTok video is unavailable")

                    if "private" in stderr.lower():
                        raise VideoNotFoundError(video_id, "TikTok video is private")

                    raise VideoDownloadError(
                        video_id,
                        f"TikTok error: {stderr.splitlines()[-1] if stderr else 'Unknown error'}"
                    )

                info = json.loads(stdout)

                return VideoInfo(
                    id=info.get('id', video_id),
                    title=info.get('title', info.get('description', 'TikTok Video')[:100]),
                    thumbnail=info.get('thumbnail'),
                    duration=info.get('duration', 0),
                    quality=f"{info.get('height', 'N/A')}p" if info.get('height') else None,
                    file_size=self._format_file_size(info.get('filesize')) if info.get('filesize') else None
                )

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse TikTok metadata: {e}")
                raise VideoDownloadError(video_id, "Failed to parse TikTok video metadata")
            except Exception as e:
                logger.error(f"TikTok get_video_info error: {str(e)}")
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
        Download TikTok video synchronously.

        TikTok videos are typically available in good quality without
        special authentication for public content.
        """
        with metrics_tracker.track_youtube_api('tiktok_download_video'):
            temp_cookies_file = None
            try:
                file_name = f"tiktok_{video_id}_{uuid.uuid4().hex[:8]}.mp4"
                output_path = self.download_dir / file_name

                cmd = ['nice', '-n', '15', self.yt_dlp_path]
                cmd.extend([
                    '--retries', '5',
                    '--fragment-retries', '5',
                    '--socket-timeout', '30',
                    '-f', 'best[ext=mp4]/best',  # TikTok format selection
                    '--merge-output-format', 'mp4',
                    '--newline', '--no-part',
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
                    logger.error(f"yt-dlp TikTok failed for {video_id}:\n{error_output}")
                    raise VideoDownloadError(video_id, "TikTok download failed")

                if not output_path.exists():
                    raise VideoDownloadError(video_id, "Downloaded TikTok file not found")

                return str(output_path)

            except Exception as e:
                logger.error(f"TikTok download error: {e}")
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
            logger.error(f"TikTok cleanup error: {e}")

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
tiktok_service = TikTokService()
