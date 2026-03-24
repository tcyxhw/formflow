# 审批流程系统剩余功能 - 实现检查清单

## 功能 1: WorkflowOperationLog 表

### 数据库设计
- [ ] 表名: `workflow_operation_log`
- [ ] 字段:
  - [ ] `id` (PK)
  - [ ] `tenant_id` (FK)
  - [ ] `process_instance_id` (FK)
  - [ ] `operation_type` (VARCHAR 20)
  - [ ] `operator_id` (FK)
  - [ ] `comment` (VARCHAR 500)
  - [ ] `detail_json` (JSONB)
  - [ ] `created_at` (DateTime)
  - [ ] `updated_at` (DateTime)
- [ ] 索引:
  - [ ] `idx_instance_created` (process_instance_id, created_at)
  - [ ] `idx_operation_type` (operation_type, created_at)
  - [ ] `idx_tenant_created` (tenant_id, created_at)

### 模型实现
- [ ] 在 `backend/app/models/workflow.py` 中定义 `WorkflowOperationLog` 类
- [ ] 添加所有字段和关系
- [ ] 添加表注释和字段注释

### 迁移脚本
- [ ] 创建迁移脚本 `backend/alembic/versions/XXX_add_remaining_features.py`
- [ ] 实现 `upgrade()` 函数
- [ ] 实现 `downgrade()` 函数
- [ ] 测试迁移脚本

### 服务层
- [ ] 创建 `backend/app/services/workflow_operation_log_service.py`
- [ ] 实现 `create_log()` 方法
- [ ] 实现 `get_process_logs()` 方法
- [ ] 实现 `get_operation_timeline()` 方法
- [ ] 添加错误处理和日志记录

### 测试
- [ ] 单元测试: 日志创建
- [ ] 单元测试: 日志查询
- [ ] 单元测试: 时间线生成
- [ ] 集成测试: 完整流程

---

## 功能 2: ProcessInstance.form_data_snapshot 字段

### 数据库设计
- [ ] 表名: `process_instance`
- [ ] 新增字段:
  - [ ] `form_data_snapshot` (JSONB, nullable)

### 模型实现
- [ ] 在 `ProcessInstance` 类中添加字段
- [ ] 添加字段注释

### 迁移脚本
- [ ] 在迁移脚本中添加字段
- [ ] 测试迁移脚本

### 业务逻辑
- [ ] 在 `ProcessService.start_process()` 中保存快照
- [ ] 获取表单数据
- [ ] 保存到 `form_data_snapshot` 字段

### API 集成
- [ ] 在审批时间线 API 中返回快照
- [ ] 在流程详情 API 中返回快照

### 测试
- [ ] 单元测试: 快照保存
- [ ] 单元测试: 快照查询
- [ ] 单元测试: 快照不可变性
- [ ] 集成测试: 完整流程

---

## 功能 3: Task 表扩展字段

### 数据库设计
- [ ] 表名: `task`
- [ ] 新增字段:
  - [ ] `task_type` (VARCHAR 20, default='approve')
  - [ ] `comment` (VARCHAR 500, nullable)

### 模型实现
- [ ] 在 `Task` 类中添加字段
- [ ] 添加字段注释

### 迁移脚本
- [ ] 在迁移脚本中添加字段
- [ ] 测试迁移脚本

### 业务逻辑
- [ ] 在 `_create_task_for_node()` 中设置 `task_type`
- [ ] 在审批完成时设置 `comment`
- [ ] 在任务查询中使用字段

### API 集成
- [ ] 在任务列表 API 中返回 `task_type`
- [ ] 在任务列表 API 中返回 `comment`
- [ ] 在任务详情 API 中返回 `comment`

### 测试
- [ ] 单元测试: task_type 设置
- [ ] 单元测试: comment 保存
- [ ] 单元测试: 任务类型区分
- [ ] 集成测试: 完整流程

---

## 功能 4: 表单字段 API

### 服务层
- [ ] 创建 `backend/app/services/form_field_service.py`
- [ ] 实现 `get_form_fields()` 方法
- [ ] 实现 `_parse_form_fields()` 方法
- [ ] 实现 `_get_system_fields()` 方法
- [ ] 添加缓存支持

### 数据模型
- [ ] 创建 `FormField` Pydantic 模型
- [ ] 创建 `FormFieldOption` Pydantic 模型
- [ ] 创建 `FormFieldsResponse` Pydantic 模型

### API 端点
- [ ] 在 `backend/app/api/v1/forms.py` 中添加路由
- [ ] 实现 `GET /api/v1/forms/{form_id}/fields` 端点
- [ ] 添加权限验证
- [ ] 添加错误处理
- [ ] 添加文档字符串

### 字段类型支持
- [ ] text
- [ ] number
- [ ] select
- [ ] checkbox
- [ ] date
- [ ] datetime
- [ ] textarea
- [ ] radio

### 系统字段
- [ ] sys_submitter
- [ ] sys_submitter_dept
- [ ] sys_submit_time

### 缓存
- [ ] 实现 Redis 缓存
- [ ] 设置缓存过期时间 (1 小时)
- [ ] 实现缓存失效机制

### 测试
- [ ] 单元测试: 字段解析
- [ ] 单元测试: 系统字段包含
- [ ] 单元测试: 缓存功能
- [ ] 集成测试: API 端点
- [ ] 集成测试: 权限验证

