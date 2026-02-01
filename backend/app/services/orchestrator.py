import concurrent.futures
from typing import Optional
import traceback

from app.services.progress import ProgressService, PhaseStatus, JobStatus
from app.services.audio_analyzer import AudioAnalyzerService
from app.services.ocr_analyzer import OCRAnalyzerService
from app.services.video_analyzer import VideoAnalyzerService
from app.services.risk_evaluator import RiskEvaluatorService
from app.models.database import SessionLocal
from app.models.job import AnalysisJob, RiskItem as DBRiskItem, RiskCategory, RiskLevel, RiskSource


class OrchestratorService:
    def __init__(self, progress_service: ProgressService):
        self.progress_service = progress_service
        self.audio_analyzer = AudioAnalyzerService()
        self.ocr_analyzer = OCRAnalyzerService()
        self.video_analyzer = VideoAnalyzerService()
        self.risk_evaluator = RiskEvaluatorService()

    def run_analysis(self, job_id: str, video_path: str, metadata: dict) -> dict:
        """
        解析パイプラインを実行

        Args:
            job_id: ジョブID
            video_path: 動画ファイルパス
            metadata: メタ情報

        Returns:
            解析結果
        """
        transcription_result = None
        ocr_result = None
        video_analysis_result = None

        errors = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            audio_future = executor.submit(
                self._run_audio_analysis, job_id, video_path
            )
            ocr_future = executor.submit(
                self._run_ocr_analysis, job_id, video_path
            )
            video_future = executor.submit(
                self._run_video_analysis, job_id, video_path
            )

            try:
                transcription_result = audio_future.result()
            except Exception as e:
                errors["audio"] = str(e)
                self.progress_service.update_progress(
                    job_id, "audio", PhaseStatus.failed, 0
                )

            try:
                ocr_result = ocr_future.result()
            except Exception as e:
                errors["ocr"] = str(e)
                self.progress_service.update_progress(
                    job_id, "ocr", PhaseStatus.failed, 0
                )

            try:
                video_analysis_result = video_future.result()
            except Exception as e:
                errors["video"] = str(e)
                self.progress_service.update_progress(
                    job_id, "video", PhaseStatus.failed, 0
                )

        self.progress_service.update_progress(
            job_id, "risk", PhaseStatus.processing, 0
        )

        try:
            risk_assessment = self.risk_evaluator.evaluate(
                transcription_result,
                ocr_result,
                video_analysis_result,
                metadata,
            )
            risk_result = self.risk_evaluator.result_to_dict(risk_assessment)

            self._save_risk_items(job_id, risk_assessment)

            self.progress_service.update_progress(
                job_id, "risk", PhaseStatus.completed, 100
            )

        except Exception as e:
            errors["risk"] = str(e)
            self.progress_service.update_progress(
                job_id, "risk", PhaseStatus.failed, 0
            )
            risk_result = {"overall_score": 0, "risk_level": "none", "risks": []}

        # Check current status before marking as complete
        current_progress = self.progress_service.get_progress(job_id)
        if current_progress and current_progress.get("status") != JobStatus.failed.value:
            self.progress_service.set_job_completed(job_id)

        return {
            "transcription": transcription_result,
            "ocr": ocr_result,
            "video_analysis": video_analysis_result,
            "overall_score": risk_result.get("overall_score", 0),
            "risk_level": risk_result.get("risk_level", "none"),
            "risks": risk_result.get("risks", []),
            "errors": errors if errors else None,
        }

    def _run_audio_analysis(self, job_id: str, video_path: str) -> Optional[dict]:
        """音声解析を実行"""
        self.progress_service.update_progress(
            job_id, "audio", PhaseStatus.processing, 0
        )

        try:
            result = self.audio_analyzer.analyze(video_path)
            result_dict = self.audio_analyzer.result_to_dict(result)

            self.progress_service.update_progress(
                job_id, "audio", PhaseStatus.completed, 100
            )

            return result_dict

        except Exception as e:
            self.progress_service.update_progress(
                job_id, "audio", PhaseStatus.failed, 0
            )
            raise

    def _run_ocr_analysis(self, job_id: str, video_path: str) -> Optional[dict]:
        """OCR解析を実行"""
        self.progress_service.update_progress(
            job_id, "ocr", PhaseStatus.processing, 0
        )

        try:
            result = self.ocr_analyzer.analyze(video_path)
            result_dict = self.ocr_analyzer.result_to_dict(result)

            self.progress_service.update_progress(
                job_id, "ocr", PhaseStatus.completed, 100
            )

            return result_dict

        except Exception as e:
            self.progress_service.update_progress(
                job_id, "ocr", PhaseStatus.failed, 0
            )
            raise

    def _run_video_analysis(self, job_id: str, video_path: str) -> Optional[dict]:
        """映像解析を実行"""
        self.progress_service.update_progress(
            job_id, "video", PhaseStatus.processing, 0
        )

        try:
            result = self.video_analyzer.analyze(video_path)
            result_dict = self.video_analyzer.result_to_dict(result)

            self.progress_service.update_progress(
                job_id, "video", PhaseStatus.completed, 100
            )

            return result_dict

        except Exception as e:
            self.progress_service.update_progress(
                job_id, "video", PhaseStatus.failed, 0
            )
            raise

    def _save_risk_items(self, job_id: str, risk_assessment) -> None:
        """リスク項目をDBに保存"""
        db = SessionLocal()
        try:
            for risk in risk_assessment.risks:
                db_risk = DBRiskItem(
                    job_id=job_id,
                    timestamp=risk.timestamp,
                    end_timestamp=risk.end_timestamp,
                    category=RiskCategory(risk.category.value),
                    subcategory=risk.subcategory,
                    score=risk.score,
                    level=RiskLevel(risk.level.value),
                    rationale=risk.rationale,
                    source=RiskSource(risk.source.value),
                    evidence=risk.evidence,
                )
                db.add(db_risk)

            db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
