# app/schemas/auth.py
"""
认证相关Schema
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from app.schemas.base import BaseSchema


class LoginRequest(BaseSchema):
    """登录请求"""
    account: str = Field(..., description="账号/邮箱/手机号")
    password: str = Field(..., description="密码")
    tenant_id: Optional[int] = Field(None, description="租户ID")


class TokenResponse(BaseSchema):
    """Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(..., description="访问令牌过期时间(秒)")


class RefreshTokenRequest(BaseSchema):
    """刷新Token请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class RegisterRequest(BaseSchema):
    """注册请求"""
    account: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")  # 改为 pattern
    tenant_id: int = Field(..., description="租户ID")