# 审批流程优化 - 任务清单

## 第一阶段：P0 优先级（第 1-2 周）

### 第 1 周：条件格式统一 + CONDITION 节点

#### Day 1-2：条件表达式格式统一

- [x] 1.1 创建后端条件评估器 V2
  - [x] 1.1.1 创建 `backend/app/services/condition_evaluator_v2.py`
  - [x] 1.1.2 实现 `ConditionEvaluatorV2` 类
  - [x] 1.1.3 支持所有 15 种运算符
  - [x] 1.1.4 支持类型转换
  - [x] 1.1.5 支持嵌套条件

- [x] 1.2 创建条件转换器
  - [x] 1.2.1 创建 `backend/app/services/condition_converter.py`
  - [x] 1.2.2 实现 JsonLogic → 设计格式转换
  - [x] 1.2.3 编写转换测试

- [x] 1.3 更新路由评估器
  - [x] 1.3.1 修改 `RouteEvaluator` 使用新的评估器
  - [x] 1.3.2 保持 API 兼容性

- [x] 1.4 编写单元测试
  - [x] 1.4.1 创建 `backend/tests/test_condition_evaluator_v2.py`
  - [x] 1.4.2 测试所有运算符
  - [x] 1.4.3 测试类型转换
  - [x] 1.4.4 测试嵌套条件

#### Day 3-4：CONDITION 节点实现

- [-] 2.1 数据库迁移
  - [x] 2.1.1 创建迁移脚本 `008_add_condition_node_support.py`
  - [x] 2.1.2 添加 `condition_branches` 字段到 `FlowNode`
  - [x] 2.1.3 运行迁移：`alembic upgrade head`

- [-] 2.2 后端流程推进逻辑
  - [x] 2.2.1 修改 `ProcessService._dispatch_nodes()`
  - [x] 2.2.2 添加 CONDITION 节点处理
  - [x] 2.2.3 实现条件分支评估
  - [x] 2.2.4 实现默认路由

- [-] 2.3 后端流程校验
  - [x] 2.3.1 修改 `FlowService._validate_flow_structure()`
  - [x] 2.3.2 添加 `_validate_condition_node_config()`
  - [x] 2.3.3 校验分支数量 >= 2
  - [x] 2.3.4 校验条件表达式

- [-] 2.4 前端类型定义
  - [x] 2.4.1 更新 `my-app/src/types/flow.ts`
  - [x] 2.4.2 添加 `condition_branches` 字段

- [-] 2.5 前端条件节点编辑器
  - [x] 2.5.1 创建 `ConditionNodeEditor.vue`
  - [x] 2.5.2 实现分支列表编辑
  - [x] 2.5.3 实现条件表达式编辑
  - [x] 2.5.4 实现优先级排序
  - [x] 2.5.5 实现默认路由设置

- [x] 2.6 编写测试
  - [x] 2.6.1 创建 `backend/tests/test_condition_node.py`
  - [x] 2.6.2 测试条件分支逻辑
  - [x] 2.6.3 测试默认路由
  - [x] 2.6.4 创建前端单元测试

#### Day 5：表单字段 API

- [-] 3.1 后端 API 实现
  - [x] 3.1.1 在 `backend/app/api/v1/forms.py` 添加 `get_form_fields()`
  - [x] 3.1.2 返回表单字段列表
  - [x] 3.1.3 包含系统字段

- [x] 3.2 前端 API 接口
  - [x] 3.2.1 在 `my-app/src/api/form.ts` 添加 `getFormFields()`
  - [x] 3.2.2 在条件构造器中集成

- [-] 3.3 编写测试
  - [x] 3.3.1 创建 `backend/tests/test_form_fields_api.py`
  - [x] 3.3.2 测试字段返回

---

### 第 2 周：驳回策略 + 审批操作 API

#### Day 1-2：驳回策略实现

- [x] 4.1 数据库迁移
  - [x] 4.1.1 创建迁移脚本 `009_add_reject_strategy.py`
  - [x] 4.1.2 添加 `reject_strategy` 字段到 `FlowNode`
  - [x] 4.1.3 运行迁移

- [x] 4.2 后端驳回处理逻辑
  - [x] 4.2.1 创建 `backend/app/services/approval_service.py`
  - [x] 4.2.2 实现 `_handle_rejection()`
  - [x] 4.2.3 实现 TO_START 策略
  - [x] 4.2.4 实现 TO_PREVIOUS 策略
  - [x] 4.2.5 实现 `_find_previous_approval_node()`

