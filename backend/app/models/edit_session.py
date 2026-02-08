"""Edit session, edit action, and export job models for timeline editor."""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, DateTime, Enum, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.database import Base


class EditSessionStatus(str, PyEnum):
    """Status of an edit session."""
    draft = "draft"
    exporting = "exporting"
    completed = "completed"


class EditActionType(str, PyEnum):
    """Type of edit action."""
    cut = "cut"
    mute = "mute"
    mosaic = "mosaic"
    telop = "telop"
    skip = "skip"


class ExportJobStatus(str, PyEnum):
    """Status of an export job."""
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class EditSession(Base):
    """Edit session for a completed analysis job."""
    __tablename__ = "edit_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_jobs.id"),
        nullable=False,
        unique=True,
    )
    status = Column(
        Enum(EditSessionStatus),
        default=EditSessionStatus.draft,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    job = relationship("AnalysisJob", back_populates="edit_session")
    actions = relationship(
        "EditAction",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="EditAction.start_time",
    )
    export_jobs = relationship(
        "ExportJob",
        back_populates="session",
        order_by="ExportJob.created_at.desc()",
    )


class EditAction(Base):
    """An edit action within an edit session."""
    __tablename__ = "edit_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("edit_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    risk_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("risk_items.id"),
        nullable=True,
    )
    type = Column(Enum(EditActionType), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    options = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("EditSession", back_populates="actions")
    risk_item = relationship("RiskItem")


class ExportJob(Base):
    """An export job for rendering edited video."""
    __tablename__ = "export_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("edit_sessions.id"),
        nullable=False,
    )
    status = Column(
        Enum(ExportJobStatus),
        default=ExportJobStatus.pending,
        nullable=False,
    )
    output_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("EditSession", back_populates="export_jobs")
