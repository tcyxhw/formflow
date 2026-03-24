"""
模块用途: 表单分类系统 - 集成测试
依赖配置: sqlite 内存数据库
数据流向: 完整的业务流程 -> 验证端到端功能
函数清单:
    - test_end_to_end_category_creation_workflow(): 端到端分类创建流程
    - test_end_to_end_form_creation_with_category(): 端到端表单创建与分类分配
    - test_end_to_end_form_filtering_by_category(): 端到端表单分类过滤
    - test_end_to_end_category_deletion_with_cascading(): 端到端分类删除与级联处理
    - test_multi_tenant_isolation_across_workflows(): 多租户隔离验证
"""
from __future__ import annotations

from typing import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models import category as category_models  # noqa: F401
from app.models import form as form_models  # noqa: F401
from app.models import user as user_models  # noqa: F401
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


def test_end_to_end_category_creation_workflow(
    db_session: Session,
    prepare_tenant: int
):
    """
    端到端分类创建流程
    
    验证完整的分类创建、查询、更新、删除流程
    
    Validates: Requirements 1.1-1.6
    """
    # Step 1: 创建分类
    cat1 = CategoryService.create_category(prepare_tenant, "HR Forms", db_session)
    cat2 = CategoryService.create_category(prepare_tenant, "Finance Forms", db_session)
    
    assert cat1.id is not None
    assert cat2.id is not None
    
    # Step 2: 查询分类列表
    categories, total = CategoryService.get_categories(prepare_tenant, db=db_session)
    assert total == 2
    assert len(categories) == 2
    
    # Step 3: 获取单个分类
    retrieved = CategoryService.get_category(cat1.id, prepare_tenant, db_session)
    assert retrieved.name == "HR Forms"
    
    # Step 4: 更新分类
    updated = CategoryService.update_category(
        cat1.id,
        prepare_tenant,
        "Human Resources",
        db_session
    )
    assert updated.name == "Human Resources"
    
    # Step 5: 验证更新
    categories, _ = CategoryService.get_categories(prepare_tenant, db=db_session)
    hr_cat = next(c for c in categories if c.id == cat1.id)
    assert hr_cat.name == "Human Resources"


def test_end_to_end_form_creation_with_category(
    db_session: Session,
    prepare_tenant: int
):
    """
    端到端表单创建与分类分配
    
    验证表单创建时的分类分配流程
    
    Validates: Requirements 2.1-2.5
    """
    # Step 1: 初始化默认分类
    default_cat = CategoryService.initialize_default_category(prepare_tenant, db_session)
    
    # Step 2: 创建自定义分类
    custom_cat = CategoryService.create_category(prepare_tenant, "HR Forms", db_session)
    
    # Step 3: 创建表单并分配到自定义分类
    form = Form(
        tenant_id=prepare_tenant,
        name="Employee Onboarding",
        category_id=custom_cat.id,
        owner_user_id=1,
        status="draft"
    )
    db_session.add(form)
    db_session.commit()
    
    # Step 4: 验证表单分类分配
    queried_form = db_session.query(Form).filter(Form.id == form.id).first()
    assert queried_form.category_id == custom_cat.id
    
    # Step 5: 创建表单但不指定分类（应该使用默认分类）
    form2 = Form(
        tenant_id=prepare_tenant,
        name="General Form",
        category_id=default_cat.id,
        owner_user_id=1,
        status="draft"
    )
    db_session.add(form2)
    db_session.commit()
    
    queried_form2 = db_session.query(Form).filter(Form.id == form2.id).first()
    assert queried_form2.category_id == default_cat.id


def test_end_to_end_form_filtering_by_category(
    db_session: Session,
    prepare_tenant: int
):
    """
    端到端表单分类过滤
    
    验证按分类过滤表单的完整流程
    
    Validates: Requirements 3.1-3.5
    """
    # Step 1: 创建分类
    hr_cat = CategoryService.create_category(prepare_tenant, "HR Forms", db_session)
    finance_cat = CategoryService.create_category(prepare_tenant, "Finance Forms", db_session)
    
    # Step 2: 创建表单
    forms_data = [
        ("Employee Onboarding", hr_cat.id),
        ("Leave Request", hr_cat.id),
        ("Expense Report", finance_cat.id),
        ("Budget Request", finance_cat.id),
    ]
    
    for name, category_id in forms_data:
        form = Form(
            tenant_id=prepare_tenant,
            name=name,
            category_id=category_id,
            owner_user_id=1,
            status="draft"
        )
        db_session.add(form)
    db_session.commit()
    
    # Step 3: 按HR分类过滤
    hr_forms = db_session.query(Form).filter(
        Form.tenant_id == prepare_tenant,
        Form.category_id == hr_cat.id
    ).all()
    
    assert len(hr_forms) == 2
    assert all(f.category_id == hr_cat.id for f in hr_forms)
    
    # Step 4: 按Finance分类过滤
    finance_forms = db_session.query(Form).filter(
        Form.tenant_id == prepare_tenant,
        Form.category_id == finance_cat.id
    ).all()
    
    assert len(finance_forms) == 2
    assert all(f.category_id == finance_cat.id for f in finance_forms)
    
    # Step 5: 查询所有表单
    all_forms = db_session.query(Form).filter(
        Form.tenant_id == prepare_tenant
    ).all()
    
    assert len(all_forms) == 4


