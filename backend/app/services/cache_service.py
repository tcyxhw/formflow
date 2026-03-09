# app/services/cache_service.py
"""
缓存服务 - 统一处理用户相关的通用缓存操作

功能概述:
- 提供用户信息、权限、登录状态等业务数据的缓存管理
- 实现登录失败计数和频率限制
- 支持用户注册频率控制
- 提供缓存批量操作和模式清理

主要类和方法:
└─ CacheService (缓存服务)
    ├─ cache_user_info()            # 缓存用户基本信息
    ├─ cache_user_positions()       # 缓存用户岗位信息
    ├─ get_user_info()              # 获取缓存的用户信息
    ├─ get_user_positions()         # 获取缓存的用户岗位
    ├─ clear_user_cache()           # 清除用户所有相关缓存
    ├─ increment_login_failed()     # 增加登录失败次数
    ├─ get_login_failed_count()     # 获取登录失败次数
    ├─ clear_login_failed()         # 清除登录失败计数
    ├─ check_register_limit()       # 检查注册频率限制
    └─ increment_register_count()   # 增加注册计数

缓存键名规范:
- 用户信息: user:info:{user_id}
- 用户岗位: user:positions:{user_id}
- 登录失败: login_failed:{account}
- 注册限制: register:ip:{ip_address}

使用场景:
- 减少数据库查询，提升用户信息获取性能
- 防止暴力破解和恶意注册
- 用户权限和状态的快速验证
- 登出时的缓存清理

依赖关系:
- 依赖: RedisClient (基础Redis操作)
- 被依赖: AuthService, ValidationService
"""
from typing import Dict, Any, List, Optional
from app.core.redis_client import redis_client, clear_cache_pattern


class CacheService:
    """缓存服务"""

    # 缓存键前缀
    USER_INFO_PREFIX = "user:info"
    USER_POSITIONS_PREFIX = "user:positions"
    LOGIN_FAILED_PREFIX = "login_failed"
    REGISTER_LIMIT_PREFIX = "register:ip"

    @staticmethod
    async def cache_user_info(user_id: int, user_data: Dict[str, Any], expire: int = 3600):
        """缓存用户基本信息"""
        await redis_client.set(
            f"{CacheService.USER_INFO_PREFIX}:{user_id}",
            user_data,
            expire=expire
        )

    @staticmethod
    async def cache_user_positions(user_id: int, positions: List[str], expire: int = 3600):
        """缓存用户岗位"""
        await redis_client.set(
            f"{CacheService.USER_POSITIONS_PREFIX}:{user_id}",
            positions,
            expire=expire
        )

    @staticmethod
    async def get_user_info(user_id: int) -> Optional[Dict[str, Any]]:
        """获取缓存的用户信息"""
        return await redis_client.get(f"{CacheService.USER_INFO_PREFIX}:{user_id}")

    @staticmethod
    async def get_user_positions(user_id: int) -> Optional[List[str]]:
        """获取缓存的用户岗位"""
        return await redis_client.get(f"{CacheService.USER_POSITIONS_PREFIX}:{user_id}")

    @staticmethod
    async def clear_user_cache(user_id: int):
        """清除用户所有缓存"""
        await clear_cache_pattern(f"user:*:{user_id}")

    @staticmethod
    async def increment_login_failed(account: str, expire: int = 300) -> int:
        """增加登录失败次数"""
        key = f"{CacheService.LOGIN_FAILED_PREFIX}:{account}"
        count = await redis_client.incr(key, amount=1)
        await redis_client.expire(key, expire)
        return count

    @staticmethod
    async def get_login_failed_count(account: str) -> int:
        """获取登录失败次数"""
        count = await redis_client.get(f"{CacheService.LOGIN_FAILED_PREFIX}:{account}")
        return int(count) if count else 0

    @staticmethod
    async def clear_login_failed(account: str):
        """清除登录失败计数"""
        await redis_client.delete(f"{CacheService.LOGIN_FAILED_PREFIX}:{account}")

    @staticmethod
    async def check_register_limit(ip: str, limit: int = 10) -> bool:
        """检查注册频率限制"""
        key = f"{CacheService.REGISTER_LIMIT_PREFIX}:{ip}"
        count = await redis_client.get(key)
        return count and int(count) > limit

    @staticmethod
    async def increment_register_count(ip: str, expire: int = 3600):
        """增加注册计数"""
        key = f"{CacheService.REGISTER_LIMIT_PREFIX}:{ip}"
        await redis_client.incr(key, amount=1)
        await redis_client.expire(key, expire)