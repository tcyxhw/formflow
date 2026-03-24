"""
附件业务逻辑服务
"""
from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.models.form import Attachment
from app.services.storage_service import StorageService
from app.core.exceptions import NotFoundError, AuthorizationError
from typing import List, Optional
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


class AttachmentService:
    """附件服务"""

    @staticmethod
    async def upload_attachment(
            file: UploadFile,
            tenant_id: int,
            user_id: int,
            owner_type: str = "temp",
            owner_id: Optional[int] = None,
            db: Session = None
    ) -> Attachment:
        """上传附件"""
        # 读取文件内容
        file_content = await file.read()

        # 上传到MinIO
        upload_result = StorageService.upload_file(
            file_data=file_content,
            filename=file.filename,
            content_type=file.content_type,
            tenant_id=tenant_id,
            category="forms"
        )

        # 创建附件记录
        attachment = Attachment(
            tenant_id=tenant_id,
            owner_type=owner_type,
            owner_id=owner_id,
            file_name=file.filename,
            content_type=file.content_type,
            size=upload_result["size"],
            storage_path=upload_result["storage_path"],
            created_by=user_id
        )

        db.add(attachment)
        db.commit()
        db.refresh(attachment)

        logger.info(f"Uploaded attachment: id={attachment.id}, filename={file.filename}")
        return attachment

    @staticmethod
    def bind_attachment(
            attachment_id: int,
            owner_type: str,
            owner_id: int,
            tenant_id: int,
            db: Session
    ) -> bool:
        """绑定附件到提交"""
        attachment = db.query(Attachment).filter(
            Attachment.id == attachment_id,
            Attachment.tenant_id == tenant_id
        ).first()

        if not attachment:
            raise NotFoundError(f"附件不存在: id={attachment_id}")

        attachment.owner_type = owner_type
        attachment.owner_id = owner_id

        db.commit()

        logger.info(f"Bound attachment: id={attachment_id} to {owner_type}:{owner_id}")
        return True

    @staticmethod
    def get_attachment_by_id(
            attachment_id: int,
            tenant_id: int,
            db: Session
    ) -> Attachment:
        """查询附件"""
        attachment = db.query(Attachment).filter(
            Attachment.id == attachment_id,
            Attachment.tenant_id == tenant_id
        ).first()

        if not attachment:
            raise NotFoundError(f"附件不存在: id={attachment_id}")

        return attachment

    @staticmethod
    def list_attachments(
            owner_type: str,
            owner_id: int,
            tenant_id: int,
            db: Session
    ) -> List[Attachment]:
        """查询对象的所有附件"""
        return db.query(Attachment).filter(
            Attachment.owner_type == owner_type,
            Attachment.owner_id == owner_id,
            Attachment.tenant_id == tenant_id
        ).all()

    @staticmethod
    def delete_attachment(
            attachment_id: int,
            tenant_id: int,
            user_id: int,
            db: Session
    ) -> bool:
        """删除附件"""
        attachment = AttachmentService.get_attachment_by_id(attachment_id, tenant_id, db)

        # 权限检查
        if attachment.created_by != user_id:
            raise AuthorizationError("只能删除自己上传的附件")

        # 删除MinIO文件
        try:
            StorageService.delete_file(attachment.storage_path)
        except Exception as e:
            logger.warning(f"Delete file from storage failed: {e}")

        # 删除数据库记录
        db.delete(attachment)
        db.commit()

        logger.info(f"Deleted attachment: id={attachment_id}")
        return True

    @staticmethod
    def get_download_url(
            attachment_id: int,
            tenant_id: int,
            expires: int = 3600,
            db: Session = None
    ) -> str:
        """生成下载URL（返回后端代理URL，而不是MinIO预签名URL）"""
        # 返回后端代理URL，确保认证一致性和避免跨域问题
        return f"/api/v1/attachments/{attachment_id}/download"

    @staticmethod
    def clean_temp_attachments(db: Session) -> int:
        """清理临时附件"""
        cutoff_time = datetime.now() - timedelta(minutes=30)

        temp_attachments = db.query(Attachment).filter(
            Attachment.owner_type == "temp",
            Attachment.created_at < cutoff_time
        ).all()

        count = 0
        for attachment in temp_attachments:
            try:
                StorageService.delete_file(attachment.storage_path)
                db.delete(attachment)
                count += 1
            except Exception as e:
                logger.error(f"Clean temp attachment error: {attachment.id}, {e}")

        db.commit()

        logger.info(f"Cleaned {count} temp attachments")
        return count
