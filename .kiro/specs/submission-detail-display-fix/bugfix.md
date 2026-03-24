# Bugfix Requirements Document

## Introduction

修复提交详情页面的显示问题：
1. 基本信息卡片显示了过多不必要的字段，应该只显示核心信息
2. 页面显示了不必要的快照信息卡片和流程轨迹卡片
3. 表单数据部分的字段标签显示为英文字段名（如 `rating`、`feedback`）而非中文标签（如 `评分`、`反馈`）

这些问题影响了用户查看提交详情时的体验，导致信息过载和可读性差。根本原因是：
1. 当 `snapshot_json` 为 `null` 或 `field_labels` 为空时，前端回退显示字段的英文键名
2. **后端在从 schema_json 提取字段标签时使用了错误的键名 `field["name"]`，而实际字段使用的是 `field["id"]`**

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN 用户在提交详情页面查看基本信息时 THEN 系统显示了 8 个字段（提交 ID、表单名称、提交人、状态、提交时间、耗时、来源、IP 地址），缺少提交人 ID

1.2 WHEN 用户在提交详情页面时 THEN 系统显示了快照信息卡片和流程轨迹卡片，增加了页面复杂度

1.3 WHEN 提交记录的 `snapshot_json` 为 `null` 或 `snapshot_json.field_labels` 为空时 THEN 表单数据的字段标签显示为英文字段名（如 `rating`、`feedback`、`course_name`）

1.4 WHEN 用户通过 SQL 直接插入提交记录时 THEN `snapshot_json` 字段未被正确填充，导致字段标签无法显示

1.5 **WHEN 后端从 schema_json 提取字段标签时 THEN 代码使用 `field["name"]` 获取字段键名，但实际 schema_json 中字段使用 `field["id"]`，导致提取失败，field_labels 始终为空**

### Expected Behavior (Correct)

2.1 WHEN 用户在提交详情页面查看基本信息时 THEN 系统应只显示 5 个字段：提交 ID、表单名称、提交人、提交人 ID、提交时间

2.2 WHEN 用户在提交详情页面时 THEN 系统不应显示快照信息卡片和流程轨迹卡片

2.3 WHEN 提交记录的 `snapshot_json.field_labels` 存在时 THEN 表单数据的字段标签应显示对应的中文标签

2.4 WHEN 提交记录的 `snapshot_json` 为 `null` 或 `field_labels` 为空时 THEN 系统应从当前表单版本的 `schema_json` 中获取字段标签作为回退方案

2.5 **WHEN 后端从 schema_json 提取字段标签时 THEN 代码应使用 `field["id"]` 获取字段键名，使用 `field["label"]` 获取字段标签**

### Unchanged Behavior (Regression Prevention)

3.1 WHEN 用户在提交详情页面查看表单数据内容时 THEN 系统应继续正确显示所有字段的值

3.2 WHEN 用户在提交详情页面查看附件列表时 THEN 系统应继续正确显示附件信息和下载链接

3.3 WHEN 用户点击"查看原始 JSON"按钮时 THEN 系统应继续正确显示原始数据
