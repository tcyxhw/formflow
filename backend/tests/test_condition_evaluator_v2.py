"""
条件评估器 V2 单元测试
"""
import pytest
from datetime import datetime, date, timedelta
from app.services.condition_evaluator_v2 import ConditionEvaluatorV2, evaluate_condition_tree


class TestConditionEvaluatorV2:
    """条件评估器 V2 测试"""

    # ==================== 基础运算符测试 ====================

    def test_equals_operator(self):
        """测试 EQUALS 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'amount',
            'fieldType': 'NUMBER',
            'operator': 'EQUALS',
            'value': 1000
        }
        data = {'amount': 1000}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'amount': 2000}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_not_equals_operator(self):
        """测试 NOT_EQUALS 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'status',
            'fieldType': 'TEXT',
            'operator': 'NOT_EQUALS',
            'value': 'rejected'
        }
        data = {'status': 'approved'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'status': 'rejected'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_greater_than_operator(self):
        """测试 GREATER_THAN 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'amount',
            'fieldType': 'NUMBER',
            'operator': 'GREATER_THAN',
            'value': 1000
        }
        data = {'amount': 1500}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'amount': 500}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_greater_equal_operator(self):
        """测试 GREATER_EQUAL 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'amount',
            'fieldType': 'NUMBER',
            'operator': 'GREATER_EQUAL',
            'value': 1000
        }
        data = {'amount': 1000}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'amount': 1500}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'amount': 500}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_less_than_operator(self):
        """测试 LESS_THAN 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'amount',
            'fieldType': 'NUMBER',
            'operator': 'LESS_THAN',
            'value': 1000
        }
        data = {'amount': 500}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'amount': 1500}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_less_equal_operator(self):
        """测试 LESS_EQUAL 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'amount',
            'fieldType': 'NUMBER',
            'operator': 'LESS_EQUAL',
            'value': 1000
        }
        data = {'amount': 1000}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'amount': 500}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'amount': 1500}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    # ==================== 范围运算符测试 ====================

    def test_between_operator(self):
        """测试 BETWEEN 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'amount',
            'fieldType': 'NUMBER',
            'operator': 'BETWEEN',
            'value': [1000, 5000]
        }
        data = {'amount': 3000}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'amount': 1000}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'amount': 5000}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'amount': 500}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

        data = {'amount': 6000}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    # ==================== 字符串运算符测试 ====================

    def test_contains_operator(self):
        """测试 CONTAINS 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'description',
            'fieldType': 'TEXT',
            'operator': 'CONTAINS',
            'value': 'urgent'
        }
        data = {'description': 'This is urgent'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'description': 'This is normal'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_not_contains_operator(self):
        """测试 NOT_CONTAINS 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'description',
            'fieldType': 'TEXT',
            'operator': 'NOT_CONTAINS',
            'value': 'urgent'
        }
        data = {'description': 'This is normal'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'description': 'This is urgent'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    # ==================== 列表运算符测试 ====================

    def test_in_operator(self):
        """测试 IN 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'department',
            'fieldType': 'TEXT',
            'operator': 'IN',
            'value': ['HR', 'Finance', 'IT']
        }
        data = {'department': 'HR'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'department': 'Sales'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_not_in_operator(self):
        """测试 NOT_IN 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'department',
            'fieldType': 'TEXT',
            'operator': 'NOT_IN',
            'value': ['HR', 'Finance', 'IT']
        }
        data = {'department': 'Sales'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'department': 'HR'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    # ==================== 多选字段运算符测试 ====================

    def test_has_any_operator(self):
        """测试 HAS_ANY 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'tags',
            'fieldType': 'MULTI_SELECT',
            'operator': 'HAS_ANY',
            'value': ['urgent', 'important']
        }
        data = {'tags': ['urgent', 'normal']}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'tags': ['normal', 'routine']}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_has_all_operator(self):
        """测试 HAS_ALL 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'tags',
            'fieldType': 'MULTI_SELECT',
            'operator': 'HAS_ALL',
            'value': ['urgent', 'important']
        }
        data = {'tags': ['urgent', 'important', 'normal']}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'tags': ['urgent', 'normal']}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    # ==================== 空值检查运算符测试 ====================

    def test_is_empty_operator(self):
        """测试 IS_EMPTY 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'comment',
            'fieldType': 'TEXT',
            'operator': 'IS_EMPTY',
            'value': None
        }
        data = {'comment': None}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'comment': ''}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'comment': 'some text'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_is_not_empty_operator(self):
        """测试 IS_NOT_EMPTY 运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'comment',
            'fieldType': 'TEXT',
            'operator': 'IS_NOT_EMPTY',
            'value': None
        }
        data = {'comment': 'some text'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'comment': None}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

        data = {'comment': ''}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    # ==================== 日期运算符测试 ====================

    def test_date_before_now_operator(self):
        """测试 DATE_BEFORE_NOW 运算符"""
        today = datetime.now().date()
        past_date = today - timedelta(days=10)

        condition = {
            'type': 'RULE',
            'fieldKey': 'created_date',
            'fieldType': 'DATE',
            'operator': 'DATE_BEFORE_NOW',
            'value': 5
        }
        data = {'created_date': past_date}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        future_date = today + timedelta(days=10)
        data = {'created_date': future_date}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_date_after_now_operator(self):
        """测试 DATE_AFTER_NOW 运算符"""
        today = datetime.now().date()
        future_date = today + timedelta(days=10)

        condition = {
            'type': 'RULE',
            'fieldKey': 'deadline',
            'fieldType': 'DATE',
            'operator': 'DATE_AFTER_NOW',
            'value': 5
        }
        data = {'deadline': future_date}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        past_date = today - timedelta(days=10)
        data = {'deadline': past_date}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    # ==================== 类型转换测试 ====================

    def test_number_type_conversion(self):
        """测试数字类型转换"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'amount',
            'fieldType': 'NUMBER',
            'operator': 'GREATER_THAN',
            'value': 1000
        }
        # 字符串转换为数字
        data = {'amount': '1500'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

    def test_date_type_conversion(self):
        """测试日期类型转换"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'created_date',
            'fieldType': 'DATE',
            'operator': 'EQUALS',
            'value': '2024-01-15'
        }
        # 字符串转换为日期
        data = {'created_date': '2024-01-15'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

    def test_multi_select_type_conversion(self):
        """测试多选类型转换"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'tags',
            'fieldType': 'MULTI_SELECT',
            'operator': 'HAS_ANY',
            'value': ['urgent', 'important']
        }
        # 字符串转换为列表
        data = {'tags': 'urgent,normal'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

    # ==================== 嵌套条件测试 ====================

    def test_and_group(self):
        """测试 AND 条件组"""
        condition = {
            'type': 'GROUP',
            'logic': 'AND',
            'children': [
                {
                    'type': 'RULE',
                    'fieldKey': 'amount',
                    'fieldType': 'NUMBER',
                    'operator': 'GREATER_THAN',
                    'value': 1000
                },
                {
                    'type': 'RULE',
                    'fieldKey': 'department',
                    'fieldType': 'TEXT',
                    'operator': 'EQUALS',
                    'value': 'Finance'
                }
            ]
        }
        data = {'amount': 1500, 'department': 'Finance'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'amount': 500, 'department': 'Finance'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_or_group(self):
        """测试 OR 条件组"""
        condition = {
            'type': 'GROUP',
            'logic': 'OR',
            'children': [
                {
                    'type': 'RULE',
                    'fieldKey': 'amount',
                    'fieldType': 'NUMBER',
                    'operator': 'GREATER_THAN',
                    'value': 5000
                },
                {
                    'type': 'RULE',
                    'fieldKey': 'priority',
                    'fieldType': 'TEXT',
                    'operator': 'EQUALS',
                    'value': 'urgent'
                }
            ]
        }
        data = {'amount': 3000, 'priority': 'urgent'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'amount': 3000, 'priority': 'normal'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_nested_groups(self):
        """测试嵌套条件组"""
        condition = {
            'type': 'GROUP',
            'logic': 'AND',
            'children': [
                {
                    'type': 'RULE',
                    'fieldKey': 'amount',
                    'fieldType': 'NUMBER',
                    'operator': 'GREATER_THAN',
                    'value': 1000
                },
                {
                    'type': 'GROUP',
                    'logic': 'OR',
                    'children': [
                        {
                            'type': 'RULE',
                            'fieldKey': 'department',
                            'fieldType': 'TEXT',
                            'operator': 'EQUALS',
                            'value': 'Finance'
                        },
                        {
                            'type': 'RULE',
                            'fieldKey': 'department',
                            'fieldType': 'TEXT',
                            'operator': 'EQUALS',
                            'value': 'HR'
                        }
                    ]
                }
            ]
        }
        data = {'amount': 1500, 'department': 'Finance'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        data = {'amount': 1500, 'department': 'IT'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    # ==================== 边界情况测试 ====================

    def test_missing_field(self):
        """测试缺失字段"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'nonexistent',
            'fieldType': 'TEXT',
            'operator': 'EQUALS',
            'value': 'test'
        }
        data = {'other_field': 'value'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_none_condition(self):
        """测试 None 条件"""
        data = {'amount': 1000}
        assert ConditionEvaluatorV2.evaluate(None, data) is True

    def test_empty_group(self):
        """测试空条件组"""
        condition = {
            'type': 'GROUP',
            'logic': 'AND',
            'children': []
        }
        data = {'amount': 1000}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

    def test_invalid_condition_type(self):
        """测试无效的条件类型"""
        condition = {
            'type': 'INVALID',
            'fieldKey': 'amount',
            'operator': 'EQUALS',
            'value': 1000
        }
        data = {'amount': 1000}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_unsupported_operator(self):
        """测试不支持的运算符"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'amount',
            'fieldType': 'NUMBER',
            'operator': 'UNSUPPORTED',
            'value': 1000
        }
        data = {'amount': 1000}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    # ==================== 实际场景测试 ====================

    def test_approval_routing_scenario(self):
        """测试审批路由场景：大额招待费"""
        # 条件：金额 > 5000 且部门为 Finance
        condition = {
            'type': 'GROUP',
            'logic': 'AND',
            'children': [
                {
                    'type': 'RULE',
                    'fieldKey': 'amount',
                    'fieldType': 'NUMBER',
                    'operator': 'GREATER_THAN',
                    'value': 5000
                },
                {
                    'type': 'RULE',
                    'fieldKey': 'department',
                    'fieldType': 'TEXT',
                    'operator': 'EQUALS',
                    'value': 'Finance'
                }
            ]
        }
        # 应该路由到 CFO 审批
        data = {'amount': 8000, 'department': 'Finance'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        # 不应该路由到 CFO 审批
        data = {'amount': 3000, 'department': 'Finance'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    def test_complex_approval_scenario(self):
        """测试复杂审批场景"""
        # 条件：(金额 > 1000 且 < 5000) 或 (金额 >= 5000 且部门为 Finance)
        condition = {
            'type': 'GROUP',
            'logic': 'OR',
            'children': [
                {
                    'type': 'GROUP',
                    'logic': 'AND',
                    'children': [
                        {
                            'type': 'RULE',
                            'fieldKey': 'amount',
                            'fieldType': 'NUMBER',
                            'operator': 'GREATER_THAN',
                            'value': 1000
                        },
                        {
                            'type': 'RULE',
                            'fieldKey': 'amount',
                            'fieldType': 'NUMBER',
                            'operator': 'LESS_THAN',
                            'value': 5000
                        }
                    ]
                },
                {
                    'type': 'GROUP',
                    'logic': 'AND',
                    'children': [
                        {
                            'type': 'RULE',
                            'fieldKey': 'amount',
                            'fieldType': 'NUMBER',
                            'operator': 'GREATER_EQUAL',
                            'value': 5000
                        },
                        {
                            'type': 'RULE',
                            'fieldKey': 'department',
                            'fieldType': 'TEXT',
                            'operator': 'EQUALS',
                            'value': 'Finance'
                        }
                    ]
                }
            ]
        }
        # 金额 2000，应该满足第一个条件
        data = {'amount': 2000, 'department': 'IT'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        # 金额 6000，部门 Finance，应该满足第二个条件
        data = {'amount': 6000, 'department': 'Finance'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is True

        # 金额 6000，部门 IT，不应该满足任何条件
        data = {'amount': 6000, 'department': 'IT'}
        assert ConditionEvaluatorV2.evaluate(condition, data) is False

    # ==================== 便利函数测试 ====================

    def test_evaluate_condition_tree_function(self):
        """测试便利函数 evaluate_condition_tree"""
        condition = {
            'type': 'RULE',
            'fieldKey': 'amount',
            'fieldType': 'NUMBER',
            'operator': 'GREATER_THAN',
            'value': 1000
        }
        data = {'amount': 1500}
        assert evaluate_condition_tree(condition, data) is True

        # None 条件应该返回 True
        assert evaluate_condition_tree(None, data) is True
