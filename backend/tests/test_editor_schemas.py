"""Tests for editor Pydantic schemas."""
import pytest
from datetime import datetime
from uuid import uuid4
from pydantic import ValidationError

from app.schemas.editor import (
    EditActionType,
    EditSessionStatus,
    ExportJobStatus,
    MosaicOptions,
    TelopOptions,
    EditActionInput,
    EditActionResponse,
    EditSessionUpdate,
    EditSessionResponse,
    ExportStatusResponse,
    VideoUrlResponse,
    DownloadUrlResponse,
)


class TestEnums:
    """Tests for editor enums."""

    def test_edit_action_type_values(self):
        """Verify all edit action type values."""
        assert EditActionType.cut == "cut"
        assert EditActionType.mute == "mute"
        assert EditActionType.mosaic == "mosaic"
        assert EditActionType.telop == "telop"
        assert EditActionType.skip == "skip"

    def test_edit_session_status_values(self):
        """Verify all edit session status values."""
        assert EditSessionStatus.draft == "draft"
        assert EditSessionStatus.exporting == "exporting"
        assert EditSessionStatus.completed == "completed"

    def test_export_job_status_values(self):
        """Verify all export job status values."""
        assert ExportJobStatus.pending == "pending"
        assert ExportJobStatus.processing == "processing"
        assert ExportJobStatus.completed == "completed"
        assert ExportJobStatus.failed == "failed"


class TestMosaicOptions:
    """Tests for MosaicOptions schema."""

    def test_valid_mosaic_options(self):
        """Test creating valid mosaic options."""
        options = MosaicOptions(x=100, y=100, width=200, height=200)
        assert options.x == 100
        assert options.y == 100
        assert options.width == 200
        assert options.height == 200
        assert options.blur_strength == 10  # default

    def test_mosaic_options_with_blur_strength(self):
        """Test mosaic options with custom blur strength."""
        options = MosaicOptions(x=50, y=50, width=100, height=100, blur_strength=20)
        assert options.blur_strength == 20

    def test_mosaic_options_negative_values_rejected(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValidationError):
            MosaicOptions(x=-10, y=100, width=200, height=200)

    def test_mosaic_options_zero_dimensions_rejected(self):
        """Test that zero dimensions are rejected."""
        with pytest.raises(ValidationError):
            MosaicOptions(x=100, y=100, width=0, height=200)


class TestTelopOptions:
    """Tests for TelopOptions schema."""

    def test_valid_telop_options(self):
        """Test creating valid telop options."""
        options = TelopOptions(
            text="Sample text",
            x=50,
            y=400,
            font_size=24,
            font_color="#FFFFFF",
        )
        assert options.text == "Sample text"
        assert options.x == 50
        assert options.y == 400
        assert options.font_size == 24
        assert options.font_color == "#FFFFFF"
        assert options.background_color is None

    def test_telop_options_with_background(self):
        """Test telop options with background color."""
        options = TelopOptions(
            text="Test",
            x=0,
            y=0,
            font_size=16,
            font_color="#000000",
            background_color="#FFFF00",
        )
        assert options.background_color == "#FFFF00"

    def test_telop_options_empty_text_rejected(self):
        """Test that empty text is rejected."""
        with pytest.raises(ValidationError):
            TelopOptions(
                text="",
                x=50,
                y=400,
                font_size=24,
                font_color="#FFFFFF",
            )

    def test_telop_options_invalid_font_size_rejected(self):
        """Test that invalid font size is rejected."""
        with pytest.raises(ValidationError):
            TelopOptions(
                text="Test",
                x=50,
                y=400,
                font_size=0,
                font_color="#FFFFFF",
            )

    def test_telop_options_japanese_text(self):
        """Test telop options with Japanese text."""
        options = TelopOptions(
            text="日本語テキスト",
            x=100,
            y=300,
            font_size=32,
            font_color="#FFFFFF",
        )
        assert options.text == "日本語テキスト"


class TestEditActionInput:
    """Tests for EditActionInput schema."""

    def test_valid_cut_action(self):
        """Test creating a valid cut action."""
        action = EditActionInput(
            type=EditActionType.cut,
            start_time=10.0,
            end_time=20.0,
        )
        assert action.type == EditActionType.cut
        assert action.start_time == 10.0
        assert action.end_time == 20.0
        assert action.risk_item_id is None
        assert action.options is None

    def test_valid_mute_action(self):
        """Test creating a valid mute action."""
        action = EditActionInput(
            type=EditActionType.mute,
            start_time=5.0,
            end_time=15.0,
        )
        assert action.type == EditActionType.mute

    def test_valid_mosaic_action_with_options(self):
        """Test creating a mosaic action with options."""
        action = EditActionInput(
            type=EditActionType.mosaic,
            start_time=0.0,
            end_time=5.0,
            options=MosaicOptions(x=100, y=100, width=200, height=200),
        )
        assert action.type == EditActionType.mosaic
        assert action.options.x == 100

    def test_valid_telop_action_with_options(self):
        """Test creating a telop action with options."""
        action = EditActionInput(
            type=EditActionType.telop,
            start_time=30.0,
            end_time=40.0,
            options=TelopOptions(
                text="テスト",
                x=50,
                y=400,
                font_size=24,
                font_color="#FFFFFF",
            ),
        )
        assert action.type == EditActionType.telop
        assert action.options.text == "テスト"

    def test_action_with_risk_item_id(self):
        """Test action linked to a risk item."""
        risk_id = uuid4()
        action = EditActionInput(
            risk_item_id=risk_id,
            type=EditActionType.cut,
            start_time=10.0,
            end_time=20.0,
        )
        assert action.risk_item_id == risk_id

    def test_action_with_existing_id(self):
        """Test action with existing id for updates."""
        action_id = uuid4()
        action = EditActionInput(
            id=action_id,
            type=EditActionType.mute,
            start_time=5.0,
            end_time=10.0,
        )
        assert action.id == action_id

    def test_end_time_must_be_after_start_time(self):
        """Test that end time must be after start time."""
        with pytest.raises(ValidationError):
            EditActionInput(
                type=EditActionType.cut,
                start_time=20.0,
                end_time=10.0,
            )

    def test_negative_times_rejected(self):
        """Test that negative times are rejected."""
        with pytest.raises(ValidationError):
            EditActionInput(
                type=EditActionType.cut,
                start_time=-5.0,
                end_time=10.0,
            )


