# app/api/deps.py
"""
FastAPI 依赖注入模块
"""
from typing import Optional, List, Generator, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging
from datetime import datetime
from app.core.database import get_db
from app.core.security import decode_token
from app.core.redis_client import redis_client, RateLimiter
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    RateLimitError
)
from app.models.user import User, Role, UserRole
from app.models.notification import RefreshToken
import hashlib

logger = logging.getLogger(__name__)

# Bearer 认证方案
security = HTTPBearer(auto_error=False)


# ✅ 修复：新增从 request.state 获取用户的函数
async def get_current_user(
        request: Request,
        db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户的完整信息

    ⚠️ 重要修改：
    - 不再从 Authorization 头重新验证令牌
    - 直接从 AuthMiddleware 设置的 request.state 中获取用户信息
    - 避免在令牌刷新后重复验证旧令牌导致失败

    :param request: FastAPI Request 对象，包含 state.user_id
    :param db: 数据库会话，用于查询用户信息
    :return: 当前登录的用户对象
    :raises AuthenticationError: 用户不存在或已被禁用时
    """
    # ✅ 从中间件设置的 state 中获取用户信息
    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", None)

    logger.debug(f"get_current_user: user_id={user_id}, tenant_id={tenant_id}")

    if not user_id:
        raise AuthenticationError("未认证：缺少用户标识")

    # ✅ 从数据库查询用户（不需要再验证令牌）
    user = db.query(User).filter(
        User.id == user_id,
        User.is_active == True
    ).first()

    if not user:
        logger.warning(f"用户不存在: user_id={user_id}")
        raise AuthenticationError("用户不存在或已禁用")

    # ✅ 将租户 ID 附加到用户对象（保持兼容性）
    user.current_tenant_id = tenant_id

    logger.debug(f"成功获取用户: {user.account}")
    return user


# ✅ 保留原有的 get_current_token（用于特殊场景）
async def get_current_token(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    从请求头中提取并返回 JWT Token

    ⚠️ 注意：这个函数现在主要用于特殊场景（如刷新令牌接口）
    大部分情况下应该使用 get_current_user（从 request.state 获取）
    """
    if not credentials:
        raise AuthenticationError("未提供认证凭据")

    return credentials.credentials


# ✅ 保留原有的 get_current_tenant_id（使用新的 get_current_user）
async def get_current_tenant_id(
        user: User = Depends(get_current_user)
) -> int:
    """
    获取当前操作的租户 ID
    """
    if user.current_tenant_id is None:
        raise AuthenticationError("租户ID缺失")
    return user.current_tenant_id


# ✅ 修复：optional_current_user 也改为从 state 获取
async def optional_current_user(
        request: Request,
        db: Session = Depends(get_db)
) -> Optional[User]:
    """
    可选的用户认证

    ⚠️ 修改：从 request.state 获取，而不是重新验证令牌
    """
    # ✅ 从 state 获取用户信息
    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", None)

    if not user_id:
        return None

    try:
        user = db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()

        if user:
            user.current_tenant_id = tenant_id

        return user
    except Exception:
        return None


# ✅ PermissionChecker 保持不变（它依赖 get_current_user，会自动使用新逻辑）
class PermissionChecker:
    """权限检查器类"""

    def __init__(
            self,
            required_permissions: Optional[List[str]] = None,
            required_roles: Optional[List[str]] = None,
            allow_self: bool = False
    ):
        self.required_permissions = required_permissions or []
        self.required_roles = required_roles or []
        self.allow_self = allow_self

    async def __call__(
            self,
            request: Request,
            user: User = Depends(get_current_user),  # ✅ 自动使用新的 get_current_user
            db: Session = Depends(get_db)
    ) -> User:
        """执行权限检查"""
        # 检查角色要求
        if self.required_roles:
            # 使用用户表中的 tenant_id 字段
            tenant_id = user.tenant_id
            
            user_roles = db.query(Role).join(UserRole).filter(
                UserRole.user_id == user.id,
                UserRole.tenant_id == tenant_id
            ).all()

            role_names = [role.name for role in user_roles]

            if not any(role in role_names for role in self.required_roles):
                logger.warning(
                    f"用户 {user.id} 缺少需要的角色: {self.required_roles}"
                )
                raise AuthorizationError(
                    f"需要以下角色之一: {', '.join(self.required_roles)}"
                )

        # 检查权限要求
        if self.required_permissions:
            pass  # TODO: 实现权限检查

        # 允许用户操作自己的资源
        if self.allow_self:
            path_params = request.path_params
            resource_user_id = path_params.get("user_id")

            if resource_user_id and int(resource_user_id) == user.id:
                return user

        return user


# 预定义的权限检查器（保持不变）
RequireSuperAdmin = PermissionChecker(required_roles=["系统管理员"])
RequireAdmin = PermissionChecker(required_roles=["系统管理员", "租户管理员"])
RequireFormCreator = PermissionChecker(required_roles=["表单创建者"])
RequireApprover = PermissionChecker(required_roles=["审批人"])


# 流程配置权限检查器
class FlowConfigurationPermissionChecker:
    """流程配置权限检查器
    
    允许以下用户访问流程配置：
    1. 系统管理员或租户管理员
    2. 表单创建者（仅限于自己创建的表单的流程）
    """

    async def __call__(
            self,
            request: Request,
            user: User = Depends(get_current_user),
            tenant_id: int = Depends(get_current_tenant_id),
            db: Session = Depends(get_db)
    ) -> User:
        """执行流程配置权限检查"""
        from app.models.workflow import FlowDefinition
        from app.models.form import Form
        
        # 获取流程定义ID（从路径参数）
        flow_definition_id = request.path_params.get("flow_definition_id")
        if not flow_definition_id:
            raise AuthorizationError("缺少流程定义ID")
        
        try:
            flow_definition_id = int(flow_definition_id)
        except (ValueError, TypeError):
            raise AuthorizationError("流程定义ID格式错误")
        
        # 检查用户是否是管理员
        user_roles = db.query(Role).join(UserRole).filter(
            UserRole.user_id == user.id,
            UserRole.tenant_id == tenant_id
        ).all()
        
        role_names = [role.name for role in user_roles]
        is_admin = any(role in role_names for role in ["系统管理员", "租户管理员"])
        
        if is_admin:
            return user
        
        # 如果不是管理员，检查是否是表单创建者
        flow_definition = db.query(FlowDefinition).filter(
            FlowDefinition.id == flow_definition_id,
            FlowDefinition.tenant_id == tenant_id
        ).first()
        
        if not flow_definition:
            raise AuthorizationError("流程定义不存在或无权访问")
        
        form = db.query(Form).filter(Form.id == flow_definition.form_id).first()
        
        if not form:
            raise AuthorizationError("表单不存在")
        
        if form.owner_user_id != user.id:
            logger.warning(
                f"用户 {user.id} 尝试访问非自己创建的表单 {form.id} 的流程配置"
            )
            raise AuthorizationError("只有表单创建者可以配置审批流程")
        
        return user


RequireFlowConfiguration = FlowConfigurationPermissionChecker()


# ✅ RateLimitChecker 保持不变
class RateLimitChecker:
    """限流检查器"""

    def __init__(
            self,
            max_requests: int = 100,
            window_seconds: int = 60,
            identifier_type: str = "user"
    ):
        self.limiter = RateLimiter(max_requests, window_seconds)
        self.identifier_type = identifier_type

    async def __call__(
            self,
            request: Request,
            user: Optional[User] = Depends(optional_current_user)
    ) -> None:
        """执行限流检查"""
        if self.identifier_type == "user" and user:
            identifier = f"user:{user.id}"
        elif self.identifier_type == "ip":
            identifier = f"ip:{request.client.host}"
        elif self.identifier_type == "combined":
            if user:
                identifier = f"combined:{user.id}:{request.client.host}"
            else:
                identifier = f"ip:{request.client.host}"
        else:
            identifier = f"ip:{request.client.host}"

        is_allowed = await self.limiter.is_allowed(identifier)

        if not is_allowed:
            remaining = await self.limiter.get_remaining(identifier)
            raise RateLimitError(
                f"请求过于频繁，请稍后再试",
                data={"remaining": remaining}
            )


# ✅ verify_refresh_token 保持不变（它需要验证刷新令牌，所以应该使用 decode_token）
async def verify_refresh_token(
        token: str,
        db: Session = Depends(get_db)
) -> RefreshToken:
    """验证刷新令牌的有效性"""
    payload = decode_token(token)

    if payload.get("type") != "refresh":
        raise AuthenticationError("令牌类型错误")

    jti = payload.get("jti")
    if not jti:
        raise AuthenticationError("令牌格式无效")

    jti_hash = hashlib.sha256(jti.encode()).hexdigest()

    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.jti_hash == jti_hash,
        RefreshToken.active == True
    ).first()

    if not refresh_token:
        raise AuthenticationError("刷新令牌无效或已失效")

    if refresh_token.expires_at < datetime.utcnow():
        refresh_token.active = False
        db.commit()
        raise AuthenticationError("刷新令牌已过期")

    return refresh_token


# ✅ TenantIsolation 保持不变
class TenantIsolation:
    """租户隔离依赖注入类"""

    def __init__(self, model_class: Any):
        self.model_class = model_class

    def __call__(
            self,
            db: Session = Depends(get_db),
            tenant_id: int = Depends(get_current_tenant_id)
    ) -> Any:
        """返回已添加租户过滤条件的查询对象"""
        return db.query(self.model_class).filter(
            self.model_class.tenant_id == tenant_id
        )