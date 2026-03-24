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
    include_children: Optional[bool] = Field(None, description="部门类型时是否包含子部门")
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
    
    @validator("include_children")
    def validate_include_children(cls, v: Optional[bool], values: dict) -> Optional[bool]:
        """验证 include_children 仅对 department 类型有效。

        Time: O(1), Space: O(1)
        """
        grant_type = values.get("grant_type")
        if v is not None and grant_type != GrantType.DEPARTMENT:
            raise ValueError("include_children 仅对 department 类型有效")
        return v


class FormPermissionCreateRequest(FormPermissionBase):
    """创建权限请求体"""

    pass


class FormPermissionUpdateRequest(BaseModel):
    """更新权限请求体"""

    include_children: Optional[bool] = Field(None, description="部门类型时是否包含子部门")
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


class FormPermissionResponse(BaseModel):
    """权限响应模型（不带验证器，兼容历史数据）"""

    id: int
    form_id: int
    tenant_id: int
    grant_type: GrantType
    grantee_id: int
    permission: PermissionType
    include_children: Optional[bool] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
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



class GrantPermissionDTO(BaseModel):
    """授予权限DTO - 单条权限授予"""
    
    grant_type: GrantType = Field(..., description="授权类型：user/role/department/position")
    grantee_id: int = Field(..., ge=1, description="授权对象ID")
    permission: PermissionType = Field(..., description="权限类型：view/fill/edit/export/manage")
    include_children: Optional[bool] = Field(None, description="部门类型时是否包含子部门，默认True")
    valid_from: Optional[datetime] = Field(None, description="生效开始时间")
    valid_to: Optional[datetime] = Field(None, description="生效结束时间")
    
    @validator("include_children", always=True)
    def set_default_include_children(cls, v: Optional[bool], values: dict) -> Optional[bool]:
        """为 department 类型设置默认值 True"""
        grant_type = values.get("grant_type")
        if grant_type == GrantType.DEPARTMENT and v is None:
            return True
        return v


class BatchGrantPermissionItem(BaseModel):
    """批量授权单项"""
    
    grant_type: GrantType = Field(..., description="授权类型")
    grantee_id: int = Field(..., ge=1, description="授权对象ID")
    permissions: List[PermissionType] = Field(..., min_items=1, description="权限类型列表")
    include_children: Optional[bool] = Field(None, description="部门类型时是否包含子部门")
    valid_from: Optional[datetime] = Field(None, description="生效开始时间（可被全局覆盖）")
    valid_to: Optional[datetime] = Field(None, description="生效结束时间（可被全局覆盖）")


class BatchGrantPermissionDTO(BaseModel):
    """批量授权请求"""
    
    items: List[BatchGrantPermissionItem] = Field(..., min_items=1, description="授权项列表")
    valid_from: Optional[datetime] = Field(None, description="全局生效开始时间")
    valid_to: Optional[datetime] = Field(None, description="全局生效结束时间")


class PermissionCheckDTO(BaseModel):
    """权限检查请求"""
    
    required_level: PermissionType = Field(..., description="需要的权限级别")


class PermissionCheckResponse(BaseModel):
    """权限检查响应"""
    
    has_permission: bool = Field(..., description="是否拥有权限")
    user_level: Optional[PermissionType] = Field(None, description="用户拥有的最高权限级别")
    is_owner: bool = Field(default=False, description="是否为表单创建者")


class PermissionTargetResponse(BaseModel):
    """权限授权对象响应（带名称）"""
    
    id: int
    form_id: int
    grant_type: GrantType
    grantee_id: int
    grantee_name: str = Field(..., description="授权对象名称")
    permission: PermissionType
    include_children: Optional[bool]
    valid_from: Optional[datetime]
    valid_to: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class FormPermissionListWithOwnerResponse(BaseModel):
    """权限列表响应（包含创建者信息）"""
    
    owner: dict = Field(..., description="表单创建者信息")
    permissions: List[PermissionTargetResponse] = Field(default_factory=list, description="权限列表")
