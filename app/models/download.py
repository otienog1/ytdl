from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class DownloadStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoInfo(BaseModel):
    id: str
    title: str
    thumbnail: str
    duration: int
    file_size: Optional[str] = None
    quality: Optional[str] = None


class Download(BaseModel):
    job_id: str = Field(alias="jobId")
    url: str
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: int = 0
    video_info: Optional[VideoInfo] = Field(None, alias="videoInfo")
    download_url: Optional[str] = Field(None, alias="downloadUrl")
    error: Optional[str] = None
    user_id: Optional[str] = Field(None, alias="userId")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DownloadResponse(BaseModel):
    job_id: str = Field(alias="jobId")
    status: DownloadStatus
    progress: int = 0
    video_info: Optional[VideoInfo] = Field(None, alias="videoInfo")
    download_url: Optional[str] = Field(None, alias="downloadUrl")
    error: Optional[str] = None

    class Config:
        populate_by_name = True
