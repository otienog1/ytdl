"""
Storage statistics API routes
"""
from fastapi import APIRouter
from app.services.storage_tracker import storage_tracker
from app.models.storage_stats import AllStorageStatsResponse

router = APIRouter(prefix="/api/storage", tags=["storage"])


@router.get("/stats", response_model=AllStorageStatsResponse)
async def get_storage_stats():
    """
    Get storage usage statistics for all cloud providers.

    Returns:
        - providers: List of provider statistics (GCS, Azure, S3)
        - total_size_bytes: Total storage used across all providers
        - total_size_gb: Total storage in GB
        - total_file_count: Total number of files across all providers

    Each provider includes:
        - provider: Provider name ("gcs", "azure", or "s3")
        - total_size_bytes: Current usage in bytes
        - total_size_gb: Current usage in GB
        - file_count: Number of files stored
        - available_bytes: Remaining storage (5GB - used)
        - available_gb: Remaining storage in GB
        - used_percentage: Percentage of 5GB limit used
        - is_full: Whether provider has reached 5GB limit
        - last_updated: Timestamp of last update
    """
    stats = await storage_tracker.get_all_stats()
    return stats
