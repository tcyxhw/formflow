"""
模块用途: FormPermissionService 单元测试
依赖配置: sqlite 内存数据库
数据流向: sqlite -> SQLAlchemy Session -> Service 调用 -> 断言
函数清单:
    - db_session(): 提供测试数据库会话
    - prepare_form_context(): 构造基础数据
    - test_create_and_list_permissions(): 测试创建与查询
    - test_duplicate_permission_raises_business_error(): 测试重复校验
    - test_update_permission_time_range(): 测试有效期更新
    - test_role_based_permission_resolution(): 测试角色授权
    - test_owner_has_permission_without_explicit_grant(): 测试创建者默认权限
    - test_ensure_permission_denied_for_unauthorized_user(): 测试无权访问
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterator, Tuple

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.core.exceptions import AuthorizationError, BusinessError
from app.models import form as form_models  # noqa: F401 注册模型
from app.models import user as user_models  # noqa: F401 注册模型
from app.models.form import Form
from app.models.user import Role, Tenant, User, UserRole
from app.schemas.form_permission_schemas import (
    FormPermissionCreateRequest,
    FormPermissionUpdateRequest,
    GrantType,
    PermissionType,
)
from app.services.form_permission_service import FormPermissionService


@pytest.fixture()
def db_session() -> Iterator[Session]:
    """构建独立的 sqlite 会话。

    Time: O(1), Space: O(1)
    """

    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def prepare_form_context(db: Session) -> Tuple[Tenant, User, Form]:
    """初始化租户、用户与表单。

    Time: O(1), Space: O(1)
    """

    tenant = Tenant(name="测试学校")
    db.add(tenant)
    db.flush()

    owner = User(
        tenant_id=tenant.id,
        account="owner",
        password_hash="hashed",
        name="表单创建者",
        email="owner@example.com",
        is_active=True,
    )
    db.add(owner)
    db.flush()

    form = Form(
        tenant_id=tenant.id,
        name="测试表单",
        access_mode="authenticated",
        owner_user_id=owner.id,
        status="draft",
        allow_edit=True,
        max_edit_count=1,
    )
    db.add(form)
    db.commit()
    db.refresh(form)
    return tenant, owner, form


def test_create_and_list_permissions(db_session: Session) -> None:
    """验证创建权限后可在列表中查询。"""

    tenant, owner, form = prepare_form_context(db_session)
    request = FormPermissionCreateRequest(
        grant_type=GrantType.USER,
        grantee_id=owner.id,
        permission=PermissionType.MANAGE,
    )

    created = FormPermissionService.create_permission(form.id, tenant.id, request, db_session)
    assert created.id is not None

    permissions = FormPermissionService.list_permissions(form.id, tenant.id, db_session)
    assert len(permissions) == 1
    assert permissions[0].grantee_id == owner.id


def test_duplicate_permission_raises_business_error(db_session: Session) -> None:
    """重复授权应抛出 BusinessError。"""

    tenant, owner, form = prepare_form_context(db_session)
    request = FormPermissionCreateRequest(
        grant_type=GrantType.USER,
        grantee_id=owner.id,
        permission=PermissionType.MANAGE,
    )
    FormPermissionService.create_permission(form.id, tenant.id, request, db_session)

    with pytest.raises(BusinessError):
        FormPermissionService.create_permission(form.id, tenant.id, request, db_session)


def test_update_permission_time_range(db_session: Session) -> None:
    """更新有效期应正确保存。"""

    tenant, owner, form = prepare_form_context(db_session)
    request = FormPermissionCreateRequest(
        grant_type=GrantType.USER,
        grantee_id=owner.id,
        permission=PermissionType.VIEW,
    )
    permission = FormPermissionService.create_permission(form.id, tenant.id, request, db_session)

    valid_from = datetime.now(timezone.utc)
    valid_to = valid_from + timedelta(days=7)
    update_request = FormPermissionUpdateRequest(valid_from=valid_from, valid_to=valid_to)

    updated = FormPermissionService.update_permission(permission.id, tenant.id, update_request, db_session)
    assert updated.valid_from == valid_from
    assert updated.valid_to == valid_to


def test_role_based_permission_resolution(db_session: Session) -> None:
    """角色授权的用户应具备对应权限。"""

    tenant, owner, form = prepare_form_context(db_session)
    approver = User(
        tenant_id=tenant.id,
        account="approver",
        password_hash="hashed",
        name="审批人",
        is_active=True,
    )
    db_session.add(approver)
    db_session.flush()

    role = Role(tenant_id=tenant.id, name="审批角色")
    db_session.add(role)
    db_session.flush()

    user_role = UserRole(tenant_id=tenant.id, user_id=approver.id, role_id=role.id)
    db_session.add(user_role)
    db_session.commit()

    request = FormPermissionCreateRequest(
        grant_type=GrantType.ROLE,
        grantee_id=role.id,
        permission=PermissionType.FILL,
    )
    FormPermissionService.create_permission(form.id, tenant.id, request, db_session)

    has_permission = FormPermissionService.has_permission(
        form_id=form.id,
        tenant_id=tenant.id,
        permission=PermissionType.FILL,
        user_id=approver.id,
        db=db_session,
    )
    assert has_permission is True


def test_owner_has_permission_without_explicit_grant(db_session: Session) -> None:
    """表单创建者无需显式授权即可管理表单。"""

    tenant, owner, form = prepare_form_context(db_session)
    FormPermissionService.ensure_permission(
        form_id=form.id,
        tenant_id=tenant.id,
        permission=PermissionType.MANAGE,
        user_id=owner.id,
        db=db_session,
    )


def test_ensure_permission_denied_for_unauthorized_user(db_session: Session) -> None:
    """未授权用户调用 ensure_permission 应被拒绝。"""

    tenant, owner, form = prepare_form_context(db_session)
    outsider = User(
        tenant_id=tenant.id,
        account="outsider",
        password_hash="hashed",
        name="访问者",
        is_active=True,
    )
    db_session.add(outsider)
    db_session.commit()

    with pytest.raises(AuthorizationError):
        FormPermissionService.ensure_permission(
            form_id=form.id,
            tenant_id=tenant.id,
            permission=PermissionType.VIEW,
            user_id=outsider.id,
            db=db_session,
        )
