"""
草稿业务逻辑服务
"""
from sqlalchemy.orm import Session
from app.models.form import FormDraft
from app.schemas.submission_schemas import DraftSaveRequest
from app.core.exceptions import NotFoundError
from typing import Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DraftService:
    """草稿服务"""

    @staticmethod
    def save_draft(
            request: DraftSaveRequest,
            tenant_id: int,
            user_id: Optional[int],
            session_id: Optional[str],
            db: Session
    ) -> FormDraft:
        """保存草稿"""
        # 查找现有草稿
        if user_id:
            draft = db.query(FormDraft).filter(
                FormDraft.form_id == request.form_id,
                FormDraft.user_id == user_id,
                FormDraft.tenant_id == tenant_id
            ).first()
        elif session_id:
            draft = db.query(FormDraft).filter(
                FormDraft.form_id == request.form_id,
                FormDraft.session_id == session_id,
                FormDraft.tenant_id == tenant_id
            ).first()
        else:
            raise ValueError("user_id 或 session_id 必须提供一个")

        # 获取表单版本
        from app.models.form import FormVersion
        version = db.query(FormVersion).filter(
            FormVersion.form_id == request.form_id,
            FormVersion.version > 0
        ).order_by(FormVersion.version.desc()).first()

        if not version:
            raise NotFoundError("表单版本不存在")

        now = datetime.now()
        expires_at = now + timedelta(days=7)

        if draft:
            # 更新现有草稿
            draft.draft_data = request.data
            draft.auto_saved_at = now
            draft.expires_at = expires_at
            draft.status = "active"
        else:
            # 创建新草稿
            draft = FormDraft(
                tenant_id=tenant_id,
                form_id=request.form_id,
                form_version_id=version.id,
                user_id=user_id,
                session_id=session_id,
                draft_data=request.data,
                auto_saved_at=now,
                expires_at=expires_at,
                status="active"
            )
            db.add(draft)

        db.commit()
        db.refresh(draft)

        logger.info(f"Saved draft: form_id={request.form_id}, user_id={user_id}")
        return draft

    @staticmethod
    def get_draft(
            form_id: int,
            tenant_id: int,
            user_id: Optional[int],
            session_id: Optional[str],
            db: Session
    ) -> Optional[FormDraft]:
        """获取草稿"""
        if user_id:
            draft = db.query(FormDraft).filter(
                FormDraft.form_id == form_id,
                FormDraft.user_id == user_id,
                FormDraft.tenant_id == tenant_id,
                FormDraft.status == "active"
            ).first()
        elif session_id:
            draft = db.query(FormDraft).filter(
                FormDraft.form_id == form_id,
                FormDraft.session_id == session_id,
                FormDraft.tenant_id == tenant_id,
                FormDraft.status == "active"
            ).first()
        else:
            return None

        # 检查是否过期
        if draft and draft.expires_at and draft.expires_at < datetime.now():
            draft.status = "expired"
            db.commit()
            return None

        return draft

    @staticmethod
    def delete_draft(
            draft_id: int,
            tenant_id: int,
            db: Session
    ) -> bool:
        """删除草稿"""
        draft = db.query(FormDraft).filter(
            FormDraft.id == draft_id,
            FormDraft.tenant_id == tenant_id
        ).first()

        if not draft:
            return False

        db.delete(draft)
        db.commit()

        logger.info(f"Deleted draft: id={draft_id}")
        return True

    @staticmethod
    def delete_draft_by_user_form(
            user_id: int,
            form_id: int,
            tenant_id: int,
            db: Session
    ) -> bool:
        """根据用户和表单删除草稿"""
        draft = db.query(FormDraft).filter(
            FormDraft.form_id == form_id,
            FormDraft.user_id == user_id,
            FormDraft.tenant_id == tenant_id
        ).first()

        if draft:
            db.delete(draft)
            db.commit()
            return True

        return False

    @staticmethod
    def clean_expired_drafts(db: Session) -> int:
        """清理过期草稿"""
        now = datetime.now()
        result = db.query(FormDraft).filter(
            FormDraft.expires_at < now
        ).delete()

        db.commit()

        logger.info(f"Cleaned {result} expired drafts")
        return result