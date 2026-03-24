"""
测试 WorkflowOperationLogService 服务类
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.workflow import WorkflowOperationLog, ProcessInstance, FlowDefinition, FlowNode
from app.models.form import Form, FormVersion, Submission
from app.models.user import User, Tenant
from app.services.workflow_operation_log_service import WorkflowOperationLogService
from app.core.exceptions import NotFoundError


@pytest.fixture
def setup_test_data(db_session: Session):
    """设置测试数据"""
    # 创建租户
    tenant = Tenant(name="Test Tenant")
    db_session.add(tenant)
    db_session.flush()

    # 创建用户
    user = User(
        tenant_id=tenant.id,
        account="testuser",
        password_hash="hash",
        name="Test User",
        email="test@example.com",
    )
    db_session.add(user)
    db_session.flush()

    # 创建表单
    form = Form(
        tenant_id=tenant.id,
        name="Test Form",
        access_mode="private",
        owner_user_id=user.id,
    )
    db_session.add(form)
    db_session.flush()

    # 创建表单版本
    form_version = FormVersion(
        form_id=form.id,
        version=1,
        schema_json={"fields": []},
    )
    db_session.add(form_version)
    db_session.flush()

    # 创建提交记录
    submission = Submission(
        tenant_id=tenant.id,
        form_id=form.id,
        form_version_id=form_version.id,
        submitter_user_id=user.id,
        data_jsonb={},
    )
    db_session.add(submission)
    db_session.flush()

    # 创建流程定义
    flow_def = FlowDefinition(
        tenant_id=tenant.id,
        form_id=form.id,
        version=1,
        definition_json={},
    )
    db_session.add(flow_def)
    db_session.flush()

    # 创建流程实例
    process = ProcessInstance(
        tenant_id=tenant.id,
        form_id=form.id,
        form_version_id=form_version.id,
        submission_id=submission.id,
        flow_definition_id=flow_def.id,
    )
    db_session.add(process)
    db_session.flush()

    return {
        "tenant": tenant,
        "user": user,
        "form": form,
        "form_version": form_version,
        "submission": submission,
        "flow_def": flow_def,
        "process": process,
    }


class TestWorkflowOperationLogService:
    """WorkflowOperationLogService 测试类"""

    def test_create_log(self, db_session: Session, setup_test_data):
        """测试创建操作日志"""
        data = setup_test_data

        log = WorkflowOperationLogService.create_log(
            tenant_id=data["tenant"].id,
            process_instance_id=data["process"].id,
            operation_type="SUBMIT",
            operator_id=data["user"].id,
            comment="Test comment",
            detail_json={"key": "value"},
            db=db_session,
        )

        assert log.id is not None
        assert log.tenant_id == data["tenant"].id
        assert log.process_instance_id == data["process"].id
        assert log.operation_type == "SUBMIT"
        assert log.operator_id == data["user"].id
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

    def test_get_process_logs(self, db_session: Session, setup_test_data):
        """测试获取流程的操作日志"""
        data = setup_test_data

        # 创建多条日志
        for i in range(5):
            WorkflowOperationLogService.create_log(
                tenant_id=data["tenant"].id,
                process_instance_id=data["process"].id,
                operation_type="APPROVE" if i % 2 == 0 else "REJECT",
                operator_id=data["user"].id,
                comment=f"Comment {i}",
                db=db_session,
            )

        db_session.commit()

        # 获取日志
        logs, total = WorkflowOperationLogService.get_process_logs(
            process_instance_id=data["process"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            page=1,
            page_size=10,
        )

        assert total == 5
        assert len(logs) == 5
        # 验证按创建时间倒序
        assert logs[0].created_at >= logs[-1].created_at

    def test_get_process_logs_pagination(self, db_session: Session, setup_test_data):
        """测试日志分页"""
        data = setup_test_data

        # 创建10条日志
        for i in range(10):
            WorkflowOperationLogService.create_log(
                tenant_id=data["tenant"].id,
                process_instance_id=data["process"].id,
                operation_type="APPROVE",
                operator_id=data["user"].id,
                db=db_session,
            )

        db_session.commit()

        # 第一页
        logs1, total1 = WorkflowOperationLogService.get_process_logs(
            process_instance_id=data["process"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            page=1,
            page_size=5,
        )

        assert total1 == 10
        assert len(logs1) == 5

        # 第二页
        logs2, total2 = WorkflowOperationLogService.get_process_logs(
            process_instance_id=data["process"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            page=2,
            page_size=5,
        )

        assert total2 == 10
        assert len(logs2) == 5
        # 验证两页的日志不重复
        ids1 = {log.id for log in logs1}
        ids2 = {log.id for log in logs2}
        assert len(ids1 & ids2) == 0

    def test_get_operation_timeline(self, db_session: Session, setup_test_data):
        """测试获取操作时间线"""
        data = setup_test_data

        # 创建多条日志
        for i in range(3):
            WorkflowOperationLogService.create_log(
                tenant_id=data["tenant"].id,
                process_instance_id=data["process"].id,
                operation_type="APPROVE",
                operator_id=data["user"].id,
                comment=f"Comment {i}",
                detail_json={"index": i},
                db=db_session,
            )

        db_session.commit()

        # 获取时间线
        timeline = WorkflowOperationLogService.get_operation_timeline(
            process_instance_id=data["process"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
        )

        assert len(timeline) == 3
        # 验证时间线按创建时间正序排列
        for i in range(len(timeline) - 1):
            assert timeline[i]["created_at"] <= timeline[i + 1]["created_at"]

        # 验证时间线包含所有必要字段
        for entry in timeline:
            assert "id" in entry
            assert "operation_type" in entry
            assert "operator_id" in entry
            assert "comment" in entry
            assert "detail_json" in entry
            assert "created_at" in entry

    def test_get_log_by_id(self, db_session: Session, setup_test_data):
        """测试获取日志详情"""
        data = setup_test_data

        log = WorkflowOperationLogService.create_log(
            tenant_id=data["tenant"].id,
            process_instance_id=data["process"].id,
            operation_type="APPROVE",
            operator_id=data["user"].id,
            comment="Test",
            db=db_session,
        )

        db_session.commit()

        # 获取日志
        retrieved_log = WorkflowOperationLogService.get_log_by_id(
            log_id=log.id,
            tenant_id=data["tenant"].id,
            db=db_session,
        )

        assert retrieved_log.id == log.id
        assert retrieved_log.operation_type == "APPROVE"

    def test_get_log_by_id_not_found(self, db_session: Session, setup_test_data):
        """测试获取不存在的日志"""
        data = setup_test_data
        
        with pytest.raises(NotFoundError, match="操作日志不存在"):
            WorkflowOperationLogService.get_log_by_id(
                log_id=9999,
                tenant_id=data["tenant"].id,
                db=db_session,
            )

    def test_get_log_by_id_wrong_tenant(self, db_session: Session, setup_test_data):
        """测试获取其他租户的日志"""
        data = setup_test_data

        log = WorkflowOperationLogService.create_log(
            tenant_id=data["tenant"].id,
            process_instance_id=data["process"].id,
            operation_type="APPROVE",
            operator_id=data["user"].id,
            db=db_session,
        )

        db_session.commit()

        # 尝试用其他租户ID获取
        with pytest.raises(NotFoundError, match="操作日志不存在"):
            WorkflowOperationLogService.get_log_by_id(
                log_id=log.id,
                tenant_id=9999,
                db=db_session,
            )

    def test_operation_types(self, db_session: Session, setup_test_data):
        """测试不同的操作类型"""
        data = setup_test_data

        operation_types = ["SUBMIT", "APPROVE", "REJECT", "CANCEL", "CC"]

        for op_type in operation_types:
            log = WorkflowOperationLogService.create_log(
                tenant_id=data["tenant"].id,
                process_instance_id=data["process"].id,
                operation_type=op_type,
                operator_id=data["user"].id,
                db=db_session,
            )

            assert log.operation_type == op_type

        db_session.commit()

        # 验证所有日志都被创建
        logs, total = WorkflowOperationLogService.get_process_logs(
            process_instance_id=data["process"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
        )

        assert total == len(operation_types)
