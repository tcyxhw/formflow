# 审批流程完善设计方案 - 第三部分

## 十、表单字段 API 实现详设

### 10.1 字段定义数据结构

```python
class FormFieldResponse(BaseModel):
    key: str
    name: str
    type: str  # TEXT/NUMBER/SINGLE_SELECT/MULTI_SELECT/DATE/DATETIME/USER/DEPARTMENT
    options: Optional[List[Dict]] = None
    isSystem: bool = False
    required: bool = False
    description: Optional[str] = None
```

### 10.2 API 实现

```python
# backend/app/api/v1/forms.py

@router.get("/{form_id}/fields")
async def get_form_fields(
    form_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """获取表单字段列表"""
    
    # 1. 查表单
    form = db.query(Form).filter(
        Form.id == form_id,
        Form.tenant_id == current_user.tenant_id,
    ).first()
    
    if not form:
        raise NotFoundError("表单不存在")
    
    # 2. 查表单版本
    form_version = db.query(FormVersion).filter(
        FormVersion.form_id == form_id,
    ).order_by(FormVersion.version.desc()).first()
    
    if not form_version:
        raise NotFoundError("表单版本不存在")
    
    # 3. 解析字段
    fields = []
    
    # 从 form_version.schema 中提取字段
    schema = form_version.schema or {}
    form_fields = schema.get("fields", [])
    
    for field in form_fields:
        field_response = FormFieldResponse(
            key=field.get("key"),
            name=field.get("name"),
            type=field.get("type"),
            options=field.get("options"),
            isSystem=False,
            required=field.get("required", False),
            description=field.get("description"),
        )
        fields.append(field_response)
    
    # 4. 添加系统字段
    system_fields = [
        FormFieldResponse(
            key="sys_submitter",
            name="提交人",
            type="USER",
            isSystem=True,
        ),
        FormFieldResponse(
            key="sys_submitter_dept",
            name="提交人部门",
            type="DEPARTMENT",
            isSystem=True,
        ),
        FormFieldResponse(
            key="sys_submit_time",
            name="提交时间",
            type="DATETIME",
            isSystem=True,
        ),
    ]
    
    fields.extend(system_fields)
    
    return success_response(data=fields)
```

---

## 十一、查询接口实现详设

### 11.1 待办列表

```python
@router.get("/pending")
async def get_pending_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """待办列表"""
    
    query = db.query(Task, ProcessInstance, Form).join(
        ProcessInstance, ProcessInstance.id == Task.process_instance_id
    ).join(
        Form, Form.id == ProcessInstance.form_id
    ).filter(
        Task.assignee_user_id == current_user.id,
        Task.status == "open",
        Task.task_type == "approve",
        Task.tenant_id == current_user.tenant_id,
    ).order_by(Task.created_at.desc())
    
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    
    result = []
    for task, instance, form in items:
        result.append({
            "task_id": task.id,
            "instance_id": instance.id,
            "form_id": form.id,
            "form_name": form.name,
            "form_data": instance.form_data_snapshot,
            "created_at": task.created_at,
            "due_at": task.due_at,
        })
    
    return success_response(data={
        "items": result,
        "total": total,
        "page": page,
        "size": size,
    })
```

### 11.2 已办列表

```python
@router.get("/completed")
async def get_completed_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """已办列表"""
    
    query = db.query(Task, ProcessInstance, Form).join(
        ProcessInstance, ProcessInstance.id == Task.process_instance_id
    ).join(
        Form, Form.id == ProcessInstance.form_id
    ).filter(
        Task.assignee_user_id == current_user.id,
        Task.status == "completed",
        Task.task_type == "approve",
        Task.tenant_id == current_user.tenant_id,
    ).order_by(Task.completed_at.desc())
    
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    
    result = []
    for task, instance, form in items:
        result.append({
            "task_id": task.id,
            "instance_id": instance.id,
            "form_id": form.id,
            "form_name": form.name,
            "form_data": instance.form_data_snapshot,
            "action": task.action,
            "comment": task.comment,
            "completed_at": task.completed_at,
        })
    
    return success_response(data={
        "items": result,
        "total": total,
        "page": page,
        "size": size,
    })
```

### 11.3 我发起的

```python
@router.get("/initiated")
async def get_initiated_instances(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """我发起的"""
    
    # 从 submission 表查找发起人
    query = db.query(ProcessInstance, Form, Submission).join(
        Form, Form.id == ProcessInstance.form_id
    ).join(
        Submission, Submission.id == ProcessInstance.submission_id
    ).filter(
        Submission.created_by == current_user.id,
        ProcessInstance.tenant_id == current_user.tenant_id,
    ).order_by(ProcessInstance.created_at.desc())
    
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    
    result = []
    for instance, form, submission in items:
        result.append({
            "instance_id": instance.id,
            "form_id": form.id,
            "form_name": form.name,
            "form_data": instance.form_data_snapshot,
            "state": instance.state,
            "created_at": instance.created_at,
        })
    
    return success_response(data={
        "items": result,
        "total": total,
        "page": page,
        "size": size,
    })
```

