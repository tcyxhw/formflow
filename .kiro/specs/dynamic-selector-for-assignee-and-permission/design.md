# 动态选择器功能 Bugfix 设计

## 概述

本次修复旨在为审批流程配置（FlowNodeInspector.vue）和表单权限配置（FormPermissionDrawer.vue）添加动态选择器功能。当用户选择不同的类型（用户、角色、部门、岗位、群组、表达式）时，系统应显示对应的选择器组件，而不是让用户手动输入 ID。

这个修复将显著提升用户体验，减少配置错误，使审批流程和权限配置更加直观和高效。

## 术语表

- **Bug_Condition (C)**: 用户选择了特定类型（用户/角色/部门/岗位/群组/表达式）但系统未显示对应选择器的情况
- **Property (P)**: 当用户选择特定类型时，系统应显示对应的选择器组件并允许用户选择具体对象
- **Preservation**: 现有的类型选择、数据保存、表单验证等功能必须保持不变
- **FlowNodeInspector**: 审批流程节点属性配置组件，位于 `my-app/src/components/flow-configurator/FlowNodeInspector.vue`
- **FormPermissionDrawer**: 表单权限配置抽屉组件，位于 `my-app/src/components/form/FormPermissionDrawer.vue`
- **assignee_type**: 审批节点的负责人类型字段（user/role/group/department/position/expr）
- **assignee_value**: 审批节点的负责人值字段，存储选中对象的 ID 或表达式
- **grant_type**: 权限授权类型字段（user/role/department/position）
- **grantee_id**: 权限授权对象 ID 字段

## Bug 详情

### Bug Condition

当用户在配置审批流程或表单权限时选择了特定的类型，但系统没有提供相应的选择器来选择具体对象。这导致用户必须手动输入 ID（对于权限配置）或无法输入任何值（对于审批流程配置），严重影响了配置的便利性和准确性。

**形式化规范:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type { component: string, selectedType: string }
  OUTPUT: boolean
  
  RETURN (input.component == 'FlowNodeInspector' 
          AND input.selectedType IN ['user', 'role', 'group', 'department', 'position', 'expr']
          AND NOT hasSelectorForType(input.selectedType))
         OR
         (input.component == 'FormPermissionDrawer'
          AND input.selectedType IN ['user', 'role', 'department', 'position']
          AND NOT hasSelectorForType(input.selectedType))
