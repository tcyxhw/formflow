"""
文件存储服务
支持MinIO和本地存储
"""
from minio import Minio
from minio.error import S3Error
from app.config import settings
from app.core.exceptions import ValidationError, BusinessError
from pathlib import Path
import hashlib
import uuid
from datetime import timedelta
from typing import Optional, BinaryIO
import logging

logger = logging.getLogger(__name__)


class StorageService:
    """文件存储服务"""

    _client: Optional[Minio] = None

    @classmethod
    def get_client(cls) -> Minio:
        """获取MinIO客户端（单例）"""
        if cls._client is None:
            cls._client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            # 确保bucket存在
            cls._ensure_bucket(settings.MINIO_BUCKET)
        return cls._client

    @classmethod
    def _ensure_bucket(cls, bucket_name: str):
        """确保bucket存在"""
        try:
            client = cls._client
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e}")
            raise BusinessError(f"存储桶创建失败: {str(e)}")

    @staticmethod
    def _get_file_hash(file_data: bytes) -> str:
        """计算文件SHA256哈希"""
        return hashlib.sha256(file_data).hexdigest()

    @staticmethod
    def _get_storage_path(tenant_id: int, category: str, file_hash: str, extension: str) -> str:
        """
        生成存储路径
        格式: {tenant_id}/{category}/{hash[:2]}/{hash[2:4]}/{hash}.{ext}
        """
        return f"{tenant_id}/{category}/{file_hash[:2]}/{file_hash[2:4]}/{file_hash}{extension}"

    @classmethod
    def upload_file(
            cls,
            file_data: bytes,
            filename: str,
            content_type: str,
            tenant_id: int,
            category: str = "forms"
    ) -> dict:
        """
        上传文件到MinIO

        Args:
            file_data: 文件二进制数据
            filename: 原始文件名
            content_type: MIME类型
            tenant_id: 租户ID
            category: 分类（forms/qrcodes/exports）

        Returns:
            {
                "storage_path": "路径",
                "file_hash": "哈希值",
                "size": 文件大小
            }
        """
        # 检查文件大小
        file_size = len(file_data)
        if file_size > settings.UPLOAD_MAX_SIZE:
            raise ValidationError(
                f"文件大小超过限制（最大{settings.UPLOAD_MAX_SIZE / 1024 / 1024}MB）"
            )

        # 检查文件扩展名
        extension = Path(filename).suffix.lower()
        if extension not in settings.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"不支持的文件类型：{extension}，允许的类型：{settings.ALLOWED_EXTENSIONS}"
            )

        # 计算哈希
        file_hash = cls._get_file_hash(file_data)

        # 生成存储路径
        storage_path = cls._get_storage_path(tenant_id, category, file_hash, extension)

        try:
            client = cls.get_client()

            # 检查文件是否已存在（去重）
            try:
                stat = client.stat_object(settings.MINIO_BUCKET, storage_path)
                logger.info(f"File already exists, reusing: {storage_path}")
                return {
                    "storage_path": storage_path,
                    "file_hash": file_hash,
                    "size": file_size
                }
            except S3Error as e:
                if e.code != 'NoSuchKey':
                    raise

            # 上传文件
            from io import BytesIO
            client.put_object(
                settings.MINIO_BUCKET,
                storage_path,
                BytesIO(file_data),
                length=file_size,
                content_type=content_type
            )

            logger.info(f"Uploaded file: {storage_path}, size: {file_size}")

            return {
                "storage_path": storage_path,
                "file_hash": file_hash,
                "size": file_size
            }

        except S3Error as e:
            logger.error(f"Failed to upload file: {e}")
            raise BusinessError(f"文件上传失败: {str(e)}")

    @classmethod
    def get_download_url(cls, storage_path: str, expires: int = 3600) -> str:
        """
        生成预签名下载URL

        Args:
            storage_path: 存储路径
            expires: 有效期（秒），默认1小时

        Returns:
            预签名URL
        """
        try:
            client = cls.get_client()
            url = client.presigned_get_object(
                settings.MINIO_BUCKET,
                storage_path,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to generate download URL: {e}")
            raise BusinessError(f"生成下载链接失败: {str(e)}")

    @classmethod
    def get_file_data(cls, storage_path: str) -> bytes:
        """获取文件二进制数据"""
        response = None
        try:
            client = cls.get_client()
            response = client.get_object(settings.MINIO_BUCKET, storage_path)
            return response.read()
        except S3Error as e:
            logger.error(f"Failed to get file data: {e}")
            raise BusinessError(f"文件读取失败: {str(e)}")
        finally:
            if response:
                response.close()
                response.release_conn()

    @classmethod
    def delete_file(cls, storage_path: str) -> bool:
        """删除文件"""
        try:
            client = cls.get_client()
            client.remove_object(settings.MINIO_BUCKET, storage_path)
            logger.info(f"Deleted file: {storage_path}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    @classmethod
    def file_exists(cls, storage_path: str) -> bool:
        """检查文件是否存在"""
        try:
            client = cls.get_client()
            client.stat_object(settings.MINIO_BUCKET, storage_path)
            return True
        except S3Error:
            return False