"""
表单版本服务
"""
from sqlalchemy.orm import Session
from app.models.form import FormVersion
from app.core.exceptions import NotFoundError
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class FormVersionService:
    """表单版本服务"""

    @staticmethod
    def get_version_by_id(
            version_id: int,
            tenant_id: int,
            db: Session
    ) -> FormVersion:
        """根据ID获取版本"""
        version = db.query(FormVersion).filter(
            FormVersion.id == version_id,
            FormVersion.tenant_id == tenant_id
        ).first()

        if not version:
            raise NotFoundError(f"版本不存在: id={version_id}")

        return version

    @staticmethod
    def get_version_by_number(
            form_id: int,
            version_num: int,
            tenant_id: int,
            db: Session
    ) -> FormVersion:
        """根据版本号获取版本"""
        version = db.query(FormVersion).filter(
            FormVersion.form_id == form_id,
            FormVersion.version == version_num,
            FormVersion.tenant_id == tenant_id
        ).first()

        if not version:
            raise NotFoundError(f"版本不存在: form_id={form_id}, version={version_num}")

        return version

    @staticmethod
    def list_versions(
            form_id: int,
            tenant_id: int,
            db: Session,
            include_draft: bool = False
    ) -> List[FormVersion]:
        """
        获取表单的所有版本

        Args:
            form_id: 表单ID
            tenant_id: 租户ID
            db: 数据库会话
            include_draft: 是否包含草稿版本

        Returns:
            版本列表（按版本号降序）
        """
        query = db.query(FormVersion).filter(
            FormVersion.form_id == form_id,
            FormVersion.tenant_id == tenant_id
        )

        if not include_draft:
            query = query.filter(FormVersion.version > 0)

        return query.order_by(FormVersion.version.desc()).all()

    @staticmethod
    def get_latest_version(
            form_id: int,
            tenant_id: int,
            db: Session
    ) -> Optional[FormVersion]:
        """获取最新发布版本"""
        return db.query(FormVersion).filter(
            FormVersion.form_id == form_id,
            FormVersion.tenant_id == tenant_id,
            FormVersion.version > 0
        ).order_by(FormVersion.version.desc()).first()

    @staticmethod
    def compare_versions(
            version_id_1: int,
            version_id_2: int,
            tenant_id: int,
            db: Session
    ) -> dict:
        """
        比较两个版本的差异

        Returns:
            {
                "version_1": {...},
                "version_2": {...},
                "diff": {
                    "added_fields": [...],
                    "removed_fields": [...],
                    "modified_fields": [...]
                }
            }
        """
        v1 = FormVersionService.get_version_by_id(version_id_1, tenant_id, db)
        v2 = FormVersionService.get_version_by_id(version_id_2, tenant_id, db)

        # 简单的字段差异比较
        fields_1 = {f["id"]: f for f in v1.schema_json.get("fields", [])}
        fields_2 = {f["id"]: f for f in v2.schema_json.get("fields", [])}

        added = [fields_2[fid] for fid in fields_2 if fid not in fields_1]
        removed = [fields_1[fid] for fid in fields_1 if fid not in fields_2]
        modified = []

        for fid in fields_1:
            if fid in fields_2 and fields_1[fid] != fields_2[fid]:
                modified.append({
                    "field_id": fid,
                    "old": fields_1[fid],
                    "new": fields_2[fid]
                })

        return {
            "version_1": {
                "id": v1.id,
                "version": v1.version,
                "published_at": v1.published_at
            },
            "version_2": {
                "id": v2.id,
                "version": v2.version,
                "published_at": v2.published_at
            },
            "diff": {
                "added_fields": added,
                "removed_fields": removed,
                "modified_fields": modified
            }
        }