# 流程审批路由条件绑定 Bug 修复设计

## 概述

本设计文档针对流程审批配置页面中的两个关键 Bug 进行修复：

1. **路由属性绑定问题**：路由属性和条件没有与当前节点绑定，导致所有节点共享同一个路由属性和条件，而不是只显示进入该节点的路由。

2. **条件显示本地化问题**：条件展示使用英文字段名（如 `student_id`）而不是中文字段标签（如 "学号"），降低了用户体验。

修复策略采用最小化改动原则，通过改进路由过滤逻辑和条件显示中的字段标签本地化，确保用户在配置复杂审批流程时能够准确识别和操作路由条件。

## 术语表

- **Bug_Condition (C)**: 触发 Bug 的条件 - 当用户在流程审批配置页面选择一个节点时，系统显示所有路由而不是只显示进入该节点的路由，或者条件显示使用英文字段名而不是中文标签
- **Property (P)**: 期望行为 - 系统应该只显示进入当前节点的路由，并使用中文字段标签显示条件
- **Preservation**: 保持不变的行为 - 其他路由属性编辑、条件编辑操作、节点切换等功能应该继续正常工作
- **FlowRouteInspector**: 位于 `my-app/src/components/flow-configurator/FlowRouteInspector.vue` 的路由检查器组件，负责显示和编辑路由属性和条件
- **ConditionRule**: 位于 `my-app/src/components/flow-configurator/ConditionRule.vue` 的条件规则组件，负责显示单个条件规则
- **FieldLabelService**: 位于 `my-app/src/services/fieldLabelService.ts` 的字段标签服务，提供字段键到中文标签的映射
- **currentNodeKey**: 当前选中节点的唯一标识符
- **to_node_key**: 路由的目标节点标识符
- **fieldKey**: 条件中使用的字段的唯一标识符（英文）
- **JsonLogic**: 用于表示条件的 JSON 格式，内部使用英文字段名

## Bug 详情

### Bug 条件

Bug 在以下情况下触发：

1. 用户在流程审批配置页面选择一个节点时，系统显示所有路由的属性和条件，而不仅仅是进入该节点的路由
2. 用户查看路由条件时，系统使用英文字段名（如 `student_id`）显示条件，而不是中文字段标签（如 "学号"）
3. 用户编辑路由条件中的字段选择时，系统显示的字段列表使用英文字段名，而不是中文字段标签

**形式化规范：**

```
FUNCTION isBugCondition(input)
  INPUT: input of type {
    selectedNodeKey: string,
    routes: FlowRouteConfig[],
    displayedRoutes: FlowRouteConfig[],
    conditionDisplay: string,
    fieldLabels: Record<string, string>
  }
  OUTPUT: boolean
  
  RETURN (selectedNodeKey is not null)
         AND (displayedRoutes.length > 0)
         AND (EXISTS route IN displayedRoutes WHERE route.to_node_key != selectedNodeKey)
         OR (conditionDisplay contains English fieldKey instead of Chinese label)
         OR (fieldSelector displays English fieldKey instead of Chinese label)
END FUNCTION
```

### 示例

**示例 1：路由过滤问题**
- 场景：用户在流程配置页面选择了"审批人审核"节点
- 当前行为：系统显示所有 5 条路由（包括进入其他节点的路由）
- 期望行为：系统应该只显示进入"审批人审核"节点的 2 条路由
- 影响：用户无法准确识别哪些路由进入当前节点，容易误操作

**示例 2：条件显示本地化问题**
- 场景：用户查看一条路由的条件，条件为"学号等于1"
- 当前行为：系统显示"student_id 等于 1"（使用英文字段名）
- 期望行为：系统应该显示"学号 等于 1"（使用中文字段标签）
- 影响：用户需要记住英文字段名才能理解条件，降低工作效率

**示例 3：字段选择器本地化问题**
- 场景：用户在条件编辑器中选择字段
- 当前行为：字段列表显示"student_id"、"class_name"等英文字段名
- 期望行为：字段列表应该显示"学号"、"班级名称"等中文字段标签
- 影响：用户需要记住英文字段名才能选择正确的字段

**边界情况：无路由进入当前节点**
- 场景：用户选择了一个没有任何路由进入的节点
- 期望行为：系统应该显示"请选择一条路由"的提示，而不是显示其他节点的路由

## 期望行为

### 保持不变的行为

**不变行为 1：路由属性编辑**
- 当用户编辑路由的优先级、默认路由标志等属性时，系统应该继续正常保存这些属性
- 这些属性的编辑不应该受到路由过滤改动的影响

**不变行为 2：条件编辑操作**
- 当用户在条件编辑模态框中添加、编辑或删除条件时，系统应该继续正常处理这些操作
- 条件的内部表示（JsonLogic 格式）应该继续使用英文字段名，不改变数据格式

