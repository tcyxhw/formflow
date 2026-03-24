"""
正例: singledispatch 分发

适用场景:
- 类型集合是开放的，未来可能新增类型
- 需要允许外部代码在不修改原函数的情况下注册新类型处理
- 分发逻辑会持续增长

何时不需要:
- 类型集合封闭、分支少、逻辑简单时，if/elif 可能更直观

设计要点:
- 基函数定义默认行为或抛出 TypeError
- 每个类型注册独立处理

参考:
- PEP 443 — Single-dispatch generic functions
"""

from functools import singledispatch


@singledispatch
def normalize(value):
    raise TypeError(f"unsupported type: {type(value).__name__}")


@normalize.register
def _(value: str) -> str:
    return value.strip()


@normalize.register
def _(value: list) -> list:
    return [normalize(v) for v in value]


if __name__ == "__main__":
    print(normalize("  hello  "))
    print(normalize([" a ", " b "]))
