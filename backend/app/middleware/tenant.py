# app/middleware/tenant.py
"""
租户识别中间件
从请求中提取租户信息
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable


class TenantMiddleware(BaseHTTPMiddleware):
    """
    租户识别中间件
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
            self,
            request: Request,
            call_next: Callable
    ):
        """
        从请求中提取租户信息

        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            响应对象
        """
        # 尝试从多个来源获取租户信息
        tenant_id = None

        # 1. 从请求头获取
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            try:
                tenant_id = int(tenant_header)
            except ValueError:
                pass

        # 2. 从子域名获取（如 school1.formflow.com）
        # host = request.headers.get("host", "")
        # if "." in host:
        #     subdomain = host.split(".")[0]
        #     # 根据子域名查询租户ID

        # 3. 从路径获取（如 /api/v1/tenant/1/...）
        # 这个通常在路由中处理

        # 将租户ID存储到request.state中
        request.state.tenant_id = tenant_id

        # 继续处理请求
        response = await call_next(request)

        return response