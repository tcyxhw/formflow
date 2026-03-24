"""
模块用途: 审计日志Pydantic模型
依赖配置: 无
数据流向: API请求 -> Schema验证 -> Service处理
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AuditLogQueryRequest(BaseModel):
    """审计日志查询请求"""

    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    actor_user_id: Optional[int] = Field(None, description="操作人ID")
    resource_type: Optional[str] = Field(None, description="资源类型: form/submission/task")
    action: Optional[str] = Field(None, description="动作类型")
    date_from: Optional[datetime] = Field(None, description="开始时间")
    date_to: Optional[datetime] = Field(None, description="结束时间")
    resource_id: Optional[int] = Field(None, description="资源ID（用于详情页）")
    only_mine: bool = Field(False, description="仅查看自己的")


class AuditLogResponse(BaseModel):
    """审计日志响应"""

    id: int
    tenant_id: int
    actor_user_id: Optional[int] = Field(None, description="操作人ID")
    actor_name: Optional[str] = Field(None, description="用户姓名")
    action: str = Field(..., description="动作")
    resource_type: str = Field(..., description="资源类型")
    resource_id: Optional[int] = Field(None, description="资源ID")
    before_json: Optional[Dict[str, Any]] = Field(None, description="变更前快照")
    after_json: Optional[Dict[str, Any]] = Field(None, description="变更后快照")
    ip: Optional[str] = Field(None, description="来源IP")
    ua: Optional[str] = Field(None, description="用户代理")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """审计日志列表响应"""

    items: List[AuditLogResponse] = Field(default_factory=list, description="日志记录")
    total: int = Field(0, description="总数")


class AuditLogExportRequest(BaseModel):
    """审计日志导出请求（支持批量）"""

    actor_user_id: Optional[int] = Field(None, description="操作人ID")
    resource_type: Optional[str] = Field(None, description="资源类型")
    action: Optional[str] = Field(None, description="动作类型")
    date_from: Optional[datetime] = Field(None, description="开始时间")
    date_to: Optional[datetime] = Field(None, description="结束时间")
    resource_ids: Optional[List[int]] = Field(None, description="批量导出特定资源")


class ChangeComparisonItem(BaseModel):
    """变更对比项"""

    field: str = Field(..., description="字段名")
    before: Any = Field(None, description="变更前值")
    after: Any = Field(None, description="变更后值")
    change_type: str = Field(..., description="变更类型: added/modified/removed")


class AuditLogCompareResponse(BaseModel):
    """变更对比响应"""

    log_id: int = Field(..., description="日志ID")
    action: str = Field(..., description="动作")
    resource_type: str = Field(..., description="资源类型")
    changes: List[ChangeComparisonItem] = Field(default_factory=list, description="变更列表")
    created_at: datetime = Field(..., description="创建时间")
