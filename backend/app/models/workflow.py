# app/models/workflow.py
"""
流程与任务相关模型
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    UniqueConstraint,
    Index,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import DBBaseModel


class FlowDefinition(DBBaseModel):
    """流程定义表"""
    __tablename__ = "flow_definition"
    __table_args__ = (
        UniqueConstraint("tenant_id", "form_id", "version", name="uq_flow_def"),
    )

    form_id = Column(Integer, ForeignKey("form.id"), nullable=False)
    version = Column(Integer, nullable=False, comment="版本号")
    name = Column(String(100), nullable=False, comment="流程名称")
    active_snapshot_id = Column(Integer, ForeignKey("flow_snapshot.id"), nullable=True, comment="当前生效快照ID")

    # 关系
    # nodes = relationship("FlowNode", back_populates="flow_definition")
    # routes = relationship("FlowRoute", back_populates="flow_definition")
    # instances = relationship("ProcessInstance", back_populates="flow_definition")


class FlowNode(DBBaseModel):
    """流程节点表"""
    __tablename__ = "flow_node"

    flow_definition_id = Column(Integer, ForeignKey("flow_definition.id"), nullable=False)
    name = Column(String(100), nullable=False, comment="节点名称")
    type = Column(String(20), nullable=False, comment="节点类型：start/user/auto/end")
    assignee_type = Column(String(20), nullable=True, comment="指派类型：role/position/group/user/expr")
    assignee_value = Column(JSON, nullable=True, comment="指派参数")
    approve_policy = Column(String(20), default="any", comment="会签策略：any/all/percent")
    approve_threshold = Column(Integer, nullable=True, comment="percent 策略阈值(1-100)")
    sla_hours = Column(Integer, nullable=True, comment="处理时限(小时)")
    allow_delegate = Column(Boolean, default=True, comment="允许代理")
    route_mode = Column(String(20), default="exclusive", comment="路由模式：exclusive/parallel")
    auto_approve_enabled = Column(Boolean, default=False, comment="自动审批开关")
    auto_approve_cond = Column(JSON, nullable=True, comment="自动通过条件")
    auto_reject_cond = Column(JSON, nullable=True, comment="自动驳回条件")
    auto_sample_ratio = Column(Float, default=0, comment="抽检比例")
    next_default_node_id = Column(Integer, nullable=True, comment="默认去向节点ID")
    reject_strategy = Column(String(20), default="TO_START", comment="驳回策略：TO_START/TO_PREVIOUS")
    condition_branches = Column(JSON, nullable=True, comment='条件分支配置：{"branches": [...], "default_target_node_id": ...}')

    # 关系
    # flow_definition = relationship("FlowDefinition", back_populates="nodes")
    # tasks = relationship("Task", back_populates="node")


class FlowRoute(DBBaseModel):
    """流程路由规则表"""
    __tablename__ = "flow_route"
    __table_args__ = (
        UniqueConstraint("from_node_id", "priority", name="uq_route_priority"),
    )

    flow_definition_id = Column(Integer, ForeignKey("flow_definition.id"), nullable=False)
    from_node_id = Column(Integer, ForeignKey("flow_node.id"), nullable=False)
    to_node_id = Column(Integer, ForeignKey("flow_node.id"), nullable=False)
    priority = Column(Integer, nullable=False, comment="优先级")
    condition_json = Column(JSON, nullable=True, comment="条件表达式")
    enabled = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否默认")

    # 关系
    # flow_definition = relationship("FlowDefinition", back_populates="routes")
    # from_node = relationship("FlowNode", foreign_keys=[from_node_id])
    # to_node = relationship("FlowNode", foreign_keys=[to_node_id])


class FlowSnapshot(DBBaseModel):
    """流程快照表，存储运行态不可变配置。"""

    __tablename__ = "flow_snapshot"
    __table_args__ = (
        UniqueConstraint("flow_definition_id", "version_tag", name="uq_flow_snapshot_version"),
        Index("idx_snapshot_flow", "flow_definition_id"),
    )

    flow_definition_id = Column(Integer, ForeignKey("flow_definition.id"), nullable=False)
    version_tag = Column(String(50), nullable=False, comment="快照版本标签")
    rules_payload = Column(JSONB, nullable=False, comment="运行态规则载荷")
    metadata_json = Column(JSONB, nullable=True, comment="发布时的元信息")
    created_by = Column(Integer, ForeignKey("user.id"), nullable=True, comment="发布人")


class FlowDraft(DBBaseModel):
    """流程草稿表，存储编辑态配置。"""

    __tablename__ = "flow_draft"
    __table_args__ = (
        UniqueConstraint("flow_definition_id", name="uq_flow_draft_definition"),
    )

    flow_definition_id = Column(Integer, ForeignKey("flow_definition.id"), nullable=False)
    version = Column(Integer, nullable=False, default=1, comment="乐观锁版本")
    nodes_graph = Column(JSONB, nullable=True, comment="画布节点与连线信息")
    config_json = Column(JSONB, nullable=False, comment="节点与路由配置快照")
    updated_by = Column(Integer, ForeignKey("user.id"), nullable=True, comment="最后编辑人")
    last_snapshot_id = Column(Integer, ForeignKey("flow_snapshot.id"), nullable=True, comment="最近同步快照ID")


class ProcessInstance(DBBaseModel):
    """流程实例表"""
    __tablename__ = "process_instance"
    __table_args__ = (
        Index("idx_tenant_form_state", "tenant_id", "form_id", "state"),
    )

    form_id = Column(Integer, ForeignKey("form.id"), nullable=False)
    form_version_id = Column(Integer, ForeignKey("form_version.id"), nullable=False)
    submission_id = Column(Integer, ForeignKey("submission.id"), nullable=False)
    flow_definition_id = Column(Integer, ForeignKey("flow_definition.id"), nullable=False)
    state = Column(String(20), default="running", comment="状态：running/finished/canceled")
    form_data_snapshot = Column(JSONB, nullable=True, comment="表单数据快照")

    # 关系
    # flow_definition = relationship("FlowDefinition", back_populates="instances")
    # tasks = relationship("Task", back_populates="process_instance")
    # parallel_runtimes = relationship("ParallelRuntime", back_populates="process_instance")


class Task(DBBaseModel):
    """待办任务表"""
    __tablename__ = "task"
    __table_args__ = (
        Index("idx_assignee_user", "assignee_user_id", "status"),
        Index("idx_assignee_group", "assignee_group_id", "status"),
    )

    process_instance_id = Column(Integer, ForeignKey("process_instance.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("flow_node.id"), nullable=False)
    assignee_user_id = Column(Integer, ForeignKey("user.id"), nullable=True, comment="指派用户ID")
    assignee_group_id = Column(Integer, ForeignKey("approval_group.id"), nullable=True, comment="指派小组ID")
    status = Column(String(20), default="open", comment="状态：open/claimed/completed/canceled")
    action = Column(String(20), nullable=True, comment="完成动作：approve/reject/transfer等")
    due_at = Column(DateTime, nullable=True, comment="到期时间")
    claimed_by = Column(Integer, ForeignKey("user.id"), nullable=True, comment="认领人ID")
    claimed_at = Column(DateTime, nullable=True, comment="认领时间")
    completed_by = Column(Integer, ForeignKey("user.id"), nullable=True, comment="完成人ID")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    payload_json = Column(JSON, nullable=True, comment="节点表单数据")
    version = Column(Integer, default=1, comment="版本号(乐观锁)")
    task_type = Column(String(20), default="approve", comment="任务类型：approve/cc")
    comment = Column(String(500), nullable=True, comment="审批意见")

    # 关系 - 修复：移除 back_populates，使用字符串形式的 foreign_keys
    # process_instance = relationship("ProcessInstance", back_populates="tasks")
    # node = relationship("FlowNode", back_populates="tasks")
    # assignee_user = relationship(
    #     "User",
    #     foreign_keys="Task.assignee_user_id"  # 修复：使用字符串，移除 back_populates
    # )
    # assignee_group = relationship("ApprovalGroup")
    # claimed_user = relationship(
    #     "User",
    #     foreign_keys="Task.claimed_by"  # 修复：使用字符串
    # )
    # completed_user = relationship(
    #     "User",
    #     foreign_keys="Task.completed_by"  # 修复：使用字符串
    # )
    # action_logs = relationship("TaskActionLog", back_populates="task")


class TaskActionLog(DBBaseModel):
    """任务操作日志表"""
    __tablename__ = "task_action_log"
    __table_args__ = (
        Index("idx_task_created", "task_id", "created_at"),
    )

    tenant_id = Column(Integer, nullable=False, comment="租户ID")
    task_id = Column(Integer, ForeignKey("task.id"), nullable=False)
    actor_user_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="操作人ID")
    action = Column(String(20), nullable=False, comment="动作")
    detail_json = Column(JSON, nullable=True, comment="操作详情")

    # 关系
    # task = relationship("Task", back_populates="action_logs")
    # actor = relationship("User")


class ParallelRuntime(DBBaseModel):
    """并行运行态表"""
    __tablename__ = "parallel_runtime"
    __table_args__ = (
        UniqueConstraint("process_instance_id", "fork_node_id", name="uq_parallel_runtime"),
    )

    process_instance_id = Column(Integer, ForeignKey("process_instance.id"), nullable=False)
    fork_node_id = Column(Integer, ForeignKey("flow_node.id"), nullable=False, comment="分叉节点ID")
    opened_count = Column(Integer, nullable=False, comment="开启分支数")
    arrived_count = Column(Integer, default=0, comment="已到达数")
    join_policy = Column(String(20), nullable=False, comment="汇合策略：all/any/n_of_m")
    n_required = Column(Integer, nullable=True, comment="需要数量")
    closed = Column(Boolean, default=False, comment="是否已放行")
    opened_branches = Column(JSON, nullable=True, comment="分支清单")

    # 关系
    # process_instance = relationship("ProcessInstance", back_populates="parallel_runtimes")
    # fork_node = relationship("FlowNode")


class WorkflowOperationLog(DBBaseModel):
    """流程操作日志表"""
    __tablename__ = "workflow_operation_log"
    __table_args__ = (
        Index("idx_instance_created", "process_instance_id", "created_at"),
        Index("idx_operation_type", "operation_type", "created_at"),
        Index("idx_tenant_created", "tenant_id", "created_at"),
    )

    tenant_id = Column(Integer, nullable=False, comment="租户ID")
    process_instance_id = Column(Integer, ForeignKey("process_instance.id"), nullable=False, comment="流程实例ID")
    operation_type = Column(String(20), nullable=False, comment="操作类型：SUBMIT/APPROVE/REJECT/CANCEL/CC")
    operator_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="操作人ID")
    comment = Column(String(500), nullable=True, comment="操作备注")
    detail_json = Column(JSONB, nullable=True, comment="操作详情")

    # 关系
    # process_instance = relationship("ProcessInstance")
    # operator = relationship("User")
