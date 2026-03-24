"""
测试条件转换器 - JsonLogic 到设计格式的转换
"""
import pytest
from app.services.condition_converter import (
    ConditionConverter,
    convert_json_logic_to_design_format
)


class TestConditionConverter:
    """条件转换器测试"""

    def test_convert_simple_equals(self):
        """测试简单的 EQUALS 转换"""
        json_logic = {
            '==': [
                {'var': 'amount'},
                10000
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result is not None
        assert result['type'] == 'RULE'
        assert result['fieldKey'] == 'amount'
        assert result['operator'] == 'EQUALS'
        assert result['value'] == 10000

    def test_convert_not_equals(self):
        """测试 NOT_EQUALS 转换"""
        json_logic = {
            '!=': [
                {'var': 'status'},
                'rejected'
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['type'] == 'RULE'
        assert result['fieldKey'] == 'status'
        assert result['operator'] == 'NOT_EQUALS'
        assert result['value'] == 'rejected'

    def test_convert_greater_than(self):
        """测试 GREATER_THAN 转换"""
        json_logic = {
            '>': [
                {'var': 'amount'},
                5000
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['type'] == 'RULE'
        assert result['fieldKey'] == 'amount'
        assert result['operator'] == 'GREATER_THAN'
        assert result['value'] == 5000

    def test_convert_greater_equal(self):
        """测试 GREATER_EQUAL 转换"""
        json_logic = {
            '>=': [
                {'var': 'amount'},
                10000
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['operator'] == 'GREATER_EQUAL'

    def test_convert_less_than(self):
        """测试 LESS_THAN 转换"""
        json_logic = {
            '<': [
                {'var': 'amount'},
                1000
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['operator'] == 'LESS_THAN'

    def test_convert_less_equal(self):
        """测试 LESS_EQUAL 转换"""
        json_logic = {
            '<=': [
                {'var': 'amount'},
                1000
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['operator'] == 'LESS_EQUAL'

    def test_convert_in_operator(self):
        """测试 IN 运算符转换"""
        json_logic = {
            'in': [
                {'var': 'category'},
                ['招待', '差旅', '会议']
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['type'] == 'RULE'
        assert result['fieldKey'] == 'category'
        assert result['operator'] == 'IN'
        assert result['value'] == ['招待', '差旅', '会议']

    def test_convert_starts_with(self):
        """测试 startsWith 转换"""
        json_logic = {
            'startsWith': [
                {'var': 'code'},
                'EXP'
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['type'] == 'RULE'
        assert result['fieldKey'] == 'code'
        assert result['operator'] == 'CONTAINS'
        assert result['value'] == 'EXP'

    def test_convert_ends_with(self):
        """测试 endsWith 转换"""
        json_logic = {
            'endsWith': [
                {'var': 'code'},
                '_APPROVED'
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['type'] == 'RULE'
        assert result['fieldKey'] == 'code'
        assert result['operator'] == 'CONTAINS'
        assert result['value'] == '_APPROVED'


    def test_convert_and_group(self):
        """测试 AND 逻辑组转换"""
        json_logic = {
            'and': [
                {'>=': [{'var': 'amount'}, 10000]},
                {'==': [{'var': 'category'}, '招待']}
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['type'] == 'GROUP'
        assert result['logic'] == 'AND'
        assert len(result['children']) == 2
        assert result['children'][0]['type'] == 'RULE'
        assert result['children'][0]['operator'] == 'GREATER_EQUAL'
        assert result['children'][1]['type'] == 'RULE'
        assert result['children'][1]['operator'] == 'EQUALS'

    def test_convert_or_group(self):
        """测试 OR 逻辑组转换"""
        json_logic = {
            'or': [
                {'==': [{'var': 'status'}, 'pending']},
                {'==': [{'var': 'status'}, 'draft']}
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['type'] == 'GROUP'
        assert result['logic'] == 'OR'
        assert len(result['children']) == 2

    def test_convert_nested_groups(self):
        """测试嵌套条件组转换"""
        json_logic = {
            'and': [
                {
                    'or': [
                        {'==': [{'var': 'category'}, '招待']},
                        {'==': [{'var': 'category'}, '差旅']}
                    ]
                },
                {'>=': [{'var': 'amount'}, 5000]}
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['type'] == 'GROUP'
        assert result['logic'] == 'AND'
        assert result['children'][0]['type'] == 'GROUP'
        assert result['children'][0]['logic'] == 'OR'
        assert result['children'][1]['type'] == 'RULE'

    def test_convert_with_field_definitions(self):
        """测试使用字段定义推断类型"""
        json_logic = {
            '>=': [
                {'var': 'amount'},
                10000
            ]
        }

        field_definitions = {
            'amount': {'type': 'NUMBER', 'name': '金额'}
        }

        result = ConditionConverter.convert(json_logic, field_definitions)

        assert result['fieldType'] == 'NUMBER'

    def test_convert_system_field_type_inference(self):
        """测试系统字段类型推断"""
        json_logic = {
            '>': [
                {'var': 'sys_submit_time'},
                '2024-01-01'
            ]
        }

        result = ConditionConverter.convert(json_logic)

        # 系统字段应该推断为 DATE 类型
        assert result['fieldType'] == 'DATE'

    def test_convert_none_condition(self):
        """测试 None 条件转换"""
        result = ConditionConverter.convert(None)
        assert result is None

    def test_convert_invalid_condition_format(self):
        """测试无效条件格式"""
        with pytest.raises(ValueError):
            ConditionConverter.convert("invalid")

    def test_convert_missing_field_key(self):
        """测试缺少字段键的条件"""
        json_logic = {
            '==': [
                100,  # 不是字段引用
                100
            ]
        }

        with pytest.raises(ValueError):
            ConditionConverter.convert(json_logic)

    def test_convert_invalid_in_operands(self):
        """测试无效的 IN 操作数"""
        json_logic = {
            'in': [
                {'var': 'category'}
                # 缺少第二个操作数
            ]
        }

        with pytest.raises(ValueError):
            ConditionConverter.convert(json_logic)

    def test_convert_complex_approval_scenario(self):
        """测试复杂的审批场景转换"""
        # 场景：金额 >= 10000 且 (类别为招待 或 类别为差旅) 且 部门为市场部
        json_logic = {
            'and': [
                {'>=': [{'var': 'amount'}, 10000]},
                {
                    'or': [
                        {'==': [{'var': 'category'}, '招待']},
                        {'==': [{'var': 'category'}, '差旅']}
                    ]
                },
                {'==': [{'var': 'department'}, '市场部']}
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['type'] == 'GROUP'
        assert result['logic'] == 'AND'
        assert len(result['children']) == 3
        assert result['children'][0]['type'] == 'RULE'
        assert result['children'][1]['type'] == 'GROUP'
        assert result['children'][2]['type'] == 'RULE'

    def test_convenience_function(self):
        """测试便利函数"""
        json_logic = {
            '==': [
                {'var': 'status'},
                'approved'
            ]
        }

        result = convert_json_logic_to_design_format(json_logic)

        assert result is not None
        assert result['type'] == 'RULE'
        assert result['fieldKey'] == 'status'
        assert result['operator'] == 'EQUALS'

    def test_convert_single_and_condition(self):
        """测试单个 AND 条件"""
        json_logic = {
            'and': {
                '==': [{'var': 'status'}, 'active']
            }
        }

        result = ConditionConverter.convert(json_logic)

        assert result['type'] == 'GROUP'
        assert result['logic'] == 'AND'
        assert len(result['children']) == 1

    def test_convert_single_or_condition(self):
        """测试单个 OR 条件"""
        json_logic = {
            'or': {
                '==': [{'var': 'status'}, 'active']
            }
        }

        result = ConditionConverter.convert(json_logic)

        assert result['type'] == 'GROUP'
        assert result['logic'] == 'OR'
        assert len(result['children']) == 1

    def test_convert_in_with_single_value(self):
        """测试 IN 运算符单个值"""
        json_logic = {
            'in': [
                {'var': 'category'},
                '招待'
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['operator'] == 'IN'
        assert result['value'] == ['招待']

    def test_convert_multiple_comparison_operators(self):
        """测试多个比较运算符"""
        operators = [
            ('==', 'EQUALS'),
            ('!=', 'NOT_EQUALS'),
            ('>', 'GREATER_THAN'),
            ('>=', 'GREATER_EQUAL'),
            ('<', 'LESS_THAN'),
            ('<=', 'LESS_EQUAL'),
        ]

        for json_op, design_op in operators:
            json_logic = {
                json_op: [
                    {'var': 'amount'},
                    1000
                ]
            }

            result = ConditionConverter.convert(json_logic)
            assert result['operator'] == design_op, f"Failed for operator {json_op}"

    def test_convert_preserves_field_values(self):
        """测试转换保留字段值"""
        json_logic = {
            '==': [
                {'var': 'name'},
                'John Doe'
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['value'] == 'John Doe'

    def test_convert_preserves_numeric_values(self):
        """测试转换保留数值"""
        json_logic = {
            '>=': [
                {'var': 'amount'},
                10000.50
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['value'] == 10000.50

    def test_convert_deeply_nested_groups(self):
        """测试深层嵌套条件组"""
        json_logic = {
            'and': [
                {
                    'or': [
                        {
                            'and': [
                                {'==': [{'var': 'a'}, 1]},
                                {'==': [{'var': 'b'}, 2]}
                            ]
                        },
                        {'==': [{'var': 'c'}, 3]}
                    ]
                },
                {'==': [{'var': 'd'}, 4]}
            ]
        }

        result = ConditionConverter.convert(json_logic)

        assert result['type'] == 'GROUP'
        assert result['logic'] == 'AND'
        assert result['children'][0]['type'] == 'GROUP'
        assert result['children'][0]['logic'] == 'OR'
        assert result['children'][0]['children'][0]['type'] == 'GROUP'



class TestConditionConverterIntegration:
    """条件转换器与评估器的集成测试"""

    def test_convert_and_evaluate_simple_condition(self):
        """测试转换后的条件可以被评估器正确评估"""
        from app.services.condition_evaluator_v2 import ConditionEvaluatorV2

        # JsonLogic 格式
        json_logic = {
            '>=': [
                {'var': 'amount'},
                10000
            ]
        }

        # 转换为设计格式
        design_condition = ConditionConverter.convert(json_logic)

        # 评估条件
        data = {'amount': 15000}
        result = ConditionEvaluatorV2.evaluate(design_condition, data)

        assert result is True

    def test_convert_and_evaluate_complex_condition(self):
        """测试复杂条件的转换和评估"""
        from app.services.condition_evaluator_v2 import ConditionEvaluatorV2

        # JsonLogic 格式：金额 >= 10000 且 (类别为招待 或 类别为差旅)
        json_logic = {
            'and': [
                {'>=': [{'var': 'amount'}, 10000]},
                {
                    'or': [
                        {'==': [{'var': 'category'}, '招待']},
                        {'==': [{'var': 'category'}, '差旅']}
                    ]
                }
            ]
        }

        # 转换为设计格式
        design_condition = ConditionConverter.convert(json_logic)

        # 测试满足条件的数据
        data1 = {'amount': 15000, 'category': '招待'}
        result1 = ConditionEvaluatorV2.evaluate(design_condition, data1)
        assert result1 is True

        # 测试不满足条件的数据
        data2 = {'amount': 5000, 'category': '招待'}
        result2 = ConditionEvaluatorV2.evaluate(design_condition, data2)
        assert result2 is False

        # 测试不满足条件的数据
        data3 = {'amount': 15000, 'category': '会议'}
        result3 = ConditionEvaluatorV2.evaluate(design_condition, data3)
        assert result3 is False

    def test_convert_and_evaluate_nested_condition(self):
        """测试嵌套条件的转换和评估"""
        from app.services.condition_evaluator_v2 import ConditionEvaluatorV2

        # 复杂的嵌套条件
        json_logic = {
            'and': [
                {
                    'or': [
                        {'==': [{'var': 'category'}, '招待']},
                        {'==': [{'var': 'category'}, '差旅']}
                    ]
                },
                {'>=': [{'var': 'amount'}, 5000]},
                {'!=': [{'var': 'status'}, 'rejected']}
            ]
        }

        design_condition = ConditionConverter.convert(json_logic)

        # 满足所有条件
        data = {
            'category': '招待',
            'amount': 10000,
            'status': 'pending'
        }
        result = ConditionEvaluatorV2.evaluate(design_condition, data)
        assert result is True

    def test_convert_and_evaluate_in_operator(self):
        """测试 IN 运算符的转换和评估"""
        from app.services.condition_evaluator_v2 import ConditionEvaluatorV2

        json_logic = {
            'in': [
                {'var': 'category'},
                ['招待', '差旅', '会议']
            ]
        }

        design_condition = ConditionConverter.convert(json_logic)

        # 值在列表中
        data1 = {'category': '招待'}
        result1 = ConditionEvaluatorV2.evaluate(design_condition, data1)
        assert result1 is True

        # 值不在列表中
        data2 = {'category': '其他'}
        result2 = ConditionEvaluatorV2.evaluate(design_condition, data2)
        assert result2 is False

    def test_convert_and_evaluate_approval_routing(self):
        """测试审批路由场景的转换和评估"""
        from app.services.condition_evaluator_v2 import ConditionEvaluatorV2

        # 场景：大额招待费审批
        # 条件：金额 >= 10000 且 类别为招待
        json_logic = {
            'and': [
                {'>=': [{'var': 'amount'}, 10000]},
                {'==': [{'var': 'category'}, '招待']}
            ]
        }

        design_condition = ConditionConverter.convert(json_logic)

        # 测试数据
        submission_data = {
            'amount': 12000,
            'category': '招待',
            'department': '市场部'
        }

        result = ConditionEvaluatorV2.evaluate(design_condition, submission_data)
        assert result is True

    def test_convert_preserves_evaluation_semantics(self):
        """测试转换保留评估语义"""
        from app.services.condition_evaluator_v2 import ConditionEvaluatorV2

        # 多个测试用例
        test_cases = [
            (
                {'==': [{'var': 'status'}, 'active']},
                {'status': 'active'},
                True
            ),
            (
                {'!=': [{'var': 'status'}, 'active']},
                {'status': 'inactive'},
                True
            ),
            (
                {'>': [{'var': 'amount'}, 1000]},
                {'amount': 2000},
                True
            ),
            (
                {'<': [{'var': 'amount'}, 1000]},
                {'amount': 500},
                True
            ),
        ]

        for json_logic, data, expected in test_cases:
            design_condition = ConditionConverter.convert(json_logic)
            result = ConditionEvaluatorV2.evaluate(design_condition, data)
            assert result == expected, f"Failed for {json_logic}"
