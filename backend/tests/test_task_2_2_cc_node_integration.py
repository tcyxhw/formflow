"""
任务 2.2：CC 节点集成测试

测试内容：
- 完整流程中的 CC 节点处理
- CC 节点与审批流程的协同
- 边界情况处理
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.form import Form, FormVersion, Submission
from app.models.workflow import FlowDefinition, FlowNode, FlowRoute, ProcessInstance, Task
from app.models.user import User, Tenant, UserRole, Role
from app.services.process_service import ProcessService
from app.services.approval_service import TaskService
from app.schemas.approval_schemas import TaskActionRequest


@pytest.fixture
def setup_full_flow_data(db_session: Session):
    """设置完整流程测试数据"""
    # 创建租户
    tenant = Tenant(name="test_tenant")
    db_session.add(tenant)
    db_session.flush()
    
    # 创建用户
    submitter = User(
        tenant_id=tenant.id,
        username="submitter",
        email="submitter@example.com",
        password_hash="hash",
    )
    approver = User(
        tenant_id=tenant.id,
        username="approver",
        email="approver@example.com",
        password_hash="hash",
    )
    cc_user1 = User(
        tenant_id=tenant.id,
        username="cc_user1",
        email="cc_user1@example.com",
        password_hash="hash",
    )
    cc_user2 = User(
        tenant_id=tenant.id,
        username="cc_user2",
        email="cc_user2@example.com",
        password_hash="hash",
    )
    db_session.add_all([submitter, approver, cc_user1, cc_user2])
    db_session.flush()
    
    # 创建表单
    form = Form(
        tenant_id=tenant.id,
        name="Test Form",
        owner_user_id=submitter.id,
        status="published",
    )
    db_session.add(form)
    db_session.flush()
    
    # 创建表单版本
    form_version = FormVersion(
        tenant_id=tenant.id,
        form_id=form.id,
        version=1,
        schema_json={"fields": []},
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
    
    # 创建审批节点
    approval_node = FlowNode(
        tenant_id=tenant.id,
        flow_definition_id=flow_def.id,
        type="user",
        name="Approval Node",
        config_json={"assignee_type": "user", "assignee_id": approver.id},
    )
    db_session.add(approval_node)
    db_session.flush()
    
    # 创建 CC 节点
    cc_node = FlowNode(
        tenant_id=tenant.id,
        flow_definition_id=flow_def.id,
        type="cc",
        name="CC Node",
        assignee_type="user",
        assignee_value={"user_ids": [cc_user1.id, cc_user2.id]},
    )
    db_session.add(cc_node)
    db_session.flush()
    
    # 创建结束节点
    end_node = FlowNode(
        tenant_id=tenant.id,
        flow_definition_id=flow_def.id,
        type="end",
        name="End Node",
    )
    db_session.add(end_node)
    db_session.flush()
    
    # 创建路由：审批 -> CC -> 结束
    route1 = FlowRoute(
        tenant_id=tenant.id,
        flow_definition_id=flow_def.id,
        from_node_id=approval_node.id,
        to_node_id=cc_node.id,
    )
    route2 = FlowRoute(
        tenant_id=tenant.id,
        flow_definition_id=flow_def.id,
        from_node_id=cc_node.id,
        to_node_id=end_node.id,
    )
    db_session.add_all([route1, route2])
    db_session.flush()
    
    # 创建提交记录
    submission = Submission(
        tenant_id=tenant.id,
        form_id=form.id,
        form_version_id=form_version.id,
        submitter_user_id=submitter.id,
        data_jsonb={"field1": "Test Value"},
        status="submitted",
    )
    db_session.add(submission)
    db_session.flush()
    
    return {
        "tenant": tenant,
        "submitter": submitter,
        "approver": approver,
        "cc_user1": cc_user1,
        "cc_user2": cc_user2,
        "form": form,
        "form_version": form_version,
        "flow_def": flow_def,
        "approval_node": approval_node,
        "cc_node": cc_node,
        "end_node": end_node,
        "submission": submission,
    }


class TestCCNodeIntegration:
    """CC 节点集成测试"""
    
    def test_complete_flow_with_cc_node(self, db_session: Session, setup_full_flow_data):
        """测试：完整流程包含 CC 节点"""
        data = setup_full_flow_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["submitter"].id,
        )
        
        # 验证流程已启动
        assert process.id is not None
        assert process.state == "running"
        
        # 查询审批任务
        approval_task = db_session.query(Task).filter(
            Task.process_instance_id == process.id,
            Task.node_id == data["approval_node"].id,
        ).first()
        
        # 验证审批任务已创建
        assert approval_task is not None
        assert approval_task.task_type == "approve"
        assert approval_task.assignee_user_id == data["approver"].id
    
    def test_cc_tasks_created_after_approval(self, db_session: Session, setup_full_flow_data):
        """测试：审批后创建 CC 任务"""
        data = setup_full_flow_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["submitter"].id,
        )
        
        # 获取审批任务
        approval_task = db_session.query(Task).filter(
            Task.process_instance_id == process.id,
            Task.node_id == data["approval_node"].id,
        ).first()
        
        # 认领审批任务
        approval_task.claimed_by = data["approver"].id
        approval_task.claimed_at = datetime.now(timezone.utc)
        db_session.flush()
        
        # 执行审批操作
        request = TaskActionRequest(
            action="approve",
            comment="Approved",
            extra_data={},
        )
        
        TaskService.perform_task_action(
            task_id=approval_task.id,
            tenant_id=data["tenant"].id,
            request=request,
            current_user=data["approver"],
            db=db_session,
        )
        
        # 查询 CC 任务
        cc_tasks = db_session.query(Task).filter(
            Task.process_instance_id == process.id,
            Task.node_id == data["cc_node"].id,
        ).all()
        
        # 验证 CC 任务已创建
        assert len(cc_tasks) == 2
        assert all(task.task_type == "cc" for task in cc_tasks)
    
    def test_cc_tasks_assigned_to_correct_users(self, db_session: Session, setup_full_flow_data):
        """测试：CC 任务分配给正确的用户"""
        data = setup_full_flow_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["submitter"].id,
        )
        
        # 获取审批任务
        approval_task = db_session.query(Task).filter(
            Task.process_instance_id == process.id,
            Task.node_id == data["approval_node"].id,
        ).first()
        
        # 认领审批任务
        approval_task.claimed_by = data["approver"].id
        approval_task.claimed_at = datetime.now(timezone.utc)
        db_session.flush()
        
        # 执行审批操作
        request = TaskActionRequest(
            action="approve",
            comment="Approved",
            extra_data={},
        )
        
        TaskService.perform_task_action(
            task_id=approval_task.id,
            tenant_id=data["tenant"].id,
            request=request,
            current_user=data["approver"],
            db=db_session,
        )
        
        # 查询 CC 任务
        cc_tasks = db_session.query(Task).filter(
            Task.process_instance_id == process.id,
            Task.node_id == data["cc_node"].id,
        ).all()
        
        # 验证 CC 任务分配
        assignee_ids = [task.assignee_user_id for task in cc_tasks]
        assert data["cc_user1"].id in assignee_ids
        assert data["cc_user2"].id in assignee_ids
    
    def test_flow_completes_after_cc_node(self, db_session: Session, setup_full_flow_data):
        """测试：CC 节点后流程继续推进"""
        data = setup_full_flow_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["submitter"].id,
        )
        
        # 获取审批任务
        approval_task = db_session.query(Task).filter(
            Task.process_instance_id == process.id,
            Task.node_id == data["approval_node"].id,
        ).first()
        
        # 认领审批任务
        approval_task.claimed_by = data["approver"].id
        approval_task.claimed_at = datetime.now(timezone.utc)
        db_session.flush()
        
        # 执行审批操作
        request = TaskActionRequest(
            action="approve",
            comment="Approved",
            extra_data={},
        )
        
        TaskService.perform_task_action(
            task_id=approval_task.id,
            tenant_id=data["tenant"].id,
            request=request,
            current_user=data["approver"],
            db=db_session,
        )
        
        # 刷新流程实例
        db_session.refresh(process)
        
        # 验证流程状态
        # 注意：CC 节点是信息节点，不阻止流程推进
        # 流程应该继续到结束节点
        assert process.state == "finished"
    
    def test_cc_node_with_rejection(self, db_session: Session, setup_full_flow_data):
        """测试：审批驳回时不创建 CC 任务"""
        data = setup_full_flow_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["submitter"].id,
        )
        
        # 获取审批任务
        approval_task = db_session.query(Task).filter(
            Task.process_instance_id == process.id,
            Task.node_id == data["approval_node"].id,
        ).first()
        
        # 认领审批任务
        approval_task.claimed_by = data["approver"].id
        approval_task.claimed_at = datetime.now(timezone.utc)
        db_session.flush()
        
        # 执行驳回操作
        request = TaskActionRequest(
            action="reject",
            comment="Rejected",
            extra_data={},
        )
        
        TaskService.perform_task_action(
            task_id=approval_task.id,
            tenant_id=data["tenant"].id,
            request=request,
            current_user=data["approver"],
            db=db_session,
        )
        
        # 查询 CC 任务
        cc_tasks = db_session.query(Task).filter(
            Task.process_instance_id == process.id,
            Task.node_id == data["cc_node"].id,
        ).all()
        
        # 验证没有创建 CC 任务
        assert len(cc_tasks) == 0
    
    def test_multiple_cc_nodes_in_sequence(self, db_session: Session, setup_full_flow_data):
        """测试：多个 CC 节点顺序处理"""
        data = setup_full_flow_data
        
        # 创建第二个 CC 节点
        cc_node2 = FlowNode(
            tenant_id=data["tenant"].id,
            flow_definition_id=data["flow_def"].id,
            type="cc",
            name="CC Node 2",
            assignee_type="user",
            assignee_value={"user_ids": [data["cc_user1"].id]},
        )
        db_session.add(cc_node2)
        db_session.flush()
        
        # 创建路由：CC1 -> CC2 -> 结束
        route_cc1_cc2 = FlowRoute(
            tenant_id=data["tenant"].id,
            flow_definition_id=data["flow_def"].id,
            from_node_id=data["cc_node"].id,
            to_node_id=cc_node2.id,
        )
        route_cc2_end = FlowRoute(
            tenant_id=data["tenant"].id,
            flow_definition_id=data["flow_def"].id,
            from_node_id=cc_node2.id,
            to_node_id=data["end_node"].id,
        )
        
        # 删除原来的路由
        db_session.query(FlowRoute).filter(
            FlowRoute.from_node_id == data["cc_node"].id,
            FlowRoute.to_node_id == data["end_node"].id,
        ).delete()
        
        db_session.add_all([route_cc1_cc2, route_cc2_end])
        db_session.flush()
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["submitter"].id,
        )
        
        # 获取审批任务
        approval_task = db_session.query(Task).filter(
            Task.process_instance_id == process.id,
            Task.node_id == data["approval_node"].id,
        ).first()
        
        # 认领审批任务
        approval_task.claimed_by = data["approver"].id
        approval_task.claimed_at = datetime.now(timezone.utc)
        db_session.flush()
        
        # 执行审批操作
        request = TaskActionRequest(
            action="approve",
            comment="Approved",
            extra_data={},
        )
        
        TaskService.perform_task_action(
            task_id=approval_task.id,
            tenant_id=data["tenant"].id,
            request=request,
            current_user=data["approver"],
            db=db_session,
        )
        
        # 查询所有 CC 任务
        cc_tasks_1 = db_session.query(Task).filter(
            Task.process_instance_id == process.id,
            Task.node_id == data["cc_node"].id,
        ).all()
        cc_tasks_2 = db_session.query(Task).filter(
            Task.process_instance_id == process.id,
            Task.node_id == cc_node2.id,
        ).all()
        
        # 验证两组 CC 任务都已创建
        assert len(cc_tasks_1) == 2
        assert len(cc_tasks_2) == 1
    
    def test_cc_node_with_no_assignees(self, db_session: Session, setup_full_flow_data):
        """测试：CC 节点无抄送人时的处理"""
        data = setup_full_flow_data
        
        # 修改 CC 节点配置为空
        data["cc_node"].assignee_value = {"user_ids": []}
        db_session.flush()
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["submitter"].id,
        )
        
        # 获取审批任务
        approval_task = db_session.query(Task).filter(
            Task.process_instance_id == process.id,
            Task.node_id == data["approval_node"].id,
        ).first()
        
        # 认领审批任务
        approval_task.claimed_by = data["approver"].id
        approval_task.claimed_at = datetime.now(timezone.utc)
        db_session.flush()
        
        # 执行审批操作
        request = TaskActionRequest(
            action="approve",
            comment="Approved",
            extra_data={},
        )
        
        TaskService.perform_task_action(
            task_id=approval_task.id,
            tenant_id=data["tenant"].id,
            request=request,
            current_user=data["approver"],
            db=db_session,
        )
        
        # 查询 CC 任务
        cc_tasks = db_session.query(Task).filter(
            Task.process_instance_id == process.id,
            Task.node_id == data["cc_node"].id,
        ).all()
        
        # 验证没有创建 CC 任务
        assert len(cc_tasks) == 0
        
        # 验证流程继续推进
        db_session.refresh(process)
        assert process.state == "finished"
