from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    with patch("app.api.routes.editor.SessionLocal") as mock:
        mock_session = MagicMock()
        mock.return_value = mock_session
        yield mock_session


def test_get_video_url_not_found(client, mock_db_session):
    mock_db_session.query.return_value.join.return_value.filter.return_value.first.return_value = None

    response = client.get(f"/api/jobs/{uuid4()}/video-url")

    assert response.status_code == 404


def test_get_video_url_success(client, mock_db_session):
    job = MagicMock()
    video = MagicMock()
    video.file_path = "videos/test.mp4"
    job.video = video

    mock_db_session.query.return_value.join.return_value.filter.return_value.first.return_value = job

    with patch("app.api.routes.editor.StorageService") as storage_mock:
        storage_instance = storage_mock.return_value
        storage_instance.generate_presigned_url.return_value = "http://example.com/video"

        response = client.get(f"/api/jobs/{uuid4()}/video-url")

    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "http://example.com/video"
    assert "expires_at" in data


def test_get_edit_session_not_found(client, mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    response = client.get(f"/api/jobs/{uuid4()}/edit-session")

    assert response.status_code == 404


def test_get_edit_session_success(client, mock_db_session):
    job = MagicMock()
    job.id = uuid4()
    mock_db_session.query.return_value.filter.return_value.first.return_value = job

    session = MagicMock()
    session.id = uuid4()
    session.job_id = job.id
    session.status = "draft"
    session.actions = []
    session.created_at = datetime.utcnow()
    session.updated_at = datetime.utcnow()

    with patch("app.api.routes.editor.EditSessionService") as service_mock:
        service_instance = service_mock.return_value
        service_instance.get_or_create_session.return_value = session

        response = client.get(f"/api/jobs/{job.id}/edit-session")

    assert response.status_code == 200
    assert response.json()["job_id"] == str(job.id)


def test_update_edit_session_success(client, mock_db_session):
    job = MagicMock()
    job.id = uuid4()
    mock_db_session.query.return_value.filter.return_value.first.return_value = job

    session = MagicMock()
    session.id = uuid4()
    session.job_id = job.id
    session.status = "draft"
    session.actions = []
    session.created_at = datetime.utcnow()
    session.updated_at = datetime.utcnow()

    with patch("app.api.routes.editor.EditSessionService") as service_mock:
        service_instance = service_mock.return_value
        service_instance.update_session.return_value = session

        response = client.put(
            f"/api/jobs/{job.id}/edit-session",
            json={"actions": []},
        )

    assert response.status_code == 200
    assert response.json()["job_id"] == str(job.id)
