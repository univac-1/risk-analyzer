import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.models.database import SessionLocal
from app.models.job import AnalysisJob, Video, RiskItem as DBRiskItem
from app.schemas.job import (
    AnalysisJobResponse,
    AnalysisJobSummary,
    ProgressStatusResponse,
    PhaseProgress,
    VideoMetadata,
    Platform,
    JobStatus,
    PhaseStatus,
    RiskItemResponse,
    RiskAssessmentResponse,
    AnalysisResultResponse,
    RiskCategory,
    RiskLevel,
    RiskSource,
)
from app.services.progress import ProgressService
from app.services.storage import StorageService

router = APIRouter()


@router.get("", response_model=list[AnalysisJobSummary])
async def list_jobs():
    """
    ジョブ一覧を取得

    - 全ジョブをステータス付きで一覧取得
    - 作成日時の降順でソート
    """
    db = SessionLocal()
    try:
        jobs = (
            db.query(AnalysisJob)
            .join(Video)
            .order_by(AnalysisJob.created_at.desc())
            .all()
        )

        return [
            AnalysisJobSummary(
                id=job.id,
                status=JobStatus(job.status.value),
                video_name=job.video.original_name,
                created_at=job.created_at,
                completed_at=job.completed_at,
            )
            for job in jobs
        ]
    finally:
        db.close()


@router.get("/{job_id}", response_model=AnalysisJobResponse)
async def get_job(job_id: str):
    """
    ジョブ詳細を取得

    - 個別ジョブの詳細情報を取得
    """
    db = SessionLocal()
    try:
        job = (
            db.query(AnalysisJob)
            .join(Video)
            .filter(AnalysisJob.id == job_id)
            .first()
        )

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ジョブが見つかりません",
            )

        return AnalysisJobResponse(
            id=job.id,
            status=JobStatus(job.status.value),
            video_name=job.video.original_name,
            metadata=VideoMetadata(
                purpose=job.purpose,
                platform=Platform(job.platform.value),
                target_audience=job.target_audience,
            ),
            created_at=job.created_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
        )
    finally:
        db.close()


@router.get("/{job_id}/progress", response_model=ProgressStatusResponse)
async def get_job_progress(job_id: str):
    """
    ジョブの進捗状況を取得

    - フェーズ別進捗状況をRedisから取得
    - 推定残り時間を含む進捗ステータス返却
    """
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ジョブが見つかりません",
            )
    finally:
        db.close()

    progress_service = ProgressService()
    progress = progress_service.get_progress(job_id)

    if not progress:
        return ProgressStatusResponse(
            job_id=job_id,
            status=JobStatus.pending,
            overall=0.0,
            phases={
                "audio": PhaseProgress(status=PhaseStatus.pending, progress=0.0),
                "ocr": PhaseProgress(status=PhaseStatus.pending, progress=0.0),
                "video": PhaseProgress(status=PhaseStatus.pending, progress=0.0),
                "risk": PhaseProgress(status=PhaseStatus.pending, progress=0.0),
            },
            estimated_remaining_seconds=None,
        )

    return ProgressStatusResponse(
        job_id=progress["job_id"],
        status=JobStatus(progress["status"]),
        overall=progress["overall"],
        phases={
            phase: PhaseProgress(
                status=PhaseStatus(data["status"]),
                progress=data["progress"],
            )
            for phase, data in progress["phases"].items()
        },
        estimated_remaining_seconds=progress.get("estimated_remaining_seconds"),
    )


@router.get("/{job_id}/results", response_model=AnalysisResultResponse)
async def get_job_results(job_id: str):
    """
    解析結果を取得

    - 完了ジョブの解析結果を取得
    - リスク箇所をタイムコード順に返却
    """
    db = SessionLocal()
    try:
        job = (
            db.query(AnalysisJob)
            .join(Video)
            .filter(AnalysisJob.id == job_id)
            .first()
        )

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ジョブが見つかりません",
            )

        if job.status.value != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="解析がまだ完了していません",
            )

        risk_items = (
            db.query(DBRiskItem)
            .filter(DBRiskItem.job_id == job_id)
            .order_by(DBRiskItem.timestamp)
            .all()
        )

        job_response = AnalysisJobResponse(
            id=job.id,
            status=JobStatus(job.status.value),
            video_name=job.video.original_name,
            metadata=VideoMetadata(
                purpose=job.purpose,
                platform=Platform(job.platform.value),
                target_audience=job.target_audience,
            ),
            created_at=job.created_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
        )

        risk_item_responses = [
            RiskItemResponse(
                id=item.id,
                timestamp=item.timestamp,
                end_timestamp=item.end_timestamp,
                category=RiskCategory(item.category.value),
                subcategory=item.subcategory,
                score=item.score,
                level=RiskLevel(item.level.value),
                rationale=item.rationale,
                source=RiskSource(item.source.value),
                evidence=item.evidence,
            )
            for item in risk_items
        ]

        assessment = RiskAssessmentResponse(
            overall_score=job.overall_score or 0.0,
            risk_level=RiskLevel(job.risk_level.value) if job.risk_level else RiskLevel.none,
            risks=risk_item_responses,
        )

        video_url = None
        try:
            storage = StorageService()
            if job.video.file_path and storage.file_exists(job.video.file_path):
                video_url = storage.generate_presigned_url(job.video.file_path, expiration=3600)
        except Exception:
            pass

        return AnalysisResultResponse(job=job_response, assessment=assessment, video_url=video_url)

    finally:
        db.close()


@router.get("/{job_id}/events")
async def get_job_events(job_id: str):
    """
    SSEによるリアルタイム進捗配信

    - Server-Sent Events エンドポイント
    - 進捗更新をリアルタイムでクライアントに配信
    """
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ジョブが見つかりません",
            )
    finally:
        db.close()

    async def event_generator() -> AsyncGenerator[dict, None]:
        progress_service = ProgressService()
        last_progress = None

        while True:
            progress = progress_service.get_progress(job_id)

            if progress != last_progress:
                last_progress = progress
                yield {
                    "event": "progress",
                    "data": json.dumps(progress or {}),
                }

                if progress and progress.get("status") in ["completed", "failed"]:
                    yield {
                        "event": "complete",
                        "data": json.dumps({"status": progress.get("status")}),
                    }
                    break

            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())
