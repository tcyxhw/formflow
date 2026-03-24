# 审批流程全链路设计对照分析报告

## 执行摘要

本报告对比设计文档与现有源码实现，分析 FormFlow 审批流程系统的完善度。

**总体评估**：
- ✅ **核心架构完善**：后端模型、服务、API 基本完整
- ⚠️ **部分功能差异**：设计与实现存在命名、结构差异
- ❌ **关键缺失**：流程实例执行、任务派发、条件评估需优化
- ❌ **前端缺失**：流程设计器、条件构造器 UI 组件未完全集成

---

## 第一部分：数据模型对照

### 1.1 设计要求 vs 实现现状

#### 设计中的表结构

| 表名 | 用途 | 设计字段 |
|------|------|--------|
| workflow_definition | 流程定义 | id, form_id, name, status(DRAFT/PUBLISHED/DISABLED), nodes, edges |
| workflow_node | 流程节点 | id, nodeKey, nodeType, nodeName, nodeConfig, positionX, positionY |
| workflow_edge | 流程连线 | id, sourceNodeKey, targetNodeKey |
| workflow_instance | 流程实例 | id, workflow_id, form_id, form_data_id, status, initiator_id, form_data_snapshot, current_node_key |
| workflow_task | 待办任务 | id, instance_id, node_key, task_type, assignee_id, status |
| workflow_operation_log | 操作日志 | id, instance_id, operation_type, operator_id, comment |

#### 实现中的表结构

| 表名 | 实现字段 | 差异 |
|------|--------|------|
| flow_definition | id, form_id, version, name, active_snapshot_id | ✅ 基本对应，但用版本管理替代 status |
| flow_node | id, flow_definition_id, name, type, assignee_type, assignee_value, approve_policy, sla_hours, auto_approve_enabled | ⚠️ 扩展了会签、SLA、自动审批功能 |
| flow_route | id, from_node_id, to_node_id, priority, condition_json, is_default | ✅ 对应 workflow_edge，但用 ID 而非 nodeKey |
| process_instance | id, form_id, form_version_id, submission_id, flow_definition_id, state | ⚠️ 关联 submission 而非 form_data_id |
| task | id, process_instance_id, node_id, assignee_user_id, status, action, claimed_by, completed_by | ✅ 基本对应，但字段更丰富 |
| task_action_log | id, task_id, actor_user_id, action, detail_json | ⚠️ 关联 task 而非 instance |

**关键差异**：
1. ❌ **缺失 workflow_edge 表**：实现用 flow_route 替代，但 flow_route 包含条件表达式，设计中条件应在 workflow_node.nodeConfig 中
2. ⚠️ **nodeKey vs ID**：设计用字符串 nodeKey，实现用数字 ID
3. ⚠️ **form_data_snapshot**：设计要求存储表单数据快照，实现未见相关字段

---

### 1.2 枚举类型对照

#### 设计中的 11 个枚举

| # | 枚举名 | 设计值 | 实现现状 |
|---|--------|--------|--------|
| ① | FieldType | TEXT/NUMBER/SINGLE_SELECT/MULTI_SELECT/DATE/DATETIME/USER/DEPARTMENT | ✅ 前端 condition.ts 已定义 |
| ② | NodeType | START/APPROVAL/CONDITION/CC/END | ⚠️ 实现用 start/user/auto/end，缺 CONDITION/CC |
| ③ | ApproverType | SPECIFIC_USER/ROLE/DEPARTMENT_HEAD/FORM_FIELD | ⚠️ 实现用 user/group/role/department/position/expr |
| ④ | RejectStrategy | TO_START/TO_PREVIOUS | ❌ 实现未见相关字段 |
| ⑤ | Operator | EQUALS/NOT_EQUALS/GREATER_THAN/...（15个） | ✅ 前端 condition.ts 已定义 |
| ⑥ | Logic | AND/OR | ✅ 前端 condition.ts 已定义 |
| ⑦ | WorkflowStatus | DRAFT/PUBLISHED/DISABLED | ⚠️ 实现用 version 管理，未见 status 字段 |
| ⑧ | InstanceStatus | RUNNING/APPROVED/REJECTED/CANCELED | ⚠️ 实现用 state: running/finished/canceled，缺 REJECTED |
| ⑨ | OperationType | SUBMIT/APPROVE/REJECT/CANCEL/CC | ⚠️ 实现用 action 字段，值不完全对应 |
| ⑩ | TaskStatus | PENDING/APPROVED/REJECTED/CANCELED | ⚠️ 实现用 status: open/claimed/completed/canceled |
| ⑪ | TaskType | APPROVE/CC | ❌ 实现未见相关字段 |

**问题总结**：
- ❌ 缺失 CONDITION 节点类型的完整支持
- ❌ 缺失 CC（抄送）节点类型
- ❌ 缺失驳回策略（RejectStrategy）
- ⚠️ 状态值命名不一致

---

## 第二部分：流程设计阶段对照

### 2.1 第1步：获取表单字段

**设计要求**：
```
GET /api/form/{formId}/fields
返回：[{ key, name, type, options }]
```

