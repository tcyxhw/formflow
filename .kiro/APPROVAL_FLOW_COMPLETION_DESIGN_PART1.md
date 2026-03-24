# 审批流程完善设计方案 - 第一部分

## 一、概述

本设计方案基于当前代码实现，完善剩余的 40% 功能。包括：
- CONDITION 节点类型实现
- CC 节点类型实现
- 审批操作 API 实现
- 表单字段 API 实现
- 查询接口实现
- 条件表达式格式统一
- 流程设计器 UI 实现

---

## 二、数据模型扩展

### 2.1 FlowNode 表扩展

**当前字段**：
```python
type = Column(String(20))  # start/user/auto/end
```

**扩展方案**：
```python
# 在 FlowNode 中添加
type = Column(String(20))  # start/user/auto/end/condition/cc

# 对于 CONDITION 节点
condition_branches = Column(JSONB, nullable=True, comment="条件分支配置")
# 格式：{
#   "branches": [
#     {
#       "priority": 1,
#       "label": "大额招待费",
#       "condition": { "type": "GROUP", ... },
#       "target_node_id": 123
#     }
#   ],
#   "default_target_node_id": 456
# }

# 对于 CC 节点
cc_assignee_type = Column(String(20), nullable=True)  # user/group/role/department/position
cc_assignee_value = Column(JSON, nullable=True)  # 抄送人配置
```

### 2.2 ProcessInstance 表扩展

**添加字段**：
```python
form_data_snapshot = Column(JSONB, nullable=True, comment="表单数据快照")
# 格式：{
#   "amount": 15000,
#   "category": "招待",
#   "sys_submitter": 1001,
#   "sys_submitter_dept": "总裁办",
#   "sys_submit_time": "2024-12-15 10:30:00"
# }
```

### 2.3 Task 表扩展

**添加字段**：
```python
task_type = Column(String(20), default="approve", comment="任务类型：approve/cc")
comment = Column(String(500), nullable=True, comment="审批意见")
```

### 2.4 新增 WorkflowOperationLog 表

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

## 三、后端服务层设计

### 3.1 条件表达式格式转换服务

**文件**：`backend/app/services/condition_converter.py`

**功能**：
- 将设计格式（条件树）转换为 JsonLogic 格式
- 将 JsonLogic 格式转换为设计格式
- 支持双向转换

**核心方法**：
```python
class ConditionConverter:
    @staticmethod
    def tree_to_jsonlogic(tree: Dict) -> Dict:
        """条件树 → JsonLogic"""
        # 递归转换
        
    @staticmethod
    def jsonlogic_to_tree(jsonlogic: Dict) -> Dict:
        """JsonLogic → 条件树"""
        # 递归转换
        
    @staticmethod
    def validate_tree(tree: Dict) -> Tuple[bool, Optional[str]]:
        """验证条件树格式"""
```

### 3.2 条件评估器完善

**文件**：`backend/app/services/condition_evaluator_v2.py`

**扩展运算符**：
- BETWEEN：介于
- HAS_ANY：多选字段包含任一
- HAS_ALL：多选字段包含全部
- DATE_BEFORE_NOW：早于当前时间 X 天
- DATE_AFTER_NOW：晚于当前时间 X 天

**核心方法**：
```python
class ConditionEvaluatorV2:
    @staticmethod
    def evaluate(condition: Dict, data: Dict) -> bool:
        """评估条件树"""
        
    @staticmethod
    def compare(actual, operator, expected, field_type) -> bool:
        """比较函数，支持所有 15 种运算符"""
```

### 3.3 流程推进服务扩展

**文件**：`backend/app/services/process_service.py`

**扩展方法**：
```python
class ProcessService:
    @staticmethod
    def _dispatch_nodes(...) -> List[Task]:
        """扩展支持 CONDITION 和 CC 节点"""
        # 处理 CONDITION 节点
        if node.type == "condition":
            # 评估条件分支
            # 递归调用 executeNode
            
        # 处理 CC 节点
        if node.type == "cc":
            # 创建抄送任务
            # task_type = "cc"
```

### 3.4 审批服务

**文件**：`backend/app/services/approval_service.py`

**新增方法**：
```python
class ApprovalService:
    @staticmethod
    def approve_task(task_id: int, comment: str, user_id: int, db: Session) -> Task:
        """审批通过"""
        # 1. 查任务，校验权限
        # 2. 更新任务状态
        # 3. 记录操作日志
        # 4. 推进流程
        
    @staticmethod
    def reject_task(task_id: int, comment: str, user_id: int, db: Session) -> Task:
        """审批驳回"""
        # 1. 查任务，校验权限
        # 2. 更新任务状态
        # 3. 记录操作日志
        # 4. 处理驳回逻辑
        
    @staticmethod
    def cancel_instance(instance_id: int, user_id: int, db: Session) -> ProcessInstance:
        """撤回申请"""
        # 1. 查实例，校验权限
        # 2. 取消所有待处理任务
        # 3. 更新实例状态
        # 4. 记录操作日志
```

