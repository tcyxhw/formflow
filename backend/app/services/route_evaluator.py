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


class RouteEvaluator:
    """路由条件评估器。"""

    OPERATOR_MAP: Dict[str, Callable[[Any, Any], bool]] = {
        "equals": lambda actual, expected: actual == expected,
        "not_equals": lambda actual, expected: actual != expected,
        "gt": lambda actual, expected: RouteEvaluator._compare_numbers(actual, expected, lambda a, b: a > b),
        "gte": lambda actual, expected: RouteEvaluator._compare_numbers(actual, expected, lambda a, b: a >= b),
        "lt": lambda actual, expected: RouteEvaluator._compare_numbers(actual, expected, lambda a, b: a < b),
        "lte": lambda actual, expected: RouteEvaluator._compare_numbers(actual, expected, lambda a, b: a <= b),
        "in": lambda actual, expected: actual in expected if isinstance(expected, (list, tuple, set)) else False,
        "not_in": lambda actual, expected: actual not in expected if isinstance(expected, (list, tuple, set)) else True,
        "contains": lambda actual, expected: isinstance(actual, (list, tuple, set, str)) and expected in actual,
        "starts_with": lambda actual, expected: isinstance(actual, str) and isinstance(expected, str) and actual.startswith(expected),
        "ends_with": lambda actual, expected: isinstance(actual, str) and isinstance(expected, str) and actual.endswith(expected),
        "is_null": lambda actual, _expected: actual is None,
        "not_null": lambda actual, _expected: actual is not None,
    }

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
        evaluator = cls.OPERATOR_MAP.get(operator)
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

    @staticmethod
    def _compare_numbers(actual: Any, expected: Any, comparator: Callable[[float, float], bool]) -> bool:
        """数值型比较，失败则返回 False。"""

        try:
            actual_num = float(actual)
            expected_num = float(expected)
        except (TypeError, ValueError):
            return False
        return comparator(actual_num, expected_num)
