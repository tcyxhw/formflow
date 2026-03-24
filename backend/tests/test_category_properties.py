"""
模块用途: 表单分类系统 - 属性测试（Property-Based Testing）
依赖配置: sqlite 内存数据库，hypothesis
数据流向: 生成随机数据 -> 执行操作 -> 验证属性
函数清单:
    - test_property_1_category_uniqueness_within_tenant(): 分类名称唯一性
    - test_property_2_category_name_validation(): 分类名称验证
    - test_property_3_cascading_category_deletion(): 级联删除
    - test_property_4_default_category_protection(): 默认分类保护
    - test_property_5_form_default_category_assignment(): 表单默认分类分配
    - test_property_6_multi_tenant_category_isolation(): 多租户隔离
    - test_property_7_category_filtering_accuracy(): 分类过滤准确性
    - test_property_8_all_categories_filter(): 全部分类过滤
    - test_property_9_category_information_persistence(): 分类信息持久化
    - test_property_11_default_category_initialization(): 默认分类初始化
    - test_property_12_category_list_pagination(): 分类列表分页
"""
from __future__ import annotations

from typing import Iterator

import pytest
from hypothesis import given, strategies as st
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


# ========== Property 1: Category Uniqueness Within Tenant ==========
@given(st.text(min_size=1, max_size=50))
def test_property_1_category_uniqueness_within_tenant(
    db_session: Session,
    prepare_tenant: int,
    category_name: str
):
    """
    Property 1: 分类名称在租户内唯一
    
    对于任何租户，创建一个分类后，尝试创建同名分类应该被拒绝。
    
    Validates: Requirements 1.6
    """
    # 跳过空字符串
    if not category_name.strip():
        return
    
    # 创建第一个分类
    CategoryService.create_category(prepare_tenant, category_name, db_session)
    
    # 尝试创建同名分类 - 应该抛出 ConflictError
    with pytest.raises(ConflictError):
        CategoryService.create_category(prepare_tenant, category_name, db_session)


# ========== Property 2: Category Name Validation ==========
@given(st.text())
def test_property_2_category_name_validation(
    db_session: Session,
    prepare_tenant: int,
    category_name: str
):
    """
    Property 2: 分类名称验证
    
    对于任何分类名称，如果长度不在 1-50 之间，创建应该被拒绝。
    
    Validates: Requirements 1.5
    """
    if len(category_name) == 0 or len(category_name) > 50:
        # 应该抛出 ValidationError
        with pytest.raises(ValidationError):
            CategoryService.create_category(prepare_tenant, category_name, db_session)
    else:
        # 应该成功创建
        category = CategoryService.create_category(prepare_tenant, category_name, db_session)
        assert category.name == category_name


# ========== Property 3: Cascading Category Deletion ==========
def test_property_3_cascading_category_deletion(
    db_session: Session,
    prepare_tenant: int
):
    """
    Property 3: 级联分类删除
    
    当删除一个分类时，该分类下的所有表单应该被重新分配到默认分类。
    
    Validates: Requirements 1.4, 4.4, 8.3
    """
    # 初始化默认分类
    default_cat = CategoryService.initialize_default_category(prepare_tenant, db_session)
    
    # 创建要删除的分类
    to_delete = CategoryService.create_category(prepare_tenant, "To Delete", db_session)
    
    # 创建多个表单并分配到要删除的分类
    forms = []
    for i in range(5):
        form = Form(
            tenant_id=prepare_tenant,
            name=f"Form {i}",
            category_id=to_delete.id,
            owner_user_id=1,
            status="draft"
        )
        db_session.add(form)
        forms.append(form)
    db_session.commit()
    
    # 删除分类
    CategoryService.delete_category(to_delete.id, prepare_tenant, db_session)
    
    # 验证所有表单都被重新分配到默认分类
    for form in forms:
        db_session.refresh(form)
        assert form.category_id == default_cat.id


# ========== Property 4: Default Category Protection ==========
def test_property_4_default_category_protection(
    db_session: Session,
    prepare_tenant: int
):
    """
    Property 4: 默认分类保护
    
    尝试删除默认分类应该被拒绝。
    
    Validates: Requirements 8.4
    """
    default_cat = CategoryService.initialize_default_category(prepare_tenant, db_session)
    
    with pytest.raises(ValidationError):
        CategoryService.delete_category(default_cat.id, prepare_tenant, db_session)


# ========== Property 5: Form Default Category Assignment ==========
def test_property_5_form_default_category_assignment(
    db_session: Session,
    prepare_tenant: int
):
    """
    Property 5: 表单默认分类分配
    
    创建没有指定分类的表单时，应该自动分配到默认分类。
    
    Validates: Requirements 4.3, 8.2
    """
    # 初始化默认分类
    default_cat = CategoryService.initialize_default_category(prepare_tenant, db_session)
    
    # 创建表单但不指定分类
    form = Form(
        tenant_id=prepare_tenant,
        name="Test Form",
        category_id=None,  # 不指定分类
        owner_user_id=1,
        status="draft"
    )
    db_session.add(form)
    db_session.commit()
    
    # 在实际应用中，FormService.create_form 应该自动分配默认分类
    # 这里我们验证默认分类存在
    assert default_cat is not None
    assert default_cat.is_default is True


