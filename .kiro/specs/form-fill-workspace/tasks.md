# Implementation Plan: 表单填写工作区

## Overview

本实现计划将表单填写工作区功能分解为可执行的编码任务。实现将分为后端API开发、前端组件开发、权限集成和测试验证四个主要阶段。后端使用Python FastAPI构建RESTful接口，前端使用Vue3 + TypeScript构建响应式界面，通过现有的表单权限系统确保安全访问控制。

## Tasks

- [x] 1. 后端数据模型与Schema定义
  - [x] 1.1 创建用户快捷入口数据库模型
    - 在 `backend/app/models/` 创建 `user_quick_access.py`
    - 定义 `UserQuickAccess` 模型，包含 user_id, form_id, sort_order 字段
    - 添加唯一约束和索引以优化查询性能
    - _Requirements: 6.6, 6.7, 6.8_
  
  - [x] 1.2 创建数据库迁移脚本
    - 使用 `alembic revision --autogenerate` 生成迁移文件
    - 验证迁移脚本包含 user_quick_access 表创建语句
    - _Requirements: 6.6_
  
  - [x] 1.3 定义工作区相关Pydantic Schema
    - 在 `backend/app/schemas/` 创建 `workspace_schemas.py`
    - 实现 `FillableFormsQuery`, `FillableFormItem`, `FillableFormsResponse`, `QuickAccessResponse`
    - 添加字段验证规则（page >= 1, page_size <= 100, sort_order in ['asc', 'desc']）
    - _Requirements: 1.1, 1.3, 5.1, 5.6_

- [x] 2. 后端服务层实现
  - [x] 2.1 实现FormWorkspaceService核心业务逻辑
    - 在 `backend/app/services/` 创建 `form_workspace_service.py`
    - 实现 `get_fillable_forms()` 方法，集成权限检查、搜索、筛选、排序、分页
    - 实现表单状态计算逻辑（is_expired, is_closed, can_fill）
    - _Requirements: 1.1, 1.2, 2.1, 4.1, 5.2, 5.5_
  
  - [ ]* 2.2 编写FormWorkspaceService属性测试
    - **Property 1: 权限过滤完整性** - 返回的表单列表中所有表单都必须是用户有FILL权限的
    - **Validates: Requirements 4.1, 4.2**
  
  - [ ]* 2.3 编写FormWorkspaceService属性测试
    - **Property 2: 搜索结果准确性** - 当提供搜索关键词时，所有返回的表单标题或描述必须包含该关键词
    - **Validates: Requirements 2.1, 2.7**
  
  - [ ]* 2.4 编写FormWorkspaceService属性测试
    - **Property 3: 分页一致性** - 所有页面的表单总数之和等于total字段，且每页数量不超过page_size
    - **Validates: Requirements 1.3, 1.4**
  
  - [x] 2.5 实现快捷入口管理服务
    - 在 `form_workspace_service.py` 添加 `add_quick_access()`, `remove_quick_access()`, `get_quick_access_forms()` 方法
    - 实现排序逻辑和去重处理
    - _Requirements: 6.6, 6.7, 6.8, 6.9_
  
  - [ ]* 2.6 编写快捷入口服务单元测试
    - 测试添加、移除、查询快捷入口的边界情况
    - 测试重复添加的幂等性
    - _Requirements: 6.6, 6.7, 6.8_

- [x] 3. 后端API路由实现
  - [x] 3.1 实现可填写表单列表API端点
    - 在 `backend/app/api/v1/` 创建或更新 `forms.py`
    - 实现 `GET /api/v1/forms/fillable` 端点
    - 添加参数验证、权限检查、错误处理
    - 使用 `success_response` 包装返回数据
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 4.1, 5.2_
  
  - [x] 3.2 实现快捷入口管理API端点
    - 实现 `POST /api/v1/forms/{form_id}/quick-access` 端点
    - 实现 `DELETE /api/v1/forms/{form_id}/quick-access` 端点
    - 实现 `GET /api/v1/forms/quick-access` 端点
    - _Requirements: 6.6, 6.7, 6.8, 6.9_
  
  - [ ]* 3.3 编写API端点集成测试
    - 测试未认证用户访问返回401
    - 测试无权限表单不出现在列表中
    - 测试搜索、筛选、分页参数的正确处理
    - _Requirements: 4.1, 4.2, 1.3, 2.1_

- [x] 4. Checkpoint - 后端功能验证
  - 运行 `alembic upgrade head` 应用数据库迁移
  - 运行 `pytest` 确保所有测试通过
  - 使用 `/api/v1/docs` Swagger界面手动测试API端点
  - 确认权限检查正常工作，无权限表单被正确过滤
  - 如有问题请向用户反馈

