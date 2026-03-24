# Implementation Plan: Approval Flow Configuration

## Overview

本实现计划将审批流程配置功能分解为可执行的编码任务。该功能允许表单创建者在表单发布前配置审批流程，通过可视化流程配置器设计流程结构，并在发布前进行严格的拓扑和业务规则校验。

实现采用后端优先策略，先完成核心校验逻辑和服务层，再集成前端路由和UI组件。所有任务按照用户指定的优先级排序，确保核心流程优先实现。

## Tasks

### 1. 后端：表单创建时自动创建流程定义

- [x] 1.1 在 FormService.create_form() 中添加 FlowDefinition 自动创建逻辑
  - 修改 `backend/app/services/form_service.py` 中的 `create_form()` 方法
  - 在创建 Form 记录后，创建关联的 FlowDefinition 记录
  - 设置 FlowDefinition 的 tenant_id、form_id、name（格式："{form.name} - 审批流程"）
  - 设置 version=0, active_snapshot_id=None（草稿状态）
  - 将 flow_definition.id 赋值给 form.flow_definition_id
  - 确保在同一事务中提交
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 1.2 编写属性测试：表单创建初始化流程定义
  - **Property 1: Form Creation Initializes Flow Definition**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
  - 使用 hypothesis 生成随机的表单创建请求
  - 验证每次创建表单都会自动创建 FlowDefinition
  - 验证 FlowDefinition 的 form_id、tenant_id 匹配
  - 验证初始状态为草稿（version=0, active_snapshot_id=None）

- [ ]* 1.3 编写单元测试：表单创建流程定义集成
  - 测试正常创建表单时 FlowDefinition 被创建
  - 测试 FlowDefinition 的字段值正确性
  - 测试事务回滚时 FlowDefinition 不会被创建
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

### 2. 后端：实现流程校验方法

- [x] 2.1 在 FlowService 中实现基础校验方法
  - 修改 `backend/app/services/flow_service.py`
  - 实现 `_validate_single_start_node(nodes)` 方法
    - 统计 type="start" 的节点数量
    - 如果数量为 0，抛出 BusinessError("流程必须有一个开始节点")
    - 如果数量 > 1，抛出 BusinessError("流程只能有一个开始节点")
  - 实现 `_validate_at_least_one_end_node(nodes)` 方法
    - 统计 type="end" 的节点数量
    - 如果数量为 0，抛出 BusinessError("流程必须至少有一个结束节点")
  - 实现 `_validate_at_least_one_approval_node(nodes)` 方法
    - 统计 type="approval" 的节点数量
    - 如果数量为 0，抛出 BusinessError("流程必须至少有一个审批节点")
  - _Requirements: 6.1, 6.2, 7.1, 7.2, 8.1, 8.2_

- [ ]* 2.2 编写属性测试：节点类型校验
  - **Property 4: Single Start Node Validation**
  - **Property 5: At Least One End Node Validation**
  - **Property 6: At Least One Approval Node Validation**
  - **Validates: Requirements 6.1, 7.1, 8.1**
  - 使用 hypothesis 生成随机节点配置
  - 验证只有符合节点数量要求的配置才能通过校验
  - 验证错误消息正确

- [x] 2.3 在 FlowService 中实现边校验方法
  - 实现 `_validate_node_edges(nodes, routes)` 方法
    - 构建邻接表（outgoing 和 incoming）
    - 遍历所有节点，检查非 end 节点是否有出边
    - 遍历所有节点，检查非 start 节点是否有入边
    - 如果校验失败，抛出 BusinessError 并包含节点名称
  - _Requirements: 9.1, 9.2, 10.1, 10.2_

- [ ]* 2.4 编写属性测试：边校验
  - **Property 7: Non-End Nodes Have Outgoing Edges**
  - **Property 8: Non-Start Nodes Have Incoming Edges**
  - **Validates: Requirements 9.1, 10.1**
  - 使用 hypothesis 生成随机图结构
  - 验证边校验逻辑正确识别缺失的边

- [-] 2.5 在 FlowService 中实现条件节点和审批节点校验
  - 实现 `_validate_condition_node_branches(nodes, routes)` 方法
    - 构建出边邻接表
    - 遍历 type="condition" 的节点
    - 检查每个条件节点的出边数量 >= 2
    - 如果校验失败，抛出 BusinessError 并包含节点名称
  - 实现 `_validate_approval_node_config(nodes)` 方法
    - 遍历 type="approval" 的节点
    - 检查 config 中是否有 approver_type 和 approver_ids
    - 如果校验失败，抛出 BusinessError 并包含节点名称
  - _Requirements: 11.1, 11.2, 12.1, 12.2_

