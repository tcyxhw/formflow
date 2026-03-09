"""
模块用途: 多渠道通知服务
依赖配置: 
  - 环境变量: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD（邮件）
  - Redis: 用于存储通知队列
数据流向: 
  业务触发 -> 通知构建 -> 渠道分发（站内信/邮件/推送）
  -> 发送记录 -> 失败重试
函数清单:
    - send_notification(): 通用通知入口
    - send_in_app(): 发送站内信
    - send_email(): 发送邮件
    - batch_send(): 批量发送
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """通知渠道枚举。"""

    IN_APP = "in_app"      # 站内信
    EMAIL = "email"        # 邮件
    SMS = "sms"            # 短信（预留）
    PUSH = "push"          # 推送（预留）


class NotificationPriority(str, Enum):
    """通知优先级。"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, Enum):
    """通知类型。"""

    TASK_ASSIGNED = "task_assigned"           # 任务指派
    TASK_ESCALATED = "task_escalated"         # 任务升级
    TASK_DUE_SOON = "task_due_soon"           # 任务即将到期
    TASK_OVERDUE = "task_overdue"             # 任务已逾期
    PROCESS_COMPLETED = "process_completed"   # 流程完成
    SYSTEM = "system"                         # 系统通知


class NotificationTemplate(BaseModel):
    """通知模板。"""

    type: NotificationType
    title_template: str
    content_template: str
    channels: List[NotificationChannel] = Field(default_factory=lambda: [NotificationChannel.IN_APP])
    priority: NotificationPriority = NotificationPriority.NORMAL


# 预定义模板
NOTIFICATION_TEMPLATES: Dict[NotificationType, NotificationTemplate] = {
    NotificationType.TASK_ASSIGNED: NotificationTemplate(
        type=NotificationType.TASK_ASSIGNED,
        title_template="新任务指派: {task_title}",
        content_template="您有一个新的审批任务需要处理。任务来自流程: {process_name}，请于 {due_time} 前完成。",
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
        priority=NotificationPriority.NORMAL,
    ),
    NotificationType.TASK_ESCALATED: NotificationTemplate(
        type=NotificationType.TASK_ESCALATED,
        title_template="任务升级提醒: {task_title}",
        content_template="任务已因超时自动升级。原处理人: {old_assignee_name}，当前指派给您。任务来自流程: {process_name}",
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
        priority=NotificationPriority.HIGH,
    ),
    NotificationType.TASK_DUE_SOON: NotificationTemplate(
        type=NotificationType.TASK_DUE_SOON,
        title_template="任务即将到期: {task_title}",
        content_template="您的任务将在 {remaining_time} 后到期，请尽快处理。流程: {process_name}",
        channels=[NotificationChannel.IN_APP],
        priority=NotificationPriority.NORMAL,
    ),
    NotificationType.TASK_OVERDUE: NotificationTemplate(
        type=NotificationType.TASK_OVERDUE,
        title_template="任务已逾期: {task_title}",
        content_template="您的任务已逾期 {overdue_time}，请立即处理或联系上级。流程: {process_name}",
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
        priority=NotificationPriority.URGENT,
    ),
    NotificationType.PROCESS_COMPLETED: NotificationTemplate(
        type=NotificationType.PROCESS_COMPLETED,
        title_template="流程已完成: {process_name}",
        content_template="您参与的流程 {process_name} 已{result}。",
        channels=[NotificationChannel.IN_APP],
        priority=NotificationPriority.NORMAL,
    ),
}


@dataclass
class Notification:
    """通知实体。"""

    id: Optional[int] = None
    recipient_id: int = 0
    recipient_type: str = "user"  # user / group
    type: NotificationType = NotificationType.SYSTEM
    title: str = ""
    content: str = ""
    channels: List[NotificationChannel] = field(default_factory=list)
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    status: str = "pending"  # pending / sent / failed / read
    error_message: Optional[str] = None