### 11.4 审批时间线

```python
@router.get("/instances/{instance_id}/timeline")
async def get_timeline(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """审批时间线"""
    
    # 查流程实例
    instance = db.query(ProcessInstance).filter(
        ProcessInstance.id == instance_id,
        ProcessInstance.tenant_id == current_user.tenant_id,
    ).first()
    
    if not instance:
        raise NotFoundError("流程实例不存在")
    
    # 查操作日志
    logs = db.query(WorkflowOperationLog).filter(
        WorkflowOperationLog.process_instance_id == instance_id,
    ).order_by(WorkflowOperationLog.created_at.asc()).all()
    
    result = []
    for log in logs:
        operator = db.query(User).filter(User.id == log.operator_id).first()
        result.append({
            "time": log.created_at,
            "operator": operator.name if operator else "系统",
            "operation": log.operation_type,
            "comment": log.comment,
            "detail": log.detail_json,
        })
    
    return success_response(data=result)
```

---

## 十二、流程设计器 UI 设计

### 12.1 组件结构

```
FlowDesigner.vue (主容器)
├── FlowCanvas.vue (画布)
│   ├── FlowNode.vue (节点)
│   ├── FlowEdge.vue (连线)
│   └── SelectionBox.vue (选择框)
├── NodeInspector.vue (节点检查器)
│   ├── BasicConfig.vue (基本配置)
│   ├── ApprovalConfig.vue (审批配置)
│   ├── ConditionConfig.vue (条件配置)
│   └── CCConfig.vue (抄送配置)
├── RouteInspector.vue (路由检查器)
│   └── ConditionEditor.vue (条件编辑)
├── NodePalette.vue (节点调色板)
└── Toolbar.vue (工具栏)
```

### 12.2 画布组件

```typescript
// my-app/src/components/flow-designer/FlowCanvas.vue

<template>
  <div class="flow-canvas" ref="canvasRef">
    <!-- 网格背景 -->
    <svg class="grid-background">
      <!-- 网格线 -->
    </svg>
    
    <!-- 连线 -->
    <svg class="edges-layer">
      <FlowEdge 
        v-for="edge in edges" 
        :key="edge.id"
        :edge="edge"
        @click="selectEdge"
      />
    </svg>
    
    <!-- 节点 -->
    <div class="nodes-layer">
      <FlowNode 
        v-for="node in nodes" 
        :key="node.id"
        :node="node"
        :selected="selectedNodeId === node.id"
        @click="selectNode"
        @drag="dragNode"
      />
    </div>
    
    <!-- 选择框 -->
    <SelectionBox 
      v-if="selectionBox"
      :box="selectionBox"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import FlowNode from './FlowNode.vue'
import FlowEdge from './FlowEdge.vue'
import SelectionBox from './SelectionBox.vue'

const canvasRef = ref<HTMLElement>()
const nodes = ref([])
const edges = ref([])
const selectedNodeId = ref<number | null>(null)
const selectionBox = ref(null)

// 拖拽节点
const dragNode = (nodeId: number, x: number, y: number) => {
  const node = nodes.value.find(n => n.id === nodeId)
  if (node) {
    node.position_x = x
    node.position_y = y
  }
}

// 选择节点
const selectNode = (nodeId: number) => {
  selectedNodeId.value = nodeId
}

// 连线
const connectNodes = (fromNodeId: number, toNodeId: number) => {
  edges.value.push({
    id: `edge_${fromNodeId}_${toNodeId}`,
    from_node_id: fromNodeId,
    to_node_id: toNodeId,
  })
}
</script>
```

### 12.3 节点检查器

```typescript
// my-app/src/components/flow-designer/NodeInspector.vue

<template>
  <div class="node-inspector" v-if="selectedNode">
    <n-tabs>
      <n-tab-pane name="basic" tab="基本信息">
        <BasicConfig :node="selectedNode" @update="updateNode" />
      </n-tab-pane>
      
      <n-tab-pane name="approval" tab="审批配置" v-if="selectedNode.type === 'user'">
        <ApprovalConfig :node="selectedNode" @update="updateNode" />
      </n-tab-pane>
      
      <n-tab-pane name="condition" tab="条件配置" v-if="selectedNode.type === 'condition'">
        <ConditionConfig :node="selectedNode" @update="updateNode" />
      </n-tab-pane>
      
      <n-tab-pane name="cc" tab="抄送配置" v-if="selectedNode.type === 'cc'">
        <CCConfig :node="selectedNode" @update="updateNode" />
      </n-tab-pane>
    </n-tabs>
  </div>
</template>
```

### 12.4 条件配置编辑器

