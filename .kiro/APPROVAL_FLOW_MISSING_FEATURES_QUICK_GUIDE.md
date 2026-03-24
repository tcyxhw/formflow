# 审批流程缺失功能快速指南

**生成时间**: 2026-03-16  
**优先级**: 立即执行  
**预计工作量**: 8-12 小时

---

## 🎯 5 个必须实现的功能

### 1️⃣ WorkflowOperationLog 表（P0 - 2-3 小时）

**目的**: 记录审批流程中的所有操作（提交、审批、驳回等）

**需要创建的文件**:

#### 1.1 迁移脚本
**文件**: `backend/alembic/versions/010_create_workflow_operation_log.py`

```python
"""Create workflow_operation_log table"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'workflow_operation_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('process_instance_id', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(20), nullable=False),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('comment', sa.String(500), nullable=True),
        sa.Column('detail_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['process_instance_id'], ['process_instance.id']),
        sa.ForeignKeyConstraint(['operator_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_instance_created', 'workflow_operation_log', 
                    ['process_instance_id', 'created_at'])

def downgrade():
    op.drop_index('idx_instance_created', 'workflow_operation_log')
    op.drop_table('workflow_operation_log')
```

#### 1.2 ORM 模型
**文件**: `backend/app/models/workflow.py` - 添加到文件末尾

```python
class WorkflowOperationLog(DBBaseModel):
    """流程操作日志表"""
    __tablename__ = "workflow_operation_log"
    __table_args__ = (
        Index("idx_instance_created", "process_instance_id", "created_at"),
    )

    process_instance_id = Column(Integer, ForeignKey("process_instance.id"), nullable=False)
    operation_type = Column(String(20), nullable=False, comment="操作类型：SUBMIT/APPROVE/REJECT/CANCEL/CC")
    operator_id = Column(Integer, ForeignKey("user.id"), nullable=False, comment="操作人ID")
    comment = Column(String(500), nullable=True, comment="操作备注")
    detail_json = Column(JSONB, nullable=True, comment="操作详情")
```

---

### 2️⃣ ProcessInstance.form_data_snapshot 字段（P0 - 1-2 小时）

**目的**: 保存表单数据快照，用于审批时间线展示

**需要创建的文件**:

#### 2.1 迁移脚本
**文件**: `backend/alembic/versions/011_add_form_data_snapshot.py`

```python
"""Add form_data_snapshot to process_instance"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.add_column('process_instance', 
        sa.Column('form_data_snapshot', postgresql.JSONB(), nullable=True, 
                  comment="表单数据快照"))

def downgrade():
    op.drop_column('process_instance', 'form_data_snapshot')
```

#### 2.2 更新 ORM 模型
**文件**: `backend/app/models/workflow.py` - ProcessInstance 类中添加

```python
class ProcessInstance(DBBaseModel):
    """流程实例表"""
    # ... 现有字段 ...
    form_data_snapshot = Column(JSONB, nullable=True, comment="表单数据快照")
```

---

### 3️⃣ Task 表扩展字段（P0 - 1-2 小时）

**目的**: 支持 CC 节点和审批意见记录

**需要创建的文件**:

#### 3.1 迁移脚本
**文件**: `backend/alembic/versions/012_extend_task_table.py`

```python
"""Extend task table with task_type and comment"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('task', 
        sa.Column('task_type', sa.String(20), default='approve', 
                  comment="任务类型：approve/cc"))
    op.add_column('task', 
        sa.Column('comment', sa.String(500), nullable=True, 
                  comment="审批意见"))

def downgrade():
    op.drop_column('task', 'comment')
    op.drop_column('task', 'task_type')
```

#### 3.2 更新 ORM 模型
**文件**: `backend/app/models/workflow.py` - Task 类中添加

```python
class Task(DBBaseModel):
    """待办任务表"""
    # ... 现有字段 ...
    task_type = Column(String(20), default="approve", comment="任务类型：approve/cc")
    comment = Column(String(500), nullable=True, comment="审批意见")
```

---

### 4️⃣ 表单字段 API（P0 - 2-3 小时）

**目的**: 前端条件构造器获取表单字段

**需要修改的文件**: `backend/app/api/v1/forms.py`

#### 4.1 添加端点

```python
@router.get("/{form_id}/fields", summary="获取表单字段")
async def get_form_fields(
    form_id: int = Path(..., ge=1, description="表单ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """获取表单字段列表，用于条件构造器"""
    
    form = db.query(Form).filter(
        Form.id == form_id,
        Form.tenant_id == tenant_id,
    ).first()
    
    if not form:
        raise NotFoundError("表单不存在")
    
    # 解析表单配置获取字段
    fields = []
    if form.config:
        for field in form.config.get("fields", []):
            fields.append({
                "key": field.get("key"),
                "name": field.get("name"),
                "type": field.get("type"),
                "options": field.get("options", []),
                "isSystem": False,
            })
    
    # 添加系统字段
    system_fields = [
        {"key": "sys_submitter", "name": "提交人", "type": "USER", "isSystem": True},
        {"key": "sys_submitter_dept", "name": "提交人部门", "type": "TEXT", "isSystem": True},
        {"key": "sys_submit_time", "name": "提交时间", "type": "DATE", "isSystem": True},
    ]
    fields.extend(system_fields)
    
    return success_response(data={"fields": fields})
```

---

### 5️⃣ CC 节点业务逻辑（P1 - 3-4 小时）

**目的**: 支持抄送功能

**需要修改的文件**: `backend/app/services/process_service.py`

