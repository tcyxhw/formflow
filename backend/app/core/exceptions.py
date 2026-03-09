# app/core/exceptions.py
"""
自定义异常类
统一的异常处理
"""
from typing import Any, Optional, Dict
from fastapi import HTTPException, status


class BaseError(HTTPException):
    """基础错误类"""

    def __init__(
            self,
            code: int,
            message: str,
            data: Optional[Any] = None,
            status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(status_code=status_code, detail=message)


class ValidationError(BaseError):
    """验证错误"""

    def __init__(self, message: str = "验证失败", data: Optional[Any] = None):
        super().__init__(
            code=4001,
            message=message,
            data=data,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class AuthenticationError(BaseError):
    """认证错误"""

    def __init__(self, message: str = "未登录或登录已过期", data: Optional[Any] = None):
        super().__init__(
            code=4011,
            message=message,
            data=data,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(BaseError):
    """授权错误"""

    def __init__(self, message: str = "权限不足", data: Optional[Any] = None):
        super().__init__(
            code=4031,
            message=message,
            data=data,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(BaseError):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在", data: Optional[Any] = None):
        super().__init__(
            code=4041,
            message=message,
            data=data,
            status_code=status.HTTP_404_NOT_FOUND
        )


class BusinessError(BaseError):
    """业务错误"""

    def __init__(self, message: str = "业务处理失败", data: Optional[Any] = None):
        super().__init__(
            code=5001,
            message=message,
            data=data,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class RateLimitError(BaseError):
    """限流错误"""

    def __init__(self, message: str = "请求过于频繁", data: Optional[Any] = None):
        super().__init__(
            code=4291,
            message=message,
            data=data,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class DatabaseError(BaseError):
    """数据库错误"""

    def __init__(self, message: str = "数据库操作失败", data: Optional[Any] = None):
        super().__init__(
            code=5002,
            message=message,
            data=data,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ExternalServiceError(BaseError):
    """外部服务错误"""

    def __init__(self, message: str = "外部服务调用失败", data: Optional[Any] = None):
        super().__init__(
            code=5003,
            message=message,
            data=data,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


# 错误码映射
ERROR_CODES = {
    # 4xxx 客户端错误
    4001: "验证失败",
    4011: "未登录或登录已过期",
    4012: "Token无效",
    4013: "Token已过期",
    4031: "权限不足",
    4032: "角色权限不足",
    4033: "数据权限不足",
    4041: "资源不存在",
    4042: "用户不存在",
    4043: "表单不存在",
    4291: "请求过于频繁",

    # 5xxx 服务端错误
    5001: "业务处理失败",
    5002: "数据库操作失败",
    5003: "外部服务调用失败",
    5004: "文件处理失败",
    5005: "缓存操作失败",
}