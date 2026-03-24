# app/middleware/tenant.py
"""
租户识别中间件
从请求中提取租户信息
"""
from starlette.types import ASGIApp


class TenantMiddleware:
    """
    租户识别中间件 - 使用纯 ASGI 实现
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if "state" not in scope:
            scope["state"] = {}

        headers = scope.get("headers", [])
        for name, value in headers:
            if name == b"x-tenant-id":
                try:
                    scope["state"]["tenant_id_from_header"] = int(value.decode())
                except ValueError:
                    pass
                break

        await self.app(scope, receive, send)