# app/core/exception_handlers.py
"""
全局异常处理器
统一处理所有异常，返回标准格式的错误响应
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.core.exceptions import BaseError

logger = logging.getLogger(__name__)


async def base_error_handler(request: Request, exc: BaseError) -> JSONResponse:
    """
    处理自定义基础错误

    统一返回格式：
    {
        "code": 4011,
        "message": "账号或密码错误",
        "data": null
    }
    """
    logger.warning(
        f"业务错误 [{exc.code}]: {exc.message} - "
        f"URL: {request.url} - "
        f"Method: {request.method} - "
        f"IP: {request.client.host if request.client else 'Unknown'}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": exc.data
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    处理标准HTTP异常（如FastAPI内部抛出的HTTPException）
    """
    logger.warning(
        f"HTTP异常 [{exc.status_code}]: {exc.detail} - "
        f"URL: {request.url} - "
        f"Method: {request.method}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理请求参数验证异常（Pydantic验证失败）
    """
    logger.warning(
        f"参数验证失败: {exc.errors()} - "
        f"URL: {request.url} - "
        f"Method: {request.method}"
    )

    # 格式化验证错误信息
    errors = []
    for error in exc.errors():
        field = ".".join([str(loc) for loc in error["loc"] if loc != "body"])
        message = error["msg"]
        if field:
            errors.append(f"{field}: {message}")
        else:
            errors.append(message)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 4220,
            "message": "请求参数验证失败",
            "data": {
                "errors": errors,
                "detail": exc.errors()
            }
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    处理数据库异常
    """
    logger.error(
        f"数据库异常: {str(exc)} - "
        f"URL: {request.url} - "
        f"Method: {request.method}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 5002,
            "message": "数据库操作失败，请稍后重试",
            "data": None
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理未捕获的异常（兜底处理）
    """
    logger.error(
        f"未捕获的异常: {type(exc).__name__}: {str(exc)} - "
        f"URL: {request.url} - "
        f"Method: {request.method} - "
        f"IP: {request.client.host if request.client else 'Unknown'}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 5000,
            "message": "系统内部错误，请联系管理员",
            "data": None
        }
    )