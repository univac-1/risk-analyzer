import logging
import os
import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

logger = logging.getLogger(__name__)

from app.config import get_settings
from app.models.database import SessionLocal
from app.models.job import AnalysisJob, Video, Platform as DBPlatform, JobStatus
from app.schemas.job import AnalysisJobResponse, VideoMetadata, Platform
from app.services.storage import StorageService
from app.services.progress import ProgressService
from app.tasks.analyze import analyze_video

router = APIRouter()
settings = get_settings()


def validate_file(file: UploadFile) -> None:
    """ファイルのバリデーション"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ファイル名が指定されていません",
        )

    extension = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if extension not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"サポートされていないファイル形式です。対応形式: {settings.allowed_extensions}",
        )

    if file.content_type and not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="動画ファイルを指定してください",
        )


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=AnalysisJobResponse)
async def upload_video(
    file: Annotated[UploadFile, File(description="動画ファイル（mp4形式）")],
    purpose: Annotated[str, Form(description="動画の用途")],
    platform: Annotated[Platform, Form(description="投稿先媒体")],
    target_audience: Annotated[str, Form(description="想定ターゲット")],
):
    """
    動画をアップロードし、解析を開始する

    - 動画ファイルをストレージに保存
    - ジョブレコードを作成
    - 解析タスクを登録
    - ジョブIDを返却（非同期処理）
    """
    validate_file(file)

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"ファイルサイズが上限を超えています。上限: {settings.max_file_size_mb}MB",
        )

    storage_service = StorageService()
    try:
        file_path = storage_service.upload_file(
            file.file,
            file.filename,
            file.content_type or "video/mp4",
        )
    except Exception as e:
        logger.error(f"ストレージへのアップロードに失敗しました: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ストレージへのアップロードに失敗しました: {str(e)}",
        )

    db = SessionLocal()
    try:
        video = Video(
            id=uuid.uuid4(),
            file_path=file_path,
            original_name=file.filename,
            file_size=file_size,
        )
        db.add(video)
        db.flush()

        job = AnalysisJob(
            id=uuid.uuid4(),
            video_id=video.id,
            status=JobStatus.pending,
            purpose=purpose,
            platform=DBPlatform(platform.value),
            target_audience=target_audience,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        db.refresh(video)

        logger.info(f"動画アップロード成功: job_id={job.id}, file={video.original_name}")

        progress_service = ProgressService()
        progress_service.initialize_progress(str(job.id))

        analyze_video.delay(
            str(job.id),
            file_path,
            {
                "purpose": purpose,
                "platform": platform.value,
                "target_audience": target_audience,
            },
        )

        return AnalysisJobResponse(
            id=job.id,
            status=job.status,
            video_name=video.original_name,
            metadata=VideoMetadata(
                purpose=purpose,
                platform=platform,
                target_audience=target_audience,
            ),
            created_at=job.created_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
        )

    except Exception as e:
        logger.error(f"アップロード処理中にエラーが発生しました: {e}", exc_info=True)
        db.rollback()
        try:
            storage_service.delete_file(file_path)
        except Exception as delete_error:
            logger.warning(f"アップロード失敗後のファイル削除に失敗しました: {delete_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"アップロードに失敗しました: {str(e)}",
        )
    finally:
        db.close()
