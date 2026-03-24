"""
模块用途: 流程路由条件评估器
依赖配置: 无
数据流向: FlowRoute.condition_json -> RouteEvaluator -> ProcessService
函数清单:
    - RouteEvaluator.evaluate(): 评估路由条件
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field, RootModel


class RouteRule(BaseModel):
    """单条路由规则或规则集合。"""

    logic: Optional[str] = Field(default=None, description="逻辑类型：and/or")
    rules: Optional[List["RouteRule"]] = Field(default=None, description="子规则列表")
    field: Optional[str] = Field(default=None, description="上下文字段名，支持嵌套访问")
    operator: Optional[str] = Field(default="equals", description="比较操作符")
    value: Optional[Any] = Field(default=None, description="比较值")

    class Config:
        extra = "ignore"


RouteRule.model_rebuild()


class RouteCondition(RootModel):
    """支持列表或单条规则的条件容器。"""

    root: RouteRule


def _compare_numbers(actual: Any, expected: Any, comparator: Callable[[float, float], bool]) -> bool:
    """数值型比较，失败则返回 False。"""

    try:
        actual_num = float(actual)
        expected_num = float(expected)
    except (TypeError, ValueError):
        return False
    return comparator(actual_num, expected_num)


def _eval_between(actual: Any, expected: Any) -> bool:
    """BETWEEN运算符：actual >= expected[0] AND actual <= expected[1]

    :param actual: 实际值
    :param expected: 期望值范围 [min, max]
    :return: 是否在范围内

    Time: O(1), Space: O(1)
    """
    if not isinstance(expected, (list, tuple)) or len(expected) != 2:
        return False
    try:
        actual_num = float(actual)
        return actual_num >= float(expected[0]) and actual_num <= float(expected[1])
    except (TypeError, ValueError):
        return False


def _eval_has_any(actual: Any, expected: Any) -> bool:
    """HAS_ANY运算符：actual和expected有交集

    :param actual: 实际值列表
    :param expected: 期望值列表
    :return: 是否有交集

    Time: O(N), Space: O(N)
    """
    if not isinstance(actual, (list, tuple, set)):
        return False
    if not isinstance(expected, (list, tuple, set)):
        return False
    return bool(set(actual) & set(expected))


def _eval_has_all(actual: Any, expected: Any) -> bool:
    """HAS_ALL运算符：actual包含expected全部元素

    :param actual: 实际值列表
    :param expected: 期望值列表
    :return: 是否包含全部元素

    Time: O(N), Space: O(N)
    """
    if not isinstance(actual, (list, tuple, set)):
        return False
    if not isinstance(expected, (list, tuple, set)):
        return False
    return set(expected).issubset(set(actual))


def _eval_is_empty(actual: Any, _expected: Any) -> bool:
    """IS_EMPTY运算符

    :param actual: 实际值
    :param _expected: 未使用
    :return: 是否为空

    Time: O(1), Space: O(1)
    """
    if actual is None:
        return True
    if isinstance(actual, str) and actual == "":
        return True
    if isinstance(actual, (list, tuple, dict)) and len(actual) == 0:
        return True
    return False


def _eval_is_not_empty(actual: Any, _expected: Any) -> bool:
    """IS_NOT_EMPTY运算符

    :param actual: 实际值
    :param _expected: 未使用
    :return: 是否非空

    Time: O(1), Space: O(1)
    """
    return not _eval_is_empty(actual, _expected)


# 运算符映射字典
OPERATOR_MAP: Dict[str, Callable[[Any, Any], bool]] = {
    "equals": lambda actual, expected: actual == expected,
    "not_equals": lambda actual, expected: actual != expected,
    "gt": lambda actual, expected: _compare_numbers(actual, expected, lambda a, b: a > b),
    "gte": lambda actual, expected: _compare_numbers(actual, expected, lambda a, b: a >= b),
    "lt": lambda actual, expected: _compare_numbers(actual, expected, lambda a, b: a < b),
    "lte": lambda actual, expected: _compare_numbers(actual, expected, lambda a, b: a <= b),
    "in": lambda actual, expected: actual in expected if isinstance(expected, (list, tuple, set)) else False,
    "not_in": lambda actual, expected: actual not in expected if isinstance(expected, (list, tuple, set)) else True,
    "contains": lambda actual, expected: isinstance(actual, (list, tuple, set, str)) and expected in actual,
    "not_contains": lambda actual, expected: not (isinstance(actual, (list, tuple, set, str)) and expected in actual),
    "starts_with": lambda actual, expected: isinstance(actual, str) and isinstance(expected, str) and actual.startswith(expected),
    "ends_with": lambda actual, expected: isinstance(actual, str) and isinstance(expected, str) and actual.endswith(expected),
    "is_null": lambda actual, _expected: actual is None,
    "not_null": lambda actual, _expected: actual is not None,
    "between": _eval_between,
    "has_any": _eval_has_any,
    "has_all": _eval_has_all,
    "is_empty": _eval_is_empty,
    "is_not_empty": _eval_is_not_empty,
}


class RouteEvaluator:
    """路由条件评估器。"""

    LOGIC_MAP: Dict[str, Callable[[List[bool]], bool]] = {
        "and": all,
        "or": any,
    }

    @classmethod
    def evaluate(cls, condition_data: Optional[Dict[str, Any]], context: Dict[str, Any]) -> bool:
        """评估路由条件。

        :param condition_data: 路由条件 JSON
        :param context: 需要参与判断的上下文字典
        :return: 条件是否成立

        Time: O(N), Space: O(N)
        """

        if not condition_data:
            return True

        try:
            condition = RouteCondition.model_validate(condition_data)
        except Exception:
            # 条件数据格式无效，返回 False 表示不匹配
            return False

        return cls._evaluate_rule(condition.root, context)

    @classmethod
    def _evaluate_rule(cls, rule: RouteRule, context: Dict[str, Any]) -> bool:
        """递归求值单条规则。"""

        logic = (rule.logic or "").lower()
        if logic in cls.LOGIC_MAP and rule.rules:
            results = [cls._evaluate_rule(sub_rule, context) for sub_rule in rule.rules]
            aggregator = cls.LOGIC_MAP[logic]
            return aggregator(results)

        if not rule.field:
            return True

        operator = (rule.operator or "equals").lower()
        actual = cls._extract_value(context, rule.field)
        evaluator = OPERATOR_MAP.get(operator)
        if not evaluator:
            return False

        return evaluator(actual, rule.value)

    @staticmethod
    def _extract_value(context: Dict[str, Any], field: str) -> Any:
        """支持点号路径的上下文字段提取。"""

        value: Any = context
        for part in field.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value
