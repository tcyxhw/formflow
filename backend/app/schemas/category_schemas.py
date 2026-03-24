"""
模块用途: 表单分类相关的 Pydantic 模型
依赖配置: Pydantic, datetime
数据流向: 请求 -> 验证 -> 业务逻辑 -> 响应序列化
函数清单:
    - CategoryCreateRequest: 创建分类请求模型
    - CategoryUpdateRequest: 更新分类请求模型
    - CategoryResponse: 分类响应模型
    - CategoryListResponse: 分类列表响应模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CategoryCreateRequest(BaseModel):
    """创建分类请求"""
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")


class CategoryUpdateRequest(BaseModel):
    """更新分类请求"""
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")


class CategoryResponse(BaseModel):
    """分类响应"""
    id: int
    name: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryListResponse(BaseModel):
    """分类列表响应"""
    items: List[CategoryResponse]
    total: int
    page: int
    page_size: int
