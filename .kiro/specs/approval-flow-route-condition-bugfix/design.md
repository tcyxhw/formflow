# 审批流路由条件配置修复 - 设计文档

## 概述

本设计文档针对审批流路由条件配置中的三个主要问题：路由属性绑定混乱、条件字段标签显示不正确、条件编辑弹窗样式混乱。通过实现路由过滤、字段标签本地化和 UI 样式改进，确保每个路由有独立的条件和属性，提升用户体验。

## 术语表

- **Bug_Condition (C)**: 触发 bug 的条件 - 用户在编辑不同节点时，系统显示错误的路由条件或属性
- **Property (P)**: 期望行为 - 系统只显示与当前节点相关的路由，条件使用中文标签显示，UI 样式清晰
- **Preservation**: 保留的行为 - 基本的流程创建、保存、加载功能不受影响
- **FlowRouteInspector**: 路由属性编辑组件，位于 `my-app/src/components/flow-configurator/FlowRouteInspector.vue`
- **ConditionBuilderV2**: 条件构建器组件，位于 `my-app/src/components/flow-configurator/ConditionBuilderV2.vue`
- **FieldLabelService**: 字段标签映射服务，位于 `my-app/src/services/fieldLabelService.ts`
- **currentNodeKey**: 当前编辑的节点的唯一标识符
- **to_node_key**: 路由的目标节点标识符

## Bug 详情

### Bug 条件

bug 在以下情况下触发：

1. **路由属性混乱**: 用户在编辑节点 B 时，系统显示所有路由而不是只显示进入节点 B 的路由（to_node_key = B）
2. **条件数据混乱**: 用户在节点 A 添加条件后切换到节点 B，系统仍然显示节点 A 的条件
3. **字段标签显示错误**: 条件编辑弹窗中显示英文字段名（如 student_id）而不是中文标签（如"学号"）
4. **条件编辑弹窗样式混乱**: 已添加的条件没有清晰的视觉分隔、边框、间距和操作按钮

### 正式规范

```
FUNCTION isBugCondition(input)
  INPUT: input of type UserAction
  OUTPUT: boolean
  
  RETURN (input.action = 'edit_node' AND input.nodeKey = B)
         AND (displayedRoutes.length > relevantRoutes.length)
         OR (input.action = 'view_condition' AND conditionFieldsUseEnglishNames)
         OR (input.action = 'view_condition' AND conditionItemsLackVisualSeparation)
END FUNCTION
```

### 示例

**示例 1 - 路由属性混乱**
- 当前行为: 编辑节点 B 时，显示所有 5 条路由
- 期望行为: 编辑节点 B 时，只显示 2 条进入节点 B 的路由（to_node_key = B）

**示例 2 - 条件数据混乱**
- 当前行为: 在节点 A 添加条件"金额 > 1000"后，切换到节点 B，仍然显示"金额 > 1000"
- 期望行为: 切换到节点 B 后，显示节点 B 的条件（可能为空或不同的条件）

**示例 3 - 字段标签显示错误**
- 当前行为: 条件编辑弹窗显示"student_id 等于 123"
- 期望行为: 条件编辑弹窗显示"学号 等于 123"

**示例 4 - 条件编辑弹窗样式混乱**
- 当前行为: 已添加的条件项没有边框、间距混乱、操作按钮不清晰
- 期望行为: 每个条件项有清晰的边框、充足的间距、明确的编辑/删除按钮

## 期望行为

### 保留需求

**不变的行为:**
- 创建新的审批流时，系统仍然能够正确创建节点和路由
- 保存审批流配置时，系统仍然能够正确保存所有节点和路由数据到数据库
- 查看已保存的审批流时，系统仍然能够正确加载并显示所有节点和路由数据
- 删除节点时，系统仍然能够正确删除相关的路由和条件数据
- 在条件构建器中添加条件规则时，系统仍然能够正确验证条件表达式的有效性
- 在条件编辑弹窗中编辑条件时，系统仍然能够正确保存条件到路由配置中

**作用域:**
所有不涉及路由过滤、字段标签显示、条件编辑弹窗样式的操作应该完全不受影响。这包括：
- 节点的创建、编辑、删除
- 路由的创建、删除
- 条件表达式的验证和计算
- 流程的保存和加载

## 假设的根本原因

基于 bug 描述，最可能的问题是：

1. **路由过滤缺失**: FlowRouteInspector 组件没有根据 `currentNodeKey` 过滤路由，导致显示所有路由而不是只显示进入当前节点的路由

2. **路由选择逻辑错误**: 当用户在路由列表中选择一条路由时，没有正确关联到该路由的条件数据

3. **字段标签映射缺失**: 在 `formatConditionForDisplay` 函数中，没有使用 `FieldLabelService` 获取字段的中文标签，而是直接显示字段键

4. **条件编辑弹窗样式不完善**: `conditions-list-section` 的样式定义不完整，条件项的边框、间距、背景色不清晰

5. **字段标签在条件编辑弹窗中显示不正确**: 在条件编辑弹窗中，条件项显示的字段名没有转换为中文标签

