"""
反例: 管线步骤依赖隐藏共享状态

何时算反模式:
- 步骤表面签名是 dict -> dict，实际还在读取外部可变状态
- 步骤顺序不能调整，因为后面的步骤隐式依赖前面步骤写入的全局状态

问题:
- 单独测试 step2 需要先手动设置 ctx，测试脆弱
- 调换 step1 和 step2 的顺序，运行时才发现问题
- 并发环境下 ctx 被多个请求共享，可能数据错乱
"""

ctx: dict[str, object] = {}


def step1(data: dict[str, object]) -> dict[str, object]:
    ctx["raw"] = data
    return data


def step2(data: dict[str, object]) -> dict[str, object]:
    if "raw" not in ctx:
        raise RuntimeError("missing raw — step1 必须先运行")
    copied = dict(data)
    copied["validated"] = True
    return copied


# 更合理的做法:
# def step1(data: dict[str, object]) -> dict[str, object]:
#     return {**data, "raw_snapshot": dict(data)}
#
# def step2(data: dict[str, object]) -> dict[str, object]:
#     if "raw_snapshot" not in data:
#         raise ValueError("missing raw_snapshot")
#     return {**data, "validated": True}
