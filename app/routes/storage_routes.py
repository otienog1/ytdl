"""
Storage statistics API routes
"""
from fastapi import APIRouter
from app.services.storage_tracker import storage_tracker
from app.models.storage_stats import AllStorageStatsResponse, EnhancedStorageStatsResponse

router = APIRouter(prefix="/api/storage", tags=["storage"])


@router.get("/stats", response_model=EnhancedStorageStatsResponse)
async def get_storage_stats():
    """
    Get enhanced storage usage statistics for all cloud providers.

    Returns:
        - providers: List of provider statistics (GCS, Azure, S3)
        - total_used_gb: Total storage used in GB
        - total_available_gb: Total available storage in GB
        - overall_used_percentage: Overall storage usage percentage

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

    # Calculate enhanced totals
    total_used_bytes = sum(p.total_size_bytes for p in stats.providers)
    total_available_bytes = sum(p.available_bytes for p in stats.providers)
    total_capacity_bytes = total_used_bytes + total_available_bytes

    total_used_gb = total_used_bytes / (1024 ** 3)
    total_available_gb = total_available_bytes / (1024 ** 3)
    overall_used_percentage = (total_used_bytes / total_capacity_bytes * 100) if total_capacity_bytes > 0 else 0

    return EnhancedStorageStatsResponse(
        providers=stats.providers,
        total_used_gb=total_used_gb,
        total_available_gb=total_available_gb,
        overall_used_percentage=overall_used_percentage
    )
