# app/middleware/auth.py
"""
认证中间件 - 处理双 Token 验证和自动刷新
"""
from typing import Optional
from fastapi import Request, HTTPException, status
from app.services.token_service import TokenService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """认证中间件 - 使用纯 ASGI 实现"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if "state" not in scope:
            scope["state"] = {}

        request = Request(scope, receive, send)

        if request.method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        if self._should_skip_auth(request.url.path):
            await self.app(scope, receive, send)
            return

        access_token = self._extract_token(request.headers.get("Authorization"))
        
        if not access_token:
            access_token = request.query_params.get("token")
            if access_token:
                logger.debug("从URL参数获取token")
        
        refresh_token = request.headers.get("X-Refresh-Token")

        logger.debug(f"请求: {request.method} {request.url.path}")
        logger.debug(f"访问令牌: {'存在' if access_token else '缺失'}")

        if not access_token:
            await self._send_error_response(scope, send, status.HTTP_401_UNAUTHORIZED, "未提供访问令牌")
            return

        access_payload = await TokenService.verify_access_token(access_token)

        if access_payload:
            scope["state"]["user_id"] = access_payload.get("user_id")
            scope["state"]["tenant_id"] = access_payload.get("tenant_id")
            scope["state"]["family_id"] = access_payload.get("family_id")
            scope["state"]["access_token"] = access_token

            exp_timestamp = access_payload.get("exp", 0)
            current_timestamp = datetime.utcnow().timestamp()
            time_remaining = exp_timestamp - current_timestamp

            new_access_token = None
            new_refresh_token = None
            token_rotated = False

            if time_remaining < 30 and refresh_token:
                try:
                    logger.info(f"预防性刷新 - 用户: {access_payload.get('user_id')}, 剩余: {time_remaining:.1f}秒")
                    new_tokens = await TokenService.refresh_access_token(refresh_token)
                    if new_tokens:
                        new_access_token = new_tokens["access_token"]
                        if new_tokens.get("token_rotated"):
                            new_refresh_token = new_tokens["refresh_token"]
                            token_rotated = True
                except Exception as e:
                    logger.warning(f"预防性刷新失败: {str(e)}")

            if new_access_token:
                await self._send_with_token_headers(scope, receive, send, new_access_token, new_refresh_token, token_rotated)
            else:
                await self.app(scope, receive, send)
            return

        logger.warning("访问令牌无效或已过期")

        if not refresh_token:
            logger.error("刷新令牌缺失")
            await self._send_error_response(scope, send, status.HTTP_401_UNAUTHORIZED, "访问令牌已过期，未提供刷新令牌")
            return

        try:
            logger.info("尝试使用刷新令牌获取新访问令牌")
            new_tokens = await TokenService.refresh_access_token(refresh_token)

            if not new_tokens:
                logger.error("刷新令牌无效或已过期")
                await self._send_error_response(scope, send, status.HTTP_401_UNAUTHORIZED, "刷新令牌无效或已过期，请重新登录")
                return

            new_access_payload = await TokenService.verify_access_token(new_tokens["access_token"])

            if not new_access_payload:
                logger.error("新访问令牌验证失败")
                await self._send_error_response(scope, send, status.HTTP_401_UNAUTHORIZED, "令牌刷新失败")
                return

            scope["state"]["user_id"] = new_access_payload.get("user_id")
            scope["state"]["tenant_id"] = new_access_payload.get("tenant_id")
            scope["state"]["family_id"] = new_access_payload.get("family_id")
            scope["state"]["access_token"] = new_tokens["access_token"]

            logger.info(f"令牌刷新成功 - 用户: {new_access_payload.get('user_id')}")

            await self._send_with_token_headers(scope, receive, send, new_tokens["access_token"], 
                                                 new_tokens.get("refresh_token"), new_tokens.get("token_rotated", False))

        except Exception as e:
            logger.error(f"Token刷新异常: {str(e)}", exc_info=True)
            await self._send_error_response(scope, send, status.HTTP_401_UNAUTHORIZED, "认证失败，请重新登录")

    def _extract_token(self, auth_header: str | None) -> str | None:
        if not auth_header:
            return None
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return None

    def _should_skip_auth(self, path: str) -> bool:
        skip_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/tenants",
            "/api/v1/auth/validate-tenant",
            "/api/health",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        return any(path.startswith(p) for p in skip_paths)

    async def _send_error_response(self, scope, send, status_code: int, detail: str):
        from app.config import settings
        import json

        response_body = json.dumps({"detail": detail}).encode("utf-8")

        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(response_body)).encode()),
        ]

        origin = None
        for name, value in scope.get("headers", []):
            if name == b"origin":
                origin = value.decode()
                break

        if origin and (origin in settings.BACKEND_CORS_ORIGINS or "*" in settings.BACKEND_CORS_ORIGINS):
            headers.append((b"access-control-allow-origin", origin.encode()))
            headers.append((b"access-control-allow-credentials", b"true"))

        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": headers,
        })
        await send({
            "type": "http.response.body",
            "body": response_body,
        })

    async def _send_with_token_headers(self, scope, receive, send, access_token, refresh_token, token_rotated):
        original_send = send

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"X-New-Access-Token", access_token.encode()))
                headers.append((b"X-Token-Refreshed", b"true"))
                if token_rotated and refresh_token:
                    headers.append((b"X-New-Refresh-Token", refresh_token.encode()))
                    headers.append((b"X-Token-Rotated", b"true"))
                message["headers"] = headers
            await original_send(message)

        await self.app(scope, receive, send_wrapper)


async def get_current_user(request: Request) -> dict:
    """获取当前用户信息"""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证"
        )

    return {
        "user_id": request.state.user_id,
        "tenant_id": request.state.tenant_id,
        "family_id": request.state.family_id
    }


async def get_current_token(request: Request) -> str:
    """获取当前请求的访问令牌"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供访问令牌"
        )

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌格式"
        )

    return parts[1]
