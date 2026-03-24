# Bugfix Requirements Document

## Introduction

用户报告前端发送登录请求一直超时，但后端没有任何日志输出，说明请求根本没有到达后端路由层。经过代码分析发现，问题出在 `UserService` 中：所有数据库操作方法都是同步的（没有 `async def`），但它们在异步的 `AuthService.login()` 和 `AuthMiddleware` 中被调用，导致同步的数据库查询阻塞了异步事件循环。

具体问题：
- `backend/app/services/user_service.py` 中的所有方法都是同步的（`def` 而不是 `async def`）
- 这些方法在异步上下文中被调用（`AuthService.login()`, `AuthMiddleware`, `ValidationService` 等）
- 同步的 SQLAlchemy 数据库查询在异步事件循环中执行会导致阻塞
- 请求在中间件层就被阻塞，永远无法到达路由层，因此后端没有任何日志输出
- 前端请求一直等待直到超时（180秒）

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN 前端发送登录请求时 THEN 请求在 `AuthMiddleware` 中调用同步的 `UserService` 方法进行数据库查询，导致异步事件循环被阻塞，请求永久挂起直到超时

1.2 WHEN 任何需要认证的请求到达 `AuthMiddleware` 时 THEN 中间件可能调用同步的数据库操作（如 `UserService.find_user_by_id()`），导致请求被阻塞

1.3 WHEN `AuthService.login()` 调用 `UserService.find_user_by_account()` 时 THEN 同步的数据库查询阻塞异步事件循环，导致登录流程无法完成

1.4 WHEN `ValidationService` 调用 `UserService` 的同步方法时 THEN 验证流程被阻塞，影响所有需要验证的接口

### Expected Behavior (Correct)

2.1 WHEN 前端发送登录请求时 THEN 所有数据库操作应该使用异步方式执行，请求应该在合理时间内完成（< 5秒）

2.2 WHEN 任何需要认证的请求到达 `AuthMiddleware` 时 THEN 中间件中的所有数据库操作应该是异步的，不阻塞事件循环

2.3 WHEN `AuthService.login()` 调用用户查询方法时 THEN 应该使用异步的数据库查询，不阻塞主流程

2.4 WHEN `ValidationService` 进行数据验证时 THEN 所有数据库操作应该是异步的

### Unchanged Behavior (Regression Prevention)

3.1 WHEN 数据库查询成功时 THEN 返回的数据格式和内容应该与修复前完全一致

3.2 WHEN 用户不存在或查询失败时 THEN 错误处理逻辑应该保持不变

3.3 WHEN 其他不涉及 `UserService` 的接口被调用时 THEN 应该继续正常工作

3.4 WHEN 数据库事务需要提交或回滚时 THEN 事务处理逻辑应该保持不变

3.5 WHEN 用户信息被缓存时 THEN 缓存逻辑应该保持不变
