"""
条件评估器单元测试
"""
import pytest
from app.services.condition_evaluator import ConditionEvaluator, evaluate_flow_condition


class TestConditionEvaluator:
    """条件评估器测试"""

    def test_simple_equality(self):
        """测试简单相等条件"""
        condition = {"==": [{"var": "amount"}, 1000]}
        data = {"amount": 1000}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"amount": 500}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

    def test_inequality(self):
        """测试不相等条件"""
        condition = {"!=": [{"var": "status"}, "rejected"]}
        data = {"status": "approved"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"status": "rejected"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

    def test_greater_than(self):
        """测试大于条件"""
        condition = {">": [{"var": "amount"}, 1000]}
        data = {"amount": 1500}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"amount": 500}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

    def test_less_than(self):
        """测试小于条件"""
        condition = {"<": [{"var": "amount"}, 1000]}
        data = {"amount": 500}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"amount": 1500}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

    def test_greater_equal(self):
        """测试大于等于条件"""
        condition = {">=": [{"var": "amount"}, 1000]}
        data = {"amount": 1000}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"amount": 1500}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"amount": 500}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

    def test_less_equal(self):
        """测试小于等于条件"""
        condition = {"<=": [{"var": "amount"}, 1000]}
        data = {"amount": 1000}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"amount": 500}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"amount": 1500}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

    def test_and_logic(self):
        """测试 AND 逻辑"""
        condition = {
            "and": [
                {"==": [{"var": "amount"}, 1000]},
                {"==": [{"var": "department"}, "sales"]}
            ]
        }
        data = {"amount": 1000, "department": "sales"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"amount": 1000, "department": "hr"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

    def test_or_logic(self):
        """测试 OR 逻辑"""
        condition = {
            "or": [
                {"==": [{"var": "status"}, "approved"]},
                {"==": [{"var": "status"}, "pending"]}
            ]
        }
        data = {"status": "approved"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"status": "pending"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"status": "rejected"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

    def test_not_logic(self):
        """测试 NOT 逻辑"""
        condition = {
            "!": {"==": [{"var": "status"}, "rejected"]}
        }
        data = {"status": "approved"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"status": "rejected"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

    def test_string_contains(self):
        """测试字符串包含条件"""
        condition = {"in": ["admin", {"var": "roles"}]}
        data = {"roles": "admin,user,guest"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"roles": "user,guest"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

    def test_string_starts_with(self):
        """测试字符串开头条件"""
        condition = {"startsWith": [{"var": "email"}, "admin"]}
        data = {"email": "admin@example.com"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"email": "user@example.com"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

    def test_string_ends_with(self):
        """测试字符串结尾条件"""
        condition = {"endsWith": [{"var": "email"}, "@example.com"]}
        data = {"email": "user@example.com"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"email": "user@other.com"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

    def test_complex_nested_condition(self):
        """测试复杂嵌套条件"""
        condition = {
            "and": [
                {">": [{"var": "amount"}, 1000]},
                {
                    "or": [
                        {"==": [{"var": "department"}, "sales"]},
                        {"==": [{"var": "department"}, "marketing"]}
                    ]
                }
            ]
        }
        data = {"amount": 1500, "department": "sales"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is True

        data = {"amount": 500, "department": "sales"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

        data = {"amount": 1500, "department": "hr"}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

    def test_missing_field(self):
        """测试缺失字段"""
        condition = {"==": [{"var": "amount"}, 1000]}
        data = {}
        assert ConditionEvaluator.evaluate_condition(condition, data) is False

    def test_none_condition(self):
        """测试 None 条件"""
        data = {"amount": 1000}
        assert ConditionEvaluator.evaluate_condition(None, data) is True

    def test_evaluate_conditions_and(self):
        """测试多条件 AND 逻辑"""
        rules = [
            {"==": [{"var": "amount"}, 1000]},
            {"==": [{"var": "department"}, "sales"]}
        ]
        data = {"amount": 1000, "department": "sales"}
        assert ConditionEvaluator.evaluate_conditions(rules, "AND", data) is True

        data = {"amount": 1000, "department": "hr"}
        assert ConditionEvaluator.evaluate_conditions(rules, "AND", data) is False

    def test_evaluate_conditions_or(self):
        """测试多条件 OR 逻辑"""
        rules = [
            {"==": [{"var": "status"}, "approved"]},
            {"==": [{"var": "status"}, "pending"]}
        ]
        data = {"status": "approved"}
        assert ConditionEvaluator.evaluate_conditions(rules, "OR", data) is True

        data = {"status": "rejected"}
        assert ConditionEvaluator.evaluate_conditions(rules, "OR", data) is False

    def test_evaluate_flow_condition_none(self):
        """测试流程条件评估 - None 条件"""
        data = {"amount": 1000}
        assert evaluate_flow_condition(None, data) is True

    def test_evaluate_flow_condition_valid(self):
        """测试流程条件评估 - 有效条件"""
        condition = {">": [{"var": "amount"}, 1000]}
        data = {"amount": 1500}
        assert evaluate_flow_condition(condition, data) is True

    def test_evaluate_flow_condition_invalid(self):
        """测试流程条件评估 - 无效条件"""
        condition = {">": [{"var": "amount"}, 1000]}
        data = {"amount": 500}
        assert evaluate_flow_condition(condition, data) is False

    def test_evaluate_flow_condition_error(self):
        """测试流程条件评估 - 错误处理"""
        # 格式错误的条件应该返回 False
        condition = {"invalid_operator": [{"var": "amount"}, 1000]}
        data = {"amount": 1000}
        assert evaluate_flow_condition(condition, data) is False


class TestApprovalFlowScenarios:
    """审批流程场景测试"""

    def test_amount_based_approval_routing(self):
        """测试基于金额的审批路由"""
        # 场景：金额 < 1000 -> 直接批准
        condition_direct = {"<": [{"var": "amount"}, 1000]}
        assert ConditionEvaluator.evaluate_condition(condition_direct, {"amount": 500}) is True
        assert ConditionEvaluator.evaluate_condition(condition_direct, {"amount": 1500}) is False

        # 场景：1000 <= 金额 < 10000 -> 部门经理审批
        condition_manager = {
            "and": [
                {">=": [{"var": "amount"}, 1000]},
                {"<": [{"var": "amount"}, 10000]}
            ]
        }
        assert ConditionEvaluator.evaluate_condition(condition_manager, {"amount": 5000}) is True
        assert ConditionEvaluator.evaluate_condition(condition_manager, {"amount": 500}) is False
        assert ConditionEvaluator.evaluate_condition(condition_manager, {"amount": 15000}) is False

        # 场景：金额 >= 10000 -> 总经理审批
        condition_director = {">=": [{"var": "amount"}, 10000]}
        assert ConditionEvaluator.evaluate_condition(condition_director, {"amount": 15000}) is True
        assert ConditionEvaluator.evaluate_condition(condition_director, {"amount": 5000}) is False

    def test_department_based_approval(self):
        """测试基于部门的审批"""
        # 销售部门需要特殊审批
        condition = {"==": [{"var": "department"}, "sales"]}
        assert ConditionEvaluator.evaluate_condition(condition, {"department": "sales"}) is True
        assert ConditionEvaluator.evaluate_condition(condition, {"department": "hr"}) is False

    def test_combined_conditions(self):
        """测试组合条件"""
        # 销售部门且金额 > 5000 需要总经理审批
        condition = {
            "and": [
                {"==": [{"var": "department"}, "sales"]},
                {">": [{"var": "amount"}, 5000]}
            ]
        }
        assert ConditionEvaluator.evaluate_condition(
            condition,
            {"department": "sales", "amount": 6000}
        ) is True
        assert ConditionEvaluator.evaluate_condition(
            condition,
            {"department": "sales", "amount": 3000}
        ) is False
        assert ConditionEvaluator.evaluate_condition(
            condition,
            {"department": "hr", "amount": 6000}
        ) is False