- [ ]* 2.6 编写属性测试：条件节点和审批节点校验
  - **Property 9: Condition Nodes Have Two Branches**
  - **Property 10: Approval Nodes Have Approver Configuration**
  - **Validates: Requirements 11.1, 12.1**
  - 使用 hypothesis 生成随机节点配置
  - 验证条件节点分支数量校验
  - 验证审批节点配置校验

- [-] 2.7 在 FlowService 中实现可达性校验
  - 实现 `_validate_reachability(nodes, routes)` 方法
    - 找到 start 节点
    - 找到所有 end 节点
    - 构建邻接表
    - 使用 BFS 从 start 节点遍历图
    - 检查是否至少有一个 end 节点在可达集合中
    - 如果不可达，抛出 BusinessError("流程不可达：无法从开始节点到达结束节点")
  - _Requirements: 13.1, 13.2_

- [ ]* 2.8 编写属性测试：可达性校验
  - **Property 11: End Node Reachability**
  - **Validates: Requirements 13.2**
  - 使用 hypothesis 生成随机图结构
  - 验证可达性算法正确识别不可达的流程

- [-] 2.9 在 FlowService 中实现死循环检测
  - 实现 `_validate_no_dead_cycles(nodes, routes)` 方法
    - 构建邻接表
    - 获取所有 end 节点 ID 集合
    - 使用 DFS 检测环
    - 对于检测到的环，检查是否包含至少一个 end 节点
    - 如果存在不包含 end 节点的环，抛出 BusinessError("流程存在死循环")
  - _Requirements: 14.1, 14.2, 14.3_

- [ ]* 2.10 编写属性测试：死循环检测
  - **Property 12: No Dead Cycles**
  - **Validates: Requirements 14.1**
  - 使用 hypothesis 生成包含环的图结构
  - 验证死循环检测算法正确识别死循环
  - 验证包含 end 节点的环被允许

- [x] 2.11 在 FlowService.publish_flow() 中集成所有校验
  - 修改 `publish_flow()` 方法
  - 在创建 FlowSnapshot 之前调用 `_validate_flow_structure(nodes, routes)`
  - 实现 `_validate_flow_structure()` 方法，依次调用所有 9 个校验方法
  - 确保任何校验失败都会阻止发布（不创建 snapshot，不更新 version）
  - _Requirements: 17.1, 17.2_

- [ ]* 2.12 编写属性测试：校验原子性
  - **Property 13: Validation Atomicity**
  - **Validates: Requirements 6.4, 7.4, 8.4, 9.4, 10.4, 11.4, 12.4**
  - 使用 hypothesis 生成无效的流程配置
  - 验证发布失败时不会创建 FlowSnapshot
  - 验证发布失败时 version 不会增加
  - 验证发布失败时 active_snapshot_id 不会更新

### 3. 后端：表单发布前流程校验

- [x] 3.1 在 FormService.publish_form() 中添加流程发布状态校验
  - 修改 `backend/app/services/form_service.py` 中的 `publish_form()` 方法
  - 在现有权限检查后，添加流程校验逻辑
  - 检查 form.flow_definition_id 是否存在
  - 如果存在，查询 FlowDefinition
  - 检查 FlowDefinition.active_snapshot_id 是否为 None
  - 如果为 None，抛出 ValidationError("表单发布前必须先配置并发布审批流程")
  - _Requirements: 15.1, 15.2, 15.3_

- [ ]* 3.2 编写属性测试：表单发布需要已发布流程
  - **Property 14: Form Publish Requires Published Flow**
  - **Validates: Requirements 15.1**
  - 使用 hypothesis 生成表单和流程状态组合
  - 验证只有流程已发布的表单才能发布成功

- [ ]* 3.3 编写属性测试：表单发布原子性
  - **Property 15: Form Publish Atomicity**
  - **Validates: Requirements 15.4**
  - 验证表单发布失败时状态不变
  - 验证不会创建新的 FormVersion

- [ ]* 3.4 编写单元测试：表单发布流程校验集成
  - 测试表单发布时流程未发布的情况
  - 测试表单发布时流程已发布的情况
  - 测试错误消息正确性
  - _Requirements: 15.1, 15.2, 15.3_

### 4. 后端：流程权限校验

