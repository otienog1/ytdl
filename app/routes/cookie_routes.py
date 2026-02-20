"""
Cookie management API routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.cookie_refresh_service import cookie_refresh_service
from app.utils.logger import logger


router = APIRouter()


class CookieRefreshRequest(BaseModel):
    reason: str = "manual_trigger"


@router.post("/trigger-refresh")
async def trigger_cookie_refresh(request: CookieRefreshRequest):
    """
    Manually trigger a cookie refresh job

    This endpoint allows administrators to manually trigger a cookie refresh
    when needed (e.g., after detecting authentication issues).
    """
    try:
        success = cookie_refresh_service.trigger_cookie_refresh(reason=request.reason)

        if success:
            return {
                "success": True,
                "message": "Cookie refresh job triggered successfully",
                "reason": request.reason
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to trigger cookie refresh. Check logs for details."
            )

    except Exception as e:
        logger.error(f"Error triggering cookie refresh: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue-status")
async def get_queue_status():
    """
    Get the current status of the cookie refresh queue

    Returns information about pending, active, completed, and failed jobs.
    """
    try:
        status = cookie_refresh_service.get_queue_status()

        if "error" in status:
            raise HTTPException(status_code=500, detail=status["error"])

        return {
            "success": True,
            "queue": "cookie-refresh",
            "status": status
        }

    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cookies-status")
async def get_cookies_status():
    """
    Check if the YouTube cookies file exists and is accessible
    """
    try:
        import os
        cookies_file = os.getenv('YT_DLP_COOKIES_FILE')

        if not cookies_file:
            return {
                "exists": False,
                "configured": False,
                "message": "YT_DLP_COOKIES_FILE environment variable not set"
            }

        exists = os.path.exists(cookies_file)
        file_size = os.path.getsize(cookies_file) if exists else 0
        modified_time = os.path.getmtime(cookies_file) if exists else None

        return {
            "exists": exists,
            "configured": True,
            "path": cookies_file,
            "size_bytes": file_size,
            "last_modified": modified_time,
            "message": "Cookies file found" if exists else "Cookies file missing"
        }

    except Exception as e:
        logger.error(f"Error checking cookies status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