**实现现状**：
- ❌ 未找到相关 API 端点
- ❌ 前端无法获取表单字段列表用于条件构造器

**优化建议**：
需要实现 `GET /api/v1/forms/{form_id}/fields` 端点

---

### 2.2 第2-5步：流程设计与保存

**设计要求**：
```
POST /api/workflow/definition
{
  formId, name, nodes[], edges[]
}
```

**实现现状**：
- ✅ 后端有 `PUT /api/v1/flows/{flow_definition_id}/draft` 保存草稿
- ✅ 后端有 `POST /api/v1/flows/{flow_definition_id}/publish` 发布流程
- ⚠️ 前端类型定义完整，但 UI 组件未完全集成

**差异分析**：
1. 设计用 POST 创建，实现用 PUT 更新草稿（更合理）
2. 设计的 nodes/edges 分离，实现的 nodes/routes 合并（routes 包含条件）
3. 设计的 nodeConfig 存储在节点，实现的条件存储在 route

---

### 2.3 第6步：发布流程校验

**设计要求的 9 项校验**：
1. ✅ START 有且仅有 1 个
2. ✅ END 至少 1 个
3. ✅ APPROVAL 至少 1 个
4. ✅ 每个节点有出入边
5. ⚠️ CONDITION 至少 2 条出边（实现未见 CONDITION 节点）
6. ✅ APPROVAL 配了审批人
7. ✅ 可达性检查（BFS）
8. ✅ 无环检测（DFS）
9. ❌ 缺失：CONDITION 节点的条件表达式校验

**实现现状**：
- ✅ flow_service.py 中 `_validate_flow_structure()` 实现了 8 项校验
- ❌ 缺失 CONDITION 节点类型的校验

---

## 第三部分：流程执行阶段对照

### 3.1 第1步：表单提交触发流程

**设计要求**：
```
POST /api/workflow/submit
{ formId, formDataId }

后端逻辑：
1. 查流程定义
2. 组装表单数据 Map
3. 创建 workflow_instance
4. 写操作日志
5. 调用 advanceFrom(instance, startNode, formData)
```

**实现现状**：
- ✅ ProcessService.start_process() 实现了核心逻辑
- ⚠️ 表单提交触发流程的 API 端点未找到
- ❌ 缺失 form_data_snapshot 的保存

**优化建议**：
1. 需要在 submission API 中集成流程启动逻辑
2. 需要保存表单数据快照到 process_instance

---

### 3.2 第2-3步：条件评估与路由推进

**设计要求**：
```
advanceFrom(instance, currentNode, formData)
  → 查连线表
  → 拿到 targetNodeKey
  → 调用 executeNode(instance, targetNode, formData)

executeNode(CONDITION)
  → 评估条件树
  → 按 priority 排序
  → 递归调用 executeNode
```

**实现现状**：
- ✅ ProcessService.advance_from_node() 实现了路由推进
- ✅ RouteEvaluator.evaluate() 实现了条件评估
- ⚠️ 条件表达式格式为 JsonLogic，与设计的条件树结构不同

**条件表达式格式对比**：

设计格式（条件树）：
```json
{
  "type": "GROUP",
  "logic": "AND",
  "children": [
    { "type": "RULE", "fieldKey": "amount", "operator": "GREATER_THAN", "value": 10000 },
    { "type": "RULE", "fieldKey": "category", "operator": "EQUALS", "value": "招待" }
  ]
}
```

实现格式（JsonLogic）：
```json
{
  "and": [
    { ">=": [{ "var": "amount" }, 10000] },
    { "==": [{ "var": "category" }, "招待"] }
  ]
}
```

**问题**：
- ❌ 条件表达式格式完全不同
- ❌ 前端条件构造器生成的是设计格式，后端评估的是 JsonLogic 格式
- ❌ 需要转换层或统一格式

---

### 3.3 第4-5步：条件计算与审批人解析

**设计要求的 compare 函数**：
- 支持 15 种运算符
- 支持类型转换（NUMBER、DATE、MULTI_SELECT）
- 支持 IS_EMPTY、BETWEEN、IN、HAS_ANY、HAS_ALL 等

**实现现状**：
- ✅ ConditionEvaluator 支持基本运算符
- ⚠️ 运算符支持不完整（缺 BETWEEN、HAS_ANY、HAS_ALL 等）
- ❌ 类型转换逻辑不完善

**审批人解析**：

设计要求：
```
SPECIFIC_USER → approverIds
ROLE → 查用户-角色关系表
DEPARTMENT_HEAD → 查部门主管
FORM_FIELD → 从表单数据取值
```

实现现状：
- ✅ AssignmentService 实现了审批人解析
- ⚠️ 支持的类型：user/group/role/department/position/expr
- ❌ 缺失 FORM_FIELD 类型的支持

---

### 3.4 第6步：审批操作

**设计要求**：
```
POST /api/workflow/task/{taskId}/approve
POST /api/workflow/task/{taskId}/reject
POST /api/workflow/instance/{instanceId}/cancel
```

**实现现状**：
- ❌ 未找到相关 API 端点
- ❌ 审批操作的完整流程未实现