- [x] 4.3 前端类型定义
  - [x] 4.3.1 更新 `my-app/src/types/flow.ts`
  - [x] 4.3.2 添加 `RejectStrategy` 类型

- [x] 4.4 前端审批节点编辑器
  - [x] 4.4.1 在节点编辑器中添加驳回策略选择

- [x] 4.5 编写测试
  - [x] 4.5.1 创建 `backend/tests/test_reject_strategy.py`
  - [x] 4.5.2 测试 TO_START 策略
  - [x] 4.5.3 测试 TO_PREVIOUS 策略

#### Day 3-5：审批操作 API

- [x] 5.1 后端 API 实现
  - [x] 5.1.1 创建 `backend/app/api/v1/approvals.py`
  - [x] 5.1.2 实现 `approve_task()` 端点
  - [x] 5.1.3 实现 `reject_task()` 端点
  - [x] 5.1.4 实现 `cancel_instance()` 端点
  - [x] 5.1.5 添加权限检查

- [x] 5.2 后端 Pydantic 模型
  - [x] 5.2.1 创建 `backend/app/schemas/approval_schemas.py`
  - [x] 5.2.2 定义 `ApproveTaskRequest`
  - [x] 5.2.3 定义 `RejectTaskRequest`

- [x] 5.3 前端 API 接口
  - [x] 5.3.1 创建 `my-app/src/api/approval.ts`
  - [x] 5.3.2 实现 `approveTask()`
  - [x] 5.3.3 实现 `rejectTask()`
  - [x] 5.3.4 实现 `cancelInstance()`

- [x] 5.4 前端审批页面
  - [x] 5.4.1 创建 `my-app/src/views/ApprovalDetail.vue`
  - [x] 5.4.2 显示任务详情
  - [x] 5.4.3 实现审批操作
  - [x] 5.4.4 实现驳回操作
  - [x] 5.4.5 实现撤回操作

- [x] 5.5 编写测试
  - [x] 5.5.1 创建 `backend/tests/test_approval_api.py`
  - [x] 5.5.2 测试权限检查
  - [x] 5.5.3 测试状态更新
  - [x] 5.5.4 创建前端单元测试

---

## 第二阶段：P1 优先级（第 3-4 周）

### 第 3 周：流程设计器 UI + 查询接口

#### Day 1-3：流程设计器 UI

- [-] 6.1 前端画布组件
  - [ ] 6.1.1 创建 `my-app/src/components/flow-designer/FlowCanvas.vue`
  - [ ] 6.1.2 实现节点拖拽
  - [ ] 6.1.3 实现连线绘制
  - [ ] 6.1.4 实现节点删除
  - [ ] 6.1.5 实现缩放和平移

- [-] 6.2 前端节点编辑器
  - [ ] 6.2.1 创建 `my-app/src/components/flow-designer/FlowNodeEditor.vue`
  - [ ] 6.2.2 实现基本信息编辑
  - [ ] 6.2.3 实现审批人配置
  - [ ] 6.2.4 实现驳回策略配置
  - [ ] 6.2.5 实现条件分支配置

- [-] 6.3 前端路由编辑器
  - [ ] 6.3.1 创建 `my-app/src/components/flow-designer/FlowRouteEditor.vue`
  - [ ] 6.3.2 实现条件表达式编辑
  - [ ] 6.3.3 实现优先级设置
  - [ ] 6.3.4 实现默认路由设置

- [ ] 6.4 前端节点调色板
  - [x] 6.4.1 创建 `my-app/src/components/flow-designer/FlowNodePalette.vue`
  - [x] 6.4.2 实现节点类型选择
  - [x] 6.4.3 实现拖拽添加

- [-] 6.5 前端主容器
  - [x] 6.5.1 创建 `my-app/src/views/FlowDesigner.vue`
  - [x] 6.5.2 整合所有子组件
  - [x] 6.5.3 实现保存功能
  - [x] 6.5.4 实现发布功能

- [-] 6.6 前端状态管理
  - [x] 6.6.1 创建 `my-app/src/stores/useFlowStore.ts`
  - [x] 6.6.2 管理节点列表
  - [x] 6.6.3 管理路由列表
  - [x] 6.6.4 管理选中节点

- [x] 6.7 编写测试
  - [x] 6.7.1 创建组件单元测试
  - [x] 6.7.2 创建集成测试
  - [x] 6.7.3 创建端到端测试

