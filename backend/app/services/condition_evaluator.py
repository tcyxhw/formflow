"""
模块用途: JsonLogic 条件评估引擎
依赖配置: 无外部依赖
数据流向: JsonLogic表达式 + 提交数据 -> 条件评估 -> 布尔结果
函数清单:
    - evaluate_condition(): 评估单个条件表达式
    - evaluate_conditions(): 评估多个条件（支持AND/OR逻辑）
"""
from typing import Any, Dict, List, Union
import logging

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    """JsonLogic 条件评估器"""

    @staticmethod
    def evaluate_condition(
        condition: Dict[str, Any],
        data: Dict[str, Any]
    ) -> bool:
        """
        评估单个 JsonLogic 条件表达式

        Args:
            condition: JsonLogic 表达式字典
            data: 提交数据（表单字段值）

        Returns:
            条件是否满足

        Raises:
            ValueError: 条件格式错误或不支持的操作符
        """
        if not condition:
            return True

        # 处理 AND 逻辑
        if 'and' in condition:
            conditions = condition['and']
            if not isinstance(conditions, list):
                conditions = [conditions]
            return all(
                ConditionEvaluator.evaluate_condition(cond, data)
                for cond in conditions
            )

        # 处理 OR 逻辑
        if 'or' in condition:
            conditions = condition['or']
            if not isinstance(conditions, list):
                conditions = [conditions]
            return any(
                ConditionEvaluator.evaluate_condition(cond, data)
                for cond in conditions
            )

        # 处理 NOT 逻辑
        if '!' in condition:
            inner = condition['!']
            return not ConditionEvaluator.evaluate_condition(inner, data)

        # 处理比较操作符
        for operator in ['==', '!=', '>', '<', '>=', '<=']:
            if operator in condition:
                operands = condition[operator]
                if not isinstance(operands, list) or len(operands) != 2:
                    raise ValueError(f"Invalid operands for {operator}")
                
                left = ConditionEvaluator._resolve_value(operands[0], data)
                right = ConditionEvaluator._resolve_value(operands[1], data)
                
                if operator == '==':
                    return left == right
                elif operator == '!=':
                    return left != right
                elif operator == '>':
                    return left > right
                elif operator == '<':
                    return left < right
                elif operator == '>=':
                    return left >= right
                elif operator == '<=':
                    return left <= right

        # 处理字符串操作
        if 'in' in condition:
            operands = condition['in']
            if not isinstance(operands, list) or len(operands) != 2:
                raise ValueError("Invalid operands for 'in'")
            
            value = ConditionEvaluator._resolve_value(operands[0], data)
            container = ConditionEvaluator._resolve_value(operands[1], data)
            
            if isinstance(container, str):
                return str(value) in container
            elif isinstance(container, (list, tuple)):
                return value in container
            else:
                return False

        if 'startsWith' in condition:
            operands = condition['startsWith']
            if not isinstance(operands, list) or len(operands) != 2:
                raise ValueError("Invalid operands for 'startsWith'")
            
            text = str(ConditionEvaluator._resolve_value(operands[0], data))
            prefix = str(ConditionEvaluator._resolve_value(operands[1], data))
            return text.startswith(prefix)

        if 'endsWith' in condition:
            operands = condition['endsWith']
            if not isinstance(operands, list) or len(operands) != 2:
                raise ValueError("Invalid operands for 'endsWith'")
            
            text = str(ConditionEvaluator._resolve_value(operands[0], data))
            suffix = str(ConditionEvaluator._resolve_value(operands[1], data))
            return text.endswith(suffix)

        # 如果没有识别的操作符，返回 False（默认不通过）
        logger.warning(f"Unknown condition operator in: {condition}")
        return False

    @staticmethod
    def _resolve_value(value: Any, data: Dict[str, Any]) -> Any:
        """
        解析值（支持变量引用）

        Args:
            value: 值或变量引用
            data: 数据字典

        Returns:
            解析后的值
        """
        if isinstance(value, dict):
            # 处理变量引用 {"var": "field_name"}
            if 'var' in value:
                field_name = value['var']
                return data.get(field_name)
            # 处理嵌套条件
            return ConditionEvaluator.evaluate_condition(value, data)
        
        return value

    @staticmethod
    def evaluate_conditions(
        rules: List[Dict[str, Any]],
        logic: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        评估多个条件规则

        Args:
            rules: 条件规则列表
            logic: 逻辑关系 ('AND' 或 'OR')
            data: 提交数据

        Returns:
            条件是否满足
        """
        if not rules:
            return True

        results = [
            ConditionEvaluator.evaluate_condition(rule, data)
            for rule in rules
        ]

        if logic.upper() == 'AND':
            return all(results)
        elif logic.upper() == 'OR':
            return any(results)
        else:
            logger.warning(f"Unknown logic operator: {logic}, defaulting to AND")
            return all(results)


def evaluate_flow_condition(
    condition: Union[Dict[str, Any], None],
    submission_data: Dict[str, Any]
) -> bool:
    """
    评估流程路由条件

    Args:
        condition: JsonLogic 条件表达式（可为 None）
        submission_data: 表单提交数据

    Returns:
        条件是否满足（None 条件默认返回 True）
    """
    if condition is None:
        return True

    try:
        return ConditionEvaluator.evaluate_condition(condition, submission_data)
    except Exception as e:
        logger.error(f"Error evaluating condition: {e}", exc_info=True)
        # 条件评估失败时，默认返回 False（不通过）
        return False