- [x] 5. 前端类型定义与API客户端
  - [x] 5.1 定义TypeScript类型
    - 在 `my-app/src/types/` 创建 `workspace.ts`
    - 定义 `FillableFormItem`, `FillableFormsResponse`, `FillableFormsQuery`, `FilterState`, `PaginationState` 接口
    - _Requirements: 1.1, 5.1_
  
  - [x] 5.2 实现API客户端函数
    - 在 `my-app/src/api/` 创建 `workspace.ts`
    - 实现 `getFillableForms()`, `addQuickAccess()`, `removeQuickAccess()`, `getQuickAccessForms()` 函数
    - 使用统一的 HTTP 客户端和错误处理
    - _Requirements: 1.1, 6.6, 6.7, 6.8_

- [x] 6. 前端组合式函数实现
  - [x] 6.1 实现useFillWorkspace组合函数
    - 在 `my-app/src/composables/` 创建 `useFillWorkspace.ts`
    - 实现状态管理（forms, loading, error, pagination, filters）
    - 实现 `loadForms()` 方法，处理API调用和状态更新
    - 实现 `debouncedSearch()` 方法，使用300ms防抖
    - 实现 `handleFilter()`, `handlePageChange()`, `handleSort()` 方法
    - _Requirements: 1.1, 1.3, 1.4, 2.1, 5.1, 5.6_
  
  - [x] 6.2 实现useQuickAccess组合函数
    - 在 `my-app/src/composables/` 创建 `useQuickAccess.ts`
    - 实现快捷入口的增删查功能
    - 实现本地状态管理和持久化
    - _Requirements: 6.6, 6.7, 6.8, 6.9_

- [x] 7. 前端基础组件实现
  - [x] 7.1 实现SearchBar搜索栏组件
    - 在 `my-app/src/components/workspace/` 创建 `SearchBar.vue`
    - 实现搜索输入框、清除按钮、ESC键清除功能
    - 使用 v-model 双向绑定
    - 添加防抖处理（通过父组件传入的debounce prop）
    - _Requirements: 2.1, 2.2, 2.5, 2.6_
  
  - [x] 7.2 实现FilterPanel筛选面板组件
    - 在 `my-app/src/components/workspace/` 创建 `FilterPanel.vue`
    - 实现状态筛选、类别筛选、时间范围筛选
    - 实现清除所有筛选按钮
    - 使用 Naive UI 的 Select 和 DatePicker 组件
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.10_
  
  - [x] 7.3 实现FormCard表单卡片组件
    - 在 `my-app/src/components/workspace/` 创建 `FormCard.vue`
    - 显示表单标题、类别、创建时间、状态标识
    - 根据状态显示不同颜色（进行中-绿色、即将截止-黄色、已过期-灰色）
    - 实现点击卡片导航、悬停显示完整描述
    - 添加"填写"、"查看详情"、"添加到快捷入口"操作按钮
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.8, 3.9, 6.8_

- [x] 8. 前端主容器组件实现
  - [x] 8.1 实现FillWorkspace主页面组件
    - 在 `my-app/src/views/` 创建 `FillWorkspace.vue`
    - 集成 SearchBar, FilterPanel, FormCard 组件
    - 使用 useFillWorkspace 组合函数管理状态
    - 实现分页控件（使用 Naive UI 的 Pagination 组件）
    - 实现加载状态、空状态、错误状态的UI展示
    - _Requirements: 1.1, 1.9, 1.10, 1.11, 2.4_
  
  - [x] 8.2 实现QuickAccess快捷入口组件
    - 在 `my-app/src/components/workspace/` 创建 `QuickAccess.vue`
    - 显示快捷入口表单列表
    - 实现快速导航和移除功能
    - 支持横向滚动或分页显示
    - _Requirements: 6.6, 6.7, 6.9, 6.10_
  
  - [x] 8.3 集成快捷入口到主页面
    - 在 FillWorkspace.vue 顶部添加 QuickAccess 组件
    - 实现快捷入口与表单列表的联动
    - _Requirements: 6.6, 6.7_

