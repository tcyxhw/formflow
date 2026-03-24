# 实施计划

- [x] 1. 编写 bug 条件探索测试
  - **Property 1: Bug Condition** - 后端分类访问错误和前端过度显示
  - **关键**: 此测试必须在未修复的代码上失败 - 失败确认 bug 存在
  - **不要在测试失败时尝试修复测试或代码**
  - **注意**: 此测试编码了预期行为 - 在实施后通过时将验证修复
  - **目标**: 暴露反例以证明 bug 存在
  - **作用域 PBT 方法**: 对于确定性 bug，将属性作用域限定为具体失败案例以确保可重现性
  - 测试后端访问 `form.category` 时抛出 AttributeError（来自设计中的 Bug Condition）
  - 测试前端显示快照信息卡片、流程轨迹卡片和 8 个基本信息字段
  - 测试前端字段标签显示为英文 key 而非中文标签
  - 测试断言应匹配设计中的 Expected Behavior Properties
  - 在未修复的代码上运行测试
  - **预期结果**: 测试失败（这是正确的 - 证明 bug 存在）
  - 记录发现的反例以理解根本原因
  - 当测试编写完成、运行并记录失败时标记任务完成
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. 编写保持性属性测试（在实施修复之前）
  - **Property 2: Preservation** - 其他功能保持不变
  - **重要**: 遵循观察优先方法
  - 在未修复的代码上观察非 bug 输入的行为
  - 编写基于属性的测试捕获从 Preservation Requirements 观察到的行为模式
  - 基于属性的测试生成许多测试用例以提供更强保证
  - 在未修复的代码上运行测试
  - **预期结果**: 测试通过（这确认了要保持的基线行为）
  - 当测试编写完成、运行并在未修复代码上通过时标记任务完成
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 3. 修复后端分类访问和前端显示问题

  - [x] 3.1 实施修复
    - 修改 `backend/app/services/form_workspace_service.py` 第 143 行：将 `category=form.category` 改为 `category=form.category_id`
    - 修改 `backend/app/services/form_workspace_service.py` 第 342 行：将 `category=form.category` 改为 `category=form.category_id`
    - 修改 `backend/app/services/form_workspace_service.py` 第 476 行：将 `form.category` 改为 `form.category_id`
    - 修改 `my-app/src/views/submissions/SubmissionDetailView.vue`：移除快照信息卡片（第 68-82 行）
    - 修改 `my-app/src/views/submissions/SubmissionDetailView.vue`：移除流程轨迹卡片（第 145-234 行）
    - 修改 `my-app/src/views/submissions/SubmissionDetailView.vue`：精简基本信息卡片为 3 个字段（提交 ID、表单名称、提交时间）
    - 修改 `my-app/src/views/submissions/SubmissionDetailView.vue`：确保字段标签使用 `snapshot_json.field_labels` 中的中文标签
    - 移除不再使用的响应式变量和函数（`timelineLoading`、`timelineError`、`timeline`、`loadTimeline` 等）
    - _Bug_Condition: isBugCondition(input) 其中 input 访问 form.category 或显示过多信息/英文标签_
    - _Expected_Behavior: expectedBehavior(result) 来自设计_
    - _Preservation: 设计中的 Preservation Requirements_
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3_

  - [x] 3.2 验证 bug 条件探索测试现在通过
    - **Property 1: Expected Behavior** - 后端正确访问分类 ID 和前端精简显示
    - **重要**: 重新运行任务 1 中的相同测试 - 不要编写新测试
    - 任务 1 中的测试编码了预期行为
    - 当此测试通过时，确认满足了预期行为
    - 运行任务 1 中的 bug 条件探索测试
    - **预期结果**: 测试通过（确认 bug 已修复）
    - _Requirements: 设计中的 Expected Behavior Properties_

  - [x] 3.3 验证保持性测试仍然通过
    - **Property 2: Preservation** - 其他功能保持不变
    - **重要**: 重新运行任务 2 中的相同测试 - 不要编写新测试
    - 运行任务 2 中的保持性属性测试
    - **预期结果**: 测试通过（确认无回归）
    - 确认修复后所有测试仍然通过（无回归）

- [x] 4. 检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户。
