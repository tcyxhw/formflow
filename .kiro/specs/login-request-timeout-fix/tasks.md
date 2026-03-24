# 实施计划

- [x] 1. 编写 Bug Condition 探索性测试
  - **Property 1: Bug Condition** - 审计日志阻塞异步请求
  - **关键**: 此测试必须在未修复代码上失败 - 失败证明 bug 存在
  - **不要在测试失败时尝试修复测试或代码**
  - **注意**: 此测试编码了期望行为 - 修复后通过时将验证修复有效
  - **目标**: 暴露证明 bug 存在的反例
  - **作用域 PBT 方法**: 对于确定性 bug，将属性作用域限定为具体失败案例以确保可重现性
  - 测试实现细节来自设计文档中的 Bug Condition
  - 测试断言应匹配设计文档中的 Expected Behavior Properties
  - 在未修复代码上运行测试
  - **预期结果**: 测试失败（这是正确的 - 证明 bug 存在）
  - 记录发现的反例以理解根本原因
  - 当测试编写、运行并记录失败时标记任务完成
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. 编写保持性属性测试（在实施修复前）
  - **Property 2: Preservation** - 审计日志功能完整性
  - **重要**: 遵循观察优先方法
  - 在未修复代码上观察非 bug 输入的行为
  - 编写属性测试捕获来自 Preservation Requirements 的观察行为模式
  - 属性测试自动生成许多测试用例以提供更强保证
  - 在未修复代码上运行测试
  - **预期结果**: 测试通过（确认要保持的基线行为）
  - 当测试在未修复代码上编写、运行并通过时标记任务完成
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. 修复审计日志阻塞问题

  - [x] 3.1 实施修复
    - 修改 `backend/app/utils/audit.py`：
      - 新增 `_background_create_audit_log` 函数，在后台任务中使用独立的同步会话创建审计日志
      - 修改 `audit_log` 装饰器，检测 `BackgroundTasks` 参数并将审计日志记录添加到后台任务
      - 在 `create_audit_log` 中移除阻塞性的 `SessionLocal()` 调用，改为记录警告
    - 更新所有使用 `@audit_log` 装饰器的异步路由，添加 `BackgroundTasks` 参数：
      - `backend/app/api/v1/auth.py` - 登录、注册、刷新令牌等接口
      - `backend/app/api/v1/admin.py` - 管理员操作接口
      - `backend/app/api/v1/forms.py` - 表单相关接口
      - `backend/app/api/v1/submissions.py` - 提交相关接口
      - `backend/app/api/v1/flows.py` - 流程相关接口
      - 其他使用审计日志的接口
    - _Bug_Condition: isBugCondition(input) where input.route.has_decorator('@audit_log') AND input.route.is_async AND input.db_parameter IS None_
    - _Expected_Behavior: 审计日志记录在后台任务中异步执行，主请求在 5 秒内完成_
    - _Preservation: 审计日志数据格式、字段、错误处理逻辑保持不变_
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 验证 Bug Condition 探索性测试现在通过
    - **Property 1: Expected Behavior** - 审计日志不阻塞请求
    - **重要**: 重新运行任务 1 中的相同测试 - 不要编写新测试
    - 任务 1 中的测试编码了期望行为
    - 当此测试通过时，确认期望行为已满足
    - 运行任务 1 中的 Bug Condition 探索性测试
    - **预期结果**: 测试通过（确认 bug 已修复）
    - _Requirements: Expected Behavior Properties from design_

  - [x] 3.3 验证保持性测试仍然通过
    - **Property 2: Preservation** - 审计日志功能完整性
    - **重要**: 重新运行任务 2 中的相同测试 - 不要编写新测试
    - 运行任务 2 中的保持性属性测试
    - **预期结果**: 测试通过（确认无回归）
    - 确认修复后所有测试仍然通过（无回归）

- [x] 4. 检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户
