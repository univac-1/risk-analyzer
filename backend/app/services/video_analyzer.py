import json
import tempfile
import os
import logging
from typing import Any, Dict

import vertexai
from vertexai.generative_models import GenerativeModel, Part

from app.config import get_settings
from app.services.storage import StorageService

settings = get_settings()
logger = logging.getLogger(__name__)


class VideoAnalyzerService:
    def __init__(self):
        self.storage_service = StorageService()
        if settings.google_cloud_project:
            vertexai.init(project=settings.google_cloud_project, location="us-central1")
        # Use Flash model for video
        self.model = GenerativeModel("gemini-2.5-pro")

    def analyze(self, video_path: str) -> Dict[str, Any]:
        """
        動画全体を解析 (Gemini 2.0 Native Video)

        Args:
            video_path: ストレージ内の動画ファイルパス

        Returns:
            映像解析結果 (Dict)
        """
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_file:
            video_local_path = video_file.name

        try:
            logger.info(f"Downloading video for analysis: {video_path}")
            self.storage_service.download_file(video_path, video_local_path)

            # Check file size roughly
            file_size = os.path.getsize(video_local_path)
            logger.info(f"Video size: {file_size / (1024*1024):.2f} MB")

            # Note: For larger files (>20MB), consider using GCS URI instead of inline data
            with open(video_local_path, "rb") as f:
                video_data = f.read()

            video_part = Part.from_data(
                data=video_data,
                mime_type="video/mp4"
            )

            prompt = """
            あなたは動画のコンテンツアナリストです。この動画を詳細に分析し、
            将来的な炎上リスク評価の根拠となる可能性のあるすべての客観的な情報を抽出してください。
            特に、以下の要素に注目し、時間軸に沿って詳細に記述してください。

            - **人物**: 表情、ジェスチャー、行動（例: 暴力行為、挑発的な動き、不快な表現）
            - **物体**: 不適切な物体、武器、シンボル、ブランドロゴなど
            - **シーン**: 環境、背景、雰囲気、場所、文脈（例: 公共の場でのプライバシー侵害、危険な場所での撮影）
            - **潜在的なリスク兆候**: 暴力、差別、誤解を招く可能性のある視覚的要素、不適切な内容

            タイムスタンプは厳密にfloat型（秒）で表現し、JSON形式で出力してください。

            {
                "summary": "動画全体の客観的な要約",
                "timeline": [
                    {
                        "timestamp_start": "開始時間 (float, 秒)",
                        "timestamp_end": "終了時間 (float, 秒)",
                        "description": "何が起きているかの客観的かつ詳細な描写。人物の行動、物体の存在、シーンの状況など。",
                        "potential_risk_indicators": [
                            {"type": "aggressiveness", "evidence": "具体的な攻撃的兆候（例：拳を振り上げている）"},
                            {"type": "discrimination", "evidence": "具体的な差別的兆候（例：特定のジェスチャー）"},
                            {"type": "misleading", "evidence": "具体的な誤解を招く兆候（例：誤情報を示すポスター）"},
                            {"type": "other_risk", "evidence": "その他の懸念事項（例：危険なスタント）"}
                        ],
                        "persons": [
                             {"description": "人物の描写", "expression": "表情", "action": "行動", "attire": "服装"}
                        ],
                        "detected_objects": [
                            {"label": "検出された物体", "confidence": "信頼度 (float)"}
                        ],
                        "scene_context": {
                            "location": "場所",
                            "atmosphere": "雰囲気",
                            "context_description": "シーンの客観的な説明"
                        }
                    }
                ],
                "overall_video_analysis": {
                     "tone": "動画全体のトーンや雰囲気",
                     "flags": ["潜在的な問題点1", "潜在的な問題点2"]
                }
            }
            """

            logger.info("Sending request to Gemini...")
            response = self.model.generate_content(
                [prompt, video_part],
                generation_config={"response_mime_type": "application/json"}
            )
            
            logger.info(f"Raw response from Gemini: {json.dumps(json.loads(response.text), indent=2, ensure_ascii=False)}")

            try:
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {response.text}")
                return {
                    "summary": "解析エラー: JSONパース失敗",
                    "timeline": [],
                    "error": str(e)
                }
            except Exception as e:
                logger.error(f"Error processing response: {e}")
                return {
                    "summary": "解析エラー: 処理失敗",
                    "timeline": [],
                    "error": str(e)
                }

        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            raise
        finally:
            if os.path.exists(video_local_path):
                os.unlink(video_local_path)

    def result_to_dict(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """結果を辞書形式に変換 (すでに辞書なのでそのまま返す)"""
        return result

