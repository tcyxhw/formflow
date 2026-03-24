"""
模块用途: 异步 API Client 正例
依赖配置: BASE_URL, TOKEN
数据流向: 外部 API -> 校验 -> 结构化返回
函数清单:
    - fetch_user(user_id): 获取用户信息
"""

from typing import Any
import httpx


async def fetch_user(user_id: str, base_url: str, token: str) -> dict[str, Any]:
    """
    获取用户信息。

    :param user_id: 用户 ID
    :param base_url: API 基础地址
    :param token: 鉴权令牌
    :return: 用户信息字典
    :raises ValueError: 参数非法
    """
    if not user_id:
        raise ValueError("user_id cannot be empty")
    if not base_url:
        raise ValueError("base_url cannot be empty")

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{base_url}/users/{user_id}", headers=headers)
        response.raise_for_status()
        return response.json()
