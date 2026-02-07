import concurrent.futures
import logging 
import traceback                                                                                                                                                                                                    │
from typing import Optional

from app.services.progress import ProgressService, PhaseStatus, JobStatus
from app.services.audio_analyzer import AudioAnalyzerService
from app.services.ocr_analyzer import OCRAnalyzerService
from app.services.video_analyzer import VideoAnalyzerService
from app.services.risk_evaluator import RiskEvaluatorService
from app.models.database import SessionLocal
from app.models.job import AnalysisJob, RiskItem as DBRiskItem, RiskCategory, RiskLevel, RiskSource

logger = logging.getLogger(__name__)


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

        logger.info(f"[{job_id}] リスク評価開始")
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

            # リスク評価結果の詳細ログ
            logger.info(
                f"[{job_id}] リスク評価完了: "
                f"overall_score={risk_result.get('overall_score', 0)}, "
                f"risk_level={risk_result.get('risk_level', 'none')}, "
                f"リスク項目数={len(risk_result.get('risks', []))}"
            )
            if risk_result.get("risks"):
                for i, risk in enumerate(risk_result["risks"][:5]):  # 最初の5つのリスク
                    logger.info(
                        f"[{job_id}] リスク[{i}]: "
                        f"category={risk.get('category')}, "
                        f"score={risk.get('score')}, "
                        f"level={risk.get('level')}, "
                        f"source={risk.get('source')}"
                    )

            self._save_risk_items(job_id, risk_assessment)

            self.progress_service.update_progress(
                job_id, "risk", PhaseStatus.completed, 100
            )

        except Exception as e:
            logger.error(f"[{job_id}] リスク評価失敗: error={e}", exc_info=True)
            errors["risk"] = str(e)
            self.progress_service.update_progress(
                job_id, "risk", PhaseStatus.failed, 0
            )
            risk_result = {"overall_score": 0, "risk_level": "none", "risks": []}

        # Check current status before marking as complete
        current_progress = self.progress_service.get_progress(job_id)
        if current_progress and current_progress.get("status") != JobStatus.failed.value:
            self.progress_service.set_job_completed(job_id)

        # 解析結果サマリーログ
        logger.info(
            f"[{job_id}] ========== 解析結果サマリー ==========\n"
            f"  音声解析: {'成功' if transcription_result else '失敗/データなし'}\n"
            f"  OCR解析: {'成功' if ocr_result else '失敗/データなし'}\n"
            f"  映像解析: {'成功' if video_analysis_result else '失敗/データなし'}\n"
            f"  総合スコア: {risk_result.get('overall_score', 0)}\n"
            f"  リスクレベル: {risk_result.get('risk_level', 'none')}\n"
            f"  リスク項目数: {len(risk_result.get('risks', []))}\n"
            f"  エラー: {errors if errors else 'なし'}\n"
            f"=========================================="
        )

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
        logger.info(f"[{job_id}] 音声解析開始: video_path={video_path}")
        self.progress_service.update_progress(
            job_id, "audio", PhaseStatus.processing, 0
        )

        try:
            result = self.audio_analyzer.analyze(video_path)
            result_dict = self.audio_analyzer.result_to_dict(result)

            # 音声解析結果の詳細ログ
            segment_count = len(result_dict.get("segments", [])) if result_dict else 0
            total_text_length = sum(len(s.get("text", "")) for s in result_dict.get("segments", [])) if result_dict else 0
            avg_confidence = 0
            if result_dict and result_dict.get("segments"):
                confidences = [s.get("confidence", 0) for s in result_dict["segments"] if s.get("confidence")]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            logger.info(
                f"[{job_id}] 音声解析完了: "
                f"セグメント数={segment_count}, "
                f"総文字数={total_text_length}, "
                f"平均信頼度={avg_confidence:.2f}"
            )
            if result_dict and result_dict.get("segments"):
                for i, seg in enumerate(result_dict["segments"][:3]):  # 最初の3セグメントのみ
                    logger.info(f"[{job_id}] 音声セグメント[{i}]: text=\"{seg.get('text', '')[:50]}...\", confidence={seg.get('confidence', 0):.2f}")

            self.progress_service.update_progress(
                job_id, "audio", PhaseStatus.completed, 100
            )

            return result_dict

        except Exception as e:
            logger.error(f"[{job_id}] 音声解析失敗: error={e}", exc_info=True)
            self.progress_service.update_progress(
                job_id, "audio", PhaseStatus.failed, 0
            )
            raise

    def _run_ocr_analysis(self, job_id: str, video_path: str) -> Optional[dict]:
        """OCR解析を実行"""
        logger.info(f"[{job_id}] OCR解析開始: video_path={video_path}")
        self.progress_service.update_progress(
            job_id, "ocr", PhaseStatus.processing, 0
        )

        try:
            result = self.ocr_analyzer.analyze(video_path)
            result_dict = self.ocr_analyzer.result_to_dict(result)

            # OCR解析結果の詳細ログ
            text_count = len(result_dict.get("texts", [])) if result_dict else 0
            unique_texts = set()
            if result_dict and result_dict.get("texts"):
                for t in result_dict["texts"]:
                    unique_texts.add(t.get("text", ""))
            avg_confidence = 0
            if result_dict and result_dict.get("texts"):
                confidences = [t.get("confidence", 0) for t in result_dict["texts"] if t.get("confidence")]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            logger.info(
                f"[{job_id}] OCR解析完了: "
                f"検出テキスト数={text_count}, "
                f"ユニークテキスト数={len(unique_texts)}, "
                f"平均信頼度={avg_confidence:.2f}"
            )
            if unique_texts:
                sample_texts = list(unique_texts)[:5]  # 最初の5つのユニークテキスト
                for i, text in enumerate(sample_texts):
                    logger.info(f"[{job_id}] OCRテキスト[{i}]: \"{text[:100]}\"")

            self.progress_service.update_progress(
                job_id, "ocr", PhaseStatus.completed, 100
            )

            return result_dict

        except Exception as e:
            logger.error(f"[{job_id}] OCR解析失敗: error={e}", exc_info=True)
            self.progress_service.update_progress(
                job_id, "ocr", PhaseStatus.failed, 0
            )
            raise

    def _run_video_analysis(self, job_id: str, video_path: str) -> Optional[dict]:
        """映像解析を実行"""
        logger.info(f"[{job_id}] 映像解析開始: video_path={video_path}")
        self.progress_service.update_progress(
            job_id, "video", PhaseStatus.processing, 0
        )

        try:
            result = self.video_analyzer.analyze(video_path)
            result_dict = self.video_analyzer.result_to_dict(result)

            # 映像解析結果の詳細ログ
            frame_count = len(result_dict.get("frames", [])) if result_dict else 0
            total_persons = 0
            total_objects = 0
            scenes = set()
            if result_dict and result_dict.get("frames"):
                for frame in result_dict["frames"]:
                    total_persons += len(frame.get("persons", []))
                    total_objects += len(frame.get("objects", []))
                    if frame.get("scene"):
                        scenes.add(frame["scene"].get("classification", ""))

            logger.info(
                f"[{job_id}] 映像解析完了: "
                f"フレーム数={frame_count}, "
                f"検出人物数={total_persons}, "
                f"検出オブジェクト数={total_objects}, "
                f"シーン種類数={len(scenes)}"
            )
            if result_dict and result_dict.get("frames"):
                for i, frame in enumerate(result_dict["frames"][:3]):  # 最初の3フレームのみ
                    persons = len(frame.get("persons", []))
                    objects = len(frame.get("objects", []))
                    scene = frame.get("scene", {}).get("classification", "不明")
                    logger.info(
                        f"[{job_id}] フレーム[{i}] timestamp={frame.get('timestamp', 0):.1f}s: "
                        f"人物={persons}, オブジェクト={objects}, シーン={scene}"
                    )

            self.progress_service.update_progress(
                job_id, "video", PhaseStatus.completed, 100
            )

            return result_dict

        except Exception as e:
            logger.error(f"[{job_id}] 映像解析失敗: error={e}", exc_info=True)
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
