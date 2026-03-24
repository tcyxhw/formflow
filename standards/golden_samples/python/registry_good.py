"""
正例: 显式注册表

适用场景:
- 存在真实扩展点（如: 多种导出格式、多种字段类型）
- 需要在运行时发现、查询、列举已注册的实现

设计要点:
- 注册表是显式对象，不是模块级全局变量
- 重复注册检测
- 缺失时给出明确报错
- 支持列举所有已注册项（便于调试和文档生成）

参考:
- pluggy PluginManager 的 register()/unregister() 设计
"""

from collections.abc import Callable


class HandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[str], str]] = {}

    def register(self, name: str, handler: Callable[[str], str]) -> None:
        if name in self._handlers:
            raise ValueError(f"handler already registered: {name}")
        self._handlers[name] = handler

    def get(self, name: str) -> Callable[[str], str]:
        try:
            return self._handlers[name]
        except KeyError as exc:
            available = ", ".join(sorted(self._handlers)) or "(none)"
            raise LookupError(
                f"unknown handler: {name!r}; available: {available}"
            ) from exc

    def list_registered(self) -> list[str]:
        return sorted(self._handlers)


def export_csv(data: str) -> str:
    return f"csv:{data}"


def export_xlsx(data: str) -> str:
    return f"xlsx:{data}"


if __name__ == "__main__":
    registry = HandlerRegistry()
    registry.register("csv", export_csv)
    registry.register("xlsx", export_xlsx)

    print(f"已注册: {registry.list_registered()}")
    exporter = registry.get("csv")
    print(exporter("payload"))
