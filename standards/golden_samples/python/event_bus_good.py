"""
正例: 事件总线（通知型副作用场景）

适用场景:
- 跨模块的一对多通知
- 发布者不需要知道消费者的存在
- 表单提交后需要同时: 发通知、写审计日志、打点

设计要点:
- 事件是不可变数据对象
- 订阅和发布解耦
- 本样例中的异常隔离仅适用于“非关键通知型副作用”
- 如果 handler 属于关键业务链路，应 fail fast 或显式汇总失败结果

参考:
- Django signals 文档对“隐式耦合与可维护性”的警告
"""

from dataclasses import dataclass
from collections import defaultdict
from collections.abc import Callable
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FormSubmitted:
    form_id: str
    tenant_id: str


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable[[object], None]]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable[[object], None]) -> None:
        self._handlers[event_type].append(handler)

    def publish_non_critical(self, event: object) -> None:
        """
        仅用于非关键通知型副作用事件。
        单个 handler 失败不阻塞后续 handler。
        """
        for handler in self._handlers[type(event)]:
            try:
                handler(event)
            except Exception:
                logger.exception("non-critical handler %s failed for %r", handler.__name__, event)


def send_notification(event: FormSubmitted) -> None:
    print(f"发送通知: {event.form_id}")


def write_audit_log(event: FormSubmitted) -> None:
    print(f"写审计日志: {event.form_id}")


if __name__ == "__main__":
    bus = EventBus()
    bus.subscribe(FormSubmitted, send_notification)
    bus.subscribe(FormSubmitted, write_audit_log)
    bus.publish_non_critical(FormSubmitted(form_id="f1", tenant_id="t1"))
