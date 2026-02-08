"""Tests for edit session, edit action, and export job models."""
import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import Base
from app.models.job import AnalysisJob, Video, JobStatus, Platform
from app.models.edit_session import (
    EditSession,
    EditAction,
    ExportJob,
    EditSessionStatus,
    EditActionType,
    ExportJobStatus,
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_video(db_session):
    """Create a sample video for testing."""
    video = Video(
        id=uuid.uuid4(),
        file_path="/test/video.mp4",
        original_name="video.mp4",
        file_size=1000000,
        duration=120.0,
    )
    db_session.add(video)
    db_session.commit()
    return video


@pytest.fixture
def sample_job(db_session, sample_video):
    """Create a sample analysis job for testing."""
    job = AnalysisJob(
        id=uuid.uuid4(),
        video_id=sample_video.id,
        status=JobStatus.completed,
        purpose="Test",
        platform=Platform.twitter,
        target_audience="general",
    )
    db_session.add(job)
    db_session.commit()
    return job


class TestEditSessionStatus:
    """Tests for EditSessionStatus enum."""

    def test_status_values(self):
        """Verify all expected status values exist."""
        assert EditSessionStatus.draft == "draft"
        assert EditSessionStatus.exporting == "exporting"
        assert EditSessionStatus.completed == "completed"


class TestEditActionType:
    """Tests for EditActionType enum."""

    def test_action_type_values(self):
        """Verify all expected action type values exist."""
        assert EditActionType.cut == "cut"
        assert EditActionType.mute == "mute"
        assert EditActionType.mosaic == "mosaic"
        assert EditActionType.telop == "telop"
        assert EditActionType.skip == "skip"


class TestExportJobStatus:
    """Tests for ExportJobStatus enum."""

    def test_export_status_values(self):
        """Verify all expected export status values exist."""
        assert ExportJobStatus.pending == "pending"
        assert ExportJobStatus.processing == "processing"
        assert ExportJobStatus.completed == "completed"
        assert ExportJobStatus.failed == "failed"


class TestEditSession:
    """Tests for EditSession model."""

    def test_create_edit_session(self, db_session, sample_job):
        """Test creating an edit session."""
        session = EditSession(
            job_id=sample_job.id,
            status=EditSessionStatus.draft,
        )
        db_session.add(session)
        db_session.commit()

        assert session.id is not None
        assert session.job_id == sample_job.id
        assert session.status == EditSessionStatus.draft
        assert session.created_at is not None
        assert session.updated_at is not None

    def test_edit_session_default_status(self, db_session, sample_job):
        """Test that edit session defaults to draft status."""
        session = EditSession(job_id=sample_job.id)
        db_session.add(session)
        db_session.commit()

        assert session.status == EditSessionStatus.draft

    def test_edit_session_job_relationship(self, db_session, sample_job):
        """Test edit session relationship with analysis job."""
        session = EditSession(job_id=sample_job.id)
        db_session.add(session)
        db_session.commit()

        db_session.refresh(session)
        assert session.job is not None
        assert session.job.id == sample_job.id

    def test_unique_job_constraint(self, db_session, sample_job):
        """Test that only one edit session can exist per job."""
        session1 = EditSession(job_id=sample_job.id)
        db_session.add(session1)
        db_session.commit()

        session2 = EditSession(job_id=sample_job.id)
        db_session.add(session2)
        with pytest.raises(Exception):  # IntegrityError for unique constraint
            db_session.commit()


class TestEditAction:
    """Tests for EditAction model."""

    def test_create_edit_action(self, db_session, sample_job):
        """Test creating an edit action."""
        session = EditSession(job_id=sample_job.id)
        db_session.add(session)
        db_session.commit()

        action = EditAction(
            session_id=session.id,
            type=EditActionType.cut,
            start_time=10.0,
            end_time=20.0,
        )
        db_session.add(action)
        db_session.commit()

        assert action.id is not None
        assert action.session_id == session.id
        assert action.type == EditActionType.cut
        assert action.start_time == 10.0
        assert action.end_time == 20.0
        assert action.risk_item_id is None
        assert action.options is None
        assert action.created_at is not None

    def test_edit_action_with_options(self, db_session, sample_job):
        """Test creating an edit action with options."""
        session = EditSession(job_id=sample_job.id)
        db_session.add(session)
        db_session.commit()

        mosaic_options = {
            "x": 100,
            "y": 100,
            "width": 200,
            "height": 200,
            "blurStrength": 10,
        }
        action = EditAction(
            session_id=session.id,
            type=EditActionType.mosaic,
            start_time=5.0,
            end_time=15.0,
            options=mosaic_options,
        )
        db_session.add(action)
        db_session.commit()

        db_session.refresh(action)
        assert action.options == mosaic_options

    def test_edit_action_telop_options(self, db_session, sample_job):
        """Test creating a telop action with text options."""
        session = EditSession(job_id=sample_job.id)
        db_session.add(session)
        db_session.commit()

        telop_options = {
            "text": "Sample telop text",
            "x": 50,
            "y": 400,
            "fontSize": 24,
            "fontColor": "#FFFFFF",
            "backgroundColor": "#000000",
        }
        action = EditAction(
            session_id=session.id,
            type=EditActionType.telop,
            start_time=30.0,
            end_time=40.0,
            options=telop_options,
        )
        db_session.add(action)
        db_session.commit()

        db_session.refresh(action)
        assert action.options["text"] == "Sample telop text"

    def test_edit_action_session_relationship(self, db_session, sample_job):
        """Test edit action relationship with edit session."""
        session = EditSession(job_id=sample_job.id)
        db_session.add(session)
        db_session.commit()

        action = EditAction(
            session_id=session.id,
            type=EditActionType.mute,
            start_time=0.0,
            end_time=5.0,
        )
        db_session.add(action)
        db_session.commit()

        db_session.refresh(session)
        assert len(session.actions) == 1
        assert session.actions[0].id == action.id

    def test_cascade_delete_actions(self, db_session, sample_job):
        """Test that actions are deleted when session is deleted."""
        session = EditSession(job_id=sample_job.id)
        db_session.add(session)
        db_session.commit()

        action1 = EditAction(
            session_id=session.id,
            type=EditActionType.cut,
            start_time=10.0,
            end_time=20.0,
        )
        action2 = EditAction(
            session_id=session.id,
            type=EditActionType.mute,
            start_time=30.0,
            end_time=40.0,
        )
        db_session.add_all([action1, action2])
        db_session.commit()

        session_id = session.id
        db_session.delete(session)
        db_session.commit()

        # Verify actions are deleted
        remaining_actions = db_session.query(EditAction).filter(
            EditAction.session_id == session_id
        ).all()
        assert len(remaining_actions) == 0


class TestExportJob:
    """Tests for ExportJob model."""

    def test_create_export_job(self, db_session, sample_job):
        """Test creating an export job."""
        session = EditSession(job_id=sample_job.id)
        db_session.add(session)
        db_session.commit()

        export = ExportJob(
            session_id=session.id,
            status=ExportJobStatus.pending,
        )
        db_session.add(export)
        db_session.commit()

        assert export.id is not None
        assert export.session_id == session.id
        assert export.status == ExportJobStatus.pending
        assert export.output_path is None
        assert export.error_message is None
        assert export.created_at is not None
        assert export.completed_at is None

    def test_export_job_default_status(self, db_session, sample_job):
        """Test that export job defaults to pending status."""
        session = EditSession(job_id=sample_job.id)
        db_session.add(session)
        db_session.commit()

        export = ExportJob(session_id=session.id)
        db_session.add(export)
        db_session.commit()

        assert export.status == ExportJobStatus.pending

    def test_export_job_completion(self, db_session, sample_job):
        """Test completing an export job."""
        session = EditSession(job_id=sample_job.id)
        db_session.add(session)
        db_session.commit()

        export = ExportJob(session_id=session.id)
        db_session.add(export)
        db_session.commit()

        # Complete the export
        export.status = ExportJobStatus.completed
        export.output_path = "/exports/edited_video.mp4"
        export.completed_at = datetime.utcnow()
        db_session.commit()

        db_session.refresh(export)
        assert export.status == ExportJobStatus.completed
        assert export.output_path == "/exports/edited_video.mp4"
        assert export.completed_at is not None

    def test_export_job_failure(self, db_session, sample_job):
        """Test failed export job with error message."""
        session = EditSession(job_id=sample_job.id)
        db_session.add(session)
        db_session.commit()

        export = ExportJob(session_id=session.id)
        db_session.add(export)
        db_session.commit()

        # Fail the export
        export.status = ExportJobStatus.failed
        export.error_message = "FFmpeg encoding error"
        db_session.commit()

        db_session.refresh(export)
        assert export.status == ExportJobStatus.failed
        assert export.error_message == "FFmpeg encoding error"

    def test_export_job_session_relationship(self, db_session, sample_job):
        """Test export job relationship with edit session."""
        session = EditSession(job_id=sample_job.id)
        db_session.add(session)
        db_session.commit()

        export1 = ExportJob(session_id=session.id)
        export2 = ExportJob(session_id=session.id)
        db_session.add_all([export1, export2])
        db_session.commit()

        db_session.refresh(session)
        assert len(session.export_jobs) == 2

    def test_multiple_exports_per_session(self, db_session, sample_job):
        """Test that multiple export jobs can exist per session (re-export)."""
        session = EditSession(job_id=sample_job.id)
        db_session.add(session)
        db_session.commit()

        # First export
        export1 = ExportJob(
            session_id=session.id,
            status=ExportJobStatus.completed,
            output_path="/exports/v1.mp4",
        )
        db_session.add(export1)
        db_session.commit()

        # Second export (re-export)
        export2 = ExportJob(
            session_id=session.id,
            status=ExportJobStatus.pending,
        )
        db_session.add(export2)
        db_session.commit()

        exports = db_session.query(ExportJob).filter(
            ExportJob.session_id == session.id
        ).all()
        assert len(exports) == 2