def test_end_to_end_category_deletion_with_cascading(
    db_session: Session,
    prepare_tenant: int
):
    """
    端到端分类删除与级联处理
    
    验证删除分类时的级联处理流程
    
    Validates: Requirements 1.4, 4.4, 8.3, 8.4
    """
    # Step 1: 初始化默认分类
    default_cat = CategoryService.initialize_default_category(prepare_tenant, db_session)
    
    # Step 2: 创建要删除的分类
    to_delete = CategoryService.create_category(prepare_tenant, "To Delete", db_session)
    
    # Step 3: 创建表单并分配到要删除的分类
    forms_data = []
    for i in range(3):
        form = Form(
            tenant_id=prepare_tenant,
            name=f"Form {i}",
            category_id=to_delete.id,
            owner_user_id=1,
            status="draft"
        )
        db_session.add(form)
        forms_data.append(form)
    db_session.commit()
    
    # Step 4: 验证表单分配到要删除的分类
    forms_before = db_session.query(Form).filter(
        Form.category_id == to_delete.id
    ).all()
    assert len(forms_before) == 3
    
    # Step 5: 删除分类
    CategoryService.delete_category(to_delete.id, prepare_tenant, db_session)
    
    # Step 6: 验证分类已删除
    categories, _ = CategoryService.get_categories(prepare_tenant, db=db_session)
    assert not any(c.id == to_delete.id for c in categories)
    
    # Step 7: 验证表单已重新分配到默认分类
    for form in forms_data:
        db_session.refresh(form)
        assert form.category_id == default_cat.id
    
    # Step 8: 验证无法删除默认分类
    from app.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        CategoryService.delete_category(default_cat.id, prepare_tenant, db_session)


def test_multi_tenant_isolation_across_workflows(db_session: Session):
    """
    多租户隔离验证
    
    验证多租户环境下的完整隔离
    
    Validates: Requirements 7.1-7.4
    """
    # Step 1: 创建两个租户
    tenant1 = Tenant(name="Tenant 1")
    tenant2 = Tenant(name="Tenant 2")
    db_session.add_all([tenant1, tenant2])
    db_session.commit()
    
    # Step 2: 为每个租户创建分类
    cat1_t1 = CategoryService.create_category(tenant1.id, "HR Forms", db_session)
    cat1_t2 = CategoryService.create_category(tenant2.id, "Finance Forms", db_session)
    
    # Step 3: 为每个租户创建表单
    form_t1 = Form(
        tenant_id=tenant1.id,
        name="Form T1",
        category_id=cat1_t1.id,
        owner_user_id=1,
        status="draft"
    )
    form_t2 = Form(
        tenant_id=tenant2.id,
        name="Form T2",
        category_id=cat1_t2.id,
        owner_user_id=1,
        status="draft"
    )
    db_session.add_all([form_t1, form_t2])
    db_session.commit()
    
    # Step 4: 验证租户1只能看到自己的分类
    categories_t1, _ = CategoryService.get_categories(tenant1.id, db=db_session)
    assert len(categories_t1) == 1
    assert categories_t1[0].id == cat1_t1.id
    
    # Step 5: 验证租户2只能看到自己的分类
    categories_t2, _ = CategoryService.get_categories(tenant2.id, db=db_session)
    assert len(categories_t2) == 1
    assert categories_t2[0].id == cat1_t2.id
    
    # Step 6: 验证租户1的表单只能看到自己的分类
    forms_t1 = db_session.query(Form).filter(
        Form.tenant_id == tenant1.id
    ).all()
    assert len(forms_t1) == 1
    assert forms_t1[0].category_id == cat1_t1.id
    
    # Step 7: 验证租户2的表单只能看到自己的分类
    forms_t2 = db_session.query(Form).filter(
        Form.tenant_id == tenant2.id
    ).all()
    assert len(forms_t2) == 1
    assert forms_t2[0].category_id == cat1_t2.id
    
    # Step 8: 验证跨租户访问被拒绝
    from app.core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):
        CategoryService.get_category(cat1_t1.id, tenant2.id, db_session)
    
    with pytest.raises(NotFoundError):
        CategoryService.get_category(cat1_t2.id, tenant1.id, db_session)
