"""
WebSocket connection management
"""
from typing import Dict, Set
from fastapi import WebSocket
from app.utils.logger import logger


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        # job_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

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
        """Send update to all connections for a job"""
        if job_id not in self.active_connections:
            return

        # Send to all connected clients for this job
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
