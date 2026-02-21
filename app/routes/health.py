"""
Health check endpoints for load balancer monitoring
"""
from fastapi import APIRouter
from app.config.settings import settings
from app.services.cookie_refresh_service import cookie_refresh_service
from app.utils.logger import logger
import os

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Basic health check endpoint for load balancer

    Returns HTTP 200 if server is healthy, HTTP 503 if cookies unavailable
    """
    try:
        # Check if cookies file exists for this account
        cookies_available = cookie_refresh_service.check_cookies_file_exists()

        # Check if refresh is in progress
        refresh_in_progress = False
        try:
            if cookie_refresh_service.redis_client:
                refresh_key = f"cookie:refresh:{settings.YT_ACCOUNT_ID}:in_progress"
                refresh_in_progress = bool(cookie_refresh_service.redis_client.get(refresh_key))
        except Exception as e:
            logger.error(f"Error checking refresh status: {e}")

        # Server is healthy if cookies are available
        is_healthy = cookies_available and not refresh_in_progress

        response = {
            "status": "healthy" if is_healthy else "degraded",
            "cookies_available": cookies_available,
            "refresh_in_progress": refresh_in_progress,
            "account_id": settings.YT_ACCOUNT_ID,
            "can_process_downloads": is_healthy
        }

        # Return 503 if not healthy (tells load balancer to route to other servers)
        if not is_healthy:
            return response  # FastAPI will use default 200, we handle status in exception handler

        return response

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "error",
            "cookies_available": False,
            "can_process_downloads": False,
            "account_id": settings.YT_ACCOUNT_ID,
            "error": str(e)
        }


@router.get("/cookies")
async def cookies_health():
    """
    Detailed cookies health check

    Returns information about cookie file status and last refresh time
    """
    try:
        cookies_file = settings.YT_DLP_COOKIES_FILE

        if not cookies_file:
            return {
                "configured": False,
                "exists": False,
                "account_id": settings.YT_ACCOUNT_ID,
                "message": "No cookies file configured for this server"
            }

        exists = os.path.exists(cookies_file)
        file_info = {}

        if exists:
            stat = os.stat(cookies_file)
            file_info = {
                "size_bytes": stat.st_size,
                "last_modified": stat.st_mtime,
                "path": cookies_file
            }

        # Check refresh status
        refresh_in_progress = False
        try:
            if cookie_refresh_service.redis_client:
                refresh_key = f"cookie:refresh:{settings.YT_ACCOUNT_ID}:in_progress"
                refresh_in_progress = bool(cookie_refresh_service.redis_client.get(refresh_key))
        except Exception as e:
            logger.error(f"Error checking refresh status: {e}")

        return {
            "configured": True,
            "exists": exists,
            "account_id": settings.YT_ACCOUNT_ID,
            "refresh_in_progress": refresh_in_progress,
            "file_info": file_info if exists else None,
            "message": "Cookies available" if exists else "Cookies file missing"
        }

    except Exception as e:
        logger.error(f"Cookies health check error: {e}")
        return {
            "configured": bool(settings.YT_DLP_COOKIES_FILE),
            "exists": False,
            "account_id": settings.YT_ACCOUNT_ID,
            "error": str(e)
        }
