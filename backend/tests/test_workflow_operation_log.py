"""
模块用途: 测试工作流操作日志表和相关模型扩展
依赖配置: pytest, SQLAlchemy
数据流向: 测试数据 -> 数据库 -> 验证结果
函数清单:
    - test_workflow_operation_log_model(): 测试操作日志模型
    - test_process_instance_snapshot_field(): 测试表单数据快照字段
    - test_task_extended_fields(): 测试任务扩展字段
"""

import pytest
from sqlalchemy.orm import Session

from app.models.workflow import (
    WorkflowOperationLog,
    ProcessInstance,
    Task,
    FlowDefinition,
    FlowNode,
)
from app.models.form import Form, FormVersion, Submission
from app.models.user import User


class TestWorkflowOperationLogModel:
    """测试工作流操作日志模型"""

    def test_workflow_operation_log_has_required_fields(self):
        """验证 WorkflowOperationLog 模型有所有必需字段"""
        # 检查模型是否有所有必需的列
        assert hasattr(WorkflowOperationLog, 'tenant_id')
        assert hasattr(WorkflowOperationLog, 'process_instance_id')
        assert hasattr(WorkflowOperationLog, 'operation_type')
        assert hasattr(WorkflowOperationLog, 'operator_id')
        assert hasattr(WorkflowOperationLog, 'comment')
        assert hasattr(WorkflowOperationLog, 'detail_json')

    def test_workflow_operation_log_table_name(self):
        """验证表名"""
        assert WorkflowOperationLog.__tablename__ == "workflow_operation_log"

    def test_workflow_operation_log_has_indexes(self):
        """验证索引定义"""
        # 检查 __table_args__ 中是否定义了索引
        assert hasattr(WorkflowOperationLog, '__table_args__')
        table_args = WorkflowOperationLog.__table_args__
        assert len(table_args) >= 3  # 至少有 3 个索引


class TestProcessInstanceFormDataSnapshot:
    """测试流程实例表单数据快照字段"""

    def test_process_instance_has_form_data_snapshot_field(self):
        """验证 ProcessInstance 有 form_data_snapshot 字段"""
        assert hasattr(ProcessInstance, 'form_data_snapshot')

    def test_process_instance_snapshot_field_type(self):
        """验证 form_data_snapshot 字段类型"""
        # 检查字段是否是 JSONB 类型
        from sqlalchemy.dialects.postgresql import JSONB
        
        column = ProcessInstance.__table__.columns['form_data_snapshot']
        # 检查列类型是否兼容 JSON
        assert 'JSON' in str(column.type).upper() or 'JSONB' in str(column.type).upper()


class TestTaskExtendedFields:
    """测试任务扩展字段"""

    def test_task_has_task_type_field(self):
        """验证 Task 有 task_type 字段"""
        assert hasattr(Task, 'task_type')

    def test_task_has_comment_field(self):
        """验证 Task 有 comment 字段"""
        assert hasattr(Task, 'comment')

    def test_task_type_default_value(self):
        """验证 task_type 默认值"""
        # 检查列的默认值
        column = Task.__table__.columns['task_type']
        assert column.default is not None or column.server_default is not None

    def test_task_comment_max_length(self):
        """验证 comment 字段长度限制"""
        column = Task.__table__.columns['comment']
        # 检查字符串长度
        assert column.type.length == 500


class TestWorkflowOperationLogIntegration:
    """集成测试"""

    def test_models_can_be_instantiated(self):
        """验证模型可以被实例化"""
        # 这只是验证模型定义是否正确
        try:
            log = WorkflowOperationLog(
                tenant_id=1,
                process_instance_id=1,
                operation_type="SUBMIT",
                operator_id=1,
            )
            assert log is not None
        except Exception as e:
            pytest.fail(f"Failed to instantiate WorkflowOperationLog: {e}")

    def test_process_instance_with_snapshot(self):
        """验证 ProcessInstance 可以存储快照"""
        try:
            process = ProcessInstance(
                tenant_id=1,
                form_id=1,
                form_version_id=1,
                submission_id=1,
                flow_definition_id=1,
                form_data_snapshot={"key": "value"},
            )
            assert process.form_data_snapshot == {"key": "value"}
        except Exception as e:
            pytest.fail(f"Failed to create ProcessInstance with snapshot: {e}")

    def test_task_with_extended_fields(self):
        """验证 Task 可以使用扩展字段"""
        try:
            task = Task(
                tenant_id=1,
                process_instance_id=1,
                node_id=1,
                task_type="cc",
                comment="Test comment",
            )
            assert task.task_type == "cc"
            assert task.comment == "Test comment"
        except Exception as e:
            pytest.fail(f"Failed to create Task with extended fields: {e}")