**不变行为 3：节点切换**
- 当用户切换不同的节点时，系统应该正确更新显示的路由列表和条件
- 路由列表应该根据新选中的节点进行过滤

**不变行为 4：JSON 编辑器**
- 当用户查看 JSON 编辑器中的 JsonLogic 格式时，系统应该继续使用英文字段名作为内部表示
- 不改变数据格式，只改变显示层的本地化

**范围说明：**
所有不涉及路由过滤和条件显示本地化的功能应该完全不受影响。这包括：
- 路由的创建、删除、更新
- 条件的逻辑组合（AND/OR）
- 其他节点属性的编辑
- 流程的保存和发布

## 根本原因分析

基于 Bug 描述和代码分析，最可能的根本原因包括：

### 原因 1：路由过滤逻辑缺失

在 `FlowRouteInspector.vue` 中，组件接收 `route` prop 来显示单个路由的属性。但是，当用户选择一个节点时，系统应该根据 `currentNodeKey` 过滤路由，只显示进入该节点的路由（`to_node_key === currentNodeKey`）。

当前代码中虽然定义了 `relevantRoutes` 计算属性，但这个属性没有被用于过滤显示的路由。组件仍然显示所有传入的路由。

### 原因 2：条件显示中缺少字段标签映射

在 `formatConditionForDisplay` 函数中，虽然有 `getFieldLabel` 函数调用，但这个函数依赖于 `formSchema` prop。如果 `formSchema` 没有正确传递或为空，函数会回退到使用英文字段名。

同时，在 `ConditionRule.vue` 中的字段选择器，虽然使用了 `fieldOptions` 计算属性，但这个属性直接使用 `f.name` 作为标签。如果 `f.name` 没有正确设置为中文标签，就会显示英文字段名。

### 原因 3：字段定义中的标签不一致

在 `ConditionRule.vue` 中，`fieldOptions` 计算属性使用 `f.name` 作为标签。但是，传入的 `fields` prop 中的 `name` 字段可能没有正确设置为中文标签，而是使用了英文字段名。

### 原因 4：FieldLabelService 没有被充分利用

虽然 `FieldLabelService` 提供了从 `formSchema` 中提取字段标签的功能，但在 `ConditionRule.vue` 中没有使用这个服务。组件直接使用 `fields` prop 中的 `name` 字段，而不是从 `formSchema` 中获取标签。

## 正确性属性

Property 1: Bug 条件 - 路由过滤和条件显示本地化

_对于任何_ 用户选择一个节点的输入，修复后的 `FlowRouteInspector` 组件 SHALL 只显示进入该节点的路由（`to_node_key === currentNodeKey`），并使用中文字段标签显示条件（从 `formSchema` 中获取），格式为"中文标签 运算符 数值"（例如"学号等于1"）。

**验证需求：2.1, 2.2, 2.3**

Property 2: 保持不变 - 其他功能保持不变

_对于任何_ 不涉及路由过滤和条件显示本地化的输入（如编辑路由属性、编辑条件、切换节点等），修复后的代码 SHALL 产生与原始代码相同的结果，保持所有现有功能不变。

**验证需求：3.1, 3.2, 3.3, 3.4**

## 修复实现

### 所需改动

假设我们的根本原因分析是正确的：

**文件 1：`my-app/src/components/flow-configurator/FlowRouteInspector.vue`**

**函数：`relevantRoutes` 计算属性和路由显示逻辑**

**具体改动：**

1. **改动 1：改进路由过滤逻辑**
   - 在 `relevantRoutes` 计算属性中，添加对 `currentNodeKey` 的检查
   - 只返回 `to_node_key === currentNodeKey` 的路由
   - 确保当没有路由进入当前节点时，显示"请选择一条路由"的提示

2. **改动 2：改进条件显示中的字段标签映射**
   - 在 `formatConditionForDisplay` 函数中，确保 `getFieldLabel` 函数正确使用 `formSchema`
   - 当 `formSchema` 为空时，提供合理的备选方案（使用英文字段名）
   - 在递归处理 JsonLogic 表达式时，对所有字段引用都应用标签映射

3. **改动 3：改进字段选择器中的标签显示**
   - 在 `ConditionRule.vue` 中，改进 `fieldOptions` 计算属性
   - 使用 `FieldLabelService.getFieldLabel()` 从 `formSchema` 中获取中文标签
   - 确保字段列表显示中文标签而不是英文字段名

4. **改动 4：确保 formSchema 正确传递**
   - 检查 `FlowRouteInspector` 的所有调用处，确保 `formSchema` prop 被正确传递
   - 如果 `formSchema` 为空，添加日志警告，便于调试

