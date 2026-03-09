"""
模块用途: 审计日志查询与导出服务
依赖配置: 无
数据流向: AuditLog模型 -> 查询/导出 -> API响应
函数清单:
    - list_audit_logs(): 分页查询审计日志
    - export_audit_logs_to_csv(): 导出CSV
    - get_audit_log_detail(): 详情查询
    - compare_changes(): 变更对比
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import csv
import io

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models.notification import AuditLog
from app.models.user import User
from app.core.exceptions import NotFoundError, AuthorizationError


class AuditService:
    """审计日志服务"""

    @staticmethod
    def list_audit_logs(
        tenant_id: int,
        current_user_id: int,
        is_admin: bool,
        query: 'AuditLogQueryRequest',
        db: Session,
    ) -> Tuple[List[AuditLog], int]:
        """查询审计日志

        权限控制:
        - 管理员: 可查看全部
        - 普通用户: 只能查看自己相关的

        :param tenant_id: 租户ID
        :param current_user_id: 当前用户ID
        :param is_admin: 是否管理员
        :param query: 查询参数
        :param db: 数据库会话
        :return: (日志列表, 总数)

        Time: O(N), Space: O(N)
        """

        # 构建基础查询
        base_query = db.query(AuditLog).filter(
            AuditLog.tenant_id == tenant_id
        )

        # 权限过滤
        if not is_admin:
            # 非管理员只能看自己的
            base_query = base_query.filter(
                AuditLog.actor_user_id == current_user_id
            )
        elif query.only_mine and is_admin:
            # 管理员但只想看自己的
            base_query = base_query.filter(
                AuditLog.actor_user_id == current_user_id
            )

        # 其他筛选条件
        if query.actor_user_id is not None:
            base_query = base_query.filter(
                AuditLog.actor_user_id == query.actor_user_id
            )

        if query.resource_type:
            base_query = base_query.filter(
                AuditLog.resource_type == query.resource_type
            )

        if query.action:
            base_query = base_query.filter(
                AuditLog.action == query.action
            )

        if query.resource_id is not None:
            base_query = base_query.filter(
                AuditLog.resource_id == query.resource_id
            )

        if query.date_from:
            base_query = base_query.filter(
                AuditLog.created_at >= query.date_from
            )

        if query.date_to:
            base_query = base_query.filter(
                AuditLog.created_at <= query.date_to
            )

        # 统计总数
        total = base_query.count()

        # 分页查询
        logs = (
            base_query.order_by(desc(AuditLog.created_at))
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
            .all()
        )

        return logs, total

    @staticmethod
    def get_audit_log_detail(
        log_id: int,
        tenant_id: int,
        current_user_id: int,
        is_admin: bool,
        db: Session,
    ) -> AuditLog:
        """获取审计日志详情

        :param log_id: 日志ID
        :param tenant_id: 租户ID
        :param current_user_id: 当前用户ID
        :param is_admin: 是否管理员
        :param db: 数据库会话
        :return: 审计日志对象
        :raises NotFoundError: 日志不存在
        :raises AuthorizationError: 无权限查看

        Time: O(1), Space: O(1)
        """

        log = db.query(AuditLog).filter(
            AuditLog.id == log_id,
            AuditLog.tenant_id == tenant_id,
        ).first()

        if not log:
            raise NotFoundError("审计日志不存在")

        # 权限检查
        if not is_admin and log.actor_user_id != current_user_id:
            raise AuthorizationError("无权查看此审计日志")

        return log

    @staticmethod
    def export_audit_logs_to_csv(
        tenant_id: int,
        current_user_id: int,
        is_admin: bool,
        request: 'AuditLogExportRequest',
        db: Session,
    ) -> str:
        """导出审计日志为CSV

        权限控制同 list_audit_logs
        限制最大导出10000条

        :param tenant_id: 租户ID
        :param current_user_id: 当前用户ID
        :param is_admin: 是否管理员
        :param request: 导出参数
        :param db: 数据库会话
        :return: CSV内容字符串

        Time: O(N), Space: O(N)
        """

        # 构建查询条件（同list_audit_logs）
        base_query = db.query(AuditLog).filter(
            AuditLog.tenant_id == tenant_id
        )

        # 权限过滤
        if not is_admin:
            base_query = base_query.filter(
                AuditLog.actor_user_id == current_user_id
            )

        # 其他筛选
        if request.actor_user_id is not None:
            base_query = base_query.filter(
                AuditLog.actor_user_id == request.actor_user_id
            )

        if request.resource_type:
            base_query = base_query.filter(
                AuditLog.resource_type == request.resource_type
            )

        if request.action:
            base_query = base_query.filter(
                AuditLog.action == request.action
            )

        if request.resource_ids:
            base_query = base_query.filter(
                AuditLog.resource_id.in_(request.resource_ids)
            )

        if request.date_from:
            base_query = base_query.filter(
                AuditLog.created_at >= request.date_from
            )

        if request.date_to:
            base_query = base_query.filter(
                AuditLog.created_at <= request.date_to
            )

        # 限制最大导出数量
        MAX_EXPORT = 10000
        logs = (
            base_query.order_by(desc(AuditLog.created_at))
            .limit(MAX_EXPORT)
            .all()
        )

        # 查询用户姓名映射
        user_ids = {log.actor_user_id for log in logs if log.actor_user_id}
        users = db.query(User.id, User.name).filter(User.id.in_(user_ids)).all()
        user_map = {u.id: u.name for u in users}

        # 生成CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # 写入表头
        writer.writerow([
            "ID",
            "操作人ID",
            "操作人姓名",
            "动作",
            "资源类型",
            "资源ID",
            "变更前",
            "变更后",
            "IP地址",
            "用户代理",
            "创建时间",
        ])

        # 写入数据
        for log in logs:
            writer.writerow([
                log.id,
                log.actor_user_id,
                user_map.get(log.actor_user_id, ""),
                log.action,
                log.resource_type,
                log.resource_id,
                str(log.before_json) if log.before_json else "",
                str(log.after_json) if log.after_json else "",
                log.ip or "",
                log.ua or "",
                log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
            ])

        return output.getvalue()

    @staticmethod
    def compare_changes(
        before: Optional[Dict[str, Any]],
        after: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """对比变更前后的差异

        :param before: 变更前数据
        :param after: 变更后数据
        :return: 变更字段列表，每个字段包含:
            - field: 字段名
            - before: 变更前值
            - after: 变更后值
            - change_type: added/modified/removed

        Time: O(K), Space: O(K)  K=字段数
        """

        changes = []
        before = before or {}
        after = after or {}

        all_keys = set(before.keys()) | set(after.keys())

        for key in all_keys:
            before_val = before.get(key)
            after_val = after.get(key)

            if key not in before:
                # 新增字段
                changes.append({
                    "field": key,
                    "before": None,
                    "after": after_val,
                    "change_type": "added",
                })
            elif key not in after:
                # 删除字段
                changes.append({
                    "field": key,
                    "before": before_val,
                    "after": None,
                    "change_type": "removed",
                })
            elif before_val != after_val:
                # 修改字段
                changes.append({
                    "field": key,
                    "before": before_val,
                    "after": after_val,
                    "change_type": "modified",
                })

        # 按字段名排序
        changes.sort(key=lambda x: x["field"])

        return changes
