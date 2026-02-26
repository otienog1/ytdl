"""
Storage tracking service for monitoring storage usage across providers
"""
from datetime import datetime
from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.config.multi_storage import multi_storage
from app.models.storage_stats import StorageStats, StorageStatsResponse, AllStorageStatsResponse
from app.services.email_service import email_service
from app.utils.logger import logger
from app.monitoring.metrics import storage_usage_bytes, storage_file_count


class StorageTracker:
    """Track storage usage for all providers"""

    def __init__(self):
        self._db_client: Optional[AsyncIOMotorClient] = None
        self._db = None

    async def _get_db(self):
        """Get database instance"""
        if self._db is None:
            self._db_client = AsyncIOMotorClient(settings.MONGODB_URI)
            try:
                self._db = self._db_client.get_database()
            except:
                self._db = self._db_client["ytdl_db"]
        return self._db

    async def initialize_provider_stats(self, provider: str):
        """Initialize stats for a provider if not exists"""
        db = await self._get_db()
        existing = await db.storage_stats.find_one({"provider": provider})
        if not existing:
            stats = StorageStats(provider=provider)
            await db.storage_stats.insert_one(stats.model_dump())
            logger.info(f"Initialized storage stats for provider: {provider}")

    async def add_file_usage(self, provider: str, file_size_bytes: int, file_name: str):
        """Track a new file upload"""
        db = await self._get_db()

        # Ensure stats exist
        await self.initialize_provider_stats(provider)

        # Update stats
        result = await db.storage_stats.update_one(
            {"provider": provider},
            {
                "$inc": {
                    "total_size_bytes": file_size_bytes,
                    "file_count": 1
                },
                "$set": {
                    "last_updated": datetime.utcnow()
                }
            }
        )

        # Get updated stats
        stats = await db.storage_stats.find_one({"provider": provider})

        # Update Prometheus metrics
        if stats:
            storage_usage_bytes.labels(provider=provider).set(stats["total_size_bytes"])
            storage_file_count.labels(provider=provider).set(stats["file_count"])

        # Check if limit reached
        limit = settings.STORAGE_LIMIT_BYTES
        if stats and stats["total_size_bytes"] >= limit:
            # Mark as full
            await db.storage_stats.update_one(
                {"provider": provider},
                {"$set": {"is_full": True}}
            )

            # Send alert if not already sent
            if not stats.get("alert_sent", False):
                total_gb = stats["total_size_bytes"] / (1024 ** 3)
                limit_gb = limit / (1024 ** 3)
                await email_service.send_storage_alert(provider, total_gb, limit_gb)

                # Mark alert as sent
                await db.storage_stats.update_one(
                    {"provider": provider},
                    {"$set": {"alert_sent": True}}
                )

        logger.info(
            f"Storage tracking: {provider} added {file_size_bytes} bytes "
            f"({file_size_bytes / (1024 ** 2):.2f} MB) for file: {file_name}"
        )

    async def remove_file_usage(self, provider: str, file_size_bytes: int, file_name: str):
        """Track a file deletion"""
        db = await self._get_db()

        result = await db.storage_stats.update_one(
            {"provider": provider},
            {
                "$inc": {
                    "total_size_bytes": -file_size_bytes,
                    "file_count": -1
                },
                "$set": {
                    "last_updated": datetime.utcnow()
                }
            }
        )

        # Get updated stats to check if we're below limit now
        stats = await db.storage_stats.find_one({"provider": provider})
        if stats:
            # Update Prometheus metrics
            storage_usage_bytes.labels(provider=provider).set(stats["total_size_bytes"])
            storage_file_count.labels(provider=provider).set(stats["file_count"])

            limit = settings.STORAGE_LIMIT_BYTES
            if stats["total_size_bytes"] < limit:
                # Reset is_full and alert_sent flags
                await db.storage_stats.update_one(
                    {"provider": provider},
                    {"$set": {"is_full": False, "alert_sent": False}}
                )

        logger.info(
            f"Storage tracking: {provider} removed {file_size_bytes} bytes "
            f"({file_size_bytes / (1024 ** 2):.2f} MB) for file: {file_name}"
        )

    async def get_provider_stats(self, provider: str) -> Optional[StorageStatsResponse]:
        """Get storage stats for a specific provider"""
        db = await self._get_db()

        # Ensure stats exist
        await self.initialize_provider_stats(provider)

        stats = await db.storage_stats.find_one({"provider": provider})
        if not stats:
            return None

        limit = settings.STORAGE_LIMIT_BYTES
        used = stats.get("total_size_bytes", 0)
        available = max(0, limit - used)
        used_percentage = (used / limit * 100) if limit > 0 else 0

        return StorageStatsResponse(
            provider=stats["provider"],
            total_size_bytes=used,
            total_size_gb=used / (1024 ** 3),
            file_count=stats.get("file_count", 0),
            available_bytes=available,
            available_gb=available / (1024 ** 3),
            used_percentage=used_percentage,
            is_full=stats.get("is_full", False),
            last_updated=stats.get("last_updated", datetime.utcnow())
        )

    async def get_all_stats(self) -> AllStorageStatsResponse:
        """Get storage stats for all providers"""
        available_providers = multi_storage.get_available_providers()
        provider_stats = []
        total_bytes = 0
        total_files = 0

        for provider in available_providers:
            stats = await self.get_provider_stats(provider)
            if stats:
                provider_stats.append(stats)
                total_bytes += stats.total_size_bytes
                total_files += stats.file_count

        return AllStorageStatsResponse(
            providers=provider_stats,
            total_size_bytes=total_bytes,
            total_size_gb=total_bytes / (1024 ** 3),
            total_file_count=total_files
        )

    async def get_available_providers_under_limit(self) -> list[str]:
        """Get list of providers that are not at capacity"""
        db = await self._get_db()
        available_providers = multi_storage.get_available_providers()

        # Initialize all providers
        for provider in available_providers:
            await self.initialize_provider_stats(provider)

        # Get providers that are not full
        providers_under_limit = []
        for provider in available_providers:
            stats = await db.storage_stats.find_one({"provider": provider})
            if stats and not stats.get("is_full", False):
                providers_under_limit.append(provider)

        return providers_under_limit


storage_tracker = StorageTracker()
