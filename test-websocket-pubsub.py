"""
Test script to verify Redis pub/sub for WebSocket updates
Run this to simulate what happens when Celery publishes progress updates
"""
import asyncio
import json
from app.websocket import manager

async def test_publish():
    """Test publishing messages to Redis"""
    print("=" * 60)
    print("Testing WebSocket Redis Pub/Sub")
    print("=" * 60)
    print()

    # Simulate what Celery does when sending progress updates
    job_id = "test-job-123"

    # Test different progress values
    progress_updates = [5, 10, 20, 30, 50, 70, 90, 100]

    for progress in progress_updates:
        data = {
            "type": "status",
            "data": {
                "jobId": job_id,
                "status": "processing",
                "progress": progress
            }
        }

        print(f"\nPublishing progress: {progress}%")
        await manager.send_update(job_id, data)
        await asyncio.sleep(0.5)  # Small delay between updates

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    print()
    print("What to check:")
    print("1. Look for: 'Published WebSocket update to Redis for job test-job-123'")
    print("2. Subscriber count should be 0 (no WebSocket connected)")
    print("3. If you connect a WebSocket to ws://localhost:3001/ws/download/test-job-123")
    print("   Then subscriber count should be 1")

if __name__ == "__main__":
    asyncio.run(test_publish())
