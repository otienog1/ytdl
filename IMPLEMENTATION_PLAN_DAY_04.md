# Day 4: WebSocket Real-Time Progress Updates

**Goal**: Replace polling with WebSocket for real-time download progress
**Estimated Time**: 6-8 hours
**Priority**: MEDIUM - Improves performance and UX

---

## Morning Session (3-4 hours)

### Task 4.1: Install WebSocket dependencies (15 min)

```bash
cd backend-python
pipenv install websockets python-socketio

cd ../frontend
npm install socket.io-client
```

---

### Task 4.2: Create WebSocket manager (60 min)

**File: `backend-python/app/websocket/__init__.py`**
```python
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
```

---

### Task 4.3: Create WebSocket endpoint (45 min)

**File: `backend-python/app/routes/websocket_routes.py`**
```python
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
```

**File: `backend-python/app/main.py`** (Register WebSocket routes)
```python
from app.routes import websocket_routes

# Include WebSocket router
app.include_router(websocket_routes.router)
```

---

### Task 4.4: Update tasks to send WebSocket updates (90 min)

**File: `backend-python/app/queue/tasks.py`** (Add WebSocket notifications)
```python
from app.websocket import manager
import asyncio

async def _update_status(
    job_id: str,
    status: str,
    progress: int = None,
    **kwargs
):
    """Update download status and notify via WebSocket"""
    db = get_database()

    update_data = {
        "status": status,
        "updatedAt": datetime.utcnow()
    }

    if progress is not None:
        update_data["progress"] = progress

    for key, value in kwargs.items():
        if value is not None:
            update_data[key] = value

    await db.downloads.update_one(
        {"jobId": job_id},
        {"$set": update_data}
    )

    # Send WebSocket update
    try:
        await manager.send_update(job_id, {
            "type": "status",
            "data": {
                "jobId": job_id,
                "status": status,
                "progress": progress,
                **kwargs
            }
        })
    except Exception as e:
        logger.error(f"Failed to send WebSocket update: {e}")

    logger.info(f"Download {job_id} status: {status} ({progress}%)")


async def _process_download_async(task, url: str, job_id: str, cookies: dict = None):
    """Process download with WebSocket progress updates"""
    # ... existing code ...

    # Update progress at each stage with WebSocket
    await _update_status(job_id, 'processing', progress=5)

    # Fetch video info
    video_info = await youtube_service.get_video_info(url, cookies=cookies)
    await _update_status(job_id, 'processing', progress=10, videoInfo=video_info.model_dump(by_alias=True))

    # Check for existing download
    await _update_status(job_id, 'processing', progress=15)

    # ... more updates at each step ...

    # Downloading video
    await _update_status(job_id, 'processing', progress=20)

    # ... download progress can be sent in real-time ...

    # Uploading to storage
    await _update_status(job_id, 'processing', progress=90)

    # Complete
    await _update_status(
        job_id,
        'completed',
        progress=100,
        downloadUrl=download_url,
        videoInfo=video_info_dict,
        storageProvider=storage_provider,
        fileSize=file_size
    )
```

---

## Afternoon Session (3-4 hours)

### Task 4.5: Create frontend WebSocket hook (60 min)

**File: `frontend/hooks/useWebSocket.ts`**
```typescript
import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

interface DownloadStatus {
  jobId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  videoInfo?: any;
  downloadUrl?: string;
  error?: string;
}

interface UseWebSocketReturn {
  status: DownloadStatus | null;
  isConnected: boolean;
  error: Error | null;
}

export function useWebSocket(jobId: string): UseWebSocketReturn {
  const [status, setStatus] = useState<DownloadStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    if (!jobId) return;

    try {
      // Create WebSocket connection
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:\/\//, '') || 'localhost:3001';
      const ws = new WebSocket(`${protocol}//${host}/ws/download/${jobId}`);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;

        // Send periodic ping to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000); // Every 30 seconds

        ws.onclose = () => {
          clearInterval(pingInterval);
        };
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'status') {
            setStatus(message.data);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError(new Error('WebSocket connection error'));
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);

        // Attempt to reconnect if not normal closure
        if (event.code !== 1000 && reconnectAttempts.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`Reconnecting in ${delay}ms...`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;

    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setError(err as Error);
    }
  }, [jobId]);

  useEffect(() => {
    connect();

    return () => {
      // Cleanup
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
        wsRef.current = null;
      }
    };
  }, [connect]);

  return { status, isConnected, error };
}
```

---

### Task 4.6: Update frontend to use WebSocket (90 min)

**File: `frontend/app/page.tsx`** (Update to use WebSocket)
```typescript
'use client';

import { useState } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { VideoPreview } from '@/components/VideoPreview';
import { ProgressIndicator } from '@/components/ProgressIndicator';