### 3.5 查询服务

**文件**：`backend/app/services/query_service.py`

**新增方法**：
```python
class QueryService:
    @staticmethod
    def get_pending_tasks(user_id: int, page: int, size: int, db: Session) -> Page[Task]:
        """待办列表"""
        
    @staticmethod
    def get_completed_tasks(user_id: int, page: int, size: int, db: Session) -> Page[Task]:
        """已办列表"""
        
    @staticmethod
    def get_initiated_instances(user_id: int, page: int, size: int, db: Session) -> Page[ProcessInstance]:
        """我发起的"""
        
    @staticmethod
    def get_timeline(instance_id: int, db: Session) -> List[WorkflowOperationLog]:
        """审批时间线"""
```

---

## 四、API 层设计

### 4.1 审批操作 API

**文件**：`backend/app/api/v1/approvals.py`

**端点**：
```python
# 审批通过
@router.post("/tasks/{task_id}/approve")
async def approve_task(
    task_id: int,
    request: ApproveRequest,  # { comment: str }
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """审批通过"""
    
# 审批驳回
@router.post("/tasks/{task_id}/reject")
async def reject_task(
    task_id: int,
    request: RejectRequest,  # { comment: str }
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """审批驳回"""
    
# 撤回申请
@router.post("/instances/{instance_id}/cancel")
async def cancel_instance(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """撤回申请"""
```

### 4.2 表单字段 API

**文件**：`backend/app/api/v1/forms.py`

**端点**：
```python
# 获取表单字段
@router.get("/{form_id}/fields")
async def get_form_fields(
    form_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """获取表单字段列表"""
    # 返回：[
    #   { key: "amount", name: "报销金额", type: "NUMBER", options: [] },
    #   { key: "sys_submitter", name: "提交人", type: "USER", isSystem: true }
    # ]
```

### 4.3 查询 API

**文件**：`backend/app/api/v1/approvals.py`

**端点**：
```python
# 待办列表
@router.get("/pending")
async def get_pending_tasks(
    page: int = 1,
    size: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """待办列表"""
    
# 已办列表
@router.get("/completed")
async def get_completed_tasks(
    page: int = 1,
    size: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """已办列表"""
    
# 我发起的
@router.get("/initiated")
async def get_initiated_instances(
    page: int = 1,
    size: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """我发起的"""
    
# 审批时间线
@router.get("/instances/{instance_id}/timeline")
async def get_timeline(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """审批时间线"""
```

---

## 五、前端设计

### 5.1 表单字段 API 集成

**文件**：`my-app/src/api/flow.ts`

```typescript
export async function getFormFields(formId: number) {
  return request.get(`/forms/${formId}/fields`)
}
```

### 5.2 审批操作 API 集成

**文件**：`my-app/src/api/approval.ts`

```typescript
export async function approveTask(taskId: number, comment: string) {
  return request.post(`/approvals/tasks/${taskId}/approve`, { comment })
}

export async function rejectTask(taskId: number, comment: string) {
  return request.post(`/approvals/tasks/${taskId}/reject`, { comment })
}

export async function cancelInstance(instanceId: number) {
  return request.post(`/approvals/instances/${instanceId}/cancel`)
}
```

### 5.3 查询 API 集成

**文件**：`my-app/src/api/approval.ts`

```typescript
export async function getPendingTasks(page: number, size: number) {
  return request.get(`/approvals/pending`, { params: { page, size } })
}

export async function getCompletedTasks(page: number, size: number) {
  return request.get(`/approvals/completed`, { params: { page, size } })
}

export async function getInitiatedInstances(page: number, size: number) {
  return request.get(`/approvals/initiated`, { params: { page, size } })
}

export async function getTimeline(instanceId: number) {
  return request.get(`/approvals/instances/${instanceId}/timeline`)
}
```

### 5.4 流程设计器 UI 组件

**文件**：`my-app/src/components/flow-designer/FlowDesigner.vue`

**主要组件**：
- FlowCanvas.vue - 画布
- FlowNode.vue - 节点
- FlowEdge.vue - 连线
- NodeInspector.vue - 节点检查器
- RouteInspector.vue - 路由检查器
- NodePalette.vue - 节点调色板

