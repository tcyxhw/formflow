"""
反例: 全局注册表 + 无显式发现 + 无隔离

何时算反模式:
- 注册表是模块级全局变量，测试之间互相污染
- 没有显式扫描入口，是否注册成功完全取决于 import 是否恰好发生
- 无法列举已注册项，调试困难

何时不算反模式:
- Flask/FastAPI 的路由装饰器也依赖注册
- 但它们有显式容器（app / router）做隔离
- 且有显式装配/发现机制（如 include_router）
- 关键区别是：有容器隔离 + 有显式发现机制 → 可接受
              裸全局 dict + 靠 import 碰运气 → 高风险

问题:
- REGISTRY 是裸全局 dict，所有测试共享同一份
- 没有重复注册检测
- 新模块写了 @register 但忘记 import → 静默失败
"""

REGISTRY: dict[str, object] = {}


def register(name: str):
    def deco(fn):
        REGISTRY[name] = fn
        return fn
    return deco


@register("csv")
def export_csv(data: str) -> str:
    return f"csv:{data}"


# 看起来可用，但:
# 1. 只有该模块被 import 时才注册
# 2. 测试 A import 了，测试 B 没 import → 行为不一致
# 3. 没有地方能列出“到底注册了什么”
