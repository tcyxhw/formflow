"""
用户管理相关Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.base import BaseSchema


class UserListItem(BaseSchema):
    """用户列表项"""
    id: int
    account: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    department_name: Optional[str] = None
    department_id: Optional[int] = None
    roles: List[str] = Field(default_factory=list)
    positions: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class UserListQuery(BaseSchema):
    """用户列表查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页大小")
    department_id: Optional[int] = Field(default=None, description="部门ID筛选")
    position_id: Optional[int] = Field(default=None, description="岗位ID筛选")
    role: Optional[str] = Field(default=None, description="角色筛选")
    keyword: Optional[str] = Field(default=None, description="关键词搜索（账号/姓名）")
    is_active: Optional[bool] = Field(default=None, description="是否启用")


class UserUpdateRequest(BaseSchema):
    """用户更新请求"""
    name: Optional[str] = Field(None, min_length=2, max_length=50, description="姓名")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$", description="手机号")
    department_id: Optional[int] = Field(None, description="主属部门ID")
    position_ids: Optional[List[int]] = Field(None, description="岗位ID列表")
    role: Optional[str] = Field(None, description="角色标识")
    is_active: Optional[bool] = Field(None, description="是否启用")


class ManageablePosition(BaseSchema):
    """可管理岗位"""
    id: int
    name: str
    level: Optional[int] = Field(None, description="岗位层级（越小越高）")


class ManageableDepartment(BaseSchema):
    """可管理部门"""
    id: int
    name: str
    type: Optional[str] = None
    parent_id: Optional[int] = None
    posts: List[ManageablePosition] = Field(default_factory=list, description="部门下所有岗位")


class CurrentUserPosition(BaseSchema):
    """当前用户岗位信息"""
    id: int
    name: str
    department_id: int
    department_name: str


class ManageableScope(BaseSchema):
    """可管理范围"""
    departments: List[ManageableDepartment] = Field(default_factory=list)
    positions: List[ManageablePosition] = Field(default_factory=list)
    is_admin: bool = Field(default=False, description="是否为管理员")
    current_user_department: Optional[ManageableDepartment] = Field(None, description="当前用户所在部门")
    current_user_positions: List[CurrentUserPosition] = Field(default_factory=list, description="当前用户岗位列表")


class ImportPreviewRow(BaseSchema):
    """导入预览行"""
    row_index: int
    account: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department_name: str
    position_name: Optional[str] = None
    role: Optional[str] = None
    is_valid: bool = True
    error_message: Optional[str] = None


class ImportPreviewResponse(BaseSchema):
    """导入预览响应"""
    preview_key: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows: List[ImportPreviewRow]


class ImportConfirmRequest(BaseSchema):
    """导入确认请求"""
    preview_key: str = Field(..., description="预览key")
    selected_rows: Optional[List[int]] = Field(None, description="选中的行索引列表，为空则导入全部有效行")
