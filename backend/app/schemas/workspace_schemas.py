"""
模块用途: 表单填写工作区相关Schema
依赖配置: 无
数据流向: HTTP请求 -> Pydantic校验 -> Service -> 响应序列化
函数清单:
    - FillableFormsQuery: 可填写表单查询参数
    - FillableFormItem: 可填写表单项
    - FillableFormsResponse: 可填写表单列表响应
    - QuickAccessResponse: 快捷入口响应
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class FillableFormsQuery(BaseModel):
    """可填写表单查询参数"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(default=None, max_length=100, description="搜索关键词")
    status: Optional[str] = Field(default=None, description="表单状态筛选")
    category: Optional[str] = Field(default=None, description="表单类别筛选")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向: asc/desc")

    @validator("sort_order")
    def validate_sort_order(cls, v: str) -> str:
        """验证排序方向只能是 asc 或 desc。

        Time: O(1), Space: O(1)
        """
        if v not in ["asc", "desc"]:
            raise ValueError("sort_order 必须是 'asc' 或 'desc'")
        return v


class FillableFormItem(BaseModel):
    """可填写表单项"""

    id: int
    name: str
    category: Optional[str]
    status: str
    owner_name: str
    created_at: datetime
    updated_at: datetime
    submit_deadline: Optional[datetime]
    is_expired: bool
    is_closed: bool
    is_fill_limit_reached: bool
    can_fill: bool
    description: Optional[str] = None

    class Config:
        from_attributes = True


class FillableFormsResponse(BaseModel):
    """可填写表单列表响应"""

    items: List[FillableFormItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class QuickAccessResponse(BaseModel):
    """快捷入口响应"""

    items: List[FillableFormItem]