**缺失的功能**：
1. 审批通过 → 继续推进流程
2. 审批驳回 → 根据 RejectStrategy 处理
3. 发起人撤回 → 取消所有待处理任务

---

## 第四部分：查询展示阶段对照

**设计要求**：
- 待办列表
- 已办列表
- 我发起的
- 审批时间线

**实现现状**：
- ❌ 未找到相关 API 端点
- ❌ 查询接口未实现

---

## 第五部分：前端组件对照

### 5.1 条件构造器

**设计要求**：
- ConditionBuilderV2.vue（主容器）
- ConditionGroup.vue（条件组）
- ConditionRule.vue（单条规则）
- ValueInput.vue（值输入）

**实现现状**：
- ✅ 所有组件文件存在
- ✅ 类型定义完整（condition.ts）
- ⚠️ 组件与后端条件格式不匹配（设计格式 vs JsonLogic）

### 5.2 流程设计器

**设计要求**：
- 画布（节点拖拽、连线）
- 节点检查器（配置编辑）
- 路由检查器（条件编辑）
- 节点调色板

**实现现状**：
- ❌ 流程设计器 UI 组件未找到
- ❌ 画布、节点编辑等功能未实现

---

## 第六部分：关键缺失与优化清单

### 🔴 关键缺失（必须实现）

1. **CONDITION 节点类型**
   - 后端 NodeType 缺失 CONDITION
   - 条件分支逻辑未实现
   - 条件节点的校验未实现

2. **CC（抄送）节点类型**
   - 后端 NodeType 缺失 CC
   - 抄送任务派发逻辑未实现

3. **驳回策略（RejectStrategy）**
   - 数据库字段缺失
   - 驳回处理逻辑未实现

4. **审批操作 API**
   - POST /api/v1/workflow/task/{taskId}/approve
   - POST /api/v1/workflow/task/{taskId}/reject
   - POST /api/v1/workflow/instance/{instanceId}/cancel

5. **条件表达式格式统一**
   - 前端生成设计格式，后端评估 JsonLogic 格式
   - 需要转换层或统一为一种格式

6. **表单字段 API**
   - GET /api/v1/forms/{form_id}/fields
   - 用于前端条件构造器获取字段列表

7. **流程设计器 UI**
   - 画布组件
   - 节点编辑器
   - 路由编辑器

### 🟡 需要优化（建议改进）

1. **状态值命名**
   - InstanceStatus: RUNNING/APPROVED/REJECTED/CANCELED
   - TaskStatus: PENDING/APPROVED/REJECTED/CANCELED
   - 当前实现不一致

2. **条件评估器**
   - 运算符支持不完整
   - 类型转换逻辑需完善
   - 缺失 BETWEEN、HAS_ANY、HAS_ALL 等

3. **审批人类型**
   - 缺失 FORM_FIELD 类型
   - 需要支持从表单字段取值

4. **表单数据快照**
   - process_instance 缺失 form_data_snapshot 字段
   - 需要保存提交时的表单数据

5. **查询接口**
   - 待办列表
   - 已办列表
   - 我发起的
   - 审批时间线

### ✅ 已完善（无需改动）

1. ✅ 流程定义的草稿管理
2. ✅ 流程发布与快照机制
3. ✅ 流程结构校验（8 项）
4. ✅ 基本的路由推进逻辑
5. ✅ 任务派发机制
6. ✅ 会签、SLA、自动审批等扩展功能

---

## 第七部分：优化建议

### 优先级 P0（立即处理）

1. **实现 CONDITION 节点类型**
   - 在 NodeType 中添加 CONDITION
   - 实现条件分支逻辑
   - 添加条件节点校验

2. **统一条件表达式格式**
   - 选择一种格式（建议保留设计格式）
   - 前端生成该格式
   - 后端添加转换层或直接支持

3. **实现审批操作 API**
   - 审批通过
   - 审批驳回（含 RejectStrategy）
   - 发起人撤回

4. **实现表单字段 API**
   - 返回表单的所有字段定义
   - 包括系统字段

### 优先级 P1（本周处理）

1. **实现流程设计器 UI**
   - 画布组件
   - 节点编辑器
   - 路由编辑器

2. **完善条件评估器**
   - 支持所有 15 种运算符
   - 完善类型转换逻辑

3. **实现查询接口**
   - 待办列表
   - 已办列表
   - 我发起的
   - 审批时间线

4. **添加 form_data_snapshot 字段**
   - 保存表单数据快照

### 优先级 P2（后续优化）

1. **实现 CC 节点类型**
2. **优化状态值命名**
3. **支持 FORM_FIELD 审批人类型**
4. **完善错误处理与日志**

---

## 总结

FormFlow 的审批流程系统已有**坚实的基础架构**，但与设计文档相比存在**关键功能缺失**和**格式不统一**的问题。

**建议按以下顺序推进**：
1. 实现 CONDITION 节点和条件分支逻辑
2. 统一条件表达式格式
3. 实现审批操作 API
4. 实现流程设计器 UI
5. 完善条件评估器和查询接口

