"""
WebSocket routes for real-time updates with Redis pub/sub
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket import manager
from app.config.database import get_database
from app.utils.logger import logger
import asyncio
import json

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

        # Subscribe to Redis channel for this job
        redis_task = None
        if manager.redis_client:
            redis_task = asyncio.create_task(
                _subscribe_to_redis_updates(websocket, job_id)
            )

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
        # Cancel Redis subscription task
        if redis_task:
            redis_task.cancel()
        manager.disconnect(websocket, job_id)


async def _subscribe_to_redis_updates(websocket: WebSocket, job_id: str):
    """Subscribe to Redis pub/sub and forward messages to WebSocket"""
    pubsub = None
    redis_client = None

    try:
        # Create a new Redis connection for pubsub (sync Redis in async context)
        import redis
        from app.config.settings import settings

        # Use sync Redis pubsub with asyncio loop
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        pubsub = redis_client.pubsub()
        channel = f"websocket:{job_id}"
        pubsub.subscribe(channel)

        logger.info(f"Subscribed to Redis channel: {channel}")

        # Poll for messages (run in executor to avoid blocking)
        loop = asyncio.get_event_loop()

        while True:
            # Get message from Redis (with timeout)
            message = await loop.run_in_executor(
                None,
                lambda: pubsub.get_message(timeout=1.0)
            )

            if message and message['type'] == 'message':
                try:
                    # Parse and forward to WebSocket
                    data = json.loads(message['data'])
                    await websocket.send_json(data)
                    logger.info(f"Forwarded Redis message to WebSocket: {job_id} - progress: {data.get('data', {}).get('progress', 'N/A')}%")
                except Exception as e:
                    logger.error(f"Error forwarding Redis message: {e}")

            # Small delay to prevent busy loop
            await asyncio.sleep(0.1)

    except asyncio.CancelledError:
        logger.info(f"Redis subscription cancelled for job {job_id}")
    except Exception as e:
        logger.error(f"Redis subscription error for job {job_id}: {e}", exc_info=True)
    finally:
        # Clean up Redis connection
        if pubsub:
            try:
                pubsub.unsubscribe(channel)
                pubsub.close()
            except Exception as e:
                logger.error(f"Error closing pubsub: {e}")
        if redis_client:
            try:
                redis_client.close()
            except Exception as e:
                logger.error(f"Error closing redis client: {e}")
