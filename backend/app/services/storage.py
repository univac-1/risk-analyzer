import os
import uuid
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional

from app.config import get_settings

settings = get_settings()


class BaseStorageService(ABC):
    """ストレージサービスの基底クラス"""

    @abstractmethod
    def upload_file(
        self,
        file: BinaryIO,
        original_filename: str,
        content_type: str = "video/mp4",
    ) -> str:
        """ファイルをアップロードし、保存先パスを返す"""
        pass

    @abstractmethod
    def download_file(self, file_path: str, destination: str) -> None:
        """ファイルをダウンロード"""
        pass

    @abstractmethod
    def get_file_content(self, file_path: str) -> bytes:
        """ファイル内容を取得"""
        pass

    @abstractmethod
    def generate_presigned_url(self, file_path: str, expiration: int = 3600) -> str:
        """署名付きURLを生成"""
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        """ファイルを削除"""
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """ファイルが存在するか確認"""
        pass

    @abstractmethod
    def get_file_size(self, file_path: str) -> Optional[int]:
        """ファイルサイズを取得"""
        pass

    @abstractmethod
    def get_file_stream(self, file_path: str):
        """ファイルをストリーム形式で取得"""
        pass

    def _generate_unique_path(self, original_filename: str) -> str:
        """ユニークなファイルパスを生成"""
        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        return f"videos/{unique_filename}"


class S3StorageService(BaseStorageService):
    """S3/MinIO互換ストレージサービス"""

    def __init__(self):
        import boto3
        from botocore.exceptions import ClientError

        self.ClientError = ClientError
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.storage_endpoint,
            aws_access_key_id=settings.storage_access_key,
            aws_secret_access_key=settings.storage_secret_key,
        )
        self.bucket = settings.storage_bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """バケットが存在しない場合は作成"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except self.ClientError:
            self.s3_client.create_bucket(Bucket=self.bucket)

    def upload_file(
        self,
        file: BinaryIO,
        original_filename: str,
        content_type: str = "video/mp4",
    ) -> str:
        file_path = self._generate_unique_path(original_filename)
        self.s3_client.upload_fileobj(
            file,
            self.bucket,
            file_path,
            ExtraArgs={"ContentType": content_type},
        )
        return file_path

    def upload_file_to_path(
        self,
        file: BinaryIO,
        file_path: str,
        content_type: str = "video/mp4",
    ) -> str:
        """
        指定したパスにファイルをアップロード

        Args:
            file: ファイルオブジェクト
            file_path: 保存先のファイルパス（キー）
            content_type: MIMEタイプ

        Returns:
            保存先のファイルパス（キー）
        """
        self.s3_client.upload_fileobj(
            file,
            self.bucket,
            file_path,
            ExtraArgs={"ContentType": content_type},
        )
        return file_path

    def download_file(self, file_path: str, destination: str) -> None:
        self.s3_client.download_file(self.bucket, file_path, destination)

    def get_file_content(self, file_path: str) -> bytes:
        response = self.s3_client.get_object(Bucket=self.bucket, Key=file_path)
        return response["Body"].read()

    def generate_presigned_url(self, file_path: str, expiration: int = 3600) -> str:
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": file_path},
            ExpiresIn=expiration,
        )

    def delete_file(self, file_path: str) -> None:
        self.s3_client.delete_object(Bucket=self.bucket, Key=file_path)

    def file_exists(self, file_path: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=file_path)
            return True
        except self.ClientError:
            return False

    def get_file_size(self, file_path: str) -> Optional[int]:
        try:
            response = self.s3_client.head_object(Bucket=self.bucket, Key=file_path)
            return response["ContentLength"]
        except self.ClientError:
            return None

    def get_file_stream(self, file_path: str):
        """Get file as streaming response"""
        response = self.s3_client.get_object(Bucket=self.bucket, Key=file_path)
        return response["Body"]


class GCSStorageService(BaseStorageService):
    """Google Cloud Storage サービス"""

    def __init__(self):
        from google.cloud import storage
        from google.cloud.exceptions import NotFound

        self.NotFound = NotFound
        self.client = storage.Client()
        self.bucket_name = settings.storage_bucket
        self.bucket = self.client.bucket(self.bucket_name)

    def upload_file(
        self,
        file: BinaryIO,
        original_filename: str,
        content_type: str = "video/mp4",
    ) -> str:
        file_path = self._generate_unique_path(original_filename)
        blob = self.bucket.blob(file_path)
        blob.upload_from_file(file, content_type=content_type)
        return file_path

    def upload_file_to_path(
        self,
        file: BinaryIO,
        file_path: str,
        content_type: str = "video/mp4",
    ) -> str:
        blob = self.bucket.blob(file_path)
        blob.upload_from_file(file, content_type=content_type)
        return file_path

    def download_file(self, file_path: str, destination: str) -> None:
        blob = self.bucket.blob(file_path)
        blob.download_to_filename(destination)

    def get_file_content(self, file_path: str) -> bytes:
        blob = self.bucket.blob(file_path)
        return blob.download_as_bytes()

    def generate_presigned_url(self, file_path: str, expiration: int = 3600) -> str:
        from datetime import timedelta
        import google.auth
        from google.auth.transport import requests as google_requests

        blob = self.bucket.blob(file_path)

        # Get credentials and refresh to ensure a valid access token
        credentials, _ = google.auth.default()
        auth_request = google_requests.Request()
        credentials.refresh(auth_request)

        # Resolve service account email
        service_account_email = settings.gcs_service_account_email
        if not service_account_email:
            if hasattr(credentials, 'service_account_email'):
                service_account_email = credentials.service_account_email
            elif hasattr(credentials, 'signer_email'):
                service_account_email = credentials.signer_email

        if not service_account_email:
            raise ValueError(
                "gcs_service_account_email が設定されていないため署名付きURLを生成できません。"
            )

        # Cloud Run上では access_token を渡すことでIAM signBlob APIを使って署名する
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration),
            method="GET",
            service_account_email=service_account_email,
            access_token=credentials.token,
        )

    def delete_file(self, file_path: str) -> None:
        blob = self.bucket.blob(file_path)
        blob.delete()

    def file_exists(self, file_path: str) -> bool:
        blob = self.bucket.blob(file_path)
        return blob.exists()

    def get_file_size(self, file_path: str) -> Optional[int]:
        blob = self.bucket.blob(file_path)
        blob.reload()
        return blob.size

    def get_file_stream(self, file_path: str):
        """Get file as streaming response"""
        from io import BytesIO

        blob = self.bucket.blob(file_path)
        # Download to BytesIO buffer
        buffer = BytesIO()
        blob.download_to_file(buffer)
        buffer.seek(0)
        return buffer


def StorageService() -> BaseStorageService:
    """設定に基づいて適切なストレージサービスを返すファクトリ関数"""
    if settings.use_gcs:
        return GCSStorageService()
    else:
        return S3StorageService()
