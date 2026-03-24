# Bugfix Requirements Document

## Introduction

修复审批控制台中 SLA 时间计算错误的 bug。当前系统混用了 `datetime.now()` (本地时间) 和 `datetime.utcnow()` (UTC 时间)，导致在 UTC+8 时区下 SLA 剩余时间计算出现 8 小时的偏差。例如，从 2026-03-14 09:41 到 2026-03-15 17:30 的剩余时间应为约 31 小时 49 分钟，但系统显示为 39 小时 49 分钟。

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN 计算 SLA 剩余时间时使用 `datetime.utcnow()` 而截止时间基于本地时间 THEN 系统在 UTC+8 时区下计算出的剩余时间比实际多 8 小时

1.2 WHEN `approval_service.py` 的 `_calc_remaining_minutes` 函数使用 `datetime.utcnow()` 计算当前时间 THEN 与数据库中存储的本地时间进行比较时产生时区偏差

1.3 WHEN `sla_service.py` 的 `calculate_due_at` 函数使用 `datetime.utcnow()` 计算截止时间 THEN 生成的截止时间与系统其他部分使用的本地时间不一致

1.4 WHEN 系统同时存在使用 `datetime.now()` 和 `datetime.utcnow()` 的代码 THEN 不同模块之间的时间计算产生不可预测的偏差

### Expected Behavior (Correct)

2.1 WHEN 计算 SLA 剩余时间时 THEN 系统 SHALL 使用一致的时区基准（UTC）进行所有时间计算

2.2 WHEN `_calc_remaining_minutes` 函数计算剩余时间时 THEN 系统 SHALL 使用 timezone-aware 的 datetime 对象确保时区一致性

2.3 WHEN `calculate_due_at` 函数计算截止时间时 THEN 系统 SHALL 返回 UTC 时间并在数据库中以 UTC 格式存储

2.4 WHEN 前端显示时间时 THEN 系统 SHALL 将 UTC 时间转换为用户本地时区进行显示

2.5 WHEN 从 2026-03-14 09:41 (UTC+8) 到 2026-03-15 17:30 (UTC+8) 计算剩余时间 THEN 系统 SHALL 正确显示约 31 小时 49 分钟

### Unchanged Behavior (Regression Prevention)

3.1 WHEN 审批任务的其他时间字段（创建时间、更新时间）已正确存储 THEN 系统 SHALL CONTINUE TO 保持这些字段的正确性

3.2 WHEN SLA 超时判断逻辑正确工作 THEN 系统 SHALL CONTINUE TO 准确判断任务是否超时

3.3 WHEN 审批流程的其他功能（任务分配、状态流转）正常运行 THEN 系统 SHALL CONTINUE TO 保持这些功能不受影响

3.4 WHEN 表单截止时间验证等其他时间相关功能正常工作 THEN 系统 SHALL CONTINUE TO 保持这些功能的正确性

3.5 WHEN 数据库中已存在的审批任务数据 THEN 系统 SHALL CONTINUE TO 正确读取和处理这些历史数据
