# 审批流程优化实施方案

## 一、条件表达式格式统一方案

### 问题分析

**前端生成的格式**（设计格式）：
```json
{
  "type": "GROUP",
  "logic": "AND",
  "children": [
    {
      "type": "RULE",
      "fieldKey": "amount",
      "fieldType": "NUMBER",
      "operator": "GREATER_THAN",
      "value": 10000
    }
  ]
}
```

**后端评估的格式**（JsonLogic）：
```json
{
  "and": [
    { ">=": [{ "var": "amount" }, 10000] }
  ]
}
```

### 解决方案

**方案 A：统一为设计格式（推荐）**
- 优点：更易读、更易维护、与设计文档一致
- 缺点：需要重写后端条件评估器
- 工作量：中等

**方案 B：统一为 JsonLogic 格式**
- 优点：后端已有实现
- 缺点：前端条件构造器需要改造
- 工作量：中等

**推荐选择**：方案 A（统一为设计格式）

### 实施步骤

1. **后端实现新的条件评估器**
   ```python
   class ConditionEvaluator:
       @staticmethod
       def evaluate(condition: Dict, data: Dict) -> bool:
           """评估设计格式的条件树"""
           if condition['type'] == 'RULE':
               return ConditionEvaluator._evaluate_rule(condition, data)
           elif condition['type'] == 'GROUP':
               return ConditionEvaluator._evaluate_group(condition, data)
   ```

2. **前端条件构造器保持不变**
   - 已经生成设计格式

3. **迁移现有 JsonLogic 条件**
   - 编写转换脚本
   - 将数据库中的 JsonLogic 条件转换为设计格式

---

## 二、CONDITION 节点类型实现方案

### 数据库变更

```python
# 在 FlowNode 中添加字段
class FlowNode(DBBaseModel):
    # 现有字段...
    
    # 新增：条件分支配置（仅 CONDITION 节点使用）
    condition_branches = Column(JSON, nullable=True, comment="条件分支配置")
    # 格式：
    # {
    #   "branches": [
    #     {
    #       "priority": 1,
    #       "label": "大额招待费",
    #       "condition": { ... },
    #       "target_node_id": 123
    #     }
    #   ],
    #   "default_target_node_id": 456
    # }
```

### 后端逻辑实现

```python
class ProcessService:
    @staticmethod
    def _dispatch_nodes(...):
        """处理 CONDITION 节点"""
        if node.type == 'condition':
            branches = node.condition_branches.get('branches', [])
            # 按 priority 排序
            branches.sort(key=lambda b: b['priority'])
            
            for branch in branches:
                condition = branch['condition']
                if ConditionEvaluator.evaluate(condition, context):
                    target_node_id = branch['target_node_id']
                    # 继续推进到目标节点
                    return ProcessService._dispatch_nodes(
                        [target_node], ...
                    )
            
            # 所有分支都不匹配，走默认路由
            default_target_id = node.condition_branches.get('default_target_node_id')
            # ...
```

### 前端类型更新

```typescript
// 在 flow.ts 中更新 FlowNodeConfig
export interface FlowNodeConfig {
  // 现有字段...
  
  // 新增：条件分支（仅 CONDITION 节点使用）
  condition_branches?: {
    branches: Array<{
      priority: number
      label: string
      condition: ConditionNode
      target_node_key: string
    }>
    default_target_node_key: string
  }
}
```

### 校验规则

```python
# 在 flow_service.py 中添加
@staticmethod
def _validate_condition_node_config(nodes: List[Dict]) -> None:
    """校验 CONDITION 节点配置"""
    for node in nodes:
        if node.get('type') == 'condition':
            branches = node.get('condition_branches', {}).get('branches', [])
            if len(branches) < 2:
                raise BusinessError(f"{node['name']} 必须至少有 2 条分支")
            
            # 校验每个分支的条件表达式
            for branch in branches:
                condition = branch.get('condition')
                if not condition:
                    raise BusinessError(f"{node['name']} 的分支 {branch['label']} 缺少条件")
```

---

## 三、驳回策略实现方案

### 数据库变更

```python
class FlowNode(DBBaseModel):
    # 现有字段...
    
    # 新增：驳回策略（仅 APPROVAL 节点使用）
    reject_strategy = Column(
        String(20),
        default='TO_START',
        comment="驳回策略：TO_START/TO_PREVIOUS"
    )
```

### 后端逻辑实现

```python
class TaskService:
    @staticmethod
    def reject_task(task_id: int, comment: str, db: Session):
        """处理任务驳回"""
        task = db.query(Task).filter(Task.id == task_id).first()
        process = task.process_instance
        node = task.node
        
        # 更新任务状态
        task.status = 'rejected'
        task.action = 'reject'
        task.comment = comment
        
        # 根据驳回策略处理
        if node.reject_strategy == 'TO_START':
            # 驳回到发起人
            process.state = 'rejected'
            # 通知发起人
        elif node.reject_strategy == 'TO_PREVIOUS':
            # 驳回到上一个审批节点
            previous_node = TaskService._find_previous_approval_node(process, node, db)
            if previous_node:
                # 重新派发任务给上一个节点
                ProcessService._create_task_for_node(process, previous_node, ...)
            else:
                # 找不到上一个节点，按 TO_START 处理
                process.state = 'rejected'
```

---

## 四、审批操作 API 实现方案

### 新增 API 端点

