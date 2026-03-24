# 审批流程配置UX缺陷修复 - 实现任务清单

## 任务概览

本任务清单包含两个UX缺陷的修复实现：
1. **缺陷1**：条件设置空间受限 - 将条件编辑改为独立模态框
2. **缺陷2**：开始/结束节点显示不必要的配置 - 根据节点类型条件渲染

---

## 缺陷2：开始/结束节点配置优化（优先实现）

### 2.1 添加条件渲染逻辑

- [x] 2.1.1 在 FlowNodeInspector.vue 中添加三个辅助方法
  - `shouldShowApprovalConfig(nodeType)` - 判断是否显示审批配置
  - `shouldShowConditionConfig(nodeType)` - 判断是否显示条件配置
  - `shouldShowBasicInfoHint(nodeType)` - 判断是否显示基本信息提示
  - _Requirements: 2.2, 2.3_

### 2.2 隐藏开始节点的审批配置

- [x] 2.2.1 在 FlowNodeInspector.vue 中，将审批相关字段用 `v-if="shouldShowApprovalConfig(node.type)"` 包装
  - 包括：负责人类型、审批策略、SLA、允许代理、驳回策略、自动审批
  - _Requirements: 2.2_

- [x] 2.2.2 为开始节点添加信息提示
  - 使用 `n-alert` 组件显示："开始节点是流程的入口点，无需配置审批相关参数。"
  - 仅在 `node.type === 'start'` 时显示
  - _Requirements: 2.2_

### 2.3 隐藏结束节点的审批配置

- [x] 2.3.1 在 FlowNodeInspector.vue 中，结束节点也使用相同的条件渲染逻辑
  - _Requirements: 2.3_

- [x] 2.3.2 为结束节点添加信息提示
  - 使用 `n-alert` 组件显示："结束节点是流程的终点，无需配置审批相关参数。"
  - 仅在 `node.type === 'end'` 时显示
  - _Requirements: 2.3_

### 2.4 验证其他节点类型不受影响

- [x] 2.4.1 验证人工审批节点（user）显示所有审批配置
  - _Requirements: 3.1_

- [x] 2.4.2 验证自动节点（auto）显示所有审批配置
  - _Requirements: 3.2_

- [x] 2.4.3 验证条件节点（condition）显示条件分支配置，不显示审批配置
  - _Requirements: 3.3_

---

## 缺陷1：条件编辑模态框实现

### 1.1 添加模态框状态管理

- [x] 1.1.1 在 FlowNodeInspector.vue 中添加两个新的 ref 状态
  - `showConditionModal` - 控制模态框显示/隐藏
  - `editingConditionBranches` - 存储临时编辑的条件数据
  - _Requirements: 2.1_

### 1.2 实现模态框打开逻辑

- [x] 1.2.1 在 FlowNodeInspector.vue 中添加 `openConditionModal()` 方法
  - 复制 `node.condition_branches` 到 `editingConditionBranches`
  - 设置 `showConditionModal = true`
  - _Requirements: 2.1_

- [x] 1.2.2 在条件节点配置区域添加"编辑条件"按钮
  - 点击时调用 `openConditionModal()`
  - 按钮类型为 primary
  - _Requirements: 2.1_

### 1.3 实现模态框保存逻辑

- [x] 1.3.1 在 FlowNodeInspector.vue 中添加 `saveCondition()` 方法
  - 调用 `emitPatch({ condition_branches: editingConditionBranches })`
  - 设置 `showConditionModal = false`
  - _Requirements: 2.1_

- [x] 1.3.2 在模态框中配置正按钮（保存）
  - 点击时调用 `saveCondition()`
  - _Requirements: 2.1_

### 1.4 实现模态框取消逻辑

- [x] 1.4.1 在 FlowNodeInspector.vue 中添加 `cancelCondition()` 方法
  - 清空 `editingConditionBranches`
  - 设置 `showConditionModal = false`
  - _Requirements: 2.1_

- [x] 1.4.2 在模态框中配置负按钮（取消）
  - 点击时调用 `cancelCondition()`
  - _Requirements: 2.1_

### 1.5 添加模态框组件

- [x] 1.5.1 在 FlowNodeInspector.vue 中添加 `n-modal` 组件
  - 标题："编辑条件表达式"
  - 宽度：1000px（large preset）
  - 预设：dialog
  - 可关闭：false
  - 遮罩可关闭：false
  - 正按钮：保存
  - 负按钮：取消
  - _Requirements: 2.1_

- [x] 1.5.2 在模态框中嵌入 ConditionNodeEditor 组件
  - 传递 `editingConditionBranches` 作为 modelValue
  - 传递其他必要的 props（allNodes、formSchema、formId、disabled）
  - 监听 `update:modelValue` 事件，更新 `editingConditionBranches`
  - _Requirements: 2.1_

### 1.6 从面板中移除内嵌条件编辑器

- [x] 1.6.1 在 FlowNodeInspector.vue 中，将条件节点配置改为显示"编辑条件"按钮
  - 移除原有的 ConditionNodeEditor 内嵌显示
  - 添加条件分支数量显示
  - _Requirements: 2.1_

### 1.7 验证条件编辑功能保持不变

- [x] 1.7.1 验证在模态框中可以添加条件规则
  - _Requirements: 3.4_

- [x] 1.7.2 验证在模态框中可以添加条件分组
  - _Requirements: 3.4_

- [x] 1.7.3 验证在模态框中可以删除条件规则
  - _Requirements: 3.4_

