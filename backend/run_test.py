"""
Simple test runner for the tenant_id bug exploration test.
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime
from typing import Tuple
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.core.database import Base
from app.models.workflow import FlowDefinition, FlowNode, ProcessInstance, Task, TaskActionLog
from app.models.user import Tenant, User
from app.services.approval_service import TaskService


def seed_process_context(db: Session) -> Tuple[Tenant, User, FlowNode, ProcessInstance]:
    """初始化租户、用户与流程上下文。"""
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
    db: Session,
    tenant_id: int,
    node_id: int,
    process_id: int,
    assignee_user_id: int | None = None,
) -> Task:
    """创建开放状态的任务。"""
    task = Task(
        tenant_id=tenant_id,
        process_instance_id=process_id,
        node_id=node_id,
        assignee_user_id=assignee_user_id,
        status="open",
        payload_json={},
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def test_claim_task_tenant_id_bug():
    """测试 claim_task 创建 TaskActionLog 时 tenant_id 是否正确设置。"""
    print("=" * 60)
    print("Bug Condition Exploration Test: TaskActionLog tenant_id on Claim")
    print("=" * 60)
    
    # 创建内存数据库
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    db = TestingSession()
    
    try:
        # 初始化测试数据
        tenant, user, node, process = seed_process_context(db)
        print(f"\n[Tear Up] Created tenant (id={tenant.id}), user (id={user.id})")
        
        # 创建开放状态的任务
        task = _create_open_task(
            db=db,
            tenant_id=tenant.id,
            node_id=node.id,
            process_id=process.id,
            assignee_user_id=user.id,
        )
        print(f"[Tear Up] Created task (id={task.id}, tenant_id={task.tenant_id})")
        
        # 验证任务创建成功
        assert task.id is not None
        assert task.tenant_id == tenant.id
        print("[Verify] Task created with valid tenant_id")
        
        # 调用 claim_task 认领任务
        print("\n[Action] Calling TaskService.claim_task()...")
        try:
            result = TaskService.claim_task(
                task_id=task.id,
                tenant_id=tenant.id,
                current_user=user,
                db=db,
            )
            print(f"[Success] Task claimed, status={result.status.value}")
        except Exception as e:
            print(f"[Error] claim_task raised exception: {type(e).__name__}: {e}")
            return False
        
        # 查询创建的 TaskActionLog 记录
        action_log = (
            db.query(TaskActionLog)
            .filter(TaskActionLog.task_id == task.id)
            .first()
        )
        
        if action_log is None:
            print("[Error] TaskActionLog record not found!")
            return False
        
        print(f"\n[Verify] TaskActionLog created:")
        print(f"  - task_id: {action_log.task_id}")
        print(f"  - actor_user_id: {action_log.actor_user_id}")
        print(f"  - action: {action_log.action}")
        print(f"  - tenant_id: {action_log.tenant_id}")
        
        # 关键验证: TaskActionLog 的 tenant_id 应有效（非 NULL）
        if action_log.tenant_id is None:
            print("\n" + "!" * 60)
            print("BUG CONFIRMED: TaskActionLog.tenant_id is NULL!")
            print("!" * 60)
            print("\nCounterexample:")
            print("  - claim_task() was called with valid tenant_id")
            print("  - _create_action_log() did not pass tenant_id to TaskActionLog")
            print("  - TaskActionLog.tenant_id = NULL (violates NOT NULL constraint)")
            print("\nRoot Cause:")
            print("  - claim_task calls _create_action_log without tenant_id parameter")
            print("  - _create_action_log does not set tenant_id when creating TaskActionLog")
            return False
        else:
            print("\n[Success] TaskActionLog.tenant_id is valid (not NULL)")
            print(f"  tenant_id = {action_log.tenant_id}")
            return True
            
    finally:
        db.close()
        Base.metadata.drop_all(engine)


if __name__ == "__main__":
    success = test_claim_task_tenant_id_bug()
    print("\n" + "=" * 60)
    if success:
        print("TEST PASSED: Bug is fixed!")
    else:
        print("TEST FAILED: Bug confirmed (expected on unfixed code)")
    print("=" * 60)
    sys.exit(0 if success else 1)