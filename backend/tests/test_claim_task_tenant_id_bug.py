"""
模块用途: TaskActionLog tenant_id bug 探索性测试
依赖配置: sqlite 内存数据库
数据流向: sqlite -> SQLAlchemy Session -> TaskService.claim_task -> TaskActionLog
函数清单:
    - test_claim_task_creates_action_log_with_valid_tenant_id(): 验证认领任务时创建带有效 tenant_id 的操作日志
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterator, Tuple

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models.workflow import FlowDefinition, FlowNode, ProcessInstance, Task, TaskActionLog
from app.models.user import Tenant, User
from app.services.approval_service import TaskService


@pytest.fixture()
def db_session() -> Iterator[Session]:
    """构建独立 sqlite 会话。

    Time: O(1), Space: O(1)
    """
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def seed_process_context(db: Session) -> Tuple[Tenant, User, FlowNode, ProcessInstance]:
    """初始化租户、用户与流程上下文。

    Time: O(1), Space: O(1)
    """
    tenant = Tenant(name="测试租户")
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        account="approver",
        password_hash="hashed",
        name="审批人",
        is_active=True,
    )
    db.add(user)
    db.flush()

    flow_def = FlowDefinition(tenant_id=tenant.id, form_id=1, version=1, name="示例流程")
    db.add(flow_def)
    db.flush()

    node = FlowNode(
        tenant_id=tenant.id,
        flow_definition_id=flow_def.id,
        name="节点 A",
        type="user",
    )
    db.add(node)
    db.flush()

    process = ProcessInstance(
        tenant_id=tenant.id,
        form_id=1,
        form_version_id=1,
        submission_id=1,
        flow_definition_id=flow_def.id,
        state="running",
    )
    db.add(process)
    db.commit()
    db.refresh(process)

    return tenant, user, node, process


def _create_open_task(
    *,
    db: Session,
    tenant_id: int,
    node_id: int,
    process_id: int,
    assignee_user_id: int | None = None,
    assignee_group_id: int | None = None,
) -> Task:
    """创建开放状态的任务。

    Time: O(1), Space: O(1)
    """
    task = Task(
        tenant_id=tenant_id,
        process_instance_id=process_id,
        node_id=node_id,
        assignee_user_id=assignee_user_id,
        assignee_group_id=assignee_group_id,
        status="open",
        payload_json={},
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def test_claim_task_creates_action_log_with_valid_tenant_id(db_session: Session) -> None:
    """认领任务时创建的操作日志应包含有效的 tenant_id。

    Bug Condition: claim_task 调用 _create_action_log 时未传递 tenant_id，
    导致 TaskActionLog.tenant_id 为 NULL，触发 NOT NULL 约束 violation。

    Expected Behavior: TaskActionLog.tenant_id 应从 task.tenant_id 获取，
    确保日志记录与任务属于同一租户。

    Validates: Requirements 2.1, 2.2, 2.3
    """
    tenant, user, node, process = seed_process_context(db_session)

    # 创建开放状态的任务
    task = _create_open_task(
        db=db_session,
        tenant_id=tenant.id,
        node_id=node.id,
        process_id=process.id,
        assignee_user_id=user.id,
    )

    # 验证任务创建成功且有有效的 tenant_id
    assert task.id is not None
    assert task.tenant_id == tenant.id

    # 调用 claim_task 认领任务
    result = TaskService.claim_task(
        task_id=task.id,
        tenant_id=tenant.id,
        current_user=user,
        db=db_session,
    )

    # 验证任务认领成功
    assert result.id == task.id
    assert result.status.value == "claimed"

    # 查询创建的 TaskActionLog 记录
    action_log = (
        db_session.query(TaskActionLog)
        .filter(TaskActionLog.task_id == task.id)
        .first()
    )

    # 验证操作日志已创建
    assert action_log is not None, "TaskActionLog 记录应已创建"
    assert action_log.action == "claim", "操作类型应为 claim"
    assert action_log.actor_user_id == user.id, "操作人应为当前用户"

    # 关键验证: TaskActionLog 的 tenant_id 应有效（非 NULL）
    # BUG: 当前代码不会设置 tenant_id，导致此断言失败
    assert action_log.tenant_id is not None, (
        "TaskActionLog.tenant_id 不应为 NULL，"
        "应从 task.tenant_id 获取以满足 NOT NULL 约束"
    )
    assert action_log.tenant_id == tenant.id, (
        f"TaskActionLog.tenant_id 应等于 task.tenant_id ({tenant.id})，"
        f"实际为 {action_log.tenant_id}"
    )