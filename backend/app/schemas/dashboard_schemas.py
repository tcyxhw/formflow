"""
模块用途: 首页统计数据模型
依赖配置: 无
数据流向: 数据库查询 -> Pydantic Schema -> API 响应
函数清单:
    - DashboardStatsResponse(): 首页统计响应
    - DashboardTrendResponse(): 提交量趋势响应
    - DashboardDistributionResponse(): 审批状态分布响应
"""
from pydantic import BaseModel, Field
from typing import List


class DashboardStatsResponse(BaseModel):
    """首页统计数据响应"""

    pending_tasks: int = Field(default=0, ge=0, description="待办任务数")
    weekly_processed: int = Field(default=0, ge=0, description="本周处理量")
    avg_processing_time_minutes: float = Field(default=0.0, ge=0, description="平均处理时长（分钟）")
    approval_rate: float = Field(default=0.0, ge=0, le=100, description="审批通过率（百分比）")


class DailySubmissionCount(BaseModel):
    """每日提交数量"""

    date: str = Field(..., description="日期 (YYYY-MM-DD)")
    count: int = Field(default=0, ge=0, description="提交数量")


class DashboardTrendResponse(BaseModel):
    """提交量趋势响应"""

    data: List[DailySubmissionCount] = Field(default_factory=list, description="最近7天每日提交量")


class StatusDistributionItem(BaseModel):
    """状态分布项"""

    name: str = Field(..., description="状态名称")
    value: int = Field(default=0, ge=0, description="数量")


class DashboardDistributionResponse(BaseModel):
    """审批状态分布响应"""

    data: List[StatusDistributionItem] = Field(default_factory=list, description="状态分布数据")
