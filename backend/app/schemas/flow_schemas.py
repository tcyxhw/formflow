"""
模块用途: 流程定义/草稿/快照相关 Schema
依赖配置: 无
数据流向: API Request -> Pydantic 校验 -> Service 层
函数清单:
    - _validate_jsonlogic(): 校验 JsonLogic 表达式结构
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, RootModel, validator

JsonLogicDict = Dict[str, Any]


# ==================== 枚举定义 ====================

class WorkflowStatus(str, Enum):
    """流程定义状态"""
    DRAFT = "draft"
    PUBLISHED = "published"
    DISABLED = "disabled"


class InstanceStatus(str, Enum):
    """流程实例状态"""
    RUNNING = "running"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELED = "canceled"


class OperationType(str, Enum):
    """操作日志类型"""
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    CANCEL = "cancel"
    CC = "cc"


class RejectStrategy(str, Enum):
    """驳回策略"""
    TO_START = "TO_START"  # 驳回到发起人，流程结束
    TO_PREVIOUS = "TO_PREVIOUS"  # 驳回到上一个审批节点


# ==================== 类型别名 ====================

NODE_TYPE = Literal["start", "user", "auto", "condition", "cc", "end"]
ASSIGNEE_TYPE = Literal["user", "group", "role", "department", "position", "expr", "form_field", "department_post"]
APPROVE_POLICY = Literal["any", "all", "percent"]
ROUTE_MODE = Literal["exclusive", "parallel"]

LOGIC_OPERATORS = {"and", "or", "!", "if"}
COMPARISON_OPERATORS = {"==", "!=", ">", ">=", "<", "<=", "in"}
VALUE_OPERATORS = {"var", "missing", "missing_some"}


def _validate_jsonlogic(expression: JsonLogicDict) -> JsonLogicDict:
    """校验 JsonLogic 表达式是否符合基本结构。

    :param expression: JsonLogic 表达式字典
    :return: 通过校验后的原始表达式

    Time: O(1), Space: O(1)
    """

    if not isinstance(expression, dict) or not expression:
        raise ValueError("JsonLogic 表达式不能为空")

    operator = next(iter(expression))
    if operator not in LOGIC_OPERATORS | COMPARISON_OPERATORS | VALUE_OPERATORS:
        raise ValueError(f"不支持的 JsonLogic 操作符: {operator}")

    return expression


class JsonLogicExpression(RootModel[JsonLogicDict]):
    """JsonLogic 表达式封装，用于前后端规则互通。"""

    def __init__(self, **data: Any) -> None:
        _validate_jsonlogic(data)
        super().__init__(**data)

    def dict(self, *args: Any, **kwargs: Any) -> JsonLogicDict:
        return self.model_dump(*args, **kwargs)


class FlowNodeConfig(BaseModel):
    """流程节点配置。"""

    id: Optional[int] = Field(None, description="节点 ID，未保存时为空")
    temp_id: Optional[str] = Field(None, description="前端临时 ID，用于连线映射")
    name: str = Field(..., min_length=1, max_length=100, description="节点名称")
    type: NODE_TYPE = Field(..., description="节点类型")
    assignee_type: Optional[ASSIGNEE_TYPE] = Field(None, description="指派类型")
    assignee_value: Optional[Dict[str, Any]] = Field(None, description="指派参数")
    approve_policy: APPROVE_POLICY = Field("any", description="会签策略")
    approve_threshold: Optional[int] = Field(None, ge=1, le=100, description="percent 策略阈值")
    route_mode: ROUTE_MODE = Field("exclusive", description="路由模式")
    sla_hours: Optional[int] = Field(None, ge=1, le=720, description="SLA 小时数")
    allow_delegate: bool = Field(True, description="是否允许代理")
    auto_approve_enabled: bool = Field(False, description="是否开启自动审批")
    auto_approve_cond: Optional[JsonLogicExpression] = Field(None, description="自动通过条件")
    auto_reject_cond: Optional[JsonLogicExpression] = Field(None, description="自动驳回条件")
    auto_sample_ratio: float = Field(0.0, ge=0.0, le=1.0, description="抽检比例")
    auto_claim_on_auto_action: bool = Field(False, description="自动审批时自动认领")
    reject_strategy: RejectStrategy = Field(RejectStrategy.TO_START, description="驳回策略")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")

    @validator("auto_sample_ratio")
    def ensure_sample_ratio(cls, value: float) -> float:
        if value is None:
            return 0.0
        return round(value, 4)


class FlowRouteConfig(BaseModel):
    """流程路由配置。"""

    id: Optional[int] = Field(None, description="路由 ID")
    from_node_key: str = Field(..., min_length=1, description="来源节点 Key 或 ID")
    to_node_key: str = Field(..., min_length=1, description="目标节点 Key 或 ID")
    priority: int = Field(1, ge=1, le=999, description="路由优先级")
    condition: Optional[JsonLogicExpression] = Field(None, description="路由条件")
    is_default: bool = Field(False, description="是否为默认路由")


class FlowDraftPayload(BaseModel):
    """流程草稿的完整配置载荷。"""

    version: int = Field(..., ge=1, description="乐观锁版本")
    nodes: List[FlowNodeConfig] = Field(..., description="节点配置列表")
    routes: List[FlowRouteConfig] = Field(..., description="路由配置列表")
    nodes_graph: Dict[str, Any] = Field(default_factory=dict, description="前端画布坐标数据")


class FlowDraftResponse(FlowDraftPayload):
    """草稿响应。"""

    flow_definition_id: int = Field(..., description="所属流程 ID")
    updated_by: Optional[int] = Field(None, description="最后编辑人")
    updated_at: Optional[datetime] = Field(None, description="最后更新时间")
    last_snapshot_id: Optional[int] = Field(None, description="最近同步快照 ID")


class FlowDraftSaveRequest(FlowDraftPayload):
    """保存草稿请求。"""

    flow_definition_id: int = Field(..., ge=1, description="流程 ID")


class FlowPublishRequest(BaseModel):
    """发布流程请求。"""

    flow_definition_id: int = Field(..., ge=1, description="流程 ID")
    version: int = Field(..., ge=1, description="草稿版本，用于乐观锁判断")
    version_tag: Optional[str] = Field(None, max_length=50, description="发布版本号，例如 v1.0.0")
    changelog: Optional[str] = Field(None, max_length=500, description="发布说明")


class FlowSnapshotResponse(BaseModel):
    """流程快照响应。"""

    id: int
    flow_definition_id: int
    version_tag: str
    rules_payload: Dict[str, Any]
    metadata_json: Dict[str, Any] | None = None
    created_at: datetime
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


class FlowDefinitionResponse(BaseModel):
    """流程定义概要。"""

    id: int
    form_id: int
    name: str
    version: int
    active_snapshot_id: Optional[int]
    active_snapshot_tag: Optional[str] = Field(None, description="当前生效快照版本")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FlowDefinitionDetailResponse(BaseModel):
    """包含草稿与快照信息的流程定义详情。"""

    definition: FlowDefinitionResponse
    draft: Optional[FlowDraftResponse] = None
    active_snapshot: Optional[FlowSnapshotResponse] = None
    snapshots: List[FlowSnapshotResponse] = Field(default_factory=list)