class TestEditActionResponse:
    """Tests for EditActionResponse schema."""

    def test_valid_response(self):
        """Test creating a valid action response."""
        action_id = uuid4()
        response = EditActionResponse(
            id=action_id,
            type=EditActionType.cut,
            start_time=10.0,
            end_time=20.0,
            created_at=datetime.utcnow(),
        )
        assert response.id == action_id
        assert response.type == EditActionType.cut


class TestEditSessionUpdate:
    """Tests for EditSessionUpdate schema."""

    def test_valid_session_update(self):
        """Test creating a valid session update."""
        update = EditSessionUpdate(
            actions=[
                EditActionInput(
                    type=EditActionType.cut,
                    start_time=10.0,
                    end_time=20.0,
                ),
                EditActionInput(
                    type=EditActionType.mute,
                    start_time=30.0,
                    end_time=40.0,
                ),
            ]
        )
        assert len(update.actions) == 2

    def test_empty_actions_allowed(self):
        """Test that empty actions list is allowed."""
        update = EditSessionUpdate(actions=[])
        assert len(update.actions) == 0


class TestEditSessionResponse:
    """Tests for EditSessionResponse schema."""

    def test_valid_response(self):
        """Test creating a valid session response."""
        session_id = uuid4()
        job_id = uuid4()
        response = EditSessionResponse(
            id=session_id,
            job_id=job_id,
            status=EditSessionStatus.draft,
            actions=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert response.id == session_id
        assert response.job_id == job_id
        assert response.status == EditSessionStatus.draft


class TestExportStatusResponse:
    """Tests for ExportStatusResponse schema."""

    def test_pending_export(self):
        """Test pending export status."""
        export_id = uuid4()
        response = ExportStatusResponse(
            export_id=export_id,
            status=ExportJobStatus.pending,
            progress=0.0,
        )
        assert response.status == ExportJobStatus.pending
        assert response.progress == 0.0
        assert response.error_message is None

    def test_processing_export(self):
        """Test processing export status."""
        export_id = uuid4()
        response = ExportStatusResponse(
            export_id=export_id,
            status=ExportJobStatus.processing,
            progress=50.0,
        )
        assert response.status == ExportJobStatus.processing
        assert response.progress == 50.0

    def test_completed_export(self):
        """Test completed export status."""
        export_id = uuid4()
        response = ExportStatusResponse(
            export_id=export_id,
            status=ExportJobStatus.completed,
            progress=100.0,
        )
        assert response.status == ExportJobStatus.completed
        assert response.progress == 100.0

    def test_failed_export(self):
        """Test failed export status with error."""
        export_id = uuid4()
        response = ExportStatusResponse(
            export_id=export_id,
            status=ExportJobStatus.failed,
            progress=30.0,
            error_message="FFmpeg encoding error",
        )
        assert response.status == ExportJobStatus.failed
        assert response.error_message == "FFmpeg encoding error"

    def test_progress_validation(self):
        """Test that progress must be between 0 and 100."""
        with pytest.raises(ValidationError):
            ExportStatusResponse(
                export_id=uuid4(),
                status=ExportJobStatus.processing,
                progress=150.0,
            )


class TestVideoUrlResponse:
    """Tests for VideoUrlResponse schema."""

    def test_valid_response(self):
        """Test creating a valid video URL response."""
        response = VideoUrlResponse(
            url="https://example.com/video.mp4",
            expires_at="2026-01-01T01:00:00Z",
        )
        assert response.url == "https://example.com/video.mp4"
        assert response.expires_at == "2026-01-01T01:00:00Z"


class TestDownloadUrlResponse:
    """Tests for DownloadUrlResponse schema."""

    def test_valid_response(self):
        """Test creating a valid download URL response."""
        response = DownloadUrlResponse(
            url="https://example.com/edited_video.mp4",
            expires_at="2026-01-01T01:00:00Z",
        )
        assert response.url == "https://example.com/edited_video.mp4"
