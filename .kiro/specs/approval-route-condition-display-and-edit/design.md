# 审批路由条件显示和编辑功能 Bugfix 设计

## Overview

本设计文档针对审批流程配置页面中路由条件配置功能的四个关键缺陷进行系统性修复：

1. **字段选择被替换问题**：ConditionBuilderV2 组件在滑动选择字段时，字段被系统字段替换
2. **已配置条件不显示**：FlowRouteInspector 组件无法展示已保存的路由条件
3. **编辑弹窗缺少条件展示**：条件编辑弹窗无法加载已有条件
4. **缺少条件管理功能**：缺少查看、编辑、删除条件的 UI 交互入口

修复策略采用最小化改动原则，重点解决数据流转和状态同步问题，确保条件的正确保存、加载和显示。

## Glossary

- **Bug_Condition (C)**: 触发 bug 的条件 - 当用户配置路由条件时，系统无法正确保存、加载或显示条件数据
- **Property (P)**: 期望的正确行为 - 路由条件应该能够正确保存为 JsonLogic 格式，并在界面上正确加载和显示
- **Preservation**: 需要保持不变的现有行为 - 首次添加条件、取消编辑、保存条件、多层嵌套逻辑、其他路由属性编辑、JSON 手动编辑等功能
- **JsonLogic**: 一种用于表示逻辑表达式的 JSON 格式，例如 `{"and": [{"==": [{"var": "amount"}, 100]}]}`
- **ConditionNode**: 前端条件构建器使用的内部数据结构，包含 GROUP 和 RULE 两种类型
- **FlowRouteInspector**: 路由属性检查器组件，位于 `my-app/src/components/flow-configurator/FlowRouteInspector.vue`
- **ConditionBuilderV2**: 条件构建器组件，位于 `my-app/src/components/flow-configurator/ConditionBuilderV2.vue`
- **flowDraft store**: 流程草稿状态管理，位于 `my-app/src/stores/flowDraft.ts`
- **route.condition**: 路由配置对象中的条件字段，存储 JsonLogic 格式的条件表达式

## Bug Details

### Bug Condition

bug 在以下四种场景中表现：

**场景 1：字段选择被替换**
用户在 ConditionBuilderV2 组件中通过滑动操作选择表单字段时，系统会将之前选择的字段替换为系统字段，导致最终只保留最后一个选择的字段。

**场景 2：已配置条件不显示**
用户已经为路由配置了条件（route.condition 存在 JsonLogic 数据）并关闭条件编辑弹窗后，FlowRouteInspector 组件不显示已配置的条件内容。

**场景 3：编辑弹窗缺少条件展示**
用户点击"编辑条件"按钮打开条件编辑弹窗时，弹窗中的 ConditionBuilderV2 组件不显示路由已有的条件配置。

**场景 4：缺少条件管理功能**
用户需要查看、修改或删除已配置的路由条件时，系统没有提供相应的 UI 交互入口和功能。

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type UserInteraction
  OUTPUT: boolean
  
  RETURN (input.action == 'SELECT_FIELD' AND fieldsGetReplaced(input))
         OR (input.action == 'CLOSE_CONDITION_MODAL' AND NOT conditionDisplayed(input.route))
         OR (input.action == 'OPEN_CONDITION_MODAL' AND NOT conditionLoaded(input.route))
         OR (input.action == 'MANAGE_CONDITION' AND NOT managementUIAvailable())
