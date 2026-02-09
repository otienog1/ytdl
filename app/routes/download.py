from fastapi import APIRouter, HTTPException, Request
from app.models.download import DownloadResponse, Download, DownloadStatus
from app.utils.validators import DownloadRequest
from app.queue.tasks import process_download
from app.config.database import get_database
from app.middleware.rate_limit import limiter
from app.utils.logger import logger
import uuid
from datetime import datetime

router = APIRouter()


@router.post("/", response_model=DownloadResponse)
@limiter.limit("30/15minutes")
async def initiate_download(request: Request, download_request: DownloadRequest):
    """Initiate a video download"""
    try:
        url = str(download_request.url)
        job_id = str(uuid.uuid4())
        cookies = download_request.cookies  # Optional cookies from frontend

        # Create download record
        db = get_database()
        download_doc = {
            'jobId': job_id,
            'url': url,
            'status': DownloadStatus.QUEUED.value,
            'progress': 0,
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }

        await db.downloads.insert_one(download_doc)

        # Enqueue task with optional cookies
        process_download.delay(url, job_id, cookies)

        logger.info(f"Download initiated: {job_id} for URL: {url} (cookies: {'yes' if cookies else 'no'})")

        return DownloadResponse(
            jobId=job_id,
            status=DownloadStatus.QUEUED
        )
    except Exception as e:
        logger.error(f"Error initiating download: {e}")
        raise HTTPException(status_code=500, detail=str(e))
