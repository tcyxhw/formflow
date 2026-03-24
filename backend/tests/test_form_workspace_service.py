"""
模块用途: FormWorkspaceService 快捷入口功能单元测试
依赖配置: sqlite 内存数据库
数据流向: sqlite -> SQLAlchemy Session -> Service 调用 -> 断言
函数清单:
    - db_session(): 提供测试数据库会话
    - prepare_test_context(): 构造基础数据（租户、用户、表单）
    - test_add_quick_access(): 测试添加快捷入口
    - test_add_quick_access_idempotent(): 测试重复添加的幂等性
    - test_remove_quick_access(): 测试移除快捷入口
    - test_remove_nonexistent_quick_access(): 测试移除不存在的快捷入口
    - test_get_quick_access_forms(): 测试获取快捷入口列表
    - test_quick_access_sorting(): 测试快捷入口排序逻辑
"""
from __future__ import annotations

from typing import Iterator, Tuple

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models.form import Form
from app.models.user import Tenant, User
from app.models.user_quick_access import UserQuickAccess
from app.services.form_workspace_service import FormWorkspaceService


@pytest.fixture()
def db_session() -> Iterator[Session]:
    """构建独立的 sqlite 会话。

    Time: O(1), Space: O(1)
    """
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    
    # 只创建我们需要的表，避免 JSONB 类型问题
    Tenant.__table__.create(engine, checkfirst=True)
    User.__table__.create(engine, checkfirst=True)
    Form.__table__.create(engine, checkfirst=True)
    UserQuickAccess.__table__.create(engine, checkfirst=True)
    
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        # 清理表
        UserQuickAccess.__table__.drop(engine, checkfirst=True)
        Form.__table__.drop(engine, checkfirst=True)
        User.__table__.drop(engine, checkfirst=True)
        Tenant.__table__.drop(engine, checkfirst=True)


def prepare_test_context(db: Session) -> Tuple[Tenant, User, Form, Form]:
    """初始化租户、用户与表单。

    Time: O(1), Space: O(1)
    """
    tenant = Tenant(name="测试学校")
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        account="testuser",
        password_hash="hashed",
        name="测试用户",
        email="test@example.com",
        is_active=True,
    )
    db.add(user)
    db.flush()

    form1 = Form(
        tenant_id=tenant.id,
        name="表单1",
        access_mode="authenticated",
        owner_user_id=user.id,
        status="published",
        allow_edit=True,
        max_edit_count=1,
    )
    form2 = Form(
        tenant_id=tenant.id,
        name="表单2",
        access_mode="authenticated",
        owner_user_id=user.id,
        status="published",
        allow_edit=True,
        max_edit_count=1,
    )
    db.add(form1)
    db.add(form2)
    db.commit()
    db.refresh(form1)
    db.refresh(form2)
    return tenant, user, form1, form2


def test_add_quick_access(db_session: Session) -> None:
    """验证添加快捷入口功能。"""
    tenant, user, form1, form2 = prepare_test_context(db_session)

    # 添加第一个快捷入口
    quick_access = FormWorkspaceService.add_quick_access(
        user_id=user.id,
        tenant_id=tenant.id,
        form_id=form1.id,
        db=db_session,
    )

    assert quick_access.id is not None
    assert quick_access.user_id == user.id
    assert quick_access.form_id == form1.id
    assert quick_access.sort_order == 0


def test_add_quick_access_idempotent(db_session: Session) -> None:
    """验证重复添加快捷入口的幂等性。"""
    tenant, user, form1, form2 = prepare_test_context(db_session)

    # 第一次添加
    first_add = FormWorkspaceService.add_quick_access(
        user_id=user.id,
        tenant_id=tenant.id,
        form_id=form1.id,
        db=db_session,
    )

    # 第二次添加同一个表单
    second_add = FormWorkspaceService.add_quick_access(
        user_id=user.id,
        tenant_id=tenant.id,
        form_id=form1.id,
        db=db_session,
    )

    # 应该返回同一个记录
    assert first_add.id == second_add.id
    assert first_add.sort_order == second_add.sort_order

    # 验证数据库中只有一条记录
    count = (
        db_session.query(UserQuickAccess)
        .filter(
            UserQuickAccess.user_id == user.id,
            UserQuickAccess.form_id == form1.id,
        )
        .count()
    )
    assert count == 1


def test_remove_quick_access(db_session: Session) -> None:
    """验证移除快捷入口功能。"""
    tenant, user, form1, form2 = prepare_test_context(db_session)

    # 先添加快捷入口
    FormWorkspaceService.add_quick_access(
        user_id=user.id,
        tenant_id=tenant.id,
        form_id=form1.id,
        db=db_session,
    )

    # 移除快捷入口
    result = FormWorkspaceService.remove_quick_access(
        user_id=user.id,
        tenant_id=tenant.id,
        form_id=form1.id,
        db=db_session,
    )

    assert result is True

    # 验证数据库中已删除
    count = (
        db_session.query(UserQuickAccess)
        .filter(
            UserQuickAccess.user_id == user.id,
            UserQuickAccess.form_id == form1.id,
        )
        .count()
    )
    assert count == 0


def test_remove_nonexistent_quick_access(db_session: Session) -> None:
    """验证移除不存在的快捷入口返回False。"""
    tenant, user, form1, form2 = prepare_test_context(db_session)

    # 移除不存在的快捷入口
    result = FormWorkspaceService.remove_quick_access(
        user_id=user.id,
        tenant_id=tenant.id,
        form_id=form1.id,
        db=db_session,
    )

    assert result is False


def test_get_quick_access_forms(db_session: Session) -> None:
    """验证获取快捷入口列表功能。"""
    tenant, user, form1, form2 = prepare_test_context(db_session)

    # 添加两个快捷入口
    FormWorkspaceService.add_quick_access(
        user_id=user.id,
        tenant_id=tenant.id,
        form_id=form1.id,
        db=db_session,
    )
    FormWorkspaceService.add_quick_access(
        user_id=user.id,
        tenant_id=tenant.id,
        form_id=form2.id,
        db=db_session,
    )

    # 获取快捷入口列表
    response = FormWorkspaceService.get_quick_access_forms(
        user_id=user.id,
        tenant_id=tenant.id,
        db=db_session,
    )

    assert len(response.items) == 2
    assert response.items[0].id == form1.id
    assert response.items[1].id == form2.id


def test_quick_access_sorting(db_session: Session) -> None:
    """验证快捷入口排序逻辑。"""
    tenant, user, form1, form2 = prepare_test_context(db_session)

    # 添加第一个快捷入口
    qa1 = FormWorkspaceService.add_quick_access(
        user_id=user.id,
        tenant_id=tenant.id,
        form_id=form1.id,
        db=db_session,
    )

    # 添加第二个快捷入口
    qa2 = FormWorkspaceService.add_quick_access(
        user_id=user.id,
        tenant_id=tenant.id,
        form_id=form2.id,
        db=db_session,
    )

    # 验证排序顺序递增
    assert qa1.sort_order == 0
    assert qa2.sort_order == 1

    # 获取列表，验证按排序顺序返回
    response = FormWorkspaceService.get_quick_access_forms(
        user_id=user.id,
        tenant_id=tenant.id,
        db=db_session,
    )

    assert response.items[0].id == form1.id
    assert response.items[1].id == form2.id
