# Bugfix 需求文档

## 介绍

在表单审批配置页面（FlowNodeInspector.vue）和表单权限配置页面（FormPermissionDrawer.vue）中，用户选择不同的类型（如用户、角色、部门、岗位等）后，系统没有提供对应的选择器来选择具体的对象。用户只能看到一个通用的输入框或数字输入框，无法方便地选择具体的用户、角色、部门或岗位。

这个问题影响了用户体验，使得配置审批流程和权限时需要手动输入 ID，容易出错且不够直观。

## Bug 分析

### 当前行为（缺陷）

1.1 WHEN 用户在 FlowNodeInspector.vue 中选择"负责人类型"为"用户"、"角色"、"群组"、"部门"或"岗位"时 THEN 系统不显示任何对应的选择器，用户无法选择具体的对象

1.2 WHEN 用户在 FormPermissionDrawer.vue 中选择"授权类型"为"用户"、"角色"、"部门"或"岗位"后 THEN 系统仅显示一个"对象ID"的数字输入框，用户必须手动输入 ID 而无法从列表中选择

1.3 WHEN 用户在 FlowNodeInspector.vue 中选择"负责人类型"为"表达式"时 THEN 系统不显示文本输入框供用户输入表达式

### 期望行为（正确）

2.1 WHEN 用户在 FlowNodeInspector.vue 中选择"负责人类型"为"用户"时 THEN 系统应显示用户选择器（输入框或下拉框），允许用户通过用户名或 ID 选择具体用户

2.2 WHEN 用户在 FlowNodeInspector.vue 中选择"负责人类型"为"角色"时 THEN 系统应显示角色下拉选择器，列出可选的角色列表

2.3 WHEN 用户在 FlowNodeInspector.vue 中选择"负责人类型"为"群组"时 THEN 系统应显示群组下拉选择器，列出可选的群组列表

2.4 WHEN 用户在 FlowNodeInspector.vue 中选择"负责人类型"为"部门"时 THEN 系统应显示部门下拉选择器，列出可选的部门列表

2.5 WHEN 用户在 FlowNodeInspector.vue 中选择"负责人类型"为"岗位"时 THEN 系统应显示岗位下拉选择器，列出可选的岗位列表

2.6 WHEN 用户在 FlowNodeInspector.vue 中选择"负责人类型"为"表达式"时 THEN 系统应显示文本输入框，允许用户输入表达式

2.7 WHEN 用户在 FormPermissionDrawer.vue 中选择"授权类型"为"用户"时 THEN 系统应显示用户选择器（输入框或下拉框），允许用户通过用户名或 ID 选择具体用户

2.8 WHEN 用户在 FormPermissionDrawer.vue 中选择"授权类型"为"角色"时 THEN 系统应显示角色下拉选择器，列出可选的角色列表

2.9 WHEN 用户在 FormPermissionDrawer.vue 中选择"授权类型"为"部门"时 THEN 系统应显示部门下拉选择器，列出可选的部门列表

2.10 WHEN 用户在 FormPermissionDrawer.vue 中选择"授权类型"为"岗位"时 THEN 系统应显示岗位下拉选择器，列出可选的岗位列表

### 不变行为（回归预防）

3.1 WHEN 用户在 FlowNodeInspector.vue 中选择"负责人类型"为任意类型时 THEN 系统应继续保存所选类型到 `assignee_type` 字段

3.2 WHEN 用户在 FormPermissionDrawer.vue 中选择"授权类型"为任意类型时 THEN 系统应继续保存所选类型到 `grant_type` 字段

3.3 WHEN 用户在 FlowNodeInspector.vue 中配置其他节点属性（如审批策略、SLA、驳回策略等）时 THEN 系统应继续正常保存这些配置

3.4 WHEN 用户在 FormPermissionDrawer.vue 中配置权限的其他属性（如权限类型、生效时间、失效时间等）时 THEN 系统应继续正常保存这些配置

3.5 WHEN 用户在两个组件中进行任何配置操作时 THEN 系统应继续保持现有的表单验证逻辑

3.6 WHEN 用户在 FlowNodeInspector.vue 中选择节点类型为"开始"、"结束"或"条件分支"时 THEN 系统应继续显示对应的配置界面而不显示负责人类型选择器
