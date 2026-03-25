"""
模块用途: 首页统计数据模型
依赖配置: 无
数据流向: 数据库查询 -> Pydantic Schema -> API 响应
函数清单:
    - DashboardStatsResponse(): 首页统计响应
"""
from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    """首页统计数据响应"""

    pending_tasks: int = Field(default=0, ge=0, description="待办任务数")
    weekly_processed: int = Field(default=0, ge=0, description="本周处理量")
    avg_processing_time_minutes: float = Field(default=0.0, ge=0, description="平均处理时长（分钟）")
    approval_rate: float = Field(default=0.0, ge=0, le=100, description="审批通过率（百分比）")
