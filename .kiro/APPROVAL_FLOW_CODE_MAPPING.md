# 审批流程代码对照表

## 一、后端关键文件映射

### 数据模型层

| 设计概念 | 实现文件 | 实现类/表 | 完善度 |
|---------|--------|---------|--------|
| 流程定义 | `backend/app/models/workflow.py` | `FlowDefinition` | ✅ 完善 |
| 流程节点 | `backend/app/models/workflow.py` | `FlowNode` | ⚠️ 缺 CONDITION/CC |
| 流程连线 | `backend/app/models/workflow.py` | `FlowRoute` | ✅ 完善 |
| 流程快照 | `backend/app/models/workflow.py` | `FlowSnapshot` | ✅ 完善 |
| 流程草稿 | `backend/app/models/workflow.py` | `FlowDraft` | ✅ 完善 |
| 流程实例 | `backend/app/models/workflow.py` | `ProcessInstance` | ⚠️ 缺 form_data_snapshot |
| 待办任务 | `backend/app/models/workflow.py` | `Task` | ✅ 完善 |
| 操作日志 | `backend/app/models/workflow.py` | `TaskActionLog` | ✅ 完善 |

### 服务层

| 设计功能 | 实现文件 | 实现类/方法 | 完善度 |
|---------|--------|-----------|--------|
| 流程定义管理 | `backend/app/services/flow_service.py` | `FlowService` | ✅ 完善 |
| 流程发布校验 | `backend/app/services/flow_service.py` | `_validate_flow_structure()` | ⚠️ 缺 CONDITION 校验 |
| 流程实例启动 | `backend/app/services/process_service.py` | `ProcessService.start_process()` | ✅ 完善 |
| 流程推进 | `backend/app/services/process_service.py` | `ProcessService.advance_from_node()` | ⚠️ 缺 CONDITION 处理 |
| 条件评估 | `backend/app/services/condition_evaluator.py` | `ConditionEvaluator` | ⚠️ 格式不匹配 |
| 路由评估 | `backend/app/services/route_evaluator.py` | `RouteEvaluator` | ✅ 完善 |
| 审批人解析 | `backend/app/services/assignment_service.py` | `AssignmentService` | ⚠️ 缺 FORM_FIELD |
| 任务派发 | `backend/app/services/process_service.py` | `_create_task_for_node()` | ✅ 完善 |
| 任务操作 | `backend/app/services/approval_service.py` | `TaskService` | ❌ 缺审批/驳回 API |

### API 层

| 设计端点 | 实现文件 | 实现方法 | 完善度 |
|---------|--------|--------|--------|
| 获取流程详情 | `backend/app/api/v1/flows.py` | `get_flow_definition()` | ✅ 完善 |
| 获取流程草稿 | `backend/app/api/v1/flows.py` | `get_flow_draft()` | ✅ 完善 |
| 保存流程草稿 | `backend/app/api/v1/flows.py` | `save_flow_draft()` | ✅ 完善 |
| 发布流程 | `backend/app/api/v1/flows.py` | `publish_flow()` | ✅ 完善 |
| 获取表单字段 | ❌ 不存在 | - | ❌ 缺失 |
| 提交表单触发流程 | ❌ 不存在 | - | ❌ 缺失 |
| 审批通过 | ❌ 不存在 | - | ❌ 缺失 |
| 审批驳回 | ❌ 不存在 | - | ❌ 缺失 |
| 撤回申请 | ❌ 不存在 | - | ❌ 缺失 |
| 待办列表 | ❌ 不存在 | - | ❌ 缺失 |
| 已办列表 | ❌ 不存在 | - | ❌ 缺失 |
| 我发起的 | ❌ 不存在 | - | ❌ 缺失 |
| 审批时间线 | ❌ 不存在 | - | ❌ 缺失 |

---

## 二、前端关键文件映射

### 类型定义

| 设计概念 | 实现文件 | 实现类型 | 完善度 |
|---------|--------|--------|--------|
| 字段类型 | `my-app/src/types/condition.ts` | `FieldType` | ✅ 完善 |
| 运算符 | `my-app/src/types/condition.ts` | `Operator` | ✅ 完善 |
| 逻辑关系 | `my-app/src/types/condition.ts` | `LogicType` | ✅ 完善 |
| 条件规则 | `my-app/src/types/condition.ts` | `ConditionRule` | ✅ 完善 |
| 条件组 | `my-app/src/types/condition.ts` | `ConditionGroup` | ✅ 完善 |
| 流程节点 | `my-app/src/types/flow.ts` | `FlowNodeConfig` | ✅ 完善 |
| 流程路由 | `my-app/src/types/flow.ts` | `FlowRouteConfig` | ✅ 完善 |
| 流程草稿 | `my-app/src/types/flow.ts` | `FlowDraftResponse` | ✅ 完善 |

