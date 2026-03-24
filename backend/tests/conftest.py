"""
pytest 配置和共享 fixture
"""
from typing import Iterator

import pytest
from sqlalchemy import create_engine, event, Column, Integer, String, ForeignKey, DateTime, JSON, Table, MetaData
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from app.core.database import Base
from app.models import category as category_models  # noqa: F401
from app.models import form as form_models  # noqa: F401
from app.models import user as user_models  # noqa: F401
from app.models import workflow as workflow_models  # noqa: F401
from app.models.user import Tenant, User


@pytest.fixture()
def db_session() -> Iterator[Session]:
    """构建独立的 sqlite 会话"""
    engine = create_engine("sqlite:///:memory:", future=True)
    
    # 禁用外键约束以避免 JSONB 问题
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()
    
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    
    # 创建最小化的表结构用于测试
    metadata = MetaData()
    
    # 创建租户表
    tenant_table = Table(
        'tenant',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(255), nullable=False),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
    )
    
    # 创建部门表
    department_table = Table(
        'department',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('tenant_id', Integer, ForeignKey('tenant.id'), nullable=False),
        Column('name', String(100), nullable=False),
        Column('parent_id', Integer, ForeignKey('department.id')),
        Column('type', String(20), nullable=False),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
    )
    
    # 创建用户表
    user_table = Table(
        'user',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('tenant_id', Integer, ForeignKey('tenant.id'), nullable=False),
        Column('account', String(50), nullable=False),
        Column('password_hash', String(255), nullable=False),
        Column('name', String(50), nullable=False),
        Column('email', String(100)),
        Column('phone', String(20)),
        Column('department_id', Integer, ForeignKey('department.id')),
        Column('is_active', Integer, default=1),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
    )
    
    # 创建表单表
    form_table = Table(
        'form',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('tenant_id', Integer, ForeignKey('tenant.id'), nullable=False),
        Column('name', String(255), nullable=False),
        Column('description', String(500)),
        Column('access_mode', String(20), nullable=False),
    )
    
    # 创建表单版本表
    form_version_table = Table(
        'form_version',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('form_id', Integer, ForeignKey('form.id'), nullable=False),
        Column('version', Integer, nullable=False),
        Column('schema_json', JSON),
    )
    
    # 创建提交表
    submission_table = Table(
        'submission',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('tenant_id', Integer, ForeignKey('tenant.id'), nullable=False),
        Column('form_id', Integer, ForeignKey('form.id'), nullable=False),
        Column('form_version_id', Integer, ForeignKey('form_version.id'), nullable=False),
        Column('submitter_user_id', Integer, ForeignKey('user.id'), nullable=True),
        Column('data_jsonb', JSON),
    )
    
    # 创建流程定义表
    flow_definition_table = Table(
        'flow_definition',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('tenant_id', Integer, ForeignKey('tenant.id'), nullable=False),
        Column('form_id', Integer, ForeignKey('form.id'), nullable=False),
        Column('version', Integer, nullable=False),
        Column('definition_json', JSON),
    )
    
    # 创建流程节点表
    flow_node_table = Table(
        'flow_node',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('flow_definition_id', Integer, ForeignKey('flow_definition.id'), nullable=False),
        Column('tenant_id', Integer, ForeignKey('tenant.id'), nullable=False),
        Column('type', String(20), nullable=False),
    )
    
    # 创建流程实例表
    process_instance_table = Table(
        'process_instance',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('tenant_id', Integer, ForeignKey('tenant.id'), nullable=False),
        Column('form_id', Integer, ForeignKey('form.id'), nullable=False),
        Column('form_version_id', Integer, ForeignKey('form_version.id'), nullable=False),
        Column('submission_id', Integer, ForeignKey('submission.id'), nullable=False),
        Column('flow_definition_id', Integer, ForeignKey('flow_definition.id'), nullable=False),
        Column('state', String(20), default='running'),
        Column('form_data_snapshot', JSON),
    )
    
    # 创建操作日志表
    operation_log_table = Table(
        'workflow_operation_log',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('tenant_id', Integer, ForeignKey('tenant.id'), nullable=False),
        Column('process_instance_id', Integer, ForeignKey('process_instance.id'), nullable=False),
        Column('operation_type', String(20), nullable=False),
        Column('operator_id', Integer, ForeignKey('user.id'), nullable=False),
        Column('comment', String(500)),
        Column('detail_json', JSON),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
    )
    
    # 创建所有表
    metadata.create_all(engine)
    
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def tenant_id(db_session: Session) -> int:
    """创建测试租户"""
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.flush()
    return tenant.id


@pytest.fixture()
def user_id(db_session: Session, tenant_id: int) -> int:
    """创建测试用户"""
    user = User(
        tenant_id=tenant_id,
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
    )
    db_session.add(user)
    db_session.flush()
    return user.id



