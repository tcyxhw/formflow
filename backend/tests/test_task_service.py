"""
模块用途: TaskService SLA 等级过滤单元测试
依赖配置: sqlite 内存数据库
数据流向: sqlite -> SQLAlchemy Session -> TaskService.list_tasks -> Pydantic Schema
函数清单:
    - db_session(): 构建独立会话
    - seed_process_context(): 初始化租户/用户/流程上下文
    - test_list_tasks_filter_by_sla_level(): 验证各 SLA 等级过滤结果
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterator, Tuple

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models.workflow import FlowDefinition, FlowNode, ProcessInstance, Task
from app.models.user import Tenant, User
from app.schemas.approval_schemas import SlaLevel, TaskListRequest
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
    """初始化租户、用户与流程节点上下文。

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


def _create_task(
    *,
    db: Session,
    tenant_id: int,
    node_id: int,
    process_id: int,
    assignee_user_id: int,
    due_at: datetime | None,
) -> Task:
    """生成指定 due_at 的任务。

    Time: O(1), Space: O(1)
    """

    task = Task(
        tenant_id=tenant_id,
        process_instance_id=process_id,
        node_id=node_id,
        assignee_user_id=assignee_user_id,
        status="open",
        due_at=due_at,
        payload_json={},
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def test_list_tasks_filter_by_sla_level(db_session: Session) -> None:
    """不同 SLA 等级应仅返回对应任务。

    Time: O(K), Space: O(1)  (K = 枚举等级数量)
    """

    tenant, user, node, process = seed_process_context(db_session)
    now = datetime.utcnow()

    task_map: Dict[SlaLevel, Task] = {
        SlaLevel.UNKNOWN: _create_task(
            db=db_session,
            tenant_id=tenant.id,
            node_id=node.id,
            process_id=process.id,
            assignee_user_id=user.id,
            due_at=None,
        ),
        SlaLevel.EXPIRED: _create_task(
            db=db_session,
            tenant_id=tenant.id,
            node_id=node.id,
            process_id=process.id,
            assignee_user_id=user.id,
            due_at=now - timedelta(minutes=5),
        ),
        SlaLevel.CRITICAL: _create_task(
            db=db_session,
            tenant_id=tenant.id,
            node_id=node.id,
            process_id=process.id,
            assignee_user_id=user.id,
            due_at=now + timedelta(minutes=10),
        ),
        SlaLevel.WARNING: _create_task(
            db=db_session,
            tenant_id=tenant.id,
            node_id=node.id,
            process_id=process.id,
            assignee_user_id=user.id,
            due_at=now + timedelta(minutes=60),
        ),
        SlaLevel.NORMAL: _create_task(
            db=db_session,
            tenant_id=tenant.id,
            node_id=node.id,
            process_id=process.id,
            assignee_user_id=user.id,
            due_at=now + timedelta(minutes=240),
        ),
    }

    for level, task in task_map.items():
        request = TaskListRequest(
            page=1,
            page_size=10,
            only_mine=True,
            include_group_tasks=False,
            sla_level=level,
        )
        items, total = TaskService.list_tasks(request, tenant.id, user, db_session)
        assert total == 1
        assert len(items) == 1
        assert items[0].id == task.id
        assert items[0].sla_level == level.value


def test_get_sla_summary(db_session: Session) -> None:
    """SLA 汇总应统计不同等级任务数量。

    Time: O(N), Space: O(1)
    """

    tenant, user, node, process = seed_process_context(db_session)
    now = datetime.utcnow()

    # 构建不同等级的任务分布
    _create_task(
        db=db_session,
        tenant_id=tenant.id,
        node_id=node.id,
        process_id=process.id,
        assignee_user_id=user.id,
        due_at=None,
    )
    _create_task(
        db=db_session,
        tenant_id=tenant.id,
        node_id=node.id,
        process_id=process.id,
        assignee_user_id=user.id,
        due_at=now - timedelta(minutes=5),
    )
    _create_task(
        db=db_session,
        tenant_id=tenant.id,
        node_id=node.id,
        process_id=process.id,
        assignee_user_id=user.id,
        due_at=now + timedelta(minutes=15),
    )
    _create_task(
        db=db_session,
        tenant_id=tenant.id,
        node_id=node.id,
        process_id=process.id,
        assignee_user_id=user.id,
        due_at=now + timedelta(minutes=90),
    )
    _create_task(
        db=db_session,
        tenant_id=tenant.id,
        node_id=node.id,
        process_id=process.id,
        assignee_user_id=user.id,
        due_at=now + timedelta(minutes=240),
    )

    request = TaskListRequest(
        page=1,
        page_size=1,
        only_mine=True,
        include_group_tasks=False,
    )
    summary = TaskService.get_sla_summary(request, tenant.id, user, db_session)

    assert summary.total == 5
    assert summary.unknown == 1
    assert summary.expired == 1
    assert summary.critical == 1
    assert summary.warning == 1
    assert summary.normal == 1
