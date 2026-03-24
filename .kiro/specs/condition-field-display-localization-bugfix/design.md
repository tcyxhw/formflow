# 流程审批路由条件字段显示本地化修复设计文档

## 概述

修复流程审批路由条件配置中字段显示的本地化问题。虽然 FieldLabelService.getFieldLabel() 方法已经存在，但在实际使用中仍存在字段选择器显示英文字段名、"系统字段"异常替换、以及条件显示未本地化等问题。本设计通过确保正确调用 FieldLabelService 并修复字段选项计算逻辑来解决这些问题。

## 术语表

- **Bug_Condition (C)**: 字段显示未本地化的条件 - 当用户在条件配置界面看到英文字段名而不是中文标签时
- **Property (P)**: 期望的本地化显示行为 - 字段应显示中文标签而不是英文键名
- **Preservation**: 现有功能保持不变 - 字段选择、条件验证等核心功能不受影响
- **FieldLabelService**: 位于 `my-app/src/services/fieldLabelService.ts` 的字段标签映射服务
- **formSchema**: 包含字段定义和标签信息的表单结构数据
- **ConditionRule**: 位于 `my-app/src/components/flow-configurator/ConditionRule.vue` 的条件规则组件
- **ConditionBuilderV2**: 位于 `my-app/src/components/flow-configurator/ConditionBuilderV2.vue` 的条件构建器组件

## Bug 详情

### Bug 条件

Bug 在用户配置流程审批路由条件时出现。ConditionRule.vue 和 ConditionBuilderV2.vue 组件虽然调用了 FieldLabelService.getFieldLabel()，但由于 formSchema 传递不正确或字段选项计算逻辑有问题，导致字段仍显示英文名称。

**正式规范：**
```
FUNCTION isBugCondition(input)
  INPUT: input of type FieldDisplayContext
  OUTPUT: boolean
  
  RETURN input.component IN ['ConditionRule', 'ConditionBuilderV2']
         AND input.fieldDisplayed IN fieldOptions
         AND input.fieldDisplayed.label MATCHES /^[a-zA-Z_]+$/
         AND FieldLabelService.getFieldLabel(input.fieldKey, input.formSchema) != input.fieldKey
END FUNCTION
```

### 示例

- **字段选择器显示**: 用户看到 "student_id" 而不是 "学号"
- **系统字段替换**: 滑动选择时最上方字段被替换成"系统字段"文本
- **条件显示**: 条件显示为 "student_id == 1" 而不是 "学号 等于 1"
- **边界情况**: formSchema 为空时应优雅降级到英文字段名

## 预期行为

### 保持不变的需求

**不变行为：**
- 字段选择器的基本选择功能必须继续正常工作
- 条件逻辑验证必须继续保持准确性
- 现有的字段数据结构必须保持完整性
- 其他非字段显示相关的功能必须继续正常运行

**范围：**
所有不涉及字段标签显示的输入都应完全不受此修复影响。这包括：
- 字段选择的核心逻辑
- 条件验证和计算
- 数据结构的完整性
- 组件的其他功能

## 假设的根本原因

基于 Bug 描述，最可能的问题是：

1. **formSchema 传递问题**: ConditionRule.vue 可能没有正确接收到 formSchema 参数
   - ConditionBuilderV2.vue 传递 formSchema 时可能存在问题
   - Props 传递链路中可能存在中断

2. **字段选项计算逻辑错误**: fieldOptions 计算属性可能存在逻辑问题
   - 分组显示逻辑导致"系统字段"替换问题
   - FieldLabelService.getFieldLabel() 调用时机不正确

3. **字段加载时机问题**: ConditionBuilderV2.vue 中字段加载可能存在时序问题
   - API 字段和 schema 字段的合并逻辑有问题
   - 字段标签设置在字段加载完成前执行

4. **边界情况处理不当**: FieldLabelService 调用时可能存在边界情况
   - formSchema 为空时的处理逻辑
   - 字段不存在时的降级逻辑

## 正确性属性

Property 1: Bug 条件 - 字段显示本地化

_对于任何_ 字段显示上下文，其中 Bug 条件成立（isBugCondition 返回 true），修复后的组件应该显示通过 FieldLabelService.getFieldLabel() 获取的中文标签，而不是英文字段键名。

**验证: 需求 2.1, 2.2, 2.3, 2.4**

Property 2: 保持不变 - 非显示功能保持

_对于任何_ 不涉及字段标签显示的输入（Bug 条件不成立），修复后的代码应该产生与原始代码完全相同的行为，保持字段选择、条件验证等核心功能不变。

