# app/schemas/base.py
"""
基础Schema定义
"""
from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

T = TypeVar('T')


class BaseSchema(BaseModel):
    """基础Schema"""
    model_config = ConfigDict(
        from_attributes=True,  # 允许从ORM模型创建
        str_strip_whitespace=True,  # 自动去除字符串首尾空格
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = 1
    size: int = 20

    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


class BatchOperationResult(BaseModel):
    """批量操作结果"""
    success_count: int = 0
    failed_count: int = 0
    failed_items: List[dict] = []
    message: str = "批量操作完成"