import os
import subprocess
import json
from pathlib import Path
from typing import Dict
from app.utils.logger import logger
from app.models.download import VideoInfo


class YouTubeService:
    def __init__(self):
        self.download_dir = Path("downloads")
        self.download_dir.mkdir(exist_ok=True)

        # Get yt-dlp path (use local venv version by default)
        self.yt_dlp_path = os.getenv('YT_DLP_PATH', 'yt-dlp')

        # Get ffmpeg path (use local bin version if available)
        self.ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')
        self.ffprobe_path = os.getenv('FFPROBE_PATH', 'ffprobe')

        # Optional cookies file for YouTube authentication (to avoid bot detection)
        self.cookies_file = os.getenv('YT_DLP_COOKIES_FILE')

    async def get_video_info(self, url: str) -> VideoInfo:
        """Get video information using yt-dlp"""
        try:
            cmd = [self.yt_dlp_path, '--dump-json', '--no-playlist', url]

            # Add ffmpeg location if using local binary
            if self.ffmpeg_path != 'ffmpeg':
                cmd.extend(['--ffmpeg-location', os.path.dirname(self.ffmpeg_path)])

            # Use Node.js as JavaScript runtime (avoids "No supported JavaScript runtime" warning)
            cmd.extend(['--extractor-args', 'youtube:player_client=android'])

            # Add cookies if available (helps avoid bot detection)
            if self.cookies_file and os.path.exists(self.cookies_file):
                cmd.extend(['--cookies', self.cookies_file])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            info = json.loads(result.stdout)

            return VideoInfo(
                id=info['id'],
                title=info['title'],
                thumbnail=info['thumbnail'],
                duration=info['duration'],
                quality=f"{info.get('height', 'N/A')}p" if info.get('height') else None,
                file_size=self._format_file_size(info.get('filesize')) if info.get('filesize') else None
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Error fetching video info: {e.stderr}")
            raise Exception("Failed to fetch video information")
        except Exception as e:
            logger.error(f"Error fetching video info: {e}")
            raise Exception("Failed to fetch video information")

    def download_video_sync(self, url: str, video_id: str, progress_callback=None) -> str:
        """Download video using yt-dlp with real-time progress tracking (sync version)"""
        try:
            import uuid
            import re
            file_name = f"{video_id}_{uuid.uuid4().hex[:8]}.mp4"
            output_path = self.download_dir / file_name

            # Build yt-dlp command
            cmd = [
                self.yt_dlp_path,
                '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                '--merge-output-format', 'mp4',
                '--newline',  # Output progress on new lines for easier parsing
                '-o', str(output_path),
                url
            ]

            # Add ffmpeg location if using local binary
            if self.ffmpeg_path != 'ffmpeg':
                cmd.extend(['--ffmpeg-location', os.path.dirname(self.ffmpeg_path)])

            # Use Android player client (avoids bot detection better than web client)
            cmd.extend(['--extractor-args', 'youtube:player_client=android'])

            # Add cookies if available
            if self.cookies_file and os.path.exists(self.cookies_file):
                cmd.extend(['--cookies', self.cookies_file])

            # Download with real-time progress tracking
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            logger.info(f"Starting download for {video_id}")
            last_progress = 0

            # Parse progress from yt-dlp output
            for line in process.stdout:
                line = line.strip()
                logger.debug(f"yt-dlp output: {line}")

                if progress_callback:
                    # yt-dlp progress format: [download]  45.2% of 10.5MiB at 1.2MiB/s ETA 00:05
                    if '[download]' in line and '%' in line:
                        match = re.search(r'(\d+\.?\d*)%', line)
                        if match:
                            percentage = float(match.group(1))
                            # Scale download progress to 20-80% of total (80% = download complete)
                            scaled_progress = int(20 + (percentage * 0.6))

                            # Only call callback if progress changed by at least 1%
                            if scaled_progress > last_progress:
                                logger.info(f"Download progress: {percentage}% -> scaled: {scaled_progress}%")
                                progress_callback(scaled_progress)
                                last_progress = scaled_progress
                    # Merging formats progress
                    elif '[Merger]' in line or 'Merging formats' in line:
                        logger.info("Merging video and audio formats")
                        progress_callback(85)

            process.wait()

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd)

            logger.info(f"Video downloaded successfully: {file_name}")
            return str(output_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error downloading video: {e}")
            raise Exception("Failed to download video")
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            raise Exception("Failed to download video")

    async def download_video(self, url: str, video_id: str, progress_callback=None) -> str:
        """Download video using yt-dlp with real-time progress tracking"""
        # Run synchronous download in thread pool to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.download_video_sync, url, video_id, progress_callback)

    async def delete_local_file(self, file_path: str):
        """Delete local file"""
        try:
            os.remove(file_path)
            logger.info(f"Local file deleted: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting local file: {e}")

    def _format_file_size(self, bytes: int) -> str:
        """Format file size in human-readable format"""
        if bytes == 0:
            return "0 Bytes"

        k = 1024
        sizes = ['Bytes', 'KB', 'MB', 'GB']
        i = 0
        size = float(bytes)

        while size >= k and i < len(sizes) - 1:
            size /= k
            i += 1

        return f"{round(size, 2)} {sizes[i]}"


youtube_service = YouTubeService()
