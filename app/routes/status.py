from fastapi import APIRouter, HTTPException
from app.models.download import DownloadResponse
from app.config.database import get_database
from app.utils.logger import logger

router = APIRouter()


@router.get("/{job_id}", response_model=DownloadResponse)
async def get_download_status(job_id: str):
    """Get download status"""
    try:
        db = get_database()
        download = await db.downloads.find_one({'jobId': job_id})

        if not download:
            raise HTTPException(
                status_code=404,
                detail="Download not found"
            )

        return DownloadResponse(
            jobId=download.get('jobId'),
            status=download.get('status'),
            progress=download.get('progress', 0),
            videoInfo=download.get('videoInfo'),
            downloadUrl=download.get('downloadUrl'),
            error=download.get('error')
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting download status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
