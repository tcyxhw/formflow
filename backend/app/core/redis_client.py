# app/core/redis_client.py
"""
Redis连接池和缓存管理

功能概述:
- 提供Redis连接池管理和基础操作封装
- 支持字符串、哈希、列表、集合等Redis数据类型操作
- 提供缓存装饰器和限流器功能
- 统一的键名生成规范: {tenant_id}:{module}:{key}

主要类和方法:
┌─ RedisClient (Redis客户端封装)
│   ├─ connect()                    # 建立Redis连接
│   ├─ disconnect()                 # 关闭Redis连接
│   ├─ get_key()                    # 生成标准化的Redis键名
│   ├─ get/set/delete/exists()      # 基础键值操作
│   ├─ expire/ttl()                 # 过期时间管理
│   ├─ incr/decr()                  # 计数器操作
│   ├─ lpush/rpop/lrange()          # 列表操作
│   └─ hset/hget/hgetall/hdel()     # 哈希表操作
│
├─ @cache()                         # 缓存装饰器，支持自动缓存函数结果
├─ clear_cache_pattern()            # 批量清理匹配模式的缓存
└─ RateLimiter                      # 基于滑动窗口的限流器
    ├─ is_allowed()                 # 检查请求是否允许通过
    └─ get_remaining()              # 获取剩余请求次数

使用场景:
- 所有需要Redis操作的服务的基础依赖
- 提供统一的缓存操作接口
- 防止Redis连接泄漏和操作异常

依赖关系:
- 被所有缓存服务调用
- 不依赖其他业务服务
"""
import redis.asyncio as redis
from typing import Optional, Any, Union
import json
import pickle
from functools import wraps
import hashlib
import asyncio
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis客户端封装"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """建立Redis连接"""
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50
            )
            await self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
            raise

    async def disconnect(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis连接已关闭")

    def get_key(self, tenant_id: int, module: str, key: str) -> str:
        """
        生成Redis键名
        格式: {tenant_id}:{module}:{key}
        """
        return f"{tenant_id}:{module}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except json.JSONDecodeError:
            return value
        except Exception as e:
            logger.error(f"Redis获取失败: {str(e)}")
            return None

    async def set(
            self,
            key: str,
            value: Any,
            expire: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        try:
            if not isinstance(value, str):
                value = json.dumps(value, default=str)

            if expire:
                await self.redis_client.setex(key, expire, value)
            else:
                await self.redis_client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis设置失败: {str(e)}")
            return False

    async def delete(self, *keys: str) -> int:
        """删除缓存"""
        try:
            return await self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis删除失败: {str(e)}")
            return 0

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self.redis_client.exists(key) > 0

    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        return await self.redis_client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        return await self.redis_client.ttl(key)

    async def incr(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        return await self.redis_client.incrby(key, amount)

    async def decr(self, key: str, amount: int = 1) -> int:
        """递减计数器"""
        return await self.redis_client.decrby(key, amount)

    async def lpush(self, key: str, *values: Any) -> int:
        """列表左侧推入"""
        json_values = [json.dumps(v, default=str) for v in values]
        return await self.redis_client.lpush(key, *json_values)

    async def rpop(self, key: str) -> Optional[Any]:
        """列表右侧弹出"""
        value = await self.redis_client.rpop(key)
        if value:
            return json.loads(value)
        return None

    async def lrange(self, key: str, start: int, end: int) -> list:
        """获取列表范围"""
        values = await self.redis_client.lrange(key, start, end)
        return [json.loads(v) for v in values]

    async def hset(self, key: str, field: str, value: Any) -> int:
        """哈希表设置字段"""
        if not isinstance(value, str):
            value = json.dumps(value, default=str)
        return await self.redis_client.hset(key, field, value)

    async def hget(self, key: str, field: str) -> Optional[Any]:
        """哈希表获取字段"""
        value = await self.redis_client.hget(key, field)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def hgetall(self, key: str) -> dict:
        """获取哈希表所有字段"""
        data = await self.redis_client.hgetall(key)
        result = {}
        for field, value in data.items():
            try:
                result[field] = json.loads(value)
            except json.JSONDecodeError:
                result[field] = value
        return result

    async def hdel(self, key: str, *fields: str) -> int:
        """删除哈希表字段"""
        return await self.redis_client.hdel(key, *fields)


# 创建全局Redis客户端实例
redis_client = RedisClient()


def cache(
        expire: int = 3600,
        key_prefix: str = "",
        key_builder: Optional[callable] = None
):
    """
    缓存装饰器

    Args:
        expire: 过期时间(秒)
        key_prefix: 键前缀
        key_builder: 自定义键构建函数
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 构建缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # 默认使用函数名和参数构建键
                params = f"{args}_{kwargs}"
                params_hash = hashlib.md5(params.encode()).hexdigest()
                cache_key = f"{key_prefix}:{func.__name__}:{params_hash}"

            # 尝试从缓存获取
            cached_value = await redis_client.get(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            await redis_client.set(cache_key, result, expire)
            logger.debug(f"缓存设置: {cache_key}")

            return result

        return wrapper

    return decorator


async def clear_cache_pattern(pattern: str) -> int:
    """
    清除匹配模式的缓存

    Args:
        pattern: Redis键模式，如 "user:*"

    Returns:
        删除的键数量
    """
    try:
        # 使用SCAN避免阻塞
        deleted_count = 0
        async for key in redis_client.redis_client.scan_iter(match=pattern):
            await redis_client.delete(key)
            deleted_count += 1

        logger.info(f"清除缓存模式 {pattern}, 删除 {deleted_count} 个键")
        return deleted_count
    except Exception as e:
        logger.error(f"清除缓存失败: {str(e)}")
        return 0


class RateLimiter:
    """
    基于Redis的限流器
    使用滑动窗口算法
    """

    def __init__(
            self,
            max_requests: int = 100,
            window_seconds: int = 60
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def is_allowed(self, identifier: str) -> bool:
        """
        检查是否允许请求

        Args:
            identifier: 标识符(如用户ID、IP等)

        Returns:
            是否允许请求
        """
        key = f"rate_limit:{identifier}"
        now = asyncio.get_event_loop().time()

        # 使用Redis事务
        pipe = redis_client.redis_client.pipeline()

        # 移除过期的请求记录
        pipe.zremrangebyscore(key, 0, now - self.window_seconds)

        # 获取当前窗口内的请求数
        pipe.zcard(key)

        # 添加当前请求
        pipe.zadd(key, {str(now): now})

        # 设置过期时间
        pipe.expire(key, self.window_seconds)

        results = await pipe.execute()
        current_requests = results[1]

        return current_requests < self.max_requests

    async def get_remaining(self, identifier: str) -> int:
        """获取剩余请求次数"""
        key = f"rate_limit:{identifier}"
        now = asyncio.get_event_loop().time()

        # 清理过期记录
        await redis_client.redis_client.zremrangebyscore(
            key, 0, now - self.window_seconds
        )

        # 获取当前请求数
        current = await redis_client.redis_client.zcard(key)

        return max(0, self.max_requests - current)