- [x] 1.7.4 验证条件数据的保存和丢弃功能正常
  - _Requirements: 3.5_

---

## 集成测试

### 3.1 完整流程测试

- [x] 3.1.1 创建包含开始、人工审批、条件、结束节点的流程
  - 验证每个节点显示正确的配置字段
  - _Requirements: 2.2, 2.3, 3.1, 3.2, 3.3_

- [x] 3.1.2 编辑条件节点的条件表达式
  - 点击"编辑条件"打开模态框
  - 在模态框中修改条件
  - 点击"保存"，验证条件已更新
  - _Requirements: 2.1, 3.4, 3.5_

- [x] 3.1.3 验证流程数据正确保存
  - 保存流程
  - 重新加载流程
  - 验证所有节点配置正确
  - _Requirements: 2.1, 2.2, 2.3_

### 3.2 回归测试

- [x] 3.2.1 验证人工审批节点的所有配置功能正常
  - 修改负责人类型、审批策略、SLA 等
  - 验证数据正确保存
  - _Requirements: 3.1_

- [x] 3.2.2 验证条件节点的条件编辑功能正常
  - 添加/修改/删除条件规则
  - 验证条件数据正确保存
  - _Requirements: 3.3, 3.4, 3.5_

- [x] 3.2.3 验证流程的其他功能不受影响
  - 节点的添加/删除/连接
  - 流程的保存/加载
  - _Requirements: 3.1, 3.2, 3.3_

---

## 代码质量检查

### 4.1 代码风格检查

- [x] 4.1.1 运行 ESLint 检查 FlowNodeInspector.vue
  - 修复所有 linting 错误
  - 确保代码风格一致

- [x] 4.1.2 运行 TypeScript 类型检查
  - 确保没有类型错误
  - 所有新增代码都有正确的类型注解

### 4.2 单元测试

- [x] 4.2.1 为 FlowNodeInspector.vue 添加单元测试
  - 测试条件渲染逻辑
  - 测试模态框打开/关闭
  - 测试条件数据保存/丢弃

### 4.3 文档更新

- [x] 4.3.1 更新 FlowNodeInspector.vue 的 README
  - 说明新增的条件渲染逻辑
  - 说明模态框的使用方式

---

## 验收标准

### 缺陷1的验收标准

- ✅ 条件编辑在独立模态框中显示
- ✅ 模态框宽度足够显示完整的条件编辑器
- ✅ 点击"保存"，条件数据正确更新
- ✅ 点击"取消"，条件数据保持不变
- ✅ 条件编辑的所有功能（添加规则、添加分组、删除规则等）正常工作
- ✅ 其他节点类型的配置不受影响

### 缺陷2的验收标准

- ✅ 开始节点仅显示"节点名称"和"节点类型"
- ✅ 开始节点显示信息提示
- ✅ 结束节点仅显示"节点名称"和"节点类型"
- ✅ 结束节点显示信息提示
- ✅ 人工审批节点显示所有审批配置
- ✅ 自动节点显示所有审批配置
- ✅ 条件节点显示条件分支配置
- ✅ 节点类型切换时，配置字段正确更新

---

## 实现建议

### 代码组织

1. **FlowNodeInspector.vue 的改动**
   - 在 `<script setup>` 中添加新的状态和方法
   - 在 `<template>` 中添加条件渲染逻辑和模态框
   - 在 `<style>` 中添加新的样式（如果需要）

2. **保持代码可读性**
   - 使用清晰的方法名称（如 `shouldShowApprovalConfig`）
   - 添加注释说明条件渲染的逻辑
   - 保持缩进和格式一致

### 测试建议

1. **手动测试**
   - 在浏览器中打开流程设计器
   - 创建不同类型的节点，验证配置字段的显示
   - 编辑条件节点，验证模态框的功能

2. **自动化测试**
   - 为新增的方法编写单元测试
   - 为条件渲染逻辑编写集成测试
   - 运行现有的测试，确保没有回归

### 性能考虑

- 条件编辑模态框的打开/关闭不会影响其他组件的性能
- 条件渲染逻辑使用简单的 `v-if`，性能开销很小
- 没有额外的 API 调用或数据处理

---

## 时间估计

| 任务 | 估计时间 |
|------|---------|
| 2.1 - 2.4 缺陷2实现 | 1-2 小时 |
| 1.1 - 1.7 缺陷1实现 | 2-3 小时 |
| 3.1 - 3.2 集成测试 | 1-2 小时 |
| 4.1 - 4.3 代码质量 | 1 小时 |
| **总计** | **5-8 小时** |

---

## 相关文件

- `my-app/src/components/flow-configurator/FlowNodeInspector.vue` - 主要改动文件
- `my-app/src/components/flow-configurator/ConditionNodeEditor.vue` - 无需改动
- `my-app/src/components/flow-configurator/ConditionBuilderV2.vue` - 无需改动
- `my-app/src/types/flow.ts` - 类型定义（无需改动）
- `my-app/src/types/condition.ts` - 条件类型定义（无需改动）

---

## 注意事项

1. **保持向后兼容**
   - 确保现有的流程数据能正确加载
   - 确保节点配置的保存格式不变

2. **测试覆盖**
   - 测试所有节点类型的配置显示
   - 测试模态框的打开/关闭/保存/取消
   - 测试条件编辑的所有功能

3. **用户体验**
   - 确保模态框的大小合适
   - 确保按钮的位置和标签清晰
   - 确保信息提示的内容准确

4. **代码审查**
   - 在提交前进行代码审查
   - 确保代码风格一致
   - 确保没有遗留的调试代码
