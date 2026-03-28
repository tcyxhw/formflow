"""
模块用途: 审批任务智能指派服务
依赖配置: 无
数据流向: FlowNode 配置 -> AssignmentService -> Task.assignee 信息
函数清单:
    - AssignmentService.select_assignee(): 计算任务指派人
    - AssignmentService._pick_best_user_intelligent(): 智能选择最佳用户
    - AssignmentService._calculate_user_score(): 计算用户综合评分
    - AssignmentService._fetch_user_statistics(): 获取用户历史统计
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.models.user import (
    User,
    UserPosition,
    UserRole,
)
from app.models.workflow import Task, FlowNode, TaskActionLog

PENDING_STATUSES = ("open", "claimed")
logger = logging.getLogger(__name__)


@dataclass
class UserScore:
    """用户分配评分结果"""

    user_id: int
    load_score: float          # 负载得分 0-100
    efficiency_score: float    # 效率得分 0-100
    quality_score: float       # 质量得分 0-100
    total_score: float         # 总得分 0-100

    # 权重配置（可配置化）
    LOAD_WEIGHT = 0.4
    EFFICIENCY_WEIGHT = 0.4
    QUALITY_WEIGHT = 0.2


class AssignmentService:
    """审批节点指派策略集合。"""

    @staticmethod
    def select_assignee(
        node: FlowNode,
        tenant_id: int,
        db: Session,
        form_data: Optional[Dict[str, Any]] = None,
        initiator_id: Optional[int] = None,
    ) -> Tuple[Optional[int], Optional[int]]:
        """根据节点配置与实时负载确定指派对象。

        :param node: 当前流程节点
        :param tenant_id: 租户 ID
        :param db: 会话
        :param form_data: 表单数据（用于FORM_FIELD类型）
        :param initiator_id: 发起人ID（用于DEPARTMENT_POST类型）
        :return: (assignee_user_id, assignee_group_id)

        Time: O(N), Space: O(1)
        """

        if not node.assignee_type:
            return None, None

        if node.assignee_type == "user":
            user_id = AssignmentService._pick_best_user_intelligent(node.assignee_value or {}, tenant_id, db)
            return user_id, None

        if node.assignee_type == "group":
            return None, AssignmentService._pick_group(node.assignee_value)

        if node.assignee_type == "role":
            user_id = AssignmentService._pick_user_by_role(node.assignee_value, tenant_id, db)
            return user_id, None

        if node.assignee_type == "department":
            user_id = AssignmentService._pick_user_by_department(node.assignee_value, tenant_id, db)
            return user_id, None

        if node.assignee_type == "position":
            user_id = AssignmentService._pick_user_by_position(node.assignee_value, tenant_id, db)
            return user_id, None

        if node.assignee_type == "expr":
            return AssignmentService._evaluate_expression(node.assignee_value or {}, tenant_id, db)

        if node.assignee_type == "form_field":
            return AssignmentService._pick_user_by_form_field(
                node.assignee_value, form_data or {}, tenant_id, db
            )

        if node.assignee_type == "department_post":
            return AssignmentService._pick_user_by_department_post(
                node.assignee_value, initiator_id, tenant_id, db
            )

        raise BusinessError(f"未知的指派类型: {node.assignee_type}")

    @staticmethod
    def _pick_best_user(config: dict, tenant_id: int, db: Session) -> Optional[int]:
        """在候选用户中选择当前负载最轻者。

        Time: O(N), Space: O(N)
        """

        user_ids = config.get("user_ids") or []
        if not user_ids:
            single_id = config.get("user_id")
            return single_id

        pending_map = AssignmentService._fetch_pending_workloads(user_ids, tenant_id, db)
        sorted_candidates = sorted(user_ids, key=lambda uid: (pending_map.get(uid, 0), uid))
        return sorted_candidates[0] if sorted_candidates else None

    @staticmethod
    def _pick_group(config: Optional[dict]) -> Optional[int]:
        """返回配置的小组 ID。"""

        if not config:
            return None
        return config.get("group_id")

    @staticmethod
    def _pick_user_by_role(config: Optional[dict], tenant_id: int, db: Session) -> Optional[int]:
        """根据角色获取候选列表（使用智能分配）。"""

        if not config or not config.get("role_id"):
            return None

        rows = (
            db.query(UserRole.user_id)
            .filter(
                UserRole.tenant_id == tenant_id,
                UserRole.role_id == config["role_id"],
            )
            .all()
        )
        user_ids = [row.user_id for row in rows]
        return AssignmentService._pick_best_user_intelligent({"user_ids": user_ids}, tenant_id, db)

    @staticmethod
    def _pick_user_by_department(config: Optional[dict], tenant_id: int, db: Session) -> Optional[int]:
        """限定部门挑选成员（使用智能分配）。"""

        if not config or not config.get("department_id"):
            return None

        rows = (
            db.query(User.id)
            .filter(
                User.tenant_id == tenant_id,
                User.department_id == config["department_id"],
                User.is_active.is_(True),
            )
            .all()
        )
        user_ids = [row.id for row in rows]
        return AssignmentService._pick_best_user_intelligent({"user_ids": user_ids}, tenant_id, db)

    @staticmethod
    def _pick_user_by_position(config: Optional[dict], tenant_id: int, db: Session) -> Optional[int]:
        """结合岗位生效期筛选候选人（使用智能分配）。"""

        if not config or not config.get("position_id"):
            return None

        now = datetime.utcnow()
        rows = (
            db.query(UserPosition.user_id)
            .filter(
                UserPosition.tenant_id == tenant_id,
                UserPosition.position_id == config["position_id"],
                (UserPosition.effective_from.is_(None) | (UserPosition.effective_from <= now)),
                (UserPosition.effective_to.is_(None) | (UserPosition.effective_to >= now)),
            )
            .all()
        )
        user_ids = [row.user_id for row in rows]
        return AssignmentService._pick_best_user_intelligent({"user_ids": user_ids}, tenant_id, db)

    @staticmethod
    def _evaluate_expression(config: dict, tenant_id: int, db: Session) -> Tuple[Optional[int], Optional[int]]:
        """解析自定义表达式，目前支持 user/group 直指（使用智能分配）。"""

        if config.get("group_id"):
            return None, config["group_id"]
        if config.get("user_id"):
            return config["user_id"], None
        user_id = AssignmentService._pick_best_user_intelligent(config, tenant_id, db)
        return user_id, None

    @staticmethod
    def _fetch_pending_workloads(user_ids: List[int], tenant_id: int, db: Session) -> Dict[int, int]:
        """统计用户未完成任务数量，用于衡量负载。

        Time: O(N), Space: O(N)
        """

        if not user_ids:
            return {}

        rows = (
            db.query(Task.assignee_user_id, func.count(Task.id))
            .filter(
                Task.tenant_id == tenant_id,
                Task.assignee_user_id.in_(user_ids),
                Task.status.in_(PENDING_STATUSES),
            )
            .group_by(Task.assignee_user_id)
            .all()
        )
        return {row[0]: int(row[1]) for row in rows}

    @staticmethod
    def _fetch_user_statistics(
        user_ids: List[int],
        tenant_id: int,
        db: Session,
        days: int = 30,
    ) -> Dict[int, Dict[str, Any]]:
        """批量获取用户历史统计信息。

        统计维度：
        - avg_completion_hours: 平均完成时长（小时）
        - completion_count: 完成任务数
        - approve_count: 通过数量
        - reject_count: 驳回数量
        - approve_ratio: 通过比例

        :param user_ids: 用户ID列表
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :param days: 统计天数（默认30天）
        :return: {user_id: {统计字段}}

        Time: O(N), Space: O(N)
        """

        if not user_ids:
            return {}

        # 计算时间范围
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 查询每个用户的平均完成时长（从任务创建到完成）
        completion_stats = (
            db.query(
                Task.assignee_user_id,
                func.count(Task.id).label("completion_count"),
                func.avg(
                    func.extract('epoch', Task.completed_at - Task.created_at) / 3600
                ).label("avg_completion_hours"),
            )
            .filter(
                Task.tenant_id == tenant_id,
                Task.assignee_user_id.in_(user_ids),
                Task.status == "completed",
                Task.completed_at >= cutoff_date,
            )
            .group_by(Task.assignee_user_id)
            .all()
        )

        # 查询每个用户的审批动作统计（通过/驳回）
        action_stats = (
            db.query(
                TaskActionLog.actor_user_id,
                TaskActionLog.action,
                func.count(TaskActionLog.id).label("action_count"),
            )
            .filter(
                TaskActionLog.tenant_id == tenant_id,
                TaskActionLog.actor_user_id.in_(user_ids),
                TaskActionLog.created_at >= cutoff_date,
                TaskActionLog.action.in_(["approve", "reject"]),
            )
            .group_by(TaskActionLog.actor_user_id, TaskActionLog.action)
            .all()
        )

        # 组装统计结果
        stats_map: Dict[int, Dict[str, Any]] = {}

        # 处理完成统计
        for row in completion_stats:
            user_id = row[0]
            stats_map[user_id] = {
                "completion_count": row[1],
                "avg_completion_hours": float(row[2]) if row[2] else 0.0,
            }

        # 处理动作统计
        action_map: Dict[int, Dict[str, int]] = {}
        for row in action_stats:
            user_id = row[0]
            action = row[1]
            count = row[2]
            if user_id not in action_map:
                action_map[user_id] = {}
            action_map[user_id][action] = count

        # 合并数据
        for user_id in user_ids:
            if user_id not in stats_map:
                stats_map[user_id] = {}

            # 计算通过比例
            user_actions = action_map.get(user_id, {})
            approve_count = user_actions.get("approve", 0)
            reject_count = user_actions.get("reject", 0)
            total_actions = approve_count + reject_count

            stats_map[user_id]["approve_count"] = approve_count
            stats_map[user_id]["reject_count"] = reject_count
            stats_map[user_id]["approve_ratio"] = (
                approve_count / total_actions if total_actions > 0 else 0.0
            )

        return stats_map

    @staticmethod
    def _calculate_user_score(
        user_id: int,
        pending_count: int,
        stats: Dict[str, Any],
    ) -> UserScore:
        """计算用户分配得分。

        评分逻辑：
        1. 负载得分 (40%):
           - 公式: 100 - min(待办数 × 10, 100)
           - 解释: 0个待办=100分，10个待办=0分，线性递减

        2. 效率得分 (40%):
           - 公式: 100 - min(平均完成小时数 × 2, 100)
           - 解释: 0小时=100分，50小时=0分，线性递减
           - 边界: 无历史数据时默认50分

        3. 质量得分 (20%):
           - 公式: 通过率 × 100
           - 解释: 100%通过=100分
           - 边界: 无历史数据时默认80分

        4. 总得分:
           - 公式: 负载×0.4 + 效率×0.4 + 质量×0.2

        :param user_id: 用户ID
        :param pending_count: 当前待办任务数
        :param stats: 历史统计数据
        :return: 用户评分结果

        Time: O(1), Space: O(1)
        """

        # 1. 负载得分 (0个待办=100分，10个待办=0分)
        load_score = max(0.0, 100.0 - (pending_count * 10))

        # 2. 效率得分
        avg_hours = stats.get("avg_completion_hours", 0.0)
        if avg_hours > 0:
            # 0小时=100分，50小时=0分
            efficiency_score = max(0.0, 100.0 - (avg_hours * 2))
        else:
            # 无历史数据，默认50分
            efficiency_score = 50.0

        # 3. 质量得分
        approve_ratio = stats.get("approve_ratio", 0.0)
        if approve_ratio > 0 or stats.get("completion_count", 0) > 0:
            quality_score = approve_ratio * 100
        else:
            # 无历史数据，默认80分
            quality_score = 80.0

        # 4. 计算总得分
        total_score = (
            load_score * UserScore.LOAD_WEIGHT +
            efficiency_score * UserScore.EFFICIENCY_WEIGHT +
            quality_score * UserScore.QUALITY_WEIGHT
        )

        return UserScore(
            user_id=user_id,
            load_score=round(load_score, 2),
            efficiency_score=round(efficiency_score, 2),
            quality_score=round(quality_score, 2),
            total_score=round(total_score, 2),
        )

    @staticmethod
    def _pick_best_user_intelligent(
        config: dict,
        tenant_id: int,
        db: Session,
    ) -> Optional[int]:
        """智能选择最佳用户（基于综合评分）。

        流程：
        1. 从 config 获取候选用户列表
        2. 查询当前负载（pending tasks）
        3. 查询历史统计（30天）
        4. 为每个用户计算综合得分
        5. 返回得分最高的用户

        :param config: 配置信息，包含 user_ids 或 user_id
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 最佳用户ID

        Time: O(N), Space: O(N)
        """

        # 步骤1: 获取候选用户
        user_ids = config.get("user_ids") or []
        if not user_ids:
            single_id = config.get("user_id")
            return single_id

        if len(user_ids) == 1:
            return user_ids[0]

        # 步骤2: 查询当前负载
        pending_map = AssignmentService._fetch_pending_workloads(
            user_ids, tenant_id, db
        )

        # 步骤3: 查询历史统计（默认30天）
        stats_map = AssignmentService._fetch_user_statistics(
            user_ids, tenant_id, db, days=30
        )

        # 步骤4: 计算得分并排序
        scored_users: List[Tuple[int, float]] = []
        for user_id in user_ids:
            pending = pending_map.get(user_id, 0)
            stats = stats_map.get(user_id, {})
            score = AssignmentService._calculate_user_score(
                user_id, pending, stats
            )
            scored_users.append((user_id, score.total_score))

            # 记录日志（调试用）
            logger.debug(
                f"用户评分: user_id={user_id}, "
                f"pending={pending}, "
                f"score={score.total_score}, "
                f"(load={score.load_score}, eff={score.efficiency_score}, qual={score.quality_score})"
            )

        # 步骤5: 返回最高分用户（分数降序，相同则按id升序）
        scored_users.sort(key=lambda x: (-x[1], x[0]))
        best_user_id = scored_users[0][0] if scored_users else None

        if best_user_id:
            best_score = scored_users[0][1]
            logger.info(
                f"智能分配: 选中 user_id={best_user_id}, score={best_score}, "
                f"候选数={len(user_ids)}"
            )

        return best_user_id

    @staticmethod
    def _pick_user_by_form_field(
        config: Optional[dict],
        form_data: Dict[str, Any],
        tenant_id: int,
        db: Session,
    ) -> Tuple[Optional[int], Optional[int]]:
        """从表单字段取审批人。

        :param config: 配置信息，包含form_field_key
        :param form_data: 表单数据
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: (assignee_user_id, assignee_group_id)

        Time: O(1), Space: O(1)
        """
        if not config or not config.get("form_field_key"):
            raise BusinessError("表单字段审批人配置不完整")

        field_key = config["form_field_key"]
        field_value = form_data.get(field_key)

        if not field_value:
            raise BusinessError(f"表单字段 {field_key} 未填写审批人")

        # 支持单用户ID或用户ID列表
        if isinstance(field_value, list):
            user_ids = []
            for v in field_value:
                if v:
                    try:
                        user_ids.append(int(v))
                    except (TypeError, ValueError):
                        pass
        else:
            try:
                user_ids = [int(field_value)]
            except (TypeError, ValueError):
                raise BusinessError(f"表单字段 {field_key} 的值不是有效的用户ID")

        if not user_ids:
            raise BusinessError(f"表单字段 {field_key} 未提供有效的用户ID")

        # 如果只有一个用户，直接返回
        if len(user_ids) == 1:
            # 验证用户是否存在
            user = (
                db.query(User)
                .filter(
                    User.id == user_ids[0],
                    User.tenant_id == tenant_id,
                    User.is_active.is_(True),
                )
                .first()
            )
            if not user:
                raise BusinessError(f"用户ID {user_ids[0]} 不存在或已禁用")
            return user_ids[0], None

        # 多个用户时，使用智能分配
        user_id = AssignmentService._pick_best_user_intelligent(
            {"user_ids": user_ids}, tenant_id, db
        )
        return user_id, None

    @staticmethod
    def _pick_user_by_department_post(
        config: Optional[dict],
        initiator_id: Optional[int],
        tenant_id: int,
        db: Session,
    ) -> Tuple[Optional[int], Optional[int]]:
        """部门岗位匹配。

        :param config: 配置信息，包含match_mode、post_id、department_id(可选)
        :param initiator_id: 发起人ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: (assignee_user_id, assignee_group_id)

        Time: O(N), Space: O(N)
        """
        if not config:
            raise BusinessError("部门岗位配置不完整")

        match_mode = config.get("match_mode", "FIXED")
        post_id = config.get("post_id")

        if not post_id:
            raise BusinessError("缺少岗位配置")

        if match_mode == "FIXED":
            # 固定部门+岗位
            department_id = config.get("department_id")
            if not department_id:
                raise BusinessError("FIXED模式缺少部门配置")
            user_id = AssignmentService._find_users_by_dept_post(
                department_id, post_id, tenant_id, db
            )
            return user_id, None

        elif match_mode == "CURRENT":
            # 发起人当前部门
            if initiator_id is None:
                raise BusinessError("发起人ID未知，无法进行部门岗位匹配")
            dept_id = AssignmentService._get_user_department(initiator_id, tenant_id, db)
            if not dept_id:
                raise BusinessError(f"发起人(ID:{initiator_id})未设置部门，请先在用户管理中为该用户分配部门")
            user_id = AssignmentService._find_users_by_dept_post(
                dept_id, post_id, tenant_id, db
            )
            return user_id, None

        elif match_mode == "ORG_CHAIN_UP":
            # 沿部门链向上查找
            if initiator_id is None:
                raise BusinessError("发起人ID未知，无法进行部门岗位匹配")
            return AssignmentService._find_users_by_org_chain(
                initiator_id, post_id, tenant_id, db
            )

        else:
            raise BusinessError(f"未知的岗位匹配模式: {match_mode}")

    @staticmethod
    def _get_user_department(user_id: Optional[int], tenant_id: int, db: Session) -> Optional[int]:
        """获取用户的主属部门ID。

        优先从 UserDepartmentPost 表获取，如果没有则回退到 User.department_id。

        :param user_id: 用户ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 部门ID

        Time: O(1), Space: O(1)
        """
        from app.models.user import UserDepartmentPost

        if user_id is None:
            return None

        # 优先从 UserDepartmentPost 表获取
        user_dept_post = (
            db.query(UserDepartmentPost.department_id)
            .filter(
                UserDepartmentPost.user_id == user_id,
                UserDepartmentPost.tenant_id == tenant_id,
            )
            .first()
        )

        if user_dept_post:
            return user_dept_post[0]

        # 回退到 User.department_id
        user = (
            db.query(User)
            .filter(
                User.id == user_id,
                User.tenant_id == tenant_id,
            )
            .first()
        )
        return user.department_id if user else None

    @staticmethod
    def _find_users_by_dept_post(
        department_id: int,
        post_id: int,
        tenant_id: int,
        db: Session,
    ) -> Optional[int]:
        """根据部门和岗位查找用户。

        优先使用 UserDepartmentPost 表查询，如果没有结果则回退到 UserDepartment + UserPosition 联合查询。

        :param department_id: 部门ID
        :param post_id: 岗位ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 用户ID

        Time: O(N), Space: O(N)
        """
        from app.models.user import UserDepartmentPost, UserDepartment, UserPosition

        # 优先使用 UserDepartmentPost 表查询
        user_ids = (
            db.query(UserDepartmentPost.user_id)
            .filter(
                UserDepartmentPost.department_id == department_id,
                UserDepartmentPost.post_id == post_id,
                UserDepartmentPost.tenant_id == tenant_id,
            )
            .all()
        )

        if user_ids:
            user_id_list = [uid for (uid,) in user_ids]
            return AssignmentService._pick_best_user_intelligent(
                {"user_ids": user_id_list}, tenant_id, db
            )

        # 回退到 UserDepartment + UserPosition 联合查询
        user_dept = (
            db.query(UserDepartment.user_id)
            .filter(
                UserDepartment.department_id == department_id,
                UserDepartment.tenant_id == tenant_id,
            )
            .subquery()
        )

        user_pos = (
            db.query(UserPosition.user_id)
            .filter(
                UserPosition.position_id == post_id,
                UserPosition.tenant_id == tenant_id,
            )
            .subquery()
        )

        # 获取同时满足条件的用户
        user_ids = (
            db.query(user_dept.c.user_id)
            .join(user_pos, user_dept.c.user_id == user_pos.c.user_id)
            .all()
        )

        if not user_ids:
            return None

        # 使用智能分配选择最佳用户
        user_id_list = [uid for (uid,) in user_ids]
        return AssignmentService._pick_best_user_intelligent(
            {"user_ids": user_id_list}, tenant_id, db
        )

    @staticmethod
    def _find_users_by_org_chain(
        user_id: Optional[int],
        post_id: int,
        tenant_id: int,
        db: Session,
    ) -> Tuple[Optional[int], Optional[int]]:
        """沿发起人部门链向上查找岗位。

        按照plan1.md规则：
        1. 逐级向上查找
        2. 到根部门（is_root=true）时停止
        3. 使用user_department_post表查询

        :param user_id: 用户ID
        :param post_id: 岗位ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: (assignee_user_id, assignee_group_id)

        Time: O(depth), Space: O(1)
        """
        from app.models.user import UserDepartmentPost, Department
        
        # 使用 _get_user_department 获取用户的部门ID
        if user_id is None:
            raise BusinessError("用户ID未知，无法查找组织链")
        current_dept_id = AssignmentService._get_user_department(user_id, tenant_id, db)
        
        if not current_dept_id:
            raise BusinessError(f"用户(ID:{user_id})未设置部门，请先在用户管理中为该用户分配部门")
        
        # 逐级向上查找
        while True:
            # 查当前部门下有没有这个岗位的人
            result = (
                db.query(UserDepartmentPost.user_id)
                .filter(
                    UserDepartmentPost.department_id == current_dept_id,
                    UserDepartmentPost.post_id == post_id,
                    UserDepartmentPost.tenant_id == tenant_id,
                )
                .first()
            )
            
            if result:
                return result[0], None
            
            # 查上级部门
            current_dept = (
                db.query(Department)
                .filter(
                    Department.id == current_dept_id,
                    Department.tenant_id == tenant_id,
                )
                .first()
            )
            
            if not current_dept or not current_dept.parent_id:
                raise BusinessError("未找到该岗位人员")
            
            parent_dept = (
                db.query(Department)
                .filter(
                    Department.id == current_dept.parent_id,
                    Department.tenant_id == tenant_id,
                )
                .first()
            )
            
            if not parent_dept:
                raise BusinessError("未找到该岗位人员")
            
            # 到根部门了，不再往上（校级领导不参与自动上溯）
            if parent_dept.is_root:
                raise BusinessError("未找到该岗位人员")
            
            current_dept_id = parent_dept.id

    @staticmethod
    def _find_users_by_dept_post_single(
        department_id: int,
        post_id: int,
        tenant_id: int,
        db: Session,
    ) -> Optional[int]:
        """根据部门和岗位查找单个用户（简化版）。

        优先使用 UserDepartmentPost 表查询，如果没有结果则回退到 UserDepartment + UserPosition 联合查询。

        :param department_id: 部门ID
        :param post_id: 岗位ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 用户ID

        Time: O(N), Space: O(N)
        """
        from app.models.user import UserDepartmentPost, UserDepartment, UserPosition

        # 优先使用 UserDepartmentPost 表查询
        result = (
            db.query(UserDepartmentPost.user_id)
            .filter(
                UserDepartmentPost.department_id == department_id,
                UserDepartmentPost.post_id == post_id,
                UserDepartmentPost.tenant_id == tenant_id,
            )
            .first()
        )

        if result:
            return result[0]

        # 回退到 UserDepartment + UserPosition 联合查询
        user_dept = (
            db.query(UserDepartment.user_id)
            .filter(
                UserDepartment.department_id == department_id,
                UserDepartment.tenant_id == tenant_id,
            )
            .subquery()
        )

        user_pos = (
            db.query(UserPosition.user_id)
            .filter(
                UserPosition.position_id == post_id,
                UserPosition.tenant_id == tenant_id,
            )
            .subquery()
        )

        # 获取同时满足条件的用户
        result = (
            db.query(user_dept.c.user_id)
            .join(user_pos, user_dept.c.user_id == user_pos.c.user_id)
            .first()
        )

        return result[0] if result else None
