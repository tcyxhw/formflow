"""
任务 1.5：Task 扩展字段集成测试

测试内容：
- 任务创建时设置 task_type 字段
- 审批完成时设置 comment 字段
- 不同任务类型的区分
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.form import Form, FormVersion, Submission
from app.models.workflow import FlowDefinition, FlowNode, ProcessInstance, Task
from app.models.user import User, Tenant
from app.services.process_service import ProcessService
from app.services.approval_service import TaskService
from app.schemas.approval_schemas import TaskActionRequest


@pytest.fixture
def setup_test_data(db_session: Session):
    """设置测试数据"""
    # 创建租户
    tenant = Tenant(name="test_tenant")
    db_session.add(tenant)
    db_session.flush()
    
    # 创建用户
    user = User(
        tenant_id=tenant.id,
        username="test_user",
        email="test@example.com",
        password_hash="hash",
    )
    db_session.add(user)
    db_session.flush()
    
    # 创建表单
    form = Form(
        tenant_id=tenant.id,
        name="Test Form",
        owner_user_id=user.id,
        status="published",
    )
    db_session.add(form)
    db_session.flush()
    
    # 创建表单版本
    form_version = FormVersion(
        tenant_id=tenant.id,
        form_id=form.id,
        version=1,
        schema_json={
            "fields": [
                {"id": "field1", "name": "Name", "type": "text"},
            ]
        },
    )
    db_session.add(form_version)
    db_session.flush()
    
    # 创建流程定义
    flow_def = FlowDefinition(
        tenant_id=tenant.id,
        form_id=form.id,
        version=1,
        definition_json={"nodes": [], "routes": []},
    )
    db_session.add(flow_def)
    db_session.flush()
    
    # 创建流程节点
    node = FlowNode(
        tenant_id=tenant.id,
        flow_definition_id=flow_def.id,
        type="user",
        name="Approval Node",
        config_json={"assignee_type": "user", "assignee_id": user.id},
    )
    db_session.add(node)
    db_session.flush()
    
    # 创建提交记录
    submission = Submission(
        tenant_id=tenant.id,
        form_id=form.id,
        form_version_id=form_version.id,
        submitter_user_id=user.id,
        data_jsonb={"field1": "Test Value"},
        status="submitted",
    )
    db_session.add(submission)
    db_session.flush()
    
    return {
        "tenant": tenant,
        "user": user,
        "form": form,
        "form_version": form_version,
        "flow_def": flow_def,
        "node": node,
        "submission": submission,
    }


class TestTaskFieldsIntegration:
    """Task 扩展字段集成测试"""
    
    def test_task_type_set_on_creation(self, db_session: Session, setup_test_data):
        """测试：任务创建时设置 task_type 为 'approve'"""
        data = setup_test_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user"].id,
        )
        
        # 查询创建的任务
        task = db_session.query(Task).filter(
            Task.process_instance_id == process.id
        ).first()
        
        # 验证 task_type 已设置
        assert task is not None
        assert task.task_type == "approve"
    
    def test_task_type_persisted_in_database(self, db_session: Session, setup_test_data):
        """测试：task_type 正确持久化到数据库"""
        data = setup_test_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user"].id,
        )
        
        task_id = db_session.query(Task).filter(
            Task.process_instance_id == process.id
        ).first().id
        
        # 提交事务
        db_session.commit()
        
        # 从数据库重新查询
        retrieved_task = db_session.query(Task).filter(Task.id == task_id).first()
        
        # 验证 task_type 已正确保存
        assert retrieved_task is not None
        assert retrieved_task.task_type == "approve"
    
    def test_comment_set_on_task_completion(self, db_session: Session, setup_test_data):
        """测试：审批完成时设置 comment 字段"""
        data = setup_test_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user"].id,
        )
        
        # 获取任务
        task = db_session.query(Task).filter(
            Task.process_instance_id == process.id
        ).first()
        
        # 认领任务
        task.claimed_by = data["user"].id
        task.claimed_at = datetime.now(timezone.utc)
        db_session.flush()
        
        # 执行审批操作
        request = TaskActionRequest(
            action="approve",
            comment="This looks good to me",
            extra_data={},
        )
        
        TaskService.perform_task_action(
            task_id=task.id,
            tenant_id=data["tenant"].id,
            request=request,
            current_user=data["user"],
            db=db_session,
        )
        
        # 验证 comment 已设置
        assert task.comment == "This looks good to me"
    
    def test_comment_persisted_in_database(self, db_session: Session, setup_test_data):
        """测试：comment 正确持久化到数据库"""
        data = setup_test_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user"].id,
        )
        
        # 获取任务
        task = db_session.query(Task).filter(
            Task.process_instance_id == process.id
        ).first()
        task_id = task.id
        
        # 认领任务
        task.claimed_by = data["user"].id
        task.claimed_at = datetime.now(timezone.utc)
        db_session.flush()
        
        # 执行审批操作
        request = TaskActionRequest(
            action="approve",
            comment="Approved with modifications",
            extra_data={},
        )
        
        TaskService.perform_task_action(
            task_id=task.id,
            tenant_id=data["tenant"].id,
            request=request,
            current_user=data["user"],
            db=db_session,
        )
        
        # 提交事务
        db_session.commit()
        
        # 从数据库重新查询
        retrieved_task = db_session.query(Task).filter(Task.id == task_id).first()
        
        # 验证 comment 已正确保存
        assert retrieved_task is not None
        assert retrieved_task.comment == "Approved with modifications"
    
    def test_comment_with_special_characters(self, db_session: Session, setup_test_data):
        """测试：comment 支持特殊字符"""
        data = setup_test_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user"].id,
        )
        
        # 获取任务
        task = db_session.query(Task).filter(
            Task.process_instance_id == process.id
        ).first()
        
        # 认领任务
        task.claimed_by = data["user"].id
        task.claimed_at = datetime.now(timezone.utc)
        db_session.flush()
        
        # 执行审批操作，包含特殊字符
        special_comment = "需要修改：字段1应为'中文'，字段2需要@符号，价格¥100"
        request = TaskActionRequest(
            action="approve",
            comment=special_comment,
            extra_data={},
        )
        
        TaskService.perform_task_action(
            task_id=task.id,
            tenant_id=data["tenant"].id,
            request=request,
            current_user=data["user"],
            db=db_session,
        )
        
        # 验证特殊字符已正确保存
        assert task.comment == special_comment
    
    def test_comment_empty_string(self, db_session: Session, setup_test_data):
        """测试：comment 可以为空字符串"""
        data = setup_test_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user"].id,
        )
        
        # 获取任务
        task = db_session.query(Task).filter(
            Task.process_instance_id == process.id
        ).first()
        
        # 认领任务
        task.claimed_by = data["user"].id
        task.claimed_at = datetime.now(timezone.utc)
        db_session.flush()
        
        # 执行审批操作，不提供 comment
        request = TaskActionRequest(
            action="approve",
            comment="",
            extra_data={},
        )
        
        TaskService.perform_task_action(
            task_id=task.id,
            tenant_id=data["tenant"].id,
            request=request,
            current_user=data["user"],
            db=db_session,
        )
        
        # 验证 comment 为空字符串
        assert task.comment == ""
    
    def test_comment_max_length(self, db_session: Session, setup_test_data):
        """测试：comment 字段长度限制（500字符）"""
        data = setup_test_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user"].id,
        )
        
        # 获取任务
        task = db_session.query(Task).filter(
            Task.process_instance_id == process.id
        ).first()
        
        # 认领任务
        task.claimed_by = data["user"].id
        task.claimed_at = datetime.now(timezone.utc)
        db_session.flush()
        
        # 创建 500 字符的 comment
        long_comment = "A" * 500
        request = TaskActionRequest(
            action="approve",
            comment=long_comment,
            extra_data={},
        )
        
        TaskService.perform_task_action(
            task_id=task.id,
            tenant_id=data["tenant"].id,
            request=request,
            current_user=data["user"],
            db=db_session,
        )
        
        # 验证 comment 已正确保存
        assert task.comment == long_comment
        assert len(task.comment) == 500
    
    def test_task_type_and_comment_together(self, db_session: Session, setup_test_data):
        """测试：task_type 和 comment 字段协同工作"""
        data = setup_test_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user"].id,
        )
        
        # 获取任务
        task = db_session.query(Task).filter(
            Task.process_instance_id == process.id
        ).first()
        
        # 验证初始状态
        assert task.task_type == "approve"
        assert task.comment is None
        
        # 认领任务
        task.claimed_by = data["user"].id
        task.claimed_at = datetime.now(timezone.utc)
        db_session.flush()
        
        # 执行审批操作
        request = TaskActionRequest(
            action="approve",
            comment="Looks good",
            extra_data={},
        )
        
        TaskService.perform_task_action(
            task_id=task.id,
            tenant_id=data["tenant"].id,
            request=request,
            current_user=data["user"],
            db=db_session,
        )
        
        # 验证两个字段都已正确设置
        assert task.task_type == "approve"
        assert task.comment == "Looks good"
