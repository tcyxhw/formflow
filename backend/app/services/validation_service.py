# app/services/validation_service.py
"""
验证服务 - 统一处理各种验证逻辑
"""
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.user import Tenant
from app.core.exceptions import ValidationError
from app.services.user_service import UserService
from app.services.cache_service import CacheService


class ValidationService:
    """验证服务"""

    @staticmethod
    async def validate_login_attempt(account: str) -> bool:
        """验证登录尝试是否被限制"""
        failed_count = await CacheService.get_login_failed_count(account)
        if failed_count > 5:
            raise ValidationError("登录失败次数过多，请5分钟后再试")
        return True

    @staticmethod
    async def validate_register_frequency(ip: str):
        """验证注册频率"""
        if await CacheService.check_register_limit(ip):
            raise ValidationError("注册请求过于频繁，请稍后再试")

    @staticmethod
    def validate_tenant_exists(tenant_id: int, db: Session):
        """验证租户是否存在"""
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ValidationError("租户不存在")
        return tenant

    @staticmethod
    def validate_user_uniqueness(account: str, email: str, phone: str,
                                 tenant_id: int, db: Session):
        """验证用户信息唯一性"""
        if UserService.check_account_exists(account, tenant_id, db):
            raise ValidationError("账号已存在")

        if email and UserService.check_email_exists(email, tenant_id, db):
            raise ValidationError("邮箱已被使用")

        if phone and UserService.check_phone_exists(phone, tenant_id, db):
            raise ValidationError("手机号已被使用")

    @staticmethod
    def validate_user_active(user) -> bool:
        """验证用户是否激活"""
        if not user.is_active:
            raise ValidationError("账号已被禁用")
        return True