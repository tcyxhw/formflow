# 实现计划

- [x] 1. 编写 Bug Condition 探索测试
  - **Property 1: Bug Condition** - 异步上下文中同步数据库操作导致事件循环阻塞
  - **关键**: 此测试必须在未修复的代码上失败 - 失败确认 bug 存在
  - **不要在测试失败时尝试修复测试或代码**
  - **注意**: 此测试编码了预期行为 - 在实现修复后通过时将验证修复
  - **目标**: 暴露反例，证明 bug 存在
  - **作用域 PBT 方法**: 对于确定性 bug，将属性作用域限定为具体的失败案例以确保可重现性
  - 测试登录场景：`AuthService.login()` 调用 `UserService.find_user_by_account()` 时请求应在 5 秒内完成
  - 测试认证中间件场景：需要认证的请求调用 `UserService.find_user_by_id()` 时不应被阻塞
  - 测试注册场景：`AuthService.register()` 调用 `UserService.create_user()` 时请求应在 5 秒内完成
  - 测试并发场景：多个登录请求同时发送时不应全部被阻塞
  - 在未修复的代码上运行测试
  - **预期结果**: 测试失败（这是正确的 - 证明 bug 存在）
  - 记录发现的反例以理解根本原因
  - 当测试编写完成、运行并记录失败时标记任务完成
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. 编写 Preservation 属性测试（在实现修复之前）
  - **Property 2: Preservation** - 数据库查询结果和错误处理保持不变
  - **重要**: 遵循观察优先方法
  - 观察未修复代码上的行为：对于非 bug 条件输入
    - `find_user_by_account()` 成功时返回 User 对象，失败时返回 None
    - `find_user_by_id()` 成功时返回 User 对象，失败时返回 None
    - `check_account_exists()` 返回布尔值
    - `create_user()` 成功时返回新创建的 User 对象
  - 编写属性测试捕获观察到的行为模式（来自设计文档中的 Preservation Requirements）
  - 属性测试为更强的保留保证生成许多测试用例
  - 在未修复的代码上运行测试
  - **预期结果**: 测试通过（这确认了要保留的基线行为）
  - 当测试编写完成、运行并在未修复代码上通过时标记任务完成
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 3. 修复 UserService 同步方法导致的事件循环阻塞

  - [x] 3.1 将 UserService 所有方法改为异步
    - 将所有 `def` 改为 `async def`
    - 使用 `await db.execute(select(...))` 替代 `db.query(...)`
    - 使用 `result.scalar_one_or_none()` 或 `result.scalars().all()` 获取结果
    - 确保返回的数据格式与原同步方法完全一致
    - _Bug_Condition: isBugCondition(context, method_call) where context.is_async == True AND method_call.target == UserService AND method_call.method.is_sync == True_
    - _Expected_Behavior: 所有数据库操作使用异步方式执行，不阻塞事件循环，请求在 5 秒内完成（来自设计文档）_
    - _Preservation: 数据库查询返回的数据格式、内容、错误处理逻辑必须保持不变（来自设计文档）_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.4_

  - [x] 3.2 更新所有调用点添加 await
    - 在 `AuthService.login()` 中的调用添加 `await`
    - 在 `AuthService.refresh_token()` 中的调用添加 `await`
    - 在 `AuthService.register()` 中的调用添加 `await`
    - 在 `ValidationService` 中的调用添加 `await`（如果有）
    - 在 `AuthMiddleware` 中的调用添加 `await`（如果有）
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 3.3 验证 Bug Condition 探索测试现在通过
    - **Property 1: Expected Behavior** - 异步数据库操作不阻塞事件循环
    - **重要**: 重新运行步骤 1 中的相同测试 - 不要编写新测试
    - 步骤 1 中的测试编码了预期行为
    - 当此测试通过时，确认预期行为得到满足
    - 运行步骤 1 中的 Bug Condition 探索测试
    - **预期结果**: 测试通过（确认 bug 已修复）
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 3.4 验证 Preservation 测试仍然通过
    - **Property 2: Preservation** - 数据库查询结果和错误处理保持不变
    - **重要**: 重新运行步骤 2 中的相同测试 - 不要编写新测试
    - 运行步骤 2 中的 Preservation 属性测试
    - **预期结果**: 测试通过（确认没有回归）
    - 确认修复后所有测试仍然通过（没有回归）

- [ ] 4. 检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户
