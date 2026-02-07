from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, ConfigDict


class Platform(str, Enum):
    twitter = "twitter"
    instagram = "instagram"
    youtube = "youtube"
    tiktok = "tiktok"
    other = "other"


class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class PhaseStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class RiskCategory(str, Enum):
    aggressiveness = "aggressiveness"
    discrimination = "discrimination"
    misleading = "misleading"


class RiskLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"


class RiskSource(str, Enum):
    audio = "audio"
    ocr = "ocr"
    video = "video"


class VideoMetadata(BaseModel):
    purpose: str = Field(..., min_length=1, max_length=500)
    platform: Platform
    target_audience: str = Field(..., min_length=1, max_length=500)


class AnalysisJobResponse(BaseModel):
    id: UUID
    status: JobStatus
    video_name: str
    metadata: VideoMetadata
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    @field_serializer('created_at', 'completed_at')
    def serialize_datetime(self, dt: Optional[datetime], _info) -> Optional[str]:
        """datetimeをISO 8601形式（UTC）でシリアライズ"""
        if dt is None:
            return None
        # naive datetimeの場合、UTCとして扱う
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    model_config = ConfigDict(from_attributes=True)


class AnalysisJobSummary(BaseModel):
    id: UUID
    status: JobStatus
    video_name: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    @field_serializer('created_at', 'completed_at')
    def serialize_datetime(self, dt: Optional[datetime], _info) -> Optional[str]:
        """datetimeをISO 8601形式（UTC）でシリアライズ"""
        if dt is None:
            return None
        # naive datetimeの場合、UTCとして扱う
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    model_config = ConfigDict(from_attributes=True)


class PhaseProgress(BaseModel):
    status: PhaseStatus
    progress: float = Field(..., ge=0, le=100)


class ProgressStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    overall: float = Field(..., ge=0, le=100)
    phases: dict[str, PhaseProgress]
    estimated_remaining_seconds: Optional[float] = None


class RiskItemResponse(BaseModel):
    id: UUID
    timestamp: float
    end_timestamp: float
    category: RiskCategory
    subcategory: str
    score: float
    level: RiskLevel
    rationale: str
    source: RiskSource
    evidence: str

    model_config = ConfigDict(from_attributes=True)


class RiskAssessmentResponse(BaseModel):
    overall_score: float
    risk_level: RiskLevel
    risks: list[RiskItemResponse]


class AnalysisResultResponse(BaseModel):
    job: AnalysisJobResponse
    assessment: RiskAssessmentResponse
    video_url: Optional[str] = None
