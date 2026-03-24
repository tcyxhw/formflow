"""
模块用途: 流程操作日志服务
依赖配置: 无
数据流向: WorkflowOperationLog模型 -> 创建/查询 -> API响应
函数清单:
    - create_log(): 创建操作日志
    - get_process_logs(): 获取流程的操作日志
    - get_operation_timeline(): 获取操作时间线
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy import desc, and_

from app.models.workflow import WorkflowOperationLog
from app.core.exceptions import NotFoundError


class WorkflowOperationLogService:
    """流程操作日志服务"""

    @staticmethod
    def create_log(
        tenant_id: int,
        process_instance_id: int,
        operation_type: str,
        operator_id: int,
        comment: Optional[str] = None,
        detail_json: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> WorkflowOperationLog:
        """创建操作日志

        :param tenant_id: 租户ID
        :param process_instance_id: 流程实例ID
        :param operation_type: 操作类型 (SUBMIT/APPROVE/REJECT/CANCEL/CC)
        :param operator_id: 操作人ID
        :param comment: 操作备注
        :param detail_json: 操作详情JSON
        :param db: 数据库会话
        :return: 创建的操作日志对象

        Time: O(1), Space: O(1)
        """
        if db is None:
            raise ValueError("数据库会话不能为空")

        log = WorkflowOperationLog(
            tenant_id=tenant_id,
            process_instance_id=process_instance_id,
            operation_type=operation_type,
            operator_id=operator_id,
            comment=comment,
            detail_json=detail_json,
        )

        db.add(log)
        db.flush()

        return log

    @staticmethod
    def get_process_logs(
        process_instance_id: int,
        tenant_id: int,
        db: Session,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[WorkflowOperationLog], int]:
        """获取流程的操作日志

        :param process_instance_id: 流程实例ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :param page: 页码
        :param page_size: 每页数量
        :return: (日志列表, 总数)

        Time: O(N), Space: O(N)
        """

        # 构建基础查询
        stmt = select(WorkflowOperationLog).filter(
            and_(
                WorkflowOperationLog.process_instance_id == process_instance_id,
                WorkflowOperationLog.tenant_id == tenant_id,
            )
        )

        # 统计总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar()

        # 分页查询，按创建时间倒序
        logs = (
            db.execute(
                stmt.order_by(desc(WorkflowOperationLog.created_at))
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )

        return logs, total

    @staticmethod
    def get_operation_timeline(
        process_instance_id: int,
        tenant_id: int,
        db: Session,
    ) -> List[Dict[str, Any]]:
        """获取操作时间线

        :param process_instance_id: 流程实例ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 时间线列表，每个项包含:
            - id: 日志ID
            - operation_type: 操作类型
            - operator_id: 操作人ID
            - comment: 操作备注
            - detail_json: 操作详情
            - created_at: 创建时间

        Time: O(N), Space: O(N)
        """

        stmt = select(WorkflowOperationLog).filter(
            and_(
                WorkflowOperationLog.process_instance_id == process_instance_id,
                WorkflowOperationLog.tenant_id == tenant_id,
            )
        ).order_by(WorkflowOperationLog.created_at)
        result = db.execute(stmt)
        logs = result.scalars().all()

        timeline = []
        for log in logs:
            timeline.append({
                "id": log.id,
                "operation_type": log.operation_type,
                "operator_id": log.operator_id,
                "comment": log.comment,
                "detail_json": log.detail_json,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            })

        return timeline

    @staticmethod
    def get_log_by_id(
        log_id: int,
        tenant_id: int,
        db: Session,
    ) -> WorkflowOperationLog:
        """获取操作日志详情

        :param log_id: 日志ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 操作日志对象
        :raises NotFoundError: 日志不存在

        Time: O(1), Space: O(1)
        """

        stmt = select(WorkflowOperationLog).filter(
            and_(
                WorkflowOperationLog.id == log_id,
                WorkflowOperationLog.tenant_id == tenant_id,
            )
        )
        log = db.execute(stmt).scalars().first()

        if not log:
            raise NotFoundError("操作日志不存在")

        return log
