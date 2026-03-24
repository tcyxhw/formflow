"""
任务 1.4：ProcessInstance 快照字段集成测试

测试内容：
- 流程启动时保存表单数据快照
- 查询流程实例时返回快照
- 快照数据完整性验证
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.form import Form, FormVersion, Submission
from app.models.workflow import FlowDefinition, FlowNode, ProcessInstance
from app.models.user import User, Tenant
from app.services.process_service import ProcessService
from app.core.exceptions import BusinessError


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
                {"id": "field2", "name": "Email", "type": "email"},
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
    form_data = {
        "field1": "John Doe",
        "field2": "john@example.com",
        "timestamp": datetime.now().isoformat(),
    }
    submission = Submission(
        tenant_id=tenant.id,
        form_id=form.id,
        form_version_id=form_version.id,
        submitter_user_id=user.id,
        data_jsonb=form_data,
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
        "form_data": form_data,
    }


class TestProcessInstanceSnapshot:
    """ProcessInstance 快照字段集成测试"""
    
    def test_snapshot_saved_on_process_start(self, db_session: Session, setup_test_data):
        """测试：流程启动时保存表单数据快照"""
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
        
        # 验证快照已保存
        assert process.form_data_snapshot is not None
        assert process.form_data_snapshot == data["form_data"]
        assert process.form_data_snapshot["field1"] == "John Doe"
        assert process.form_data_snapshot["field2"] == "john@example.com"
    
    def test_snapshot_persisted_in_database(self, db_session: Session, setup_test_data):
        """测试：快照数据持久化到数据库"""
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
        process_id = process.id
        
        # 提交事务
        db_session.commit()
        
        # 从数据库重新查询
        retrieved_process = db_session.query(ProcessInstance).filter(
            ProcessInstance.id == process_id
        ).first()
        
        # 验证快照已正确保存
        assert retrieved_process is not None
        assert retrieved_process.form_data_snapshot is not None
        assert retrieved_process.form_data_snapshot["field1"] == "John Doe"
    
    def test_snapshot_with_complex_data(self, db_session: Session, setup_test_data):
        """测试：复杂表单数据快照保存"""
        data = setup_test_data
        
        # 创建复杂的表单数据
        complex_form_data = {
            "field1": "John Doe",
            "field2": "john@example.com",
            "nested": {
                "address": "123 Main St",
                "city": "New York",
                "zip": "10001",
            },
            "array": [
                {"item": "Item 1", "value": 100},
                {"item": "Item 2", "value": 200},
            ],
            "timestamp": datetime.now().isoformat(),
        }
        
        # 更新提交记录
        data["submission"].data_jsonb = complex_form_data
        db_session.flush()
        
        # 启动流程
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user"].id,
        )
        
        # 验证复杂数据已正确保存
        assert process.form_data_snapshot == complex_form_data
        assert process.form_data_snapshot["nested"]["city"] == "New York"
        assert len(process.form_data_snapshot["array"]) == 2
        assert process.form_data_snapshot["array"][0]["value"] == 100
    
    def test_snapshot_null_when_submission_not_found(self, db_session: Session, setup_test_data):
        """测试：提交记录不存在时快照为 null"""
        data = setup_test_data
        
        # 使用不存在的 submission_id
        process = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=99999,  # 不存在的 ID
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user"].id,
        )
        
        # 验证快照为 null
        assert process.form_data_snapshot is None
    
    def test_snapshot_independent_from_submission(self, db_session: Session, setup_test_data):
        """测试：快照独立于提交记录的后续修改"""
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
        
        original_snapshot = process.form_data_snapshot.copy()
        
        # 修改提交记录的数据
        data["submission"].data_jsonb["field1"] = "Modified Name"
        db_session.flush()
        
        # 验证快照未被修改
        assert process.form_data_snapshot == original_snapshot
        assert process.form_data_snapshot["field1"] == "John Doe"
        assert data["submission"].data_jsonb["field1"] == "Modified Name"
    
    def test_multiple_processes_have_independent_snapshots(self, db_session: Session, setup_test_data):
        """测试：多个流程实例有独立的快照"""
        data = setup_test_data
        
        # 创建第二个提交记录
        form_data_2 = {
            "field1": "Jane Doe",
            "field2": "jane@example.com",
        }
        submission_2 = Submission(
            tenant_id=data["tenant"].id,
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submitter_user_id=data["user"].id,
            data_jsonb=form_data_2,
            status="submitted",
        )
        db_session.add(submission_2)
        db_session.flush()
        
        # 启动两个流程
        process_1 = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=data["submission"].id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user"].id,
        )
        
        process_2 = ProcessService.start_process(
            form_id=data["form"].id,
            form_version_id=data["form_version"].id,
            submission_id=submission_2.id,
            tenant_id=data["tenant"].id,
            db=db_session,
            operator_id=data["user"].id,
        )
        
        # 验证两个流程有不同的快照
        assert process_1.form_data_snapshot["field1"] == "John Doe"
        assert process_2.form_data_snapshot["field1"] == "Jane Doe"
        assert process_1.form_data_snapshot != process_2.form_data_snapshot
