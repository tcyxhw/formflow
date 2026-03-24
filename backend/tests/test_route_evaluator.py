"""
路由评估器单元测试 - 验证旧格式和新格式的兼容性

测试覆盖：
1. 旧格式（RouteRule）的条件评估
2. 新格式（设计格式）的条件评估
3. 格式检测逻辑
4. 向后兼容性
"""
import pytest
from app.services.route_evaluator import RouteEvaluator


class TestRouteEvaluatorFormatDetection:
    """测试格式检测逻辑"""

    def test_detect_new_format_rule(self):
        """测试检测新格式 RULE"""
        condition = {
            "type": "RULE",
            "fieldKey": "amount",
            "operator": "GREATER_THAN",
            "value": 1000,
            "fieldType": "NUMBER"
        }
        assert RouteEvaluator._is_design_format(condition) is True

    def test_detect_new_format_group(self):
        """测试检测新格式 GROUP"""
        condition = {
            "type": "GROUP",
            "logic": "AND",
            "children": []
        }
        assert RouteEvaluator._is_design_format(condition) is True

    def test_detect_old_format_with_field(self):
        """测试检测旧格式（包含 field）"""
        condition = {
            "field": "amount",
            "operator": "gt",
            "value": 1000
        }
        assert RouteEvaluator._is_design_format(condition) is False

    def test_detect_old_format_with_logic(self):
        """测试检测旧格式（包含 logic）"""
        condition = {
            "logic": "and",
            "rules": [
                {"field": "amount", "operator": "gt", "value": 1000}
            ]
        }
        assert RouteEvaluator._is_design_format(condition) is False

    def test_detect_old_format_with_operator(self):
        """测试检测旧格式（包含 operator）"""
        condition = {
            "operator": "equals",
            "value": "approved"
        }
        assert RouteEvaluator._is_design_format(condition) is False

    def test_detect_old_format_with_rules(self):
        """测试检测旧格式（包含 rules）"""
        condition = {
            "rules": [
                {"field": "status", "operator": "equals", "value": "approved"}
            ]
        }
        assert RouteEvaluator._is_design_format(condition) is False

    def test_detect_non_dict_returns_false(self):
        """测试非字典类型返回 False"""
        assert RouteEvaluator._is_design_format(None) is False
        assert RouteEvaluator._is_design_format([]) is False
        assert RouteEvaluator._is_design_format("string") is False


