import json
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import vertexai # Still needed for vertexai.init
from vertexai.generative_models import GenerativeModel # No longer directly used by RiskEvaluatorService but might be useful in future

from app.config import get_settings # Still needed for settings.google_cloud_project
settings = get_settings()

from app.services.gemini_video_analysis import UnifiedVideoAnalysisResult


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
    risks: List[RiskItem]

    def evaluate(
        self,
        unified_analysis: UnifiedVideoAnalysisResult, # New signature
        metadata: dict, # metadata is still passed by OrchestratorService but not directly used here
    ) -> RiskAssessment:
        """
        Geminiによる統合分析結果に基づいてリスク評価をパースし、整形する。

        Args:
            unified_analysis: Geminiによる統合動画分析結果。
            metadata: メタ情報（現在未使用だが引数としては維持）。

        Returns:
            リスク評価結果
        """
        # Geminiが直接リスクを返しているので、それをパース
        overall_score = unified_analysis.gemini_overall_score if unified_analysis.gemini_overall_score is not None else 0.0
        risk_level_str = unified_analysis.gemini_risk_level if unified_analysis.gemini_risk_level else RiskLevel.none.value
        try:
            risk_level = RiskLevel(risk_level_str)
        except ValueError:
            risk_level = RiskLevel.none

        risks = []
        for risk_data in unified_analysis.risks:
            try:
                risk = RiskItem(
                    id=risk_data.get("id", str(uuid.uuid4())), # Use ID from Gemini or generate
                    timestamp=float(risk_data.get("timestamp", 0)),
                    end_timestamp=float(risk_data.get("end_timestamp", risk_data.get("timestamp", 0))),
                    category=RiskCategory(risk_data.get("category", "misleading")),
                    subcategory=risk_data.get("subcategory", ""),
                    score=float(risk_data.get("score", 0)),
                    level=RiskLevel(risk_data.get("level", "low")),
                    rationale=risk_data.get("rationale", ""),
                    source=RiskSource(risk_data.get("source", "video")), # Source is now always 'video' from Gemini
                    evidence=risk_data.get("evidence", ""),
                )
                risks.append(risk)
            except (ValueError, KeyError) as e:
                # Log error or handle malformed risk item from Gemini
                print(f"Error parsing risk item from Gemini: {e} - Data: {risk_data}")
                continue

        return RiskAssessment(
            overall_score=overall_score,
            risk_level=risk_level,
            risks=risks,
        )

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