END FUNCTION
```

### Examples

**示例 1：字段选择被替换**
- 用户操作：在条件构建器中选择"报销金额"字段，然后滑动选择"费用类别"字段
- 预期行为：两个字段都应该保留在条件列表中
- 实际行为：只保留"费用类别"字段，"报销金额"被系统字段替换

**示例 2：已配置条件不显示**
- 用户操作：配置条件 `{"and": [{"==": [{"var": "amount"}, 1000]}]}`，点击保存，关闭弹窗
- 预期行为：FlowRouteInspector 应显示"已设置条件"，并展示条件详情（如"报销金额 等于 1000"）
- 实际行为：只显示"已设置条件"文本，没有条件详情展示

**示例 3：编辑弹窗缺少条件展示**
- 用户操作：路由已有条件 `{"==": [{"var": "category"}, "差旅"]}`，点击"编辑条件"按钮
- 预期行为：ConditionBuilderV2 应显示现有条件（费用类别 等于 差旅）
- 实际行为：ConditionBuilderV2 显示空白，没有加载已有条件

**示例 4：缺少条件管理功能**
- 用户操作：想要删除已配置的路由条件
- 预期行为：应该有"清空条件"或"删除条件"按钮
- 实际行为：没有相应的 UI 入口，只能通过 JSON 编辑器手动删除

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- 首次为路由添加条件时，系统应正常打开空白的条件编辑器
- 点击"取消"按钮时，系统应放弃所有未保存的修改
- 点击"保存条件"按钮时，系统应将条件转换为 JsonLogic 格式并更新到 route.condition
- 多层嵌套的 AND/OR 逻辑组应正确处理序列化和反序列化
- 修改路由的其他属性（优先级、默认路由等）时，不应影响条件配置功能
- JSON 编辑器应继续支持手动输入 JsonLogic 格式的条件表达式

**Scope:**
所有不涉及条件显示、加载和字段选择的功能应完全不受影响。这包括：
- 节点的添加、删除、编辑操作
- 路由的添加、删除操作
- 流程图的拖拽和布局
- 流程的保存和发布
- 其他节点属性的配置

## Hypothesized Root Cause

基于代码分析，最可能的问题原因如下：

### 问题 1：字段选择被替换

**根因分析**：
1. **字段数据源混乱**：ConditionBuilderV2 组件同时使用 `apiFields` 和 `schemaFields` 两个数据源，可能导致字段列表在滑动时被重新计算和替换
2. **响应式更新问题**：`allFields` 计算属性在 API 加载完成后会触发更新，可能导致正在编辑的字段被重置
3. **字段顺序问题**：系统字段总是被添加到字段列表末尾，可能在某些情况下覆盖表单字段

### 问题 2：已配置条件不显示

**根因分析**：
1. **缺少条件展示 UI**：FlowRouteInspector 组件只显示"已设置条件"或"未设置条件"文本，没有实现条件详情的渲染逻辑
2. **JsonLogic 到可读文本的转换缺失**：没有将 JsonLogic 格式转换为用户友好的文本描述（如"报销金额 等于 1000"）

### 问题 3：编辑弹窗缺少条件展示

**根因分析**：
1. **条件加载逻辑错误**：`openConditionModal` 函数中调用了 `jsonLogicToConditionNode` 转换函数，但转换结果可能为 null 或格式不正确
2. **ConditionBuilderV2 初始化问题**：组件的 `watch` 监听器可能没有正确处理初始值的加载
3. **数据格式不匹配**：存储的 JsonLogic 格式可能与 ConditionBuilderV2 期望的格式不完全兼容

### 问题 4：缺少条件管理功能

**根因分析**：
1. **UI 设计不完整**：FlowRouteInspector 组件没有设计条件管理相关的按钮和交互
2. **功能未实现**：没有实现"清空条件"、"删除条件"等功能函数

## Correctness Properties

Property 1: Bug Condition - 路由条件正确保存、加载和显示

_For any_ 用户交互，当用户配置路由条件、保存条件、关闭弹窗、重新打开编辑弹窗时，系统 SHALL 正确保存条件为 JsonLogic 格式，在界面上清晰展示条件内容，并在编辑弹窗中正确加载已有条件，允许用户查看、编辑和删除条件。

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - 非条件配置功能保持不变

_For any_ 用户交互，当用户操作不涉及路由条件的显示、加载和字段选择时，系统 SHALL 产生与原始代码完全相同的行为，保持所有现有功能（首次添加条件、取消编辑、保存条件、多层嵌套逻辑、其他路由属性编辑、JSON 手动编辑）的正常运行。

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

假设我们的根因分析正确，需要进行以下修改：

**File**: `my-app/src/components/flow-configurator/FlowRouteInspector.vue`

**Function**: `openConditionModal`, 条件显示 UI

**Specific Changes**:

1. **修复条件加载逻辑**：
   - 在 `openConditionModal` 函数中，确保 `jsonLogicToConditionNode` 正确转换 JsonLogic 格式
   - 添加详细的日志输出，帮助调试转换过程
   - 处理边界情况（null、空对象、格式错误等）

2. **添加条件展示 UI**：
   - 在"条件设置"区域添加条件详情展示组件
   - 实现 JsonLogic 到可读文本的转换函数（如 `formatConditionForDisplay`）
   - 显示条件的字段名、操作符、值等信息

3. **添加条件管理功能**：
   - 添加"清空条件"按钮，允许用户删除所有条件
   - 在条件详情展示区域添加"编辑"和"删除"按钮
   - 实现相应的事件处理函数

4. **改进条件编辑弹窗**：
   - 在弹窗顶部添加已配置条件的预览区域
   - 确保 ConditionBuilderV2 正确接收和显示初始值

**File**: `my-app/src/components/flow-configurator/ConditionBuilderV2.vue`

**Function**: `loadFormFields`, `allFields` 计算属性, `watch` 监听器

**Specific Changes**:

1. **修复字段选择被替换问题**：
   - 确保 `apiFields` 和 `schemaFields` 的合并逻辑正确
   - 避免在字段加载完成后触发不必要的响应式更新
   - 确保系统字段不会覆盖表单字段

2. **改进初始值加载**：
   - 在 `watch` 监听器中添加详细的日志输出
   - 确保 `modelValue` 的变化能够正确触发 `rootGroup` 的更新
   - 处理 null 和空对象的边界情况

3. **优化字段数据源**：
   - 优先使用 API 加载的字段
   - 如果 API 加载失败，回退到 schema 字段
   - 确保字段列表的稳定性，避免频繁更新

**File**: `my-app/src/stores/flowDraft.ts`

**Function**: `updateRoute`

**Specific Changes**:

1. **确保条件正确保存**：
   - 在 `updateRoute` 函数中，确保 `condition` 字段正确更新
   - 添加条件验证逻辑，确保 JsonLogic 格式正确
   - 触发 `setDirty()` 标记草稿已修改

## Testing Strategy

### Validation Approach

测试策略遵循两阶段方法：首先在未修复的代码上运行探索性测试，观察 bug 的具体表现；然后在修复后的代码上运行验证测试，确保 bug 已修复且没有引入回归。

### Exploratory Bug Condition Checking

**Goal**: 在实施修复之前，在未修复的代码上运行测试，观察 bug 的具体表现。确认或反驳根因分析。如果反驳，需要重新假设根因。

**Test Plan**: 编写测试用例模拟用户操作（选择字段、保存条件、关闭弹窗、重新打开弹窗），在未修复的代码上运行，观察失败模式并理解根本原因。

**Test Cases**:
1. **字段选择被替换测试**：模拟在 ConditionBuilderV2 中连续选择多个字段，验证字段是否被替换（预期在未修复代码上失败）
2. **条件不显示测试**：配置条件并保存，验证 FlowRouteInspector 是否显示条件详情（预期在未修复代码上失败）
3. **条件不加载测试**：保存条件后重新打开编辑弹窗，验证 ConditionBuilderV2 是否加载已有条件（预期在未修复代码上失败）
4. **条件管理功能缺失测试**：尝试查找删除条件的 UI 入口（预期在未修复代码上失败）

**Expected Counterexamples**:
- 字段选择后被系统字段替换，只保留最后一个字段
- FlowRouteInspector 只显示"已设置条件"文本，没有条件详情
- ConditionBuilderV2 显示空白，没有加载已有条件
- 没有"清空条件"或"删除条件"按钮

### Fix Checking

**Goal**: 验证对于所有触发 bug 条件的输入，修复后的函数产生预期的正确行为。

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := fixedFunction(input)
  ASSERT expectedBehavior(result)
END FOR
```

