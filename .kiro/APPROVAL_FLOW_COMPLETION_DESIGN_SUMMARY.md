# 审批流程完善设计方案 - 总结与路线图

## 一、设计方案总览

本设计方案完整覆盖了审批流程系统的所有未完成功能，包括：

| 功能模块 | 状态 | 工作量 | 优先级 |
|---------|------|--------|--------|
| CONDITION 节点 | 设计完成 | 3-4d | P0 |
| CC 节点 | 设计完成 | 2-3d | P1 |
| 审批操作 API | 设计完成 | 2-3d | P0 |
| 表单字段 API | 设计完成 | 1-2d | P0 |
| 查询接口 | 设计完成 | 2-3d | P1 |
| 条件表达式格式统一 | 设计完成 | 2-3d | P0 |
| 流程设计器 UI | 设计完成 | 5-7d | P2 |
| 数据库迁移 | 设计完成 | 1d | P0 |
| **总计** | **设计完成** | **19-28d** | - |

---

## 二、核心设计要点

### 2.1 CONDITION 节点设计

**关键特性**：
- ✅ 支持多个条件分支
- ✅ 每个分支有优先级、标签、条件、目标节点
- ✅ 支持默认分支
- ✅ 条件使用设计格式（条件树）
- ✅ 按优先级排序，第一个匹配的分支被执行

**实现位置**：
- 数据模型：`FlowNode.condition_branches`
- 流程推进：`ProcessService._dispatch_nodes()` 中添加 CONDITION 处理
- 条件评估：`ProcessService._evaluate_condition_branches()`
- 流程校验：`FlowService._validate_flow_structure()` 中添加 CONDITION 校验

### 2.2 CC 节点设计

**关键特性**：
- ✅ 支持多种抄送人类型（user/group/role/department/position）
- ✅ 为每个抄送人创建任务（task_type = "cc"）
- ✅ 抄送任务仅通知，不需要操作
- ✅ CC 节点后继续推进流程

**实现位置**：
- 数据模型：`FlowNode.cc_assignee_type` 和 `FlowNode.cc_assignee_value`
- 任务创建：`ProcessService._create_cc_task()`
- 流程推进：`ProcessService._dispatch_nodes()` 中添加 CC 处理

### 2.3 条件表达式格式统一

**设计方案**：
- ✅ 保留设计格式（条件树）作为标准格式
- ✅ 前端生成条件树格式
- ✅ 后端支持条件树格式直接评估
- ✅ 提供转换层支持 JsonLogic 兼容

**实现位置**：
- 转换服务：`backend/app/services/condition_converter.py`
- 条件评估器 V2：`backend/app/services/condition_evaluator_v2.py`
- 支持所有 15 种运算符

### 2.4 审批操作 API 设计

**三个核心 API**：
1. `POST /api/v1/approvals/tasks/{taskId}/approve` - 审批通过
2. `POST /api/v1/approvals/tasks/{taskId}/reject` - 审批驳回
3. `POST /api/v1/approvals/instances/{instanceId}/cancel` - 撤回申请

**关键流程**：
- ✅ 权限校验
- ✅ 状态校验
- ✅ 任务更新
- ✅ 操作日志记录
- ✅ 流程推进

### 2.5 表单字段 API 设计

**API 端点**：
- `GET /api/v1/forms/{form_id}/fields` - 获取表单字段列表

**返回数据**：
- ✅ 表单字段定义（key, name, type, options）
- ✅ 系统字段（sys_submitter, sys_submitter_dept, sys_submit_time）

### 2.6 查询接口设计

**四个查询 API**：
1. `GET /api/v1/approvals/pending` - 待办列表
2. `GET /api/v1/approvals/completed` - 已办列表
3. `GET /api/v1/approvals/initiated` - 我发起的
4. `GET /api/v1/approvals/instances/{instanceId}/timeline` - 审批时间线

**关键特性**：
- ✅ 分页支持
- ✅ 排序支持
- ✅ 包含表单数据快照
- ✅ 包含操作日志