END FUNCTION
```

### 示例

- **FlowNodeInspector - 选择"用户"类型**: 用户选择负责人类型为"用户"后，界面上没有显示用户选择器，用户无法选择具体的用户作为审批负责人
- **FlowNodeInspector - 选择"角色"类型**: 用户选择负责人类型为"角色"后，界面上没有显示角色下拉框，用户无法选择具体的角色
- **FlowNodeInspector - 选择"表达式"类型**: 用户选择负责人类型为"表达式"后，界面上没有显示文本输入框，用户无法输入表达式
- **FormPermissionDrawer - 选择"部门"类型**: 用户选择授权类型为"部门"后，界面上只显示一个"对象ID"的数字输入框，用户必须手动输入部门 ID 而不能从列表中选择

## 期望行为

### Preservation Requirements

**不变行为:**
- 类型选择下拉框的功能和选项必须保持不变
- 数据保存逻辑（assignee_type、assignee_value、grant_type、grantee_id）必须保持不变
- 表单验证规则必须保持不变
- 其他节点属性配置（审批策略、SLA、驳回策略等）必须保持不变
- 权限配置的其他属性（权限类型、生效时间、失效时间等）必须保持不变
- 节点类型为"开始"、"结束"、"条件分支"时的界面显示逻辑必须保持不变

**范围:**
所有不涉及选择器显示的功能都应完全不受影响，包括：
- 类型选择的保存和读取
- 表单提交和验证
- 数据的序列化和反序列化
- 组件的其他交互逻辑

## 假设的根本原因

基于 Bug 描述和代码分析，最可能的问题是：

1. **缺少条件渲染逻辑**: 组件中没有根据选择的类型动态显示不同选择器的逻辑
   - FlowNodeInspector.vue 中选择 assignee_type 后没有对应的 v-if 条件渲染
   - FormPermissionDrawer.vue 中只有一个固定的数字输入框

2. **缺少后端 API 接口**: 前端需要调用后端 API 获取用户、角色、部门、岗位、群组列表，但这些接口可能不完整
   - 需要获取用户列表的接口（支持搜索）
   - 需要获取角色列表的接口
   - 需要获取部门列表的接口
   - 需要获取岗位列表的接口
   - 需要获取群组列表的接口

3. **缺少前端 API 封装**: 即使后端接口存在，前端可能没有对应的 API 调用封装

4. **数据字段使用不当**: assignee_value 字段可能没有被正确使用来存储选中的值

## 正确性属性

Property 1: Bug Condition - 动态选择器显示

_对于任何_ 用户在 FlowNodeInspector 或 FormPermissionDrawer 中选择了特定类型（用户/角色/部门/岗位/群组/表达式）的输入，修复后的组件应该显示对应的选择器组件，并允许用户从列表中选择具体对象或输入表达式。

**验证需求: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10**

Property 2: Preservation - 现有功能保持不变

_对于任何_ 不涉及选择器显示的操作（类型选择、数据保存、表单验证、其他属性配置），修复后的代码应该产生与原始代码完全相同的行为，保持所有现有功能不变。

**验证需求: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## 修复实现

### 需要的变更

假设我们的根本原因分析是正确的：

**后端文件**: 
- `backend/app/api/v1/users.py` - 可能需要添加或修改接口
- `backend/app/api/v1/admin.py` - 可能需要添加角色、部门、岗位、群组查询接口

**前端文件**:
- `my-app/src/components/flow-configurator/FlowNodeInspector.vue`
- `my-app/src/components/form/FormPermissionDrawer.vue`
- `my-app/src/api/` - 需要添加新的 API 调用封装

**具体变更**:

1. **后端 API 接口**:
   - 添加 `GET /api/v1/users/list` - 获取用户列表（支持分页和搜索）
   - 添加 `GET /api/v1/roles/list` - 获取角色列表
   - 添加 `GET /api/v1/departments/list` - 获取部门列表
   - 添加 `GET /api/v1/positions/list` - 获取岗位列表
   - 添加 `GET /api/v1/groups/list` - 获取审批群组列表

2. **前端 API 封装**:
   - 在 `my-app/src/api/` 目录下创建或更新对应的 API 调用函数
   - 定义 TypeScript 类型接口

3. **FlowNodeInspector.vue 改造**:
   - 添加 `assignee_value` 字段的 v-model 绑定
   - 根据 `assignee_type` 的值条件渲染不同的选择器：
     - `user`: 使用 `n-select` 组件，支持远程搜索用户
     - `role`: 使用 `n-select` 组件，显示角色列表
     - `group`: 使用 `n-select` 组件，显示群组列表
     - `department`: 使用 `n-select` 组件，显示部门列表
     - `position`: 使用 `n-select` 组件，显示岗位列表
     - `expr`: 使用 `n-input` 组件，允许输入表达式
   - 添加数据加载逻辑和状态管理

4. **FormPermissionDrawer.vue 改造**:
   - 替换固定的 `n-input-number` 组件为动态选择器
   - 根据 `grant_type` 的值条件渲染不同的选择器：
     - `user`: 使用 `n-select` 组件，支持远程搜索用户
     - `role`: 使用 `n-select` 组件，显示角色列表
     - `department`: 使用 `n-select` 组件，显示部门列表
     - `position`: 使用 `n-select` 组件，显示岗位列表
   - 添加数据加载逻辑和状态管理

5. **数据存储方式**:
   - FlowNodeInspector: 将选中的 ID 或表达式存储到 `assignee_value` 字段
   - FormPermissionDrawer: 将选中的 ID 存储到 `grantee_id` 字段（保持现有逻辑）

## 测试策略

### 验证方法

测试策略遵循两阶段方法：首先在未修复的代码上展示 Bug 的反例，然后验证修复后的代码能正确工作并保持现有行为。

### 探索性 Bug Condition 检查

**目标**: 在实现修复之前展示 Bug 的反例。确认或反驳根本原因分析。如果反驳，需要重新假设。

**测试计划**: 编写测试用例模拟用户在两个组件中选择不同类型的场景，并断言应该显示对应的选择器。在未修复的代码上运行这些测试以观察失败并理解根本原因。

**测试用例**:
1. **FlowNodeInspector - 用户类型测试**: 选择负责人类型为"用户"，验证是否显示用户选择器（未修复代码上会失败）
2. **FlowNodeInspector - 角色类型测试**: 选择负责人类型为"角色"，验证是否显示角色选择器（未修复代码上会失败）
3. **FlowNodeInspector - 表达式类型测试**: 选择负责人类型为"表达式"，验证是否显示文本输入框（未修复代码上会失败）
4. **FormPermissionDrawer - 部门类型测试**: 选择授权类型为"部门"，验证是否显示部门选择器而不是数字输入框（未修复代码上会失败）

**预期反例**:
- 选择器组件未渲染或渲染了错误的组件类型
- 可能原因：缺少条件渲染逻辑、缺少后端 API、缺少前端 API 封装

### Fix Checking

**目标**: 验证对于所有满足 Bug 条件的输入，修复后的功能产生期望的行为。

**伪代码:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := renderSelector_fixed(input)
  ASSERT expectedBehavior(result)
END FOR
```

**测试方法**: 
- 单元测试：测试每个选择器组件的渲染逻辑
- 集成测试：测试完整的用户交互流程（选择类型 -> 显示选择器 -> 选择对象 -> 保存数据）

### Preservation Checking

**目标**: 验证对于所有不满足 Bug 条件的输入，修复后的功能产生与原始功能相同的结果。

**伪代码:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalBehavior(input) = fixedBehavior(input)
END FOR
```

**测试方法**: 属性测试推荐用于 Preservation 检查，因为：
- 它自动生成许多测试用例覆盖输入域
- 它能捕获手动单元测试可能遗漏的边界情况
- 它为所有非 Bug 输入提供强有力的行为不变保证

**测试计划**: 首先在未修复的代码上观察现有行为，然后编写属性测试捕获该行为。

**测试用例**:
1. **类型选择保持不变**: 验证选择类型后 assignee_type 和 grant_type 字段正确保存
2. **其他属性配置保持不变**: 验证审批策略、SLA、驳回策略等配置继续正常工作
3. **表单验证保持不变**: 验证现有的表单验证规则继续生效
4. **节点类型判断保持不变**: 验证开始、结束、条件分支节点的界面显示逻辑不受影响

### 单元测试

- 测试每个选择器组件的条件渲染逻辑
- 测试 API 调用和数据加载
- 测试数据绑定和更新逻辑
- 测试边界情况（空列表、加载失败、网络错误）

### 属性测试

- 生成随机的类型选择组合，验证选择器正确显示
- 生成随机的节点配置，验证数据保存的完整性
- 测试在多种场景下现有功能保持不变

### 集成测试

- 测试完整的审批流程配置流程（选择类型 -> 选择对象 -> 保存 -> 验证）
- 测试完整的权限配置流程（选择类型 -> 选择对象 -> 保存 -> 验证）
- 测试在不同节点类型下的配置流程
- 测试数据的持久化和回显
