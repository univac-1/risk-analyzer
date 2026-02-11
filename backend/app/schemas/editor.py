"""Pydantic schemas for timeline editor."""
from datetime import datetime
from enum import Enum
from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class EditActionType(str, Enum):
    """Type of edit action."""
    cut = "cut"
    mute = "mute"
    mosaic = "mosaic"
    telop = "telop"
    skip = "skip"


class EditSessionStatus(str, Enum):
    """Status of an edit session."""
    draft = "draft"
    exporting = "exporting"
    completed = "completed"


class ExportJobStatus(str, Enum):
    """Status of an export job."""
    none = "none"
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class MosaicOptions(BaseModel):
    """Options for mosaic/blur edit action."""
    x: int = Field(..., ge=0, description="X coordinate of mosaic region")
    y: int = Field(..., ge=0, description="Y coordinate of mosaic region")
    width: int = Field(..., gt=0, description="Width of mosaic region")
    height: int = Field(..., gt=0, description="Height of mosaic region")
    blur_strength: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Blur strength (1-100)"
    )


class TelopOptions(BaseModel):
    """Options for telop/text overlay edit action."""
    text: str = Field(..., min_length=1, max_length=500, description="Text content")
    x: int = Field(..., ge=0, description="X coordinate of text position")
    y: int = Field(..., ge=0, description="Y coordinate of text position")
    font_size: int = Field(..., gt=0, le=200, description="Font size in pixels")
    font_color: str = Field(..., description="Font color in hex format (e.g., #FFFFFF)")
    background_color: Optional[str] = Field(
        default=None,
        description="Background color in hex format (optional)"
    )


class EditActionInput(BaseModel):
    """Input schema for creating/updating an edit action."""
    id: Optional[UUID] = Field(default=None, description="Action ID for updates")
    risk_item_id: Optional[UUID] = Field(
        default=None,
        description="Associated risk item ID (optional)"
    )
    type: EditActionType = Field(..., description="Type of edit action")
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., ge=0, description="End time in seconds")
    options: Optional[Union[MosaicOptions, TelopOptions]] = Field(
        default=None,
        description="Action-specific options"
    )

    @model_validator(mode='after')
    def validate_time_range(self):
        """Validate that end_time is after start_time."""
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        return self


class EditActionResponse(BaseModel):
    """Response schema for an edit action."""
    id: UUID
    risk_item_id: Optional[UUID] = None
    type: EditActionType
    start_time: float
    end_time: float
    options: Optional[Union[MosaicOptions, TelopOptions]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EditSessionUpdate(BaseModel):
    """Request schema for updating an edit session."""
    actions: list[EditActionInput] = Field(
        default_factory=list,
        description="List of edit actions"
    )


class EditSessionResponse(BaseModel):
    """Response schema for an edit session."""
    id: UUID
    job_id: UUID
    status: EditSessionStatus
    actions: list[EditActionResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExportResponse(BaseModel):
    """Response schema for starting an export."""
    export_id: UUID
    status: ExportJobStatus


class ExportStatusResponse(BaseModel):
    """Response schema for export status."""
    export_id: Optional[UUID] = None
    status: ExportJobStatus
    progress: float = Field(default=0.0, ge=0, le=100, description="Progress percentage")
    error_message: Optional[str] = None


class VideoUrlResponse(BaseModel):
    """Response schema for video URL."""
    url: str
    expires_at: str


class DownloadUrlResponse(BaseModel):
    """Response schema for download URL."""
    url: str
    expires_at: str