- [x] 9. 路由与导航集成
  - [x] 9.1 添加工作区路由配置
    - 在 `my-app/src/router/index.ts` 添加 `/workspace/fill` 路由
    - 配置路由元信息（requiresAuth: true）
    - 实现路由守卫，确保用户已登录
    - _Requirements: 1.1, 4.1_
  
  - [x] 9.2 实现表单填写页面导航
    - 在 FormCard 组件中实现点击导航到 `/forms/:id/fill`
    - 添加导航前的权限检查（前端预检查）
    - 处理导航失败情况（表单已过期、已关闭、无权限）
    - _Requirements: 3.2, 3.3, 3.5, 3.6, 3.7_
  
  - [x] 9.3 实现键盘导航支持
    - 在 FillWorkspace 组件中监听键盘事件
    - 实现上下方向键选择表单卡片
    - 实现 Enter 键导航到选中的表单
    - _Requirements: 3.10, 3.11_

- [x] 10. 高级功能实现
  - [x] 10.1 实现自动刷新机制
    - 在 FillWorkspace 组件中使用 setInterval 每60秒刷新表单列表
    - 在组件卸载时清除定时器
    - 刷新时保持当前的筛选和搜索状态
    - _Requirements: 1.12_
  
  - [x] 10.2 实现批量操作功能
    - 在 FillWorkspace 组件中添加批量选择状态管理
    - 在 FormCard 组件中添加复选框
    - 实现全选/取消全选功能
    - 实现批量操作工具栏（批量填写、批量导出）
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ]* 10.3 编写批量操作单元测试
    - 测试全选逻辑的正确性
    - 测试部分选择时全选状态的更新
    - _Requirements: 6.4, 6.5_

- [x] 11. 权限控制与错误处理
  - [x] 11.1 实现前端权限检查
    - 在表单卡片中根据 can_fill 字段禁用填写按钮
    - 在导航前检查表单状态（is_expired, is_closed）
    - 显示相应的提示信息
    - _Requirements: 3.5, 3.6, 3.7, 4.2_
  
  - [x] 11.2 实现后端权限拦截
    - 在表单填写页面的后端路由中添加权限检查
    - 无权限时返回403错误和友好提示
    - _Requirements: 4.2, 4.3_
  
  - [x] 11.3 实现租户上下文切换处理
    - 监听租户切换事件，自动刷新表单列表
    - 清除当前的筛选和搜索状态
    - _Requirements: 4.5, 4.6_
  
  - [ ]* 11.4 编写权限控制属性测试
    - **Property 4: 权限撤销即时性** - 当用户权限被撤销后，下次刷新该表单不应出现在列表中
    - **Validates: Requirements 4.3, 4.10**

- [x] 12. UI优化与用户体验
  - [x] 12.1 实现加载状态优化
    - 使用骨架屏替代简单的加载动画
    - 实现乐观更新（快捷入口添加/移除）
    - _Requirements: 1.10_
  
  - [x] 12.2 实现搜索关键词高亮
    - 在 FormCard 组件中实现关键词匹配高亮显示
    - 使用不同颜色标识匹配的文本片段
    - _Requirements: 2.3_
  
  - [x] 12.3 实现空状态和错误状态UI
    - 设计并实现无表单时的空状态提示
    - 设计并实现搜索无结果时的空状态提示
    - 设计并实现加载失败时的错误提示和重试按钮
    - _Requirements: 1.9, 1.11, 2.4_

- [x] 13. 最终集成与验证
  - [x] 13.1 端到端功能测试
    - 测试完整的用户流程：登录 → 访问工作区 → 搜索表单 → 筛选 → 导航到填写页
    - 测试权限控制：无权限用户无法看到受限表单
    - 测试快捷入口：添加、移除、导航
    - _Requirements: 1.1, 2.1, 3.2, 4.1, 6.6_
  
  - [x] 13.2 性能优化验证
    - 验证分页加载性能（大量表单时）
    - 验证搜索防抖效果
    - 验证自动刷新不影响用户操作
    - _Requirements: 1.3, 2.1, 1.12_
  
  - [ ]* 13.3 编写端到端集成测试
    - 使用 Playwright 或 Cypress 编写自动化测试
    - 覆盖主要用户流程和边界情况
    - _Requirements: 1.1, 2.1, 3.2, 4.1_

- [x] 14. Final Checkpoint - 完整功能验证
  - 确保所有测试通过（pytest 和前端测试）
  - 在开发环境中完整测试所有功能
  - 验证权限系统正确集成
  - 验证前后端数据交互正常
  - 检查UI响应性和用户体验
  - 如有问题请向用户反馈

## Notes

- 任务标记 `*` 的为可选任务，可跳过以加快MVP开发
- 每个任务都引用了具体的需求编号以确保可追溯性
- Checkpoint任务确保增量验证，及时发现问题
- 属性测试验证通用正确性属性，单元测试验证具体示例和边界情况
- 后端优先开发，确保API稳定后再进行前端集成
- 前端组件采用自底向上的开发顺序：基础组件 → 组合函数 → 容器组件
