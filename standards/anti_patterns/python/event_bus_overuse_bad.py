"""
反例: 滥用总线替代直接调用

何时算反模式:
- 发布者和消费者在同一模块内
- 只有一个消费者，不存在一对多需求
- 用总线的唯一效果是把直接调用变成间接调用

何时不算反模式:
- 真正存在跨模块解耦、一对多通知的需求

问题:
- 控制流被隐藏，断点调试和异常追踪更困难
- 事件用裸 dict 而非类型化对象，消费端无类型提示
"""

from collections.abc import Callable


class EventBus:
    def __init__(self) -> None:
        self._handlers: list[Callable[[object], None]] = []

    def subscribe(self, handler: Callable[[object], None]) -> None:
        self._handlers.append(handler)

    def publish(self, event: object) -> None:
        for handler in self._handlers:
            handler(event)


class UserService:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def rename_user(self, user_id: str, new_name: str) -> None:
        # 这里明明可以直接调用本地逻辑，却强行发事件
        self.bus.publish(
            {
                "type": "UserRenamed",
                "user_id": user_id,
                "new_name": new_name,
            }
        )