---

## 三、实现路线图

### 第 1 周（P0 优先级 - 核心功能）

**目标**：完成审批流程的核心功能，使流程可以正常运行

#### Day 1-2：数据库迁移和模型扩展
- [ ] 创建迁移脚本：添加 CONDITION/CC 节点字段
- [ ] 创建迁移脚本：添加 form_data_snapshot 字段
- [ ] 创建迁移脚本：扩展 Task 表
- [ ] 创建迁移脚本：创建 WorkflowOperationLog 表
- [ ] 运行迁移脚本
- [ ] 更新 ORM 模型

**文件**：
- `backend/alembic/versions/009_add_condition_cc_nodes.py`
- `backend/alembic/versions/010_add_form_data_snapshot.py`
- `backend/alembic/versions/011_extend_task_table.py`
- `backend/alembic/versions/012_create_workflow_operation_log.py`
- `backend/app/models/workflow.py`

#### Day 3-4：条件表达式格式统一
- [ ] 实现 `ConditionConverter` 类
- [ ] 实现树 → JsonLogic 转换
- [ ] 实现 JsonLogic → 树转换
- [ ] 添加格式验证
- [ ] 编写单元测试

**文件**：
- `backend/app/services/condition_converter.py`
- `backend/tests/test_condition_converter.py`

#### Day 5-6：实现 ConditionEvaluatorV2
- [ ] 实现条件树直接评估
- [ ] 支持所有 15 种运算符
- [ ] 完善类型转换逻辑
- [ ] 编写单元测试

**文件**：
- `backend/app/services/condition_evaluator_v2.py`
- `backend/tests/test_condition_evaluator_v2.py`

#### Day 7：CONDITION 节点实现
- [ ] 实现 `_evaluate_condition_branches()` 方法
- [ ] 修改 `_dispatch_nodes()` 支持 CONDITION 节点
- [ ] 修改 `_validate_flow_structure()` 添加 CONDITION 校验
- [ ] 编写集成测试

**文件**：
- `backend/app/services/process_service.py`
- `backend/app/services/flow_service.py`
- `backend/tests/test_condition_node.py`

#### Day 8：审批操作 API
- [ ] 创建 `backend/app/api/v1/approvals.py`
- [ ] 实现 `approve_task()` 端点
- [ ] 实现 `reject_task()` 端点
- [ ] 实现 `cancel_instance()` 端点
- [ ] 编写集成测试

**文件**：
- `backend/app/api/v1/approvals.py`
- `backend/tests/test_approval_api.py`

#### Day 9：表单字段 API
- [ ] 在 `backend/app/api/v1/forms.py` 中添加 `get_form_fields()` 端点
- [ ] 实现字段解析逻辑
- [ ] 添加系统字段
- [ ] 编写单元测试

**文件**：
- `backend/app/api/v1/forms.py`
- `backend/tests/test_form_fields_api.py`

**预期成果**：
- ✅ 审批流程可以正常运行
- ✅ 支持 CONDITION 节点条件分支
- ✅ 支持审批操作（通过/驳回/撤回）
- ✅ 前端可以获取表单字段用于条件构造

---

### 第 2 周（P1 优先级 - 完善功能）

**目标**：完善审批流程的功能，实现所有查询接口

#### Day 1：CC 节点实现
- [ ] 实现 `_create_cc_task()` 方法
- [ ] 修改 `_dispatch_nodes()` 支持 CC 节点
- [ ] 修改 `_validate_flow_structure()` 添加 CC 校验
- [ ] 编写集成测试

**文件**：
- `backend/app/services/process_service.py`
- `backend/app/services/flow_service.py`
- `backend/tests/test_cc_node.py`

#### Day 2-3：查询接口实现
- [ ] 实现 `get_pending_tasks()` 端点
- [ ] 实现 `get_completed_tasks()` 端点
- [ ] 实现 `get_initiated_instances()` 端点
- [ ] 实现 `get_timeline()` 端点
- [ ] 编写集成测试