#### Day 4-5：查询接口

- [ ] 7.1 后端待办列表 API
  - [ ] 7.1.1 在 `backend/app/api/v1/approvals.py` 添加 `list_pending_tasks()`
  - [ ] 7.1.2 实现分页
  - [ ] 7.1.3 实现排序

- [ ] 7.2 后端已办列表 API
  - [ ] 7.2.1 添加 `list_completed_tasks()`
  - [ ] 7.2.2 实现分页
  - [ ] 7.2.3 实现排序

- [ ] 7.3 后端我发起的 API
  - [ ] 7.3.1 添加 `list_initiated_instances()`
  - [ ] 7.3.2 实现分页
  - [ ] 7.3.3 实现排序

- [ ] 7.4 后端审批时间线 API
  - [ ] 7.4.1 添加 `get_instance_timeline()`
  - [ ] 7.4.2 返回操作日志

- [ ] 7.5 前端 API 接口
  - [ ] 7.5.1 在 `my-app/src/api/approval.ts` 添加查询接口
  - [ ] 7.5.2 实现 `listPendingTasks()`
  - [ ] 7.5.3 实现 `listCompletedTasks()`
  - [ ] 7.5.4 实现 `listInitiatedInstances()`
  - [ ] 7.5.5 实现 `getInstanceTimeline()`

- [ ] 7.6 前端页面
  - [ ] 7.6.1 创建 `my-app/src/views/PendingApprovals.vue`
  - [ ] 7.6.2 创建 `my-app/src/views/CompletedApprovals.vue`
  - [ ] 7.6.3 创建 `my-app/src/views/InitiatedInstances.vue`
  - [ ] 7.6.4 创建 `my-app/src/views/ApprovalTimeline.vue`

- [ ] 7.7 编写测试
  - [ ] 7.7.1 创建 `backend/tests/test_query_api.py`
  - [ ] 7.7.2 创建前端单元测试

---

### 第 4 周：条件评估器完善 + 优化

#### Day 1-2：条件评估器完善

- [ ] 8.1 完善条件评估器
  - [ ] 8.1.1 支持 BETWEEN 运算符
  - [ ] 8.1.2 支持 HAS_ANY 运算符
  - [ ] 8.1.3 支持 HAS_ALL 运算符
  - [ ] 8.1.4 完善日期比较
  - [ ] 8.1.5 完善类型转换

- [ ] 8.2 编写测试
  - [ ] 8.2.1 创建 `backend/tests/test_all_operators.py`
  - [ ] 8.2.2 测试所有 15 种运算符
  - [ ] 8.2.3 测试边界情况

#### Day 3-4：性能优化和错误处理

- [ ] 9.1 性能优化
  - [ ] 9.1.1 添加数据库索引
  - [ ] 9.1.2 优化查询语句
  - [ ] 9.1.3 添加缓存

- [ ] 9.2 错误处理
  - [ ] 9.2.1 完善异常处理
  - [ ] 9.2.2 添加详细日志
  - [ ] 9.2.3 返回有意义的错误信息

- [ ] 9.3 编写测试
  - [ ] 9.3.1 创建性能测试
  - [ ] 9.3.2 创建错误场景测试

#### Day 5：集成测试和文档

- [ ] 10.1 集成测试
  - [ ] 10.1.1 完整流程测试
  - [ ] 10.1.2 条件分支测试
  - [ ] 10.1.3 驳回流程测试
  - [ ] 10.1.4 撤回流程测试

- [ ] 10.2 文档
  - [ ] 10.2.1 编写 API 文档
  - [ ] 10.2.2 编写前端组件文档
  - [ ] 10.2.3 编写使用指南
  - [ ] 10.2.4 编写故障排查指南

- [ ] 10.3 部署
  - [ ] 10.3.1 数据库迁移
  - [ ] 10.3.2 代码部署
  - [ ] 10.3.3 功能验证

---

## 验收标准

### 第一阶段验收

- ✅ 所有 P0 任务完成
- ✅ 单元测试覆盖率 > 80%
- ✅ 集成测试全部通过
- ✅ 代码审查通过
- ✅ 无 critical 级别 bug

### 第二阶段验收

- ✅ 所有 P1 任务完成
- ✅ 单元测试覆盖率 > 80%
- ✅ 集成测试全部通过
- ✅ 端到端测试全部通过
- ✅ 代码审查通过
- ✅ 文档完整
- ✅ 性能满足要求
- ✅ 无 critical 级别 bug

