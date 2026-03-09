"""
模块用途: 表单权限相关Schema
依赖配置: 无
数据流向: HTTP请求 -> Pydantic校验 -> Service -> 响应序列化
函数清单:
    - FormPermissionCreateRequest(): 创建权限请求体
    - FormPermissionUpdateRequest(): 更新权限请求体
    - FormPermissionResponse(): 权限信息响应
    - FormPermissionListResponse(): 权限列表响应
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class GrantType(str, Enum):
    """授权主体类型"""

    USER = "user"
    ROLE = "role"
    DEPARTMENT = "department"
    POSITION = "position"


class PermissionType(str, Enum):
    """表单权限类型"""

    VIEW = "view"
    FILL = "fill"
    EDIT = "edit"
    EXPORT = "export"
    MANAGE = "manage"


class FormPermissionBase(BaseModel):
    """表单权限基础字段"""

    grant_type: GrantType = Field(..., description="授权类型")
    grantee_id: int = Field(..., ge=1, description="授权对象ID")
    permission: PermissionType = Field(..., description="权限类型")
    valid_from: Optional[datetime] = Field(None, description="生效时间")
    valid_to: Optional[datetime] = Field(None, description="失效时间")

    @validator("valid_to")
    def validate_time_range(cls, v: Optional[datetime], values: dict) -> Optional[datetime]:
        """验证时间区间。

        Time: O(1), Space: O(1)
        """

        valid_from = values.get("valid_from")
        if v and valid_from and v < valid_from:
            raise ValueError("失效时间不能早于生效时间")
        return v


class FormPermissionCreateRequest(FormPermissionBase):
    """创建权限请求体"""

    pass


class FormPermissionUpdateRequest(BaseModel):
    """更新权限请求体"""

    valid_from: Optional[datetime] = Field(None, description="生效时间")
    valid_to: Optional[datetime] = Field(None, description="失效时间")

    @validator("valid_to")
    def validate_time_range(cls, v: Optional[datetime], values: dict) -> Optional[datetime]:
        """验证时间区间。

        Time: O(1), Space: O(1)
        """

        valid_from = values.get("valid_from")
        if v and valid_from and v < valid_from:
            raise ValueError("失效时间不能早于生效时间")
        return v


class FormPermissionResponse(FormPermissionBase):
    """权限响应模型"""

    id: int
    form_id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FormPermissionListResponse(BaseModel):
    """权限列表响应"""

    items: List[FormPermissionResponse]
    total: int


class FormPermissionMeResponse(BaseModel):
    """当前用户权限概览"""

    permissions: List[PermissionType] = Field(default_factory=list, description="已授予的权限列表")
    can_view: bool = Field(default=False, description="是否具备查看权限")
    can_fill: bool = Field(default=False, description="是否具备填写权限")
    can_edit: bool = Field(default=False, description="是否具备编辑权限")
    can_export: bool = Field(default=False, description="是否具备导出权限")
    can_manage: bool = Field(default=False, description="是否具备管理权限")
    is_owner: bool = Field(default=False, description="是否表单拥有者")
