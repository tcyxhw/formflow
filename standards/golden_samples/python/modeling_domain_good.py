"""
正例: 充血领域模型

适用场景:
- 存在多条状态转换规则、跨字段约束、领域不变量
- 审批流、状态机、核心业务规则集中的模块

设计要点:
- 领域对象同时包含数据与行为
- 关键不变量在模型内部维护，外部无法绕过
- 状态枚举用 Enum 而非裸字符串

参考: Fowler, Patterns of Enterprise Application Architecture - Domain Model
"""

from dataclasses import dataclass, field
from enum import Enum


class FormStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class FormAggregate:
    id: str
    tenant_id: str
    status: FormStatus = FormStatus.DRAFT
    fields: dict[str, object] = field(default_factory=dict)

    def submit(self) -> None:
        if not self.fields:
            raise ValueError("表单为空，不能提交")
        if self.status != FormStatus.DRAFT:
            raise ValueError(f"当前状态 {self.status.value}，只有草稿可提交")
        self.status = FormStatus.SUBMITTED

    def approve(self) -> None:
        if self.status != FormStatus.SUBMITTED:
            raise ValueError(f"当前状态 {self.status.value}，只有已提交表单可审批")
        self.status = FormStatus.APPROVED

    def reject(self, reason: str) -> None:
        if self.status != FormStatus.SUBMITTED:
            raise ValueError(f"当前状态 {self.status.value}，只有已提交表单可驳回")
        if not reason.strip():
            raise ValueError("驳回必须填写原因")
        self.status = FormStatus.REJECTED
