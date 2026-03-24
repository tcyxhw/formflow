"""
正例: 组合式管线

适用场景:
- 数据需要经过多个处理步骤
- 步骤可能需要重组、跳过、单独测试

设计要点:
- 每一步输入输出类型一致（如 dict -> dict）
- 步骤是纯函数或接近纯函数，不依赖外部隐式状态
- 步骤顺序由调用方显式定义
- 每一步可单独单测

参考:
- Unix 管道哲学 / 函数组合式处理思路
"""

from collections.abc import Callable

Step = Callable[[dict[str, object]], dict[str, object]]


def normalize_payload(data: dict[str, object]) -> dict[str, object]:
    return {
        k: v.strip() if isinstance(v, str) else v
        for k, v in data.items()
    }


def validate_required(data: dict[str, object]) -> dict[str, object]:
    if not data.get("title"):
        raise ValueError("title is required")
    return data


def inject_tenant(tenant_id: str) -> Step:
    def step(data: dict[str, object]) -> dict[str, object]:
        return {**data, "tenant_id": tenant_id}
    return step


def run_pipeline(data: dict[str, object], steps: list[Step]) -> dict[str, object]:
    result = data
    for step in steps:
        result = step(result)
    return result


if __name__ == "__main__":
    pipeline = [
        normalize_payload,
        validate_required,
        inject_tenant("t1"),
    ]
    result = run_pipeline({"title": " hello "}, pipeline)
    print(result)
