"""\
模块用途: ProcessService 自动审批与抽检逻辑单测
依赖配置: pytest + sqlite (仅内存对象, 无需真实 DB)
数据流向: 伪造上下文 -> ProcessService 静态方法 -> 决策/采样结果
函数清单:
    - build_condition(): 构建路由条件 JSON
    - test_auto_approve_condition_matches(): 命中自动通过
    - test_auto_reject_has_priority(): 自动驳回优先级高
    - test_invalid_condition_returns_validation_error(): 非法条件需给出校验错误
    - test_should_sample_ratio_boundaries(): 抽检比例边界
    - test_should_sample_is_deterministic(): 抽检结果可复现
    - test_build_auto_action_log_detail_sanitizes_context(): 日志上下文被裁剪
"""
from __future__ import annotations

import hashlib
from types import SimpleNamespace
from typing import Any, Dict

import pytest

from app.services.process_service import AutoActionDecision, ProcessService


def build_condition(field: str, operator: str, value: Any) -> Dict[str, Any]:
    """构造简单路由条件 JSON。

    :param field: 字段路径
    :param operator: 比较操作符
    :param value: 比较值

    Time: O(1), Space: O(1)
    """

    return {
        "logic": None,
        "field": field,
        "operator": operator,
        "value": value,
    }


def test_auto_approve_condition_matches() -> None:
    """满足自动通过条件时应返回 approve。

    Time: O(1), Space: O(1)
    """

    node = SimpleNamespace(
        auto_approve_enabled=True,
        auto_reject_cond=None,
        auto_approve_cond=build_condition("payload.score", "gte", 80),
    )
    context = {"payload": {"score": 90}}

    decision = ProcessService._evaluate_auto_action(node, context)

    assert decision.outcome == "approve"
    assert decision.matched_condition == "auto_approve_cond"


def test_auto_reject_has_priority() -> None:
    """自动驳回条件命中时必须优先生效。

    Time: O(1), Space: O(1)
    """

    node = SimpleNamespace(
        auto_approve_enabled=True,
        auto_reject_cond=build_condition("payload.flag", "equals", "bad"),
        auto_approve_cond=build_condition("payload.score", "gte", 80),
    )
    context = {"payload": {"flag": "bad", "score": 99}}

    decision = ProcessService._evaluate_auto_action(node, context)

    assert decision.outcome == "reject"
    assert decision.matched_condition == "auto_reject_cond"


def test_invalid_condition_returns_validation_error() -> None:
    """条件结构非法时需返回验证错误并跳过自动动作。

    Time: O(1), Space: O(1)
    """

    node = SimpleNamespace(
        auto_approve_enabled=True,
        auto_reject_cond=None,
        auto_approve_cond={},  # 缺少 root 结构
    )

    decision = ProcessService._evaluate_auto_action(node, {"payload": {}})

    assert decision.outcome is None
    assert decision.validation_error is not None


def test_should_sample_ratio_boundaries() -> None:
    """抽检比例的边界值需按期望返回布尔值。

    Time: O(1), Space: O(1)
    """

    process = SimpleNamespace(id=1)
    node_zero = SimpleNamespace(auto_sample_ratio=0, id=1)
    node_full = SimpleNamespace(auto_sample_ratio=1, id=1)
    node_invalid = SimpleNamespace(auto_sample_ratio="oops", id=1)

    assert ProcessService._should_sample_for_manual_review(process, node_zero) is False
    assert ProcessService._should_sample_for_manual_review(process, node_full) is True
    assert ProcessService._should_sample_for_manual_review(process, node_invalid) is False


def test_should_sample_is_deterministic() -> None:
    """相同 process/node 组合的抽检结果应保持可复现。

    Time: O(1), Space: O(1)
    """

    process = SimpleNamespace(id=12345)
    node = SimpleNamespace(auto_sample_ratio=0.5, id=67890)
    ratio_value = float(node.auto_sample_ratio)

    seed = f"{process.id}:{node.id}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    expected = int(digest[:8], 16) / 0xFFFFFFFF < ratio_value

    first = ProcessService._should_sample_for_manual_review(process, node)
    second = ProcessService._should_sample_for_manual_review(process, node)

    assert first == expected
    assert second == expected


def test_build_auto_action_log_detail_sanitizes_context() -> None:
    """日志详情应包含裁剪后的上下文与节点信息。

    Time: O(1), Space: O(1)
    """

    node = SimpleNamespace(id=11, name="节点 A")
    decision = AutoActionDecision(
        outcome="approve",
        matched_condition="auto_approve_cond",
        condition_payload={"field": "payload.score"},
        validation_error=None,
    )
    context = {
        "score": 95,
        "meta": {"nested": True},
    }

    detail = ProcessService._build_auto_action_log_detail(
        node=node,
        decision=decision,
        context=context,
        sampled=False,
    )

    assert detail["node_id"] == 11
    assert detail["decision"] == "approve"
    assert "meta" in detail["context_snapshot"]
    assert isinstance(detail["context_snapshot"]["meta"], str)
    assert len(detail["context_snapshot"]["meta"]) <= 200


def test_resolve_percent_threshold_prefers_explicit_field() -> None:
    """显式 approve_threshold 应优先生效，并进行边界裁剪。

    Time: O(1), Space: O(1)
    """

    # 显式 80，应直接返回 80
    node = SimpleNamespace(approve_threshold=80, assignee_value={"percent_threshold": 30})
    assert ProcessService._resolve_percent_threshold(node) == 80

    # 小于 1 的值被裁剪为 1
    node_too_small = SimpleNamespace(approve_threshold=0, assignee_value={"percent_threshold": 90})
    assert ProcessService._resolve_percent_threshold(node_too_small) == 1

    # 大于 100 的值被裁剪为 100
    node_too_large = SimpleNamespace(approve_threshold=1000, assignee_value={"percent_threshold": 10})
    assert ProcessService._resolve_percent_threshold(node_too_large) == 100


def test_resolve_percent_threshold_fallbacks_to_legacy_field() -> None:
    """approve_threshold 为空时应回退到 assignee_value.percent_threshold，并做防御处理。

    Time: O(1), Space: O(1)
    """

    # 回退到旧字段 60
    node_legacy = SimpleNamespace(approve_threshold=None, assignee_value={"percent_threshold": 60})
    assert ProcessService._resolve_percent_threshold(node_legacy) == 60

    # 旧字段缺失时默认 100
    node_missing = SimpleNamespace(approve_threshold=None, assignee_value={})
    assert ProcessService._resolve_percent_threshold(node_missing) == 100

    # 旧字段为非法字符串时同样回退到 100
    node_invalid = SimpleNamespace(approve_threshold=None, assignee_value={"percent_threshold": "oops"})
    assert ProcessService._resolve_percent_threshold(node_invalid) == 100
