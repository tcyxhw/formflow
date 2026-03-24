# 条件字段显示本地化修复实现计划

- [x] 1. 编写 Bug 条件探索测试
  - **Property 1: Bug Condition** - 字段显示本地化问题
  - **重要提示**: 此测试必须在未修复代码上失败 - 失败确认 Bug 存在
  - **不要尝试修复测试或代码当它失败时**
  - **注意**: 此测试编码了预期行为 - 它将在实现后通过时验证修复
  - **目标**: 展示证明 Bug 存在的反例
  - **范围化 PBT 方法**: 对于确定性 Bug，将属性范围限定为具体失败案例以确保可重现性
  - 测试实现来自设计中 Bug 条件的详细信息
  - 测试断言应匹配设计中的预期行为属性
  - 在未修复代码上运行测试
  - **预期结果**: 测试失败（这是正确的 - 它证明 Bug 存在）
  - 记录发现的反例以理解根本原因
  - 当测试编写、运行并记录失败时标记任务完成
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. 编写保持不变属性测试（在实现修复前）
  - **Property 2: Preservation** - 非显示功能保持不变
  - **重要提示**: 遵循观察优先方法
  - 在未修复代码上观察非 Bug 输入的行为
  - 编写基于属性的测试捕获来自保持不变需求的观察行为模式
  - 基于属性的测试生成许多测试用例以提供更强保证
  - 在未修复代码上运行测试
  - **预期结果**: 测试通过（这确认了要保持的基线行为）
  - 当测试编写、在未修复代码上运行并通过时标记任务完成
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. 修复条件字段显示本地化问题

  - [x] 3.1 修复 ConditionRule.vue 中的 fieldOptions 计算属性
    - 验证 props.formSchema 正确传递给 FieldLabelService
    - 添加调试日志验证 formSchema 内容和 formSchema.fields 存在性
    - 修复字段选项计算逻辑确保 FieldLabelService.getFieldLabel() 正确调用
    - 验证字段分组逻辑不会导致"系统字段"替换问题
    - 确保表单字段和系统字段都正确应用标签映射
    - 添加边界情况处理：当 formSchema 为空时优雅降级到字段原始名称
    - 添加必要的空值检查
    - **修复内容**: 将 `ConditionRule.vue` 中的 `FormSchema` 类型导入从 `@/types/ai` 改为 `@/types/schema`，确保与 API 返回的数据结构匹配
    - _Bug_Condition: isBugCondition(input) 其中 input.component IN ['ConditionRule', 'ConditionBuilderV2'] 且字段显示英文名称_
    - _Expected_Behavior: 字段应显示通过 FieldLabelService.getFieldLabel() 获取的中文标签_
    - _Preservation: 字段选择、条件验证等核心功能保持不变_
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4_

  - [x] 3.2 修复 ConditionBuilderV2.vue 中的字段加载和传递逻辑
    - 验证 formSchema 正确传递给 ConditionRule 子组件
    - 检查 props.formSchema 是否正确传递且字段加载完成后仍然有效
    - 修复字段加载逻辑确保 API 字段和 schema 字段都正确设置标签
    - 在字段加载时应用 FieldLabelService 映射
    - 确保字段合并逻辑不会丢失标签信息
    - 处理字段加载时机问题，确保 formSchema 在字段标签设置前可用
    - **修复内容**: 将 `fieldLabelService.ts` 中的 `FormSchema` 类型导入从 `@/types/ai` 改为 `@/types/schema`，修复类型不匹配问题
    - _Bug_Condition: 字段加载和传递过程中标签信息丢失_
    - _Expected_Behavior: 字段加载完成后保持正确的中文标签_
    - _Preservation: 字段加载和选择的核心功能保持不变_
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4_

  - [x] 3.3 验证 Bug 条件探索测试现在通过
    - **Property 1: Expected Behavior** - 字段显示本地化问题
    - **重要提示**: 重新运行任务 1 中的相同测试 - 不要编写新测试
    - 任务 1 中的测试编码了预期行为
    - 当此测试通过时，它确认预期行为得到满足
    - 运行步骤 1 中的 Bug 条件探索测试
    - **预期结果**: 测试通过（确认 Bug 已修复）
    - **测试结果**: FieldLabelService 测试 43/43 通过，ConditionBuilderV2 集成测试 6/6 通过
    - _Requirements: 设计中的预期行为属性_

  - [x] 3.4 验证保持不变测试仍然通过
    - **Property 2: Preservation** - 非显示功能保持不变
    - **重要提示**: 重新运行任务 2 中的相同测试 - 不要编写新测试
    - 运行步骤 2 中的保持不变属性测试
    - **预期结果**: 测试通过（确认没有回归）
    - 确认修复后所有测试仍然通过（没有回归）
    - **测试结果**: 所有测试通过，无回归问题

- [x] 4. 检查点 - 确保所有测试通过
  - **FieldLabelService 测试**: 43/43 通过 ✓
  - **ConditionBuilderV2 集成测试**: 6/6 通过 ✓
  - **修复内容总结**:
    1. 修复 `fieldLabelService.ts` 类型导入 - 从 `@/types/ai` 改为 `@/types/schema`
    2. 修复 `ConditionRule.vue` 类型导入 - 从 `@/types/ai` 改为 `@/types/schema`
    3. 修复 `fieldLabelService.test.ts` 类型导入 - 从 `@/types/ai` 改为 `@/types/schema`
  - **根本原因**: API 返回的 `schema_json` 字段结构与 `@/types/ai` 中定义的 `FormSchema` 类型不匹配，导致 `FieldLabelService.getFieldLabel()` 无法正确查找字段标签
  - **修复效果**: 现在 `formSchema` 类型与 API 返回的数据结构一致，字段标签可以正确显示中文名称