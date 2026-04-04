# app/services/token_service.py
"""
Token 服务 - 支持智能令牌轮转机制

功能概述:
- 负责JWT访问令牌和刷新令牌的生成、验证和管理
- 实现双Token认证机制（访问令牌 + 刷新令牌）
- 支持刷新令牌智能轮转，提供无缝用户体验
- 提供Token家族管理和安全防护

主要类和方法:
└─ TokenService (Token管理服务)
    ├─ create_tokens()              # 创建JWT令牌对（访问+刷新）
    ├─ verify_access_token()        # 验证访问令牌有效性
    ├─ verify_refresh_token()       # 验证刷新令牌有效性（支持队列）
    ├─ refresh_access_token()       # 智能刷新：访问令牌+条件性刷新令牌轮转
    ├─ revoke_tokens()              # 撤销用户所有令牌（登出）
    ├─ _create_new_access_token()   # 创建新的访问令牌（内部方法）
    └─ _create_new_refresh_token()  # 创建新的刷新令牌（内部方法）

Token结构:
- Access Token (30分钟): 包含用户信息，用于API访问
- Refresh Token (7天): 支持队列存储，智能轮转
- Family ID: 追踪令牌家族，检测异常使用

轮转机制:
- 刷新令牌使用时间超过总时间2/3时自动轮转
- 队列保存最近3个有效刷新令牌
- 前端无感知更新，提供持续的用户体验

安全特性:
- JWT签名验证防止篡改
- 令牌队列机制支持并发访问
- 定期轮转增强安全性
- Redis存储支持快速撤销
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import jwt
from app.core.exceptions import AuthenticationError
from app.services.token_cache_service import TokenCacheService
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class TokenService:
    """Token 管理服务 - 支持智能轮转"""

    # 从配置文件读取过期时间（秒）
    ACCESS_TOKEN_EXPIRE = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    REFRESH_TOKEN_EXPIRE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    @classmethod
    async def create_tokens(
            cls,
            user_id: int,
            tenant_id: int,
            extra_data: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """创建访问令牌和刷新令牌"""
        # 生成唯一的 token ID 和 family ID
        access_token_id = str(uuid.uuid4())
        refresh_token_id = str(uuid.uuid4())
        family_id = str(uuid.uuid4())

        # 创建 JWT payload
        now = datetime.utcnow()

        access_payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "token_id": access_token_id,
            "family_id": family_id,
            "type": "access",
            "exp": now + timedelta(seconds=cls.ACCESS_TOKEN_EXPIRE),
            "iat": now,
            **(extra_data or {})
        }

        refresh_payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "token_id": refresh_token_id,
            "family_id": family_id,
            "type": "refresh",
            "exp": now + timedelta(seconds=cls.REFRESH_TOKEN_EXPIRE),
            "iat": now
        }

        # 生成 JWT
        access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")
        refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm="HS256")

        # 存储访问令牌
        await TokenCacheService.store_access_token(
            tenant_id, user_id, access_token_id,
            {
                "token": access_token,
                "user_id": user_id,
                "family_id": family_id,
                "created_at": now.isoformat()
            },
            cls.ACCESS_TOKEN_EXPIRE
        )

        # 存储刷新令牌到队列
        await TokenCacheService.store_refresh_token_queue(
            tenant_id, user_id,
            {
                "token": refresh_token,
                "token_id": refresh_token_id,
                "user_id": user_id,
                "family_id": family_id,
                "created_at": now.isoformat()
            },
            cls.REFRESH_TOKEN_EXPIRE
        )

        # 存储用户当前令牌信息
        await TokenCacheService.store_user_current_tokens(
            tenant_id, user_id, access_token_id, refresh_token_id,
            family_id, cls.REFRESH_TOKEN_EXPIRE
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": cls.ACCESS_TOKEN_EXPIRE
        }

    @classmethod
    async def verify_access_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """验证访问令牌（纯 JWT，不依赖 Redis）。

        Redis 重启后不影响已有 token 验证，
        代价是无法即时撤销 access token（需等自然过期，默认 30 分钟）。
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

            if payload.get("type") != "access":
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.debug("访问令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效的访问令牌: {str(e)}")
            return None

    @classmethod
    async def verify_refresh_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """验证刷新令牌（支持队列查找）"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

            if payload.get("type") != "refresh":
                return None

            user_id = payload.get("user_id")
            tenant_id = payload.get("tenant_id")

            # 在令牌队列中查找
            token_data = await TokenCacheService.get_valid_refresh_token(
                tenant_id, user_id, token
            )

            if not token_data:
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.debug("刷新令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效的刷新令牌: {str(e)}")
            return None

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> Optional[Dict[str, str]]:
        """智能刷新：访问令牌 + 条件性刷新令牌轮转"""
        refresh_payload = await cls.verify_refresh_token(refresh_token)

        if not refresh_payload:
            return None

        user_id = refresh_payload.get("user_id")
        tenant_id = refresh_payload.get("tenant_id")
        family_id = refresh_payload.get("family_id")

        # 检查当前刷新令牌
        current_token_data = await TokenCacheService.get_valid_refresh_token(
            tenant_id, user_id, refresh_token
        )

        if not current_token_data:
            return None

        # 生成新的访问令牌
        new_access_token = await cls._create_new_access_token(
            user_id, tenant_id, family_id
        )

        # 检查是否需要轮转刷新令牌
        should_rotate = await TokenCacheService.should_rotate_refresh_token(
            tenant_id, user_id, current_token_data, cls.REFRESH_TOKEN_EXPIRE
        )

        result = {
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": cls.ACCESS_TOKEN_EXPIRE
        }

        if should_rotate:
            # 生成新的刷新令牌
            new_refresh_token = await cls._create_new_refresh_token(
                user_id, tenant_id, family_id
            )

            # 添加到令牌队列
            await TokenCacheService.store_refresh_token_queue(
                tenant_id, user_id,
                {
                    "token": new_refresh_token,
                    "token_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "family_id": family_id,
                    "created_at": datetime.utcnow().isoformat()
                },
                cls.REFRESH_TOKEN_EXPIRE
            )

            result["refresh_token"] = new_refresh_token
            result["token_rotated"] = True

            logger.info(f"刷新令牌已轮转 - 用户: {user_id}")
        else:
            # 不需要轮转，返回原刷新令牌
            result["refresh_token"] = refresh_token
            result["token_rotated"] = False

        return result

    @classmethod
    async def revoke_tokens(cls, user_id: int, tenant_id: int):
        """撤销用户的所有令牌"""
        return await TokenCacheService.revoke_user_tokens(tenant_id, user_id)

    @classmethod
    async def _create_new_access_token(
            cls,
            user_id: int,
            tenant_id: int,
            family_id: str
    ) -> str:
        """创建新的访问令牌"""
        token_id = str(uuid.uuid4())
        now = datetime.utcnow()

        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "token_id": token_id,
            "family_id": family_id,
            "type": "access",
            "exp": now + timedelta(seconds=cls.ACCESS_TOKEN_EXPIRE),
            "iat": now
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        # 存储访问令牌
        await TokenCacheService.store_access_token(
            tenant_id, user_id, token_id,
            {
                "token": token,
                "user_id": user_id,
                "family_id": family_id,
                "created_at": now.isoformat()
            },
            cls.ACCESS_TOKEN_EXPIRE
        )

        # 更新用户当前访问令牌ID
        await TokenCacheService.update_current_access_token(tenant_id, user_id, token_id)

        return token

    @classmethod
    async def _create_new_refresh_token(
            cls,
            user_id: int,
            tenant_id: int,
            family_id: str
    ) -> str:
        """创建新的刷新令牌"""
        token_id = str(uuid.uuid4())
        now = datetime.utcnow()

        payload = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "token_id": token_id,
            "family_id": family_id,
            "type": "refresh",
            "exp": now + timedelta(seconds=cls.REFRESH_TOKEN_EXPIRE),
            "iat": now
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        # 更新用户当前刷新令牌ID
        await TokenCacheService.update_current_refresh_token(tenant_id, user_id, token_id)

        return token