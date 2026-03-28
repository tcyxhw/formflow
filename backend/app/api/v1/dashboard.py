"""
模块用途: 首页统计 API
依赖配置: 无
数据流向: HTTP 请求 -> Service 调用 -> 统一响应
函数清单:
    - get_dashboard_stats(): 获取首页统计数据
    - get_dashboard_trend(): 获取提交量趋势
    - get_dashboard_distribution(): 获取审批状态分布
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_tenant_id, get_current_user
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/stats", summary="获取首页统计数据")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """获取首页统计数据。

    :param current_user: 当前用户
    :param tenant_id: 租户 ID
    :param db: 数据库会话
    :return: 统计数据

    Time: O(N), Space: O(1)
    """

    stats = DashboardService.get_stats(
        tenant_id=tenant_id,
        current_user=current_user,
        db=db,
    )
    return success_response(data=stats.model_dump())


@router.get("/trend", summary="获取提交量趋势")
async def get_dashboard_trend(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """获取最近7天提交量趋势。

    :param tenant_id: 租户 ID
    :param db: 数据库会话
    :return: 趋势数据

    Time: O(N), Space: O(1)
    """

    trend = DashboardService.get_trend(
        tenant_id=tenant_id,
        db=db,
    )
    return success_response(data=trend.model_dump())


@router.get("/distribution", summary="获取审批状态分布")
async def get_dashboard_distribution(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """获取最近7天审批状态分布。

    :param tenant_id: 租户 ID
    :param db: 数据库会话
    :return: 分布数据

    Time: O(N), Space: O(1)
    """

    distribution = DashboardService.get_distribution(
        tenant_id=tenant_id,
        db=db,
    )
    return success_response(data=distribution.model_dump())
