# app/middleware/logging.py
"""
日志中间件
记录请求和响应信息
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import uuid
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    记录每个请求的详细信息
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
            self,
            request: Request,
            call_next: Callable
    ) -> Response:
        """
        处理请求和响应

        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            响应对象
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 记录请求开始时间
        start_time = time.time()

        # 记录请求信息
        logger.info(
            f"请求开始",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )

        # 处理请求
        try:
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            # 记录响应信息
            logger.info(
                f"请求完成",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": process_time
                }
            )

            return response

        except Exception as e:
            # 记录异常
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