**文件**：
- `backend/app/api/v1/approvals.py`
- `backend/app/services/query_service.py`
- `backend/tests/test_query_api.py`

#### Day 4-5：前端 API 集成
- [ ] 创建 `my-app/src/api/approval.ts`
- [ ] 集成审批操作 API
- [ ] 集成查询 API
- [ ] 集成表单字段 API

**文件**：
- `my-app/src/api/approval.ts`
- `my-app/src/api/flow.ts`

#### Day 6-7：前端页面实现
- [ ] 实现待办列表页面
- [ ] 实现已办列表页面
- [ ] 实现我发起的页面
- [ ] 实现审批时间线页面

**文件**：
- `my-app/src/views/approval/PendingList.vue`
- `my-app/src/views/approval/CompletedList.vue`
- `my-app/src/views/approval/InitiatedList.vue`
- `my-app/src/views/approval/Timeline.vue`

**预期成果**：
- ✅ 支持 CC 节点抄送功能
- ✅ 实现所有查询接口
- ✅ 前端可以查看待办/已办/我发起的/时间线

---

### 第 3 周（P2 优先级 - UI 和优化）

**目标**：实现流程设计器 UI，完成整个系统

#### Day 1-2：画布组件实现
- [ ] 实现 `FlowCanvas.vue` 画布
- [ ] 实现 `FlowNode.vue` 节点
- [ ] 实现 `FlowEdge.vue` 连线
- [ ] 实现节点拖拽、连线绘制

**文件**：
- `my-app/src/components/flow-designer/FlowCanvas.vue`
- `my-app/src/components/flow-designer/FlowNode.vue`
- `my-app/src/components/flow-designer/FlowEdge.vue`

#### Day 3-4：检查器实现
- [ ] 实现 `NodeInspector.vue` 节点检查器
- [ ] 实现 `BasicConfig.vue` 基本配置
- [ ] 实现 `ApprovalConfig.vue` 审批配置
- [ ] 实现 `ConditionConfig.vue` 条件配置
- [ ] 实现 `CCConfig.vue` 抄送配置

**文件**：
- `my-app/src/components/flow-designer/NodeInspector.vue`
- `my-app/src/components/flow-designer/BasicConfig.vue`
- `my-app/src/components/flow-designer/ApprovalConfig.vue`
- `my-app/src/components/flow-designer/ConditionConfig.vue`
- `my-app/src/components/flow-designer/CCConfig.vue`

#### Day 5-6：路由编辑器和调色板
- [ ] 实现 `RouteInspector.vue` 路由检查器
- [ ] 实现 `NodePalette.vue` 节点调色板
- [ ] 实现 `Toolbar.vue` 工具栏

**文件**：
- `my-app/src/components/flow-designer/RouteInspector.vue`
- `my-app/src/components/flow-designer/NodePalette.vue`
- `my-app/src/components/flow-designer/Toolbar.vue`

#### Day 7：流程设计器主容器
- [ ] 实现 `FlowDesigner.vue` 主容器
- [ ] 集成所有子组件
- [ ] 实现状态管理
- [ ] 编写端到端测试

**文件**：
- `my-app/src/components/flow-designer/FlowDesigner.vue`
- `my-app/src/stores/flowDesignerStore.ts`

**预期成果**：
- ✅ 完整的流程设计器 UI
- ✅ 支持节点拖拽、连线、配置
- ✅ 支持所有节点类型的配置
- ✅ 完整的审批流程系统

---

## 四、关键实现细节

### 4.1 CONDITION 节点处理流程

```
1. 用户在画布上添加 CONDITION 节点
2. 配置条件分支（优先级、标签、条件、目标节点）
3. 保存流程定义
4. 发布流程时校验 CONDITION 节点
5. 提交表单时：
   - 流程推进到 CONDITION 节点
   - 评估条件分支
   - 按优先级排序
   - 找到第一个匹配的分支
   - 路由到目标节点
   - 如果没有分支匹配，使用默认分支
```