class TestRouteEvaluatorOldFormat:
    """测试旧格式（RouteRule）的条件评估"""

    def test_simple_equality_old_format(self):
        """测试旧格式简单相等条件"""
        condition = {
            "field": "status",
            "operator": "equals",
            "value": "approved"
        }
        context = {"status": "approved"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"status": "rejected"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_not_equals_old_format(self):
        """测试旧格式不相等条件"""
        condition = {
            "field": "status",
            "operator": "not_equals",
            "value": "rejected"
        }
        context = {"status": "approved"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"status": "rejected"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_greater_than_old_format(self):
        """测试旧格式大于条件"""
        condition = {
            "field": "amount",
            "operator": "gt",
            "value": 1000
        }
        context = {"amount": 1500}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 500}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_less_than_old_format(self):
        """测试旧格式小于条件"""
        condition = {
            "field": "amount",
            "operator": "lt",
            "value": 1000
        }
        context = {"amount": 500}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 1500}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_in_operator_old_format(self):
        """测试旧格式 IN 操作符"""
        condition = {
            "field": "status",
            "operator": "in",
            "value": ["approved", "pending"]
        }
        context = {"status": "approved"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"status": "rejected"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_contains_old_format(self):
        """测试旧格式 CONTAINS 操作符"""
        condition = {
            "field": "tags",
            "operator": "contains",
            "value": "urgent"
        }
        context = {"tags": ["urgent", "important"]}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"tags": ["normal"]}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_and_logic_old_format(self):
        """测试旧格式 AND 逻辑"""
        condition = {
            "logic": "and",
            "rules": [
                {"field": "amount", "operator": "gt", "value": 1000},
                {"field": "status", "operator": "equals", "value": "pending"}
            ]
        }
        context = {"amount": 1500, "status": "pending"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 500, "status": "pending"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_or_logic_old_format(self):
        """测试旧格式 OR 逻辑"""
        condition = {
            "logic": "or",
            "rules": [
                {"field": "amount", "operator": "gt", "value": 5000},
                {"field": "status", "operator": "equals", "value": "urgent"}
            ]
        }
        context = {"amount": 1500, "status": "urgent"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 1500, "status": "normal"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_nested_rules_old_format(self):
        """测试旧格式嵌套规则"""
        condition = {
            "logic": "and",
            "rules": [
                {"field": "amount", "operator": "gt", "value": 1000},
                {
                    "logic": "or",
                    "rules": [
                        {"field": "status", "operator": "equals", "value": "urgent"},
                        {"field": "status", "operator": "equals", "value": "high"}
                    ]
                }
            ]
        }
        context = {"amount": 1500, "status": "urgent"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 1500, "status": "normal"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_nested_field_access_old_format(self):
        """测试旧格式嵌套字段访问"""
        condition = {
            "field": "user.department",
            "operator": "equals",
            "value": "finance"
        }
        context = {"user": {"department": "finance"}}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"user": {"department": "hr"}}
        assert RouteEvaluator.evaluate(condition, context) is False


class TestRouteEvaluatorNewFormat:
    """测试新格式（设计格式）的条件评估"""

    def test_simple_rule_new_format(self):
        """测试新格式简单规则"""
        condition = {
            "type": "RULE",
            "fieldKey": "status",
            "operator": "EQUALS",
            "value": "approved",
            "fieldType": "TEXT"
        }
        context = {"status": "approved"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"status": "rejected"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_greater_than_new_format(self):
        """测试新格式大于条件"""
        condition = {
            "type": "RULE",
            "fieldKey": "amount",
            "operator": "GREATER_THAN",
            "value": 1000,
            "fieldType": "NUMBER"
        }
        context = {"amount": 1500}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 500}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_less_than_new_format(self):
        """测试新格式小于条件"""
        condition = {
            "type": "RULE",
            "fieldKey": "amount",
            "operator": "LESS_THAN",
            "value": 1000,
            "fieldType": "NUMBER"
        }
        context = {"amount": 500}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 1500}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_between_new_format(self):
        """测试新格式 BETWEEN 操作符"""
        condition = {
            "type": "RULE",
            "fieldKey": "amount",
            "operator": "BETWEEN",
            "value": [1000, 5000],
            "fieldType": "NUMBER"
        }
        context = {"amount": 3000}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 500}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_in_operator_new_format(self):
        """测试新格式 IN 操作符"""
        condition = {
            "type": "RULE",
            "fieldKey": "status",
            "operator": "IN",
            "value": ["approved", "pending"],
            "fieldType": "TEXT"
        }
        context = {"status": "approved"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"status": "rejected"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_contains_new_format(self):
        """测试新格式 CONTAINS 操作符"""
        condition = {
            "type": "RULE",
            "fieldKey": "description",
            "operator": "CONTAINS",
            "value": "urgent",
            "fieldType": "TEXT"
        }
        context = {"description": "This is urgent"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"description": "This is normal"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_and_group_new_format(self):
        """测试新格式 AND 组"""
        condition = {
            "type": "GROUP",
            "logic": "AND",
            "children": [
                {
                    "type": "RULE",
                    "fieldKey": "amount",
                    "operator": "GREATER_THAN",
                    "value": 1000,
                    "fieldType": "NUMBER"
                },
                {
                    "type": "RULE",
                    "fieldKey": "status",
                    "operator": "EQUALS",
                    "value": "pending",
                    "fieldType": "TEXT"
                }
            ]
        }
        context = {"amount": 1500, "status": "pending"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 500, "status": "pending"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_or_group_new_format(self):
        """测试新格式 OR 组"""
        condition = {
            "type": "GROUP",
            "logic": "OR",
            "children": [
                {
                    "type": "RULE",
                    "fieldKey": "amount",
                    "operator": "GREATER_THAN",
                    "value": 5000,
                    "fieldType": "NUMBER"
                },
                {
                    "type": "RULE",
                    "fieldKey": "status",
                    "operator": "EQUALS",
                    "value": "urgent",
                    "fieldType": "TEXT"
                }
            ]
        }
        context = {"amount": 1500, "status": "urgent"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 1500, "status": "normal"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_nested_groups_new_format(self):
        """测试新格式嵌套组"""
        condition = {
            "type": "GROUP",
            "logic": "AND",
            "children": [
                {
                    "type": "RULE",
                    "fieldKey": "amount",
                    "operator": "GREATER_THAN",
                    "value": 1000,
                    "fieldType": "NUMBER"
                },
                {
                    "type": "GROUP",
                    "logic": "OR",
                    "children": [
                        {
                            "type": "RULE",
                            "fieldKey": "status",
                            "operator": "EQUALS",
                            "value": "urgent",
                            "fieldType": "TEXT"
                        },
                        {
                            "type": "RULE",
                            "fieldKey": "status",
                            "operator": "EQUALS",
                            "value": "high",
                            "fieldType": "TEXT"
                        }
                    ]
                }
            ]
        }
        context = {"amount": 1500, "status": "urgent"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 1500, "status": "normal"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_has_any_new_format(self):
        """测试新格式 HAS_ANY 操作符"""
        condition = {
            "type": "RULE",
            "fieldKey": "tags",
            "operator": "HAS_ANY",
            "value": ["urgent", "important"],
            "fieldType": "MULTI_SELECT"
        }
        context = {"tags": ["urgent", "normal"]}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"tags": ["normal", "low"]}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_is_empty_new_format(self):
        """测试新格式 IS_EMPTY 操作符"""
        condition = {
            "type": "RULE",
            "fieldKey": "notes",
            "operator": "IS_EMPTY",
            "value": None,
            "fieldType": "TEXT"
        }
        context = {"notes": None}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"notes": "some text"}
        assert RouteEvaluator.evaluate(condition, context) is False


class TestRouteEvaluatorBackwardCompatibility:
    """测试向后兼容性"""

    def test_none_condition_returns_true(self):
        """测试 None 条件返回 True"""
        assert RouteEvaluator.evaluate(None, {}) is True

    def test_empty_dict_condition_returns_true(self):
        """测试空字典条件返回 True"""
        assert RouteEvaluator.evaluate({}, {}) is True

    def test_invalid_old_format_returns_false(self):
        """测试无效的旧格式返回 False"""
        condition = {
            "field": "amount",
            "operator": "invalid_op",
            "value": 1000
        }
        context = {"amount": 1500}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_missing_field_old_format_returns_false(self):
        """测试缺少字段的旧格式返回 False"""
        condition = {
            "field": "missing_field",
            "operator": "equals",
            "value": "test"
        }
        context = {"other_field": "test"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_missing_field_new_format_returns_false(self):
        """测试缺少字段的新格式返回 False"""
        condition = {
            "type": "RULE",
            "fieldKey": "missing_field",
            "operator": "EQUALS",
            "value": "test",
            "fieldType": "TEXT"
        }
        context = {"other_field": "test"}
        assert RouteEvaluator.evaluate(condition, context) is False


class TestRouteEvaluatorApprovalScenarios:
    """测试审批流程场景"""

    def test_amount_based_routing_old_format(self):
        """测试基于金额的路由（旧格式）"""
        # 大于 5000 元走财务审批
        condition = {
            "field": "amount",
            "operator": "gt",
            "value": 5000
        }
        context = {"amount": 6000}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 3000}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_amount_based_routing_new_format(self):
        """测试基于金额的路由（新格式）"""
        # 大于 5000 元走财务审批
        condition = {
            "type": "RULE",
            "fieldKey": "amount",
            "operator": "GREATER_THAN",
            "value": 5000,
            "fieldType": "NUMBER"
        }
        context = {"amount": 6000}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 3000}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_complex_approval_routing_old_format(self):
        """测试复杂审批路由（旧格式）"""
        # 金额 > 1000 且状态为 pending
        condition = {
            "logic": "and",
            "rules": [
                {"field": "amount", "operator": "gt", "value": 1000},
                {"field": "status", "operator": "equals", "value": "pending"}
            ]
        }
        context = {"amount": 1500, "status": "pending"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 500, "status": "pending"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_complex_approval_routing_new_format(self):
        """测试复杂审批路由（新格式）"""
        # 金额 > 1000 且状态为 pending
        condition = {
            "type": "GROUP",
            "logic": "AND",
            "children": [
                {
                    "type": "RULE",
                    "fieldKey": "amount",
                    "operator": "GREATER_THAN",
                    "value": 1000,
                    "fieldType": "NUMBER"
                },
                {
                    "type": "RULE",
                    "fieldKey": "status",
                    "operator": "EQUALS",
                    "value": "pending",
                    "fieldType": "TEXT"
                }
            ]
        }
        context = {"amount": 1500, "status": "pending"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 500, "status": "pending"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_multi_level_approval_old_format(self):
        """测试多级审批（旧格式）"""
        # (金额 > 5000 或 部门 = finance) 且 状态 = pending
        condition = {
            "logic": "and",
            "rules": [
                {
                    "logic": "or",
                    "rules": [
                        {"field": "amount", "operator": "gt", "value": 5000},
                        {"field": "department", "operator": "equals", "value": "finance"}
                    ]
                },
                {"field": "status", "operator": "equals", "value": "pending"}
            ]
        }
        context = {"amount": 6000, "department": "hr", "status": "pending"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 3000, "department": "hr", "status": "pending"}
        assert RouteEvaluator.evaluate(condition, context) is False

    def test_multi_level_approval_new_format(self):
        """测试多级审批（新格式）"""
        # (金额 > 5000 或 部门 = finance) 且 状态 = pending
        condition = {
            "type": "GROUP",
            "logic": "AND",
            "children": [
                {
                    "type": "GROUP",
                    "logic": "OR",
                    "children": [
                        {
                            "type": "RULE",
                            "fieldKey": "amount",
                            "operator": "GREATER_THAN",
                            "value": 5000,
                            "fieldType": "NUMBER"
                        },
                        {
                            "type": "RULE",
                            "fieldKey": "department",
                            "operator": "EQUALS",
                            "value": "finance",
                            "fieldType": "TEXT"
                        }
                    ]
                },
                {
                    "type": "RULE",
                    "fieldKey": "status",
                    "operator": "EQUALS",
                    "value": "pending",
                    "fieldType": "TEXT"
                }
            ]
        }
        context = {"amount": 6000, "department": "hr", "status": "pending"}
        assert RouteEvaluator.evaluate(condition, context) is True

        context = {"amount": 3000, "department": "hr", "status": "pending"}
        assert RouteEvaluator.evaluate(condition, context) is False
