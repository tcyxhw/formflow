"""
模块用途: CategoryService 单元测试
依赖配置: sqlite 内存数据库
数据流向: sqlite -> SQLAlchemy Session -> Service 调用 -> 断言
函数清单:
    - db_session(): 提供测试数据库会话
    - prepare_tenant(): 构造租户数据
    - test_create_category(): 测试创建分类
    - test_create_category_with_invalid_name(): 测试名称验证
    - test_create_duplicate_category(): 测试重复分类检查
    - test_get_categories(): 测试获取分类列表
    - test_update_category(): 测试更新分类
    - test_delete_category_with_cascading(): 测试删除分类及级联处理
    - test_prevent_delete_default_category(): 测试防止删除默认分类
    - test_initialize_default_category(): 测试初始化默认分类
"""
from __future__ import annotations

from typing import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.core.exceptions import ValidationError, ConflictError, NotFoundError
from app.models import category as category_models  # noqa: F401
from app.models import form as form_models  # noqa: F401
from app.models import user as user_models  # noqa: F401
from app.models.category import Category
from app.models.form import Form
from app.models.user import Tenant
from app.services.category_service import CategoryService


@pytest.fixture()
def db_session() -> Iterator[Session]:
    """构建独立的 sqlite 会话"""
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def prepare_tenant(db_session: Session) -> int:
    """构造租户数据"""
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()
    return tenant.id


def test_create_category(db_session: Session, prepare_tenant: int):
    """测试创建分类"""
    category = CategoryService.create_category(
        tenant_id=prepare_tenant,
        name="HR Forms",
        db=db_session
    )
    
    assert category.id is not None
    assert category.name == "HR Forms"
    assert category.tenant_id == prepare_tenant
    assert category.is_default is False


def test_create_category_with_empty_name(db_session: Session, prepare_tenant: int):
    """测试创建分类时名称为空"""
    with pytest.raises(ValidationError):
        CategoryService.create_category(
            tenant_id=prepare_tenant,
            name="",
            db=db_session
        )


def test_create_category_with_long_name(db_session: Session, prepare_tenant: int):
    """测试创建分类时名称过长"""
    with pytest.raises(ValidationError):
        CategoryService.create_category(
            tenant_id=prepare_tenant,
            name="A" * 51,
            db=db_session
        )


def test_create_duplicate_category(db_session: Session, prepare_tenant: int):
    """测试创建重复分类"""
    CategoryService.create_category(
        tenant_id=prepare_tenant,
        name="HR Forms",
        db=db_session
    )
    
    with pytest.raises(ConflictError):
        CategoryService.create_category(
            tenant_id=prepare_tenant,
            name="HR Forms",
            db=db_session
        )


def test_get_categories(db_session: Session, prepare_tenant: int):
    """测试获取分类列表"""
    # 创建多个分类
    CategoryService.create_category(prepare_tenant, "HR Forms", db_session)
    CategoryService.create_category(prepare_tenant, "Finance Forms", db_session)
    
    categories, total = CategoryService.get_categories(
        tenant_id=prepare_tenant,
        page=1,
        page_size=20,
        db=db_session
    )
    
    assert total == 2
    assert len(categories) == 2


def test_get_category(db_session: Session, prepare_tenant: int):
    """测试获取单个分类"""
    created = CategoryService.create_category(
        tenant_id=prepare_tenant,
        name="HR Forms",
        db=db_session
    )
    
    category = CategoryService.get_category(
        category_id=created.id,
        tenant_id=prepare_tenant,
        db=db_session
    )
    
    assert category.id == created.id
    assert category.name == "HR Forms"


def test_get_category_not_found(db_session: Session, prepare_tenant: int):
    """测试获取不存在的分类"""
    with pytest.raises(NotFoundError):
        CategoryService.get_category(
            category_id=999,
            tenant_id=prepare_tenant,
            db=db_session
        )


def test_update_category(db_session: Session, prepare_tenant: int):
    """测试更新分类"""
    created = CategoryService.create_category(
        tenant_id=prepare_tenant,
        name="HR Forms",
        db=db_session
    )
    
    updated = CategoryService.update_category(
        category_id=created.id,
        tenant_id=prepare_tenant,
        name="Human Resources",
        db=db_session
    )
    
    assert updated.name == "Human Resources"


