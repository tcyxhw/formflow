"""
模块用途: 审批任务 Schema 定义
依赖配置: 无
数据流向: ORM 模型 -> Pydantic Schema -> API 入参与响应
函数清单:
    - TaskListRequest(): 待办查询入参
    - TaskResponse(): 待办任务基础信息
    - TaskActionRequest(): 任务操作入参
    - ProcessTimelineResponse(): 流程轨迹响应
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, PositiveInt


class TaskStatus(str, Enum):
    """任务状态枚举"""

    OPEN = "open"
    CLAIMED = "claimed"
    COMPLETED = "completed"
    CANCELED = "canceled"


class SlaLevel(str, Enum):
    """SLA 等级枚举"""

    UNKNOWN = "unknown"
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EXPIRED = "expired"


class TaskListRequest(BaseModel):
    """待办任务查询参数"""

    page: PositiveInt = Field(default=1, description="页码，从 1 开始")
    page_size: PositiveInt = Field(default=20, le=100, description="每页数量")
    status: Optional[TaskStatus] = Field(default=None, description="按状态筛选")
    only_mine: bool = Field(default=True, description="仅查询个人任务")
    include_group_tasks: bool = Field(default=True, description="包含所在小组的待办池")
    keyword: Optional[str] = Field(default=None, description="关键词匹配，针对节点名称/表单数据")
    sla_level: Optional[SlaLevel] = Field(default=None, description="按 SLA 等级筛选")

    @property
    def offset(self) -> int:
        """分页偏移量。

        :return: 偏移量

        Time: O(1), Space: O(1)
        """

        return (self.page - 1) * self.page_size


class TaskAssigneeInfo(BaseModel):
    """任务指派信息"""

    user_id: Optional[int] = Field(default=None, description="指派用户 ID")
    group_id: Optional[int] = Field(default=None, description="指派小组 ID")
    group_name: Optional[str] = Field(default=None, description="小组名称")


class TaskResponse(BaseModel):
    """待办任务基本信息"""

    id: int
    process_instance_id: int
    process_state: str = Field(default="running", description="流程状态：running/finished/canceled")
    node_id: int
    node_name: Optional[str]
    flow_name: Optional[str]
    status: TaskStatus
    action: Optional[str]
    payload: Optional[Dict[str, object]]
    assignee: TaskAssigneeInfo
    claimed_by: Optional[int]
    claimed_at: Optional[datetime]
    due_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    sla_hours: Optional[int]
    is_overdue: bool
    remaining_sla_minutes: Optional[int] = Field(default=None, description="剩余 SLA 分钟数")
    sla_level: SlaLevel = Field(default=SlaLevel.UNKNOWN, description="SLA 等级：normal/warning/critical/expired")
    submitter_user_id: Optional[int] = Field(default=None, description="提交人ID")
    submitter_name: Optional[str] = Field(default=None, description="提交人姓名")
    form_data_snapshot: Optional[Dict[str, object]] = Field(default=None, description="表单数据快照")
    form_id: Optional[int] = Field(default=None, description="表单ID")


class TaskListResponse(BaseModel):
    """待办任务分页响应"""

    items: List[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TaskSlaSummary(BaseModel):
    """SLA 汇总统计"""

    total: int = Field(default=0, ge=0, description="任务总数")
    unknown: int = Field(default=0, ge=0, description="无截止时间任务数")
    normal: int = Field(default=0, ge=0, description="正常任务数")
    warning: int = Field(default=0, ge=0, description="预警任务数")
    critical: int = Field(default=0, ge=0, description="紧急任务数")
    expired: int = Field(default=0, ge=0, description="已超时任务数")


class TaskActionRequest(BaseModel):
    """任务操作请求体"""

    action: str = Field(min_length=1, description="动作标识：approve/reject/transfer 等")
    comment: Optional[str] = Field(default=None, description="审批意见")
    extra_data: Optional[Dict[str, object]] = Field(default=None, description="额外数据，如附件、抄送列表")


class TaskTransferRequest(BaseModel):
    """任务转交请求"""

    target_user_id: int = Field(..., ge=1, description="转交目标用户 ID")
    message: Optional[str] = Field(default=None, description="转交说明")


class TaskDelegateRequest(BaseModel):
    """任务委托请求"""

    delegate_user_id: int = Field(..., ge=1, description="受托人 ID")
    expire_hours: Optional[int] = Field(default=None, ge=1, description="委托有效时长 (小时)")
    message: Optional[str] = Field(default=None, description="委托说明")


class TaskAddSignRequest(BaseModel):
    """加签请求体"""

    user_ids: List[int] = Field(..., min_items=1, description="需要加签的用户 ID 列表")
    message: Optional[str] = Field(default=None, description="加签说明")


class TimelineEntry(BaseModel):
    """流程轨迹节点"""

    task_id: Optional[int]
    node_id: Optional[int]
    node_name: Optional[str]
    status: Optional[TaskStatus]
    action: Optional[str]
    actor_user_id: Optional[int]
    actor_name: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    due_at: Optional[datetime]
    remaining_sla_minutes: Optional[int] = Field(default=None, description="剩余 SLA 分钟数")
    sla_level: SlaLevel = Field(default=SlaLevel.UNKNOWN, description="SLA 等级")
    comment: Optional[str]
    actions: List["TimelineAction"] = Field(default_factory=list)


class TimelineAction(BaseModel):
    """流程节点内的操作记录"""

    action: str = Field(..., description="操作标识")
    actor_user_id: Optional[int]
    actor_name: Optional[str]
    comment: Optional[str]
    created_at: Optional[datetime]
    detail: Optional[Dict[str, object]] = None


class ProcessTimelineResponse(BaseModel):
    """流程轨迹响应体"""

    process_instance_id: int
    state: str
    entries: List[TimelineEntry]
