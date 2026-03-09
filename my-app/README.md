# 前端说明（Vue 3 + TypeScript + Vite）

## 审批 SLA 徽章 & 筛选

- 组件：`src/components/common/SlaBadge.vue`
  - Props：`level` (`SlaLevel`)、`minutes`(`number | null`)、`showRemaining`(`boolean`)
  - 逻辑：内部根据 `sla_level` 与剩余分钟数渲染 Naive UI Tag，并在需要时拼接剩余时长文案。
- 使用规范：
  1. 在 `<script setup>` 中 `import SlaBadge from '@/components/common/SlaBadge.vue'`。
  2. 模板中以 `<SlaBadge :level="task.sla_level" :minutes="task.remaining_sla_minutes" :show-remaining="true" />` 渲染。
- 筛选：`ApprovalListView` 已提供 `SLA 等级` 下拉框，调用 `listTasks` 时透传 `filters.sla_level`，可在其他页面复用同一 `TaskListQuery` 字段实现同样能力。

## SLA 概览卡片

- API：`getTaskSlaSummary(filters)`，请求参数与列表查询保持一致，后端会在 `/api/v1/approvals/summary` 上返回 `TaskSlaSummary`。
- 组件：`ApprovalListView` 头部的 “SLA 概览” 卡片。
  1. 数据通过 `Promise.all([listTasks, getTaskSlaSummary])` 同步刷新，确保表格与仪表数据一致。
  2. 每个卡片项使用 `SlaBadge` 展示等级标识，展示字段为 `total/normal/warning/critical/expired/unknown`。
  3. 可在其他页面复用 `TaskSlaSummary` 类型快速渲染类似仪表面板。

## 开发提示

- 所有与后端契约对齐的类型统一放在 `src/types` 中，如需新增字段请同步这里以及相应 API 模块。
- UI 中避免直接使用 Tag + 文案组合呈现 SLA 状态，统一走 `SlaBadge` 以保持风格一致。