def test_update_category_with_duplicate_name(db_session: Session, prepare_tenant: int):
    """测试更新分类为已存在的名称"""
    cat1 = CategoryService.create_category(prepare_tenant, "HR Forms", db_session)
    CategoryService.create_category(prepare_tenant, "Finance Forms", db_session)
    
    with pytest.raises(ConflictError):
        CategoryService.update_category(
            category_id=cat1.id,
            tenant_id=prepare_tenant,
            name="Finance Forms",
            db=db_session
        )


def test_delete_category_with_cascading(db_session: Session, prepare_tenant: int):
    """测试删除分类及级联处理"""
    # 创建默认分类
    default_cat = CategoryService.initialize_default_category(prepare_tenant, db_session)
    
    # 创建要删除的分类
    to_delete = CategoryService.create_category(prepare_tenant, "HR Forms", db_session)
    
    # 创建表单并分配到要删除的分类
    form = Form(
        tenant_id=prepare_tenant,
        name="Test Form",
        category_id=to_delete.id,
        owner_user_id=1,
        status="draft"
    )
    db_session.add(form)
    db_session.commit()
    
    # 删除分类
    CategoryService.delete_category(to_delete.id, prepare_tenant, db_session)
    
    # 验证分类已删除
    with pytest.raises(NotFoundError):
        CategoryService.get_category(to_delete.id, prepare_tenant, db_session)
    
    # 验证表单已重新分配到默认分类
    db_session.refresh(form)
    assert form.category_id == default_cat.id


def test_prevent_delete_default_category(db_session: Session, prepare_tenant: int):
    """测试防止删除默认分类"""
    default_cat = CategoryService.initialize_default_category(prepare_tenant, db_session)
    
    with pytest.raises(ValidationError):
        CategoryService.delete_category(default_cat.id, prepare_tenant, db_session)


def test_initialize_default_category(db_session: Session, prepare_tenant: int):
    """测试初始化默认分类"""
    category = CategoryService.initialize_default_category(prepare_tenant, db_session)
    
    assert category.name == "Uncategorized"
    assert category.is_default is True
    assert category.tenant_id == prepare_tenant


def test_initialize_default_category_idempotent(db_session: Session, prepare_tenant: int):
    """测试初始化默认分类的幂等性"""
    cat1 = CategoryService.initialize_default_category(prepare_tenant, db_session)
    cat2 = CategoryService.initialize_default_category(prepare_tenant, db_session)
    
    assert cat1.id == cat2.id


def test_get_default_category(db_session: Session, prepare_tenant: int):
    """测试获取默认分类"""
    created = CategoryService.initialize_default_category(prepare_tenant, db_session)
    
    default = CategoryService.get_default_category(prepare_tenant, db_session)
    
    assert default is not None
    assert default.id == created.id
    assert default.is_default is True


def test_multi_tenant_isolation(db_session: Session):
    """测试多租户隔离"""
    # 创建两个租户
    tenant1 = Tenant(name="Tenant 1")
    tenant2 = Tenant(name="Tenant 2")
    db_session.add_all([tenant1, tenant2])
    db_session.commit()
    
    # 为每个租户创建分类
    cat1 = CategoryService.create_category(tenant1.id, "HR Forms", db_session)
    cat2 = CategoryService.create_category(tenant2.id, "Finance Forms", db_session)
    
    # 验证租户1只能看到自己的分类
    categories1, _ = CategoryService.get_categories(tenant1.id, db=db_session)
    assert len(categories1) == 1
    assert categories1[0].id == cat1.id
    
    # 验证租户2只能看到自己的分类
    categories2, _ = CategoryService.get_categories(tenant2.id, db=db_session)
    assert len(categories2) == 1
    assert categories2[0].id == cat2.id
    
    # 验证跨租户访问被拒绝
    with pytest.raises(NotFoundError):
        CategoryService.get_category(cat1.id, tenant2.id, db_session)
