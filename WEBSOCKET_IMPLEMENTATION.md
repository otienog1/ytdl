# WebSocket Implementation Guide

## Overview

The backend now supports real-time progress updates via WebSocket connections, eliminating the need for polling. This significantly reduces network traffic and provides instant updates to the frontend.

## Backend Implementation

### WebSocket Endpoint

**Endpoint**: `ws://localhost:3001/ws/download/{job_id}`

Connect to this endpoint to receive real-time updates for a specific download job.

### Connection Flow

1. **Client connects** to `/ws/download/{job_id}`
2. **Server sends initial status** with current job state
3. **Server sends updates** as the download progresses
4. **Client can send "ping"** to keep connection alive (server responds with pong)

### Message Format

All WebSocket messages follow this format:

```json
{
  "type": "status" | "pong",
  "data": {
    "jobId": "string",
    "status": "queued" | "processing" | "completed" | "failed",
    "progress": 0-100,
    "videoInfo": { ... },
    "downloadUrl": "string",
    "error": "string",
    "storageProvider": "gcs" | "azure" | "s3",
    "fileSize": number
  }
}
```

### Message Types

#### Status Update
```json
{
  "type": "status",
  "data": {
    "jobId": "abc123",
    "status": "processing",
    "progress": 45,
    "videoInfo": {
      "id": "dQw4w9WgXcQ",
      "title": "Video Title",
      "thumbnail": "https://...",
      "duration": 60,
      "quality": "1080p"
    }
  }
}
```

#### Pong Response
```json
{
  "type": "pong"
}
```

## Progress Updates

The backend sends progress updates at these key stages:

| Progress | Stage |
|----------|-------|
| 5% | Starting to process |
| 10% | Video info fetched |
| 15-89% | Video download in progress (real-time) |
| 90% | Download complete, starting upload |
| 92% | Uploading to cloud storage |
| 98% | Upload complete, cleaning up |
| 100% | Job complete |

## Frontend Integration

### Basic Usage (Native WebSocket)

```typescript
// Connect to WebSocket
const ws = new WebSocket(`ws://localhost:3001/ws/download/${jobId}`);

// Handle connection open
ws.onopen = () => {
  console.log('WebSocket connected');
};

// Handle messages
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === 'status') {
    const { jobId, status, progress, videoInfo, downloadUrl } = message.data;
    // Update UI with status
  }
};

// Handle errors
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Handle connection close
ws.onclose = (event) => {
  console.log('WebSocket closed:', event.code);
  // Implement reconnection logic
};

// Keep connection alive
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  }
}, 30000); // Every 30 seconds

// Cleanup
ws.close();
```

### React Hook Example

```typescript
import { useEffect, useState, useRef } from 'react';

interface DownloadStatus {
  jobId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  videoInfo?: any;
  downloadUrl?: string;
  error?: string;
}

export function useWebSocket(jobId: string) {
  const [status, setStatus] = useState<DownloadStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const ws = new WebSocket(`ws://localhost:3001/ws/download/${jobId}`);

    ws.onopen = () => {
      setIsConnected(true);

      // Keep alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);

      ws.onclose = () => clearInterval(pingInterval);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'status') {
        setStatus(message.data);
      }
    };

    ws.onclose = () => setIsConnected(false);

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [jobId]);

  return { status, isConnected };
}
```

## Connection Management

### Automatic Reconnection

Implement exponential backoff for reconnection:

```typescript
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function connect() {
  const ws = new WebSocket(url);

  ws.onclose = (event) => {
    if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
      setTimeout(() => {
        reconnectAttempts++;
        connect();
      }, delay);
    }
  };

  ws.onopen = () => {
    reconnectAttempts = 0; // Reset on successful connection
  };
}
```

### Connection Status Indicator

Display connection status to users:

```typescript
<div>
  {isConnected ? (
    <span className="text-green-600">● Connected</span>
  ) : (
    <span className="text-red-600">● Disconnected</span>
  )}
</div>
```

## Testing

### Test WebSocket Connection

```bash
# Start backend
cd backend-python
pipenv run uvicorn app.main:app --reload

# In another terminal, test with wscat (install: npm install -g wscat)
wscat -c ws://localhost:3001/ws/download/test-job-123

# Send ping
> ping

# You should receive:
< {"type":"pong"}
```

### Browser DevTools

1. Open Chrome DevTools → Network tab
2. Filter: "WS" (WebSocket)
3. Click on the WebSocket connection
4. View "Messages" tab to see real-time messages

## Migration from Polling

### Before (Polling)
```typescript
// ❌ Old polling approach
useEffect(() => {
  const interval = setInterval(async () => {
    const response = await fetch(`/api/status/${jobId}`);
    const data = await response.json();
    setStatus(data);
  }, 1000); // Poll every second

  return () => clearInterval(interval);
}, [jobId]);
```

### After (WebSocket)
```typescript
// ✅ New WebSocket approach
const { status, isConnected } = useWebSocket(jobId);
// Status updates automatically, no polling needed!
```

## Benefits

✅ **Real-time updates**: Instant progress updates, no delay
✅ **Reduced network traffic**: ~99% reduction compared to polling
✅ **Lower server load**: No repeated HTTP requests
✅ **Better UX**: Smoother progress bars, instant completion notification
✅ **Bi-directional**: Server can push updates to client

## Architecture

```
┌─────────────┐                    ┌──────────────┐
│   Frontend  │◄───────────────────┤   Backend    │
│             │    WebSocket       │              │
│  useWebSocket│    Connection      │  /ws/download│
│             │                    │  /{job_id}   │
└─────────────┘                    └──────────────┘
                                          ▲
                                          │
                                    ┌─────┴──────┐
                                    │   Celery   │
                                    │   Worker   │
                                    │            │
                                    │ _update_   │
                                    │  status()  │
                                    └────────────┘
                                          │
                                          ▼
                                    ┌────────────┐
                                    │  MongoDB   │
                                    └────────────┘
```

## Troubleshooting

### Connection Fails

1. Check CORS settings in `app/main.py`
2. Ensure backend is running on correct port (3001)
3. Check firewall settings
4. Verify WebSocket protocol (ws:// vs wss://)

### No Updates Received

1. Check browser console for errors
2. Verify job_id is correct
3. Check backend logs for WebSocket errors
4. Ensure Celery worker is running

### Connection Drops

1. Implement reconnection logic
2. Check network stability
3. Increase ping interval if needed
4. Check server logs for disconnection reasons

## Next Steps

For frontend implementation, refer to the implementation plan:
- Create `useWebSocket` hook
- Update main page to use WebSocket
- Add connection status indicator
- Remove old polling code

See `IMPLEMENTATION_PLAN_DAY_04.md` for detailed frontend tasks.
