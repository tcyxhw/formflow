# 第 2 周快速参考指南

## 🎯 核心功能

### 驳回策略 (Reject Strategy)

#### 数据库字段
```sql
ALTER TABLE flow_node ADD COLUMN reject_strategy VARCHAR(20) DEFAULT 'TO_START';
```

#### 前端类型
```typescript
export type RejectStrategy = 'TO_START' | 'TO_PREVIOUS'

export interface FlowNodeConfig {
  reject_strategy: RejectStrategy
  // ... 其他字段
}
```

#### 后端模型
```python
class FlowNode(DBBaseModel):
    reject_strategy = Column(String(20), default="TO_START", comment="驳回策略：TO_START/TO_PREVIOUS")
```

### 驳回处理流程

#### 1. 用户执行驳回操作
```typescript
// 前端
await performTaskAction(taskId, {
  action: 'reject',
  comment: '不符合要求',
  extra_data: { reason: '信息不完整' }
})
```

#### 2. 后端处理驳回
```python
# 后端 API
@router.post("/{task_id}/actions")
async def perform_task_action(task_id, request, current_user, tenant_id, db):
    task = TaskService.perform_task_action(task_id, tenant_id, request, current_user, db)
    # 内部调用 ProcessService.handle_task_completion()
```

#### 3. 驳回策略执行
```python
# ProcessService._handle_rejection()
if reject_strategy == 'TO_PREVIOUS':
    # 驳回到上一个审批节点
    previous_node = ProcessService._find_previous_approval_node(...)
    if previous_node:
        ProcessService._dispatch_nodes(...)  # 重新创建任务
else:
    # 默认驳回到开始节点 (TO_START)
    process.state = "canceled"
    ProcessService._update_submission_status(...)
```

## 📋 API 端点

### 审批操作

#### 执行审批动作
```
POST /api/v1/approvals/{task_id}/actions
Content-Type: application/json

{
  "action": "approve" | "reject",
  "comment": "审批意见",
  "extra_data": { ... }
}

Response:
{
  "code": 0,
  "data": { TaskResponse },
  "message": "操作成功"
}
```

#### 认领任务
```
POST /api/v1/approvals/{task_id}/claim
```

#### 释放任务
```
POST /api/v1/approvals/{task_id}/release
```

#### 转交任务
```
POST /api/v1/approvals/{task_id}/transfer
{
  "target_user_id": 123,
  "message": "转交说明"
}
```

#### 委托任务
```
POST /api/v1/approvals/{task_id}/delegate
{
  "delegate_user_id": 123,
  "expire_hours": 24,
  "message": "委托说明"
}
```

#### 加签任务
```
POST /api/v1/approvals/{task_id}/add-sign
{
  "user_ids": [123, 456],
  "message": "加签说明"
}
```

### 查询接口

#### 查询待办任务
```
GET /api/v1/approvals?page=1&page_size=20&status=open&only_mine=true
```

#### 查询 SLA 分布
```
GET /api/v1/approvals/summary?status=open&only_mine=true
```

#### 查询小组待办池
```
GET /api/v1/approvals/group?page=1&page_size=20
```

#### 查询流程轨迹
```
GET /api/v1/approvals/processes/{process_instance_id}/timeline
```

## 🔧 前端集成

### 导入 API
```typescript
import {
  performTaskAction,
  claimTask,
  releaseTask,
  transferTask,
  delegateTask,
  addSignTask,
  listTasks,
  getProcessTimeline
} from '@/api/approvals'
```

### 导入类型
```typescript
import type {
  TaskResponse,
  TaskActionRequest,
  TaskListResponse,
  ProcessTimelineResponse
} from '@/types/approval'
```

### 使用示例
```typescript
// 通过任务
await performTaskAction(taskId, {
  action: 'approve',
  comment: '同意'
})

// 驳回任务
await performTaskAction(taskId, {
  action: 'reject',
  comment: '不符合要求'
})

// 查询待办
const { data } = await listTasks({
  page: 1,
  page_size: 20,
  only_mine: true
})

// 查询流程轨迹
const { data } = await getProcessTimeline(processInstanceId)
```

## 🧪 测试

### 后端测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_approval_api.py -v

# 运行特定测试函数
pytest tests/test_approval_api.py::test_approve_task -v
```

### 前端测试
```bash
# 运行单元测试
npm run test

# 运行特定测试
npm run test -- approvals.spec.ts
```

## 📊 数据流

### 驳回流程数据流
```
用户点击驳回
    ↓
前端调用 performTaskAction(taskId, { action: 'reject', ... })
    ↓
后端 API: POST /api/v1/approvals/{task_id}/actions
    ↓
TaskService.perform_task_action()
    ↓
更新 Task: status=completed, action=reject
    ↓
ProcessService.handle_task_completion()
    ↓
ProcessService._evaluate_approve_policy() → decision="reject"
    ↓
ProcessService._handle_rejection()
    ↓
检查 reject_strategy
    ├─ TO_START: 流程状态 → canceled, 提交状态 → REJECTED
    └─ TO_PREVIOUS: 查找上一个节点 → 重新创建任务
    ↓
返回更新后的 Task 信息
    ↓
前端更新 UI
```

## 🔐 权限检查

### 审批权限
```python
def _ensure_can_act(task, current_user, tenant_id, db):
    """检查用户是否有权执行审批操作"""
    # 1. 检查任务是否属于当前租户
    # 2. 检查用户是否是任务的指派人或认领人
    # 3. 检查任务状态是否允许操作
```

## 📝 关键代码位置

### 后端
- 驳回处理: `backend/app/services/process_service.py` (Line 435-520)
- 审批 API: `backend/app/api/v1/approvals.py` (Line 1-300)
- 任务服务: `backend/app/services/approval_service.py` (Line 350-410)

### 前端
- 审批 API: `my-app/src/api/approvals.ts`
- 审批类型: `my-app/src/types/approval.ts`
- 流程类型: `my-app/src/types/flow.ts`
- 审批页面: `my-app/src/views/approvals/ApprovalListView.vue`

## 🚀 部署检查清单

- [ ] 数据库迁移已执行 (`alembic upgrade head`)
- [ ] 后端代码已部署
- [ ] 前端代码已构建
- [ ] 环境变量已配置
- [ ] 单元测试全部通过
- [ ] 集成测试全部通过
- [ ] 代码审查已完成
- [ ] 文档已更新

## 📞 常见问题

### Q: 如何修改驳回策略？
A: 在流程设计器中编辑节点，选择 `reject_strategy` 字段，选择 `TO_START` 或 `TO_PREVIOUS`。

### Q: 驳回到上一个节点时，如何处理多个审批人？
A: 系统会查找最后一个已完成的任务所在的节点，重新为该节点的所有审批人创建任务。

### Q: 驳回后流程状态是什么？
A: 
- TO_START: 流程状态为 "canceled"，提交状态为 "REJECTED"
- TO_PREVIOUS: 流程状态保持 "running"，重新创建任务

### Q: 如何查看驳回历史？
A: 调用 `getProcessTimeline(processInstanceId)` 查询流程轨迹，可以看到所有的驳回操作。

## 🔗 相关文档

- 完整总结: `.kiro/APPROVAL_FLOW_WEEK2_COMPLETE.md`
- 第一阶段计划: `.kiro/IMPLEMENTATION_PHASE_1.md`
- 第二阶段计划: `.kiro/IMPLEMENTATION_PHASE_2.md`
- 系统设计: `.kiro/specs/approval-flow-optimization/design.md`
- 功能需求: `.kiro/specs/approval-flow-optimization/requirements.md`