- [x] 4.1 在 FlowService 中添加权限校验方法
  - 实现 `_check_flow_permission(flow_definition_id, tenant_id, user_id, db)` 方法
  - 查询 FlowDefinition 并 join Form 表
  - 验证 FlowDefinition.tenant_id == tenant_id（租户隔离）
  - 验证 Form.owner_user_id == user_id（创建者权限）
  - 如果校验失败，抛出 AuthorizationError
  - 在 `get_definition_detail()`, `save_draft()`, `publish_flow()` 中调用此方法
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 4.2 编写属性测试：权限控制
  - **Property 2: Only Form Creator Can Access Flow Configuration**
  - **Property 3: Tenant Isolation for Flow Access**
  - **Validates: Requirements 5.1, 5.2, 5.4**
  - 使用 hypothesis 生成不同用户和租户组合
  - 验证只有表单创建者可以访问流程配置
  - 验证跨租户访问被拒绝

- [ ]* 4.3 编写单元测试：权限校验
  - 测试非创建者访问被拒绝
  - 测试跨租户访问被拒绝
  - 测试创建者访问成功
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

### 5. 前端：添加流程配置路由

- [x] 5.1 在 router/index.ts 中添加流程配置器路由
  - 修改 `my-app/src/router/index.ts`
  - 在 authRoutes 数组中添加新的路由配置
  - 路径：`/flow/configurator/:id`
  - 组件：懒加载 `@/views/flow/Configurator.vue`
  - meta: `{ title: '流程配置器', requiresAuth: true }`
  - _Requirements: 2.1, 2.2, 2.4_

- [ ]* 5.2 编写单元测试：路由配置
  - 测试路由路径正确
  - 测试路由需要认证
  - 测试路由参数 id 正确传递
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

### 6. 前端：表单列表添加"配置流程"按钮

- [x] 6.1 在 Form List 中添加"配置流程"操作按钮
  - 修改 `my-app/src/views/form/List.vue`
  - 在 columns 定义的 actions 列中添加新按钮
  - 按钮文本：'配置流程'
  - 按钮类型：'info'
  - 按钮大小：'small'
  - disabled 条件：`row.status !== 'draft'`（只有草稿状态可配置）
  - 点击事件：调用 `handleConfigureFlow(row)`
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 6.2 实现 handleConfigureFlow 方法
  - 检查 row.flow_definition_id 是否存在
  - 如果不存在，显示错误消息："该表单没有关联的流程定义"
  - 如果存在，导航到 `/flow/configurator/${row.flow_definition_id}`
  - _Requirements: 3.4_

- [ ]* 6.3 编写组件测试：配置流程按钮状态
  - **Property 20: Flow Configuration Button State**
  - **Validates: Requirements 3.2, 3.3**
  - 测试草稿状态表单的按钮启用
  - 测试已发布表单的按钮禁用
  - 测试按钮点击导航正确

### 7. 前端：表单设计器添加流程配置引导

- [x] 7.1 在 FormDesigner 中添加流程配置提示
  - 修改 `my-app/src/components/FormDesigner/index.vue`
  - 在 handleSave 方法中，保存成功后添加通知
  - 检查 formData.status === 'draft'
  - 使用 notification.info 显示提示
  - 标题：'下一步：配置审批流程'
  - 内容：'表单已保存。发布前需要配置审批流程。'
  - 添加操作按钮："立即配置"
  - 按钮点击导航到 `/flow/configurator/${formData.flow_definition_id}`
  - duration: 8000ms
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ]* 7.2 编写组件测试：流程配置引导
  - 测试保存草稿后显示通知
  - 测试通知内容正确
  - 测试"立即配置"按钮导航正确
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

### 8. 后端：草稿保存和加载

- [x] 8.1 验证 FlowService 的草稿保存功能
  - 检查 `save_draft()` 方法是否正确保存节点和路由配置
  - 确保草稿保存不执行校验（允许保存无效配置）
  - 确保乐观锁版本控制正常工作
  - _Requirements: 16.1, 16.2, 16.3_

- [ ]* 8.2 编写属性测试：草稿保存无需校验
  - **Property 16: Draft Save Without Validation**
  - **Validates: Requirements 16.3**
  - 使用 hypothesis 生成无效的流程配置
  - 验证草稿保存成功（不抛出校验错误）

- [ ]* 8.3 编写属性测试：草稿往返保存
  - **Property 17: Draft Round-Trip Preservation**
  - **Validates: Requirements 16.1, 16.2, 16.4**
  - 使用 hypothesis 生成随机流程配置
  - 保存为草稿后重新加载
  - 验证配置完全一致

### 9. 后端：流程发布和快照

- [x] 9.1 验证 FlowService 的流程发布功能
  - 检查 `publish_flow()` 方法是否正确创建 FlowSnapshot
  - 确保 FlowDefinition.version 递增
  - 确保 FlowDefinition.active_snapshot_id 更新
  - _Requirements: 17.1, 17.2, 17.3, 17.4_

