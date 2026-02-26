"""
Admin API routes for maintenance and management tasks
"""
from fastapi import APIRouter, HTTPException
from app.queue.storage_sync_task import sync_storage_stats
from app.utils.logger import logger

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/sync-storage-stats")
async def trigger_storage_sync():
    """
    Manually trigger storage stats sync with cloud storage

    This endpoint queues a Celery task to sync MongoDB storage stats
    with actual cloud storage (GCS, Azure, S3).

    Use this to:
    - Fix discrepancies between DB and cloud storage
    - Verify storage stats accuracy
    - Clean up phantom file records

    Returns:
        dict: Task information
    """
    try:
        # Queue the sync task
        task = sync_storage_stats.delay()

        logger.info(f"Storage sync task queued: {task.id}")

        return {
            "message": "Storage sync task queued successfully",
            "task_id": task.id,
            "status": "Task will run in the background. Check logs for results."
        }
    except Exception as e:
        logger.error(f"Failed to queue storage sync task: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue storage sync task: {str(e)}"
        )


@router.get("/sync-storage-stats/status/{task_id}")
async def get_sync_status(task_id: str):
    """
    Get status of a storage sync task

    Args:
        task_id: The task ID returned from the sync endpoint

    Returns:
        dict: Task status and result
    """
    try:
        from celery.result import AsyncResult

        task_result = AsyncResult(task_id)

        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result if task_result.ready() else None
        }
    except Exception as e:
        logger.error(f"Failed to get task status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )
