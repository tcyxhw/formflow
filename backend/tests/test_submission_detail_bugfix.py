"""
Bug Condition 探索测试 - 提交详情显示修复

**Validates: Requirements 1.1**

此测试验证修复后的正确行为：
后端正确使用 form.category_id 而非 form.category 返回分类名称。
"""

from __future__ import annotations

from typing import Iterator
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.form import Form
from app.models.user import Tenant, User
from app.models.category import Category
from app.models.user_quick_access import UserQuickAccess
from app.services.form_workspace_service import FormWorkspaceService
from app.schemas.workspace_schemas import FillableFormsQuery


@pytest.fixture()
def db_session() -> Iterator[Session]:
    """构建独立的 sqlite 会话"""
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    
    # 创建所需的表
    Tenant.__table__.create(engine, checkfirst=True)
    User.__table__.create(engine, checkfirst=True)
    Category.__table__.create(engine, checkfirst=True)
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
        Category.__table__.drop(engine, checkfirst=True)
        User.__table__.drop(engine, checkfirst=True)
        Tenant.__table__.drop(engine, checkfirst=True)


class TestBackendCategoryAccessFixed:
    """
    Property 1: Expected Behavior - 后端正确访问分类 ID
    
    测试后端在获取可填写表单列表时正确使用 form.category_id
    返回分类名称而非抛出 AttributeError。
    """

    def test_get_fillable_forms_returns_category_name(
        self, db_session: Session
    ):
        """
        测试 get_fillable_forms 方法正确返回分类名称
        
        修复后，代码使用 category_id 查询分类并返回名称。
        """
        # 创建测试租户
        tenant = Tenant(name="测试学校")
        db_session.add(tenant)
        db_session.flush()

        # 创建测试用户
        user = User(
            tenant_id=tenant.id,
            account="testuser",
            password_hash="hashed",
            name="测试用户",
            email="test@example.com",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        # 创建测试分类
        category = Category(
            tenant_id=tenant.id,
            name="测试分类"
        )
        db_session.add(category)
        db_session.flush()

        # 创建测试表单
        form = Form(
            tenant_id=tenant.id,
            name="测试表单",
            category_id=category.id,
            owner_user_id=user.id,
            status="published",
            access_mode="authenticated",
            submit_deadline=datetime.now() + timedelta(days=7)
        )
        db_session.add(form)
        db_session.commit()
        db_session.refresh(form)

        # 构建查询参数
        query = FillableFormsQuery(
            page=1,
            page_size=10,
            sort_by="created_at",
            sort_order="desc"
        )

        # 验证修复后可以正常获取可填写表单列表
        result = FormWorkspaceService.get_fillable_forms(
            user_id=user.id,
            tenant_id=tenant.id,
            query=query,
            db=db_session
        )
        
        # 验证返回结果包含分类名称
        assert result.total > 0
        assert len(result.items) > 0
        assert result.items[0].category == "测试分类"

    def test_get_quick_access_forms_returns_category_name(
        self, db_session: Session
    ):
        """
        测试 get_quick_access_forms 方法正确返回分类名称
        
        修复后，代码使用 category_id 查询分类并返回名称。
        """
        # 创建测试租户
        tenant = Tenant(name="测试学校")
        db_session.add(tenant)
        db_session.flush()

        # 创建测试用户
        user = User(
            tenant_id=tenant.id,
            account="testuser",
            password_hash="hashed",
            name="测试用户",
            email="test@example.com",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        # 创建测试分类
        category = Category(
            tenant_id=tenant.id,
            name="快速访问分类"
        )
        db_session.add(category)
        db_session.flush()

        # 创建测试表单
        form = Form(
            tenant_id=tenant.id,
            name="快速访问表单",
            category_id=category.id,
            owner_user_id=user.id,
            status="published",
            access_mode="authenticated"
        )
        db_session.add(form)
        db_session.flush()

        # 添加到快速访问
        quick_access = UserQuickAccess(
            tenant_id=tenant.id,
            user_id=user.id,
            form_id=form.id,
            sort_order=0
        )
        db_session.add(quick_access)
        db_session.commit()

        # 验证修复后可以正常获取快速访问表单列表
        result = FormWorkspaceService.get_quick_access_forms(
            user_id=user.id,
            tenant_id=tenant.id,
            db=db_session
        )
        
        # 验证返回结果包含分类名称
        assert len(result.items) > 0
        assert result.items[0].category == "快速访问分类"

    def test_apply_category_filter_uses_category_id(
        self, db_session: Session
    ):
        """
        测试 _apply_category_filter 方法正确使用 category_id 进行过滤
        
        修复后，代码使用 form.category_id 进行过滤。
        """
        # 创建测试租户
        tenant = Tenant(name="测试学校")
        db_session.add(tenant)
        db_session.flush()

        # 创建测试用户
        user = User(
            tenant_id=tenant.id,
            account="testuser",
            password_hash="hashed",
            name="测试用户",
            email="test@example.com",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        # 创建测试分类
        category = Category(
            tenant_id=tenant.id,
            name="过滤测试分类"
        )
        db_session.add(category)
        db_session.flush()

        # 创建测试表单
        form = Form(
            tenant_id=tenant.id,
            name="过滤测试表单",
            category_id=category.id,
            owner_user_id=user.id,
            status="published",
            access_mode="authenticated"
        )
        db_session.add(form)
        db_session.commit()
        db_session.refresh(form)

        # 验证修复后可以正常应用分类过滤
        result = FormWorkspaceService._apply_category_filter(
            forms=[form],
            category="过滤测试分类"
        )
        
        # 验证��滤结果正确
        assert len(result) == 1
        assert result[0].id == form.id