---

## 功能 5: CC 节点业务逻辑

### AssignmentService 扩展
- [ ] 实现 `select_cc_assignees()` 方法
- [ ] 实现 `_get_users_by_role()` 方法
- [ ] 实现 `_get_users_by_department()` 方法
- [ ] 实现 `_get_users_by_position()` 方法
- [ ] 添加错误处理和日志记录

### ProcessService 扩展
- [ ] 实现 `_create_cc_tasks()` 方法
- [ ] 在 `_dispatch_nodes()` 中添加 CC 节点处理
- [ ] 记录操作日志
- [ ] 继续推进流程

### CC 节点配置格式
- [ ] 支持 user 类型
- [ ] 支持 role 类型
- [ ] 支持 department 类型
- [ ] 支持 position 类型
- [ ] 支持多个抄送人

### 业务逻辑
- [ ] 解析 CC 节点配置
- [ ] 获取抄送人列表
- [ ] 为每个抄送人创建任务
- [ ] 标记任务类型为 cc
- [ ] 记录操作日志
- [ ] 继续推进流程

### 错误处理
- [ ] CC 节点配置无效
- [ ] 抄送人列表为空
- [ ] 抄送人不存在
- [ ] 数据库错误

### 测试
- [ ] 单元测试: 抄送人解析
- [ ] 单元测试: CC 任务创建
- [ ] 单元测试: 流程继续推进
- [ ] 集成测试: 完整流程
- [ ] 集成测试: 边界情况

---

## 代码质量检查

### 命名规范
- [ ] 函数名使用 `snake_case`
- [ ] 类名使用 `PascalCase`
- [ ] 常量使用 `UPPER_SNAKE_CASE`
- [ ] 变量名使用 `snake_case`

### 类型注解
- [ ] 所有函数参数都有类型注解
- [ ] 所有函数返回值都有类型注解
- [ ] 所有类属性都有类型注解

### 文档注释
- [ ] 所有类都有 docstring
- [ ] 所有公共方法都有 docstring
- [ ] 所有复杂逻辑都有注释

### 错误处理
- [ ] 所有异常都被捕获
- [ ] 所有错误都有日志记录
- [ ] 所有错误都有用户友好的提示

### 日志记录
- [ ] 关键操作都有日志记录
- [ ] 错误都有日志记录
- [ ] 日志级别正确

### 测试覆盖
- [ ] 所有公共方法都有测试
- [ ] 所有错误路径都有测试
- [ ] 所有边界情况都有测试

---

## 性能检查

### 数据库查询
- [ ] 所有查询都使用了索引
- [ ] 没有 N+1 查询问题
- [ ] 查询性能 < 300ms

### API 响应
- [ ] 表单字段 API < 200ms
- [ ] 操作日志 API < 300ms
- [ ] CC 任务创建 < 50ms/个

### 缓存
- [ ] 表单字段已缓存
- [ ] 缓存过期时间合理
- [ ] 缓存失效机制正确

---

## 集成测试

### 完整流程测试
- [ ] 创建表单和流程定义
- [ ] 创建提交和流程实例
- [ ] 执行审批操作
- [ ] 验证操作日志
- [ ] 验证快照保存
- [ ] 验证任务字段

### CC 节点测试
- [ ] 创建包含 CC 节点的流程
- [ ] 执行完整的审批流程
- [ ] 验证 CC 任务被创建
- [ ] 验证流程继续推进
- [ ] 验证操作日志记录

### 边界情况测试
- [ ] CC 节点配置无效
- [ ] 抄送人列表为空
- [ ] 抄送人不存在
- [ ] 表单不存在
- [ ] 无权访问表单

---

## 文档完善

### API 文档
- [ ] 表单字段 API 文档
- [ ] 操作日志 API 文档
- [ ] CC 节点配置文档

### 实现指南
- [ ] CC 节点配置指南
- [ ] 操作日志查询指南
- [ ] 表单字段 API 使用指南

### 代码注释
- [ ] 所有复杂逻辑都有注释
- [ ] 所有公共 API 都有文档

---

## 部署检查

### 数据库
- [ ] 迁移脚本已验证
- [ ] 备份已创建
- [ ] 迁移已执行

### 代码
- [ ] 代码已审查
- [ ] 测试已通过
- [ ] 性能已验证

### 文档
- [ ] API 文档已更新
- [ ] 实现指南已完成
- [ ] 变更日志已更新

---

## 验收标准

### 功能验收
- [ ] WorkflowOperationLog 表创建成功
- [ ] form_data_snapshot 字段添加成功
- [ ] Task 表扩展字段添加成功
- [ ] 表单字段 API 正常工作
- [ ] CC 节点业务逻辑正常工作

### 性能验收
- [ ] 操作日志记录 < 100ms
- [ ] 表单字段 API < 200ms
- [ ] CC 任务创建 < 50ms/个
- [ ] 操作日志查询 < 300ms

### 代码质量
- [ ] 代码风格符合项目规范
- [ ] 完整的错误处理
- [ ] 完整的日志记录
- [ ] 完整的类型注解
- [ ] 完整的文档注释

### 测试覆盖
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 代码覆盖率 > 80%

---

**创建日期**: 2024-12-20  
**最后更新**: 2024-12-20  
**状态**: 待开始
