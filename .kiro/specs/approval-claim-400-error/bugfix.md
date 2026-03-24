# Bugfix Requirements Document

## Introduction

用户在审批控制台点击"认领"按钮时，前端向后端发送 `POST /api/v1/approvals/{task_id}/claim` 请求，但收到 400 Bad Request 错误响应。该问题阻塞了整个审批工作流，用户无法认领、通过或驳回任务。

经过代码分析发现，问题可能源于以下几个方面：
- 前端发送的POST请求没有请求体，但后端可能期望某些参数
- 后端的审计日志装饰器可能在处理空请求体时出错
- 认证中间件的错误响应可能被CORS拦截，导致前端无法获取具体错误信息
- 后端日志中间件可能抑制了错误输出

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN 用户在审批控制台点击"认领"按钮 THEN 前端调用 `claimTask(taskId)` 发送 POST 请求到 `/api/v1/approvals/{task_id}/claim`，但收到 400 Bad Request 错误

1.2 WHEN 后端收到认领请求 THEN 后端没有输出任何错误日志，导致无法定位问题原因

1.3 WHEN 前端收到400错误 THEN 前端显示"认领失败"消息，但无法获取具体的错误详情

1.4 WHEN 审批任务状态为 'open' 且用户有权限认领 THEN 认领操作仍然失败并返回400错误

### Expected Behavior (Correct)

2.1 WHEN 用户在审批控制台点击"认领"按钮 THEN 前端应成功发送认领请求，后端正确处理并返回200状态码和更新后的任务数据

2.2 WHEN 后端处理认领请求时发生错误 THEN 后端应在日志中输出详细的错误信息（包括堆栈跟踪），便于开发者定位问题

2.3 WHEN 前端收到错误响应 THEN 前端应能够获取到具体的错误消息（如"任务已被认领"、"无权限认领"等），并显示给用户

2.4 WHEN 审批任务状态为 'open' 且用户有权限认领 THEN 认领操作应成功执行，任务状态更新为 'claimed'，claimed_by 字段设置为当前用户ID

2.5 WHEN 后端的审计日志装饰器处理POST请求 THEN 装饰器应正确处理没有请求体的情况，不应导致400错误

2.6 WHEN 认证中间件返回错误响应 THEN 响应应包含正确的CORS头，确保前端能够接收到错误详情

### Unchanged Behavior (Regression Prevention)

3.1 WHEN 用户认领已被其他人认领的任务 THEN 系统应继续返回业务错误"任务已被其他人认领"

3.2 WHEN 用户认领不属于自己或自己小组的任务 THEN 系统应继续返回权限错误"无权处理该任务"

3.3 WHEN 用户成功认领任务后 THEN 系统应继续记录审计日志，包含操作者、操作时间和操作详情

3.4 WHEN 用户执行其他审批操作（通过、驳回、转交等） THEN 这些操作应继续正常工作，不受认领功能修复的影响

3.5 WHEN 后端处理其他POST请求（如创建表单、提交审批等） THEN 这些请求应继续正常工作，不受审计装饰器修复的影响

3.6 WHEN 前端发送其他API请求 THEN 认证中间件应继续正确处理令牌验证和刷新，CORS配置应保持不变
