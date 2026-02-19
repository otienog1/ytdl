from fastapi import APIRouter, HTTPException, Request
from app.models.download import DownloadResponse, Download, DownloadStatus
from app.utils.validators import DownloadRequest
from app.queue.tasks import process_download
from app.config.database import get_database
from app.middleware.rate_limit import limiter
from app.utils.logger import logger
import uuid
from datetime import datetime
from typing import List

router = APIRouter()


@router.post("/", response_model=DownloadResponse)
@limiter.limit("30/15minutes")
async def initiate_download(request: Request, download_request: DownloadRequest):
    """Initiate a video download"""
    try:
        url = str(download_request.url)
        job_id = str(uuid.uuid4())
        cookies = download_request.cookies  # Optional cookies from frontend
        user_id = download_request.user_id  # Optional Firebase user ID

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

        # Add userId if authenticated user
        if user_id:
            download_doc['userId'] = user_id

        await db.downloads.insert_one(download_doc)

        # Enqueue task with optional cookies
        process_download.delay(url, job_id, cookies)

        logger.info(f"Download initiated: {job_id} for URL: {url} (user: {user_id or 'anonymous'}, cookies: {'yes' if cookies else 'no'})")

        return DownloadResponse(
            jobId=job_id,
            status=DownloadStatus.QUEUED
        )
    except Exception as e:
        logger.error(f"Error initiating download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{user_id}", response_model=List[DownloadResponse])
@limiter.limit("60/minute")
async def get_user_download_history(request: Request, user_id: str, limit: int = 50):
    """Get download history for a specific user (authenticated users only)"""
    try:
        db = get_database()

        # Fetch user's completed downloads, sorted by most recent first
        cursor = db.downloads.find({
            'userId': user_id,
            'status': DownloadStatus.COMPLETED.value
        }).sort('createdAt', -1).limit(limit)

        downloads = await cursor.to_list(length=limit)

        # Convert to response format
        history = []
        for download in downloads:
            history.append(DownloadResponse(
                jobId=download.get('jobId'),
                status=DownloadStatus(download.get('status')),
                progress=download.get('progress', 100),
                videoInfo=download.get('videoInfo'),
                downloadUrl=download.get('downloadUrl'),
                error=download.get('error')
            ))

        logger.info(f"Fetched {len(history)} downloads for user {user_id}")
        return history

    except Exception as e:
        logger.error(f"Error fetching download history for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