## 正确性属性

Property 1: 路由过滤 - 只显示进入当前节点的路由

_对于任何_ 用户编辑节点 B 的操作，修复后的 FlowRouteInspector 组件 SHALL 只显示 to_node_key = B 的路由，不显示其他路由。

**验证: 需求 2.2**

Property 2: 条件数据关联 - 条件正确关联到具体的路由

_对于任何_ 用户在节点 A 添加条件后切换到节点 B 的操作，修复后的系统 SHALL 显示节点 B 的条件（可能为空或不同的条件），不显示节点 A 的条件。

**验证: 需求 2.1**

Property 3: 字段标签本地化 - 条件显示使用中文标签

_对于任何_ 用户在条件编辑弹窗中查看已添加条件的操作，修复后的系统 SHALL 显示中文字段标签（如"学号"），不显示英文字段名（如 student_id）。

**验证: 需求 2.3**

Property 4: 条件编辑弹窗样式 - 条件项有清晰的视觉分隔

_对于任何_ 用户在条件编辑弹窗中查看已添加条件的操作，修复后的系统 SHALL 为每个条件项提供清晰的边框、充足的间距、明确的操作按钮。

**验证: 需求 2.4**

Property 5: 路由属性独立性 - 每个路由有独立的属性值

_对于任何_ 用户在节点 A 修改路由优先级或默认状态的操作，修复后的系统 SHALL 正确区分不同的路由，每个路由有独立的属性值。

**验证: 需求 2.5**

Property 6: 保留 - 基本功能不受影响

_对于任何_ 不涉及路由过滤、字段标签显示、条件编辑弹窗样式的操作，修复后的系统 SHALL 产生与原始系统相同的结果。

**验证: 需求 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## 修复实现

### 修改清单

#### 1. FlowRouteInspector 组件 - 路由过滤修复

**文件**: `my-app/src/components/flow-configurator/FlowRouteInspector.vue`

**修改内容**:

1. **添加路由过滤计算属性**
   - 在 `relevantRoutes` 计算属性中，根据 `currentNodeKey` 过滤路由
   - 只显示 `to_node_key === currentNodeKey` 的路由
   - 确保路由列表与当前编辑的节点相关

2. **修复路由选择逻辑**
   - 当用户选择一条路由时，确保正确关联到该路由的条件数据
   - 使用 `from_node_key` 和 `to_node_key` 作为路由的唯一标识符

3. **改进路由描述显示**
   - 在路由信息横幅中显示"从 X 到 Y"的清晰描述
   - 在条件编辑弹窗中显示当前编辑的路由信息

#### 2. ConditionBuilderV2 组件 - 字段标签本地化修复

**文件**: `my-app/src/components/flow-configurator/ConditionBuilderV2.vue`

**修改内容**:

1. **集成 FieldLabelService**
   - 在组件中导入 `FieldLabelService`
   - 在字段列表中添加字段标签信息

2. **改进字段显示**
   - 在条件规则中显示字段标签而不是字段键
   - 在字段选择下拉菜单中显示"标签（键）"格式

#### 3. FlowRouteInspector 组件 - 字段标签显示修复

**文件**: `my-app/src/components/flow-configurator/FlowRouteInspector.vue`

**修改内容**:

1. **改进 formatConditionForDisplay 函数**
   - 使用 `FieldLabelService.getFieldLabel()` 获取字段的中文标签
   - 在条件显示中使用标签而不是字段键

2. **在条件编辑弹窗中显示中文标签**
   - 在 `conditions-list-section` 中，条件项显示中文标签
   - 确保字段标签映射正确

#### 4. FlowRouteInspector 组件 - 条件编辑弹窗样式改进

**文件**: `my-app/src/components/flow-configurator/FlowRouteInspector.vue`

**修改内容**:

1. **改进 conditions-list-section 样式**
   - 为每个条件项添加清晰的边框（1px solid #dbeafe）
   - 添加充足的间距（padding: 12px）
   - 添加背景色（#ffffff）
   - 添加圆角（border-radius: 4px）

2. **改进条件项布局**
   - 条件文本和操作按钮分别显示
   - 操作按钮（编辑、删除）清晰可见
   - 添加条件计数显示（"共 N 个"）

3. **改进条件操作按钮**
   - 编辑按钮：type="primary"，text 样式
   - 删除按钮：type="error"，text 样式
   - 按钮之间有适当的间距

4. **添加条件分组显示**
   - 在列表头部显示条件计数
   - 为不同的条件组添加视觉分隔

### 样式改进方案

#### conditions-list-section 样式

```css
.conditions-list-section {
  margin-bottom: 24px;
  padding: 16px;
  background: #f0f7ff;
  border-radius: 6px;
  border: 1px solid #bfdbfe;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.list-title {
  font-size: 13px;
  font-weight: 600;
  color: #1e40af;
}

.list-count {
  font-size: 12px;
  color: #6b7385;
}

.conditions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.condition-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #ffffff;
  border-radius: 4px;
  border: 1px solid #dbeafe;
}

.condition-text {
  flex: 1;
  font-size: 13px;
  color: #374151;
  line-height: 1.6;
  word-break: break-word;
}

.condition-actions {
  display: flex;
  gap: 8px;
  margin-left: 12px;
  flex-shrink: 0;
}
```