- [ ]* 9.2 编写属性测试：成功发布创建快照
  - **Property 18: Successful Publish Creates Snapshot**
  - **Validates: Requirements 17.2, 17.3, 17.4**
  - 使用 hypothesis 生成有效的流程配置
  - 验证发布后创建 FlowSnapshot
  - 验证 version 递增
  - 验证 active_snapshot_id 更新

- [ ]* 9.3 编写属性测试：版本递增单调性
  - **Property 19: Version Increment Monotonicity**
  - **Validates: Requirements 17.4**
  - 多次发布同一流程
  - 验证版本号严格递增
  - 验证无重复或跳跃

### 10. 前端：流程配置器错误处理

- [x] 10.1 在 FlowConfigurator 中添加校验错误处理
  - 修改 `my-app/src/views/flow/Configurator.vue`
  - 在 handlePublish 方法中添加详细的错误处理
  - 捕获 code === 4001 的业务错误
  - 使用 dialog.error 显示校验失败详情
  - 如果 errorData.failed_nodes 存在，高亮显示失败的节点
  - 捕获 code === 4003 的权限错误，导航到 /403
  - _Requirements: 6.2, 7.2, 8.2, 9.2, 10.2, 11.2, 12.2, 13.3, 14.4_

- [ ]* 10.2 编写组件测试：错误处理
  - 测试校验错误显示正确
  - 测试权限错误导航正确
  - 测试失败节点高亮功能

### 11. 前端：节点删除级联删除路由

- [x] 11.1 验证 FlowConfigurator 的节点删除功能
  - 检查删除节点时是否同时删除相关的路由
  - 确保删除的路由包括以该节点为 from_node_id 或 to_node_id 的所有路由
  - _Requirements: 18.3_

- [ ]* 11.2 编写属性测试：节点删除级联
  - **Property 21: Node Deletion Cascades to Routes**
  - **Validates: Requirements 18.3**
  - 创建包含节点和路由的流程
  - 删除节点
  - 验证相关路由被删除

### 12. 前端：结束节点不能有出边

- [x] 12.1 验证 FlowConfigurator 的结束节点限制
  - 检查是否阻止从 end 节点创建出边
  - 确保 UI 层面禁用 end 节点的输出端口
  - _Requirements: 19.4_

- [ ]* 12.2 编写属性测试：结束节点出边限制
  - **Property 22: End Nodes Cannot Have Outgoing Routes**
  - **Validates: Requirements 19.4**
  - 尝试从 end 节点创建出边
  - 验证操作被阻止

### 13. 集成测试

- [x]* 13.1 编写端到端集成测试：完整流程配置工作流
  - 测试从表单创建到流程发布的完整流程
  - 步骤 1：创建表单，验证 FlowDefinition 自动创建
  - 步骤 2：保存流程草稿
  - 步骤 3：发布流程，验证校验通过
  - 步骤 4：验证 FlowSnapshot 创建
  - 步骤 5：发布表单，验证成功
  - _Requirements: 1.1-1.4, 16.1-16.4, 17.1-17.4, 15.1-15.4_

- [x]* 13.2 编写集成测试：无效流程配置被拒绝
  - 创建包含各种校验错误的流程配置
  - 验证每种错误都被正确检测和报告
  - 验证发布失败时数据库状态不变
  - _Requirements: 6.1-14.4_

### 14. Checkpoint - 确保所有测试通过

- [x] 14.1 运行所有后端测试
  - 执行 `pytest` 确保所有单元测试和属性测试通过
  - 检查测试覆盖率是否达到目标（服务层 90%+，API 层 85%+）
  - 修复任何失败的测试

- [x] 14.2 运行所有前端测试
  - 执行 `npm run test` 确保所有组件测试通过
  - 检查测试覆盖率是否达到目标（组件 80%+）
  - 修复任何失败的测试

- [x] 14.3 手动测试完整工作流
  - 启动后端和前端开发服务器
  - 测试表单创建、流程配置、流程发布、表单发布的完整流程
  - 测试各种校验错误场景
  - 测试权限控制
  - 确保所有功能正常工作，询问用户是否有问题

## Notes

- 任务标记 `*` 的为可选测试任务，可根据时间安排跳过以加快 MVP 交付
- 每个任务都引用了具体的需求编号，确保可追溯性
- 属性测试使用 hypothesis (Python) 和 fast-check (TypeScript)
- 所有校验方法在发布时执行，草稿保存不执行校验
- 前端流程配置器组件已存在且功能完整，无需修改
- 实现顺序按照用户指定的优先级：核心流程 > 完善体验 > 测试任务
