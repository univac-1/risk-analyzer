import logging
import os
import tempfile
from datetime import datetime

from app.celery_app import celery_app
from app.models.database import SessionLocal
from app.models.edit_session import ExportJob, ExportJobStatus, EditSessionStatus
from app.services.export_progress import ExportProgressService
from app.services.storage import StorageService
from app.services.video_editor import VideoEditorService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2)
def export_video(self, export_id: str) -> dict:
    """
    編集済み動画のエクスポートタスク

    Args:
        export_id: エクスポートジョブID
    """
    db = SessionLocal()
    progress_service = ExportProgressService()
    export_job = None
    try:
        export_job = (
            db.query(ExportJob)
            .filter(ExportJob.id == export_id)
            .first()
        )
        if not export_job:
            progress_service.set_progress(export_id, "failed", 0.0, "Export job not found")
            return {"export_id": export_id, "status": "failed", "error": "Export job not found"}

        session = export_job.session
        job = session.job if session else None
        if not session or not job or not job.video:
            progress_service.set_progress(export_id, "failed", 0.0, "Job or session not found")
            export_job.status = ExportJobStatus.failed
            export_job.error_message = "Job or session not found"
            db.commit()
            return {"export_id": export_id, "status": "failed", "error": "Job or session not found"}

        export_job.status = ExportJobStatus.processing
        session.status = EditSessionStatus.exporting
        db.commit()

        progress_service.set_progress(export_id, "processing", 0.0)

        storage_service = StorageService()
        editor_service = VideoEditorService()
        duration_seconds = job.video.duration
        output_key = f"exports/{job.id}/{export_id}.mp4"

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.mp4")
            output_path = os.path.join(tmpdir, "output.mp4")

            storage_service.download_file(job.video.file_path, input_path)

            def on_progress(value: float) -> None:
                progress_service.set_progress(export_id, "processing", value)

            editor_service.run_ffmpeg(
                input_path,
                output_path,
                session.actions,
                on_progress=on_progress,
                duration_seconds=duration_seconds,
            )

            with open(output_path, "rb") as output_file:
                storage_service.upload_file_to_path(
                    output_file,
                    output_key,
                    content_type="video/mp4",
                )

        export_job.status = ExportJobStatus.completed
        export_job.output_path = output_key
        export_job.completed_at = datetime.utcnow()
        session.status = EditSessionStatus.completed
        db.commit()

        progress_service.set_progress(export_id, "completed", 100.0)
        return {"export_id": export_id, "status": "completed"}
    except Exception as exc:
        logger.error("Export task failed: %s", exc, exc_info=True)
        if export_job:
            export_job.status = ExportJobStatus.failed
            export_job.error_message = str(exc)
            db.commit()
        progress_service.set_progress(export_id, "failed", 0.0, str(exc))
        raise
    finally:
        db.close()
