import os
import subprocess
import json
import tempfile
import uuid
import re
import asyncio
from pathlib import Path
from typing import Dict, Optional
from app.utils.logger import logger
from app.models.download import VideoInfo
from app.config.settings import settings
from app.exceptions import (
    InvalidVideoURLError,
    VideoNotFoundError,
    VideoDownloadError,
    CookieUnavailableError
)
from app.monitoring.metrics import metrics_tracker
from app.services.cookie_refresh_service import cookie_refresh_service

class YouTubeService:
    def __init__(self):
        self.download_dir = Path("downloads")
        self.download_dir.mkdir(exist_ok=True)
        self.yt_dlp_path = settings.YT_DLP_PATH or os.getenv('YT_DLP_PATH', 'yt-dlp')
        self.ffmpeg_path = settings.FFMPEG_PATH or os.getenv('FFMPEG_PATH', 'ffmpeg')
        self.ffprobe_path = settings.FFPROBE_PATH or os.getenv('FFPROBE_PATH', 'ffprobe')
        self.cookies_file = settings.YT_DLP_COOKIES_FILE
        self.account_id = settings.YT_ACCOUNT_ID
        self.proxy = os.getenv('YT_DLP_PROXY')

    def _extract_video_id(self, url: str) -> str:
        patterns = [
            r'(?:youtube\.com\/(?:shorts\/|watch\?v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match: return match.group(1)
        raise InvalidVideoURLError(url)

    def _create_temp_cookies_file(self, cookies: Dict[str, str]) -> Optional[str]:
        try:
            fd, temp_path = tempfile.mkstemp(suffix='.txt', prefix='yt_cookies_')
            with os.fdopen(fd, 'w') as f:
                f.write("# Netscape HTTP Cookie File\n")
                for name, value in cookies.items():
                    f.write(f".youtube.com\tTRUE\t/\tTRUE\t0\t{name}\t{value}\n")
            return temp_path
        except Exception as e:
            logger.error(f"Error creating temp cookies: {e}")
            return None

    def _handle_cookie_error(self, error_message: str, video_id: str):
        """Enhanced error handler to bubble up specific cookie issues"""
        # If stderr is empty, we likely had a networking/IP drop
        if not error_message:
            logger.error("YT-DLP returned empty stderr. Possible IP block or SSL handshake failure.")
            return

        if cookie_refresh_service.is_cookie_refresh_needed(error_message):
            logger.warning(f"🔄 Cookie refresh required for {self.account_id}: {error_message[:150]}")
            cookie_refresh_service.trigger_cookie_refresh(reason="bot_detection")
            # This specific message will now be returned to the frontend
            raise CookieUnavailableError(self.account_id, reason=f"YouTube blocked session: {error_message[:50]}")

    async def get_video_info(self, url: str, cookies: Optional[Dict[str, str]] = None) -> VideoInfo:
        """Optimized for 1GB RAM and multi-server cookie stability"""
        with metrics_tracker.track_youtube_api('get_video_info'):
            video_id = self._extract_video_id(url)
            temp_cookies_file = None

            try:
                # 'nice' gives the OS/Redis priority over yt-dlp
                cmd = ['nice', '-n', '10', self.yt_dlp_path, '--dump-json', '--no-playlist', '--flat-playlist']
                cmd.extend(["--js-runtimes", "node", "--remote-components", "ejs:github"])

                if self.ffmpeg_path != 'ffmpeg':
                    cmd.extend(['--ffmpeg-location', os.path.dirname(self.ffmpeg_path)])

                # Determine which cookie file to use
                use_cookies_file = None
                if self.cookies_file and os.path.exists(self.cookies_file):
                    use_cookies_file = self.cookies_file
                elif cookies:
                    temp_cookies_file = self._create_temp_cookies_file(cookies)
                    use_cookies_file = temp_cookies_file

                if use_cookies_file:
                    cmd.extend(['--cookies', use_cookies_file])
                    # Force web client when using cookies for consistency
                    cmd.extend(['--extractor-args', 'youtube:player_client=web'])
                else:
                    cmd.extend(['--extractor-args', 'youtube:player_client=android,ios'])

                if self.proxy:
                    cmd.extend(['--proxy', self.proxy])

                # Add the video URL to the command
                cmd.append(url)

                # Use Popen to capture everything manually to avoid hidden failures
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    # Limit threads to prevent 1GB RAM OOM during n-sig calculation
                    env={**os.environ, "UV_THREADPOOL_SIZE": "1", "OPENBLAS_NUM_THREADS": "1"}
                )

                try:
                    stdout, stderr = process.communicate(timeout=settings.YTDLP_INFO_TIMEOUT)
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, stderr = process.communicate()
                    raise VideoDownloadError(video_id, "Metadata fetch timed out. CPU or Network saturated.")

                if process.returncode != 0:
                    logger.error(f"yt-dlp error output: {stderr}")
                    self._handle_cookie_error(stderr, video_id)
                    
                    if "Video unavailable" in stderr:
                        raise VideoNotFoundError(video_id, "Video is unavailable")
                    # Return the actual yt-dlp error so we can see it on frontend
                    raise VideoDownloadError(video_id, f"YT-DLP: {stderr.splitlines()[-1] if stderr else 'Unknown Error'}")

                info = json.loads(stdout)
                return VideoInfo(
                    id=info['id'],
                    title=info['title'],
                    thumbnail=info['thumbnail'],
                    duration=info.get('duration', 0),
                    quality=f"{info.get('height', 'N/A')}p" if info.get('height') else None,
                    file_size=self._format_file_size(info.get('filesize')) if info.get('filesize') else None
                )

            except Exception as e:
                logger.error(f"Error in get_video_info: {str(e)}")
                raise
            finally:
                if temp_cookies_file and os.path.exists(temp_cookies_file):
                    os.remove(temp_cookies_file)

    def download_video_sync(self, url: str, video_id: str, progress_callback=None, cookies: Optional[Dict[str, str]] = None) -> str:
        """Prioritized download to prevent Redis heartbeats from timing out"""
        with metrics_tracker.track_youtube_api('download_video'):
            temp_cookies_file = None
            try:
                file_name = f"{video_id}_{uuid.uuid4().hex[:8]}.mp4"
                output_path = self.download_dir / file_name

                # Limit resolution to 720p to prevent FFmpeg from crashing 1GB RAM
                cmd = ['nice', '-n', '15', self.yt_dlp_path]
                cmd.extend([
                    '--js-runtimes', 'node',
                    '-f', 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    '--merge-output-format', 'mp4',
                    '--newline', '--no-part',
                    '-o', str(output_path),
                    url
                ])

                # Cookie Handling (Mirroring get_video_info)
                if self.cookies_file and os.path.exists(self.cookies_file):
                    cmd.extend(['--cookies', self.cookies_file, '--extractor-args', 'youtube:player_client=web'])
                elif cookies:
                    temp_cookies_file = self._create_temp_cookies_file(cookies)
                    cmd.extend(['--cookies', temp_cookies_file, '--extractor-args', 'youtube:player_client=web'])
                else:
                    cmd.extend(['--extractor-args', 'youtube:player_client=android,ios'])

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    env={**os.environ, "FFMPEG_THREADS": "1"} # Prevent FFmpeg CPU spike
                )

                last_progress = 0
                if process.stdout:
                    for line in process.stdout:
                        if '[download]' in line and '%' in line:
                            match = re.search(r'(\d+\.?\d*)%', line)
                            if match:
                                percentage = float(match.group(1))
                                scaled = int(20 + (percentage * 0.6))
                                if scaled > last_progress and progress_callback:
                                    progress_callback(scaled)
                                    last_progress = scaled

                process.wait()
                if process.returncode != 0:
                    raise VideoDownloadError(video_id, "Download failed after starting.")

                if not output_path.exists():
                    raise VideoDownloadError(video_id, "Downloaded file not found.")

                return str(output_path)

            except Exception as e:
                logger.error(f"Download Error: {e}")
                raise
            finally:
                if temp_cookies_file and os.path.exists(temp_cookies_file):
                    os.remove(temp_cookies_file)

    async def download_video(self, url: str, video_id: str, progress_callback=None) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.download_video_sync, url, video_id, progress_callback)

    async def delete_local_file(self, file_path: str):
        try: os.remove(file_path)
        except Exception as e: logger.error(f"Cleanup error: {e}")

    def _format_file_size(self, bytes_val: float) -> str:
        if not bytes_val: return "N/A"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024: return f"{round(bytes_val, 2)} {unit}"
            bytes_val /= 1024
        return f"{round(bytes_val, 2)} GB"
youtube_service = YouTubeService()
