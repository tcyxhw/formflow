"""
模块用途: 表单权限服务
依赖配置: 无
数据流向: API -> Service -> ORM -> 数据库
函数清单:
    - list_permissions(): 获取表单权限列表
    - create_permission(): 新建表单权限
    - update_permission(): 更新权限有效期
    - delete_permission(): 删除表单权限
    - has_permission(): 判断用户是否拥有指定权限
    - ensure_permission(): 确保用户具备权限
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationError, BusinessError, NotFoundError
from app.models.form import FormPermission
from app.models.user import User, UserRole, UserPosition
from app.schemas.form_permission_schemas import (
    FormPermissionCreateRequest,
    FormPermissionMeResponse,
    FormPermissionUpdateRequest,
    FormPermissionResponse,
    GrantType,
    PermissionType,
)


class FormPermissionService:
    """表单权限业务逻辑"""

    @staticmethod
    def list_permissions(form_id: int, tenant_id: int, db: Session) -> List[FormPermission]:
        """获取表单权限列表。

        Time: O(N), Space: O(N)
        """

        return (
            db.query(FormPermission)
            .filter(
                FormPermission.form_id == form_id,
                FormPermission.tenant_id == tenant_id,
            )
            .order_by(FormPermission.created_at.desc())
            .all()
        )

    @staticmethod
    def create_permission(
        form_id: int,
        tenant_id: int,
        request: FormPermissionCreateRequest,
        db: Session,
    ) -> FormPermission:
        """创建新的表单权限。

        Time: O(1), Space: O(1)
        """

        existing = (
            db.query(FormPermission)
            .filter(
                FormPermission.tenant_id == tenant_id,
                FormPermission.form_id == form_id,
                FormPermission.grant_type == request.grant_type.value,
                FormPermission.grantee_id == request.grantee_id,
                FormPermission.permission == request.permission.value,
            )
            .first()
        )

        if existing:
            raise BusinessError("该授权已存在")

        permission = FormPermission(
            tenant_id=tenant_id,
            form_id=form_id,
            grant_type=request.grant_type.value,
            grantee_id=request.grantee_id,
            permission=request.permission.value,
            valid_from=request.valid_from,
            valid_to=request.valid_to,
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        return permission

    @staticmethod
    def update_permission(
        permission_id: int,
        tenant_id: int,
        request: FormPermissionUpdateRequest,
        db: Session,
    ) -> FormPermission:
        """更新表单权限的有效期。

        Time: O(1), Space: O(1)
        """

        permission = FormPermissionService._get_permission(permission_id, tenant_id, db)

        if request.valid_from is not None:
            permission.valid_from = request.valid_from
        if request.valid_to is not None:
            permission.valid_to = request.valid_to

        db.commit()
        db.refresh(permission)
        return permission

    @staticmethod
    def delete_permission(permission_id: int, tenant_id: int, db: Session) -> None:
        """删除表单权限。

        Time: O(1), Space: O(1)
        """

        permission = FormPermissionService._get_permission(permission_id, tenant_id, db)
        db.delete(permission)
        db.commit()

    @staticmethod
    def has_permission(
        form_id: int,
        tenant_id: int,
        permission: PermissionType,
        user_id: Optional[int],
        db: Session,
        allow_owner: bool = True,
    ) -> bool:
        """判断用户是否拥有指定表单权限。

        Time: O(N), Space: O(N)
        """

        if not user_id:
            return False

        user = (
            db.query(User)
            .filter(User.id == user_id, User.tenant_id == tenant_id)
            .first()
        )
        if not user:
            return False

        if allow_owner and FormPermissionService._is_form_owner(form_id, tenant_id, user_id, db):
            return True

        now = datetime.utcnow()
        permissions = (
            db.query(FormPermission)
            .filter(
                FormPermission.form_id == form_id,
                FormPermission.tenant_id == tenant_id,
                FormPermission.permission == permission.value,
                
                (FormPermission.valid_from.is_(None) | (FormPermission.valid_from <= now)),
                (FormPermission.valid_to.is_(None) | (FormPermission.valid_to >= now)),
            )
            .all()
        )

        if not permissions:
            return False

        role_ids = FormPermissionService._get_user_role_ids(user_id, tenant_id, db)
        position_ids = FormPermissionService._get_user_position_ids(user_id, tenant_id, db)

        for perm in permissions:
            grant_type = GrantType(perm.grant_type)
            if grant_type == GrantType.USER and perm.grantee_id == user_id:
                return True
            if grant_type == GrantType.ROLE and perm.grantee_id in role_ids:
                return True
            if grant_type == GrantType.DEPARTMENT and user.department_id and perm.grantee_id == user.department_id:
                return True
            if grant_type == GrantType.POSITION and perm.grantee_id in position_ids:
                return True

        return False

    @staticmethod
    def ensure_permission(
        form_id: int,
        tenant_id: int,
        permission: PermissionType,
        user_id: Optional[int],
        db: Session,
    ) -> None:
        """确保用户具备权限，否则抛出异常。

        Time: O(N), Space: O(N)
        """

        if not FormPermissionService.has_permission(form_id, tenant_id, permission, user_id, db):
            raise AuthorizationError("缺少表单访问权限")

    @staticmethod
    def get_user_permissions(
        form_id: int,
        tenant_id: int,
        user_id: Optional[int],
        db: Session,
    ) -> FormPermissionMeResponse:
        """聚合用户当前拥有的表单权限。

        :param form_id: 表单 ID
        :param tenant_id: 租户 ID
        :param user_id: 用户 ID，可为空（匿名）
        :param db: 会话
        :return: 权限概览

        Time: O(N), Space: O(N)
        """

        overview = FormPermissionMeResponse()
        if not user_id:
            return overview

        user = (
            db.query(User)
            .filter(User.id == user_id, User.tenant_id == tenant_id, User.is_active.is_(True))
            .first()
        )
        if not user:
            return overview

        is_owner = FormPermissionService._is_form_owner(form_id, tenant_id, user_id, db)
        now = datetime.utcnow()

        records = (
            db.query(FormPermission)
            .filter(
                FormPermission.form_id == form_id,
                FormPermission.tenant_id == tenant_id,
                (FormPermission.valid_from.is_(None) | (FormPermission.valid_from <= now)),
                (FormPermission.valid_to.is_(None) | (FormPermission.valid_to >= now)),
            )
            .all()
        )

        permissions: set[PermissionType] = set()
        if records:
            role_ids = FormPermissionService._get_user_role_ids(user_id, tenant_id, db)
            position_ids = FormPermissionService._get_user_position_ids(user_id, tenant_id, db)

            for record in records:
                grant_type = GrantType(record.grant_type)
                granted = False
                if grant_type == GrantType.USER and record.grantee_id == user_id:
                    granted = True
                elif grant_type == GrantType.ROLE and record.grantee_id in role_ids:
                    granted = True
                elif grant_type == GrantType.DEPARTMENT and user.department_id and record.grantee_id == user.department_id:
                    granted = True
                elif grant_type == GrantType.POSITION and record.grantee_id in position_ids:
                    granted = True

                if granted:
                    permissions.add(PermissionType(record.permission))

        if is_owner:
            permissions.update(
                {
                    PermissionType.VIEW,
                    PermissionType.FILL,
                    PermissionType.EDIT,
                    PermissionType.EXPORT,
                    PermissionType.MANAGE,
                }
            )

        overview.permissions = [perm for perm in sorted(permissions, key=lambda item: item.value)]
        overview.can_view = PermissionType.VIEW in permissions
        overview.can_fill = PermissionType.FILL in permissions
        overview.can_edit = PermissionType.EDIT in permissions
        overview.can_export = PermissionType.EXPORT in permissions
        overview.can_manage = PermissionType.MANAGE in permissions
        overview.is_owner = is_owner
        return overview

    # -------------------- 辅助方法 --------------------
    @staticmethod
    def _get_permission(permission_id: int, tenant_id: int, db: Session) -> FormPermission:
        """根据ID获取权限记录。

        Time: O(1), Space: O(1)
        """

        permission = (
            db.query(FormPermission)
            .filter(
                FormPermission.id == permission_id,
                FormPermission.tenant_id == tenant_id,
            )
            .first()
        )
        if not permission:
            raise NotFoundError("权限记录不存在")
        return permission

    @staticmethod
    def _is_form_owner(form_id: int, tenant_id: int, user_id: int, db: Session) -> bool:
        """判断是否为表单创建者。

        Time: O(1), Space: O(1)
        """

        from app.models.form import Form

        form = (
            db.query(Form)
            .filter(Form.id == form_id, Form.tenant_id == tenant_id)
            .first()
        )
        return bool(form and form.owner_user_id == user_id)

    @staticmethod
    def _get_user_role_ids(user_id: int, tenant_id: int, db: Session) -> List[int]:
        """获取用户角色ID列表。

        Time: O(N), Space: O(N)
        """

        return [role.role_id for role in db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.tenant_id == tenant_id,
        ).all()]

    @staticmethod
    def _get_user_position_ids(user_id: int, tenant_id: int, db: Session) -> List[int]:
        """获取用户岗位ID列表。

        Time: O(N), Space: O(N)
        """

        return [pos.position_id for pos in db.query(UserPosition).filter(
            UserPosition.user_id == user_id,
            UserPosition.tenant_id == tenant_id,
        ).all()]
