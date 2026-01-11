import os
import uuid
from typing import BinaryIO, Optional

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings

settings = get_settings()


class StorageService:
    def __init__(self):
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
        except ClientError:
            self.s3_client.create_bucket(Bucket=self.bucket)

    def upload_file(
        self,
        file: BinaryIO,
        original_filename: str,
        content_type: str = "video/mp4",
    ) -> str:
        """
        ファイルをアップロードし、保存先パスを返す

        Args:
            file: ファイルオブジェクト
            original_filename: 元のファイル名
            content_type: MIMEタイプ

        Returns:
            保存先のファイルパス（キー）
        """
        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = f"videos/{unique_filename}"

        self.s3_client.upload_fileobj(
            file,
            self.bucket,
            file_path,
            ExtraArgs={"ContentType": content_type},
        )

        return file_path

    def download_file(self, file_path: str, destination: str) -> None:
        """
        ファイルをダウンロード

        Args:
            file_path: ストレージ内のファイルパス
            destination: ダウンロード先のローカルパス
        """
        self.s3_client.download_file(self.bucket, file_path, destination)

    def get_file_content(self, file_path: str) -> bytes:
        """
        ファイル内容を取得

        Args:
            file_path: ストレージ内のファイルパス

        Returns:
            ファイル内容のバイト列
        """
        response = self.s3_client.get_object(Bucket=self.bucket, Key=file_path)
        return response["Body"].read()

    def generate_presigned_url(
        self,
        file_path: str,
        expiration: int = 3600,
    ) -> str:
        """
        署名付きURLを生成

        Args:
            file_path: ストレージ内のファイルパス
            expiration: URLの有効期限（秒）

        Returns:
            署名付きURL
        """
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": file_path},
            ExpiresIn=expiration,
        )

    def delete_file(self, file_path: str) -> None:
        """
        ファイルを削除

        Args:
            file_path: ストレージ内のファイルパス
        """
        self.s3_client.delete_object(Bucket=self.bucket, Key=file_path)

    def file_exists(self, file_path: str) -> bool:
        """
        ファイルが存在するか確認

        Args:
            file_path: ストレージ内のファイルパス

        Returns:
            ファイルが存在する場合True
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=file_path)
            return True
        except ClientError:
            return False

    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        ファイルサイズを取得

        Args:
            file_path: ストレージ内のファイルパス

        Returns:
            ファイルサイズ（バイト）、存在しない場合はNone
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket, Key=file_path)
            return response["ContentLength"]
        except ClientError:
            return None
