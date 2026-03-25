"""
模块用途: 首页统计 API
依赖配置: 无
数据流向: HTTP 请求 -> Service 调用 -> 统一响应
函数清单:
    - get_dashboard_stats(): 获取首页统计数据
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_tenant_id, get_current_user
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User
from app.schemas.dashboard_schemas import DashboardStatsResponse
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
