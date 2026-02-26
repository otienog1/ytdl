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
            self.queue_name = "cookie-refresh"  # Must match the queue name in cookie-extractor
            logger.info("Cookie refresh service initialized with Redis")
        except Exception as e:
            logger.error(f"Failed to initialize cookie refresh service: {e}")
            self.redis_client = None

    def trigger_cookie_refresh(self, reason: str = "expired_cookies") -> bool:
        """
        Trigger a cookie refresh job by publishing to Bull queue

        Args:
            reason: Reason for refresh (e.g., 'expired_cookies', 'missing_cookies', 'bot_detection')

        Returns:
            bool: True if job was queued successfully, False otherwise
        """
        if not self.redis_client:
            logger.error("Redis client not available, cannot trigger cookie refresh")
            return False

        try:
            # Check if refresh already in progress for this account
            account_id = settings.YT_ACCOUNT_ID
            refresh_key = f"cookie:refresh:{account_id}:in_progress"

            if self.redis_client.get(refresh_key):
                logger.info(f"Cookie refresh already in progress for account {account_id}, skipping")
                return True

            # Set refresh flag with 5-minute expiry (TTL)
            self.redis_client.setex(refresh_key, 300, "1")

            # Create job data
            import time
            job_data = {
                "reason": reason,
                "triggered_by": f"server_{account_id}",
                "account_id": account_id,
                "timestamp": int(time.time() * 1000)  # Bull uses milliseconds
            }

            # Bull queue structure:
            # - Jobs are stored in Redis list: bull:{queueName}:wait
            # - Job ID counter: bull:{queueName}:id
            # - Job data: bull:{queueName}:{jobId}

            # Get next job ID
            job_id = self.redis_client.incr(f"bull:{self.queue_name}:id")

            # Store job data as hash
            job_key = f"bull:{self.queue_name}:{job_id}"
            job_payload = {
                "data": json.dumps(job_data),
                "opts": json.dumps({
                    "attempts": 3,
                    "backoff": {"type": "exponential", "delay": 1000},
                    "timestamp": job_data["timestamp"]
                }),
                "timestamp": str(job_data["timestamp"]),
                "name": "__default__",
                "delay": "0",
                "priority": "0"
            }

            # Set job data
            self.redis_client.hset(job_key, mapping=job_payload)

            # Add job ID to wait queue
            self.redis_client.lpush(f"bull:{self.queue_name}:wait", job_id)

            logger.info(f"✅ Cookie refresh job created (ID: {job_id}, account: {job_data['account_id']}, reason: {reason})")
            return True

        except Exception as e:
            logger.error(f"Failed to trigger cookie refresh: {e}")
            # Clear the refresh flag on error
            try:
                account_id = settings.YT_ACCOUNT_ID
                self.redis_client.delete(f"cookie:refresh:{account_id}:in_progress")
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
            waiting = self.redis_client.llen(f"bull:{self.queue_name}:wait")
            active = self.redis_client.llen(f"bull:{self.queue_name}:active")
            completed = self.redis_client.llen(f"bull:{self.queue_name}:completed")
            failed = self.redis_client.llen(f"bull:{self.queue_name}:failed")

            return {
                "waiting": waiting,
                "active": active,
                "completed": completed,
                "failed": failed,
                "total": waiting + active + completed + failed
            }
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {"error": str(e)}


# Global singleton instance
cookie_refresh_service = CookieRefreshService()
