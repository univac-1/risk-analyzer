import concurrent.futures
from typing import Optional
import traceback
import logging

from app.services.progress import ProgressService, PhaseStatus

logger = logging.getLogger(__name__)
from app.services.audio_analyzer import AudioAnalyzerService
from app.services.gemini_video_analysis import GeminiVideoAnalysisService, UnifiedVideoAnalysisResult
from app.services.risk_evaluator import RiskEvaluatorService
from app.models.database import SessionLocal
from app.models.job import AnalysisJob, RiskItem as DBRiskItem, RiskCategory, RiskLevel, RiskSource


class OrchestratorService:
    def __init__(self, progress_service: ProgressService):
        self.progress_service = progress_service
        self.audio_analyzer = AudioAnalyzerService()
        self.gemini_video_analyzer = GeminiVideoAnalysisService()
        self.risk_evaluator = RiskEvaluatorService()

    def run_analysis(self, job_id: str, video_path: str, metadata: dict) -> dict:
        transcription_result = None
        unified_analysis_result: Optional[UnifiedVideoAnalysisResult] = None
        final_risks = [] # To hold risks from either Gemini or RiskEvaluatorService

        errors = {}

        # 1. 音声解析を並行実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor: # Max_workers=1 as only audio now
            audio_future = executor.submit(self._run_audio_analysis, job_id, video_path)

            try:
                transcription_result = audio_future.result()
            except Exception as e:
                errors["audio"] = str(e)
                self.progress_service.update_progress(job_id, "audio", PhaseStatus.failed, 0)
                logger.error(f"[{job_id}] 音声解析失敗 (ThreadPool): error={e}", exc_info=True)

        # 2. Geminiによる統合動画解析
        logger.info(f"[{job_id}] Geminiによる統合動画解析開始: video_path={video_path}")
        self.progress_service.update_progress(job_id, "video", PhaseStatus.processing, 0)

        try:
            unified_analysis_result = self.gemini_video_analyzer.analyze_video(video_path)
            self.progress_service.update_progress(job_id, "video", PhaseStatus.completed, 100)
            logger.info(f"[{job_id}] Geminiによる統合動画解析完了")
        except Exception as e:
            errors["gemini_video"] = str(e)
            self.progress_service.update_progress(job_id, "video", PhaseStatus.failed, 0)
            logger.error(f"[{job_id}] Geminiによる統合動画解析失敗: error={e}", exc_info=True)
            unified_analysis_result = UnifiedVideoAnalysisResult(gemini_overall_score=0, gemini_risk_level=RiskLevel.none.value, risks=[])


        # 3. リスク評価 (Geminiからの直接リスクがあればそれを使用、なければ既存のRiskEvaluatorServiceを使用)
        if unified_analysis_result and unified_analysis_result.risks:
            logger.info(f"[{job_id}] Geminiからの直接リスク評価結果を使用")
            final_risks = unified_analysis_result.risks
            overall_score = unified_analysis_result.gemini_overall_score if unified_analysis_result.gemini_overall_score is not None else 0
            risk_level_str = unified_analysis_result.gemini_risk_level if unified_analysis_result.gemini_risk_level else RiskLevel.none.value
            try:
                risk_level = RiskLevel(risk_level_str)
            except ValueError:
                risk_level = RiskLevel.none

            risk_assessment = RiskAssessment(
                overall_score=overall_score,
                risk_level=risk_level,
                risks=final_risks
            )
            risk_result = self.risk_evaluator.result_to_dict(risk_assessment) # Use existing dict conversion
            self.progress_service.update_progress(job_id, "risk", PhaseStatus.completed, 100)
        else:
            logger.info(f"[{job_id}] 既存のリスク評価サービスを使用")
            self.progress_service.update_progress(job_id, "risk", PhaseStatus.processing, 0)
            try:
                # `RiskEvaluatorService`の`evaluate`メソッドの引数をUnifiedVideoAnalysisResultの構造に合わせて調整する
                # detected_texts -> ocr_result
                # detected_objects, detected_events -> video_analysis_result
                
                # For now, prepare args as expected by old evaluate method
                ocr_input_for_risk_evaluator = {"text_annotations": unified_analysis_result.detected_texts} if unified_analysis_result else None
                video_analysis_input_for_risk_evaluator = {
                    "frames": [], # Mocking frames structure for compatibility
                    "events": unified_analysis_result.detected_events,
                    "objects": unified_analysis_result.detected_objects
                } if unified_analysis_result else None


                risk_assessment = self.risk_evaluator.evaluate(
                    transcription_result,
                    ocr_input_for_risk_evaluator,
                    video_analysis_input_for_risk_evaluator,
                    metadata,
                )
                risk_result = self.risk_evaluator.result_to_dict(risk_assessment)
                self.progress_service.update_progress(job_id, "risk", PhaseStatus.completed, 100)

            except Exception as e:
                logger.error(f"[{job_id}] リスク評価失敗 (RiskEvaluatorService): error={e}", exc_info=True)
                errors["risk"] = str(e)
                self.progress_service.update_progress(job_id, "risk", PhaseStatus.failed, 0)
                risk_result = {"overall_score": 0, "risk_level": "none", "risks": []}
        
        final_overall_score = risk_result.get("overall_score", 0)
        final_risk_level = risk_result.get("risk_level", "none")
        final_risks = risk_result.get("risks", [])


        self.progress_service.set_job_completed(job_id)

        # 解析結果サマリーログ
        logger.info(
            f"[{job_id}] ========== 解析結果サマリー ==========\n"
            f"  音声解析: {'成功' if transcription_result else '失敗/データなし'}\n"
            f"  Gemini統合解析: {'成功' if unified_analysis_result else '失敗/データなし'}\n"
            f"  総合スコア: {final_overall_score}\n"
            f"  リスクレベル: {final_risk_level}\n"
            f"  リスク項目数: {len(final_risks)}\n"
            f"  エラー: {errors if errors else 'なし'}\n"
            f"=========================================="
        )

        return {
            "transcription": transcription_result,
            # ここではOCRとVideoAnalysisはunified_analysis_resultから直接取得される
            "ocr": {"text_annotations": unified_analysis_result.detected_texts} if unified_analysis_result else None,
            "video_analysis": {
                "frames": [], # We no longer have individual frames from VideoAnalyzerService
                "detected_events": unified_analysis_result.detected_events,
                "objects": unified_analysis_result.detected_objects
            } if unified_analysis_result else None,
            "overall_score": final_overall_score,
            "risk_level": final_risk_level,
            "risks": final_risks,
            "errors": errors if errors else None,
            "gemini_risk_summary": unified_analysis_result.gemini_risk_summary if unified_analysis_result else None,
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
