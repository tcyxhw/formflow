"""
测试 WorkflowOperationLogService 服务类 - 简化版本
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, event, Column, Integer, String, DateTime, JSON, ForeignKey, Table, MetaData

from app.services.workflow_operation_log_service import WorkflowOperationLogService
from app.core.exceptions import NotFoundError


@pytest.fixture()
def simple_db_session():
    """创建简化的测试数据库会话"""
    engine = create_engine("sqlite:///:memory:", future=True)
    
    # 禁用外键约束
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()
    
    from sqlalchemy.orm import sessionmaker
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    
    # 创建最小化的表结构
    metadata = MetaData()
    
    # 创建租户表
    Table(
        'tenant',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(255), nullable=False),
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
    )
    
    # 创建部门表
    Table(
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
    Table(
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
    
    # 创建流程实例表
    Table(
        'process_instance',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('tenant_id', Integer, ForeignKey('tenant.id'), nullable=False),
        Column('state', String(20), default='running'),
    )
    
    # 创建操作日志表
    Table(
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


class TestWorkflowOperationLogServiceSimple:
    """WorkflowOperationLogService 简化测试类"""

    def test_create_log(self, simple_db_session: Session):
        """测试创建操作日志"""
        # 创建测试数据
        from app.models.user import Tenant, User
        from app.models.workflow import ProcessInstance
        
        tenant = Tenant(name="Test Tenant")
        simple_db_session.add(tenant)
        simple_db_session.flush()
        
        user = User(
            tenant_id=tenant.id,
            account="testuser",
            password_hash="hash",
            name="Test User",
        )
        simple_db_session.add(user)
        simple_db_session.flush()
        
        process = ProcessInstance(
            tenant_id=tenant.id,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
        )
        simple_db_session.add(process)
        simple_db_session.flush()

        # 创建日志
        log = WorkflowOperationLogService.create_log(
            tenant_id=tenant.id,
            process_instance_id=process.id,
            operation_type="SUBMIT",
            operator_id=user.id,
            comment="Test comment",
            detail_json={"key": "value"},
            db=simple_db_session,
        )

        assert log.id is not None
        assert log.tenant_id == tenant.id
        assert log.process_instance_id == process.id
        assert log.operation_type == "SUBMIT"
        assert log.operator_id == user.id
        assert log.comment == "Test comment"
        assert log.detail_json == {"key": "value"}

    def test_create_log_without_db(self):
        """测试创建日志时没有数据库会话"""
        with pytest.raises(ValueError, match="数据库会话不能为空"):
            WorkflowOperationLogService.create_log(
                tenant_id=1,
                process_instance_id=1,
                operation_type="SUBMIT",
                operator_id=1,
                db=None,
            )

    def test_get_process_logs(self, simple_db_session: Session):
        """测试获取流程的操作日志"""
        from app.models.user import Tenant, User
        from app.models.workflow import ProcessInstance
        
        tenant = Tenant(name="Test Tenant")
        simple_db_session.add(tenant)
        simple_db_session.flush()
        
        user = User(
            tenant_id=tenant.id,
            account="testuser",
            password_hash="hash",
            name="Test User",
        )
        simple_db_session.add(user)
        simple_db_session.flush()
        
        process = ProcessInstance(
            tenant_id=tenant.id,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
        )
        simple_db_session.add(process)
        simple_db_session.flush()

        # 创建多条日志
        for i in range(5):
            WorkflowOperationLogService.create_log(
                tenant_id=tenant.id,
                process_instance_id=process.id,
                operation_type="APPROVE" if i % 2 == 0 else "REJECT",
                operator_id=user.id,
                comment=f"Comment {i}",
                db=simple_db_session,
            )

        simple_db_session.commit()

        # 获取日志
        logs, total = WorkflowOperationLogService.get_process_logs(
            process_instance_id=process.id,
            tenant_id=tenant.id,
            db=simple_db_session,
            page=1,
            page_size=10,
        )

        assert total == 5
        assert len(logs) == 5

    def test_get_operation_timeline(self, simple_db_session: Session):
        """测试获取操作时间线"""
        from app.models.user import Tenant, User
        from app.models.workflow import ProcessInstance
        
        tenant = Tenant(name="Test Tenant")
        simple_db_session.add(tenant)
        simple_db_session.flush()
        
        user = User(
            tenant_id=tenant.id,
            account="testuser",
            password_hash="hash",
            name="Test User",
        )
        simple_db_session.add(user)
        simple_db_session.flush()
        
        process = ProcessInstance(
            tenant_id=tenant.id,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
        )
        simple_db_session.add(process)
        simple_db_session.flush()

        # 创建多条日志
        for i in range(3):
            WorkflowOperationLogService.create_log(
                tenant_id=tenant.id,
                process_instance_id=process.id,
                operation_type="APPROVE",
                operator_id=user.id,
                comment=f"Comment {i}",
                detail_json={"index": i},
                db=simple_db_session,
            )

        simple_db_session.commit()

        # 获取时间线
        timeline = WorkflowOperationLogService.get_operation_timeline(
            process_instance_id=process.id,
            tenant_id=tenant.id,
            db=simple_db_session,
        )

        assert len(timeline) == 3
        # 验证时间线包含所有必要字段
        for entry in timeline:
            assert "id" in entry
            assert "operation_type" in entry
            assert "operator_id" in entry
            assert "comment" in entry
            assert "detail_json" in entry
            assert "created_at" in entry

    def test_get_log_by_id(self, simple_db_session: Session):
        """测试获取日志详情"""
        from app.models.user import Tenant, User
        from app.models.workflow import ProcessInstance
        
        tenant = Tenant(name="Test Tenant")
        simple_db_session.add(tenant)
        simple_db_session.flush()
        
        user = User(
            tenant_id=tenant.id,
            account="testuser",
            password_hash="hash",
            name="Test User",
        )
        simple_db_session.add(user)
        simple_db_session.flush()
        
        process = ProcessInstance(
            tenant_id=tenant.id,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
        )
        simple_db_session.add(process)
        simple_db_session.flush()

        log = WorkflowOperationLogService.create_log(
            tenant_id=tenant.id,
            process_instance_id=process.id,
            operation_type="APPROVE",
            operator_id=user.id,
            comment="Test",
            db=simple_db_session,
        )

        simple_db_session.commit()

        # 获取日志
        retrieved_log = WorkflowOperationLogService.get_log_by_id(
            log_id=log.id,
            tenant_id=tenant.id,
            db=simple_db_session,
        )

        assert retrieved_log.id == log.id
        assert retrieved_log.operation_type == "APPROVE"

    def test_get_log_by_id_not_found(self, simple_db_session: Session):
        """测试获取不存在的日志"""
        with pytest.raises(NotFoundError, match="操作日志不存在"):
            WorkflowOperationLogService.get_log_by_id(
                log_id=9999,
                tenant_id=1,
                db=simple_db_session,
            )
