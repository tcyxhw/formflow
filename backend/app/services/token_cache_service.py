# app/services/token_cache_service.py
"""
Token 缓存服务 - 支持令牌轮转机制

功能概述:
- 专门负责访问令牌和刷新令牌的Redis存储操作
- 支持刷新令牌队列管理（滑动窗口机制）
- 提供Token轮转判断和管理功能
- 维护用户令牌状态和安全检查

主要类和方法:
└─ TokenCacheService (Token缓存操作)
    ├─ store_access_token()              # 存储访问令牌到Redis
    ├─ store_refresh_token_queue()       # 存储刷新令牌到队列（新增）
    ├─ get_access_token()                # 获取访问令牌数据
    ├─ get_valid_refresh_token()         # 从队列中验证刷新令牌（新增）
    ├─ should_rotate_refresh_token()     # 判断是否需要轮转（新增）
    ├─ store_user_current_tokens()       # 存储用户当前令牌ID映射
    ├─ update_current_access_token()     # 更新用户当前访问令牌ID
    └─ revoke_user_tokens()              # 撤销用户所有令牌

Redis键名规范:
- 访问令牌: {tenant_id}:access_token:{user_id}:{token_id}
- 刷新令牌队列: {tenant_id}:refresh_tokens:{user_id}
- 用户Token: {tenant_id}:user_tokens:{user_id}
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.redis_client import redis_client
import logging

logger = logging.getLogger(__name__)


class TokenCacheService:
    """Token 缓存服务 - 支持令牌轮转"""

    @staticmethod
    async def store_access_token(
            tenant_id: int,
            user_id: int,
            token_id: str,
            token_data: Dict[str, Any],
            expire: int
    ):
        """存储访问令牌"""
        key = redis_client.get_key(tenant_id, "access_token", f"{user_id}:{token_id}")
        await redis_client.set(key, token_data, expire)

    @staticmethod
    async def store_refresh_token_queue(
            tenant_id: int,
            user_id: int,
            token_data: Dict[str, Any],
            expire: int
    ):
        """存储刷新令牌到队列（最多保留3个有效令牌）"""
        key = redis_client.get_key(tenant_id, "refresh_tokens", str(user_id))

        # 添加新令牌到队列头部
        await redis_client.lpush(key, token_data)

        # 只保留最新的3个令牌（提供容错空间）
        await redis_client.redis_client.ltrim(key, 0, 2)

        # 设置过期时间
        await redis_client.expire(key, expire)

    @staticmethod
    async def get_access_token(tenant_id: int, user_id: int, token_id: str) -> Optional[Dict[str, Any]]:
        """获取访问令牌数据"""
        key = redis_client.get_key(tenant_id, "access_token", f"{user_id}:{token_id}")
        return await redis_client.get(key)

    @staticmethod
    async def get_valid_refresh_token(
            tenant_id: int,
            user_id: int,
            token: str
    ) -> Optional[Dict[str, Any]]:
        """检查令牌是否在有效队列中"""
        key = redis_client.get_key(tenant_id, "refresh_tokens", str(user_id))

        # 获取所有令牌
        tokens = await redis_client.lrange(key, 0, -1)

        for token_data in tokens:
            if token_data.get("token") == token:
                return token_data

        return None

    @staticmethod
    async def should_rotate_refresh_token(
            tenant_id: int,
            user_id: int,
            current_token_data: dict,
            total_expire_seconds: int
    ) -> bool:
        """判断是否需要轮转刷新令牌（剩余时间少于总时间的1/3时轮转）"""
        try:
            created_at = datetime.fromisoformat(current_token_data["created_at"])
            now = datetime.utcnow()

            # 计算令牌已使用时间
            used_time = (now - created_at).total_seconds()

            # 如果已使用时间超过总时间的2/3，则需要轮转
            return used_time > (total_expire_seconds * 2 / 3)
        except (KeyError, ValueError, TypeError):
            # 如果数据格式有问题，建议轮转
            logger.warning(f"令牌数据格式异常，建议轮转 - 用户: {user_id}")
            return True

    @staticmethod
    async def store_user_current_tokens(
            tenant_id: int,
            user_id: int,
            access_token_id: str,
            refresh_token_id: str,
            family_id: str,
            expire: int
    ):
        """存储用户当前的令牌ID"""
        key = redis_client.get_key(tenant_id, "user_tokens", str(user_id))
        await redis_client.hset(key, "current_access", access_token_id)
        await redis_client.hset(key, "current_refresh", refresh_token_id)
        await redis_client.hset(key, "family_id", family_id)
        await redis_client.expire(key, expire)

    @staticmethod
    async def get_user_current_tokens(tenant_id: int, user_id: int) -> Optional[Dict[str, str]]:
        """获取用户当前的令牌ID"""
        key = redis_client.get_key(tenant_id, "user_tokens", str(user_id))
        return await redis_client.hgetall(key)

    @staticmethod
    async def update_current_access_token(tenant_id: int, user_id: int, access_token_id: str):
        """更新用户当前的访问令牌ID"""
        key = redis_client.get_key(tenant_id, "user_tokens", str(user_id))
        await redis_client.hset(key, "current_access", access_token_id)

    @staticmethod
    async def update_current_refresh_token(tenant_id: int, user_id: int, refresh_token_id: str):
        """更新用户当前的刷新令牌ID"""
        key = redis_client.get_key(tenant_id, "user_tokens", str(user_id))
        await redis_client.hset(key, "current_refresh", refresh_token_id)

    @staticmethod
    async def revoke_user_tokens(tenant_id: int, user_id: int):
        """撤销用户的所有令牌"""
        # 获取用户当前的 token 信息
        user_tokens_key = redis_client.get_key(tenant_id, "user_tokens", str(user_id))
        user_tokens = await redis_client.hgetall(user_tokens_key)

        deleted_count = 0

        if user_tokens:
            # 删除访问令牌
            if access_id := user_tokens.get("current_access"):
                access_key = redis_client.get_key(tenant_id, "access_token", f"{user_id}:{access_id}")
                deleted_count += await redis_client.delete(access_key)

        # 删除刷新令牌队列
        refresh_queue_key = redis_client.get_key(tenant_id, "refresh_tokens", str(user_id))
        deleted_count += await redis_client.delete(refresh_queue_key)

        # 删除用户 token 信息
        deleted_count += await redis_client.delete(user_tokens_key)

        logger.info(f"用户 {user_id} 的所有令牌已撤销，删除 {deleted_count} 个缓存项")
        return deleted_count > 0

    @staticmethod
    async def cleanup_expired_tokens(tenant_id: int, user_id: int):
        """清理过期的令牌（可选的维护方法）"""
        key = redis_client.get_key(tenant_id, "refresh_tokens", str(user_id))

        # 获取所有令牌
        tokens = await redis_client.lrange(key, 0, -1)
        valid_tokens = []

        now = datetime.utcnow()

        for token_data in tokens:
            try:
                created_at = datetime.fromisoformat(token_data["created_at"])
                # 假设令牌有效期为7天
                if (now - created_at).total_seconds() < 7 * 24 * 60 * 60:
                    valid_tokens.append(token_data)
            except (KeyError, ValueError):
                continue

        # 重新存储有效令牌
        if valid_tokens:
            await redis_client.delete(key)
            for token_data in reversed(valid_tokens):  # 保持顺序
                await redis_client.lpush(key, token_data)
        else:
            await redis_client.delete(key)