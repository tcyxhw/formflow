"""
模块用途: 审批任务服务
依赖配置: 无
数据流向: API 层 -> TaskService -> 数据库 -> Pydantic Schema
函数清单:
    - TaskService.list_tasks(): 查询待办任务
    - TaskService.claim_task(): 认领任务
    - TaskService.release_task(): 释放任务
    - TaskService.perform_task_action(): 执行审批动作
    - TaskService.get_process_timeline(): 获取流程轨迹
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query, Session

from app.core.exceptions import AuthorizationError, BusinessError, NotFoundError
from app.models.form import Submission
from app.models.user import ApprovalGroup, ApprovalGroupMember, User
from app.models.workflow import (
    FlowDefinition,
    FlowNode,
    ProcessInstance,
    Task,
    TaskActionLog,
)
from app.services.process_service import ProcessService
from app.schemas.approval_schemas import (
    ProcessTimelineResponse,
    SlaLevel,
    TaskSlaSummary,
    TaskActionRequest,
    TaskAddSignRequest,
    TaskAssigneeInfo,
    TaskDelegateRequest,
    TaskListRequest,
    TaskResponse,
    TaskStatus,
    TaskTransferRequest,
    TimelineAction,
    TimelineEntry,
)

logger = logging.getLogger(__name__)


class TaskService:
    """审批任务相关服务"""

    @staticmethod
    def list_tasks(
        request: TaskListRequest,
        tenant_id: int,
        current_user: User,
        db: Session,
    ) -> Tuple[List[TaskResponse], int]:
        """查询待办任务。

        :param request: 查询入参
        :param tenant_id: 租户 ID
        :param current_user: 当前用户
        :param db: 数据库会话
        :return: (任务列表, 总数)

        Time: O(N), Space: O(N)
        """

        if not tenant_id:
            raise AuthorizationError("缺少租户信息")

        group_ids = TaskService._get_user_group_ids(current_user.id, tenant_id, db)

        base_query = TaskService._build_filtered_task_query(
            request=request,
            tenant_id=tenant_id,
            current_user=current_user,
            group_ids=group_ids,
            db=db,
        )

        total = base_query.count()

        data_query = (
            base_query
            .outerjoin(Submission, Submission.id == ProcessInstance.submission_id)
            .outerjoin(User, User.id == Submission.submitter_user_id)
            .with_entities(
                Task,
                FlowNode.name.label("node_name"),
                FlowDefinition.name.label("flow_name"),
                ApprovalGroup.name.label("group_name"),
                FlowNode.sla_hours.label("sla_hours"),
                ProcessInstance.state.label("process_state"),
                Submission.submitter_user_id.label("submitter_user_id"),
                User.name.label("submitter_name"),
                Submission.data_jsonb.label("form_data_snapshot"),
                ProcessInstance.form_id.label("form_id"),
            )
        )

        task_rows = (
            data_query.order_by(Task.created_at.desc())
            .offset(request.offset)
            .limit(request.page_size)
            .all()
        )

        items = [
            TaskService._build_task_response(
                task=row.Task,
                node_name=row.node_name,
                flow_name=row.flow_name,
                group_name=row.group_name,
                sla_hours=row.sla_hours,
                process_state=row.process_state,
                submitter_user_id=row.submitter_user_id,
                submitter_name=row.submitter_name,
                form_data_snapshot=row.form_data_snapshot,
                form_id=row.form_id,
            )
            for row in task_rows
        ]

        return items, total

    @staticmethod
    def _apply_sla_level_filter(query: Query, sla_level: SlaLevel) -> Query:
        """根据请求参数应用 SLA 等级过滤。

        :param query: SQLAlchemy 查询对象
        :param sla_level: 目标 SLA 等级
        :return: 追加过滤条件后的查询

        Time: O(1), Space: O(1)
        """

        now = datetime.utcnow()

        if sla_level == SlaLevel.UNKNOWN:
            return query.filter(Task.due_at.is_(None))

        query = query.filter(Task.due_at.isnot(None))

        if sla_level == SlaLevel.EXPIRED:
            return query.filter(Task.due_at <= now)

        if sla_level == SlaLevel.CRITICAL:
            upper = now + timedelta(minutes=30)
            return query.filter(Task.due_at > now, Task.due_at <= upper)

        if sla_level == SlaLevel.WARNING:
            lower = now + timedelta(minutes=30)
            upper = now + timedelta(minutes=120)
            return query.filter(Task.due_at > lower, Task.due_at <= upper)

        if sla_level == SlaLevel.NORMAL:
            lower = now + timedelta(minutes=120)
            return query.filter(Task.due_at > lower)

        return query

    @staticmethod
    def _build_filtered_task_query(
        request: TaskListRequest,
        tenant_id: int,
        current_user: User,
        group_ids: List[int] | None,
        db: Session,
    ) -> Query:
        """构建带有可见性和筛选条件的任务查询。"""

        query = (
            db.query(Task)
            .join(FlowNode, FlowNode.id == Task.node_id)
            .join(ProcessInstance, ProcessInstance.id == Task.process_instance_id)
            .join(FlowDefinition, FlowDefinition.id == ProcessInstance.flow_definition_id)
            .outerjoin(ApprovalGroup, ApprovalGroup.id == Task.assignee_group_id)
            .filter(Task.tenant_id == tenant_id)
        )

        if request.status:
            query = query.filter(Task.status == request.status.value)

        ownership_filters = [
            Task.assignee_user_id == current_user.id,
            Task.claimed_by == current_user.id,
        ]

        if request.include_group_tasks and group_ids:
            ownership_filters.append(
                and_(
                    Task.assignee_group_id.in_(group_ids),
                    Task.claimed_by.is_(None),
                )
            )

        if ownership_filters:
            if request.only_mine:
                query = query.filter(or_(*ownership_filters[:2]))
            else:
                query = query.filter(or_(*ownership_filters))

        if request.keyword:
            like_expr = f"%{request.keyword}%"
            query = query.filter(
                or_(
                    FlowNode.name.ilike(like_expr),
                    FlowDefinition.name.ilike(like_expr),
                )
            )

        if request.sla_level:
            query = TaskService._apply_sla_level_filter(query, request.sla_level)

        return query

    @staticmethod
    def get_sla_summary(
        request: TaskListRequest,
        tenant_id: int,
        current_user: User,
        db: Session,
    ) -> TaskSlaSummary:
        """统计不同 SLA 等级的任务数量。"""

        if not tenant_id:
            raise AuthorizationError("缺少租户信息")

        group_ids = TaskService._get_user_group_ids(current_user.id, tenant_id, db)
        query = TaskService._build_filtered_task_query(
            request=request,
            tenant_id=tenant_id,
            current_user=current_user,
            group_ids=group_ids,
            db=db,
        )

        due_rows = query.with_entities(Task.due_at).all()

        counters = {level.value: 0 for level in SlaLevel}
        for due_at, in due_rows:
            remaining_minutes = TaskService._calc_remaining_minutes(due_at)
            level = TaskService._calc_sla_level(remaining_minutes)
            counters[level] = counters.get(level, 0) + 1

        summary = TaskSlaSummary(
            total=sum(counters.values()),
            unknown=counters.get("unknown", 0),
            normal=counters.get("normal", 0),
            warning=counters.get("warning", 0),
            critical=counters.get("critical", 0),
            expired=counters.get("expired", 0),
        )
        return summary

    @staticmethod
    def claim_task(
        task_id: int,
        tenant_id: int,
        current_user: User,
        db: Session,
    ) -> TaskResponse:
        """认领任务。

        :param task_id: 任务 ID
        :param tenant_id: 租户 ID
        :param current_user: 当前用户
        :param db: 数据库会话
        :return: 最新任务信息

        Time: O(1), Space: O(1)
        """

        task = TaskService._get_task(task_id, tenant_id, db)
        TaskService._ensure_can_claim(task, current_user, tenant_id, db)

        if task.status != TaskStatus.OPEN.value:
            raise BusinessError("任务当前不可认领")

        task.claimed_by = current_user.id
        task.claimed_at = datetime.utcnow()
        task.status = TaskStatus.CLAIMED.value

        TaskService._create_action_log(
            task_id=task.id,
            tenant_id=tenant_id,
            actor_user_id=current_user.id,
            action="claim",
            detail={"message": "任务被认领"},
            db=db,
        )

        db.commit()
        db.refresh(task)

        return TaskService._enrich_task(task, db)

    @staticmethod
    def release_task(
        task_id: int,
        tenant_id: int,
        current_user: User,
        db: Session,
    ) -> TaskResponse:
        """释放任务。

        :param task_id: 任务 ID
        :param tenant_id: 租户 ID
        :param current_user: 当前用户
        :param db: 数据库会话
        :return: 最新任务信息

        Time: O(1), Space: O(1)
        """

        task = TaskService._get_task(task_id, tenant_id, db)

        if task.claimed_by != current_user.id:
            raise AuthorizationError("仅认领人可释放任务")

        task.claimed_by = None
        task.claimed_at = None
        task.status = TaskStatus.OPEN.value

        TaskService._create_action_log(
            task_id=task.id,
            tenant_id=tenant_id,
            actor_user_id=current_user.id,
            action="release",
            detail={"message": "任务已释放"},
            db=db,
        )

        db.commit()
        db.refresh(task)

        return TaskService._enrich_task(task, db)

    @staticmethod
    def cancel_task(
        task_id: int,
        tenant_id: int,
        current_user: User,
        db: Session,
    ) -> TaskResponse:
        """撤回任务（取消审批流程）。

        撤回条件：
        - 任务状态为 open（未被认领）
        - 且未被审批节点审批过

        撤回后操作：
        - 将任务状态标记为 canceled
        - 将流程实例状态标记为 canceled
        - 将关联的提交记录状态回退为 pending_approval

        :param task_id: 任务 ID
        :param tenant_id: 租户 ID
        :param current_user: 当前用户
        :param db: 数据库会话
        :return: 取消后的任务信息

        Time: O(1), Space: O(1)
        """
        from app.services.submission_service import SubmissionStatus

        task = TaskService._get_task(task_id, tenant_id, db)

        if task.status != TaskStatus.OPEN.value:
            raise BusinessError("只有待认领状态的任务才能撤回")

        task.status = TaskStatus.CANCELED.value

        process_instance = db.query(ProcessInstance).filter(
            ProcessInstance.id == task.process_instance_id,
            ProcessInstance.tenant_id == tenant_id
        ).first()

        if process_instance:
            process_instance.state = "canceled"

            submission = db.query(Submission).filter(
                Submission.id == process_instance.submission_id,
                Submission.tenant_id == tenant_id
            ).first()

            if submission:
                submission.status = SubmissionStatus.PENDING_APPROVAL.value

        TaskService._create_action_log(
            task_id=task.id,
            tenant_id=tenant_id,
            actor_user_id=current_user.id,
            action="cancel",
            detail={"message": "任务已撤回"},
            db=db,
        )

        db.commit()
        db.refresh(task)

        return TaskService._enrich_task(task, db)

    @staticmethod
    def perform_task_action(
        task_id: int,
        tenant_id: int,
        request: TaskActionRequest,
        current_user: User,
        db: Session,
    ) -> TaskResponse:
        """执行审批操作。

        :param task_id: 任务 ID
        :param tenant_id: 租户 ID
        :param request: 操作请求
        :param current_user: 当前用户
        :param db: 数据库会话
        :return: 最新任务信息

        Time: O(1), Space: O(1)
        """

        task = TaskService._get_task(task_id, tenant_id, db)
        TaskService._ensure_can_act(task, current_user, tenant_id, db)

        task.action = request.action
        task.status = TaskStatus.COMPLETED.value
        task.completed_by = current_user.id
        task.completed_at = datetime.utcnow()
        task.claimed_by = task.claimed_by or current_user.id

        detail: Dict[str, object] = {
            "comment": request.comment,
            "extra": request.extra_data,
        }

        TaskService._create_action_log(
            task_id=task.id,
            tenant_id=tenant_id,
            actor_user_id=current_user.id,
            action=request.action,
            detail=detail,
            db=db,
        )

        ProcessService.handle_task_completion(
            task=task,
            tenant_id=tenant_id,
            db=db,
            context={
                "action": request.action,
                "comment": request.comment,
                "extra_data": request.extra_data,
                "actor_user_id": current_user.id,
            },
        )

        db.commit()
        db.refresh(task)

        return TaskService._enrich_task(task, db)

    @staticmethod
    def transfer_task(
        task_id: int,
        tenant_id: int,
        request: TaskTransferRequest,
        current_user: User,
        db: Session,
    ) -> TaskResponse:
        """转交任务给新的处理人。

        Time: O(1), Space: O(1)
        """

        task = TaskService._get_task(task_id, tenant_id, db)
        TaskService._ensure_can_act(task, current_user, tenant_id, db)

        target_user = TaskService._get_user(request.target_user_id, tenant_id, db)
        task.assignee_user_id = target_user.id
        task.assignee_group_id = None
        task.status = TaskStatus.OPEN.value
        task.claimed_by = None
        task.claimed_at = None
        task.action = None

        TaskService._create_action_log(
            task_id=task.id,
            tenant_id=tenant_id,
            actor_user_id=current_user.id,
            action="transfer",
            detail={
                "target_user_id": target_user.id,
                "message": request.message,
            },
            db=db,
        )

        db.commit()
        db.refresh(task)
        return TaskService._enrich_task(task, db)

    @staticmethod
    def delegate_task(
        task_id: int,
        tenant_id: int,
        request: TaskDelegateRequest,
        current_user: User,
        db: Session,
    ) -> TaskResponse:
        """委托任务给其他处理人。

        Time: O(1), Space: O(1)
        """

        task = TaskService._get_task(task_id, tenant_id, db)
        TaskService._ensure_can_act(task, current_user, tenant_id, db)

        delegate_user = TaskService._get_user(request.delegate_user_id, tenant_id, db)
        task.assignee_user_id = delegate_user.id
        task.assignee_group_id = None
        task.claimed_by = None
        task.claimed_at = None
        task.status = TaskStatus.OPEN.value

        TaskService._create_action_log(
            task_id=task.id,
            tenant_id=tenant_id,
            actor_user_id=current_user.id,
            action="delegate",
            detail={
                "delegate_user_id": delegate_user.id,
                "expire_hours": request.expire_hours,
                "message": request.message,
            },
            db=db,
        )

        db.commit()
        db.refresh(task)
        return TaskService._enrich_task(task, db)

    @staticmethod
    def add_sign_tasks(
        task_id: int,
        tenant_id: int,
        request: TaskAddSignRequest,
        current_user: User,
        db: Session,
    ) -> List[TaskResponse]:
        """为任务添加加签处理人。

        Time: O(M), Space: O(M)  (M = 新增处理人数)
        """

        task = TaskService._get_task(task_id, tenant_id, db)
        TaskService._ensure_can_act(task, current_user, tenant_id, db)

        node = db.query(FlowNode).filter(FlowNode.id == task.node_id).first()
        if not node:
            raise NotFoundError("节点不存在，无法加签")

        new_tasks: List[Task] = []
        unique_user_ids = list(dict.fromkeys(request.user_ids))
        for user_id in unique_user_ids:
            TaskService._get_user(user_id, tenant_id, db)
            new_task = Task(
                tenant_id=tenant_id,
                process_instance_id=task.process_instance_id,
                node_id=task.node_id,
                assignee_user_id=user_id,
                status=TaskStatus.OPEN.value,
                payload_json=task.payload_json,
                due_at=task.due_at,
            )
            db.add(new_task)
            new_tasks.append(new_task)

        TaskService._create_action_log(
            task_id=task.id,
            tenant_id=tenant_id,
            actor_user_id=current_user.id,
            action="add_sign",
            detail={
                "add_sign_user_ids": unique_user_ids,
                "message": request.message,
            },
            db=db,
        )

        db.commit()
        responses = [TaskService._enrich_task(t, db) for t in new_tasks]
        return responses

    @staticmethod
    def get_process_timeline(
        process_instance_id: int,
        tenant_id: int,
        db: Session,
    ) -> ProcessTimelineResponse:
        """获取流程轨迹。

        :param process_instance_id: 流程实例 ID
        :param tenant_id: 租户 ID
        :param db: 数据库会话
        :return: 流程轨迹响应

        Time: O(N), Space: O(N)
        """

        process = (
            db.query(ProcessInstance)
            .filter(
                ProcessInstance.id == process_instance_id,
                ProcessInstance.tenant_id == tenant_id,
            )
            .first()
        )

        if not process:
            raise NotFoundError("流程实例不存在")

        task_rows = (
            db.query(Task, FlowNode.name.label("node_name"))
            .join(FlowNode, FlowNode.id == Task.node_id)
            .filter(
                Task.process_instance_id == process_instance_id,
                Task.tenant_id == tenant_id,
            )
            .order_by(Task.created_at.asc())
            .all()
        )

        if not task_rows:
            raise NotFoundError("流程暂无任务记录")

        task_ids = [row.Task.id for row in task_rows]
        logs = (
            db.query(TaskActionLog)
            .filter(TaskActionLog.task_id.in_(task_ids))
            .order_by(TaskActionLog.created_at.asc())
            .all()
        )
        log_map = TaskService._group_logs_by_task(logs)
        user_map = TaskService._map_user_names(TaskService._collect_actor_ids(logs), db)

        entries = [
            TaskService._build_timeline_entry(
                task=row.Task,
                node_name=row.node_name,
                logs=log_map.get(row.Task.id),
                user_map=user_map,
            )
            for row in task_rows
        ]

        return ProcessTimelineResponse(
            process_instance_id=process.id,
            state=process.state,
            entries=entries,
        )

    @staticmethod
    def list_group_tasks(
        request: TaskListRequest,
        tenant_id: int,
        current_user: User,
        db: Session,
    ) -> Tuple[List[TaskResponse], int]:
        """查询当前用户所在小组的待认领任务。

        Time: O(N), Space: O(N)
        """

        group_ids = TaskService._get_user_group_ids(current_user.id, tenant_id, db)
        if not group_ids:
            return [], 0

        query = (
            db.query(
                Task,
                FlowNode.name.label("node_name"),
                FlowDefinition.name.label("flow_name"),
                ApprovalGroup.name.label("group_name"),
                FlowNode.sla_hours.label("sla_hours"),
                ProcessInstance.state.label("process_state"),
            )
            .join(FlowNode, FlowNode.id == Task.node_id)
            .join(ProcessInstance, ProcessInstance.id == Task.process_instance_id)
            .join(FlowDefinition, FlowDefinition.id == ProcessInstance.flow_definition_id)
            .join(ApprovalGroup, ApprovalGroup.id == Task.assignee_group_id)
            .filter(
                Task.tenant_id == tenant_id,
                Task.assignee_group_id.in_(group_ids),
                Task.claimed_by.is_(None),
                Task.status == TaskStatus.OPEN.value,
            )
        )

        total = query.count()
        rows = (
            query.order_by(Task.created_at.asc())
            .offset(request.offset)
            .limit(request.page_size)
            .all()
        )

        items = [
            TaskService._build_task_response(
                task=row.Task,
                node_name=row.node_name,
                flow_name=row.flow_name,
                group_name=row.group_name,
                sla_hours=row.sla_hours,
            )
            for row in rows
        ]

        return items, total

    # ---------------------------- 私有方法 ----------------------------
    @staticmethod
    def _build_task_response(
        task: Task,
        node_name: str | None,
        flow_name: str | None,
        group_name: str | None,
        sla_hours: int | None,
        process_state: str | None,
        submitter_user_id: int | None = None,
        submitter_name: str | None = None,
        form_data_snapshot: Dict[str, object] | None = None,
        form_id: int | None = None,
    ) -> TaskResponse:
        """构建任务响应对象。

        :param task: 任务实例
        :param node_name: 节点名称
        :param flow_name: 流程名称
        :param group_name: 小组名称
        :param sla_hours: 节点 SLA
        :param submitter_user_id: 提交人ID
        :param submitter_name: 提交人姓名
        :param form_data_snapshot: 表单数据快照
        :param form_id: 表单ID
        :return: 任务响应

        Time: O(1), Space: O(1)
        """

        payload = task.payload_json or {}
        now = datetime.utcnow()
        is_overdue = bool(task.due_at and now > task.due_at)
        remaining_minutes = TaskService._calc_remaining_minutes(task.due_at)
        sla_level = TaskService._calc_sla_level(remaining_minutes)

        return TaskResponse(
            id=task.id,
            process_instance_id=task.process_instance_id,
            process_state=process_state or "running",
            node_id=task.node_id,
            node_name=node_name,
            flow_name=flow_name,
            status=TaskStatus(task.status),
            action=task.action,
            payload=payload,
            assignee=TaskAssigneeInfo(
                user_id=task.assignee_user_id,
                group_id=task.assignee_group_id,
                group_name=group_name,
            ),
            claimed_by=task.claimed_by,
            claimed_at=task.claimed_at,
            due_at=task.due_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
            sla_hours=sla_hours,
            is_overdue=is_overdue,
            remaining_sla_minutes=remaining_minutes,
            sla_level=sla_level,
            submitter_user_id=submitter_user_id,
            submitter_name=submitter_name,
            form_data_snapshot=form_data_snapshot,
            form_id=form_id,
        )

    @staticmethod
    def _get_task(task_id: int, tenant_id: int, db: Session) -> Task:
        """查询单个任务。

        :param task_id: 任务 ID
        :param tenant_id: 租户 ID
        :param db: 会话
        :return: 任务实例

        Time: O(1), Space: O(1)
        """

        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.tenant_id == tenant_id)
            .first()
        )
        if not task:
            raise NotFoundError("任务不存在")
        return task

    @staticmethod
    def _get_user(user_id: int, tenant_id: int, db: Session) -> User:
        """根据 ID 查询用户。"""

        user = (
            db.query(User)
            .filter(User.id == user_id, User.tenant_id == tenant_id, User.is_active.is_(True))
            .first()
        )
        if not user:
            raise NotFoundError("用户不存在或不可用")
        return user

    @staticmethod
    def _ensure_can_claim(task: Task, current_user: User, tenant_id: int, db: Session) -> None:
        """校验是否可认领。

        :param task: 任务实例
        :param current_user: 当前用户
        :param tenant_id: 租户 ID
        :param db: 会话

        Time: O(1), Space: O(1)
        """

        if task.assignee_user_id and task.assignee_user_id != current_user.id:
            raise AuthorizationError("任务已指定其他处理人")

        if task.assignee_group_id:
            group_ids = TaskService._get_user_group_ids(current_user.id, tenant_id, db)
            if task.assignee_group_id not in group_ids:
                raise AuthorizationError("不在该任务小组，无法认领")

        if task.claimed_by and task.claimed_by != current_user.id:
            raise BusinessError("任务已被其他人认领")

    @staticmethod
    def _ensure_can_act(task: Task, current_user: User, tenant_id: int, db: Session) -> None:
        """校验是否可执行任务。

        :param task: 任务实例
        :param current_user: 当前用户
        :param tenant_id: 租户 ID
        :param db: 会话

        Time: O(1), Space: O(1)
        """

        if task.assignee_user_id and task.assignee_user_id != current_user.id:
            raise AuthorizationError("无权处理该任务")

        if task.assignee_group_id and task.claimed_by != current_user.id:
            group_ids = TaskService._get_user_group_ids(current_user.id, tenant_id, db)
            if task.assignee_group_id not in group_ids:
                raise AuthorizationError("不在任务小组")

        if task.status == TaskStatus.COMPLETED.value:
            raise BusinessError("任务已处理")

    @staticmethod
    def _create_action_log(
        task_id: int,
        tenant_id: int,
        actor_user_id: int,
        action: str,
        detail: Dict[str, object] | None,
        db: Session,
    ) -> None:
        """写入任务操作日志。

        :param task_id: 任务 ID
        :param tenant_id: 租户 ID
        :param actor_user_id: 操作者 ID
        :param action: 动作
        :param detail: 详情
        :param db: 会话

        Time: O(1), Space: O(1)
        """

        log = TaskActionLog(
            tenant_id=tenant_id,
            task_id=task_id,
            actor_user_id=actor_user_id,
            action=action,
            detail_json=detail,
        )
        db.add(log)

    @staticmethod
    def _enrich_task(task: Task, db: Session) -> TaskResponse:
        """查询并补充任务附加信息。

        :param task: 任务实例
        :param db: 会话
        :return: 任务响应

        Time: O(1), Space: O(1)
        """

        node = db.query(FlowNode).filter(FlowNode.id == task.node_id).first()
        process = db.query(ProcessInstance).filter(ProcessInstance.id == task.process_instance_id).first()
        flow_name = None
        process_state = "running"
        submitter_user_id = None
        submitter_name = None
        form_data_snapshot = None
        form_id = None

        if process:
            flow_def = (
                db.query(FlowDefinition)
                .filter(FlowDefinition.id == process.flow_definition_id)
                .first()
            )
            flow_name = flow_def.name if flow_def else None
            process_state = process.state
            form_id = process.form_id

            if process.submission_id:
                submission = (
                    db.query(Submission)
                    .filter(Submission.id == process.submission_id)
                    .first()
                )
                if submission:
                    submitter_user_id = submission.submitter_user_id
                    form_data_snapshot = submission.data_jsonb
                    if submitter_user_id:
                        submitter = (
                            db.query(User)
                            .filter(User.id == submitter_user_id)
                            .first()
                        )
                        submitter_name = submitter.name if submitter else None

        group_name = None
        if task.assignee_group_id:
            group = (
                db.query(ApprovalGroup)
                .filter(ApprovalGroup.id == task.assignee_group_id)
                .first()
            )
            group_name = group.name if group else None

        return TaskService._build_task_response(
            task=task,
            node_name=node.name if node else None,
            flow_name=flow_name,
            group_name=group_name,
            sla_hours=node.sla_hours if node else None,
            process_state=process_state,
            submitter_user_id=submitter_user_id,
            submitter_name=submitter_name,
            form_data_snapshot=form_data_snapshot,
            form_id=form_id,
        )

    @staticmethod
    def _calc_remaining_minutes(due_at: datetime | None) -> int | None:
        """计算剩余 SLA 分钟数。"""

        if not due_at:
            return None

        delta = due_at - datetime.utcnow()
        total_minutes = int(delta.total_seconds() // 60)
        return max(total_minutes, 0)

    @staticmethod
    def _calc_sla_level(remaining_minutes: int | None) -> str:
        """根据剩余分钟数判定 SLA 等级。"""

        if remaining_minutes is None:
            return "unknown"
        if remaining_minutes <= 0:
            return "expired"
        if remaining_minutes <= 30:
            return "critical"
        if remaining_minutes <= 120:
            return "warning"
        return "normal"

    @staticmethod
    def _group_logs_by_task(logs: List[TaskActionLog]) -> Dict[int, List[TaskActionLog]]:
        """根据任务 ID 分组日志。

        :param logs: 日志列表
        :return: task_id -> 日志列表

        Time: O(N), Space: O(N)
        """

        result: Dict[int, List[TaskActionLog]] = {}
        for log in logs:
            result.setdefault(log.task_id, []).append(log)
        return result

    @staticmethod
    def _build_timeline_entry(
        task: Task,
        node_name: str | None,
        logs: Optional[List[TaskActionLog]],
        user_map: Dict[int, str],
    ) -> TimelineEntry:
        """构建流程轨迹节点。

        :param task: 任务实例
        :param node_name: 节点名称
        :param logs: 操作日志
        :param user_map: 用户名称映射
        :return: 轨迹节点

        Time: O(1), Space: O(1)
        """

        actions = TaskService._build_timeline_actions(logs, user_map)
        last_action = actions[-1] if actions else None

        remaining_minutes = TaskService._calc_remaining_minutes(task.due_at)

        return TimelineEntry(
            task_id=task.id,
            node_id=task.node_id,
            node_name=node_name,
            status=TaskStatus(task.status),
            action=task.action,
            actor_user_id=last_action.actor_user_id if last_action else None,
            actor_name=last_action.actor_name if last_action else None,
            started_at=task.created_at,
            completed_at=task.completed_at,
            due_at=task.due_at,
            remaining_sla_minutes=remaining_minutes,
            sla_level=TaskService._calc_sla_level(remaining_minutes),
            comment=last_action.comment if last_action else None,
            actions=actions,
        )

    @staticmethod
    def _extract_comment(detail: Dict[str, object]) -> str | None:
        """提取日志中的备注内容。

        :param detail: 日志详情
        :return: 备注

        Time: O(1), Space: O(1)
        """

        if not detail:
            return None
        if isinstance(detail, dict):
            comment = detail.get("comment")
            if isinstance(comment, str):
                return comment
        return None

    @staticmethod
    def _collect_actor_ids(logs: List[TaskActionLog]) -> Set[int]:
        """收集日志中的操作者 ID。

        :param logs: 日志列表
        :return: 用户 ID 集合

        Time: O(N), Space: O(N)
        """

        actor_ids: Set[int] = set()
        for log in logs:
            if log.actor_user_id:
                actor_ids.add(log.actor_user_id)
        return actor_ids

    @staticmethod
    def _map_user_names(user_ids: Set[int], db: Session) -> Dict[int, str]:
        """批量查询用户名称。

        :param user_ids: 用户 ID 集合
        :param db: 数据库会话
        :return: user_id -> 用户姓名

        Time: O(M), Space: O(M)  (M = 唯一用户数)
        """

        if not user_ids:
            return {}

        rows = db.query(User.id, User.name).filter(User.id.in_(user_ids)).all()
        return {row.id: row.name for row in rows}

    @staticmethod
    def _build_timeline_actions(
        logs: Optional[List[TaskActionLog]],
        user_map: Dict[int, str],
    ) -> List[TimelineAction]:
        """构建节点操作记录列表。

        :param logs: 节点相关的日志
        :param user_map: 用户名称映射
        :return: 操作记录列表

        Time: O(K), Space: O(K)  (K = 日志条数)
        """

        if not logs:
            return []

        actions: List[TimelineAction] = []
        for log in logs:
            detail = log.detail_json or {}
            actions.append(
                TimelineAction(
                    action=log.action,
                    actor_user_id=log.actor_user_id,
                    actor_name=user_map.get(log.actor_user_id) if log.actor_user_id else None,
                    comment=TaskService._extract_comment(detail),
                    created_at=log.created_at,
                    detail=detail,
                )
            )

        return actions

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
