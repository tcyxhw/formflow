# app/schemas/user.py
"""
用户相关Schema
"""
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from app.schemas.base import BaseSchema


class UserBase(BaseSchema):
    """用户基础信息"""
    account: str = Field(..., min_length=3, max_length=50, description="登录账号")
    name: str = Field(..., min_length=2, max_length=50, description="真实姓名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$", description="手机号")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    department_id: Optional[int] = Field(None, description="部门ID")


class UserCreate(UserBase):
    """创建用户"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")

    @field_validator('password')  # Pydantic v2 使用 field_validator
    @classmethod
    def validate_password(cls, v: str) -> str:
        """密码强度验证"""
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        if not any(c.isalpha() for c in v):
            raise ValueError('密码必须包含字母')
        return v


class UserUpdate(BaseSchema):
    """更新用户"""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    department_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """数据库中的用户"""
    id: int
    tenant_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


class UserResponse(UserInDB):
    """用户响应"""
    department_name: Optional[str] = None
    roles: List[str] = []
    positions: List[str] = []


class UserProfile(BaseSchema):
    """用户扩展信息"""
    identity_no: Optional[str] = Field(None, description="学号/工号")
    identity_type: Optional[str] = Field(None, pattern="^(student|teacher|admin)$")  # 改为 pattern
    entry_year: Optional[int] = Field(None, ge=1900, le=2100)
    grade: Optional[str] = None
    major: Optional[str] = None
    supervisor_id: Optional[int] = None
    title: Optional[str] = None
    research_area: Optional[str] = None
    office: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class PasswordChange(BaseSchema):
    """修改密码"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, description="新密码")

    @field_validator('new_password')  # Pydantic v2 使用 field_validator
    @classmethod
    def validate_password(cls, v: str, info) -> str:
        """验证新密码"""
        if 'old_password' in info.data and v == info.data['old_password']:
            raise ValueError('新密码不能与原密码相同')
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        return v