### 字段标签映射逻辑

#### formatConditionForDisplay 函数改进

```typescript
const formatConditionForDisplay = (json: any): string => {
  // ... 现有代码 ...
  
  // 获取字段的显示名称（优先使用标签，其次使用 API 字段名）
  const getFieldLabel = (fieldKey: string): string => {
    // 先从 formSchema 查找
    if (props.formSchema?.fields) {
      const field = props.formSchema.fields.find(f => f.id === fieldKey)
      if (field?.label) return field.label
    }
    
    // 使用 FieldLabelService 获取标签
    const label = FieldLabelService.getFieldLabel(fieldKey, props.formSchema)
    return label !== fieldKey ? label : fieldKey
  }
  
  // ... 在条件显示中使用 getFieldLabel ...
}
```

### 路由过滤逻辑

#### relevantRoutes 计算属性

```typescript
// 获取与当前节点相关的路由（进入该节点的路由）
const relevantRoutes = computed(() => {
  if (!props.currentNodeKey || !props.routes) return []
  
  // 只显示进入当前节点的路由（to_node_key = 当前节点）
  return props.routes.filter(route => route.to_node_key === props.currentNodeKey)
})
```

## 测试策略

### 验证方法

测试策略采用两阶段方法：首先在未修复代码上演示 bug，然后验证修复后的代码正确性并保留现有行为。

### 探索性 Bug 条件检查

**目标**: 在修复前演示 bug，确认或反驳根本原因分析。如果反驳，需要重新假设。

**测试计划**: 编写测试模拟用户在不同节点编辑路由的场景，验证显示的路由是否正确过滤。

**测试用例**:

1. **路由过滤测试**: 编辑节点 B 时，验证只显示 to_node_key = B 的路由（在未修复代码上会失败）
2. **条件数据关联测试**: 在节点 A 添加条件后切换到节点 B，验证显示的条件是否正确（在未修复代码上会失败）
3. **字段标签显示测试**: 在条件编辑弹窗中，验证显示的是中文标签而不是英文字段名（在未修复代码上会失败）
4. **条件编辑弹窗样式测试**: 验证条件项是否有清晰的边框、间距和操作按钮（在未修复代码上会失败）

**期望的反例**:
- 路由过滤失败：显示所有路由而不是只显示进入当前节点的路由
- 条件数据混乱：显示错误节点的条件
- 字段标签显示错误：显示英文字段名而不是中文标签
- 条件编辑弹窗样式混乱：条件项没有清晰的视觉分隔

### 修复检查

**目标**: 验证对于所有触发 bug 条件的输入，修复后的函数产生期望的行为。

**伪代码**:
```
FOR ALL input WHERE isBugCondition(input) DO
  result := fixedComponent(input)
  ASSERT expectedBehavior(result)
END FOR
```

### 保留检查

**目标**: 验证对于所有不触发 bug 条件的输入，修复后的函数产生与原始函数相同的结果。

**伪代码**:
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalComponent(input) = fixedComponent(input)
END FOR
```

**测试方法**: 基于属性的测试推荐用于保留检查，因为：
- 自动生成许多测试用例，覆盖输入域
- 捕获手动单元测试可能遗漏的边界情况
- 提供强有力的保证，确保行为不变

**测试计划**: 首先观察未修复代码上的行为（鼠标点击、其他交互），然后编写基于属性的测试捕获该行为。

**测试用例**:

1. **节点创建保留**: 验证创建新节点的功能不受影响
2. **路由创建保留**: 验证创建新路由的功能不受影响
3. **条件验证保留**: 验证条件表达式验证的功能不受影响
4. **流程保存保留**: 验证保存审批流配置的功能不受影响
5. **流程加载保留**: 验证加载已保存审批流的功能不受影响
6. **节点删除保留**: 验证删除节点的功能不受影响

### 单元测试

- 测试 `relevantRoutes` 计算属性是否正确过滤路由
- 测试 `formatConditionForDisplay` 函数是否正确显示中文标签
- 测试 `getFieldLabel` 函数是否正确获取字段标签
- 测试路由选择逻辑是否正确关联条件数据
- 测试条件编辑弹窗是否正确显示条件项

### 基于属性的测试

- 生成随机节点和路由配置，验证路由过滤的正确性
- 生成随机字段和条件，验证字段标签显示的正确性
- 生成随机用户操作序列，验证条件数据关联的正确性
- 验证修复前后的行为一致性（对于非 bug 输入）

### 集成测试

- 测试完整的流程编辑流程：创建节点 → 创建路由 → 编辑条件 → 保存
- 测试节点切换时的条件数据正确性
- 测试条件编辑弹窗的完整工作流
- 测试字段标签在不同场景下的显示正确性
