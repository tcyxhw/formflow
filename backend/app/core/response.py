# app/core/response.py
"""
统一响应格式封装
所有API响应都使用这个格式
"""
from typing import Any, Optional, Generic, TypeVar
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
from datetime import datetime, date
from decimal import Decimal

T = TypeVar('T')


class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""
    code: int = 200
    message: str = "成功"
    data: Optional[T] = None


class CustomJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理特殊类型"""

    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return super().default(obj)


def success_response(
        data: Any = None,
        message: str = "成功",
        code: int = 200
) -> JSONResponse:
    """
    成功响应

    Args:
        data: 响应数据
        message: 提示信息
        code: 业务状态码

    Returns:
        JSONResponse对象
    """
    content = {
        "code": code,
        "message": message,
        "data": data
    }

    # 使用自定义编码器处理特殊类型
    return JSONResponse(
        content=json.loads(
            json.dumps(content, cls=CustomJSONEncoder)
        )
    )


def error_response(
        message: str = "失败",
        code: int = 400,
        data: Any = None,
        status_code: int = 400
) -> JSONResponse:
    """
    错误响应

    Args:
        message: 错误信息
        code: 业务错误码
        data: 额外数据
        status_code: HTTP状态码

    Returns:
        JSONResponse对象
    """
    content = {
        "code": code,
        "message": message,
        "data": data
    }

    return JSONResponse(
        status_code=status_code,
        content=json.loads(
            json.dumps(content, cls=CustomJSONEncoder)
        )
    )


def paginated_response(
        items: list,
        total: int,
        page: int = 1,
        size: int = 20,
        message: str = "成功"
) -> JSONResponse:
    """
    分页响应

    Args:
        items: 数据列表
        total: 总数量
        page: 当前页码
        size: 每页大小
        message: 提示信息

    Returns:
        JSONResponse对象
    """
    data = {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if size > 0 else 0
    }

    return success_response(data=data, message=message)