### 组件

| 设计组件 | 实现文件 | 完善度 |
|---------|--------|--------|
| 条件构造器 | `my-app/src/components/flow-configurator/ConditionBuilderV2.vue` | ✅ 存在 |
| 条件组 | `my-app/src/components/flow-configurator/ConditionGroup.vue` | ✅ 存在 |
| 条件规则 | `my-app/src/components/flow-configurator/ConditionRule.vue` | ✅ 存在 |
| 值输入 | `my-app/src/components/flow-configurator/ValueInput.vue` | ✅ 存在 |
| 流程设计器 | ❌ 不存在 | ❌ 缺失 |
| 画布 | ❌ 不存在 | ❌ 缺失 |
| 节点检查器 | ❌ 不存在 | ❌ 缺失 |
| 路由检查器 | ❌ 不存在 | ❌ 缺失 |

### API 接口

| 设计接口 | 实现文件 | 实现函数 | 完善度 |
|---------|--------|--------|--------|
| 获取流程详情 | `my-app/src/api/flow.ts` | `getFlowDefinitionDetail()` | ✅ 完善 |
| 获取流程草稿 | `my-app/src/api/flow.ts` | `getFlowDraft()` | ✅ 完善 |
| 保存流程草稿 | `my-app/src/api/flow.ts` | `saveFlowDraft()` | ✅ 完善 |
| 发布流程 | `my-app/src/api/flow.ts` | `publishFlow()` | ✅ 完善 |
| 获取表单字段 | ❌ 不存在 | - | ❌ 缺失 |
| 审批通过 | ❌ 不存在 | - | ❌ 缺失 |
| 审批驳回 | ❌ 不存在 | - | ❌ 缺失 |
| 撤回申请 | ❌ 不存在 | - | ❌ 缺失 |

---

## 三、关键代码片段对照

### 3.1 条件评估

**设计要求**：
```python
# 支持 15 种运算符
# 支持类型转换
# 支持嵌套条件
```

**实现现状**：
```python
# backend/app/services/condition_evaluator.py
class ConditionEvaluator:
    @staticmethod
    def evaluate_condition(condition: Dict, data: Dict) -> bool:
        # 支持 AND/OR/NOT
        # 支持基本比较运算符
        # 不支持 BETWEEN、HAS_ANY、HAS_ALL 等
```

**问题**：
- ❌ 运算符支持不完整
- ❌ 条件格式为 JsonLogic，与设计不符

---

### 3.2 流程推进

**设计要求**：
```python
advanceFrom(instance, currentNode, formData):
    查连线表
    拿到 targetNodeKey
    调用 executeNode(instance, targetNode, formData)

executeNode(CONDITION):
    评估条件树
    按 priority 排序
    递归调用 executeNode
```

**实现现状**：
```python
# backend/app/services/process_service.py
class ProcessService:
    @staticmethod
    def advance_from_node(process, from_node, tenant_id, db, context):
        # 处理并行分支
        # 解析下一个节点
        # 派发任务
        # 不支持 CONDITION 节点
```

**问题**：
- ❌ 缺失 CONDITION 节点处理
- ⚠️ 条件评估格式不匹配

---

### 3.3 审批人解析

**设计要求**：
```python
SPECIFIC_USER → approverIds
ROLE → 查用户-角色关系表
DEPARTMENT_HEAD → 查部门主管
FORM_FIELD → 从表单数据取值
```

**实现现状**：
```python
# backend/app/services/assignment_service.py
class AssignmentService:
    @staticmethod
    def resolve_assignees(assignee_type, assignee_value, context):
        # 支持 user/group/role/department/position/expr
        # 不支持 FORM_FIELD
```

**问题**：
- ❌ 缺失 FORM_FIELD 类型

---

### 3.4 流程校验

**设计要求的 9 项校验**：
1. START 有且仅有 1 个
2. END 至少 1 个
3. APPROVAL 至少 1 个
4. 每个节点有出入边
5. CONDITION 至少 2 条出边
6. APPROVAL 配了审批人
7. 可达性检查
8. 无环检测
9. CONDITION 条件表达式校验

**实现现状**：
```python
# backend/app/services/flow_service.py
class FlowService:
    @staticmethod
    def _validate_flow_structure(nodes, routes):
        # 实现了 1-4, 6-8
        # 缺失 5（CONDITION 节点不存在）
        # 缺失 9（条件表达式校验）
```

**问题**：
- ❌ 缺失 CONDITION 节点校验
- ❌ 缺失条件表达式校验

