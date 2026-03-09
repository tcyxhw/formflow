# app/services/auth.py
"""
认证服务 - 核心认证业务逻辑协调器

功能概述:
- 统一协调用户认证相关的所有业务流程
- 整合用户验证、令牌管理、缓存更新等操作
- 提供完整的登录、注册、令牌刷新、登出功能
- 实现安全策略和异常处理

主要类和方法:
└─ AuthService (认证服务)
    ├─ login()                      # 用户登录完整流程
    │   ├─ 验证登录频率限制
    │   ├─ 用户身份验证
    │   ├─ 密码验证
    │   ├─ 用户状态检查
    │   ├─ 生成JWT令牌对
    │   ├─ 更新缓存信息
    │   └─ 返回令牌和用户信息
    │
    ├─ refresh_token()              # 访问令牌刷新流程
    │   ├─ 验证刷新令牌
    │   ├─ 生成新访问令牌
    │   ├─ 用户状态检查
    │   ├─ 更新缓存
    │   └─ 返回新令牌
    │
    ├─ register()                   # 用户注册完整流程
    │   ├─ 验证注册频率
    │   ├─ 租户有效性验证
    │   ├─ 用户信息唯一性检查
    │   ├─ 创建用户和扩展信息
    │   ├─ 更新缓存和计数
    │   └─ 返回用户信息
    │
    └─ logout()                     # 用户登出流程
        ├─ 撤销所有令牌
        ├─ 清除用户缓存
        └─ 记录登出日志

业务流程特点:
- 事务性操作，确保数据一致性
- 异步并发处理，提升性能
- 完整的错误处理和日志记录
- 安全策略集成（频率限制、状态验证）

使用场景:
- API层调用的主要认证入口
- 前端登录、注册、退出功能支持
- 令牌自动刷新机制
- 安全事件处理

依赖关系:
- 依赖: TokenService, CacheService, UserService, ValidationService
- 被依赖: API路由层 (auth.py)
"""
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import logging
import asyncio