**验证: 需求 3.1, 3.2, 3.3, 3.4**

## 修复实现

### 需要的更改

假设我们的根本原因分析是正确的：

**文件**: `my-app/src/components/flow-configurator/ConditionRule.vue`

**函数**: `fieldOptions` 计算属性

**具体更改**:
1. **修复 formSchema 传递验证**: 确保 props.formSchema 正确传递给 FieldLabelService
   - 添加调试日志验证 formSchema 内容
   - 检查 formSchema.fields 是否存在且有效

2. **修复字段选项计算逻辑**: 确保 FieldLabelService.getFieldLabel() 正确调用
   - 验证字段分组逻辑不会导致"系统字段"替换
   - 确保表单字段和系统字段都正确应用标签映射

3. **添加边界情况处理**: 处理 formSchema 为空的情况
   - 当 formSchema 为空时优雅降级到字段原始名称
   - 添加必要的空值检查

**文件**: `my-app/src/components/flow-configurator/ConditionBuilderV2.vue`

**函数**: 字段加载和传递逻辑

**具体更改**:
4. **验证 formSchema 传递**: 确保 formSchema 正确传递给 ConditionRule
   - 检查 props.formSchema 是否正确传递给子组件
   - 验证字段加载完成后 formSchema 仍然有效

5. **修复字段加载逻辑**: 确保 API 字段和 schema 字段都正确设置标签
   - 在字段加载时应用 FieldLabelService 映射
   - 确保字段合并逻辑不会丢失标签信息

## 测试策略

### 验证方法

测试策略遵循两阶段方法：首先在未修复的代码上展示 Bug 的反例，然后验证修复正确工作并保持现有行为。

### 探索性 Bug 条件检查

**目标**: 在实施修复之前展示 Bug 的反例。确认或反驳根本原因分析。如果我们反驳了，我们需要重新假设。

**测试计划**: 编写测试模拟字段选择和条件显示场景，并断言字段标签正确显示。在未修复的代码上运行这些测试以观察失败并理解根本原因。

**测试用例**:
1. **字段选择器显示测试**: 模拟字段选择，验证显示中文标签（在未修复代码上会失败）
2. **系统字段分组测试**: 模拟字段分组显示，验证不会出现"系统字段"替换（在未修复代码上会失败）
3. **条件显示测试**: 模拟条件数据显示，验证使用中文标签（在未修复代码上会失败）
4. **边界情况测试**: 模拟 formSchema 为空的情况，验证优雅降级（可能在未修复代码上失败）

**预期反例**:
- 字段选择器显示英文字段名而不是中文标签
- 可能的原因：formSchema 传递不正确、字段选项计算逻辑错误、FieldLabelService 调用问题

### 修复检查

**目标**: 验证对于所有 Bug 条件成立的输入，修复后的函数产生预期行为。

**伪代码：**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := fixedComponent(input)
  ASSERT expectedBehavior(result)
END FOR
```

### 保持不变检查

**目标**: 验证对于所有 Bug 条件不成立的输入，修复后的函数产生与原始函数相同的结果。

**伪代码：**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalComponent(input) = fixedComponent(input)
END FOR
```

**测试方法**: 推荐使用基于属性的测试进行保持不变检查，因为：
- 它自动生成输入域中的许多测试用例
- 它捕获手动单元测试可能遗漏的边界情况
- 它为所有非 Bug 输入提供强有力的保证，行为保持不变

**测试计划**: 首先在未修复代码上观察字段选择和条件验证的行为，然后编写基于属性的测试捕获该行为。

**测试用例**:
1. **字段选择功能保持**: 验证字段选择的核心功能继续工作
2. **条件验证保持**: 验证条件逻辑验证继续准确
3. **数据结构保持**: 验证字段数据结构继续完整
4. **其他功能保持**: 验证非字段显示相关功能继续正常

### 单元测试

- 测试 FieldLabelService.getFieldLabel() 在各种 formSchema 情况下的调用
- 测试字段选项计算逻辑的正确性
- 测试边界情况（formSchema 为空、字段不存在等）

### 基于属性的测试

- 生成随机字段配置并验证标签显示正确
- 生成随机 formSchema 并验证字段选择功能保持不变
- 测试在许多场景下条件验证逻辑继续工作

### 集成测试

- 测试完整的条件配置流程中字段标签显示正确
- 测试在不同 formSchema 配置下的字段显示
- 测试字段选择和条件创建的完整用户流程