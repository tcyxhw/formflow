# app/models/notification.py
"""
通知与统计相关模型
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, JSON,
    ForeignKey, UniqueConstraint, Index, Float, Boolean
)
from sqlalchemy.orm import relationship
from app.models.base import DBBaseModel, Base, TimestampMixin


class NotificationConfig(DBBaseModel):
    """通知配置表"""
    __tablename__ = "notification_config"

    business_type = Column(String(50), nullable=False, comment="业务类型")
    business_id = Column(Integer, nullable=True, comment="业务ID")
    event = Column(String(50), nullable=False, comment="通知事件")
    channels = Column(JSON, nullable=False, comment="通知渠道")
    recipient_rule = Column(JSON, nullable=True, comment="接收人规则")
    template_id = Column(Integer, nullable=True, comment="模板ID")
    enabled = Column(Boolean, default=True, comment="是否启用")


class NotificationLog(DBBaseModel):
    """通知记录表"""
    __tablename__ = "notification_log"
    __table_args__ = (
        Index("idx_recipient_status", "recipient_id", "status"),
    )

    recipient_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="接收人ID")
    type = Column(String(20), nullable=False, comment="通知类型")
    title = Column(String(200), nullable=True, comment="标题")
    content = Column(String(2000), nullable=False, comment="内容")
    status = Column(String(20), default="pending", comment="状态")
    sent_at = Column(DateTime, nullable=True, comment="发送时间")
    error_message = Column(String(500), nullable=True, comment="失败原因")
    retry_count = Column(Integer, default=0, comment="重试次数")

    # 关系
    # recipient = relationship("User")


class FormStatistics(DBBaseModel):
    """表单访问统计表"""
    __tablename__ = "form_statistics"
    __table_args__ = (
        UniqueConstraint("form_id", "stat_date", name="uq_form_stat"),
    )

    form_id = Column(Integer, ForeignKey("form.id"), nullable=False)
    stat_date = Column(DateTime, nullable=False, comment="统计日期")
    view_count = Column(Integer, default=0, comment="访问次数")
    unique_visitors = Column(Integer, default=0, comment="独立访客数")
    submit_count = Column(Integer, default=0, comment="提交次数")
    completion_rate = Column(Float, default=0, comment="完成率")
    avg_duration = Column(Integer, default=0, comment="平均填写时长(秒)")
    device_stats = Column(JSON, nullable=True, comment="设备分布")
    source_stats = Column(JSON, nullable=True, comment="来源分布")


class ScheduledJob(DBBaseModel):
    """定时任务表"""
    __tablename__ = "scheduled_job"

    job_name = Column(String(100), nullable=False, comment="任务名称")
    job_type = Column(String(50), nullable=False, comment="任务类型")
    cron_expression = Column(String(100), nullable=False, comment="cron表达式")
    job_params = Column(JSON, nullable=True, comment="任务参数")
    last_run_at = Column(DateTime, nullable=True, comment="上次执行时间")
    next_run_at = Column(DateTime, nullable=True, comment="下次执行时间")
    status = Column(String(20), default="idle", comment="执行状态")
    enabled = Column(Boolean, default=True, comment="是否启用")


class AuditLog(Base, TimestampMixin):
    """审计日志表"""
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("idx_resource", "resource_type", "resource_id"),
        Index("idx_actor_time", "actor_user_id", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, comment="租户ID")
    actor_user_id = Column(Integer, ForeignKey("user.id"), nullable=True, comment="操作人ID")
    action = Column(String(50), nullable=False, comment="动作")
    resource_type = Column(String(50), nullable=False, comment="资源类型")
    resource_id = Column(Integer, nullable=True, comment="资源ID")
    before_json = Column(JSON, nullable=True, comment="变更前快照")
    after_json = Column(JSON, nullable=True, comment="变更后快照")
    ip = Column(String(45), nullable=True, comment="来源IP")
    ua = Column(String(500), nullable=True, comment="用户代理")

    # 关系
    # actor = relationship("User")


class RefreshToken(Base, TimestampMixin):
    """刷新令牌表"""
    __tablename__ = "refresh_token"
    __table_args__ = (
        Index("idx_user_family", "user_id", "family_id", "active"),
    )

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, comment="租户ID")
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    family_id = Column(String(100), nullable=False, comment="家族ID")
    jti_hash = Column(String(255), unique=True, nullable=False, comment="令牌哈希")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    active = Column(Boolean, default=True, comment="是否有效")
    meta_json = Column(JSON, nullable=True, comment="元数据")

    # 关系
    # user = relationship("User")


class DictItem(DBBaseModel):
    """字典项表"""
    __tablename__ = "dict_item"
    __table_args__ = (
        UniqueConstraint("tenant_id", "type", "code", name="uq_dict_item"),
    )

    type = Column(String(50), nullable=False, comment="字典类型")
    code = Column(String(50), nullable=False, comment="编码")
    name = Column(String(100), nullable=False, comment="名称")
    sort = Column(Integer, default=0, comment="排序")
    enabled = Column(Boolean, default=True, comment="是否启用")