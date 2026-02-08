from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status

from app.models.database import SessionLocal
from app.models.edit_session import ExportJob, ExportJobStatus
from app.models.job import AnalysisJob, Video
from app.schemas.editor import (
    EditSessionUpdate,
    EditSessionResponse,
    VideoUrlResponse,
    ExportResponse,
    ExportStatusResponse,
    DownloadUrlResponse,
)
from app.services.edit_session import EditSessionService
from app.services.export_progress import ExportProgressService
from app.services.storage import StorageService
from app.tasks.export import export_video

router = APIRouter()


@router.get("/{job_id}/video-url", response_model=VideoUrlResponse)
async def get_video_url(job_id: str):
    """
    動画URLを取得

    - ジョブIDから元動画の署名付きURLを生成
    - 有効期限は1時間
    """
    db = SessionLocal()
    try:
        job = (
            db.query(AnalysisJob)
            .join(Video)
            .filter(AnalysisJob.id == job_id)
            .first()
        )
        if not job or not job.video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ジョブが見つかりません",
            )

        storage_service = StorageService()
        url = storage_service.generate_presigned_url(job.video.file_path, expiration=3600)
        expires_at = datetime.utcnow() + timedelta(seconds=3600)

        return VideoUrlResponse(
            url=url,
            expires_at=expires_at.isoformat(),
        )
    finally:
        db.close()


@router.get("/{job_id}/edit-session", response_model=EditSessionResponse)
async def get_edit_session(job_id: str):
    """
    編集セッションを取得

    - 存在しない場合は新規作成
    """
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ジョブが見つかりません",
            )

        service = EditSessionService(db)
        session = service.get_or_create_session(job_id)
        return EditSessionResponse.model_validate(session)
    finally:
        db.close()


@router.put("/{job_id}/edit-session", response_model=EditSessionResponse)
async def update_edit_session(job_id: str, payload: EditSessionUpdate):
    """
    編集セッションを更新

    - 編集アクションの追加・更新・削除
    """
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ジョブが見つかりません",
            )

        service = EditSessionService(db)
        try:
            session = service.update_session(job_id, payload.actions)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        return EditSessionResponse.model_validate(session)
    finally:
        db.close()


@router.post("/{job_id}/export", response_model=ExportResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_export(job_id: str):
    """
    編集済み動画のエクスポートを開始

    - エクスポートジョブを作成し非同期タスクを起動
    """
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ジョブが見つかりません",
            )

        service = EditSessionService(db)
        session = service.get_or_create_session(job_id)

        latest_export = (
            db.query(ExportJob)
            .filter(ExportJob.session_id == session.id)
            .order_by(ExportJob.created_at.desc())
            .first()
        )
        if latest_export and latest_export.status in {
            ExportJobStatus.pending,
            ExportJobStatus.processing,
        }:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="エクスポート処理が進行中です",
            )

        export_job = ExportJob(session_id=session.id, status=ExportJobStatus.pending)
        db.add(export_job)
        db.commit()
        db.refresh(export_job)

        progress_service = ExportProgressService()
        progress_service.set_progress(str(export_job.id), "pending", 0.0)

        export_video.delay(str(export_job.id))

        return ExportResponse(
            export_id=export_job.id,
            status=ExportJobStatus.pending,
        )
    finally:
        db.close()


@router.get("/{job_id}/export/status", response_model=ExportStatusResponse)
async def get_export_status(job_id: str):
    """
    エクスポート進捗を取得
    """
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ジョブが見つかりません",
            )

        session = EditSessionService(db).get_session(job_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="編集セッションが見つかりません",
            )

        export_job = (
            db.query(ExportJob)
            .filter(ExportJob.session_id == session.id)
            .order_by(ExportJob.created_at.desc())
            .first()
        )
        if not export_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="エクスポートジョブが見つかりません",
            )

        progress_service = ExportProgressService()
        progress = progress_service.get_progress(str(export_job.id))
        if progress:
            return ExportStatusResponse(
                export_id=export_job.id,
                status=ExportJobStatus(progress["status"]),
                progress=progress.get("progress", 0.0),
                error_message=progress.get("error_message"),
            )

        return ExportStatusResponse(
            export_id=export_job.id,
            status=export_job.status,
            progress=0.0,
            error_message=export_job.error_message,
        )
    finally:
        db.close()


@router.get("/{job_id}/export/download", response_model=DownloadUrlResponse)
async def get_export_download(job_id: str):
    """
    編集済み動画のダウンロードURLを取得
    """
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ジョブが見つかりません",
            )

        session = EditSessionService(db).get_session(job_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="編集セッションが見つかりません",
            )

        export_job = (
            db.query(ExportJob)
            .filter(
                ExportJob.session_id == session.id,
                ExportJob.status == ExportJobStatus.completed,
            )
            .order_by(ExportJob.created_at.desc())
            .first()
        )
        if not export_job or not export_job.output_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="エクスポート済み動画が見つかりません",
            )

        storage_service = StorageService()
        url = storage_service.generate_presigned_url(export_job.output_path, expiration=3600)
        expires_at = datetime.utcnow() + timedelta(seconds=3600)

        return DownloadUrlResponse(
            url=url,
            expires_at=expires_at.isoformat(),
        )
    finally:
        db.close()