export default function Home() {
  const [url, setUrl] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);

  // Use WebSocket hook instead of polling
  const { status, isConnected, error: wsError } = useWebSocket(jobId || '');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });

      const data = await response.json();
      setJobId(data.jobId);

    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">YouTube Shorts Downloader</h1>

      {/* Connection status indicator */}
      {jobId && (
        <div className="mb-4 text-sm">
          {isConnected ? (
            <span className="text-green-600">● Connected</span>
          ) : (
            <span className="text-red-600">● Disconnected</span>
          )}
        </div>
      )}

      {/* URL input form */}
      <form onSubmit={handleSubmit} className="mb-8">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste YouTube Shorts URL"
          className="w-full px-4 py-2 border rounded"
        />
        <button
          type="submit"
          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded"
        >
          Download
        </button>
      </form>

      {/* Real-time status updates via WebSocket */}
      {status && (
        <div>
          <ProgressIndicator
            status={status.status}
            progress={status.progress}
          />

          {status.videoInfo && (
            <VideoPreview
              videoInfo={status.videoInfo}
              downloadUrl={status.downloadUrl}
              showDownloadButton={status.status === 'completed'}
            />
          )}

          {status.error && (
            <div className="mt-4 p-4 bg-red-50 text-red-700 rounded">
              {status.error}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

---

### Task 4.7: Add connection status indicator (45 min)

**File: `frontend/components/ConnectionStatus.tsx`**
```typescript
interface ConnectionStatusProps {
  isConnected: boolean;
  error?: Error | null;
}

export function ConnectionStatus({ isConnected, error }: ConnectionStatusProps) {
  if (error) {
    return (
      <div className="flex items-center gap-2 text-sm text-red-600">
        <div className="w-2 h-2 rounded-full bg-red-600"></div>
        <span>Connection error</span>
      </div>
    );
  }

  if (!isConnected) {
    return (
      <div className="flex items-center gap-2 text-sm text-yellow-600">
        <div className="w-2 h-2 rounded-full bg-yellow-600 animate-pulse"></div>
        <span>Connecting...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-sm text-green-600">
      <div className="w-2 h-2 rounded-full bg-green-600"></div>
      <span>Connected</span>
    </div>
  );
}
```

---

### Task 4.8: Test WebSocket implementation (45 min)

**Test Plan:**

1. **Basic Connection Test**
   - Start backend: `cd backend-python && pipenv run uvicorn app.main:app --reload`
   - Start frontend: `cd frontend && npm run dev`
   - Submit download
   - Verify WebSocket connects
   - Check browser DevTools → Network → WS

2. **Progress Updates Test**
   - Submit download
   - Verify real-time progress updates (no polling)
   - Check network traffic (should only see WebSocket messages)

3. **Reconnection Test**
   - Start download
   - Restart backend
   - Verify frontend reconnects automatically
   - Check reconnection attempts in console

4. **Multiple Tabs Test**
   - Open two browser tabs
   - Submit same job ID
   - Verify both receive updates

5. **Error Handling Test**
   - Submit invalid URL
   - Verify error received via WebSocket
   - Check error display in UI

**Create test checklist:**
```markdown
## WebSocket Test Checklist

- [ ] WebSocket connects successfully
- [ ] Initial status sent on connection
- [ ] Progress updates received in real-time
- [ ] No polling requests in network tab
- [ ] Automatic reconnection works
- [ ] Multiple clients receive updates
- [ ] Errors properly transmitted
- [ ] Connection closes cleanly on completion
- [ ] Ping/pong keeps connection alive
- [ ] Connection status indicator updates
```

---

## End of Day Checklist

- [ ] WebSocket dependencies installed
- [ ] Connection manager implemented
- [ ] WebSocket endpoint created
- [ ] Tasks sending WebSocket updates
- [ ] Frontend WebSocket hook created
- [ ] Frontend updated to use WebSocket
- [ ] Connection status indicator added
- [ ] All tests passing
- [ ] No more polling in network tab
- [ ] Code committed to git

**Git Commit**:
```bash
git add .
git commit -m "Day 4: Replace polling with WebSocket for real-time updates

- Implemented WebSocket connection manager
- Created WebSocket endpoint for download progress
- Updated tasks to send real-time progress via WebSocket
- Created useWebSocket hook in frontend
- Updated UI to use WebSocket instead of polling
- Added connection status indicator
- Implemented automatic reconnection
- Reduced network traffic significantly"
```

---

## Success Metrics

✅ **Complete** if:
- WebSocket connections working
- Real-time progress updates visible
- No polling requests in network tab
- Automatic reconnection functional
- Connection status indicator working

## Tomorrow Preview

**Day 5**: Add download history UI
- Create history page component
- Integrate with existing /api/history endpoint
- Add pagination and filtering
- Implement re-download functionality
