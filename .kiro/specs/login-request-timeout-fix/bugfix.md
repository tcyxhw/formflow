# Bugfix Requirements Document

## Introduction

用户报告登录请求一直卡住直到超时，后端没有收到请求也没有报错。经过代码分析发现，问题出在审计日志装饰器 (`@audit_log`) 中：在异步上下文中使用了同步的数据库会话创建方式 (`SessionLocal()`)，导致请求被阻塞。

具体问题：
- `backend/app/utils/audit.py` 中的 `create_audit_log` 函数是异步函数
- 当没有传入 `db` 参数时，会调用 `SessionLocal()` 创建新的数据库会话
- `SessionLocal()` 是同步的 SQLAlchemy 会话工厂，在异步上下文中调用会导致阻塞
- 登录接口使用了 `@audit_log` 装饰器，触发了这个问题

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN 登录接口被调用时 THEN 审计日志装饰器尝试在异步上下文中使用同步数据库会话 (`SessionLocal()`)，导致请求永久阻塞直到超时

1.2 WHEN 审计日志装饰器中 `db` 参数为 `None` 时 THEN 系统调用同步的 `SessionLocal()` 创建数据库会话，在异步环境中造成死锁

1.3 WHEN 任何使用 `@audit_log` 装饰器的异步路由被调用且未正确传递 `db` 参数时 THEN 请求会被阻塞

### Expected Behavior (Correct)

2.1 WHEN 登录接口被调用时 THEN 审计日志应该使用异步数据库会话或正确处理同步会话，请求应该在合理时间内完成（< 5秒）

2.2 WHEN 审计日志装饰器中 `db` 参数为 `None` 时 THEN 系统应该使用异步方式创建数据库会话，或者跳过审计日志记录并记录警告

2.3 WHEN 任何使用 `@audit_log` 装饰器的异步路由被调用时 THEN 审计日志记录不应该阻塞主请求流程

### Unchanged Behavior (Regression Prevention)

3.1 WHEN 审计日志装饰器接收到有效的 `db` 参数时 THEN 系统应该继续正常记录审计日志

3.2 WHEN 其他不使用审计日志装饰器的接口被调用时 THEN 系统应该继续正常工作

3.3 WHEN 审计日志记录成功时 THEN 数据库中应该继续正确保存审计记录

3.4 WHEN 审计日志记录失败时 THEN 主请求流程不应该受到影响（已有的错误处理逻辑应该保持）
