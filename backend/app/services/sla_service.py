"""
模块用途: SLA 计算与升级策略服务
依赖配置: 环境变量 SLA_ESCALATION_DELAY_MINUTES（升级延迟，默认30分钟）
数据流向: 
  定时任务扫描 -> 识别超时任务 -> 执行升级策略（改派/回池/转值班）
  -> 记录操作日志 + 发送通知
函数清单:
    - calculate_due_at(): 计算节点到期时间
    - is_overdue(): 判断是否逾期
    - escalate_overdue_tasks(): 扫描并升级超时任务
    - _escalate_to_supervisor(): 改派上级
    - _release_to_group_pool(): 回组池
    - _transfer_to_on_duty(): 转值班
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.models.user import ApprovalGroup, ApprovalGroupMember, Department, User, UserProfile
from app.models.workflow import Task, TaskActionLog

logger = logging.getLogger(__name__)


class EscalationPolicy(str, Enum):
    """升级策略枚举。"""

    TO_SUPERVISOR = "to_supervisor"  # 改派上级
    TO_GROUP_POOL = "to_group_pool"  # 回组池
    TO_ON_DUTY = "to_on_duty"        # 转值班


@dataclass(frozen=True)
class EscalationResult:
    """升级操作结果。"""

    task_id: int
    policy: EscalationPolicy
    success: bool
    old_assignee: Optional[int]
    new_assignee: Optional[int]
    message: str


class SLAService:
    """SLA 处理与升级服务。"""

    # 默认升级延迟（分钟）：任务超时后多久触发升级
    DEFAULT_ESCALATION_DELAY_MINUTES = 30

    @staticmethod
    def calculate_due_at(sla_hours: Optional[int]) -> Optional[datetime]:
        """根据节点配置计算到期时间。

        :param sla_hours: SLA 时长（小时）
        :return: 到期时间或 None

        Time: O(1), Space: O(1)
        """

        if not sla_hours:
            return None
        return datetime.utcnow() + timedelta(hours=sla_hours)

    @staticmethod
    def is_overdue(due_at: Optional[datetime]) -> bool:
        """判断任务是否逾期。

        :param due_at: 到期时间
        :return: 是否逾期

        Time: O(1), Space: O(1)
        """

        if not due_at:
            return False
        return datetime.utcnow() > due_at

    @staticmethod
    def get_escalation_threshold() -> datetime:
        """获取升级时间阈值。

        超过该时间仍未处理的任务将触发升级。

        :return: 升级阈值时间

        Time: O(1), Space: O(1)
        """

        import os
        delay = int(os.getenv("SLA_ESCALATION_DELAY_MINUTES", "30"))
        return datetime.utcnow() - timedelta(minutes=delay)

    @staticmethod
    def escalate_overdue_tasks(
        tenant_id: int,
        db: Session,
        batch_size: int = 100,
    ) -> List[EscalationResult]:
        """扫描并升级超时任务。

        升级策略优先级：
        1. 有指派人且有上级 -> 改派上级
        2. 有小组 -> 回组池
        3. 其他 -> 转值班（预留）

        :param tenant_id: 租户 ID
        :param db: 数据库会话
        :param batch_size: 批量处理数量
        :return: 升级结果列表

        Time: O(N), Space: O(N)  N=batch_size
        """

        if not tenant_id:
            raise BusinessError("租户ID不能为空")

        threshold = SLAService.get_escalation_threshold()

        # 查询已超时且未完成的任务
        overdue_tasks = (
            db.query(Task)
            .filter(
                Task.tenant_id == tenant_id,
                Task.due_at <= threshold,
                Task.status.in_(["open", "claimed"]),
            )
            .limit(batch_size)
            .all()
        )

        results: List[EscalationResult] = []

        for task in overdue_tasks:
            result = SLAService._escalate_single_task(task, tenant_id, db)
            results.append(result)

        logger.info(
            "SLA升级扫描完成",
            extra={
                "tenant_id": tenant_id,
                "scanned": len(overdue_tasks),
                "successful": sum(1 for r in results if r.success),
            },
        )

        return results

    @staticmethod
    def _escalate_single_task(
        task: Task,
        tenant_id: int,
        db: Session,
    ) -> EscalationResult:
        """对单个任务执行升级。

        :param task: 待升级任务
        :param tenant_id: 租户 ID
        :param db: 数据库会话
        :return: 升级结果

        Time: O(1), Space: O(1)
        """

        old_assignee = task.assignee_user_id

        # 策略1：改派上级（如果当前有指派人）
        if task.assignee_user_id:
            supervisor_id = SLAService._find_supervisor(
                user_id=task.assignee_user_id,
                tenant_id=tenant_id,
                db=db,
            )
            if supervisor_id and supervisor_id != task.assignee_user_id:
                return SLAService._escalate_to_supervisor(
                    task=task,
                    supervisor_id=supervisor_id,
                    db=db,
                )

        # 策略2：回组池（如果有小组）
        if task.assignee_group_id:
            return SLAService._release_to_group_pool(task, db)

        # 策略3：转值班（预留）
        return SLAService._transfer_to_on_duty(task, db)

    @staticmethod
    def _find_supervisor(
        user_id: int,
        tenant_id: int,
        db: Session,
    ) -> Optional[int]:
        """查找用户的上级。

        查找顺序：
        1. UserProfile.supervisor_id（导师/直属上级）
        2. Department.parent_id 对应的部门负责人（预留）

        :param user_id: 用户 ID
        :param tenant_id: 租户 ID
        :param db: 数据库会话
        :return: 上级用户ID或None

        Time: O(1), Space: O(1)
        """

        # 查找导师/直属上级
        profile = (
            db.query(UserProfile)
            .filter(
                UserProfile.user_id == user_id,
                UserProfile.tenant_id == tenant_id,
            )
            .first()
        )

        if profile and profile.supervisor_id:
            # 验证上级是否有效
            supervisor = (
                db.query(User)
                .filter(
                    User.id == profile.supervisor_id,
                    User.tenant_id == tenant_id,
                    User.is_active.is_(True),
                )
                .first()
            )
            if supervisor:
                return supervisor.id

        # 查找部门上级（通过部门层级）
        user = (
            db.query(User)
            .filter(
                User.id == user_id,
                User.tenant_id == tenant_id,
            )
            .first()
        )

        if user and user.department_id:
            dept = (
                db.query(Department)
                .filter(
                    Department.id == user.department_id,
                    Department.tenant_id == tenant_id,
                )
                .first()
            )
            if dept and dept.parent_id:
                # 查找上级部门的负责人（取第一个活跃用户）
                # 这里简化处理，实际可能需要更复杂的逻辑
                manager = (
                    db.query(User)
                    .filter(
                        User.department_id == dept.parent_id,
                        User.tenant_id == tenant_id,
                        User.is_active.is_(True),
                    )
                    .first()
                )
                if manager:
                    return manager.id

        return None

    @staticmethod
    def _escalate_to_supervisor(
        task: Task,
        supervisor_id: int,
        db: Session,
    ) -> EscalationResult:
        """将任务改派给上级。

        :param task: 任务实例
        :param supervisor_id: 上级用户ID
        :param db: 数据库会话
        :return: 升级结果

        Time: O(1), Space: O(1)
        """

        old_assignee = task.assignee_user_id

        # 更新任务指派
        task.assignee_user_id = supervisor_id
        task.assignee_group_id = None
        task.claimed_by = None
        task.claimed_at = None
        task.status = "open"

        # 记录操作日志
        log = TaskActionLog(
            task_id=task.id,
            actor_user_id=0,  # 系统用户
            action="escalate_to_supervisor",
            detail_json={
                "old_assignee": old_assignee,
                "new_assignee": supervisor_id,
                "reason": "SLA超时自动升级",
            },
        )
        db.add(log)

        return EscalationResult(
            task_id=task.id,
            policy=EscalationPolicy.TO_SUPERVISOR,
            success=True,
            old_assignee=old_assignee,
            new_assignee=supervisor_id,
            message="已改派上级",
        )

    @staticmethod
    def _release_to_group_pool(
        task: Task,
        db: Session,
    ) -> EscalationResult:
        """将任务释放回小组待办池。

        :param task: 任务实例
        :param db: 数据库会话
        :return: 升级结果

        Time: O(1), Space: O(1)
        """

        old_assignee = task.assignee_user_id

        # 清空个人指派，保留小组指派
        task.assignee_user_id = None
        task.claimed_by = None
        task.claimed_at = None
        task.status = "open"

        # 记录操作日志
        log = TaskActionLog(
            task_id=task.id,
            actor_user_id=0,
            action="release_to_group_pool",
            detail_json={
                "old_assignee": old_assignee,
                "group_id": task.assignee_group_id,
                "reason": "SLA超时自动回池",
            },
        )
        db.add(log)

        return EscalationResult(
            task_id=task.id,
            policy=EscalationPolicy.TO_GROUP_POOL,
            success=True,
            old_assignee=old_assignee,
            new_assignee=None,
            message="已回组池",
        )

    @staticmethod
    def _transfer_to_on_duty(
        task: Task,
        db: Session,
    ) -> EscalationResult:
        """将任务转给值班人员（预留实现）。

        当前逻辑：标记为需要人工介入

        :param task: 任务实例
        :param db: 数据库会话
        :return: 升级结果

        Time: O(1), Space: O(1)
        """

        old_assignee = task.assignee_user_id

        # 记录操作日志（标记为需要人工处理）
        log = TaskActionLog(
            task_id=task.id,
            actor_user_id=0,
            action="escalate_to_on_duty",
            detail_json={
                "old_assignee": old_assignee,
                "reason": "SLA超时，需人工分配值班人员",
                "note": "值班制度暂未配置，需管理员手动处理",
            },
        )
        db.add(log)

        return EscalationResult(
            task_id=task.id,
            policy=EscalationPolicy.TO_ON_DUTY,
            success=False,  # 标记为未完成，需要人工介入
            old_assignee=old_assignee,
            new_assignee=None,
            message="值班制度未配置，需人工处理",
        )

    @staticmethod
    def get_sla_statistics(
        tenant_id: int,
        db: Session,
    ) -> Dict[str, int]:
        """获取SLA统计信息。

        :param tenant_id: 租户 ID
        :param db: 数据库会话
        :return: 统计字典

        Time: O(1), Space: O(1)
        """

        now = datetime.utcnow()

        total_overdue = (
            db.query(Task)
            .filter(
                Task.tenant_id == tenant_id,
                Task.due_at <= now,
                Task.status.in_(["open", "claimed"]),
            )
            .count()
        )

        total_open = (
            db.query(Task)
            .filter(
                Task.tenant_id == tenant_id,
                Task.status == "open",
            )
            .count()
        )

        total_claimed = (
            db.query(Task)
            .filter(
                Task.tenant_id == tenant_id,
                Task.status == "claimed",
            )
            .count()
        )

        return {
            "total_overdue": total_overdue,
            "total_open": total_open,
            "total_claimed": total_claimed,
        }
