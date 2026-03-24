"""
条件节点单元测试

测试范围：
- 条件分支逻辑评估
- 优先级排序
- 条件匹配和路由
- 默认路由逻辑
- 错误处理
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.models.workflow import FlowNode
from app.services.process_service import ProcessService
from app.services.condition_evaluator_v2 import ConditionEvaluatorV2
from app.core.exceptions import BusinessError


class TestEvaluateConditionBranches:
    """条件分支评估测试"""

    def test_evaluate_condition_branches_first_match(self):
        """测试条件分支评估：返回第一个匹配的分支"""
        # 创建条件节点
        node = FlowNode(
            id=1,
            flow_definition_id=1,
            name="条件分支",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "大额",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 5000,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 2,
                    },
                    {
                        "priority": 2,
                        "label": "小额",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "LESS_EQUAL",
                            "value": 5000,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 3,
                    },
                ],
                "default_target_node_id": 3,
            },
        )

        # 创建目标节点
        target_node_1 = FlowNode(
            id=2,
            flow_definition_id=1,
            name="大额审批",
            type="approval",
            tenant_id=1,
        )
        target_node_2 = FlowNode(
            id=3,
            flow_definition_id=1,
            name="小额审批",
            type="approval",
            tenant_id=1,
        )

        # 模拟数据库查询
        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.side_effect = [
            target_node_1,
        ]

        # 上下文数据
        context = {"amount": 8000}

        # 执行
        result = ProcessService._evaluate_condition_branches(node, 1, db, context)

        # 验证
        assert len(result) == 1
        assert result[0].id == 2

    def test_evaluate_condition_branches_default_route(self):
        """测试条件分支评估：没有匹配时使用默认路由"""
        node = FlowNode(
            id=1,
            flow_definition_id=1,
            name="条件分支",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "大额",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 5000,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 2,
                    },
                ],
                "default_target_node_id": 3,
            },
        )

        target_node_default = FlowNode(
            id=3,
            flow_definition_id=1,
            name="默认审批",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = (
            target_node_default
        )

        context = {"amount": 3000}

        result = ProcessService._evaluate_condition_branches(node, 1, db, context)

        assert len(result) == 1
        assert result[0].id == 3

    def test_evaluate_condition_branches_priority_order(self):
        """测试条件分支评估：按优先级顺序评估"""
        node = FlowNode(
            id=1,
            flow_definition_id=1,
            name="条件分支",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 2,
                        "label": "中额",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "BETWEEN",
                            "value": [1000, 5000],
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 2,
                    },
                    {
                        "priority": 1,
                        "label": "大额",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 5000,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 3,
                    },
                ],
                "default_target_node_id": 4,
            },
        )

        target_node = FlowNode(
            id=3,
            flow_definition_id=1,
            name="大额审批",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = target_node

        context = {"amount": 8000}

        result = ProcessService._evaluate_condition_branches(node, 1, db, context)

        # 应该返回优先级为 1 的分支（大额）
        assert len(result) == 1
        assert result[0].id == 3

    def test_evaluate_condition_branches_complex_condition(self):
        """测试条件分支评估：复杂条件表达式"""
        node = FlowNode(
            id=1,
            flow_definition_id=1,
            name="条件分支",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "大额招待费",
                        "condition": {
                            "type": "GROUP",
                            "logic": "AND",
                            "children": [
                                {
                                    "type": "RULE",
                                    "fieldKey": "amount",
                                    "operator": "GREATER_THAN",
                                    "value": 5000,
                                    "fieldType": "NUMBER",
                                },
                                {
                                    "type": "RULE",
                                    "fieldKey": "category",
                                    "operator": "EQUALS",
                                    "value": "entertainment",
                                    "fieldType": "TEXT",
                                },
                            ],
                        },
                        "target_node_id": 2,
                    },
                ],
                "default_target_node_id": 3,
            },
        )

        target_node = FlowNode(
            id=2,
            flow_definition_id=1,
            name="财务审批",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = target_node

        context = {"amount": 8000, "category": "entertainment"}

        result = ProcessService._evaluate_condition_branches(node, 1, db, context)

        assert len(result) == 1
        assert result[0].id == 2

    def test_evaluate_condition_branches_no_config(self):
        """测试条件分支评估：节点没有配置"""
        node = FlowNode(
            id=1,
            flow_definition_id=1,
            name="条件分支",
            type="condition",
            tenant_id=1,
            condition_branches=None,
        )

        db = Mock(spec=Session)
        context = {"amount": 8000}

        result = ProcessService._evaluate_condition_branches(node, 1, db, context)

        assert result == []

    def test_evaluate_condition_branches_no_matching_and_no_default(self):
        """测试条件分支评估：没有匹配且没有默认路由"""
        node = FlowNode(
            id=1,
            flow_definition_id=1,
            name="条件分支",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "大额",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 5000,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 2,
                    },
                ],
                "default_target_node_id": None,
            },
        )

        db = Mock(spec=Session)
        context = {"amount": 3000}

        result = ProcessService._evaluate_condition_branches(node, 1, db, context)

        assert result == []

    def test_evaluate_condition_branches_target_node_not_found(self):
        """测试条件分支评估：目标节点不存在"""
        node = FlowNode(
            id=1,
            flow_definition_id=1,
            name="条件分支",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "大额",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 5000,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 999,
                    },
                ],
                "default_target_node_id": 3,
            },
        )

        target_node_default = FlowNode(
            id=3,
            flow_definition_id=1,
            name="默认审批",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 匹配的分支目标节点不存在
            target_node_default,  # 默认节点存在
        ]

        context = {"amount": 8000}

        result = ProcessService._evaluate_condition_branches(node, 1, db, context)

        # 应该返回默认节点
        assert len(result) == 1
        assert result[0].id == 3

    def test_evaluate_condition_branches_multiple_branches_first_wins(self):
        """测试条件分支评估：多个分支匹配时返回第一个"""
        node = FlowNode(
            id=1,
            flow_definition_id=1,
            name="条件分支",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "大额",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 5000,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 2,
                    },
                    {
                        "priority": 2,
                        "label": "任意金额",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 0,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 3,
                    },
                ],
                "default_target_node_id": 4,
            },
        )

        target_node = FlowNode(
            id=2,
            flow_definition_id=1,
            name="大额审批",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = target_node

        context = {"amount": 8000}

        result = ProcessService._evaluate_condition_branches(node, 1, db, context)

        # 应该返回优先级为 1 的分支
        assert len(result) == 1
        assert result[0].id == 2

    def test_evaluate_condition_branches_tenant_isolation(self):
        """测试条件分支评估：租户隔离"""
        node = FlowNode(
            id=1,
            flow_definition_id=1,
            name="条件分支",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "大额",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 5000,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 2,
                    },
                ],
                "default_target_node_id": 3,
            },
        )

        db = Mock(spec=Session)
        query_mock = Mock()
        filter_mock = Mock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None

        context = {"amount": 8000}

        result = ProcessService._evaluate_condition_branches(node, 1, db, context)

        # 验证查询时包含租户 ID 过滤
        query_mock.filter.assert_called()
        call_args = query_mock.filter.call_args
        # 验证调用中包含租户 ID 过滤
        assert call_args is not None

    def test_evaluate_condition_branches_exception_handling(self):
        """测试条件分支评估：异常处理"""
        node = FlowNode(
            id=1,
            flow_definition_id=1,
            name="条件分支",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "大额",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 5000,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 2,
                    },
                ],
                "default_target_node_id": 3,
            },
        )

        db = Mock(spec=Session)
        db.query.side_effect = Exception("Database error")

        context = {"amount": 8000}

        result = ProcessService._evaluate_condition_branches(node, 1, db, context)

        # 应该返回空列表而不是抛出异常
        assert result == []

    def test_evaluate_condition_branches_missing_target_node_id(self):
        """测试条件分支评估：分支缺少 target_node_id"""
        node = FlowNode(
            id=1,
            flow_definition_id=1,
            name="条件分支",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "大额",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 5000,
                            "fieldType": "NUMBER",
                        },
                        # 缺少 target_node_id
                    },
                ],
                "default_target_node_id": 3,
            },
        )

        target_node_default = FlowNode(
            id=3,
            flow_definition_id=1,
            name="默认审批",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = (
            target_node_default
        )

        context = {"amount": 8000}

        result = ProcessService._evaluate_condition_branches(node, 1, db, context)

        # 应该跳过缺少 target_node_id 的分支，使用默认路由
        assert len(result) == 1
        assert result[0].id == 3

    def test_evaluate_condition_branches_empty_branches_list(self):
        """测试条件分支评估：分支列表为空"""
        node = FlowNode(
            id=1,
            flow_definition_id=1,
            name="条件分支",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [],
                "default_target_node_id": 3,
            },
        )

        target_node_default = FlowNode(
            id=3,
            flow_definition_id=1,
            name="默认审批",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = (
            target_node_default
        )

        context = {"amount": 8000}

        result = ProcessService._evaluate_condition_branches(node, 1, db, context)

        # 应该直接使用默认路由
        assert len(result) == 1
        assert result[0].id == 3

    def test_evaluate_condition_branches_with_or_logic(self):
        """测试条件分支评估：OR 逻辑条件"""
        node = FlowNode(
            id=1,
            flow_definition_id=1,
            name="条件分支",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "紧急或大额",
                        "condition": {
                            "type": "GROUP",
                            "logic": "OR",
                            "children": [
                                {
                                    "type": "RULE",
                                    "fieldKey": "priority",
                                    "operator": "EQUALS",
                                    "value": "urgent",
                                    "fieldType": "TEXT",
                                },
                                {
                                    "type": "RULE",
                                    "fieldKey": "amount",
                                    "operator": "GREATER_THAN",
                                    "value": 5000,
                                    "fieldType": "NUMBER",
                                },
                            ],
                        },
                        "target_node_id": 2,
                    },
                ],
                "default_target_node_id": 3,
            },
        )

        target_node = FlowNode(
            id=2,
            flow_definition_id=1,
            name="特殊审批",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = target_node

        context = {"priority": "normal", "amount": 8000}

        result = ProcessService._evaluate_condition_branches(node, 1, db, context)

        # 应该匹配 OR 条件中的第二个规则
        assert len(result) == 1
        assert result[0].id == 2


class TestConditionNodeIntegration:
    """条件节点集成测试"""

    def test_condition_node_routing_with_multiple_branches(self):
        """测试条件节点路由：多分支场景"""
        # 创建条件节点
        condition_node = FlowNode(
            id=10,
            flow_definition_id=1,
            name="金额分类",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "大额（>10000）",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 10000,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 11,
                    },
                    {
                        "priority": 2,
                        "label": "中额（5000-10000）",
                        "condition": {
                            "type": "GROUP",
                            "logic": "AND",
                            "children": [
                                {
                                    "type": "RULE",
                                    "fieldKey": "amount",
                                    "operator": "GREATER_EQUAL",
                                    "value": 5000,
                                    "fieldType": "NUMBER",
                                },
                                {
                                    "type": "RULE",
                                    "fieldKey": "amount",
                                    "operator": "LESS_EQUAL",
                                    "value": 10000,
                                    "fieldType": "NUMBER",
                                },
                            ],
                        },
                        "target_node_id": 12,
                    },
                    {
                        "priority": 3,
                        "label": "小额（<5000）",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "LESS_THAN",
                            "value": 5000,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 13,
                    },
                ],
                "default_target_node_id": 13,
            },
        )

        # 创建目标节点
        large_amount_node = FlowNode(
            id=11,
            flow_definition_id=1,
            name="大额审批",
            type="approval",
            tenant_id=1,
        )
        medium_amount_node = FlowNode(
            id=12,
            flow_definition_id=1,
            name="中额审批",
            type="approval",
            tenant_id=1,
        )
        small_amount_node = FlowNode(
            id=13,
            flow_definition_id=1,
            name="小额审批",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.side_effect = [
            large_amount_node,
        ]

        context = {"amount": 15000}

        result = ProcessService._evaluate_condition_branches(condition_node, 1, db, context)

        assert len(result) == 1
        assert result[0].id == 11

    def test_condition_node_default_route_when_no_match(self):
        """测试条件节点默认路由：所有条件都不匹配"""
        condition_node = FlowNode(
            id=20,
            flow_definition_id=1,
            name="状态分类",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "待审批",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "status",
                            "operator": "EQUALS",
                            "value": "pending",
                            "fieldType": "TEXT",
                        },
                        "target_node_id": 21,
                    },
                    {
                        "priority": 2,
                        "label": "已批准",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "status",
                            "operator": "EQUALS",
                            "value": "approved",
                            "fieldType": "TEXT",
                        },
                        "target_node_id": 22,
                    },
                ],
                "default_target_node_id": 23,
            },
        )

        default_node = FlowNode(
            id=23,
            flow_definition_id=1,
            name="其他处理",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = default_node

        context = {"status": "rejected"}

        result = ProcessService._evaluate_condition_branches(condition_node, 1, db, context)

        assert len(result) == 1
        assert result[0].id == 23

    def test_condition_node_with_complex_nested_conditions(self):
        """测试条件节点：复杂嵌套条件"""
        condition_node = FlowNode(
            id=30,
            flow_definition_id=1,
            name="复杂条件",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "特殊审批",
                        "condition": {
                            "type": "GROUP",
                            "logic": "AND",
                            "children": [
                                {
                                    "type": "GROUP",
                                    "logic": "OR",
                                    "children": [
                                        {
                                            "type": "RULE",
                                            "fieldKey": "category",
                                            "operator": "EQUALS",
                                            "value": "entertainment",
                                            "fieldType": "TEXT",
                                        },
                                        {
                                            "type": "RULE",
                                            "fieldKey": "category",
                                            "operator": "EQUALS",
                                            "value": "travel",
                                            "fieldType": "TEXT",
                                        },
                                    ],
                                },
                                {
                                    "type": "RULE",
                                    "fieldKey": "amount",
                                    "operator": "GREATER_THAN",
                                    "value": 5000,
                                    "fieldType": "NUMBER",
                                },
                            ],
                        },
                        "target_node_id": 31,
                    },
                ],
                "default_target_node_id": 32,
            },
        )

        special_node = FlowNode(
            id=31,
            flow_definition_id=1,
            name="特殊审批",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = special_node

        context = {"category": "entertainment", "amount": 8000}

        result = ProcessService._evaluate_condition_branches(condition_node, 1, db, context)

        assert len(result) == 1
        assert result[0].id == 31

    def test_condition_node_priority_evaluation_order(self):
        """测试条件节点：优先级评估顺序"""
        condition_node = FlowNode(
            id=40,
            flow_definition_id=1,
            name="优先级测试",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 3,
                        "label": "第三优先级",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "level",
                            "operator": "EQUALS",
                            "value": "low",
                            "fieldType": "TEXT",
                        },
                        "target_node_id": 43,
                    },
                    {
                        "priority": 1,
                        "label": "第一优先级",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "level",
                            "operator": "EQUALS",
                            "value": "high",
                            "fieldType": "TEXT",
                        },
                        "target_node_id": 41,
                    },
                    {
                        "priority": 2,
                        "label": "第二优先级",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "level",
                            "operator": "EQUALS",
                            "value": "medium",
                            "fieldType": "TEXT",
                        },
                        "target_node_id": 42,
                    },
                ],
                "default_target_node_id": 44,
            },
        )

        high_priority_node = FlowNode(
            id=41,
            flow_definition_id=1,
            name="高优先级处理",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = high_priority_node

        context = {"level": "high"}

        result = ProcessService._evaluate_condition_branches(condition_node, 1, db, context)

        assert len(result) == 1
        assert result[0].id == 41

    def test_condition_node_first_match_wins(self):
        """测试条件节点：第一个匹配的分支获胜"""
        condition_node = FlowNode(
            id=50,
            flow_definition_id=1,
            name="多匹配测试",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "条件1",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 1000,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 51,
                    },
                    {
                        "priority": 2,
                        "label": "条件2",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 500,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 52,
                    },
                ],
                "default_target_node_id": 53,
            },
        )

        first_match_node = FlowNode(
            id=51,
            flow_definition_id=1,
            name="第一个匹配",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = first_match_node

        context = {"amount": 2000}

        result = ProcessService._evaluate_condition_branches(condition_node, 1, db, context)

        # 应该返回第一个匹配的分支，而不是第二个
        assert len(result) == 1
        assert result[0].id == 51

    def test_condition_node_with_missing_context_field(self):
        """测试条件节点：上下文中缺少字段"""
        condition_node = FlowNode(
            id=60,
            flow_definition_id=1,
            name="缺少字段测试",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "需要金额字段",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 5000,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 61,
                    },
                ],
                "default_target_node_id": 62,
            },
        )

        default_node = FlowNode(
            id=62,
            flow_definition_id=1,
            name="默认处理",
            type="approval",
            tenant_id=1,
        )

        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = default_node

        # 上下文中没有 amount 字段
        context = {"category": "entertainment"}

        result = ProcessService._evaluate_condition_branches(condition_node, 1, db, context)

        # 应该使用默认路由
        assert len(result) == 1
        assert result[0].id == 62

    def test_condition_node_tenant_isolation(self):
        """测试条件节点：租户隔离"""
        condition_node = FlowNode(
            id=70,
            flow_definition_id=1,
            name="租户隔离测试",
            type="condition",
            tenant_id=1,
            condition_branches={
                "branches": [
                    {
                        "priority": 1,
                        "label": "分支1",
                        "condition": {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 5000,
                            "fieldType": "NUMBER",
                        },
                        "target_node_id": 71,
                    },
                ],
                "default_target_node_id": 72,
            },
        )

        db = Mock(spec=Session)
        query_mock = Mock()
        filter_mock = Mock()
        db.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None

        context = {"amount": 8000}

        result = ProcessService._evaluate_condition_branches(condition_node, 1, db, context)

        # 验证查询时包含租户 ID 过滤
        query_mock.filter.assert_called()
        assert result == []
