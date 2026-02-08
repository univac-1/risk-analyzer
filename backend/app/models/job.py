import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, String, DateTime, Enum, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.database import Base


class JobStatus(str, PyEnum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Platform(str, PyEnum):
    twitter = "twitter"
    instagram = "instagram"
    youtube = "youtube"
    tiktok = "tiktok"
    other = "other"


class RiskCategory(str, PyEnum):
    aggressiveness = "aggressiveness"
    discrimination = "discrimination"
    misleading = "misleading"


class RiskLevel(str, PyEnum):
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"


class RiskSource(str, PyEnum):
    audio = "audio"
    ocr = "ocr"
    video = "video"


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    duration = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    job = relationship("AnalysisJob", back_populates="video", uselist=False)


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.pending)
    purpose = Column(String, nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    target_audience = Column(String, nullable=False)
    overall_score = Column(Float, nullable=True)
    risk_level = Column(Enum(RiskLevel), nullable=True)
    transcription_result = Column(JSON, nullable=True)
    ocr_result = Column(JSON, nullable=True)
    video_analysis_result = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    video = relationship("Video", back_populates="job")
    risk_items = relationship("RiskItem", back_populates="job", cascade="all, delete-orphan")
    edit_session = relationship("EditSession", back_populates="job", uselist=False)


class RiskItem(Base):
    __tablename__ = "risk_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("analysis_jobs.id"), nullable=False)
    timestamp = Column(Float, nullable=False)
    end_timestamp = Column(Float, nullable=False)
    category = Column(Enum(RiskCategory), nullable=False)
    subcategory = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    level = Column(Enum(RiskLevel), nullable=False)
    rationale = Column(String, nullable=False)
    source = Column(Enum(RiskSource), nullable=False)
    evidence = Column(String, nullable=False)

    job = relationship("AnalysisJob", back_populates="risk_items")
