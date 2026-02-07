from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from app.config import get_settings
from app.services.storage import StorageService
import uuid # For generating risk IDs

# ... existing UnifiedVideoAnalysisResult dataclass ...

@dataclass
class UnifiedVideoAnalysisResult:
    """
    Geminiによる統合的な動画分析結果を保持するデータクラス。
    Geminiが動画全体から直接抽出した情報を格納する。
    """
    gemini_risk_summary: Optional[str] = None
    gemini_overall_score: Optional[float] = None
    gemini_risk_level: Optional[str] = None # Assuming str for now, will map to Enum later

    detected_texts: List[Dict[str, Any]] = field(default_factory=list)
    detected_events: List[Dict[str, Any]] = field(default_factory=list)
    detected_objects: List[Dict[str, Any]] = field(default_factory=list)

    # Geminiが直接評価したリスク項目を格納
    risks: List[Dict[str, Any]] = field(default_factory=list) # Gemini will output risks directly

    other_analysis_data: Dict[str, Any] = field(default_factory=dict)
    raw_gemini_response: Optional[str] = None

class GeminiVideoAnalysisService:
    def __init__(self):
        self.settings = get_settings()
        if self.settings.google_cloud_project:
            vertexai.init(project=self.settings.google_cloud_project, location="us-central1")
        self.model = GenerativeModel("gemini-2.0-flash-001")
        self.storage_service = StorageService()

    def analyze_video(self, video_path: str) -> UnifiedVideoAnalysisResult:
        """
        Geminiモデルを使用して動画を直接分析し、統合された結果を返す。

        Args:
            video_path: 分析する動画のGCS URL。

        Returns:
            UnifiedVideoAnalysisResult: 統合された動画分析結果。
        """
        video_part = Part.from_uri(uri=video_path, mime_type="video/mp4")

        prompt_text = """この動画コンテンツを詳細に分析し、以下の情報を厳密にJSON形式で提供してください。
        分析結果には、動画内のテキスト、検出されたオブジェクト、主要なイベント、動画全体の要約、および炎上リスク評価を含めてください。
        リスク評価は「攻撃性(aggressiveness)」「差別性(discrimination)」「誤解を招く表現(misleading)」「迷惑行為・不衛生行為(public_nuisance)」の観点で行い、それぞれの根拠と共にスコアとレベルを記載してください。
        特に、食品への汚損、店舗備品への損壊、不適切な公共の場での行動など、迷惑行為・不衛生行為に該当する明確な証拠が見られる場合は、**総合スコアおよびリスクレベルを高く評価してください。**

        出力は以下のJSONスキーマに従ってください:
        {{
            "gemini_risk_summary": "動画全体の炎上リスクに関する総合的な評価と要約。",
            "gemini_overall_score": 0-100の数値（炎上リスクの総合スコア）,
            "gemini_risk_level": "none" | "low" | "medium" | "high",
            "detected_texts": [
                {{
                    "text": "検出されたテキスト",
                    "timestamp_seconds": "テキストが表示される動画内のタイムスタンプ（秒）",
                    "confidence": "テキスト検出の確信度（0-1）"
                }}
            ],
            "detected_events": [
                {{
                    "event_description": "検出されたイベントの概要",
                    "start_timestamp_seconds": "イベント開始タイムスタンプ（秒）",
                    "end_timestamp_seconds": "イベント終了タイムスタンプ（秒）"
                }}
            ],
            "detected_objects": [
                {{
                    "object_name": "検出されたオブジェクト名",
                    "timestamp_seconds": "オブジェクトが検出される動画内のタイムスタンプ（秒）",
                    "bounding_box": {{ "x_min":0.0, "y_min":0.0, "x_max":1.0, "y_max":1.0 }}
                }}
            ],
            "risks": [
                {{
                    "timestamp": 0.0,
                    "end_timestamp": 0.0,
                    "category": "aggressiveness" | "discrimination" | "misleading" | "public_nuisance",
                    "subcategory": "具体的なリスク種別",
                    "score": 0,
                    "level": "low" | "medium" | "high",
                    "rationale": "リスクと判断した具体的な根拠",
                    "source": "video",
                    "evidence": "問題となる具体的な映像の内容"
                }}
            ]
        }}
        JSONのみを出力し、説明は不要です。
        """

        contents = [prompt_text, video_part]
        response = self.model.generate_content(contents, request_options={"timeout": 600}) # Long timeout for video analysis

        response_text = response.text.strip()
        
        # クリーンアップ: 不要なマークダウンを除去
        if response_text.startswith("```json"):
            response_text = response_text[len("```json"):]
        if response_text.endswith("```"):
            response_text = response_text[:-len("```")]
        response_text = response_text.strip()

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            print(f"Raw Gemini response: {response_text}")
            return UnifiedVideoAnalysisResult(raw_gemini_response=response_text)

        # Assuming Gemini outputs risks in the expected format
        parsed_risks = []
        for risk_data in data.get("risks", []):
            # Generate a unique ID for each risk item, as Gemini won't provide one
            risk_data['id'] = str(uuid.uuid4())
            parsed_risks.append(risk_data)

        return UnifiedVideoAnalysisResult(
            gemini_risk_summary=data.get("gemini_risk_summary"),
            gemini_overall_score=data.get("gemini_overall_score"),
            gemini_risk_level=data.get("gemini_risk_level"),
            detected_texts=data.get("detected_texts", []),
            detected_events=data.get("detected_events", []),
            detected_objects=data.get("detected_objects", []),
            risks=parsed_risks,
            other_analysis_data={k: v for k, v in data.items() if k not in [
                "gemini_risk_summary", "gemini_overall_score", "gemini_risk_level",
                "detected_texts", "detected_events", "detected_objects", "risks"
            ]},
            raw_gemini_response=response_text
        )