"""
Cookie Refresh Service - Triggers cookie extraction via Redis Bull queue
"""
import redis
import json
from app.config.settings import settings
from app.utils.logger import logger


class CookieRefreshService:
    """Service to trigger cookie refresh jobs via Redis Bull queue"""

    def __init__(self):
        """Initialize Redis connection for Bull queue"""
        try:
            # Bull uses Redis lists and hashes with specific key patterns
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            self.queue_name = "youtube:cookie:requests"  # Must match the queue name in cookie-worker.js
            logger.info("Cookie refresh service initialized with Redis")
        except Exception as e:
            logger.error(f"Failed to initialize cookie refresh service: {e}")
            self.redis_client = None

    def trigger_cookie_refresh(self, reason: str = "expired_cookies", server_id: str = None) -> bool:
        """
        Trigger a cookie refresh job by publishing to Redis queue

        Args:
            reason: Reason for refresh (e.g., 'expired_cookies', 'missing_cookies', 'bot_detection')
            server_id: Server ID to refresh cookies for (default: all servers)

        Returns:
            bool: True if job was queued successfully, False otherwise
        """
        if not self.redis_client:
            logger.error("Redis client not available, cannot trigger cookie refresh")
            return False

        try:
            # Check if refresh already in progress
            refresh_key = f"cookie:refresh:in_progress"

            if self.redis_client.get(refresh_key):
                logger.info(f"Cookie refresh already in progress, skipping")
                return True

            # Set refresh flag with 5-minute expiry (TTL)
            self.redis_client.setex(refresh_key, 300, "1")

            # Create job data matching cookie-worker.js expected format
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
                    "timestamp": int(time.time() * 1000)
                }

                # Simple queue structure used by cookie-worker.js
                # Worker uses: brpop(queueName, timeout)
                # So we use lpush to add to the left (FIFO: lpush + brpop)
                self.redis_client.lpush(self.queue_name, json.dumps(job_data))

                logger.info(f"✅ Cookie refresh job queued (server: {sid}, requestId: {job_data['requestId']}, reason: {reason})")
                jobs_queued += 1

            return jobs_queued > 0

        except Exception as e:
            logger.error(f"Failed to trigger cookie refresh: {e}")
            # Clear the refresh flag on error
            try:
                self.redis_client.delete(f"cookie:refresh:in_progress")
            except:
                pass
            return False

    def is_cookie_refresh_needed(self, error_message: str) -> bool:
        """
        Determine if a cookie refresh is needed based on error message

        Args:
            error_message: Error message from yt-dlp

        Returns:
            bool: True if cookie refresh should be triggered
        """
        # Patterns that indicate cookie/authentication issues
        cookie_error_patterns = [
            "sign in to confirm you're not a bot",
            "sign in to confirm that you",
            "this helps protect our community",
            "confirm you're not a bot",
            "sign-in required",
            "login required",
            "please sign in",
            "age-restricted",
            "members-only",
            "private video",
            "http error 403",
            "forbidden",
            "request blocked",
        ]

        error_lower = error_message.lower()
        return any(pattern in error_lower for pattern in cookie_error_patterns)

    def check_cookies_file_exists(self) -> bool:
        """Check if cookies file exists"""
        import os
        cookies_file = settings.YT_DLP_COOKIES_FILE
        if not cookies_file:
            return False
        return os.path.exists(cookies_file)

    def get_queue_status(self) -> dict:
        """Get current status of the cookie refresh queue"""
        if not self.redis_client:
            return {"error": "Redis not available"}

        try:
            # Simple queue structure - just count waiting jobs
            waiting = self.redis_client.llen(self.queue_name)

            return {
                "waiting": waiting,
                "queue_name": self.queue_name
            }
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {"error": str(e)}


# Global singleton instance
cookie_refresh_service = CookieRefreshService()
