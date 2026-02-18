"""
WebSocket routes for real-time updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket import manager
from app.config.database import get_database
from app.utils.logger import logger

router = APIRouter()


@router.websocket("/ws/download/{job_id}")
async def websocket_download_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for download progress updates"""
    await manager.connect(websocket, job_id)

    try:
        # Send initial status
        db = get_database()
        download = await db.downloads.find_one({"jobId": job_id})

        if download:
            await websocket.send_json({
                "type": "status",
                "data": {
                    "jobId": job_id,
                    "status": download.get("status"),
                    "progress": download.get("progress", 0),
                    "videoInfo": download.get("videoInfo"),
                    "downloadUrl": download.get("downloadUrl"),
                    "error": download.get("error")
                }
            })

        # Keep connection alive and listen for client messages
        while True:
            try:
                # Wait for client ping/messages
                data = await websocket.receive_text()

                # Echo pong response
                if data == "ping":
                    await websocket.send_json({"type": "pong"})

            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")

    finally:
        manager.disconnect(websocket, job_id)
