# app/schemas/ai_schemas.py
"""
AI 相关 Schema

包含 AI 表单生成的请求和响应数据模型
"""
from typing import Dict, Any, Optional
from pydantic import Field
from app.schemas.base import BaseSchema
from enum import Enum


class ThinkingType(str, Enum):
    """
    AI 思考模式枚举

    说明:
        ENABLED: 启用深度思考模式（适用于复杂任务）
        DISABLED: 禁用思考模式（适用于简单任务）
    """
    ENABLED = "enabled"
    DISABLED = "disabled"


class AIFormGenerateRequest(BaseSchema):
    """
    AI 表单生成请求

    字段说明:
        prompt: 用户需求描述文本（5-2000字符）
        thinking_type: 思考模式（可选，默认启用）
    """
    prompt: str = Field(
        ...,
        description="表单需求描述",
        min_length=5,
        max_length=2000,
        examples=["创建一个学生请假申请表，需要姓名、学号、请假类型、时间、事由"]
    )
    thinking_type: Optional[ThinkingType] = Field(
        default=ThinkingType.ENABLED,
        description="AI 思考模式"
    )


class AIFormGenerateResponse(BaseSchema):
    """
    AI 表单生成响应

    字段说明:
        config: 完整的表单配置 JSON
        summary: 配置说明（字段数量、规则数量等）
        field_count: 字段数量
        rule_count: 逻辑规则数量
    """
    config: Dict[str, Any] = Field(..., description="生成的表单配置")
    summary: str = Field(..., description="配置说明")
    field_count: int = Field(default=0, description="字段数量")
    rule_count: int = Field(default=0, description="逻辑规则数量")