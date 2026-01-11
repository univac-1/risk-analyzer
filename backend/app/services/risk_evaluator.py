import json
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, List

import vertexai
from vertexai.generative_models import GenerativeModel

from app.config import get_settings

settings = get_settings()


class RiskCategory(str, Enum):
    aggressiveness = "aggressiveness"
    discrimination = "discrimination"
    misleading = "misleading"
    explicit_content = "explicit_content"
    safety = "safety"


class RiskLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"


class RiskSource(str, Enum):
    audio = "audio"
    ocr = "ocr"
    video = "video"


@dataclass
class RiskItem:
    id: str
    timestamp: float
    end_timestamp: float
    category: RiskCategory
    subcategory: str
    score: float
    level: RiskLevel
    rationale: str
    source: RiskSource
    evidence: str


@dataclass
class RiskAssessment:
    overall_score: float
    risk_level: RiskLevel
    risks: list[RiskItem]


class RiskEvaluatorService:
    SENSITIVE_OBJECTS = {"weapon": 80, "knife": 80}

    def __init__(self):
        if settings.google_cloud_project:
            vertexai.init(project=settings.google_cloud_project, location="us-central1")
        self.model = GenerativeModel("gemini-2.0-flash-001")

    def evaluate(
        self,
        transcription: Optional[dict],
        ocr: Optional[dict],
        video_analysis: Optional[dict],
        metadata: dict,
    ) -> RiskAssessment:
        """
        解析結果を統合してリスク評価を行う
        """
        direct_video_risks = self._evaluate_video_risks_directly(video_analysis)

        video_summary = self._summarize_video_analysis(video_analysis)

        prompt = self._build_prompt(transcription, ocr, video_summary, metadata)
        response = self.model.generate_content(prompt)

        llm_assessment = self._parse_llm_response(response.text)
        
        # Combine direct risks and LLM-based risks
        combined_risks = direct_video_risks + llm_assessment.risks
        
        # Recalculate overall score and level
        if not combined_risks:
            overall_score = 0.0
            risk_level = RiskLevel.none
        else:
            overall_score = max(risk.score for risk in combined_risks)
            max_level = max(risk.level for risk in combined_risks)
            risk_level = RiskLevel(max_level)

        return RiskAssessment(
            overall_score=overall_score,
            risk_level=risk_level,
            risks=combined_risks,
        )

    def _evaluate_video_risks_directly(self, video_analysis: Optional[dict]) -> List[RiskItem]:
        """
        映像解析結果から明確なリスクを直接評価する
        """
        risks = []
        if not video_analysis:
            return risks

        # 1. Explicit Content Detection
        for annotation in video_analysis.get("explicit_content_annotations", []):
            likelihood = annotation.get("likelihood", "UNKNOWN")
            if likelihood in ["LIKELY", "VERY_LIKELY"]:
                ts = annotation.get("time_offset", 0)
                risks.append(RiskItem(
                    id=str(uuid.uuid4()),
                    timestamp=ts,
                    end_timestamp=ts,
                    category=RiskCategory.explicit_content,
                    subcategory="Pornography",
                    score=95.0 if likelihood == "VERY_LIKELY" else 80.0,
                    level=RiskLevel.high if likelihood == "VERY_LIKELY" else RiskLevel.medium,
                    rationale=f"不適切なコンテンツの可能性が「{likelihood}」と判定されました。",
                    source=RiskSource.video,
                    evidence="該当シーンの映像"
                ))

        # 2. Sensitive Object Detection
        for obj in video_analysis.get("tracked_objects", []):
            label = obj.get("label", "").lower()
            if label in self.SENSITIVE_OBJECTS:
                confidence = obj.get("confidence", 0) * 100
                if confidence >= self.SENSITIVE_OBJECTS[label]:
                    segment = obj.get("segments", [[0, 0]])[0]
                    risks.append(RiskItem(
                        id=str(uuid.uuid4()),
                        timestamp=segment[0],
                        end_timestamp=segment[1],
                        category=RiskCategory.safety,
                        subcategory="Weapon Detection",
                        score=confidence,
                        level=RiskLevel.high if confidence > 90 else RiskLevel.medium,
                        rationale=f"安全性を損なう可能性のある物体「{label}」が検出されました (確信度: {confidence:.1f}%)。",
                        source=RiskSource.video,
                        evidence=f"検出された物体: {label}"
                    ))
        
        return risks

    def _summarize_video_analysis(self, video_analysis: Optional[dict]) -> dict:
        """映像解析結果をLLM向けのサマリーに変換する"""
        if not video_analysis:
            return {"summary": "映像解析なし"}

        summary_lines = []
        
        explicit_notes = []
        for ann in video_analysis.get("explicit_content_annotations", []):
            if ann.get("likelihood") in ["LIKELY", "VERY_LIKELY"]:
                explicit_notes.append(f"{ann['time_offset']:.1f}s (Likeliness: {ann['likelihood']})")
        if explicit_notes:
            summary_lines.append(f"不適切なコンテンツの可能性が高い箇所が検出されました: {', '.join(explicit_notes)}")

        detected_objects = [obj['label'] for obj in video_analysis.get("tracked_objects", [])]
        if detected_objects:
            unique_objects = sorted(list(set(detected_objects)))
            summary_lines.append(f"主な検出オブジェクト: {', '.join(unique_objects)}")
        
        return {"summary": ". ".join(summary_lines) if summary_lines else "リスクにつながる要素は検出されませんでした。"}


    def _parse_llm_response(self, response_text: str) -> RiskAssessment:
        """LLMからのレスポンスJSONをパースする"""
        try:
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            data = json.loads(response_text)
        except (json.JSONDecodeError, AttributeError):
            return RiskAssessment(overall_score=0.0, risk_level=RiskLevel.none, risks=[])

        risks = []
        for risk_data in data.get("risks", []):
            try:
                risk = RiskItem(
                    id=str(uuid.uuid4()),
                    timestamp=float(risk_data.get("timestamp", 0)),
                    end_timestamp=float(risk_data.get("end_timestamp", risk_data.get("timestamp", 0))),
                    category=RiskCategory(risk_data.get("category")),
                    subcategory=risk_data.get("subcategory", ""),
                    score=float(risk_data.get("score", 0)),
                    level=RiskLevel(risk_data.get("level", "low")),
                    rationale=risk_data.get("rationale", ""),
                    source=RiskSource(risk_data.get("source")),
                    evidence=risk_data.get("evidence", ""),
                )
                risks.append(risk)
            except (ValueError, KeyError):
                continue
        
        return RiskAssessment(
            overall_score=float(data.get("overall_score", 0)),
            risk_level=RiskLevel(data.get("risk_level", "none")),
            risks=risks,
        )

    def _build_prompt(
        self,
        transcription: Optional[dict],
        ocr: Optional[dict],
        video_summary: Optional[dict],
        metadata: dict,
    ) -> str:
        """評価プロンプトを構築"""
        prompt = f"""あなたはSNS投稿前の動画コンテンツに対する炎上リスクを評価する専門家です。
以下の情報を元に、音声・テキストの文脈や、映像の全体的な雰囲気から判断される、より繊細なリスクを評価してください。
（映像内の不適切コンテンツや危険物など、明確なリスクは既に別システムで検出済みです）

## 投稿情報
- 用途: {metadata.get('purpose', '不明')}
- 投稿先媒体: {metadata.get('platform', '不明')}
- 想定ターゲット: {metadata.get('target_audience', '不明')}

## 解析データ

### 音声文字起こし結果
{json.dumps(transcription, ensure_ascii=False, indent=2) if transcription else '音声なし'}

### 画面内テキスト（OCR）
{json.dumps(ocr, ensure_ascii=False, indent=2) if ocr else 'テキストなし'}

### 映像内容サマリー
{json.dumps(video_summary, ensure_ascii=False, indent=2) if video_summary else '映像解析なし'}

## 評価観点

以下の観点で、文脈から読み取れる複合的なリスクを評価してください：

### 1. 攻撃性 (aggressiveness)
- 匿名性を利用した攻撃的表現
- 拡散されやすい過激な表現
- 感情的反応を煽る表現
- 集団心理を刺激する表現
- 個人攻撃につながる表現

### 2. 差別性 (discrimination)
- 人種・民族、性別・ジェンダー、性的指向、年齢、身体的特徴、社会的立場などに関する偏見やステレオタイプを助長する表現

### 3. 誤解を招く表現 (misleading)
- 断定的すぎる、曖昧、感情的、誇張された表現
- 文脈を切り取られて誤用される可能性のある表現

## 出力形式

以下のJSON形式で回答してください。明確なリスクは検出済みのため、ここでは文脈上問題があると判断されるもののみを挙げてください。

{{
  "overall_score": 0-100の数値（総合的な文脈リスクのスコア）,
  "risk_level": "none" | "low" | "medium" | "high",
  "risks": [
    {{
      "timestamp": 開始タイムコード（秒）,
      "end_timestamp": 終了タイムコード（秒）,
      "category": "aggressiveness" | "discrimination" | "misleading",
      "subcategory": "具体的なリスク種別",
      "score": 0-100の数値,
      "level": "low" | "medium" | "high",
      "rationale": "リスクと判断した具体的な根拠（文脈を重視）",
      "source": "audio" | "ocr" | "video",
      "evidence": "問題となる具体的な発言・テキスト・映像の内容"
    }}
  ]
}}

リスクが検出されない場合は、risksを空配列、overall_scoreを0、risk_levelを"none"としてください。
JSONのみを出力し、説明は不要です。"""

        return prompt

    def result_to_dict(self, result: RiskAssessment) -> dict:
        """結果を辞書形式に変換"""
        return asdict(result)