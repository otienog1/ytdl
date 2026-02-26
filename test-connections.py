"""
Quick test script to verify MongoDB and Redis connections
"""
import sys
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import redis
from app.config.settings import settings

async def test_mongodb():
    """Test MongoDB connection"""
    print("[*] Testing MongoDB connection...")
    try:
        client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
        )

        # Ping the database
        await client.admin.command('ping')

        # Get database name
        db_name = settings.MONGODB_DB_NAME
        db = client[db_name]

        # List collections
        collections = await db.list_collection_names()

        print(f"[OK] MongoDB connected successfully!")
        print(f"   URI: {settings.MONGODB_URI}")
        print(f"   Database: {db_name}")
        print(f"   Collections: {collections if collections else '(empty database)'}")

        client.close()
        return True

    except Exception as e:
        print(f"[ERROR] MongoDB connection failed: {e}")
        return False

def test_redis():
    """Test Redis connection"""
    print("\n[*] Testing Redis connection...")
    try:
        # Connect to Redis
        client = redis.from_url(settings.REDIS_URL, decode_responses=True)

        # Ping Redis
        response = client.ping()

        if response:
            # Get info
            info = client.info('server')

            print(f"[OK] Redis connected successfully!")
            print(f"   URL: {settings.REDIS_URL}")
            print(f"   Version: {info.get('redis_version', 'Unknown')}")
            print(f"   Mode: {info.get('redis_mode', 'Unknown')}")

            # Check Celery queue
            queue_len = client.llen('celery')
            print(f"   Celery queue length: {queue_len}")

            client.close()
            return True
        else:
            print("[ERROR] Redis ping failed")
            return False

    except Exception as e:
        print(f"[ERROR] Redis connection failed: {e}")
        return False

async def main():
    print("=" * 60)
    print("Testing Local Development Environment")
    print("=" * 60)
    print()

    # Test MongoDB
    mongodb_ok = await test_mongodb()

    # Test Redis
    redis_ok = test_redis()

    print("\n" + "=" * 60)
    if mongodb_ok and redis_ok:
        print("[SUCCESS] All services are working correctly!")
        print("=" * 60)
        print("\nYou can now start the backend and Celery worker:")
        print("  Terminal 1: .\\start-dev.bat")
        print("  Terminal 2: pipenv run celery -A app.queue.celery_app worker --loglevel=info --pool=solo")
        sys.exit(0)
    else:
        print("[FAILED] Some services failed to connect")
        print("=" * 60)
        print("\nPlease check:")
        if not mongodb_ok:
            print("  - MongoDB is running: netstat -ano | findstr :27017")
            print("  - Start MongoDB: net start MongoDB")
        if not redis_ok:
            print("  - Redis is running: netstat -ano | findstr :6379")
            print("  - Start Memurai: net start Memurai")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