from app.core.security import verify_password, hash_password
from app.core.exceptions import AuthenticationError
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.user_service import UserService
from app.services.cache_service import CacheService
from app.services.token_service import TokenService
from app.services.validation_service import ValidationService

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务 - 专注于核心认证流程"""

    @staticmethod
    async def login(request: LoginRequest, db: Session) -> Dict[str, Any]:
        """用户登录"""
        # 1. 验证登录频率限制
        await ValidationService.validate_login_attempt(request.account)

        # 2. 查找用户
        user = UserService.find_user_by_account(request.account, request.tenant_id, db)

        # 3. 验证用户和密码
        if not user or not verify_password(request.password, user.password_hash):
            await CacheService.increment_login_failed(request.account)
            logger.warning(f"登录失败：账号或密码错误 - {request.account}")
            raise AuthenticationError("账号或密码错误")

        # 4. 验证用户状态
        ValidationService.validate_user_active(user)

        # 5. 获取用户信息
        positions = UserService.get_user_positions(user.id, db)
        profile = UserService.get_user_profile(user.id, db)
        identity_type = profile.identity_type if profile else "student"

        # 6. 生成令牌（现在是异步的，并且自动保存到 Redis）
        token_info = await TokenService.create_tokens(
            user_id=user.id,
            tenant_id=user.tenant_id,
            extra_data={
                "account": user.account,
                "name": user.name,
                "identity_type": identity_type
            }
        )

        # 7. 清除登录失败计数并缓存用户信息
        await asyncio.gather(
            CacheService.clear_login_failed(request.account),
            CacheService.cache_user_info(user.id, {
                "id": user.id,
                "tenant_id": user.tenant_id,
                "account": user.account,
                "name": user.name,
                "email": user.email,
                "department_id": user.department_id,
                "identity_type": identity_type
            }),
            CacheService.cache_user_positions(user.id, positions)
        )

        logger.info(f"用户登录成功 - 用户ID: {user.id}, 身份: {identity_type}")

        return {
            "access_token": token_info["access_token"],
            "refresh_token": token_info["refresh_token"],
            "token_type": token_info["token_type"],
            "expires_in": token_info["expires_in"],
            "user": {
                "id": user.id,
                "account": user.account,
                "name": user.name,
                "email": user.email,
                "tenant_id": user.tenant_id,
                "identity_type": identity_type,
                "positions": positions
            }
        }

    @staticmethod
    async def refresh_token(refresh_token: str, db: Session) -> Dict[str, Any]:
        """刷新访问令牌"""
        try:
            # 1. 使用新的刷新令牌方法（包含了验证和防重放攻击）
            new_token_info = await TokenService.refresh_access_token(refresh_token)

            if not new_token_info:
                raise AuthenticationError("刷新令牌无效或已过期")

            # 2. 从刷新令牌中提取用户信息
            refresh_payload = await TokenService.verify_refresh_token(refresh_token)
            if not refresh_payload:
                raise AuthenticationError("无法验证刷新令牌")

            user_id = refresh_payload.get("user_id")
            tenant_id = refresh_payload.get("tenant_id")

            # 3. 查询用户信息（用于验证用户状态）
            user = UserService.find_user_by_id(user_id, db)
            if not user:
                # 撤销该用户的所有令牌
                await TokenService.revoke_tokens(user_id, tenant_id)
                await CacheService.clear_user_cache(user_id)
                raise AuthenticationError("用户不存在或已禁用")

            ValidationService.validate_user_active(user)

            # 4. 获取用户详细信息
            profile = UserService.get_user_profile(user.id, db)
            identity_type = profile.identity_type if profile else "student"

            # 5. 更新缓存
            await CacheService.cache_user_info(user.id, {
                "id": user.id,
                "tenant_id": user.tenant_id,
                "account": user.account,
                "name": user.name,
                "email": user.email,
                "department_id": user.department_id,
                "identity_type": identity_type
            })

            logger.info(f"令牌刷新成功 - 用户ID: {user.id}")

            return new_token_info

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"令牌刷新失败: {str(e)}")
            raise AuthenticationError("令牌刷新失败，请重新登录")

    @staticmethod
    async def register(request: RegisterRequest, db: Session) -> Dict[str, Any]:
        """用户注册"""
        # 1. 验证注册频率
        ip = getattr(request, 'client_ip', 'unknown')
        await ValidationService.validate_register_frequency(ip)

        # 2. 验证租户存在
        ValidationService.validate_tenant_exists(request.tenant_id, db)

        # 3. 验证用户信息唯一性
        ValidationService.validate_user_uniqueness(
            request.account, request.email, request.phone, request.tenant_id, db
        )

        # 4. 创建用户
        user = UserService.create_user({
            "tenant_id": request.tenant_id,
            "account": request.account,
            "password_hash": hash_password(request.password),
            "name": request.name,
            "email": request.email,
            "phone": request.phone,
            "is_active": True
        }, db)

        # 5. 创建用户扩展信息
        UserService.create_user_profile({
            "tenant_id": request.tenant_id,
            "user_id": user.id,
            "identity_type": "student",
            "entry_year": datetime.now().year
        }, db)

        db.commit()
        db.refresh(user)

        # 6. 更新缓存和计数
        await asyncio.gather(
            CacheService.increment_register_count(ip),
            CacheService.cache_user_info(user.id, {
                "id": user.id,
                "tenant_id": user.tenant_id,
                "account": user.account,
                "name": user.name,
                "email": user.email,
                "department_id": None,
                "identity_type": "student"
            })
        )

        logger.info(f"用户注册成功 - 用户ID: {user.id}")

        return {
            "id": user.id,
            "account": user.account,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "tenant_id": user.tenant_id,
            "identity_type": "student"
        }

    @staticmethod
    async def logout(user_id: int, tenant_id: int, token: str, db: Session) -> bool:
        """用户登出"""
        try:
            # 1. 撤销用户的所有令牌
            await TokenService.revoke_tokens(user_id, tenant_id)

            # 2. 清除缓存
            await CacheService.clear_user_cache(user_id)

            logger.info(f"用户登出成功 - 用户ID: {user_id}")
            return True

        except Exception as e:
            logger.error(f"用户登出失败 - 用户ID: {user_id}, 错误: {str(e)}")
            # 即使失败也尝试清除缓存
            try:
                await CacheService.clear_user_cache(user_id)
            except:
                pass
            return False