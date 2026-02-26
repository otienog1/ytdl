from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from app.models.download import Download
from app.config.database import get_database
from app.utils.logger import logger

router = APIRouter()


@router.get("/")
async def get_download_history(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status: queued, processing, completed, failed"),
    search: Optional[str] = Query(None, description="Search by video title"),
):
    """Get paginated download history with filtering"""
    try:
        db = get_database()

        # Build filter query
        filter_query = {}
        if status:
            filter_query['status'] = status
        if search:
            filter_query['videoInfo.title'] = {'$regex': search, '$options': 'i'}

        # Get total count
        total = await db.downloads.count_documents(filter_query)

        # Calculate pagination
        skip = (page - 1) * limit
        total_pages = (total + limit - 1) // limit  # Ceiling division

        # Get paginated data
        cursor = db.downloads.find(filter_query).sort('createdAt', -1).skip(skip).limit(limit)
        downloads = await cursor.to_list(length=limit)

        return {
            "items": [Download(**download) for download in downloads],
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrevious": page > 1
        }
    except Exception as e:
        logger.error(f"Error getting download history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get download history")


@router.delete("/{job_id}")
async def delete_download(job_id: str):
    """Delete a download from history"""
    try:
        db = get_database()
        result = await db.downloads.delete_one({"jobId": job_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Download not found")

        logger.info(f"Deleted download: {job_id}")
        return {"success": True, "message": "Download deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting download {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete download")
