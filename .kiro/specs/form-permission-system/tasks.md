# 任务列表：表单权限系统

## Phase 1: 后端实现

### 1.1 数据库模型
- [x] 1.1.1 创建 user_department 中间表模型
- [x] 1.1.2 为 FormPermission 添加 include_children 字段
- [x] 1.1.3 创建数据库迁移脚本

### 1.2 Pydantic Schema
- [x] 1.2.1 创建 GrantPermissionDTO
- [x] 1.2.2 创建 BatchGrantPermissionDTO
- [x] 1.2.3 创建 PermissionResponse
- [x] 1.2.4 创建 PermissionCheckDTO/Response

### 1.3 服务层
- [x] 1.3.1 实现 PermissionService.check_permission()
- [x] 1.3.2 实现 PermissionService.get_user_forms()
- [x] 1.3.3 实现 PermissionService.grant_permission()
- [x] 1.3.4 实现 PermissionService.batch_grant_permissions()
- [x] 1.3.5 实现 PermissionService.revoke_permission()
- [x] 1.3.6 实现 DepartmentHierarchyService.get_child_department_ids()
- [x] 1.3.7 实现 DepartmentHierarchyService.get_user_all_department_ids()

### 1.4 API 路由
- [x] 1.4.1 POST /forms/{form_id}/permissions - 授予权限
- [x] 1.4.2 GET /forms/{form_id}/permissions - 获取权限列表
- [x] 1.4.3 DELETE /forms/{form_id}/permissions/{perm_id} - 撤销权限
- [x] 1.4.4 POST /forms/{form_id}/permissions/batch - 批量授权
- [x] 1.4.5 GET /forms/{form_id}/permissions/check - 检查权限
- [x] 1.4.6 GET /forms/{form_id}/permissions/options/users - 用户列表
- [x] 1.4.7 GET /forms/{form_id}/permissions/options/roles - 角色列表
- [x] 1.4.8 GET /forms/{form_id}/permissions/options/departments - 部门列表
- [x] 1.4.9 GET /forms/{form_id}/permissions/options/posts - 岗位列表

### 1.5 权限校验中间件/装饰器
- [ ] 1.5.1 创建表单操作权限校验装饰器
- [ ] 1.5.2 在表单相关路由中集成权限校验

## Phase 2: 前端实现

### 2.1 TypeScript 类型定义
- [ ] 2.1.1 定义 Permission 相关类型
- [ ] 2.1.2 定义 GrantPermissionDTO 类型
- [ ] 2.1.3 定义 API 响应类型

### 2.2 API 接口
- [ ] 2.2.1 实现权限管理 API 函数
- [ ] 2.2.2 实现下拉选择器数据 API 函数
- [ ] 2.2.3 实现权限检查 API 函数

### 2.3 权限管理组件
- [ ] 2.3.1 创建 PermissionManageModal 组件
- [ ] 2.3.2 实现权限类型选择器
- [ ] 2.3.3 实现权限级别选择器
- [ ] 2.3.4 实现批量授权功能
- [ ] 2.3.5 实现权限列表展示

### 2.4 下拉选择器组件
- [ ] 2.4.1 创建 UserSelect 组件
- [ ] 2.4.2 创建 RoleSelect 组件
- [ ] 2.4.3 创建 DepartmentSelect 组件
- [ ] 2.4.4 创建 PostSelect 组件

## Phase 3: 测试

### 3.1 单元测试
- [ ] 3.1.1 测试权限校验逻辑
- [ ] 3.1.2 测试权限级别比较
- [ ] 3.1.3 测试部门层级继承
- [ ] 3.1.4 测试批量授权事务

### 3.2 集成测试
- [ ] 3.2.1 测试完整权限校验流程
- [ ] 3.2.2 测试多租户隔离
- [ ] 3.2.3 测试 API 端点

### 3.3 前端测试
- [ ] 3.3.1 测试权限管理组件
- [ ] 3.3.2 测试下拉选择器组件

## Phase 4: 文档与发布

### 4.1 文档
- [ ] 4.1.1 更新 API 文档
- [ ] 4.1.2 更新用户手册

### 4.2 发布准备
- [ ] 4.2.1 代码审查
- [ ] 4.2.2 运行完整测试套件
- [ ] 4.2.3 部署到测试环境验证