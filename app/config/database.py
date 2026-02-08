from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from app.config.settings import settings
from app.utils.logger import logger


class Database:
    client: AsyncIOMotorClient = None
    db = None


db = Database()


async def connect_to_mongo():
    """Connect to MongoDB"""
    try:
        db.client = AsyncIOMotorClient(settings.MONGODB_URI)

        # Try to get database from URI, otherwise use default name
        try:
            db.db = db.client.get_database()
        except:
            # If no database in URI, use a default name
            db.db = db.client["youtube_shorts_downloader"]
            logger.info("Using default database name: youtube_shorts_downloader")

        # Test connection
        await db.client.admin.command('ping')
        logger.info(f"MongoDB connected successfully to database: {db.db.name}")

        # Create indexes for better query performance
        await _create_indexes()
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def _create_indexes():
    """Create database indexes for optimal query performance"""
    try:
        # Index on video ID within videoInfo for deduplication lookups
        await db.db.downloads.create_index([("videoInfo.id", 1), ("status", 1)])

        # Index on jobId for fast status lookups
        await db.db.downloads.create_index("jobId")

        # Index on createdAt for cleanup operations
        await db.db.downloads.create_index("createdAt")

        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Error creating indexes (may already exist): {e}")


async def close_mongo_connection():
    """Close MongoDB connection"""
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed")


def get_database():
    """Get database instance"""
    return db.db
