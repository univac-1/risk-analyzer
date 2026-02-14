from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "video_risk_analyzer",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.analyze", "app.tasks.export"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tokyo",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="default",
    task_routes={
        "app.tasks.analyze.*": {"queue": "analysis"},
        "app.tasks.export.*": {"queue": "export"},
    },
    task_annotations={
        "app.tasks.analyze.analyze_video": {
            "max_retries": 3,
            "default_retry_delay": 60,
        },
    },
)
