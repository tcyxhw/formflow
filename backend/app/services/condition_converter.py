"""
模块用途: JsonLogic 格式转换为设计格式的转换器
依赖配置: 无外部依赖
数据流向: JsonLogic表达式 -> 转换 -> 设计格式条件树
函数清单:
    - convert(): 将 JsonLogic 转换为设计格式
    - _convert_condition(): 递归转换条件
    - _convert_comparison(): 转换比较操作符
    - _get_field_type(): 推断字段类型
"""
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class ConditionConverter:
    """JsonLogic 格式转换器"""

    # JsonLogic 运算符到设计格式运算符的映射
    OPERATOR_MAPPING = {
        '==': 'EQUALS',
        '!=': 'NOT_EQUALS',
        '>': 'GREATER_THAN',
        '>=': 'GREATER_EQUAL',
        '<': 'LESS_THAN',
        '<=': 'LESS_EQUAL',
        'in': 'IN',
        'startsWith': 'CONTAINS',
        'endsWith': 'CONTAINS',
    }

    @staticmethod
    def convert(
        json_logic_condition: Optional[Dict[str, Any]],
        field_definitions: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        将 JsonLogic 格式转换为设计格式

        Args:
            json_logic_condition: JsonLogic 格式的条件表达式
            field_definitions: 字段定义字典，用于推断字段类型
                              格式: {"field_key": {"type": "NUMBER", ...}, ...}

        Returns:
            设计格式的条件树，或 None 如果输入为 None

        Raises:
            ValueError: 条件格式错误或不支持的操作符
        """
        if json_logic_condition is None:
            return None

        if not isinstance(json_logic_condition, dict):
            raise ValueError("Condition must be a dictionary")

        if field_definitions is None:
            field_definitions = {}

        try:
            return ConditionConverter._convert_condition(
                json_logic_condition,
                field_definitions
            )
        except Exception as e:
            logger.error(f"Error converting condition: {e}", exc_info=True)
            raise

    @staticmethod
    def _convert_condition(
        condition: Dict[str, Any],
        field_definitions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        递归转换条件

        Args:
            condition: JsonLogic 条件
            field_definitions: 字段定义

        Returns:
            设计格式的条件节点
        """
        # 处理 AND 逻辑
        if 'and' in condition:
            conditions = condition['and']
            if not isinstance(conditions, list):
                conditions = [conditions]

            children = [
                ConditionConverter._convert_condition(cond, field_definitions)
                for cond in conditions
            ]

            return {
                'type': 'GROUP',
                'logic': 'AND',
                'children': children
            }

        # 处理 OR 逻辑
        if 'or' in condition:
            conditions = condition['or']
            if not isinstance(conditions, list):
                conditions = [conditions]

            children = [
                ConditionConverter._convert_condition(cond, field_definitions)
                for cond in conditions
            ]

            return {
                'type': 'GROUP',
                'logic': 'OR',
                'children': children
            }

        # 处理 NOT 逻辑（转换为 NOT_EQUALS 或其他反向操作）
        if '!' in condition:
            inner = condition['!']
            # 递归转换内部条件
            converted = ConditionConverter._convert_condition(inner, field_definitions)
            # 如果是 GROUP，添加 NOT 逻辑（暂时不支持，返回原条件的反向）
            if converted.get('type') == 'GROUP':
                logger.warning("NOT operator on GROUP is not fully supported")
                return converted
            # 如果是 RULE，反向操作符
            if converted.get('type') == 'RULE':
                operator = converted.get('operator')
                reversed_operator = ConditionConverter._reverse_operator(operator)
                converted['operator'] = reversed_operator
                return converted

        # 处理比较操作符
        for operator in ['==', '!=', '>', '<', '>=', '<=']:
            if operator in condition:
                return ConditionConverter._convert_comparison(
                    operator,
                    condition[operator],
                    field_definitions
                )

        # 处理字符串操作
        if 'in' in condition:
            operands = condition['in']
            if not isinstance(operands, list) or len(operands) != 2:
                raise ValueError("Invalid operands for 'in'")

            field_key = ConditionConverter._extract_field_key(operands[0])
            value = ConditionConverter._resolve_value(operands[1])

            if field_key is None:
                raise ValueError("Cannot extract field key from 'in' condition")

            field_type = ConditionConverter._get_field_type(
                field_key,
                field_definitions
            )

            return {
                'type': 'RULE',
                'fieldKey': field_key,
                'operator': 'IN',
                'value': value if isinstance(value, list) else [value],
                'fieldType': field_type
            }

        if 'startsWith' in condition:
            operands = condition['startsWith']
            if not isinstance(operands, list) or len(operands) != 2:
                raise ValueError("Invalid operands for 'startsWith'")

            field_key = ConditionConverter._extract_field_key(operands[0])
            value = ConditionConverter._resolve_value(operands[1])

            if field_key is None:
                raise ValueError("Cannot extract field key from 'startsWith' condition")

            field_type = ConditionConverter._get_field_type(
                field_key,
                field_definitions
            )

            return {
                'type': 'RULE',
                'fieldKey': field_key,
                'operator': 'CONTAINS',
                'value': value,
                'fieldType': field_type
            }

        if 'endsWith' in condition:
            operands = condition['endsWith']
            if not isinstance(operands, list) or len(operands) != 2:
                raise ValueError("Invalid operands for 'endsWith'")

            field_key = ConditionConverter._extract_field_key(operands[0])
            value = ConditionConverter._resolve_value(operands[1])

            if field_key is None:
                raise ValueError("Cannot extract field key from 'endsWith' condition")

            field_type = ConditionConverter._get_field_type(
                field_key,
                field_definitions
            )

            return {
                'type': 'RULE',
                'fieldKey': field_key,
                'operator': 'CONTAINS',
                'value': value,
                'fieldType': field_type
            }

        raise ValueError(f"Unknown condition operator in: {condition}")

    @staticmethod
    def _convert_comparison(
        operator: str,
        operands: List[Any],
        field_definitions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        转换比较操作符

        Args:
            operator: JsonLogic 运算符 (==, !=, >, <, >=, <=)
            operands: 操作数列表
            field_definitions: 字段定义

        Returns:
            设计格式的 RULE 节点
        """
        if not isinstance(operands, list) or len(operands) != 2:
            raise ValueError(f"Invalid operands for {operator}")

        field_key = ConditionConverter._extract_field_key(operands[0])
        value = ConditionConverter._resolve_value(operands[1])

        if field_key is None:
            raise ValueError(f"Cannot extract field key from comparison: {operands[0]}")

        design_operator = ConditionConverter.OPERATOR_MAPPING.get(operator, operator)
        field_type = ConditionConverter._get_field_type(
            field_key,
            field_definitions
        )

        return {
            'type': 'RULE',
            'fieldKey': field_key,
            'operator': design_operator,
            'value': value,
            'fieldType': field_type
        }

    @staticmethod
    def _extract_field_key(value: Any) -> Optional[str]:
        """
        从值中提取字段键

        Args:
            value: 可能是字段引用 {"var": "field_key"} 或直接值

        Returns:
            字段键，或 None 如果不是字段引用
        """
        if isinstance(value, dict) and 'var' in value:
            return value['var']
        return None

    @staticmethod
    def _resolve_value(value: Any) -> Any:
        """
        解析值

        Args:
            value: 值或变量引用

        Returns:
            解析后的值
        """
        if isinstance(value, dict):
            if 'var' in value:
                # 返回字段引用（不应该在这里出现）
                return value['var']
            # 其他字典类型，返回原值
            return value

        return value

    @staticmethod
    def _get_field_type(
        field_key: str,
        field_definitions: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        推断字段类型

        Args:
            field_key: 字段键
            field_definitions: 字段定义

        Returns:
            字段类型（默认为 TEXT）
        """
        if field_key in field_definitions:
            return field_definitions[field_key].get('type', 'TEXT')

        # 根据字段键推断类型
        if field_key.startswith('sys_'):
            if 'time' in field_key or 'date' in field_key:
                return 'DATE'
            if 'dept' in field_key or 'department' in field_key:
                return 'DEPARTMENT'
            if 'user' in field_key or 'submitter' in field_key:
                return 'USER'

        return 'TEXT'

    @staticmethod
    def _reverse_operator(operator: str) -> str:
        """
        反向运算符（用于 NOT 操作）

        Args:
            operator: 原始运算符

        Returns:
            反向运算符
        """
        reverse_map = {
            'EQUALS': 'NOT_EQUALS',
            'NOT_EQUALS': 'EQUALS',
            'GREATER_THAN': 'LESS_EQUAL',
            'GREATER_EQUAL': 'LESS_THAN',
            'LESS_THAN': 'GREATER_EQUAL',
            'LESS_EQUAL': 'GREATER_THAN',
            'IN': 'NOT_IN',
            'NOT_IN': 'IN',
            'CONTAINS': 'NOT_CONTAINS',
            'NOT_CONTAINS': 'CONTAINS',
            'IS_EMPTY': 'IS_NOT_EMPTY',
            'IS_NOT_EMPTY': 'IS_EMPTY',
        }
        return reverse_map.get(operator, operator)


def convert_json_logic_to_design_format(
    json_logic_condition: Optional[Dict[str, Any]],
    field_definitions: Optional[Dict[str, Dict[str, Any]]] = None
) -> Optional[Dict[str, Any]]:
    """
    便利函数：将 JsonLogic 转换为设计格式

    Args:
        json_logic_condition: JsonLogic 格式的条件表达式
        field_definitions: 字段定义字典

    Returns:
        设计格式的条件树，或 None 如果输入为 None
    """
    return ConditionConverter.convert(json_logic_condition, field_definitions)
