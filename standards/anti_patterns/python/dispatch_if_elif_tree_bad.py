"""
反例: 膨胀的 if/elif 分发树（当类型集合需要开放扩展时）

何时算反模式:
- 类型集合是开放的，新增类型必须修改原函数
- 分支持续增长，已明显影响可读性和扩展性
- 多处代码各自维护类似的 if/elif 树

何时不算反模式:
- 类型集合封闭且分支较少
- 所有分支在同一处维护，逻辑简单
- 此时 if/elif 比 singledispatch 更直观，不必强行切换

问题（当属于反模式时）:
- 新增类型必须找到并修改原函数
- 分支多了容易遗漏
- 外部代码无法在不修改源码的情况下扩展
"""

def normalize(value):
    if isinstance(value, str):
        return value.strip()
    elif isinstance(value, list):
        return [normalize(v) for v in value]
    elif isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    elif isinstance(value, tuple):
        return tuple(normalize(v) for v in value)
    elif isinstance(value, set):
        return {normalize(v) for v in value}
    elif isinstance(value, frozenset):
        return frozenset(normalize(v) for v in value)
    elif isinstance(value, bytes):
        return value.strip()
    else:
        raise TypeError(f"unsupported type: {type(value).__name__}")
