"""GCSStorageService.generate_presigned_url のユニットテスト

ローカル環境に google-cloud-storage がないため、sys.modules でモックする。
"""

import sys
from unittest.mock import MagicMock, patch
import pytest


@pytest.fixture(autouse=True)
def _mock_google_modules():
    """google パッケージ群をモックモジュールとして挿入

    ``import google.auth`` は ``sys.modules["google"].auth`` を参照するため、
    親モジュールの属性として子モジュールを正しく紐付ける必要がある。
    """
    mock_storage_mod = MagicMock()
    mock_auth_mod = MagicMock()
    mock_auth_transport_mod = MagicMock()
    mock_auth_transport_requests_mod = MagicMock()
    mock_exceptions_mod = MagicMock()

    # 親→子の属性チェーンを構築
    mock_google = MagicMock()
    mock_google.auth = mock_auth_mod
    mock_google.cloud.storage = mock_storage_mod
    mock_google.cloud.exceptions = mock_exceptions_mod
    mock_auth_mod.transport = mock_auth_transport_mod
    mock_auth_mod.transport.requests = mock_auth_transport_requests_mod

    modules = {
        "google": mock_google,
        "google.cloud": mock_google.cloud,
        "google.cloud.storage": mock_storage_mod,
        "google.cloud.exceptions": mock_exceptions_mod,
        "google.auth": mock_auth_mod,
        "google.auth.transport": mock_auth_transport_mod,
        "google.auth.transport.requests": mock_auth_transport_requests_mod,
    }
    with patch.dict(sys.modules, modules):
        with patch("app.services.storage.settings") as mock_settings:
            mock_settings.use_gcs = True
            mock_settings.storage_bucket = "test-bucket"
            mock_settings.gcs_service_account_email = "sa@project.iam.gserviceaccount.com"

            yield {
                "storage": mock_storage_mod,
                "auth": mock_auth_mod,
                "auth_requests": mock_auth_transport_requests_mod,
                "settings": mock_settings,
            }


def _create_service(mocks):
    """GCSStorageService を新たにインスタンス化"""
    import importlib
    import app.services.storage as storage_mod
    importlib.reload(storage_mod)

    mock_blob = MagicMock()
    mock_blob.generate_signed_url.return_value = "https://storage.googleapis.com/signed"
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mocks["storage"].Client.return_value.bucket.return_value = mock_bucket

    service = storage_mod.GCSStorageService()
    return service, mock_blob


def test_generate_presigned_url_passes_access_token(_mock_google_modules):
    """Cloud Run 環境で access_token が generate_signed_url に渡されること (BUG-1)"""
    mocks = _mock_google_modules

    mock_credentials = MagicMock()
    mock_credentials.token = "fake-access-token"
    mock_credentials.service_account_email = "sa@project.iam.gserviceaccount.com"
    mocks["auth"].default.return_value = (mock_credentials, "project-id")

    service, mock_blob = _create_service(mocks)
    url = service.generate_presigned_url("videos/test.mp4", expiration=3600)

    assert url == "https://storage.googleapis.com/signed"
    call_kwargs = mock_blob.generate_signed_url.call_args.kwargs
    assert call_kwargs["access_token"] == "fake-access-token"
    assert call_kwargs["service_account_email"] == "sa@project.iam.gserviceaccount.com"


def test_generate_presigned_url_refreshes_credentials(_mock_google_modules):
    """credentials.refresh() が呼ばれてトークンが最新化されること"""
    mocks = _mock_google_modules

    mock_credentials = MagicMock()
    mock_credentials.token = "refreshed-token"
    mocks["auth"].default.return_value = (mock_credentials, "project-id")

    service, _ = _create_service(mocks)
    service.generate_presigned_url("videos/test.mp4")

    mock_credentials.refresh.assert_called_once()


def test_generate_presigned_url_raises_without_service_account(_mock_google_modules):
    """サービスアカウントメールが取得できない場合は RuntimeError"""
    mocks = _mock_google_modules
    mocks["settings"].gcs_service_account_email = ""

    mock_credentials = MagicMock(spec=[])  # service_account_email 属性なし
    mocks["auth"].default.return_value = (mock_credentials, "project-id")

    service, _ = _create_service(mocks)

    with pytest.raises(RuntimeError, match="サービスアカウントメール"):
        service.generate_presigned_url("videos/test.mp4")