**具体验证**:
- 字段选择：验证所有选择的字段都正确保留，不被替换
- 条件显示：验证 FlowRouteInspector 正确显示条件详情
- 条件加载：验证 ConditionBuilderV2 正确加载已有条件
- 条件管理：验证"清空条件"等功能正常工作

### Preservation Checking

**Goal**: 验证对于所有不触发 bug 条件的输入，修复后的函数产生与原始函数相同的结果。

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalFunction(input) = fixedFunction(input)
END FOR
```

**Testing Approach**: 推荐使用基于属性的测试（Property-Based Testing）进行保留性检查，因为：
- 它自动生成大量测试用例，覆盖输入域
- 它能捕获手动单元测试可能遗漏的边界情况
- 它为所有非 bug 输入提供强有力的保证，确保行为不变

**Test Plan**: 首先在未修复的代码上观察非条件配置功能的行为，然后编写基于属性的测试捕获这些行为。

**Test Cases**:
1. **首次添加条件保留测试**：观察未修复代码上首次添加条件的行为，验证修复后行为一致
2. **取消编辑保留测试**：观察未修复代码上取消编辑的行为，验证修复后行为一致
3. **保存条件保留测试**：观察未修复代码上保存条件的行为，验证修复后行为一致
4. **多层嵌套逻辑保留测试**：观察未修复代码上处理嵌套逻辑的行为，验证修复后行为一致
5. **其他路由属性编辑保留测试**：观察未修复代码上编辑优先级等属性的行为，验证修复后行为一致
6. **JSON 手动编辑保留测试**：观察未修复代码上手动编辑 JSON 的行为，验证修复后行为一致

### Unit Tests

- 测试 `jsonLogicToConditionNode` 转换函数的正确性
- 测试 `conditionNodeToJsonLogic` 转换函数的正确性
- 测试 `formatConditionForDisplay` 格式化函数的输出
- 测试字段选择逻辑，确保字段不被替换
- 测试条件保存和加载的完整流程
- 测试边界情况（null、空对象、格式错误等）

### Property-Based Tests

- 生成随机的 JsonLogic 表达式，验证转换函数的双向一致性
- 生成随机的字段配置，验证字段选择的稳定性
- 生成随机的路由配置，验证条件保存和加载的正确性
- 测试多种嵌套层级的条件组合

### Integration Tests

- 测试完整的条件配置流程：打开弹窗 -> 选择字段 -> 配置条件 -> 保存 -> 关闭 -> 重新打开 -> 验证条件正确显示
- 测试条件管理流程：配置条件 -> 保存 -> 查看详情 -> 编辑 -> 删除
- 测试与其他功能的集成：配置条件的同时修改路由的其他属性
- 测试错误处理：输入无效的 JsonLogic 格式，验证错误提示
