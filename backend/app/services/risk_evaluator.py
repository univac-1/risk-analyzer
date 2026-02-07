import json
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import vertexai
from vertexai.generative_models import GenerativeModel

from app.config import get_settings

settings = get_settings()


class RiskCategory(str, Enum):
    aggressiveness = "aggressiveness"
    discrimination = "discrimination"
    misleading = "misleading"


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
    def __init__(self):
        if settings.google_cloud_project:
            vertexai.init(project=settings.google_cloud_project, location="us-central1")
        self.model = GenerativeModel("gemini-2.5-pro")

    def evaluate(
        self,
        transcription: Optional[dict],
        ocr: Optional[dict],
        video_analysis: Optional[dict],
        metadata: dict,
    ) -> RiskAssessment:
        """
        解析結果を統合してリスク評価を行う

        Args:
            transcription: 音声文字起こし結果
            ocr: OCR結果
            video_analysis: 映像解析結果
            metadata: メタ情報（purpose, platform, target_audience）

        Returns:
            リスク評価結果
        """
        prompt = self._build_prompt(transcription, ocr, video_analysis, metadata)
        response = self.model.generate_content(prompt)

        try:
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            data = json.loads(response_text)
        except (json.JSONDecodeError, AttributeError):
            return RiskAssessment(
                overall_score=0.0,
                risk_level=RiskLevel.none,
                risks=[],
            )

        risks = []
        for risk_data in data.get("risks", []):
            try:
                risk = RiskItem(
                    id=str(uuid.uuid4()),
                    timestamp=float(risk_data.get("timestamp", 0)),
                    end_timestamp=float(risk_data.get("end_timestamp", risk_data.get("timestamp", 0))),
                    category=RiskCategory(risk_data.get("category", "misleading")),
                    subcategory=risk_data.get("subcategory", ""),
                    score=float(risk_data.get("score", 0)),
                    level=RiskLevel(risk_data.get("level", "low")),
                    rationale=risk_data.get("rationale", ""),
                    source=RiskSource(risk_data.get("source", "audio")),
                    evidence=risk_data.get("evidence", ""),
                )
                risks.append(risk)
            except (ValueError, KeyError):
                continue

        overall_score = float(data.get("overall_score", 0))
        try:
            risk_level = RiskLevel(data.get("risk_level", "none"))
        except ValueError:
            risk_level = RiskLevel.none

        return RiskAssessment(
            overall_score=overall_score,
            risk_level=risk_level,
            risks=risks,
        )

    def _build_prompt(
        self,
        transcription: Optional[dict],
        ocr: Optional[dict],
        video_analysis: Optional[dict],
        metadata: dict,
    ) -> str:
        """評価プロンプトを構築"""
        prompt = f"""あなたはSNS投稿前の動画コンテンツに対する炎上リスクを評価する専門家です。
        提供される解析データを基に、極めて客観的かつ厳密にリスクを評価し、詳細な根拠と共にJSON形式で出力してください。

## 投稿情報
- 用途: {metadata.get('purpose', '不明')}
- 投稿先媒体: {metadata.get('platform', '不明')}
- 想定ターゲット: {metadata.get('target_audience', '不明')}

## 解析データ

### 音声文字起こし結果
{json.dumps(transcription, ensure_ascii=False, indent=2) if transcription else '音声なし'}

### 画面内テキスト（OCR）
{json.dumps(ocr, ensure_ascii=False, indent=2) if ocr else 'テキストなし'}

### 映像内容解析
動画から抽出された詳細なタイムライン情報です。各タイムラインエントリには、人物の行動、検出された物体、シーンの文脈、および潜在的なリスク兆候が含まれます。
{json.dumps(video_analysis, ensure_ascii=False, indent=2) if video_analysis else '映像解析なし'}

## 評価観点と判断基準

以下の3つの観点で炎上リスクを評価してください。各リスクのスコアは0-100で、根拠を詳細に記述してください。
特に、**映像内容解析のタイムラインにある 'potential_risk_indicators'、'persons' の 'action'、'detected_objects'、'scene_context' の情報を最優先して参照**し、その客観的なエビデンスに基づいてリスクを判断してください。

### 1. 攻撃性 (aggressiveness)
- **定義**: 他者への身体的・精神的危害を示唆、扇動、美化する表現。特定の個人や集団への直接的な攻撃、脅迫、挑発、暴力的な行動、武器の使用、または攻撃的なジェスチャー。
- **判断基準**:
    - 人物が攻撃的な行動（殴る、蹴る、物を投げる）をしているか。
    - 武器や危険な物体（ナイフ、銃、爆発物など）が検出されているか。
    - 表情が極度に怒りや憎悪を示しているか。
    - シーンの文脈が暴力的、または対立を煽るものであるか。
    - `potential_risk_indicators` に `"type": "aggressiveness"` が含まれ、その `evidence` が具体的か。

### 2. 差別性 (discrimination)
- **定義**: 人種、民族、性別、性的指向、年齢、障害、国籍、宗教、社会的地位など、特定の属性を持つ個人や集団を不当に貶める、嘲笑する、または排除する表現。偏見やステレオタイプを助長する内容。
- **判断基準**:
    - 特定の集団に対する不適切な描写、ジェスチャー、シンボル、服装があるか。
    - 侮辱的、軽蔑的な表現（音声、OCR、映像内のシンボル）があるか。
    - 身体的特徴や属性に基づく嘲笑、排斥を促す行動があるか。
    - シーンの文脈が特定の集団に対する偏見を助長するものであるか。
    - `potential_risk_indicators` に `"type": "discrimination"` が含まれ、その `evidence` が具体的か。

### 3. 誤解を招く表現 (misleading)
- **定義**: 事実と異なる、または誤解を与える可能性のある情報、誇張された表現、文脈を無視した情報、視聴者を欺く意図がある、または欺く結果となる表現。
- **判断基準**:
    - 誤った情報を示すテキスト（OCR）、画像、または情報源が提示されているか。
    - 不正確な主張を裏付けるような視覚的な欺瞞（例: 編集された映像、誤解を招くグラフ）。
    - 誇大な表現やステレオタイプに基づく表現が映像や音声に含まれているか。
    - 危険な行為を安全であるかのように描写し、誤った認識を与える可能性があるか。
    - `potential_risk_indicators` に `"type": "misleading"` が含まれ、その `evidence` が具体的か。

## 出力形式

以下のJSON形式で回答してください：

{{
  "overall_score": 0-100の数値（炎上リスクの総合スコア）,
  "risk_level": "none" | "low" | "medium" | "high",
  "risks": [
    {{
      "timestamp": 開始タイムコード（float, 秒）,
      "end_timestamp": 終了タイムコード（float, 秒）,
      "category": "aggressiveness" | "discrimination" | "misleading",
      "subcategory": "具体的なリスク種別",
      "score": 0-100の数値,
      "level": "low" | "medium" | "high",
      "rationale": "リスクと判断した具体的な根拠（映像内容解析のどの情報から判断したか明記すること）",
      "source": "audio" | "ocr" | "video",
      "evidence": "問題となる具体的な発言・テキスト・映像の内容（video_analysisのdescription、potential_risk_indicators、persons、detected_objects、scene_contextから引用すること）"
    }}
  ]
}}

リスクが検出されない場合は、risksを空配列、overall_scoreを0、risk_levelを"none"としてください。
JSONのみを出力し、説明は不要です。
"""

        return prompt

    def result_to_dict(self, result: RiskAssessment) -> dict:
        """結果を辞書形式に変換"""
        return {
            "overall_score": result.overall_score,
            "risk_level": result.risk_level.value,
            "risks": [
                {
                    "id": risk.id,
                    "timestamp": risk.timestamp,
                    "end_timestamp": risk.end_timestamp,
                    "category": risk.category.value,
                    "subcategory": risk.subcategory,
                    "score": risk.score,
                    "level": risk.level.value,
                    "rationale": risk.rationale,
                    "source": risk.source.value,
                    "evidence": risk.evidence,
                }
                for risk in result.risks
            ],
        }
