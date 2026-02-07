import logging
from datetime import datetime

from celery import shared_task

from app.celery_app import celery_app
from app.models.database import SessionLocal
from app.models.job import AnalysisJob, JobStatus

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def analyze_video(self, job_id: str, video_path: str, metadata: dict) -> dict:
    """
    動画解析タスク

    Args:
        job_id: 解析ジョブID
        video_path: 動画ファイルパス（Storage内）
        metadata: メタ情報（purpose, platform, target_audience）

    Returns:
        解析結果のサマリー

    Raises:
        タスク失敗時は自動リトライ後にfailed状態に更新
    """
    logger.info(f"解析タスク開始: job_id={job_id}, video_path={video_path}")

    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if not job:
            logger.error(f"ジョブが見つかりません: job_id={job_id}")
            return {"error": f"Job {job_id} not found"}

        job.status = JobStatus.processing
        db.commit()

        from app.services.orchestrator import OrchestratorService
        from app.services.progress import ProgressService

        progress_service = ProgressService()
        orchestrator = OrchestratorService(progress_service)

        try:
            result = orchestrator.run_analysis(job_id, video_path, metadata)

            job.status = JobStatus.completed
            job.completed_at = datetime.utcnow()
            job.overall_score = result.get("overall_score")
            job.risk_level = result.get("risk_level")
            job.transcription_result = result.get("transcription")
            job.ocr_result = result.get("ocr")
            job.video_analysis_result = result.get("video_analysis")
            db.commit()

            # 各解析結果の詳細をログ出力
            transcription = result.get("transcription")
            ocr = result.get("ocr")
            video_analysis = result.get("video_analysis")

            logger.info(
                f"解析タスク完了: job_id={job_id}\n"
                f"  [音声解析] セグメント数={len(transcription.get('segments', [])) if transcription else 0}\n"
                f"  [OCR解析] テキスト数={len(ocr.get('texts', [])) if ocr else 0}\n"
                f"  [映像解析] フレーム数={len(video_analysis.get('frames', [])) if video_analysis else 0}\n"
                f"  [総合結果] overall_score={result.get('overall_score')}, risk_count={len(result.get('risks', []))}"
            )

            return {
                "job_id": job_id,
                "status": "completed",
                "overall_score": result.get("overall_score"),
                "risk_count": len(result.get("risks", [])),
            }

        except Exception as e:
            logger.error(
                f"解析タスク失敗: job_id={job_id}, error={e}, "
                f"retry={self.request.retries}/{self.max_retries}",
                exc_info=True
            )
            job.status = JobStatus.failed
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()

            if self.request.retries < self.max_retries:
                logger.info(f"解析タスクリトライ: job_id={job_id}")
                raise self.retry(exc=e)

            return {"job_id": job_id, "status": "failed", "error": str(e)}

    finally:
        db.close()
