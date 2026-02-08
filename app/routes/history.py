from fastapi import APIRouter, Query
from typing import List
from app.models.download import Download
from app.config.database import get_database
from app.utils.logger import logger

router = APIRouter()


@router.get("/", response_model=List[Download])
async def get_download_history(limit: int = Query(10, ge=1, le=100)):
    """Get download history"""
    try:
        db = get_database()
        cursor = db.downloads.find().sort('createdAt', -1).limit(limit)
        downloads = await cursor.to_list(length=limit)

        return [Download(**download) for download in downloads]
    except Exception as e:
        logger.error(f"Error getting download history: {e}")
        return []