#### 5.1 在 _dispatch_nodes() 中添加 CC 处理

```python
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
    """按照节点类型生成任务或继续路由。"""
    
    tasks: List[Task] = []
    
    # ... 现有代码 ...
    
    for node in candidate_nodes:
        if node.id in visited:
            continue
        visited.add(node.id)
        
        # ... 现有的 end/auto/condition 处理 ...
        
        # 添加 CC 节点处理
        if node.type == "cc":
            ProcessService._create_cc_tasks(process, node, tenant_id, db)
            # CC 节点后继续推进流程
            cc_next = ProcessService._resolve_next_nodes(
                flow_definition_id=process.flow_definition_id,
                from_node=node,
                tenant_id=tenant_id,
                db=db,
                context=context,
            )
            tasks.extend(
                ProcessService._dispatch_nodes(
                    process=process,
                    candidate_nodes=cc_next,
                    tenant_id=tenant_id,
                    db=db,
                    context=context,
                    visited=visited,
                    origin_node=node,
                )
            )
            continue
        
        # ... 现有的 user 节点处理 ...
    
    return tasks
```

#### 5.2 添加 _create_cc_tasks() 方法

```python
@staticmethod
def _create_cc_tasks(
    process: ProcessInstance,
    node: FlowNode,
    tenant_id: int,
    db: Session,
) -> List[Task]:
    """为 CC 节点创建抄送任务"""
    
    cc_tasks = []
    
    # 获取抄送人列表
    assignee_user_ids = AssignmentService.select_cc_assignees(node, tenant_id, db)
    
    for user_id in assignee_user_ids:
        task = Task(
            tenant_id=tenant_id,
            process_instance_id=process.id,
            node_id=node.id,
            assignee_user_id=user_id,
            task_type="cc",  # 标记为抄送任务
            due_at=SLAService.calculate_due_at(node.sla_hours),
        )
        db.add(task)
        cc_tasks.append(task)
    
    return cc_tasks
```

---

## 📋 实现检查清单

### 第一阶段（数据库）

- [ ] 创建 `010_create_workflow_operation_log.py` 迁移脚本
- [ ] 创建 `011_add_form_data_snapshot.py` 迁移脚本
- [ ] 创建 `012_extend_task_table.py` 迁移脚本
- [ ] 在 `workflow.py` 中添加 WorkflowOperationLog 模型
- [ ] 在 `workflow.py` 中添加 form_data_snapshot 字段
- [ ] 在 `workflow.py` 中添加 task_type 和 comment 字段
- [ ] 运行迁移脚本：`alembic upgrade head`

### 第二阶段（API）

- [ ] 在 `forms.py` 中添加 `/fields` 端点
- [ ] 测试表单字段 API
- [ ] 验证返回格式正确

### 第三阶段（业务逻辑）

- [ ] 在 `process_service.py` 中添加 CC 节点处理
- [ ] 实现 `_create_cc_tasks()` 方法
- [ ] 在 AssignmentService 中添加 `select_cc_assignees()` 方法
- [ ] 编写单元测试

### 第四阶段（日志记录）

- [ ] 在审批操作时记录到 WorkflowOperationLog
- [ ] 在流程启动时保存 form_data_snapshot
- [ ] 在任务完成时保存审批意见

---

## 🧪 测试验证

### 数据库迁移测试

```bash
# 运行迁移
alembic upgrade head

# 验证表结构
psql -c "\d workflow_operation_log"
psql -c "\d process_instance" | grep form_data_snapshot
psql -c "\d task" | grep task_type
```

### API 测试

```bash
# 测试表单字段 API
curl -X GET http://localhost:8000/api/v1/forms/1/fields \
  -H "Authorization: Bearer <token>"

# 预期响应
{
  "code": 0,
  "data": {
    "fields": [
      {"key": "amount", "name": "报销金额", "type": "NUMBER", "isSystem": false},
      {"key": "sys_submitter", "name": "提交人", "type": "USER", "isSystem": true}
    ]
  }
}
```

### 业务逻辑测试

```python
# 测试 CC 节点
def test_cc_node_creates_tasks():
    # 创建包含 CC 节点的流程
    # 启动流程
    # 验证是否创建了抄送任务
    pass

# 测试操作日志记录
def test_operation_log_recorded():
    # 执行审批操作
    # 验证是否记录到 WorkflowOperationLog
    pass
```

---

## 📊 优先级和时间表

| 功能 | 优先级 | 工作量 | 开始时间 | 完成时间 |
|-----|--------|--------|---------|---------|
| WorkflowOperationLog | P0 | 2-3h | Day 1 | Day 1 |
| form_data_snapshot | P0 | 1-2h | Day 1 | Day 1 |
| Task 扩展字段 | P0 | 1-2h | Day 1 | Day 1 |
| 表单字段 API | P0 | 2-3h | Day 2 | Day 2 |
| CC 节点逻辑 | P1 | 3-4h | Day 3 | Day 3 |
| **总计** | - | **8-12h** | - | **Day 3** |

---

## 🔗 相关文件

- 设计文档：`.kiro/APPROVAL_FLOW_COMPLETION_DESIGN_PART1.md`
- 实现分析：`.kiro/APPROVAL_FLOW_IMPLEMENTATION_ANALYSIS.md`
- 后端模型：`backend/app/models/workflow.py`
- 后端服务：`backend/app/services/process_service.py`
- 后端 API：`backend/app/api/v1/forms.py`、`backend/app/api/v1/approvals.py`

---

**准备好开始实现了吗？** 按照上述步骤逐一完成，预计 3 天内可全部完成！
