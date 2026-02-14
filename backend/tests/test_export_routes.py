from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.edit_session import ExportJobStatus


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    with patch("app.api.routes.editor.SessionLocal") as mock:
        mock_session = MagicMock()
        mock.return_value = mock_session
        yield mock_session


def make_query_mock(result):
    query = MagicMock()
    query.filter.return_value.first.return_value = result
    query.filter.return_value.order_by.return_value.first.return_value = result
    query.order_by.return_value.first.return_value = result
    query.join.return_value.filter.return_value.first.return_value = result
    return query


def test_start_export_conflict(client, mock_db_session):
    job = MagicMock()
    job.id = uuid4()
    session = MagicMock()
    session.id = uuid4()

    export_job = MagicMock()
    export_job.status = ExportJobStatus.processing
    export_job.created_at = datetime.utcnow()

    mock_db_session.query.side_effect = [
        make_query_mock(job),
        make_query_mock(export_job),
    ]

    with patch("app.api.routes.editor.EditSessionService") as service_mock:
        service_mock.return_value.get_or_create_session.return_value = session

        response = client.post(f"/api/jobs/{job.id}/export")

    assert response.status_code == 409


def test_start_export_success(client, mock_db_session):
    job = MagicMock()
    job.id = uuid4()
    session = MagicMock()
    session.id = uuid4()

    mock_db_session.query.side_effect = [
        make_query_mock(job),
        make_query_mock(None),
    ]

    with patch("app.api.routes.editor.EditSessionService") as service_mock, \
        patch("app.api.routes.editor.ExportProgressService") as progress_mock, \
        patch("app.api.routes.editor.export_video") as export_mock:
        service_mock.return_value.get_or_create_session.return_value = session

        def refresh_side_effect(obj):
            obj.id = uuid4()

        mock_db_session.refresh.side_effect = refresh_side_effect

        response = client.post(f"/api/jobs/{job.id}/export")

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == ExportJobStatus.pending.value
    assert "export_id" in data
    progress_mock.return_value.set_progress.assert_called_once()
    export_mock.delay.assert_called_once()


def test_get_export_status_with_progress(client, mock_db_session):
    job = MagicMock()
    job.id = uuid4()
    session = MagicMock()
    session.id = uuid4()
    export_job = MagicMock()
    export_job.id = uuid4()
    export_job.status = ExportJobStatus.processing

    mock_db_session.query.side_effect = [
        make_query_mock(job),
        make_query_mock(session),
        make_query_mock(export_job),
    ]

    with patch("app.api.routes.editor.EditSessionService") as service_mock, \
        patch("app.api.routes.editor.ExportProgressService") as progress_mock:
        service_mock.return_value.get_session.return_value = session
        progress_mock.return_value.get_progress.return_value = {
            "export_id": str(export_job.id),
            "status": "processing",
            "progress": 42.0,
            "error_message": None,
        }

        response = client.get(f"/api/jobs/{job.id}/export/status")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["progress"] == 42.0


def test_get_export_download_success(client, mock_db_session):
    job = MagicMock()
    job.id = uuid4()
    session = MagicMock()
    session.id = uuid4()
    export_job = MagicMock()
    export_job.status = ExportJobStatus.completed
    export_job.output_path = "exports/test.mp4"
    export_job.created_at = datetime.utcnow()

    mock_db_session.query.side_effect = [
        make_query_mock(job),
        make_query_mock(session),
        make_query_mock(export_job),
    ]

    with patch("app.api.routes.editor.EditSessionService") as service_mock, \
        patch("app.api.routes.editor.StorageService") as storage_mock:
        service_mock.return_value.get_session.return_value = session
        storage_mock.return_value.generate_presigned_url.return_value = "http://example.com/download"

        response = client.get(f"/api/jobs/{job.id}/export/download")

    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "http://example.com/download"
    assert "expires_at" in data
