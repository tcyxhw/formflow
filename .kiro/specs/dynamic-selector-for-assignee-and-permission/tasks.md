# 实现计划

- [x] 1. 编写 Bug Condition 探索测试
  - **Property 1: Bug Condition** - 动态选择器缺失验证
  - **关键**: 此测试必须在未修复的代码上失败 - 失败确认 bug 存在
  - **不要在测试失败时尝试修复测试或代码**
  - **注意**: 此测试编码了期望行为 - 修复后通过时将验证修复
  - **目标**: 展示 bug 存在的反例
  - **作用域 PBT 方法**: 对于确定性 bug，将属性作用域限定为具体失败案例以确保可重现性
  - 测试 FlowNodeInspector 组件：选择 assignee_type 为 'user'/'role'/'group'/'department'/'position'/'expr' 时应显示对应选择器
  - 测试 FormPermissionDrawer 组件：选择 grant_type 为 'user'/'role'/'department'/'position' 时应显示对应选择器而非数字输入框
  - 测试断言应匹配设计文档中的 Expected Behavior Properties
  - 在未修复的代码上运行测试
  - **预期结果**: 测试失败（这是正确的 - 证明 bug 存在）
  - 记录发现的反例以理解根本原因
  - 当测试编写完成、运行并记录失败后标记任务完成
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_

- [x] 2. 编写 Preservation 属性测试（修复前）
  - **Property 2: Preservation** - 现有功能保持不变
  - **重要**: 遵循观察优先方法
  - 观察未修复代码在非 bug 条件输入下的行为
  - 编写属性测试捕获从 Preservation Requirements 观察到的行为模式
  - 推荐使用属性测试以获得更强的保持保证
  - 在未修复的代码上运行测试
  - **预期结果**: 测试通过（确认要保持的基线行为）
  - 当测试编写完成、运行并在未修复代码上通过后标记任务完成
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. 实现动态选择器功能修复

  - [x] 3.1 添加后端 API 接口
    - 在 `backend/app/api/v1/users.py` 添加 `GET /api/v1/users/list` 接口（支持分页和搜索）
    - 在 `backend/app/api/v1/admin.py` 添加 `GET /api/v1/roles/list` 接口
    - 在 `backend/app/api/v1/admin.py` 添加 `GET /api/v1/departments/list` 接口
    - 在 `backend/app/api/v1/admin.py` 添加 `GET /api/v1/positions/list` 接口
    - 在 `backend/app/api/v1/admin.py` 添加 `GET /api/v1/groups/list` 接口
    - 所有接口返回格式统一：`{ items: [...], total: number }`
    - _Bug_Condition: isBugCondition(input) where input.component in ['FlowNodeInspector', 'FormPermissionDrawer'] and input.selectedType in ['user', 'role', 'group', 'department', 'position', 'expr']_
    - _Expected_Behavior: 提供数据源支持前端选择器组件_
    - _Preservation: 不影响现有 API 接口的功能_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7, 2.8, 2.9, 2.10_

  - [x] 3.2 添加前端 API 封装
    - 在 `my-app/src/api/` 目录创建或更新 API 调用函数
    - 创建 `my-app/src/api/user.ts` 封装用户列表接口
    - 创建 `my-app/src/api/admin.ts` 封装角色、部门、岗位、群组列表接口
    - 定义 TypeScript 类型接口
    - _Bug_Condition: 前端缺少调用后端列表接口的封装_
    - _Expected_Behavior: 提供类型安全的 API 调用函数_
    - _Preservation: 不影响现有 API 调用逻辑_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7, 2.8, 2.9, 2.10_

  - [x] 3.3 改造 FlowNodeInspector.vue 组件
    - 添加 `assignee_value` 字段的 v-model 绑定
    - 根据 `assignee_type` 条件渲染不同选择器：
      - `user`: n-select 组件，支持远程搜索
      - `role`: n-select 组件，显示角色列表
      - `group`: n-select 组件，显示群组列表
      - `department`: n-select 组件，显示部门列表
      - `position`: n-select 组件，显示岗位列表
      - `expr`: n-input 组件，输入表达式
    - 添加数据加载逻辑和状态管理
    - 将选中的 ID 或表达式存储到 `assignee_value` 字段
    - _Bug_Condition: 选择类型后未显示对应选择器_
    - _Expected_Behavior: 根据类型动态显示对应选择器并支持选择_
    - _Preservation: 保持 assignee_type 选择、其他节点属性配置、表单验证逻辑不变_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.3, 3.5, 3.6_

  - [x] 3.4 改造 FormPermissionDrawer.vue 组件
    - 替换固定的 n-input-number 为动态选择器
    - 根据 `grant_type` 条件渲染不同选择器：
      - `user`: n-select 组件，支持远程搜索
      - `role`: n-select 组件，显示角色列表
      - `department`: n-select 组件，显示部门列表
      - `position`: n-select 组件，显示岗位列表
    - 添加数据加载逻辑和状态管理
    - 将选中的 ID 存储到 `grantee_id` 字段
    - _Bug_Condition: 选择类型后仅显示数字输入框_
    - _Expected_Behavior: 根据类型动态显示对应选择器并支持选择_
    - _Preservation: 保持 grant_type 选择、其他权限属性配置、表单验证逻辑不变_
    - _Requirements: 2.7, 2.8, 2.9, 2.10, 3.2, 3.4, 3.5_

  - [x] 3.5 验证 Bug Condition 探索测试现在通过
    - **Property 1: Expected Behavior** - 动态选择器正确显示
    - **重要**: 重新运行任务 1 中的相同测试 - 不要编写新测试
    - 任务 1 中的测试编码了期望行为
    - 当此测试通过时，确认期望行为已满足
    - 运行任务 1 中的 Bug Condition 探索测试
    - **预期结果**: 测试通过（确认 bug 已修复）
    - _Requirements: Expected Behavior Properties from design_

  - [x] 3.6 验证 Preservation 测试仍然通过
    - **Property 2: Preservation** - 现有功能保持不变
    - **重要**: 重新运行任务 2 中的相同测试 - 不要编写新测试
    - 运行任务 2 中的 Preservation 属性测试
    - **预期结果**: 测试通过（确认无回归）
    - 确认修复后所有测试仍然通过（无回归）

- [x] 4. Checkpoint - 确保所有测试通过
  - 确保所有测试通过，如有疑问请询问用户
