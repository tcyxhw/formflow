# app/middleware/logging.py
"""
日志中间件
记录请求和响应信息
"""
from fastapi import Request, Response
from starlette.types import ASGIApp
import time
import uuid
import logging

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """
    请求日志中间件 - 使用纯 ASGI 实现
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if "state" not in scope:
            scope["state"] = {}

        request_id = str(uuid.uuid4())
        scope["state"]["request_id"] = request_id

        start_time = time.time()

        logger.info(
            f"请求开始",
            extra={
                "request_id": request_id,
                "method": scope["method"],
                "url": str(scope.get("path", "")),
                "ip": scope.get("client", [""])[0] if scope.get("client") else None,
            }
        )

        response_started = False
        status_code = None

        async def send_wrapper(message):
            nonlocal response_started, status_code
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                headers = list(message.get("headers", []))
                headers.append((b"X-Request-ID", request_id.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)

            process_time = time.time() - start_time

            logger.info(
                f"请求完成",
                extra={
                    "request_id": request_id,
                    "status_code": status_code,
                    "process_time": process_time
                }
            )

        except Exception as e:
            process_time = time.time() - start_time

            logger.error(
                f"请求异常: {str(e)}",
                extra={
                    "request_id": request_id,
                    "process_time": process_time
                },
                exc_info=True
            )

            raise