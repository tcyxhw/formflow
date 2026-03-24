# 实现计划

- [x] 1. 编写 bug 条件探索测试
  - **Property 1: Bug Condition** - 路由条件正确保存、加载和显示
  - **关键要求**：此测试必须在未修复的代码上失败 - 失败确认 bug 存在
  - **不要尝试修复测试或代码**
  - **注意**：此测试编码了期望的行为 - 在实现修复后通过时将验证修复
  - **目标**：发现证明 bug 存在的反例
  - **作用域 PBT 方法**：针对确定性 bug，将属性限定为具体的失败案例以确保可重现性
  - 测试实现细节来自设计文档中的 Bug Condition
  - 测试断言应匹配设计文档中的 Expected Behavior Properties
  - 在未修复的代码上运行测试
  - **预期结果**：测试失败（这是正确的 - 证明 bug 存在）
  - 记录发现的反例以理解根本原因
  - 当测试编写完成、运行并记录失败时，标记任务完成
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2. 编写保留性属性测试（在实现修复之前）
  - **Property 2: Preservation** - 非条件配置功能保持不变
  - **重要**：遵循观察优先方法
  - 在未修复的代码上观察非 bug 输入的行为
  - 编写基于属性的测试，捕获来自 Preservation Requirements 的观察到的行为模式
  - 基于属性的测试生成许多测试用例以提供更强的保证
  - 在未修复的代码上运行测试
  - **预期结果**：测试通过（这确认了要保留的基线行为）
  - 当测试编写完成、运行并在未修复代码上通过时，标记任务完成
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. 修复审批路由条件显示和编辑功能

  - [x] 3.1 修复 ConditionBuilderV2 字段选择被替换问题
    - 分析 `allFields` 计算属性的字段合并逻辑
    - 确保 `apiFields` 和 `schemaFields` 正确合并，不会相互覆盖
    - 优化字段加载时机，避免在用户编辑时触发响应式更新
    - 确保系统字段不会替换表单字段
    - 添加字段去重逻辑，基于 `field.name` 进行唯一性判断
    - 改进 `watch` 监听器，确保 `modelValue` 变化时正确更新 `rootGroup`
    - 处理 null 和空对象的边界情况
    - _Bug_Condition: isBugCondition(input) where input.action == 'SELECT_FIELD'_
    - _Expected_Behavior: 所有选择的字段都正确保留，不被系统字段替换_
    - _Preservation: 首次添加条件、取消编辑、保存条件等功能保持不变_
    - _Requirements: 2.1, 3.1, 3.2, 3.3_

  - [x] 3.2 在 FlowRouteInspector 中添加条件展示 UI
    - 实现 `formatConditionForDisplay` 函数，将 JsonLogic 转换为可读文本
    - 在"条件设置"区域添加条件详情展示组件
    - 显示条件的字段名、操作符、值等信息
    - 支持多层嵌套的 AND/OR 逻辑组的展示
    - 添加条件为空时的占位提示（"未设置条件"）
    - 使用 Naive UI 的 `n-tag` 或 `n-text` 组件美化展示效果
    - _Bug_Condition: isBugCondition(input) where input.action == 'CLOSE_CONDITION_MODAL'_
    - _Expected_Behavior: FlowRouteInspector 清晰展示已配置的条件内容_
    - _Preservation: 修改路由其他属性时不影响条件配置功能_
    - _Requirements: 2.2, 3.5_

  - [x] 3.3 修复 FlowRouteInspector 条件加载逻辑
    - 在 `openConditionModal` 函数中添加详细的日志输出
    - 确保 `jsonLogicToConditionNode` 正确转换 JsonLogic 格式
    - 处理边界情况：null、空对象、格式错误等
    - 验证转换结果的格式是否符合 ConditionBuilderV2 的期望
    - 在弹窗顶部添加已配置条件的预览区域
    - 确保 ConditionBuilderV2 的 `v-model` 正确绑定初始值
    - 测试多种 JsonLogic 格式的兼容性
    - _Bug_Condition: isBugCondition(input) where input.action == 'OPEN_CONDITION_MODAL'_
    - _Expected_Behavior: ConditionBuilderV2 正确加载并显示路由已有的条件配置_
    - _Preservation: JSON 编辑器继续支持手动输入 JsonLogic 格式_
    - _Requirements: 2.3, 3.6_

  - [x] 3.4 在 FlowRouteInspector 中添加条件管理功能
    - 添加"清空条件"按钮，允许用户删除所有条件
    - 在条件详情展示区域添加"编辑"按钮
    - 实现 `clearCondition` 函数，将 `route.condition` 设置为 null
    - 实现 `editCondition` 函数，打开条件编辑弹窗
    - 添加确认对话框，防止误删条件
    - 确保删除条件后触发 `setDirty()` 标记草稿已修改
    - 更新 UI 状态，反映条件已被删除
    - _Bug_Condition: isBugCondition(input) where input.action == 'MANAGE_CONDITION'_
    - _Expected_Behavior: 系统提供直观的 UI 交互入口，支持查看、编辑和删除条件_
    - _Preservation: 保存条件时继续转换为 JsonLogic 格式_
    - _Requirements: 2.4, 3.3_

  - [x] 3.5 验证 bug 条件探索测试现在通过
    - **Property 1: Expected Behavior** - 路由条件正确保存、加载和显示
    - **重要**：重新运行步骤 1 中的相同测试 - 不要编写新测试
    - 步骤 1 中的测试编码了期望的行为
    - 当此测试通过时，确认期望的行为已满足
    - 运行步骤 1 中的 bug 条件探索测试
    - **预期结果**：测试通过（确认 bug 已修复）
    - _Requirements: 设计文档中的 Expected Behavior Properties_

  - [x] 3.6 验证保留性测试仍然通过
    - **Property 2: Preservation** - 非条件配置功能保持不变
    - **重要**：重新运行步骤 2 中的相同测试 - 不要编写新测试
    - 运行步骤 2 中的保留性属性测试
    - **预期结果**：测试通过（确认没有回归）
    - 确认修复后所有测试仍然通过（没有回归）

- [x] 4. 检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户。
