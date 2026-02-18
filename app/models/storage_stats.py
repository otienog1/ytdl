"""
Storage statistics models
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StorageStats(BaseModel):
    """Storage statistics for a provider"""
    provider: str  # "gcs", "azure", "s3"
    total_size_bytes: int = 0
    file_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    alert_sent: bool = False  # Track if limit alert was sent
    is_full: bool = False  # Track if provider is at capacity

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "gcs",
                "total_size_bytes": 2147483648,
                "file_count": 42,
                "last_updated": "2026-02-13T12:00:00",
                "alert_sent": False,
                "is_full": False
            }
        }


class StorageStatsResponse(BaseModel):
    """API response for storage statistics"""
    provider: str
    total_size_bytes: int
    total_size_gb: float
    file_count: int
    available_bytes: int
    available_gb: float
    used_percentage: float
    is_full: bool
    last_updated: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "gcs",
                "total_size_bytes": 2147483648,
                "total_size_gb": 2.0,
                "file_count": 42,
                "available_bytes": 3221225472,
                "available_gb": 3.0,
                "used_percentage": 40.0,
                "is_full": False,
                "last_updated": "2026-02-13T12:00:00"
            }
        }


class AllStorageStatsResponse(BaseModel):
    """API response for all storage providers"""
    providers: list[StorageStatsResponse]
    total_size_bytes: int
    total_size_gb: float
    total_file_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "providers": [],
                "total_size_bytes": 4294967296,
                "total_size_gb": 4.0,
                "total_file_count": 84
            }
        }


class EnhancedStorageStatsResponse(BaseModel):
    """Enhanced storage statistics with totals and availability"""
    providers: list[StorageStatsResponse]
    total_used_gb: float
    total_available_gb: float
    overall_used_percentage: float

    class Config:
        json_schema_extra = {
            "example": {
                "providers": [],
                "total_used_gb": 4.0,
                "total_available_gb": 11.0,
                "overall_used_percentage": 26.67
            }
        }