5. **改动 5：改进条件显示的可读性**
   - 在 `formatConditionForDisplay` 函数中，改进条件的文本格式
   - 确保显示的条件易于理解，例如"学号 等于 1"而不是"student_id == 1"

**文件 2：`my-app/src/components/flow-configurator/ConditionRule.vue`**

**函数：`fieldOptions` 计算属性**

**具体改动：**

1. **改动 1：使用 FieldLabelService 获取字段标签**
   - 导入 `FieldLabelService`
   - 在 `fieldOptions` 计算属性中，使用 `FieldLabelService.getFieldLabel()` 获取中文标签
   - 确保字段列表显示中文标签

2. **改动 2：改进字段选项的分组显示**
   - 保持现有的"表单字段"和"系统字段"分组
   - 在每个分组中，使用中文标签而不是英文字段名

## 测试策略

### 验证方法

测试策略采用两阶段方法：首先，在未修复的代码上运行测试以观察 Bug 的表现；然后，验证修复后的代码能够正确处理 Bug 并保持现有功能不变。

### 探索性 Bug 条件检查

**目标**：在修复前运行测试以观察 Bug 的表现，确认或反驳根本原因分析。如果反驳，我们需要重新分析。

**测试计划**：编写测试来模拟用户选择不同节点时的路由显示情况，以及条件显示中的字段标签。在未修复的代码上运行这些测试以观察失败情况和理解根本原因。

**测试用例**：

1. **路由过滤测试**：选择一个节点，验证只显示进入该节点的路由（将在未修复代码上失败）
2. **条件显示本地化测试**：查看路由条件，验证使用中文字段标签而不是英文字段名（将在未修复代码上失败）
3. **字段选择器本地化测试**：打开条件编辑器，验证字段列表显示中文标签（将在未修复代码上失败）
4. **无路由进入节点测试**：选择一个没有任何路由进入的节点，验证显示"请选择一条路由"的提示（可能在未修复代码上失败）

**期望的反例**：
- 路由过滤失败：显示了不应该显示的路由
- 条件显示失败：使用了英文字段名而不是中文标签
- 字段选择器失败：显示了英文字段名而不是中文标签

### 修复检查

**目标**：验证对于所有 Bug 条件成立的输入，修复后的函数产生期望的行为。

**伪代码：**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := FlowRouteInspector_fixed(input)
  ASSERT result.displayedRoutes.every(route => route.to_node_key === input.selectedNodeKey)
  ASSERT result.conditionDisplay contains Chinese labels, not English fieldKeys
  ASSERT result.fieldSelector displays Chinese labels, not English fieldKeys
END FOR
```

### 保持不变检查

**目标**：验证对于所有 Bug 条件不成立的输入，修复后的函数产生与原始函数相同的结果。

**伪代码：**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT FlowRouteInspector_original(input) = FlowRouteInspector_fixed(input)
END FOR
```

**测试方法**：属性基测试推荐用于保持不变检查，因为：
- 它自动生成许多测试用例，覆盖输入域
- 它捕获手动单元测试可能遗漏的边界情况
- 它提供强有力的保证，确保行为对所有非 Bug 输入保持不变

**测试计划**：首先在未修复代码上观察行为（路由属性编辑、条件编辑、节点切换等），然后编写属性基测试来验证这些行为在修复后继续保持不变。

**测试用例**：

1. **路由属性编辑保持不变**：验证编辑优先级、默认路由标志等属性继续正常工作
2. **条件编辑操作保持不变**：验证添加、编辑、删除条件继续正常工作
3. **节点切换保持不变**：验证切换不同节点时路由列表正确更新
4. **JSON 编辑器保持不变**：验证 JsonLogic 格式继续使用英文字段名，不改变数据格式
5. **条件逻辑组合保持不变**：验证 AND/OR 逻辑组合继续正常工作

### 单元测试

- 测试 `relevantRoutes` 计算属性，验证路由过滤逻辑
- 测试 `formatConditionForDisplay` 函数，验证条件显示中的字段标签映射
- 测试 `ConditionRule.vue` 中的 `fieldOptions` 计算属性，验证字段选择器中的标签显示
- 测试 `FieldLabelService` 的各个方法，验证字段标签映射的正确性

### 属性基测试

- 生成随机的节点选择和路由配置，验证路由过滤逻辑
- 生成随机的条件和字段配置，验证条件显示中的字段标签映射
- 生成随机的字段列表，验证字段选择器中的标签显示
- 验证修复前后的行为一致性（对于非 Bug 输入）

### 集成测试

- 测试完整的流程配置工作流，包括选择节点、查看路由、编辑条件等
- 测试在不同的表单 Schema 下的行为
- 测试在没有 formSchema 的情况下的备选方案
- 测试条件编辑模态框的打开、编辑、保存流程
