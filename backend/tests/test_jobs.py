import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.models.job import JobStatus, Platform


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    with patch("app.api.routes.jobs.SessionLocal") as mock:
        mock_session = MagicMock()
        mock.return_value = mock_session
        yield mock_session


@pytest.fixture
def sample_job():
    job = MagicMock()
    job.id = uuid4()
    job.status = JobStatus.completed
    job.purpose = "テスト用途"
    job.platform = Platform.twitter
    job.target_audience = "テスト対象"
    job.created_at = datetime.utcnow()
    job.completed_at = datetime.utcnow()
    job.error_message = None
    job.overall_score = 25.0
    job.risk_level = None

    video = MagicMock()
    video.original_name = "test.mp4"
    job.video = video

    return job


def test_list_jobs_empty(client, mock_db_session):
    """ジョブがない場合は空リストを返すこと"""
    mock_db_session.query.return_value.join.return_value.order_by.return_value.all.return_value = []

    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert response.json() == []


def test_get_job_not_found(client, mock_db_session):
    """存在しないジョブIDは404を返すこと"""
    mock_db_session.query.return_value.join.return_value.filter.return_value.first.return_value = None

    response = client.get(f"/api/jobs/{uuid4()}")
    assert response.status_code == 404


def test_get_progress_not_found(client, mock_db_session):
    """存在しないジョブの進捗は404を返すこと"""
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    response = client.get(f"/api/jobs/{uuid4()}/progress")
    assert response.status_code == 404


def test_get_results_not_completed(client, mock_db_session, sample_job):
    """未完了ジョブの結果取得は400を返すこと"""
    sample_job.status = JobStatus.processing
    mock_db_session.query.return_value.join.return_value.filter.return_value.first.return_value = sample_job

    response = client.get(f"/api/jobs/{sample_job.id}/results")
    assert response.status_code == 400
