"""
模块用途: 条件表达式评估引擎 V2（支持设计格式的条件树）
依赖配置: 无外部依赖
数据流向: 条件树 + 提交数据 -> 条件评估 -> 布尔结果
函数清单:
    - evaluate(): 评估条件树
    - _evaluate_rule(): 评估单条规则
    - _evaluate_group(): 评估条件组
    - _compare(): 处理所有运算符
"""
from typing import Any, Dict, List, Union, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class ConditionEvaluatorV2:
    """条件表达式评估器 V2（支持设计格式的条件树）"""

    # 支持的运算符
    SUPPORTED_OPERATORS = {
        'EQUALS', 'NOT_EQUALS', 'GREATER_THAN', 'GREATER_EQUAL',
        'LESS_THAN', 'LESS_EQUAL', 'BETWEEN', 'CONTAINS', 'NOT_CONTAINS',
        'IN', 'NOT_IN', 'HAS_ANY', 'HAS_ALL', 'IS_EMPTY', 'IS_NOT_EMPTY',
        'DATE_BEFORE_NOW', 'DATE_AFTER_NOW'
    }

    @staticmethod
    def evaluate(
        condition: Optional[Dict[str, Any]],
        data: Dict[str, Any],
        system_fields: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        评估条件树

        Args:
            condition: 条件树（RULE 或 GROUP 节点）
            data: 提交数据（表单字段值）
            system_fields: 系统字段值（提交人、提交人部门、提交时间等）

        Returns:
            条件是否满足

        Raises:
            ValueError: 条件格式错误或不支持的操作符
        """
        if condition is None:
            return True

        # 合并系统字段和表单数据
        if system_fields:
            data = {**data, **system_fields}

        try:
            condition_type = condition.get('type')

            if condition_type == 'RULE':
                return ConditionEvaluatorV2._evaluate_rule(condition, data)
            elif condition_type == 'GROUP':
                return ConditionEvaluatorV2._evaluate_group(condition, data)
            else:
                logger.warning(f"Unknown condition type: {condition_type}")
                return False

        except Exception as e:
            logger.error(f"Error evaluating condition: {e}", exc_info=True)
            return False

    @staticmethod
    def _evaluate_rule(
        rule: Dict[str, Any],
        data: Dict[str, Any]
    ) -> bool:
        """
        评估单条规则

        Args:
            rule: 规则节点（type='RULE'）
            data: 提交数据

        Returns:
            规则是否满足
        """
        field_key = rule.get('fieldKey')
        operator = rule.get('operator')
        value = rule.get('value')
        field_type = rule.get('fieldType')

        if not field_key or not operator:
            logger.warning(f"Invalid rule: missing fieldKey or operator")
            return False

        if operator not in ConditionEvaluatorV2.SUPPORTED_OPERATORS:
            logger.warning(f"Unsupported operator: {operator}")
            return False

        # 获取字段值（任务13：字段不存在时返回 null）
        field_value = data.get(field_key)

        # 处理空值检查
        if operator == 'IS_EMPTY':
            return field_value is None or field_value == '' or field_value == []
        elif operator == 'IS_NOT_EMPTY':
            return field_value is not None and field_value != '' and field_value != []

        # 对于其他运算符，如果字段值为空，返回 False（任务13：第二步兜底）
        if field_value is None:
            return False

        try:
            # 类型转换（任务13：类型转换失败时返回 false，不崩溃）
            field_value = ConditionEvaluatorV2._convert_value(field_value, field_type)
            compare_value = ConditionEvaluatorV2._convert_value(value, field_type)

            # 执行比较
            return ConditionEvaluatorV2._compare(
                field_value, operator, compare_value, field_type
            )
        except Exception as e:
            logger.warning(f"Error evaluating rule for field {field_key}: {e}")
            return False

    @staticmethod
    def _evaluate_group(
        group: Dict[str, Any],
        data: Dict[str, Any]
    ) -> bool:
        """
        评估条件组

        Args:
            group: 条件组节点（type='GROUP'）
            data: 提交数据

        Returns:
            条件组是否满足
        """
        logic = group.get('logic', 'AND').upper()
        children = group.get('children', [])

        # 空组处理（任务14）
        if not children:
            # AND 空组 → true（没有条件需要满足，等于无条件通过）
            # OR 空组 → false（没有条件能满足）
            return logic == 'AND'

        results = [
            ConditionEvaluatorV2.evaluate(child, data)
            for child in children
        ]

        if logic == 'AND':
            return all(results)
        elif logic == 'OR':
            return any(results)
        else:
            logger.warning(f"Unknown logic type: {logic}, defaulting to AND")
            return all(results)

    @staticmethod
    def _convert_value(
        value: Any,
        field_type: Optional[str]
    ) -> Any:
        """
        类型转换

        Args:
            value: 原始值
            field_type: 字段类型

        Returns:
            转换后的值
        """
        if value is None:
            return None

        if field_type == 'NUMBER':
            try:
                if isinstance(value, (int, float)):
                    return value
                return float(value)
            except (ValueError, TypeError):
                logger.warning(f"Failed to convert {value} to NUMBER")
                return value

        elif field_type == 'DATE':
            if isinstance(value, date):
                return value
            if isinstance(value, str):
                try:
                    # 尝试解析 ISO 格式日期
                    return datetime.fromisoformat(value).date()
                except (ValueError, TypeError):
                    logger.warning(f"Failed to convert {value} to DATE")
                    return value

        elif field_type == 'DATETIME':
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value)
                except (ValueError, TypeError):
                    logger.warning(f"Failed to convert {value} to DATETIME")
                    return value

        elif field_type == 'MULTI_SELECT':
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                # 如果是逗号分隔的字符串，转换为列表
                return [v.strip() for v in value.split(',')]
            return [value]

        elif field_type in ('USER', 'DEPARTMENT'):
            return str(value)

        return value

    @staticmethod
    def _compare(
        left: Any,
        operator: str,
        right: Any,
        field_type: Optional[str]
    ) -> bool:
        """
        比较操作

        Args:
            left: 左操作数（字段值）
            operator: 运算符
            right: 右操作数（比较值）
            field_type: 字段类型

        Returns:
            比较结果
        """
        try:
            if operator == 'EQUALS':
                return left == right

            elif operator == 'NOT_EQUALS':
                return left != right

            elif operator == 'GREATER_THAN':
                return left > right

            elif operator == 'GREATER_EQUAL':
                return left >= right

            elif operator == 'LESS_THAN':
                return left < right

            elif operator == 'LESS_EQUAL':
                return left <= right

            elif operator == 'BETWEEN':
                # right 应该是 [min, max] 的列表
                if isinstance(right, list) and len(right) == 2:
                    return right[0] <= left <= right[1]
                logger.warning(f"Invalid BETWEEN value: {right}")
                return False

            elif operator == 'CONTAINS':
                # 字符串包含
                return str(right) in str(left)

            elif operator == 'NOT_CONTAINS':
                # 字符串不包含
                return str(right) not in str(left)

            elif operator == 'IN':
                # 确保 right 是列表
                if not isinstance(right, list):
                    right = [right]
                return left in right

            elif operator == 'NOT_IN':
                # 确保 right 是列表
                if not isinstance(right, list):
                    right = [right]
                return left not in right

            elif operator == 'HAS_ANY':
                # 多选字段包含任一值
                if not isinstance(left, list):
                    left = [left]
                if not isinstance(right, list):
                    right = [right]
                return any(item in left for item in right)

            elif operator == 'HAS_ALL':
                # 多选字段包含全部值
                if not isinstance(left, list):
                    left = [left]
                if not isinstance(right, list):
                    right = [right]
                return all(item in left for item in right)

            elif operator == 'DATE_BEFORE_NOW':
                # 日期早于当前时间 X 天
                if isinstance(left, date) and isinstance(right, (int, float)):
                    days_ago = datetime.now().date() - left
                    return days_ago.days >= right
                return False

            elif operator == 'DATE_AFTER_NOW':
                # 日期晚于当前时间 X 天
                if isinstance(left, date) and isinstance(right, (int, float)):
                    days_after = left - datetime.now().date()
                    return days_after.days >= right
                return False

            else:
                logger.warning(f"Unknown operator: {operator}")
                return False

        except Exception as e:
            logger.error(f"Error in comparison: {e}", exc_info=True)
            return False


def evaluate_condition_tree(
    condition: Optional[Dict[str, Any]],
    submission_data: Dict[str, Any],
    system_fields: Optional[Dict[str, Any]] = None
) -> bool:
    """
    评估条件树（便利函数）

    Args:
        condition: 条件树（可为 None）
        submission_data: 表单提交数据
        system_fields: 系统字段值（提交人、提交人部门、提交时间等）

    Returns:
        条件是否满足（None 条件默认返回 True）
    """
    if condition is None:
        return True

    return ConditionEvaluatorV2.evaluate(condition, submission_data, system_fields)
