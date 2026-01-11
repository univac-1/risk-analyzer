import pytest
from io import BytesIO
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_storage():
    with patch("app.api.routes.videos.StorageService") as mock:
        mock_instance = MagicMock()
        mock_instance.upload_file.return_value = "videos/test-uuid.mp4"
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_db():
    with patch("app.api.routes.videos.SessionLocal") as mock:
        mock_session = MagicMock()
        mock.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_progress():
    with patch("app.api.routes.videos.ProgressService") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_task():
    with patch("app.api.routes.videos.analyze_video") as mock:
        mock.delay.return_value = MagicMock(id="task-123")
        yield mock


def test_upload_video_invalid_extension(client):
    """mp4形式以外のファイルはエラーになること"""
    file_content = b"fake video content"
    response = client.post(
        "/api/videos",
        files={"file": ("test.avi", BytesIO(file_content), "video/avi")},
        data={
            "purpose": "Test purpose",
            "platform": "twitter",
            "target_audience": "Test audience",
        },
    )
    assert response.status_code == 415


def test_upload_video_missing_file(client):
    """ファイルなしでアップロードするとエラーになること"""
    response = client.post(
        "/api/videos",
        data={
            "purpose": "Test purpose",
            "platform": "twitter",
            "target_audience": "Test audience",
        },
    )
    assert response.status_code == 422


def test_upload_video_missing_metadata(client):
    """メタ情報なしでアップロードするとエラーになること"""
    file_content = b"fake video content"
    response = client.post(
        "/api/videos",
        files={"file": ("test.mp4", BytesIO(file_content), "video/mp4")},
    )
    assert response.status_code == 422
