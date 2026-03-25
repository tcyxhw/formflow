"""
模块用途: 首页统计服务
依赖配置: 无
数据流向: API 层 -> DashboardService -> 数据库 -> Pydantic Schema
函数清单:
    - DashboardService.get_stats(): 获取首页统计数据
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import and_, case, extract, func, or_
from sqlalchemy.orm import Session

from app.models.user import ApprovalGroupMember, User
from app.models.workflow import ProcessInstance, Task, WorkflowOperationLog
from app.schemas.dashboard_schemas import DashboardStatsResponse

logger = logging.getLogger(__name__)


class DashboardService:
    """首页统计服务"""

    @staticmethod
    def get_stats(
        tenant_id: int,
        current_user: User,
        db: Session,
    ) -> DashboardStatsResponse:
        """获取首页统计数据。

        :param tenant_id: 租户 ID
        :param current_user: 当前用户
        :param db: 数据库会话
        :return: 统计数据响应

        Time: O(N), Space: O(1)
        """

        group_ids = DashboardService._get_user_group_ids(current_user.id, tenant_id, db)

        pending_tasks = DashboardService._count_pending_tasks(
            tenant_id=tenant_id,
            current_user=current_user,
            group_ids=group_ids,
            db=db,
        )

        weekly_processed = DashboardService._count_weekly_processed(
            tenant_id=tenant_id,
            current_user=current_user,
            db=db,
        )

        avg_processing_time = DashboardService._calc_avg_processing_time(
            tenant_id=tenant_id,
            db=db,
        )

        approval_rate = DashboardService._calc_approval_rate(
            tenant_id=tenant_id,
            db=db,
        )

        return DashboardStatsResponse(
            pending_tasks=pending_tasks,
            weekly_processed=weekly_processed,
            avg_processing_time_minutes=avg_processing_time,
            approval_rate=approval_rate,
        )

    @staticmethod
    def _get_user_group_ids(user_id: int, tenant_id: int, db: Session) -> List[int]:
        """查询用户所在审批小组。

        :param user_id: 用户 ID
        :param tenant_id: 租户 ID
        :param db: 会话
        :return: 小组 ID 列表

        Time: O(N), Space: O(N)
        """

        rows = (
            db.query(ApprovalGroupMember.group_id)
            .filter(
                ApprovalGroupMember.user_id == user_id,
                ApprovalGroupMember.tenant_id == tenant_id,
            )
            .all()
        )
        return [row.group_id for row in rows]

    @staticmethod
    def _count_pending_tasks(
        tenant_id: int,
        current_user: User,
        group_ids: List[int],
        db: Session,
    ) -> int:
        """统计待办任务数。

        :param tenant_id: 租户 ID
        :param current_user: 当前用户
        :param group_ids: 用户所在小组 ID 列表
        :param db: 数据库会话
        :return: 待办任务数

        Time: O(N), Space: O(1)
        """

        query = (
            db.query(func.count(Task.id))
            .filter(Task.tenant_id == tenant_id)
            .filter(Task.status == "open")
        )

        ownership_filters = [
            Task.assignee_user_id == current_user.id,
            Task.claimed_by == current_user.id,
        ]

        if group_ids:
            ownership_filters.append(
                and_(
                    Task.assignee_group_id.in_(group_ids),
                    Task.claimed_by.is_(None),
                )
            )

        query = query.filter(or_(*ownership_filters))

        return query.scalar() or 0

    @staticmethod
    def _count_weekly_processed(
        tenant_id: int,
        current_user: User,
        db: Session,
    ) -> int:
        """统计本周处理量。

        :param tenant_id: 租户 ID
        :param current_user: 当前用户
        :param db: 数据库会话
        :return: 本周处理量

        Time: O(N), Space: O(1)
        """

        week_ago = datetime.utcnow() - timedelta(days=7)

        count = (
            db.query(func.count(Task.id))
            .filter(Task.tenant_id == tenant_id)
            .filter(Task.status == "completed")
            .filter(Task.completed_at >= week_ago)
            .filter(Task.completed_by == current_user.id)
            .scalar()
        )

        return count or 0

    @staticmethod
    def _calc_avg_processing_time(
        tenant_id: int,
        db: Session,
    ) -> float:
        """计算平均处理时长（分钟）。

        :param tenant_id: 租户 ID
        :param db: 数据库会话
        :return: 平均处理时长（分钟）

        Time: O(N), Space: O(1)
        """

        week_ago = datetime.utcnow() - timedelta(days=7)

        result = (
            db.query(
                func.avg(
                    extract("epoch", Task.completed_at - Task.created_at) / 60
                )
            )
            .filter(Task.tenant_id == tenant_id)
            .filter(Task.status == "completed")
            .filter(Task.completed_at >= week_ago)
            .scalar()
        )

        return round(float(result or 0), 1)

    @staticmethod
    def _calc_approval_rate(
        tenant_id: int,
        db: Session,
    ) -> float:
        """计算审批通过率。

        :param tenant_id: 租户 ID
        :param db: 数据库会话
        :return: 审批通过率（百分比）

        Time: O(N), Space: O(1)
        """

        week_ago = datetime.utcnow() - timedelta(days=7)

        total_count = func.count().filter(
            WorkflowOperationLog.operation_type.in_(["APPROVE", "REJECT"])
        )

        result = (
            db.query(
                func.count().filter(WorkflowOperationLog.operation_type == "APPROVE")
                * 100.0
                / func.nullif(total_count, 0)
            )
            .filter(WorkflowOperationLog.tenant_id == tenant_id)
            .filter(WorkflowOperationLog.created_at >= week_ago)
            .scalar()
        )

        if result is None:
            return 0.0

        return round(float(result), 1)