```python
# backend/app/api/v1/approvals.py

@router.post("/tasks/{task_id}/approve")
async def approve_task(
    task_id: int,
    request: ApproveTaskRequest,  # { comment: str }
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """审批通过"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    # 权限检查
    if task.assignee_user_id != current_user.id:
        raise AuthorizationError("无权操作此任务")
    
    # 更新任务
    task.status = 'approved'
    task.action = 'approve'
    task.comment = request.comment
    task.completed_by = current_user.id
    task.completed_at = datetime.now()
    
    # 继续推进流程
    process = task.process_instance
    node = task.node
    ProcessService.advance_from_node(process, node, ...)
    
    db.commit()
    return success_response(message="已通过")

@router.post("/tasks/{task_id}/reject")
async def reject_task(
    task_id: int,
    request: RejectTaskRequest,  # { comment: str }
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """审批驳回"""
    # 类似 approve_task，但调用驳回逻辑

@router.post("/instances/{instance_id}/cancel")
async def cancel_instance(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发起人撤回"""
    process = db.query(ProcessInstance).filter(ProcessInstance.id == instance_id).first()
    
    # 权限检查：只有发起人可以撤回
    submission = process.submission
    if submission.created_by != current_user.id:
        raise AuthorizationError("只有发起人可以撤回")
    
    # 取消所有待处理任务
    db.query(Task).filter(
        Task.process_instance_id == instance_id,
        Task.status == 'open'
    ).update({'status': 'canceled'})
    
    # 更新流程状态
    process.state = 'canceled'
    
    db.commit()
    return success_response(message="已撤回")
```

---

## 五、表单字段 API 实现方案

### 新增 API 端点

```python
# backend/app/api/v1/forms.py

@router.get("/{form_id}/fields")
async def get_form_fields(
    form_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取表单字段列表"""
    form = db.query(Form).filter(Form.id == form_id).first()
    
    # 获取表单的最新版本
    form_version = db.query(FormVersion).filter(
        FormVersion.form_id == form_id
    ).order_by(FormVersion.version.desc()).first()
    
    # 解析字段定义
    fields = []
    for field_def in form_version.fields:
        fields.append({
            'key': field_def['key'],
            'name': field_def['name'],
            'type': field_def['type'],
            'options': field_def.get('options'),
            'isSystem': False
        })
    
    # 添加系统字段
    system_fields = [
        {
            'key': 'sys_submitter',
            'name': '提交人',
            'type': 'USER',
            'isSystem': True
        },
        {
            'key': 'sys_submitter_dept',
            'name': '提交人部门',
            'type': 'DEPARTMENT',
            'isSystem': True
        },
        {
            'key': 'sys_submit_time',
            'name': '提交时间',
            'type': 'DATETIME',
            'isSystem': True
        }
    ]
    fields.extend(system_fields)
    
    return success_response(data=fields)
```

---

## 六、流程设计器 UI 实现方案

### 组件结构

```
FlowDesigner.vue (主容器)
├── FlowCanvas.vue (画布)
│   ├── 节点渲染
│   ├── 连线渲染
│   └── 拖拽交互
├── FlowNodeInspector.vue (节点检查器)
│   ├── 基本信息编辑
│   ├── 审批人配置
│   └── 条件配置（CONDITION 节点）
├── FlowRouteInspector.vue (路由检查器)
│   └── 条件编辑
└── FlowNodePalette.vue (节点调色板)
    └── 节点类型选择
```

### 核心功能

1. **画布交互**
   - 节点拖拽
   - 连线绘制
   - 节点删除
   - 连线删除

2. **节点编辑**
   - 基本信息（名称、类型）
   - 审批人配置（类型、值）
   - 驳回策略（APPROVAL 节点）
   - 条件分支（CONDITION 节点）

3. **路由编辑**
   - 条件表达式编辑
   - 优先级设置
   - 默认路由设置

---

## 七、实施时间表

| 阶段 | 任务 | 工作量 | 时间 |
|------|------|--------|------|
| P0-1 | 条件表达式格式统一 | 3d | 第1周 |
| P0-2 | CONDITION 节点实现 | 3d | 第1周 |
| P0-3 | 驳回策略实现 | 2d | 第2周 |
| P0-4 | 审批操作 API | 3d | 第2周 |
| P1-1 | 表单字段 API | 1d | 第2周 |
| P1-2 | 流程设计器 UI | 5d | 第3周 |
| P1-3 | 条件评估器完善 | 2d | 第3周 |
| P1-4 | 查询接口实现 | 3d | 第4周 |

**总计**：约 22 个工作日（4-5 周）

---

## 八、测试策略

### 单元测试

1. 条件评估器
   - 所有 15 种运算符
   - 类型转换
   - 嵌套条件

2. 路由推进
   - CONDITION 节点分支
   - 默认路由
   - 优先级排序

3. 驳回处理
   - TO_START 策略
   - TO_PREVIOUS 策略

### 集成测试

1. 完整流程
   - 创建流程 → 发布 → 提交 → 审批 → 完成

2. 条件分支
   - 多条件分支 → 正确路由

3. 驳回流程
   - 驳回 → 重新审批 → 通过

### 端到端测试

1. 流程设计器
   - 创建节点 → 连线 → 配置 → 保存 → 发布

2. 审批流程
   - 填写表单 → 提交 → 待办 → 审批 → 完成

---

## 九、风险评估

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|--------|
| 条件格式转换失败 | 现有流程无法运行 | 中 | 充分测试、数据备份 |
| CONDITION 节点逻辑复杂 | 性能下降 | 低 | 优化算法、缓存 |
| 前后端不同步 | 功能不可用 | 中 | 充分沟通、集成测试 |
| 数据库迁移失败 | 数据丢失 | 低 | 备份、灰度发布 |