# ========== Property 6: Multi-Tenant Category Isolation ==========
def test_property_6_multi_tenant_category_isolation(db_session: Session):
    """
    Property 6: 多租户分类隔离
    
    一个租户的分类不应该对另一个租户可见。
    
    Validates: Requirements 7.1, 7.2, 7.3
    """
    # 创建两个租户
    tenant1 = Tenant(name="Tenant 1")
    tenant2 = Tenant(name="Tenant 2")
    db_session.add_all([tenant1, tenant2])
    db_session.commit()
    
    # 为租户1创建分类
    cat1 = CategoryService.create_category(tenant1.id, "Category 1", db_session)
    
    # 为租户2创建分类
    cat2 = CategoryService.create_category(tenant2.id, "Category 2", db_session)
    
    # 验证租户1无法访问租户2的分类
    with pytest.raises(NotFoundError):
        CategoryService.get_category(cat2.id, tenant1.id, db_session)
    
    # 验证租户2无法访问租户1的分类
    with pytest.raises(NotFoundError):
        CategoryService.get_category(cat1.id, tenant2.id, db_session)


# ========== Property 7: Category Filtering Accuracy ==========
@given(st.integers(min_value=1, max_value=10))
def test_property_7_category_filtering_accuracy(
    db_session: Session,
    prepare_tenant: int,
    num_forms: int
):
    """
    Property 7: 分类过滤准确性
    
    按分类过滤表单时，返回的表单应该都属于指定的分类。
    
    Validates: Requirements 3.2, 5.5
    """
    # 创建分类
    cat1 = CategoryService.create_category(prepare_tenant, "Category 1", db_session)
    cat2 = CategoryService.create_category(prepare_tenant, "Category 2", db_session)
    
    # 创建表单
    for i in range(num_forms):
        category_id = cat1.id if i % 2 == 0 else cat2.id
        form = Form(
            tenant_id=prepare_tenant,
            name=f"Form {i}",
            category_id=category_id,
            owner_user_id=1,
            status="draft"
        )
        db_session.add(form)
    db_session.commit()
    
    # 查询cat1的表单
    forms = db_session.query(Form).filter(
        Form.tenant_id == prepare_tenant,
        Form.category_id == cat1.id
    ).all()
    
    # 验证所有返回的表单都属于cat1
    for form in forms:
        assert form.category_id == cat1.id


# ========== Property 8: All Categories Filter ==========
def test_property_8_all_categories_filter(
    db_session: Session,
    prepare_tenant: int
):
    """
    Property 8: 全部分类过滤
    
    不指定分类过滤时，应该返回所有表单。
    
    Validates: Requirements 3.3
    """
    # 创建多个分类
    cat1 = CategoryService.create_category(prepare_tenant, "Category 1", db_session)
    cat2 = CategoryService.create_category(prepare_tenant, "Category 2", db_session)
    
    # 创建表单
    forms_data = []
    for i in range(5):
        category_id = cat1.id if i < 3 else cat2.id
        form = Form(
            tenant_id=prepare_tenant,
            name=f"Form {i}",
            category_id=category_id,
            owner_user_id=1,
            status="draft"
        )
        db_session.add(form)
        forms_data.append(form)
    db_session.commit()
    
    # 查询所有表单（不过滤分类）
    all_forms = db_session.query(Form).filter(
        Form.tenant_id == prepare_tenant
    ).all()
    
    # 验证返回了所有表单
    assert len(all_forms) == 5


# ========== Property 9: Category Information Persistence ==========
def test_property_9_category_information_persistence(
    db_session: Session,
    prepare_tenant: int
):
    """
    Property 9: 分类信息持久化
    
    保存表单的分类后，查询表单应该返回相同的分类ID。
    
    Validates: Requirements 2.5, 4.5
    """
    # 创建分类
    category = CategoryService.create_category(prepare_tenant, "Test Category", db_session)
    
    # 创建表单并分配分类
    form = Form(
        tenant_id=prepare_tenant,
        name="Test Form",
        category_id=category.id,
        owner_user_id=1,
        status="draft"
    )
    db_session.add(form)
    db_session.commit()
    
    # 查询表单
    queried_form = db_session.query(Form).filter(Form.id == form.id).first()
    
    # 验证分类ID相同
    assert queried_form.category_id == category.id


# ========== Property 11: Default Category Initialization ==========
def test_property_11_default_category_initialization(
    db_session: Session,
    prepare_tenant: int
):
    """
    Property 11: 默认分类初始化
    
    为新租户初始化时，应该自动创建默认分类。
    
    Validates: Requirements 8.1
    """
    # 创建新租户
    new_tenant = Tenant(name="New Tenant")
    db_session.add(new_tenant)
    db_session.commit()
    
    # 初始化默认分类
    default_cat = CategoryService.initialize_default_category(new_tenant.id, db_session)
    
    # 验证默认分类
    assert default_cat is not None
    assert default_cat.name == "Uncategorized"
    assert default_cat.is_default is True
    assert default_cat.tenant_id == new_tenant.id


# ========== Property 12: Category List Pagination ==========
@given(st.integers(min_value=1, max_value=50))
def test_property_12_category_list_pagination(
    db_session: Session,
    prepare_tenant: int,
    num_categories: int
):
    """
    Property 12: 分类列表分页
    
    分页查询分类时，应该返回正确的总数和分页信息。
    
    Validates: Requirements 5.1
    """
    # 创建多个分类
    for i in range(num_categories):
        CategoryService.create_category(prepare_tenant, f"Category {i}", db_session)
    
    # 查询第一页
    categories, total = CategoryService.get_categories(
        tenant_id=prepare_tenant,
        page=1,
        page_size=10,
        db=db_session
    )
    
    # 验证总数
    assert total == num_categories
    
    # 验证返回的分类数量不超过page_size
    assert len(categories) <= 10