```typescript
// my-app/src/components/flow-designer/ConditionConfig.vue

<template>
  <div class="condition-config">
    <div class="branches-list">
      <div v-for="(branch, idx) in branches" :key="idx" class="branch-item">
        <n-input-number v-model:value="branch.priority" label="优先级" />
        <n-input v-model:value="branch.label" placeholder="分支标签" />
        
        <ConditionBuilderV2 
          v-model="branch.condition"
          :fields="formFields"
        />
        
        <n-select 
          v-model:value="branch.target_node_id"
          :options="nodeOptions"
          placeholder="选择目标节点"
        />
        
        <n-button type="error" @click="removeBranch(idx)">删除</n-button>
      </div>
    </div>
    
    <n-button @click="addBranch">添加分支</n-button>
    
    <div class="default-branch">
      <n-select 
        v-model:value="defaultTargetNodeId"
        :options="nodeOptions"
        placeholder="选择默认分支"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ConditionBuilderV2 from '../flow-configurator/ConditionBuilderV2.vue'

const props = defineProps({
  node: Object,
})

const emit = defineEmits(['update'])

const branches = ref(props.node.condition_branches?.branches || [])
const defaultTargetNodeId = ref(props.node.condition_branches?.default_target_node_id)

const addBranch = () => {
  branches.value.push({
    priority: branches.value.length + 1,
    label: '',
    condition: null,
    target_node_id: null,
  })
}

const removeBranch = (idx: number) => {
  branches.value.splice(idx, 1)
}

const updateNode = () => {
  emit('update', {
    condition_branches: {
      branches: branches.value,
      default_target_node_id: defaultTargetNodeId.value,
    }
  })
}
</script>
```

---

## 十三、数据库迁移脚本

### 13.1 添加 CONDITION/CC 节点支持

```python
# backend/alembic/versions/009_add_condition_cc_nodes.py

def upgrade():
    op.add_column('flow_node', sa.Column('condition_branches', sa.JSON, nullable=True))
    op.add_column('flow_node', sa.Column('cc_assignee_type', sa.String(20), nullable=True))
    op.add_column('flow_node', sa.Column('cc_assignee_value', sa.JSON, nullable=True))

def downgrade():
    op.drop_column('flow_node', 'condition_branches')
    op.drop_column('flow_node', 'cc_assignee_type')
    op.drop_column('flow_node', 'cc_assignee_value')
```

### 13.2 添加 form_data_snapshot 字段

```python
# backend/alembic/versions/010_add_form_data_snapshot.py

def upgrade():
    op.add_column('process_instance', sa.Column('form_data_snapshot', sa.JSON, nullable=True))

def downgrade():
    op.drop_column('process_instance', 'form_data_snapshot')
```

### 13.3 添加 Task 表扩展字段

```python
# backend/alembic/versions/011_extend_task_table.py

def upgrade():
    op.add_column('task', sa.Column('task_type', sa.String(20), default='approve'))
    op.add_column('task', sa.Column('comment', sa.String(500), nullable=True))

def downgrade():
    op.drop_column('task', 'task_type')
    op.drop_column('task', 'comment')
```

### 13.4 创建 WorkflowOperationLog 表

```python
# backend/alembic/versions/012_create_workflow_operation_log.py

def upgrade():
    op.create_table(
        'workflow_operation_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('tenant_id', sa.Integer, nullable=False),
        sa.Column('process_instance_id', sa.Integer, sa.ForeignKey('process_instance.id'), nullable=False),
        sa.Column('operation_type', sa.String(20), nullable=False),
        sa.Column('operator_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False),
        sa.Column('comment', sa.String(500), nullable=True),
        sa.Column('detail_json', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
    )
    op.create_index('idx_instance_created', 'workflow_operation_log', ['process_instance_id', 'created_at'])

def downgrade():
    op.drop_table('workflow_operation_log')
```

---

## 十四、集成测试场景

### 14.1 CONDITION 节点测试

```python
def test_condition_node_routing():
    """测试条件节点路由"""
    # 1. 创建流程：START → CONDITION → APPROVAL1/APPROVAL2 → END
    # 2. 配置条件：amount > 10000 → APPROVAL1，否则 → APPROVAL2
    # 3. 提交表单：amount = 15000
    # 4. 验证：流程路由到 APPROVAL1
```

### 14.2 CC 节点测试

```python
def test_cc_node_task_creation():
    """测试抄送节点任务创建"""
    # 1. 创建流程：START → APPROVAL → CC → END
    # 2. 配置抄送：抄送给用户 1001, 1002
    # 3. 提交表单
    # 4. 验证：为 1001, 1002 创建了抄送任务
```

### 14.3 审批操作测试

```python
def test_approve_task():
    """测试审批通过"""
    # 1. 创建流程实例和任务
    # 2. 调用 approve_task API
    # 3. 验证：任务状态变为 completed，流程推进

def test_reject_task_to_start():
    """测试驳回到发起人"""
    # 1. 创建流程实例和任务
    # 2. 配置驳回策略：TO_START
    # 3. 调用 reject_task API
    # 4. 验证：流程状态变为 canceled

def test_reject_task_to_previous():
    """测试驳回到上一个审批节点"""
    # 1. 创建流程：START → APPROVAL1 → APPROVAL2 → END
    # 2. APPROVAL2 配置驳回策略：TO_PREVIOUS
    # 3. 提交表单，通过 APPROVAL1
    # 4. 在 APPROVAL2 驳回
    # 5. 验证：重新创建 APPROVAL1 的任务
```

