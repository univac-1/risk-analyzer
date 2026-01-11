import pytest
from unittest.mock import MagicMock, patch

from app.services.progress import ProgressService, PhaseStatus, JobStatus


@pytest.fixture
def mock_redis():
    with patch("app.services.progress.redis") as mock:
        mock_client = MagicMock()
        mock.from_url.return_value = mock_client
        yield mock_client


@pytest.fixture
def progress_service(mock_redis):
    return ProgressService()


def test_initialize_progress(progress_service, mock_redis):
    job_id = "test-job-123"
    progress_service.initialize_progress(job_id)

    mock_redis.set.assert_called()
    call_args = mock_redis.set.call_args_list[0]
    assert f"job_progress:{job_id}" in call_args[0][0]


def test_update_progress(progress_service, mock_redis):
    job_id = "test-job-123"
    mock_redis.get.return_value = '{"job_id": "test-job-123", "status": "pending", "overall": 0.0, "phases": {"audio": {"status": "pending", "progress": 0.0}, "ocr": {"status": "pending", "progress": 0.0}, "video": {"status": "pending", "progress": 0.0}, "risk": {"status": "pending", "progress": 0.0}}, "estimated_remaining_seconds": null}'

    progress_service.update_progress(
        job_id, "audio", PhaseStatus.processing, 50.0
    )

    mock_redis.set.assert_called()


def test_get_progress(progress_service, mock_redis):
    job_id = "test-job-123"
    mock_redis.get.return_value = '{"job_id": "test-job-123", "status": "processing", "overall": 25.0, "phases": {"audio": {"status": "completed", "progress": 100.0}, "ocr": {"status": "pending", "progress": 0.0}, "video": {"status": "pending", "progress": 0.0}, "risk": {"status": "pending", "progress": 0.0}}, "estimated_remaining_seconds": 300}'

    result = progress_service.get_progress(job_id)

    assert result is not None
    assert result["job_id"] == job_id
    assert result["overall"] == 25.0


def test_get_progress_not_found(progress_service, mock_redis):
    job_id = "nonexistent-job"
    mock_redis.get.return_value = None

    result = progress_service.get_progress(job_id)

    assert result is None


def test_set_job_completed(progress_service, mock_redis):
    job_id = "test-job-123"
    mock_redis.get.return_value = '{"job_id": "test-job-123", "status": "processing", "overall": 75.0, "phases": {"audio": {"status": "completed", "progress": 100.0}, "ocr": {"status": "completed", "progress": 100.0}, "video": {"status": "completed", "progress": 100.0}, "risk": {"status": "processing", "progress": 0.0}}, "estimated_remaining_seconds": 60}'

    progress_service.set_job_completed(job_id)

    mock_redis.set.assert_called()


def test_set_job_failed(progress_service, mock_redis):
    job_id = "test-job-123"
    mock_redis.get.return_value = '{"job_id": "test-job-123", "status": "processing", "overall": 50.0, "phases": {"audio": {"status": "completed", "progress": 100.0}, "ocr": {"status": "failed", "progress": 50.0}, "video": {"status": "pending", "progress": 0.0}, "risk": {"status": "pending", "progress": 0.0}}, "estimated_remaining_seconds": null}'

    progress_service.set_job_failed(job_id, "API error occurred")

    mock_redis.set.assert_called()