### 4.2 审批操作流程

```
审批通过：
1. 查任务，校验权限
2. 更新任务状态为 completed
3. 记录操作日志
4. 根据会签策略决定是否推进
5. 如果推进，调用 advance_from_node()

审批驳回：
1. 查任务，校验权限
2. 更新任务状态为 completed
3. 记录操作日志
4. 根据驳回策略处理：
   - TO_START：流程结束，标记为 REJECTED
   - TO_PREVIOUS：重新创建上一个审批节点的任务

撤回申请：
1. 查流程实例，校验权限
2. 取消所有待处理任务
3. 更新实例状态为 canceled
4. 记录操作日志
```

### 4.3 条件表达式格式转换

```
前端生成条件树格式 →
保存到数据库 →
后端评估时：
  - 选项 A：直接用 ConditionEvaluatorV2 评估条件树
  - 选项 B：转换为 JsonLogic 后用现有 RouteEvaluator 评估

建议：选项 A（直接评估条件树）
```

---

## 五、测试策略

### 5.1 单元测试

- [ ] `test_condition_converter.py` - 条件格式转换
- [ ] `test_condition_evaluator_v2.py` - 条件评估（所有 15 种运算符）
- [ ] `test_condition_node.py` - CONDITION 节点逻辑
- [ ] `test_cc_node.py` - CC 节点逻辑
- [ ] `test_approval_service.py` - 审批服务

### 5.2 集成测试

- [ ] `test_condition_node_routing.py` - CONDITION 节点路由
- [ ] `test_cc_node_task_creation.py` - CC 节点任务创建
- [ ] `test_approve_task.py` - 审批通过
- [ ] `test_reject_task_to_start.py` - 驳回到发起人
- [ ] `test_reject_task_to_previous.py` - 驳回到上一个审批节点
- [ ] `test_cancel_instance.py` - 撤回申请

### 5.3 端到端测试

- [ ] 完整的审批流程（包含 CONDITION 和 CC 节点）
- [ ] 条件分支路由
- [ ] 驳回策略处理
- [ ] 查询接口

---

## 六、风险评估与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|--------|
| 条件格式转换失败 | 现有流程无法运行 | 中 | 充分测试、数据备份 |
| CONDITION 节点逻辑复杂 | 性能下降 | 低 | 优化算法、缓存 |
| 前后端不同步 | 功能不可用 | 中 | 充分沟通、集成测试 |
| 数据库迁移失败 | 数据丢失 | 低 | 备份、灰度发布 |

---

## 七、成功标准

### 功能完成度
- ✅ CONDITION 节点完全实现
- ✅ CC 节点完全实现
- ✅ 审批操作 API 完全实现
- ✅ 表单字段 API 完全实现
- ✅ 查询接口完全实现
- ✅ 条件表达式格式统一
- ✅ 流程设计器 UI 完全实现

### 测试覆盖率
- ✅ 单元测试覆盖率 > 80%
- ✅ 集成测试覆盖率 > 70%
- ✅ 端到端测试全部通过

### 代码质量
- ✅ 代码审查通过
- ✅ 文档完整
- ✅ 性能满足要求
- ✅ 安全检查通过

---

## 八、总结

本设计方案完整覆盖了审批流程系统的所有未完成功能，包括：

**核心功能**（P0 - 第 1 周）：
- CONDITION 节点条件分支
- 审批操作 API（通过/驳回/撤回）
- 表单字段 API
- 条件表达式格式统一

**完善功能**（P1 - 第 2 周）：
- CC 节点抄送功能
- 查询接口（待办/已办/我发起的/时间线）

**UI 功能**（P2 - 第 3 周）：
- 流程设计器 UI

**预期结果**：
- 第 1 周：审批流程可以正常运行（60% → 80%）
- 第 2 周：审批流程功能完整（80% → 95%）
- 第 3 周：完整的审批流程系统（95% → 100%）

**总工作量**：19-28 天（3-4 周）

