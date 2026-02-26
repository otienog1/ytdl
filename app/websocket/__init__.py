"""
WebSocket connection management with Redis pub/sub for cross-process communication
"""
from typing import Dict, Set
from fastapi import WebSocket
from app.utils.logger import logger
import redis
import json
from app.config.settings import settings


class ConnectionManager:
    """Manage WebSocket connections with Redis pub/sub"""

    def __init__(self):
        # job_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Redis client for pub/sub (sync client for Celery compatibility)
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            logger.info("WebSocket manager connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for WebSocket: {e}")
            self.redis_client = None

    async def connect(self, websocket: WebSocket, job_id: str):
        """Accept and register new WebSocket connection"""
        await websocket.accept()

        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()

        self.active_connections[job_id].add(websocket)
        logger.info(f"WebSocket connected for job {job_id}")

    def disconnect(self, websocket: WebSocket, job_id: str):
        """Remove WebSocket connection"""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)

            # Clean up empty sets
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

        logger.info(f"WebSocket disconnected for job {job_id}")

    async def send_update(self, job_id: str, data: dict):
        """
        Send update to all connections for a job.
        Uses Redis pub/sub to bridge Celery worker -> FastAPI server communication.
        """
        # If called from Celery worker (no active connections), publish to Redis
        if job_id not in self.active_connections and self.redis_client:
            try:
                # Publish update to Redis channel
                channel = f"websocket:{job_id}"
                message = json.dumps(data)
                result = self.redis_client.publish(channel, message)
                progress = data.get('data', {}).get('progress', 'N/A')
                logger.info(f"Published WebSocket update to Redis for job {job_id} - progress: {progress}% (subscribers: {result})")
                return
            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}", exc_info=True)
                return

        # If called from FastAPI server (has active connections), send directly
        if job_id in self.active_connections:
            disconnected = set()

            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    logger.error(f"Error sending to WebSocket: {e}")
                    disconnected.add(connection)

            # Clean up disconnected clients
            for connection in disconnected:
                self.disconnect(connection, job_id)

    async def broadcast(self, data: dict):
        """Broadcast message to all connections"""
        for job_id in list(self.active_connections.keys()):
            await self.send_update(job_id, data)


# Global connection manager
manager = ConnectionManager()
