"""
Instagram Cookie Refresh Service - Triggers cookie extraction via Redis Bull queue

Similar to YouTube cookie refresh but for Instagram authentication.
"""
import redis
import json
import os
from app.config.settings import settings
from app.utils.logger import logger


class InstagramCookieRefreshService:
    """Service to trigger Instagram cookie refresh jobs via Redis Bull queue"""

    def __init__(self):
        """Initialize Redis connection for Bull queue"""
        try:
            # Use shared Redis for cookie queue coordination (fallback to local if not configured)
            redis_url = settings.BULL_REDIS_URL or settings.REDIS_URL
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True
            )
            self.queue_name = "instagram:cookie:requests"  # Queue name for Instagram cookies
            logger.info(f"Instagram cookie refresh service initialized with Redis at {redis_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Instagram cookie refresh service: {e}")
            self.redis_client = None

    def trigger_cookie_refresh(self, reason: str = "expired_cookies", server_id: str = None) -> bool:
        """
        Trigger an Instagram cookie refresh job by publishing to Redis queue

        Args:
            reason: Reason for refresh (e.g., 'expired_cookies', 'missing_cookies', 'login_required')
            server_id: Server ID to refresh cookies for (default: all servers)

        Returns:
            bool: True if job was queued successfully, False otherwise
        """
        if not self.redis_client:
            logger.error("Redis client not available, cannot trigger Instagram cookie refresh")
            return False

        try:
            # Check if refresh already in progress
            refresh_key = "instagram:cookie:refresh:in_progress"

            if self.redis_client.get(refresh_key):
                logger.info("Instagram cookie refresh already in progress, skipping")
                return True

            # Set refresh flag with 5-minute expiry (TTL)
            self.redis_client.setex(refresh_key, 300, "1")

            # Create job data
            import time
            import uuid

            # Server IDs from servers.json
            server_ids = ["backend-1", "backend-2", "backend-3"] if not server_id else [server_id]

            jobs_queued = 0
            for sid in server_ids:
                job_data = {
                    "serverId": sid,
                    "requestId": str(uuid.uuid4()),
                    "reason": reason,
                    "platform": "instagram",
                    "timestamp": int(time.time() * 1000)
                }

                # Simple queue structure - FIFO: lpush + brpop
                self.redis_client.lpush(self.queue_name, json.dumps(job_data))

                logger.info(f"✅ Instagram cookie refresh job queued (server: {sid}, requestId: {job_data['requestId']}, reason: {reason})")
                jobs_queued += 1

            return jobs_queued > 0

        except Exception as e:
            logger.error(f"Failed to trigger Instagram cookie refresh: {e}")
            # Clear the refresh flag on error
            try:
                self.redis_client.delete("instagram:cookie:refresh:in_progress")
            except:
                pass
            return False

    def is_cookie_refresh_needed(self, error_message: str) -> bool:
        """
        Determine if an Instagram cookie refresh is needed based on error message

        Args:
            error_message: Error message from yt-dlp

        Returns:
            bool: True if cookie refresh should be triggered
        """
        # Patterns that indicate Instagram cookie/authentication issues
        cookie_error_patterns = [
            "login required",
            "login page",
            "not authorized",
            "rate-limit reached or login",
            "requested content is not available",
            "please log in",
            "sign in",
            "authentication required",
            "session expired",
            "http error 401",
            "http error 403",
            "forbidden",
            "private content",
        ]

        error_lower = error_message.lower()

        matches = [pattern for pattern in cookie_error_patterns if pattern in error_lower]
        result = len(matches) > 0

        if result:
            logger.debug(f"Instagram cookie refresh needed: matches={matches}")

        return result

    def check_cookies_file_exists(self) -> bool:
        """Check if Instagram cookies file exists"""
        cookies_file = getattr(settings, 'INSTAGRAM_COOKIES_FILE', None)
        if not cookies_file:
            return False
        return os.path.exists(cookies_file)

    def get_queue_status(self) -> dict:
        """Get current status of the Instagram cookie refresh queue"""
        if not self.redis_client:
            return {"error": "Redis not available"}

        try:
            # Simple queue structure - just count waiting jobs
            waiting = self.redis_client.llen(self.queue_name)

            return {
                "waiting": waiting,
                "queue_name": self.queue_name,
                "platform": "instagram"
            }
        except Exception as e:
            logger.error(f"Failed to get Instagram queue status: {e}")
            return {"error": str(e)}


# Global singleton instance
instagram_cookie_refresh_service = InstagramCookieRefreshService()