class NotificationService:
    """多渠道通知服务。"""

    @staticmethod
    def create_notification(
        notification_type: NotificationType,
        recipient_id: int,
        context: Dict[str, Any],
        recipient_type: str = "user",
    ) -> Notification:
        """创建通知对象。

        :param notification_type: 通知类型
        :param recipient_id: 接收者ID
        :param context: 模板变量上下文
        :param recipient_type: 接收者类型
        :return: 通知对象

        Time: O(1), Space: O(1)
        """

        template = NOTIFICATION_TEMPLATES.get(notification_type)
        if not template:
            logger.warning(f"未知的通知类型: {notification_type}")
            template = NotificationTemplate(
                type=notification_type,
                title_template="系统通知",
                content_template="",
            )

        # 渲染模板
        title = template.title_template.format(**context)
        content = template.content_template.format(**context)

        return Notification(
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            type=notification_type,
            title=title,
            content=content,
            channels=template.channels.copy(),
            priority=template.priority,
            data=context,
        )

    @staticmethod
    def send_notification(
        notification: Notification,
        db: Optional[Any] = None,
    ) -> bool:
        """发送通知到所有配置的渠道。

        :param notification: 通知对象
        :param db: 数据库会话（可选，用于持久化）
        :return: 是否全部成功

        Time: O(N), Space: O(1)  N=渠道数量
        """

        success = True

        for channel in notification.channels:
            try:
                if channel == NotificationChannel.IN_APP:
                    NotificationService._send_in_app(notification)
                elif channel == NotificationChannel.EMAIL:
                    NotificationService._send_email(notification)
                elif channel == NotificationChannel.SMS:
                    NotificationService._send_sms(notification)
                elif channel == NotificationChannel.PUSH:
                    NotificationService._send_push(notification)
            except Exception as e:
                logger.error(
                    f"通知发送失败",
                    extra={
                        "channel": channel,
                        "recipient": notification.recipient_id,
                        "error": str(e),
                    },
                )
                success = False
                notification.error_message = str(e)

        notification.status = "sent" if success else "failed"
        notification.sent_at = datetime.utcnow()

        # 如果提供了数据库会话，持久化通知记录
        if db:
            NotificationService._persist_notification(notification, db)

        return success

    @staticmethod
    def notify_task_escalation(
        task_id: int,
        old_assignee_id: Optional[int],
        new_assignee_id: int,
        process_name: str,
        escalation_reason: str,
        tenant_id: int,
        db: Optional[Any] = None,
    ) -> bool:
        """发送任务升级通知。

        :param task_id: 任务ID
        :param old_assignee_id: 原处理人ID
        :param new_assignee_id: 新处理人ID
        :param process_name: 流程名称
        :param escalation_reason: 升级原因
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 是否成功

        Time: O(1), Space: O(1)
        """

        # 通知新处理人
        notification = NotificationService.create_notification(
            notification_type=NotificationType.TASK_ESCALATED,
            recipient_id=new_assignee_id,
            context={
                "task_id": task_id,
                "task_title": f"任务#{task_id}",
                "process_name": process_name,
                "old_assignee_name": f"用户#{old_assignee_id}" if old_assignee_id else "未指派",
                "escalation_reason": escalation_reason,
                "tenant_id": tenant_id,
            },
        )

        return NotificationService.send_notification(notification, db)

    @staticmethod
    def notify_task_overdue(
        task_id: int,
        assignee_id: int,
        process_name: str,
        due_time: datetime,
        tenant_id: int,
        db: Optional[Any] = None,
    ) -> bool:
        """发送任务逾期通知。

        :param task_id: 任务ID
        :param assignee_id: 处理人ID
        :param process_name: 流程名称
        :param due_time: 到期时间
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 是否成功

        Time: O(1), Space: O(1)
        """

        overdue_duration = datetime.utcnow() - due_time
        hours = int(overdue_duration.total_seconds() / 3600)

        notification = NotificationService.create_notification(
            notification_type=NotificationType.TASK_OVERDUE,
            recipient_id=assignee_id,
            context={
                "task_id": task_id,
                "task_title": f"任务#{task_id}",
                "process_name": process_name,
                "overdue_time": f"{hours}小时",
                "tenant_id": tenant_id,
            },
        )

        return NotificationService.send_notification(notification, db)

    @staticmethod
    def batch_send(
        notifications: List[Notification],
        db: Optional[Any] = None,
    ) -> Dict[str, int]:
        """批量发送通知。

        :param notifications: 通知列表
        :param db: 数据库会话
        :return: 统计结果 {sent: N, failed: M}

        Time: O(N), Space: O(1)  N=通知数量
        """

        stats = {"sent": 0, "failed": 0}

        for notification in notifications:
            success = NotificationService.send_notification(notification, db)
            if success:
                stats["sent"] += 1
            else:
                stats["failed"] += 1

        return stats

    # -------------------- 私有方法 --------------------

    @staticmethod
    def _send_in_app(notification: Notification) -> None:
        """发送站内信。

        当前实现：仅记录日志，实际应写入数据库或Redis队列

        :param notification: 通知对象

        Time: O(1), Space: O(1)
        """

        logger.info(
            f"[站内信] {notification.title}",
            extra={
                "recipient_id": notification.recipient_id,
                "type": notification.type,
                "priority": notification.priority,
            },
        )
        # 实际实现：写入 notifications 表或 Redis 队列

    @staticmethod
    def _send_email(notification: Notification) -> None:
        """发送邮件。

        当前实现：仅记录日志，实际应调用SMTP服务

        :param notification: 通知对象

        Time: O(1), Space: O(1)
        """

        import os

        smtp_host = os.getenv("SMTP_HOST")
        if not smtp_host:
            logger.debug("邮件服务未配置，跳过邮件发送")
            return

        logger.info(
            f"[邮件] {notification.title}",
            extra={
                "recipient_id": notification.recipient_id,
                "type": notification.type,
            },
        )
        # 实际实现：调用 SMTP 发送邮件

    @staticmethod
    def _send_sms(notification: Notification) -> None:
        """发送短信（预留）。

        :param notification: 通知对象

        Time: O(1), Space: O(1)
        """

        logger.debug(f"[短信] 服务未实现: {notification.title}")

    @staticmethod
    def _send_push(notification: Notification) -> None:
        """发送推送（预留）。

        :param notification: 通知对象

        Time: O(1), Space: O(1)
        """

        logger.debug(f"[推送] 服务未实现: {notification.title}")

    @staticmethod
    def _persist_notification(
        notification: Notification,
        db: Any,
    ) -> None:
        """持久化通知记录。

        :param notification: 通知对象
        :param db: 数据库会话

        Time: O(1), Space: O(1)
        """

        # 实际实现：写入 notifications 表
        # 由于目前还没有 notification 模型，先记录日志
        logger.debug(f"通知持久化: task={notification.type}, status={notification.status}")
