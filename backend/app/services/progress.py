import json
import time
from enum import Enum
from typing import Optional

import redis

from app.config import get_settings

settings = get_settings()


class PhaseStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


PHASES = ["audio", "ocr", "video", "risk"]
PHASE_WEIGHTS = {
    "audio": 0.25,
    "ocr": 0.25,
    "video": 0.25,
    "risk": 0.25,
}


class ProgressService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url)
        self.progress_key_prefix = "job_progress:"
        self.start_time_key_prefix = "job_start_time:"

    def _get_progress_key(self, job_id: str) -> str:
        return f"{self.progress_key_prefix}{job_id}"

    def _get_start_time_key(self, job_id: str) -> str:
        return f"{self.start_time_key_prefix}{job_id}"

    def initialize_progress(self, job_id: str) -> None:
        """ジョブの進捗を初期化"""
        progress_data = {
            "job_id": job_id,
            "status": JobStatus.pending.value,
            "overall": 0.0,
            "phases": {
                phase: {"status": PhaseStatus.pending.value, "progress": 0.0}
                for phase in PHASES
            },
            "estimated_remaining_seconds": None,
        }
        self.redis_client.set(
            self._get_progress_key(job_id),
            json.dumps(progress_data),
            ex=86400,
        )
        self.redis_client.set(
            self._get_start_time_key(job_id),
            str(time.time()),
            ex=86400,
        )

    def update_progress(
        self,
        job_id: str,
        phase: str,
        status: PhaseStatus,
        progress: float,
    ) -> None:
        """フェーズの進捗を更新"""
        progress_data = self.get_progress(job_id)
        if not progress_data:
            self.initialize_progress(job_id)
            progress_data = self.get_progress(job_id)

        progress_data["phases"][phase] = {
            "status": status.value,
            "progress": min(progress, 100.0),
        }

        overall = sum(
            progress_data["phases"][p]["progress"] * PHASE_WEIGHTS[p]
            for p in PHASES
        )
        progress_data["overall"] = round(overall, 2)

        if overall > 0:
            start_time = self.redis_client.get(self._get_start_time_key(job_id))
            if start_time:
                elapsed = time.time() - float(start_time)
                if overall < 100:
                    estimated_total = elapsed / (overall / 100)
                    progress_data["estimated_remaining_seconds"] = round(
                        estimated_total - elapsed, 0
                    )
                else:
                    progress_data["estimated_remaining_seconds"] = 0

        all_completed = all(
            progress_data["phases"][p]["status"] == PhaseStatus.completed.value
            for p in PHASES
        )
        any_failed = any(
            progress_data["phases"][p]["status"] == PhaseStatus.failed.value
            for p in PHASES
        )

        if any_failed:
            progress_data["status"] = JobStatus.failed.value
        elif all_completed:
            progress_data["status"] = JobStatus.completed.value
        else:
            progress_data["status"] = JobStatus.processing.value

        self.redis_client.set(
            self._get_progress_key(job_id),
            json.dumps(progress_data),
            ex=86400,
        )

    def get_progress(self, job_id: str) -> Optional[dict]:
        """ジョブの進捗状況を取得"""
        data = self.redis_client.get(self._get_progress_key(job_id))
        if data:
            return json.loads(data)
        return None

    def set_job_completed(self, job_id: str) -> None:
        """ジョブを完了状態に設定"""
        progress_data = self.get_progress(job_id)
        if progress_data:
            progress_data["status"] = JobStatus.completed.value
            progress_data["overall"] = 100.0
            progress_data["estimated_remaining_seconds"] = 0
            for phase in PHASES:
                progress_data["phases"][phase]["status"] = PhaseStatus.completed.value
                progress_data["phases"][phase]["progress"] = 100.0
            self.redis_client.set(
                self._get_progress_key(job_id),
                json.dumps(progress_data),
                ex=86400,
            )

    def set_job_failed(self, job_id: str, error: str) -> None:
        """ジョブを失敗状態に設定"""
        progress_data = self.get_progress(job_id)
        if progress_data:
            progress_data["status"] = JobStatus.failed.value
            progress_data["error"] = error
            self.redis_client.set(
                self._get_progress_key(job_id),
                json.dumps(progress_data),
                ex=86400,
            )

    def delete_progress(self, job_id: str) -> None:
        """ジョブの進捗データを削除"""
        self.redis_client.delete(self._get_progress_key(job_id))
        self.redis_client.delete(self._get_start_time_key(job_id))
