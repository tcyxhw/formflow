"""
反例: 贫血模型（当领域逻辑复杂时）

何时算反模式:
- 存在多条状态转换、跨字段校验、领域不变量
- 把这些规则外置到 Service 后，规则散落、重复、漂移

何时不算反模式:
- 纯 CRUD、无复杂业务规则的场景
- Transaction Script 对简单场景完全合理

问题:
- 模型只有数据，没有行为
- 业务规则散落在 Service 中，多个调用方可能各写一套
- 状态用裸字符串，拼写错误无法在编译期发现
"""

from dataclasses import dataclass


@dataclass
class Form:
    id: str
    tenant_id: str
    status: str
    fields: dict[str, object]


class FormService:
    """业务规则全部外置，模型沦为数据容器。"""

    def submit(self, form: Form) -> None:
        if not form.fields:
            raise ValueError("表单为空")
        if form.status != "draft":
            raise ValueError("只有草稿可以提交")
        form.status = "submitted"

    def approve(self, form: Form) -> None:
        if form.status != "submitted":
            raise ValueError("只有已提交表单可以审批")
        form.status = "approved"


class AnotherService:
    """另一个 Service 也在操作同一状态，规则容易不一致。"""

    def force_approve(self, form: Form) -> None:
        form.status = "approved"
