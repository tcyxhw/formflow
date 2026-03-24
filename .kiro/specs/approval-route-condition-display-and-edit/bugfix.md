# Bugfix Requirements Document

## Introduction

在审批流程配置页面的路由条件配置功能中，存在多个影响用户体验的缺陷：

1. **字段选择被替换问题**：在条件构建器中不断滑动选择表单字段时，每次滑动都会被系统字段替换，直到最后只剩下最后一个字段
2. **已配置条件不显示**：已经添加并配置好的审批路由条件无法在界面上展示出来
3. **编辑弹窗缺少条件展示**：在编辑路由属性的弹窗最上方需要展示已配置的条件，并支持重新编辑，但目前不显示
4. **缺少条件管理功能**：无法对已有的审批路由条件进行编辑、删除、查看操作

这些问题严重影响了用户配置审批流程的效率和准确性，需要系统性修复。

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN 用户在 ConditionBuilderV2 组件中通过滑动操作选择表单字段时 THEN 系统会将之前选择的字段替换为系统字段，导致最终只保留最后一个选择的字段

1.2 WHEN 用户已经为路由配置了条件（route.condition 存在 JsonLogic 数据）并关闭条件编辑弹窗后 THEN FlowRouteInspector 组件不显示已配置的条件内容

1.3 WHEN 用户点击"编辑条件"按钮打开条件编辑弹窗时 THEN 弹窗中的 ConditionBuilderV2 组件不显示路由已有的条件配置

1.4 WHEN 用户需要查看、修改或删除已配置的路由条件时 THEN 系统没有提供相应的 UI 交互入口和功能


### Expected Behavior (Correct)

2.1 WHEN 用户在 ConditionBuilderV2 组件中通过滑动操作选择表单字段时 THEN 系统 SHALL 正确保留所有已选择的字段，不会被系统字段替换

2.2 WHEN 用户已经为路由配置了条件（route.condition 存在 JsonLogic 数据）并关闭条件编辑弹窗后 THEN FlowRouteInspector 组件 SHALL 在界面上清晰展示已配置的条件内容（包括字段名、操作符、值等）

2.3 WHEN 用户点击"编辑条件"按钮打开条件编辑弹窗时 THEN 弹窗中的 ConditionBuilderV2 组件 SHALL 正确加载并显示路由已有的条件配置，允许用户在现有基础上进行修改

2.4 WHEN 用户需要查看、修改或删除已配置的路由条件时 THEN 系统 SHALL 提供直观的 UI 交互入口，支持查看条件详情、编辑条件内容、删除单个条件或清空所有条件

### Unchanged Behavior (Regression Prevention)

3.1 WHEN 用户首次为路由添加条件（route.condition 为 null）时 THEN 系统 SHALL CONTINUE TO 正常打开空白的条件编辑器，允许用户从零开始配置条件

3.2 WHEN 用户在条件编辑弹窗中点击"取消"按钮时 THEN 系统 SHALL CONTINUE TO 放弃所有未保存的修改，保持原有条件不变

3.3 WHEN 用户在条件编辑弹窗中点击"保存条件"按钮时 THEN 系统 SHALL CONTINUE TO 将条件转换为 JsonLogic 格式并更新到 route.condition

3.4 WHEN 用户配置的条件包含多层嵌套的 AND/OR 逻辑组时 THEN 系统 SHALL CONTINUE TO 正确处理条件的序列化和反序列化

3.5 WHEN 用户在 FlowRouteInspector 中修改路由的其他属性（优先级、默认路由等）时 THEN 系统 SHALL CONTINUE TO 正常更新这些属性，不影响条件配置功能

3.6 WHEN 用户通过 JSON 编辑器直接编辑条件时 THEN 系统 SHALL CONTINUE TO 支持手动输入 JsonLogic 格式的条件表达式
