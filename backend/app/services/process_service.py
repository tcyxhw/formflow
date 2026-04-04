"""
模块用途: 流程实例服务
依赖配置: 无
数据流向: Submission -> ProcessService -> Task/ProcessInstance
函数清单:
    - ProcessService.start_process(): 创建流程实例及首个任务
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.models.form import Form, Submission
from app.models.workflow import (
    FlowDefinition,
    FlowNode,
    FlowRoute,
    ProcessInstance,
    Task,
    TaskActionLog,
)
from app.services.assignment_service import AssignmentService
from app.services.parallel_runtime_service import ParallelRuntimeService
from app.services.route_evaluator import RouteEvaluator, RouteCondition
from app.services.sla_service import SLAService
from app.schemas.submission_schemas import SubmissionStatus
from app.utils.audit import create_audit_log_sync
from pydantic import ValidationError


SYSTEM_USER_ID = 0
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AutoActionDecision:
    """自动审批决策结果。"""

    outcome: Optional[str]
    matched_condition: Optional[str] = None
    condition_payload: Optional[Dict[str, Any]] = None
    validation_error: Optional[str] = None


class ProcessService:
    """流程实例相关服务。"""

    @staticmethod
    def start_process(
        form_id: int,
        form_version_id: int,
        submission_id: int,
        tenant_id: int,
        db: Session,
    ) -> ProcessInstance:
        """创建流程实例并派发首个任务。

        :raises BusinessError: 流程定义缺失时抛出

        Time: O(1), Space: O(1)
        """

        # 首先获取表单，检查是否有关联的流程定义
        form = db.query(Form).filter(
            Form.id == form_id,
            Form.tenant_id == tenant_id,
        ).first()

        if not form:
            raise BusinessError("表单不存在")

        # 优先使用表单关联的流程定义
        if form.flow_definition_id:
            flow_def = db.query(FlowDefinition).filter(
                FlowDefinition.id == form.flow_definition_id,
                FlowDefinition.tenant_id == tenant_id,
            ).first()
        else:
            # 如果没有关联，查询该表单的所有流程定义，取版本最高的
            flow_def = (
                db.query(FlowDefinition)
                .filter(
                    FlowDefinition.form_id == form_id,
                    FlowDefinition.tenant_id == tenant_id,
                )
                .order_by(FlowDefinition.version.desc())
                .first()
            )
        if not flow_def:
            raise BusinessError("流程尚未配置")

        start_node = (
            db.query(FlowNode)
            .filter(
                FlowNode.flow_definition_id == flow_def.id,
                FlowNode.type == "user",
            )
            .order_by(FlowNode.id.asc())
            .first()
        )
        if not start_node:
            raise BusinessError("流程缺少可执行节点")

        # 获取提交记录，获取发起人ID和表单数据
        submission = db.query(Submission).filter(
            Submission.id == submission_id,
            Submission.tenant_id == tenant_id,
        ).first()
        
        initiator_id = submission.submitter_user_id if submission else None
        form_data = submission.data_jsonb if submission else None

        process = ProcessInstance(
            tenant_id=tenant_id,
            form_id=form_id,
            form_version_id=form_version_id,
            submission_id=submission_id,
            flow_definition_id=flow_def.id,
            initiator_id=initiator_id,
            form_data_snapshot=form_data,
        )
        db.add(process)
        db.flush()

        ProcessService._create_task_for_node(
            process, start_node, tenant_id, db, initiator_id=initiator_id
        )
        db.flush()
        db.refresh(process)
        return process

    @staticmethod
    def advance_from_node(
        process: ProcessInstance,
        from_node: FlowNode,
        tenant_id: int,
        db: Session,
        context: Optional[Dict[str, object]] = None,
    ) -> List[Task]:
        """根据路由规则生成下一批任务。

        :param process: 当前流程实例
        :param from_node: 已完成的节点
        :param tenant_id: 租户 ID
        :param db: 数据库会话
        :param context: 路由需要的上下文（表单/任务数据）
        :return: 新生成的任务列表

        Time: O(N), Space: O(N)
        """

        context = context or {}

        if from_node and not ParallelRuntimeService.handle_branch_arrival(
            process_instance_id=process.id,
            tenant_id=tenant_id,
            node_id=from_node.id,
            db=db,
        ):
            return []

        next_nodes = ProcessService._resolve_next_nodes(
            flow_definition_id=process.flow_definition_id,
            from_node=from_node,
            tenant_id=tenant_id,
            db=db,
            context=context,
        )

        if not next_nodes:
            process.state = "finished"
            ProcessService._update_submission_status(
                process=process,
                status=SubmissionStatus.APPROVED.value,
                db=db,
            )
            return []

        visited: Set[int] = set()
        new_tasks = ProcessService._dispatch_nodes(
            process=process,
            candidate_nodes=next_nodes,
            tenant_id=tenant_id,
            db=db,
            context=context,
            visited=visited,
            origin_node=from_node,
        )

        if not new_tasks and process.state not in {"finished", "canceled"}:
            process.state = "finished"
            ProcessService._update_submission_status(
                process=process,
                status=SubmissionStatus.APPROVED.value,
                db=db,
            )
        return new_tasks

    @staticmethod
    def _dispatch_nodes(
        process: ProcessInstance,
        candidate_nodes: List[FlowNode],
        tenant_id: int,
        db: Session,
        context: Dict[str, object],
        visited: Set[int],
        origin_node: Optional[FlowNode] = None,
    ) -> List[Task]:
        """按照节点类型生成任务或继续路由。

        Time: O(M), Space: O(M)
        """

        tasks: List[Task] = []

        if (
            origin_node
            and origin_node.route_mode == "parallel"
            and len(candidate_nodes) > 1
        ):
            join_policy, required = ProcessService._extract_parallel_join_config(origin_node)
            ParallelRuntimeService.record_parallel_fork(
                process_instance_id=process.id,
                fork_node_id=origin_node.id,
                tenant_id=tenant_id,
                opened_nodes=[node.id for node in candidate_nodes],
                db=db,
                join_policy=join_policy,
                n_required=required,
            )

        for node in candidate_nodes:
            if node.id in visited:
                continue
            visited.add(node.id)

            if node.type == "end":
                if process.state != "canceled":
                    process.state = "finished"
                    ProcessService._update_submission_status(
                        process=process,
                        status=SubmissionStatus.APPROVED.value,
                        db=db,
                    )
                continue

            if node.type == "auto":
                auto_next = ProcessService._resolve_next_nodes(
                    flow_definition_id=process.flow_definition_id,
                    from_node=node,
                    tenant_id=tenant_id,
                    db=db,
                    context=context,
                )
                tasks.extend(
                    ProcessService._dispatch_nodes(
                        process=process,
                        candidate_nodes=auto_next,
                        tenant_id=tenant_id,
                        db=db,
                        context=context,
                        visited=visited,
                        origin_node=node,
                    )
                )
                continue

            if node.type != "user":
                # 其他类型暂不生成任务，直接跳过
                continue

            requires_manual = ProcessService._should_sample_for_manual_review(process, node)
            auto_decision = AutoActionDecision(outcome=None)
            if not requires_manual:
                auto_decision = ProcessService._evaluate_auto_action(node, context)

            if auto_decision.outcome:
                auto_task = ProcessService._create_task_for_node(process, node, tenant_id, db)
                detail = ProcessService._build_auto_action_log_detail(
                    node=node,
                    decision=auto_decision,
                    context=context,
                    sampled=requires_manual,
                )
                ProcessService._complete_task_automatically(
                    task=auto_task,
                    action=auto_decision.outcome,
                    detail=detail,
                    db=db,
                )
                ProcessService.handle_task_completion(
                    task=auto_task,
                    tenant_id=tenant_id,
                    db=db,
                    context={"auto_action": auto_decision.outcome, **context},
                )
                continue

            tasks.append(ProcessService._create_task_for_node(process, node, tenant_id, db))

        return tasks

    @staticmethod
    def _resolve_next_nodes(
        flow_definition_id: int,
        from_node: FlowNode,
        tenant_id: int,
        db: Session,
        context: Dict[str, object],
    ) -> List[FlowNode]:
        """根据路由规则筛选下一节点列表。"""

        routes = (
            db.query(FlowRoute, FlowNode)
            .join(FlowNode, FlowNode.id == FlowRoute.to_node_id)
            .filter(
                FlowRoute.flow_definition_id == flow_definition_id,
                FlowRoute.from_node_id == from_node.id,
                FlowRoute.tenant_id == tenant_id,
                FlowRoute.enabled.is_(True),
            )
            .order_by(FlowRoute.priority.asc())
            .all()
        )

        matched_nodes: List[FlowNode] = []
        default_nodes: List[FlowNode] = []

        for route, target_node in routes:
            if route.is_default:
                default_nodes.append(target_node)

            if RouteEvaluator.evaluate(route.condition_json, context):
                matched_nodes.append(target_node)
                if from_node.route_mode != "parallel":
                    break

        if matched_nodes:
            return matched_nodes

        if default_nodes:
            return default_nodes if from_node.route_mode == "parallel" else default_nodes[:1]

        if from_node.next_default_node_id:
            fallback = (
                db.query(FlowNode)
                .filter(
                    FlowNode.id == from_node.next_default_node_id,
                    FlowNode.tenant_id == tenant_id,
                )
                .first()
            )
            if fallback:
                return [fallback]

        return []

    @staticmethod
    def _compare_numbers(
        actual: object,
        expected: object,
        comparator,
    ) -> bool:
        """对数值进行防御性比较。"""

        try:
            actual_num = float(actual)
            expected_num = float(expected)
        except (TypeError, ValueError):
            return False
        return comparator(actual_num, expected_num)

    @staticmethod
    def _create_task_for_node(
        process: ProcessInstance,
        node: FlowNode,
        tenant_id: int,
        db: Session,
        form_data: Optional[Dict[str, Any]] = None,
        initiator_id: Optional[int] = None,
    ) -> Task:
        """创建节点任务。

        :param process: 流程实例
        :param node: 流程节点
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :param form_data: 表单数据（用于FORM_FIELD类型）
        :param initiator_id: 发起人ID（用于DEPARTMENT_POST类型）
        :return: 创建的任务

        Time: O(1), Space: O(1)
        """
        # 从process获取表单数据（如果未提供）
        if form_data is None and process.form_data_snapshot:
            form_data = process.form_data_snapshot

        # 从process获取发起人ID（如果未提供）
        if initiator_id is None:
            initiator_id = getattr(process, 'initiator_id', None)
            # 如果 initiator_id 仍为 None，则从 submission 获取
            if initiator_id is None and process.submission_id:
                from app.models.form import Submission
                submission = db.query(Submission).filter(
                    Submission.id == process.submission_id,
                    Submission.tenant_id == tenant_id,
                ).first()
                if submission:
                    initiator_id = submission.submitter_user_id

        assignee_user_id, assignee_group_id = AssignmentService.select_assignee(
            node, tenant_id, db, form_data=form_data, initiator_id=initiator_id
        )
        
        # 如果节点配置了自动审批时自动认领，则创建任务时直接认领
        claimed_by = None
        if node.auto_claim_on_auto_action:
            claimed_by = SYSTEM_USER_ID
        
        task = Task(
            tenant_id=tenant_id,
            process_instance_id=process.id,
            node_id=node.id,
            assignee_user_id=assignee_user_id,
            assignee_group_id=assignee_group_id,
            due_at=SLAService.calculate_due_at(node.sla_hours),
            claimed_by=claimed_by,
            claimed_at=datetime.utcnow() if claimed_by else None,
            status="claimed" if claimed_by else "open",
        )
        db.add(task)
        return task

    @staticmethod
    def handle_task_completion(
        task: Task,
        tenant_id: int,
        db: Session,
        context: Optional[Dict[str, object]] = None,
    ) -> None:
        """在任务完成后根据审批策略决定是否推进流程。

        Time: O(N), Space: O(N)
        """

        node = (
            db.query(FlowNode)
            .filter(
                FlowNode.id == task.node_id,
                FlowNode.tenant_id == tenant_id,
            )
            .first()
        )
        if not node:
            return

        process = (
            db.query(ProcessInstance)
            .filter(
                ProcessInstance.id == task.process_instance_id,
                ProcessInstance.tenant_id == tenant_id,
            )
            .with_for_update(of=ProcessInstance)
            .first()
        )
        if not process or process.state != "running":
            return

        decision = ProcessService._evaluate_approve_policy(
            node=node,
            process=process,
            tenant_id=tenant_id,
            db=db,
        )

        if decision == "pending":
            return

        if decision == "reject":
            ProcessService._handle_rejection(
                task=task,
                node=node,
                process=process,
                tenant_id=tenant_id,
                db=db,
                context=context,
            )
            return

        ProcessService._cancel_pending_node_tasks(process.id, node.id, tenant_id, db)
        ProcessService.advance_from_node(
            process=process,
            from_node=node,
            tenant_id=tenant_id,
            db=db,
            context=context,
        )

    @staticmethod
    def _evaluate_approve_policy(
        node: FlowNode,
        process: ProcessInstance,
        tenant_id: int,
        db: Session,
    ) -> str:
        """基于节点策略判定节点是否可以向下推进。"""

        tasks = (
            db.query(Task)
            .filter(
                Task.process_instance_id == process.id,
                Task.node_id == node.id,
                Task.tenant_id == tenant_id,
            )
            .all()
        )

        completed = [t for t in tasks if t.status == "completed"]
        approvals = [t for t in completed if (t.action or "").lower() == "approve"]
        rejections = [t for t in completed if (t.action or "").lower() == "reject"]

        if rejections:
            return "reject"

        policy = (node.approve_policy or "any").lower()
        if policy == "all":
            if len(completed) == len(tasks) and completed:
                return "approve"
            return "pending"

        if policy == "percent":
            threshold = ProcessService._resolve_percent_threshold(node)
            if not tasks:
                return "pending"
            required = max(1, round(len(tasks) * threshold / 100))
            if len(completed) < len(tasks):
                return "pending"
            return "approve" if len(approvals) >= required else "reject"

        # 默认 any: 任一通过即可
        if approvals:
            return "approve"
        return "pending"

    @staticmethod
    def _resolve_percent_threshold(node: FlowNode) -> int:
        """解析 percent 策略阈值，优先使用节点显式配置。

        优先读取 ``approve_threshold`` 字段，便于与前端 NodeConfig 保持 1:1 对齐；
        若为空则回退到历史兼容字段 ``assignee_value.percent_threshold``。

        Time: O(1), Space: O(1)
        """

        # 优先使用显式字段，避免依赖嵌套 JSON 结构
        if getattr(node, "approve_threshold", None) is not None:
            try:
                value = int(node.approve_threshold)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                value = 100
            return max(1, min(100, value))

        # 兼容旧数据：从 assignee_value.percent_threshold 中读取
        config = node.assignee_value if isinstance(node.assignee_value, dict) else {}
        raw = config.get("percent_threshold", 100)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = 100
        return max(1, min(100, value))

    @staticmethod
    def _cancel_pending_node_tasks(
        process_id: int,
        node_id: int,
        tenant_id: int,
        db: Session,
        exclude_completed: bool = True,
    ) -> None:
        """取消节点下剩余未完成任务，避免重复处理。"""

        query = (
            db.query(Task)
            .filter(
                Task.process_instance_id == process_id,
                Task.node_id == node_id,
                Task.tenant_id == tenant_id,
            )
        )
        if exclude_completed:
            query = query.filter(Task.status != "completed")

        for pending in query.all():
            pending.status = "canceled"

    @staticmethod
    def _evaluate_auto_action(node: FlowNode, context: Optional[Dict[str, object]]) -> AutoActionDecision:
        """评估节点的自动审批配置。"""

        if not node.auto_approve_enabled:
            return AutoActionDecision(outcome=None)

        ctx = context or {}
        for field_name, decision in (
            ("auto_reject_cond", "reject"),
            ("auto_approve_cond", "approve"),
        ):
            condition_data: Optional[Dict[str, Any]] = getattr(node, field_name)
            if not condition_data:
                continue

            is_valid, error_msg = ProcessService._validate_route_condition(condition_data)
            if not is_valid:
                logger.warning(
                    "自动审批条件解析失败",
                    extra={
                        "node_id": node.id,
                        "field": field_name,
                        "error": error_msg,
                    },
                )
                return AutoActionDecision(
                    outcome=None,
                    matched_condition=field_name,
                    condition_payload=condition_data,
                    validation_error=error_msg,
                )

            if RouteEvaluator.evaluate(condition_data, ctx):
                return AutoActionDecision(
                    outcome=decision,
                    matched_condition=field_name,
                    condition_payload=condition_data,
                )

        return AutoActionDecision(outcome=None)

    @staticmethod
    def _complete_task_automatically(
        task: Task,
        action: str,
        detail: Optional[Dict[str, Any]],
        db: Session,
    ) -> None:
        """以系统身份完成任务并记录审计。"""

        task.status = "completed"
        task.action = action
        task.completed_by = SYSTEM_USER_ID
        task.completed_at = datetime.utcnow()
        log = TaskActionLog(
            task_id=task.id,
            actor_user_id=SYSTEM_USER_ID,
            action=f"auto_{action}",
            detail_json=detail or {"message": "系统自动决策"},
        )
        db.add(log)
        create_audit_log_sync(
            action=f"auto_{action}",
            resource_type="task",
            resource_id=task.id,
            after_data=detail,
            tenant_id=task.tenant_id,
            actor_user_id=SYSTEM_USER_ID,
            db=db,
        )

    @staticmethod
    def _should_sample_for_manual_review(process: ProcessInstance, node: FlowNode) -> bool:
        """根据节点抽检比例决定是否跳过自动审批。

        :return: True 表示需要人工处理

        Time: O(1), Space: O(1)
        """

        ratio = node.auto_sample_ratio or 0
        try:
            ratio_value = float(ratio)
        except (TypeError, ValueError):
            ratio_value = 0.0

        if ratio_value <= 0:
            return False
        if ratio_value >= 1:
            return True

        seed = f"{process.id}:{node.id}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        sample = int(digest[:8], 16) / 0xFFFFFFFF
        return sample < ratio_value

    @staticmethod
    def _validate_route_condition(condition_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """验证路由条件结构是否符合契约。"""

        try:
            RouteCondition.model_validate(condition_data)
        except ValidationError as exc:
            return False, str(exc)
        return True, None

    @staticmethod
    def _build_auto_action_log_detail(
        node: FlowNode,
        decision: AutoActionDecision,
        context: Dict[str, object],
        sampled: bool,
    ) -> Dict[str, Any]:
        """构造自动审批日志详情。"""

        return {
            "message": "系统自动决策",
            "node_id": node.id,
            "node_name": node.name,
            "decision": decision.outcome,
            "matched_condition": decision.matched_condition,
            "condition_payload": decision.condition_payload,
            "validation_error": decision.validation_error,
            "sampled": sampled,
            "context_snapshot": ProcessService._sanitize_context_for_log(context),
        }

    @staticmethod
    def _sanitize_context_for_log(context: Dict[str, object], max_items: int = 6) -> Dict[str, Any]:
        """提取可审计的上下文，限制字段数量与长度。"""

        if not context:
            return {}

        snapshot: Dict[str, Any] = {}
        for idx, (key, value) in enumerate(context.items()):
            if idx >= max_items:
                break
            if isinstance(value, (str, int, float, bool)) or value is None:
                snapshot[key] = value
                continue
            snapshot[key] = str(value)[:200]
        return snapshot

    @staticmethod
    def _update_submission_status(process: ProcessInstance, status: str, db: Session) -> None:
        """同步流程状态到提交记录。

        Time: O(1), Space: O(1)
        """

        submission = (
            db.query(Submission)
            .filter(
                Submission.id == process.submission_id,
                Submission.tenant_id == process.tenant_id,
            )
            .first()
        )
        if not submission:
            return
        submission.status = status

    @staticmethod
    def _extract_parallel_join_config(node: FlowNode) -> Tuple[str, Optional[int]]:
        """解析并行节点的合流策略配置。"""

        config: Dict[str, object] = {}
        if isinstance(node.assignee_value, dict):
            config = node.assignee_value

        join_policy = str(config.get("join_policy", "all")).lower()
        if join_policy not in {"all", "any", "n_of_m", "n_of", "n"}:
            join_policy = "all"

        n_required_raw = config.get("n_required")
        try:
            required = int(n_required_raw) if n_required_raw is not None else None
        except (TypeError, ValueError):
            required = None

        return join_policy, required

    @staticmethod
    def _handle_rejection(
        task: Task,
        node: FlowNode,
        process: ProcessInstance,
        tenant_id: int,
        db: Session,
        context: Optional[Dict[str, object]] = None,
    ) -> None:
        """处理驳回逻辑，根据节点的reject_strategy决定驳回策略。

        :param task: 当前任务
        :param node: 当前节点
        :param process: 流程实例
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :param context: 上下文信息

        Time: O(N), Space: O(N)
        """
        # 获取节点的驳回策略，默认为TO_START
        reject_strategy = getattr(node, 'reject_strategy', None) or 'TO_START'

        if reject_strategy == 'TO_START':
            # 驳回到发起人，流程结束
            process.state = "canceled"
            ProcessService._cancel_pending_node_tasks(
                process.id, node.id, tenant_id, db, exclude_completed=False
            )
            ProcessService._update_submission_status(
                process=process,
                status=SubmissionStatus.REJECTED.value,
                db=db,
            )
            logger.info(
                f"流程驳回到发起人，流程结束",
                extra={
                    "process_id": process.id,
                    "node_id": node.id,
                    "task_id": task.id,
                },
            )

        elif reject_strategy == 'TO_PREVIOUS':
            # 驳回到上一个审批节点
            previous_node = ProcessService._find_previous_approval_node(
                process.id, node.id, tenant_id, db
            )

            if previous_node:
                # 取消当前节点的所有待处理任务
                ProcessService._cancel_pending_node_tasks(
                    process.id, node.id, tenant_id, db, exclude_completed=False
                )
                # 重新创建上一个节点的任务
                new_task = ProcessService._create_task_for_node(
                    process, previous_node, tenant_id, db
                )
                logger.info(
                    f"流程驳回到上一个节点",
                    extra={
                        "process_id": process.id,
                        "current_node_id": node.id,
                        "previous_node_id": previous_node.id,
                        "new_task_id": new_task.id if new_task else None,
                    },
                )
            else:
                # 没有上一个节点，退回到发起人（流程结束）
                process.state = "canceled"
                ProcessService._cancel_pending_node_tasks(
                    process.id, node.id, tenant_id, db, exclude_completed=False
                )
                ProcessService._update_submission_status(
                    process=process,
                    status=SubmissionStatus.REJECTED.value,
                    db=db,
                )
                logger.info(
                    f"无上一个节点，流程驳回到发起人并结束",
                    extra={
                        "process_id": process.id,
                        "node_id": node.id,
                    },
                )
        else:
            # 未知的驳回策略，默认按TO_START处理
            logger.warning(
                f"未知的驳回策略: {reject_strategy}，按TO_START处理",
                extra={
                    "process_id": process.id,
                    "node_id": node.id,
                    "reject_strategy": reject_strategy,
                },
            )
            process.state = "canceled"
            ProcessService._cancel_pending_node_tasks(
                process.id, node.id, tenant_id, db, exclude_completed=False
            )
            ProcessService._update_submission_status(
                process=process,
                status=SubmissionStatus.REJECTED.value,
                db=db,
            )

    @staticmethod
    def _find_previous_approval_node(
        process_id: int,
        current_node_id: int,
        tenant_id: int,
        db: Session,
    ) -> Optional[FlowNode]:
        """查找上一个审批节点。

        :param process_id: 流程实例ID
        :param current_node_id: 当前节点ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 上一个审批节点，如果没有则返回None

        Time: O(N), Space: O(1)
        """
        # 查询当前流程中已完成的任务，排除当前节点，按完成时间倒序
        completed_task = (
            db.query(Task)
            .filter(
                Task.process_instance_id == process_id,
                Task.status == "completed",
                Task.node_id != current_node_id,
                Task.tenant_id == tenant_id,
            )
            .order_by(Task.completed_at.desc())
            .first()
        )

        if completed_task:
            # 获取上一个节点
            previous_node = (
                db.query(FlowNode)
                .filter(FlowNode.id == completed_task.node_id)
                .first()
            )
            return previous_node

        return None
