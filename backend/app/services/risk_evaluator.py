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
    public_nuisance = "public_nuisance"


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
{json.dumps(video_analysis, ensure_ascii=False, indent=2) if video_analysis else '映像解析なし'}

## 評価観点

以下の4つの観点で炎上リスクを評価してください：

### 1. 攻撃性 (aggressiveness)
- 匿名性を利用した攻撃的表現
- 拡散されやすい過激な表現
- 感情的反応を煽る表現
- 集団心理を刺激する表現
- 個人攻撃につながる表現

### 2. 差別性 (discrimination)
- 人種・民族に関する偏見
- 性別・ジェンダーに関する偏見
- 性的指向に関する偏見
- 年齢・世代に関する偏見
- 身体的特徴に関する偏見
- 社会的立場に関する偏見

### 3. 誤解を招く表現 (misleading)
- 断定的すぎる表現
- 曖昧で誤解を招く表現
- 感情的・煽情的な表現
- 誇張表現
- ステレオタイプに基づく表現
- 文脈なしで切り取られやすい表現

### 4. 迷惑行為・不衛生行為 (public_nuisance)
- 店舗、施設、公共の場所での不適切な行為や器物損壊
- 食品、商品、備品への異物混入や汚損行為
- 業務妨害、他者の迷惑となる行為
- 模倣犯を誘発する可能性のある行為
- 企業やブランドの信用を著しく損なう行為

特定の行為（例：商品をなめる、唾液を付着させる、備品を汚損する、落書きする）は、その行為が飲食店や公共の場で行われた場合、たとえ一見軽微に見えても、社会的な炎上リスクが非常に高く、企業ブランドに甚大な被害を与える可能性があるため、**総合スコアおよびリスクレベルを高く評価してください。**

## 出力形式

以下のJSON形式で回答してください：

{{
  "overall_score": 0-100の数値（炎上リスクの総合スコア）,
  "risk_level": "none" | "low" | "medium" | "high",
  "risks": [
    {{
      "timestamp": 開始タイムコード（秒）,
      "end_timestamp": 終了タイムコード（秒）,
      "category": "aggressiveness" | "discrimination" | "misleading" | "public_nuisance",
      "subcategory": "具体的なリスク種別",
      "score": 0-100の数値,
      "level": "low" | "medium" | "high",
      "rationale": "リスクと判断した具体的な根拠",
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
