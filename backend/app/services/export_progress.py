"""Export progress tracking service using Redis."""
import json
from typing import Optional

import redis

from app.config import get_settings

settings = get_settings()


class ExportProgressService:
    """Manage export progress status in Redis."""

    def __init__(self) -> None:
        self.redis_client = redis.from_url(settings.redis_url)
        self.progress_key_prefix = "export_progress:"

    def _get_progress_key(self, export_id: str) -> str:
        return f"{self.progress_key_prefix}{export_id}"

    def set_progress(
        self,
        export_id: str,
        status: str,
        progress: float,
        error_message: Optional[str] = None,
    ) -> None:
        data = {
            "export_id": export_id,
            "status": status,
            "progress": max(0.0, min(progress, 100.0)),
            "error_message": error_message,
        }
        self.redis_client.set(self._get_progress_key(export_id), json.dumps(data), ex=86400)

    def get_progress(self, export_id: str) -> Optional[dict]:
        data = self.redis_client.get(self._get_progress_key(export_id))
        if data:
            return json.loads(data)
        return None

    def delete_progress(self, export_id: str) -> None:
        self.redis_client.delete(self._get_progress_key(export_id))
