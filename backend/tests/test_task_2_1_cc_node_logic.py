"""
任务 2.1：CC 节点业务逻辑实现测试

测试内容：
- CC 节点任务创建
- 抄送人选择逻辑
- CC 节点流程推进
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.form import Form, FormVersion, Submission
from app.models.workflow import FlowDefinition, FlowNode, FlowRoute, ProcessInstance, Task
from app.models.user import User, Tenant, UserRole, Role, Department, UserPosition, Position
from app.services.process_service import ProcessService
from app.services.assignment_service import AssignmentService


@pytest.fixture
def setup_cc_test_data(db_session: Session):
    """设置 CC 节点测试数据"""
    # 创建租户
    tenant = Tenant(name="test_tenant")
    db_session.add(tenant)
    db_session.flush()
    
    # 创建用户
    user1 = User(
        tenant_id=tenant.id,
        username="user1",
        email="user1@example.com",
        password_hash="hash",
    )
    user2 = User(
        tenant_id=tenant.id,
        username="user2",
        email="user2@example.com",
        password_hash="hash",
    )
    user3 = User(
        tenant_id=tenant.id,
        username="user3",
        email="user3@example.com",
        password_hash="hash",
    )
    db_session.add_all([user1, user2, user3])
    db_session.flush()
    
    # 创建角色
    role = Role(
        tenant_id=tenant.id,
        name="Manager",
    )
    db_session.add(role)
    db_session.flush()
    
    # 关联用户和角色
    user_role = UserRole(
        tenant_id=tenant.id,
        user_id=user2.id,
        role_id=role.id,
    )
    db_session.add(user_role)
    db_session.flush()
    
    # 创建部门
    department = Department(
        tenant_id=tenant.id,
        name="Engineering",
        type="department",
    )
    db_session.add(department)
    db_session.flush()
    
    # 关联用户和部门
    user3.department_id = department.id
    db_session.flush()
    
    # 创建表单
    form = Form(
        tenant_id=tenant.id,
        name="Test Form",
        owner_user_id=user1.id,
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
        config_json={"assignee_type": "user", "assignee_id": user1.id},
    )
    db_session.add(approval_node)
    db_session.flush()
    
    # 创建 CC 节点（直接指定用户）
    cc_node_direct = FlowNode(
        tenant_id=tenant.id,
        flow_definition_id=flow_def.id,
        type="cc",
        name="CC Node Direct",
        assignee_type="user",
        assignee_value={"user_ids": [user2.id, user3.id]},
    )
    db_session.add(cc_node_direct)
    db_session.flush()
    
    # 创建 CC 节点（按角色）
    cc_node_role = FlowNode(
        tenant_id=tenant.id,
        flow_definition_id=flow_def.id,
        type="cc",
        name="CC Node Role",
        assignee_type="role",
        assignee_value={"role_id": role.id},
    )
    db_session.add(cc_node_role)
    db_session.flush()
    
    # 创建 CC 节点（按部门）
    cc_node_dept = FlowNode(
        tenant_id=tenant.id,
        flow_definition_id=flow_def.id,
        type="cc",
        name="CC Node Department",
        assignee_type="department",
        assignee_value={"department_id": department.id},
    )
    db_session.add(cc_node_dept)
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
    
    # 创建路由
    route1 = FlowRoute(
        tenant_id=tenant.id,
        flow_definition_id=flow_def.id,
        from_node_id=approval_node.id,
        to_node_id=cc_node_direct.id,
    )
    route2 = FlowRoute(
        tenant_id=tenant.id,
        flow_definition_id=flow_def.id,
        from_node_id=cc_node_direct.id,
        to_node_id=end_node.id,
    )
    db_session.add_all([route1, route2])
    db_session.flush()
    
    # 创建提交记录
    submission = Submission(
        tenant_id=tenant.id,
        form_id=form.id,
        form_version_id=form_version.id,
        submitter_user_id=user1.id,
        data_jsonb={"field1": "Test Value"},
        status="submitted",
    )
    db_session.add(submission)
    db_session.flush()
    
    return {
        "tenant": tenant,
        "user1": user1,
        "user2": user2,
        "user3": user3,
        "role": role,
        "department": department,
        "form": form,
        "form_version": form_version,
        "flow_def": flow_def,
        "approval_node": approval_node,
        "cc_node_direct": cc_node_direct,
        "cc_node_role": cc_node_role,
        "cc_node_dept": cc_node_dept,
        "end_node": end_node,
        "submission": submission,
    }


class TestCCNodeLogic:
    """CC 节点业务逻辑测试"""
    
    def test_select_cc_assignees_direct_users(self, db_session: Session, setup_cc_test_data):
        """测试：直接指定用户的 CC 节点"""
        data = setup_cc_test_data
        
        # 获取抄送人列表
        assignees = AssignmentService.select_cc_assignees(
            data["cc_node_direct"],
            data["tenant"].id,
            db_session,
        )
        
        # 验证抄送人列表
        assert len(assignees) == 2
        assert data["user2"].id in assignees
        assert data["user3"].id in assignees
    
    def test_select_cc_assignees_by_role(self, db_session: Session, setup_cc_test_data):
        """测试：按角色选择 CC 抄送人"""
        data = setup_cc_test_data
        
        # 获取抄送人列表
        assignees = AssignmentService.select_cc_assignees(
            data["cc_node_role"],
            data["tenant"].id,
            db_session,
        )
        
        # 验证抄送人列表
        assert len(assignees) == 1
        assert data["user2"].id in assignees
    
    def test_select_cc_assignees_by_department(self, db_session: Session, setup_cc_test_data):
        """测试：按部门选择 CC 抄送人"""
        data = setup_cc_test_data
        
        # 获取抄送人列表
        assignees = AssignmentService.select_cc_assignees(
            data["cc_node_dept"],
            data["tenant"].id,
            db_session,
        )
        
        # 验证抄送人列表
        assert len(assignees) == 1
        assert data["user3"].id in assignees
    
    def test_create_cc_tasks(self, db_session: Session, setup_cc_test_data):
        """测试：创建 CC 任务"""
        data = setup_cc_test_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user1"].id,
        )
        
        # 创建 CC 任务
        cc_tasks = ProcessService._create_cc_tasks(
            process,
            data["cc_node_direct"],
            data["tenant"].id,
            db_session,
        )
        
        # 验证 CC 任务
        assert len(cc_tasks) == 2
        assert all(task.task_type == "cc" for task in cc_tasks)
        assert all(task.process_instance_id == process.id for task in cc_tasks)
        assert all(task.node_id == data["cc_node_direct"].id for task in cc_tasks)
    
    def test_cc_tasks_have_correct_assignees(self, db_session: Session, setup_cc_test_data):
        """测试：CC 任务分配给正确的用户"""
        data = setup_cc_test_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user1"].id,
        )
        
        # 创建 CC 任务
        cc_tasks = ProcessService._create_cc_tasks(
            process,
            data["cc_node_direct"],
            data["tenant"].id,
            db_session,
        )
        
        # 验证任务分配
        assignee_ids = [task.assignee_user_id for task in cc_tasks]
        assert data["user2"].id in assignee_ids
        assert data["user3"].id in assignee_ids
    
    def test_cc_tasks_persisted_in_database(self, db_session: Session, setup_cc_test_data):
        """测试：CC 任务持久化到数据库"""
        data = setup_cc_test_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user1"].id,
        )
        
        # 创建 CC 任务
        ProcessService._create_cc_tasks(
            process,
            data["cc_node_direct"],
            data["tenant"].id,
            db_session,
        )
        
        # 提交事务
        db_session.commit()
        
        # 从数据库查询 CC 任务
        cc_tasks = db_session.query(Task).filter(
            Task.process_instance_id == process.id,
            Task.task_type == "cc",
        ).all()
        
        # 验证 CC 任务已保存
        assert len(cc_tasks) == 2
        assert all(task.task_type == "cc" for task in cc_tasks)
    
    def test_cc_node_with_empty_assignees(self, db_session: Session, setup_cc_test_data):
        """测试：CC 节点无抄送人时的处理"""
        data = setup_cc_test_data
        
        # 创建空的 CC 节点
        empty_cc_node = FlowNode(
            tenant_id=data["tenant"].id,
            flow_definition_id=data["flow_def"].id,
            type="cc",
            name="Empty CC Node",
            assignee_type="user",
            assignee_value={"user_ids": []},
        )
        db_session.add(empty_cc_node)
        db_session.flush()
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user1"].id,
        )
        
        # 创建 CC 任务
        cc_tasks = ProcessService._create_cc_tasks(
            process,
            empty_cc_node,
            data["tenant"].id,
            db_session,
        )
        
        # 验证无任务创建
        assert len(cc_tasks) == 0
    
    def test_cc_node_with_no_config(self, db_session: Session, setup_cc_test_data):
        """测试：CC 节点无配置时的处理"""
        data = setup_cc_test_data
        
        # 创建无配置的 CC 节点
        no_config_cc_node = FlowNode(
            tenant_id=data["tenant"].id,
            flow_definition_id=data["flow_def"].id,
            type="cc",
            name="No Config CC Node",
        )
        db_session.add(no_config_cc_node)
        db_session.flush()
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user1"].id,
        )
        
        # 创建 CC 任务
        cc_tasks = ProcessService._create_cc_tasks(
            process,
            no_config_cc_node,
            data["tenant"].id,
            db_session,
        )
        
        # 验证无任务创建
        assert len(cc_tasks) == 0
    
    def test_multiple_cc_nodes_in_same_process(self, db_session: Session, setup_cc_test_data):
        """测试：同一流程中多个 CC 节点"""
        data = setup_cc_test_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user1"].id,
        )
        
        # 创建多个 CC 任务
        cc_tasks_1 = ProcessService._create_cc_tasks(
            process,
            data["cc_node_direct"],
            data["tenant"].id,
            db_session,
        )
        cc_tasks_2 = ProcessService._create_cc_tasks(
            process,
            data["cc_node_role"],
            data["tenant"].id,
            db_session,
        )
        
        # 验证两组 CC 任务
        assert len(cc_tasks_1) == 2
        assert len(cc_tasks_2) == 1
        
        # 验证任务来自不同的节点
        assert all(task.node_id == data["cc_node_direct"].id for task in cc_tasks_1)
        assert all(task.node_id == data["cc_node_role"].id for task in cc_tasks_2)
    
    def test_cc_task_type_field(self, db_session: Session, setup_cc_test_data):
        """测试：CC 任务的 task_type 字段"""
        data = setup_cc_test_data
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user1"].id,
        )
        
        # 创建 CC 任务
        cc_tasks = ProcessService._create_cc_tasks(
            process,
            data["cc_node_direct"],
            data["tenant"].id,
            db_session,
        )
        
        # 验证 task_type 字段
        for task in cc_tasks:
            assert task.task_type == "cc"
            assert task.task_type != "approve"
