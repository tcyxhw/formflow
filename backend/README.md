# 后端服务说明

## 审批任务 SLA 字段

| 字段 | 位置 | 说明 |
| --- | --- | --- |
| `sla_level` | `TaskResponse`、`TimelineEntry` | 通过剩余分钟数计算的等级标识，枚举：`unknown / normal / warning / critical / expired` |
| `remaining_sla_minutes` | `TaskResponse`、`TimelineEntry` | 任务距离到期的分钟数；逾期时返回 `0` |

> 等级划分策略：`expired (<=0 分钟)`、`critical (0-30 分钟)`、`warning (30-120 分钟)`、`normal (>120 分钟)`、`unknown (无截止时间)`。

## GET `/api/v1/approvals`

| 参数 | 类型 | 描述 |
| --- | --- | --- |
| `page` | int | 页码，默认 1 |
| `page_size` | int | 每页数量，默认 20 |
| `status` | string | 任务状态，可选 `open/claimed/completed/canceled` |
| `only_mine` | bool | 是否仅查看个人任务，默认 `true` |
| `include_group_tasks` | bool | 是否包含所属小组的待办池，默认 `true` |
| `keyword` | string | 节点 / 流程名模糊匹配 |
| `sla_level` | string | 新增：按 SLA 等级过滤，取值同上表 |

- 当传入 `sla_level=unknown` 时，仅返回未配置截止时间的任务。
- 其他等级会根据当前时间与任务 `due_at` 的关系自动过滤。

## 响应示例（节选）

```json
{
  "items": [
    {
      "id": 101,
      "node_name": "部门经理审批",
      "remaining_sla_minutes": 42,
      "sla_level": "warning"
    }
  ],
  "total": 1
}
```

前端可直接使用 `sla_level` 渲染徽章、排序或筛选。

## GET `/api/v1/approvals/summary`

| 参数 | 类型 | 描述 |
| --- | --- | --- |
| `status` | string | 与列表接口一致，用于同步过滤 |
| `only_mine` | bool | 是否仅统计个人任务 |
| `include_group_tasks` | bool | 是否包含小组待办池 |
| `keyword` | string | 模糊搜索条件（可选） |
| `sla_level` | string | 叠加特定 SLA 等级过滤（可选） |

响应内容：

```json
{
  "total": 120,
  "unknown": 5,
  "normal": 80,
  "warning": 20,
  "critical": 10,
  "expired": 5
}
```

> 服务端会复用 `TaskListRequest` 的可见性与筛选逻辑，确保仪表卡片与列表数据保持一致。
