"""
驳回策略单元测试

模块用途: 测试驳回策略的实现，包括 TO_START 和 TO_PREVIOUS 两种策略
依赖配置: 无
数据流向: FlowNode + ProcessInstance + Task -> ProcessService._handle_rejection() -> 状态更新
函数清单:
    - _handle_rejection(): 处理驳回逻辑
    - _find_previous_approval_node(): 查找上一个审批节点
    - _cancel_pending_node_tasks(): 取消待处理任务
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.models.workflow import FlowNode, ProcessInstance, Task
from app.services.process_service import ProcessService


class TestHandleRejectionToStart:
    """TO_START 策略测试：驳回到发起人，流程结束"""

    def test_to_start_sets_process_state_to_canceled(self):
        """测试 TO_START 策略：流程状态变为 canceled"""
        process = ProcessInstance(
            id=1,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
            state="running",
            tenant_id=1,
        )

        node = FlowNode(
            id=2,
            flow_definition_id=1,
            name="审批节点",
            type="approval",
            tenant_id=1,
            reject_strategy="TO_START",
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.all.return_value = []

        ProcessService._handle_rejection(
            process=process,
            node=node,
            tenant_id=1,
            db=db,
        )

        assert process.state == "canceled"

    def test_to_start_cancels_pending_tasks(self):
        """测试 TO_START 策略：取消所有待处理任务"""
        process = ProcessInstance(
            id=1,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
            state="running",
            tenant_id=1,
        )

        node = FlowNode(
            id=2,
            flow_definition_id=1,
            name="审批节点",
            type="approval",
            tenant_id=1,
            reject_strategy="TO_START",
        )

        db = Mock(spec=Session)
        pending_tasks = [
            Task(id=1, process_instance_id=1, node_id=2, status="open", tenant_id=1),
            Task(id=2, process_instance_id=1, node_id=2, status="claimed", tenant_id=1),
        ]
        
        db.query.return_value.filter.return_value.all.return_value = pending_tasks

        ProcessService._handle_rejection(
            process=process,
            node=node,
            tenant_id=1,
            db=db,
        )

        for task in pending_tasks:
            assert task.status == "canceled"

    def test_to_start_updates_submission_status(self):
        """测试 TO_START 策略：更新提交记录状态"""
        process = ProcessInstance(
            id=1,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
            state="running",
            tenant_id=1,
        )

        node = FlowNode(
            id=2,
            flow_definition_id=1,
            name="审批节点",
            type="approval",
            tenant_id=1,
            reject_strategy="TO_START",
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(ProcessService, '_update_submission_status') as mock_update:
            ProcessService._handle_rejection(
                process=process,
                node=node,
                tenant_id=1,
                db=db,
            )
            
            mock_update.assert_called_once()
            call_args = mock_update.call_args
            assert call_args[1]['process'] == process
            assert call_args[1]['status'] == "rejected"


class TestHandleRejectionToPrevious:
    """TO_PREVIOUS 策略测试：驳回到上一个审批节点"""

    def test_to_previous_finds_and_redispatches_previous_node(self):
        """测试 TO_PREVIOUS 策略：找到上一个审批节点并重新分配"""
        process = ProcessInstance(
            id=1,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
            state="running",
            tenant_id=1,
        )

        current_node = FlowNode(
            id=3,
            flow_definition_id=1,
            name="第二审批",
            type="approval",
            tenant_id=1,
            reject_strategy="TO_PREVIOUS",
        )

        previous_node = FlowNode(
            id=2,
            flow_definition_id=1,
            name="第一审批",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        
        completed_task = Task(
            id=1,
            process_instance_id=1,
            node_id=2,
            status="completed",
            tenant_id=1,
            completed_at=datetime.now(),
        )
        
        query_mock = Mock()
        filter_mock = Mock()
        
        db.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        
        filter_mock.order_by.return_value.all.return_value = [completed_task]
        filter_mock.first.return_value = previous_node
        filter_mock.all.return_value = []

        with patch.object(ProcessService, '_dispatch_nodes') as mock_dispatch:
            ProcessService._handle_rejection(
                process=process,
                node=current_node,
                tenant_id=1,
                db=db,
            )
            
            mock_dispatch.assert_called_once()
            call_args = mock_dispatch.call_args
            assert call_args[1]['process'] == process
            assert call_args[1]['candidate_nodes'] == [previous_node]

    def test_to_previous_fallback_to_start_when_no_previous_node(self):
        """测试 TO_PREVIOUS 策略：没有上一个节点时降级为 TO_START"""
        process = ProcessInstance(
            id=1,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
            state="running",
            tenant_id=1,
        )

        current_node = FlowNode(
            id=2,
            flow_definition_id=1,
            name="第一审批",
            type="approval",
            tenant_id=1,
            reject_strategy="TO_PREVIOUS",
        )

        db = Mock(spec=Session)
        
        query_mock = Mock()
        filter_mock = Mock()
        
        db.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.order_by.return_value.all.return_value = []
        filter_mock.all.return_value = []

        ProcessService._handle_rejection(
            process=process,
            node=current_node,
            tenant_id=1,
            db=db,
        )

        assert process.state == "canceled"

    def test_to_previous_cancels_current_and_after_tasks(self):
        """测试 TO_PREVIOUS 策略：取消当前节点及之后的所有任务"""
        process = ProcessInstance(
            id=1,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
            state="running",
            tenant_id=1,
        )

        current_node = FlowNode(
            id=3,
            flow_definition_id=1,
            name="第二审批",
            type="approval",
            tenant_id=1,
            reject_strategy="TO_PREVIOUS",
        )

        previous_node = FlowNode(
            id=2,
            flow_definition_id=1,
            name="第一审批",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        
        completed_task = Task(
            id=1,
            process_instance_id=1,
            node_id=2,
            status="completed",
            tenant_id=1,
            completed_at=datetime.now(),
        )
        
        pending_task = Task(
            id=2,
            process_instance_id=1,
            node_id=3,
            status="open",
            tenant_id=1,
        )
        
        query_mock = Mock()
        filter_mock = Mock()
        
        db.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        
        filter_mock.order_by.return_value.all.return_value = [completed_task]
        filter_mock.first.return_value = previous_node
        filter_mock.all.return_value = [pending_task]

        with patch.object(ProcessService, '_dispatch_nodes'):
            ProcessService._handle_rejection(
                process=process,
                node=current_node,
                tenant_id=1,
                db=db,
            )
            
            assert pending_task.status == "canceled"


class TestFindPreviousApprovalNode:
    """查找上一个审批节点的测试"""

    def test_find_previous_node_success(self):
        """测试成功找到上一个审批节点"""
        process = ProcessInstance(
            id=1,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
            state="running",
            tenant_id=1,
        )

        current_node = FlowNode(
            id=3,
            flow_definition_id=1,
            name="第二审批",
            type="approval",
            tenant_id=1,
        )

        previous_node = FlowNode(
            id=2,
            flow_definition_id=1,
            name="第一审批",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        
        completed_task = Task(
            id=1,
            process_instance_id=1,
            node_id=2,
            status="completed",
            tenant_id=1,
            completed_at=datetime.now(),
        )
        
        query_mock = Mock()
        filter_mock = Mock()
        order_by_mock = Mock()
        
        db.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        
        order_by_mock.all.return_value = [completed_task]
        filter_mock.order_by.return_value = order_by_mock
        filter_mock.first.return_value = previous_node

        result = ProcessService._find_previous_approval_node(
            process=process,
            current_node=current_node,
            tenant_id=1,
            db=db,
        )

        assert result == previous_node

    def test_find_previous_node_no_completed_tasks(self):
        """测试没有已完成任务时返回 None"""
        process = ProcessInstance(
            id=1,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
            state="running",
            tenant_id=1,
        )

        current_node = FlowNode(
            id=2,
            flow_definition_id=1,
            name="第一审批",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        
        query_mock = Mock()
        filter_mock = Mock()
        order_by_mock = Mock()
        
        db.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.order_by.return_value = order_by_mock
        
        order_by_mock.all.return_value = []

        result = ProcessService._find_previous_approval_node(
            process=process,
            current_node=current_node,
            tenant_id=1,
            db=db,
        )

        assert result is None

    def test_find_previous_node_same_as_current(self):
        """测试上一个节点与当前节点相同时返回 None"""
        process = ProcessInstance(
            id=1,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
            state="running",
            tenant_id=1,
        )

        current_node = FlowNode(
            id=2,
            flow_definition_id=1,
            name="审批节点",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        
        completed_task = Task(
            id=1,
            process_instance_id=1,
            node_id=2,
            status="completed",
            tenant_id=1,
            completed_at=datetime.now(),
        )
        
        query_mock = Mock()
        filter_mock = Mock()
        order_by_mock = Mock()
        
        db.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.order_by.return_value = order_by_mock
        
        order_by_mock.all.return_value = [completed_task]
        filter_mock.first.return_value = current_node

        result = ProcessService._find_previous_approval_node(
            process=process,
            current_node=current_node,
            tenant_id=1,
            db=db,
        )

        assert result is None


class TestRejectStrategyDefaults:
    """驳回策略默认值测试"""

    def test_default_reject_strategy_is_to_start(self):
        """测试默认驳回策略是 TO_START"""
        process = ProcessInstance(
            id=1,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
            state="running",
            tenant_id=1,
        )

        node = FlowNode(
            id=2,
            flow_definition_id=1,
            name="审批节点",
            type="approval",
            tenant_id=1,
            reject_strategy=None,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.all.return_value = []

        ProcessService._handle_rejection(
            process=process,
            node=node,
            tenant_id=1,
            db=db,
        )

        assert process.state == "canceled"

    def test_empty_string_reject_strategy_defaults_to_to_start(self):
        """测试空字符串驳回策略默认为 TO_START"""
        process = ProcessInstance(
            id=1,
            form_id=1,
            form_version_id=1,
            submission_id=1,
            flow_definition_id=1,
            state="running",
            tenant_id=1,
        )

        node = FlowNode(
            id=2,
            flow_definition_id=1,
            name="审批节点",
            type="approval",
            tenant_id=1,
            reject_strategy="",
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.all.return_value = []

        ProcessService._handle_rejection(
            process=process,
            node=node,
            tenant_id=1,
            db=db,
        )

        assert process.state == "canceled"