---

## 四、数据流向对照

### 4.1 流程设计阶段

**设计流程**：
```
前端：拖拽节点 → 连线 → 配置
  ↓
前端：生成 nodes[] + edges[]
  ↓
前端：POST /api/workflow/definition
  ↓
后端：保存 workflow_definition + workflow_node + workflow_edge
  ↓
后端：校验流程结构
  ↓
后端：发布快照
```

**实现流程**：
```
前端：拖拽节点 → 连线 → 配置
  ↓
前端：生成 nodes[] + routes[]
  ↓
前端：PUT /api/v1/flows/{id}/draft
  ↓
后端：保存 flow_draft（config_json）
  ↓
前端：POST /api/v1/flows/{id}/publish
  ↓
后端：校验流程结构
  ↓
后端：生成 flow_snapshot
```

**差异**：
- ✅ 整体流程一致
- ⚠️ 设计用 POST 创建，实现用 PUT 更新（更合理）
- ⚠️ 设计的 edges 分离，实现的 routes 合并

---

### 4.2 流程执行阶段

**设计流程**：
```
用户：填写表单 → 点击提交
  ↓
前端：POST /api/workflow/submit { formId, formDataId }
  ↓
后端：查流程定义
  ↓
后端：组装表单数据 Map
  ↓
后端：创建 workflow_instance
  ↓
后端：调用 advanceFrom(instance, startNode, formData)
  ↓
后端：查连线表 → 拿到 targetNodeKey
  ↓
后端：调用 executeNode(instance, targetNode, formData)
  ↓
后端：根据节点类型处理
  ├─ START: 继续推进
  ├─ CONDITION: 评估条件 → 递归调用 executeNode
  ├─ APPROVAL: 创建任务 → 等待审批
  ├─ CC: 创建抄送任务
  └─ END: 流程结束
```

**实现流程**：
```
用户：填写表单 → 点击提交
  ↓
前端：POST /api/v1/submissions { formId, data }
  ↓
后端：SubmissionService.create_submission()
  ↓
后端：ProcessService.start_process()
  ↓
后端：创建 process_instance
  ↓
后端：创建首个任务
  ↓
后端：等待审批人操作
  ↓
审批人：POST /api/v1/tasks/{taskId}/approve（未实现）
  ↓
后端：ProcessService.advance_from_node()
  ↓
后端：RouteEvaluator.evaluate() 评估条件
  ↓
后端：创建下一批任务
```

**差异**：
- ✅ 整体流程一致
- ❌ 缺失 CONDITION 节点处理
- ❌ 缺失审批操作 API
- ❌ 缺失 CC 节点处理

---

## 五、缺失功能清单

### 后端缺失

| 功能 | 优先级 | 工作量 |
|------|--------|--------|
| CONDITION 节点类型 | P0 | 3d |
| CC 节点类型 | P1 | 2d |
| 驳回策略（RejectStrategy） | P0 | 2d |
| 审批通过 API | P0 | 1d |
| 审批驳回 API | P0 | 1d |
| 撤回申请 API | P0 | 1d |
| 表单字段 API | P0 | 1d |
| 待办列表 API | P1 | 1d |
| 已办列表 API | P1 | 1d |
| 我发起的 API | P1 | 1d |
| 审批时间线 API | P1 | 1d |
| form_data_snapshot 字段 | P1 | 1d |
| 条件表达式格式转换 | P0 | 2d |
| 条件评估器完善 | P1 | 2d |

### 前端缺失

| 功能 | 优先级 | 工作量 |
|------|--------|--------|
| 流程设计器 UI | P1 | 5d |
| 画布组件 | P1 | 3d |
| 节点编辑器 | P1 | 2d |
| 路由编辑器 | P1 | 2d |
| 审批操作页面 | P1 | 2d |
| 待办列表页面 | P1 | 2d |
| 已办列表页面 | P1 | 2d |
| 我发起的页面 | P1 | 2d |
| 审批时间线页面 | P1 | 2d |

---

## 六、优化建议

### 立即处理（P0）

1. **统一条件表达式格式**
   - 后端支持设计格式
   - 或前端改为 JsonLogic 格式

2. **实现 CONDITION 节点**
   - 数据库字段
   - 后端逻辑
   - 前端 UI

3. **实现驳回策略**
   - 数据库字段
   - 后端逻辑

4. **实现审批操作 API**
   - 审批通过
   - 审批驳回
   - 撤回申请

5. **实现表单字段 API**
   - 用于前端条件构造器

### 后续优化（P1）

1. **实现流程设计器 UI**
2. **实现查询接口**
3. **实现 CC 节点**
4. **完善条件评估器**

