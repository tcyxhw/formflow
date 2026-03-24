# 审批流程系统剩余功能需求文档

## 一、项目概述

### 1.1 项目背景

FormFlow 审批流程系统已完成 93% 的功能实现。本文档定义了剩余 5 个核心功能的完整需求，这些功能是审批流程系统的关键组成部分，直接影响系统的完整性和可用性。

### 1.2 项目目标

- 完成审批流程系统的最后 5 个核心功能
- 实现完整的审批操作追踪和时间线展示
- 支持 CC（抄送）节点的完整业务流程
- 提供表单字段 API 支持前端条件构造器
- 达到 100% 功能完成度

### 1.3 项目范围

本需求文档涵盖以下 5 个功能：

1. **WorkflowOperationLog 表** (P0) - 审批操作日志记录
2. **ProcessInstance.form_data_snapshot 字段** (P0) - 表单数据快照
3. **Task 表扩展字段** (P0) - 任务类型和审批意见
4. **表单字段 API** (P0) - 获取表单字段定义
5. **CC 节点业务逻辑** (P1) - 抄送功能实现

---

## 二、术语表

### 系统术语

- **System**: FormFlow 审批流程系统
- **ProcessInstance**: 流程实例，代表一个具体的审批流程执行
- **Task**: 任务，代表分配给用户的审批或抄送任务
- **WorkflowOperationLog**: 工作流操作日志，记录流程中的所有操作
- **FormDataSnapshot**: 表单数据快照，保存流程启动时的表单数据
- **OperationType**: 操作类型，包括 submit、approve、reject、cancel、cc 等
- **TaskType**: 任务类型，包括 approve（审批）和 cc（抄送）
- **CCAssignee**: 抄送人，可以是用户、角色、部门或职位
- **ConditionBuilder**: 条件构造器，前端用于构建条件表达式的组件
- **FormField**: 表单字段，表单中的单个字段定义

### 业务术语

- **审批操作**: 用户对任务的操作，包括通过、驳回、撤回等
- **操作时间线**: 流程中所有操作的时间序列记录
- **抄送**: 将流程信息发送给相关人员，不需要其进行审批
- **表单快照**: 流程启动时的表单数据状态，用于审批时查看原始数据
- **系统字段**: 由系统自动生成的字段，如提交人、提交时间等

---

## 三、功能需求

### 需求 1：WorkflowOperationLog 表

**用户故事**: 作为审批管理员，我想记录审批流程中的所有操作，以便追踪流程历史和进行审计。

#### 验收标准

1. WHEN 用户执行审批操作（通过、驳回、撤回等），THE System SHALL 在 WorkflowOperationLog 表中创建一条操作记录

2. WHEN 查询操作日志，THE System SHALL 返回包含以下字段的记录：
   - id: 操作日志唯一标识
   - tenant_id: 租户 ID
   - process_instance_id: 流程实例 ID
   - operation_type: 操作类型（submit、approve、reject、cancel、cc）
   - operator_id: 操作人 ID
   - comment: 操作备注（可选）
   - detail_json: 操作详情 JSON（包含操作前后的状态变化）
   - created_at: 操作时间戳

3. WHEN 操作日志记录被创建，THE System SHALL 自动设置 created_at 为当前时间戳

4. WHEN 查询特定流程实例的操作日志，THE System SHALL 按 created_at 升序返回所有相关操作记录

5. IF 操作详情过于复杂，THEN THE System SHALL 将其序列化为 JSON 格式存储在 detail_json 字段中

6. WHEN 删除流程实例，THE System SHALL 保留对应的操作日志记录（软删除流程实例）

#### 数据模型

```python
class WorkflowOperationLog(Base):
    __tablename__ = "workflow_operation_log"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    process_instance_id: Mapped[int] = mapped_column(ForeignKey("process_instance.id"), nullable=False, index=True)
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # submit, approve, reject, cancel, cc
    operator_id: Mapped[str] = mapped_column(String(50), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String(500))
    detail_json: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关系
    process_instance: Mapped["ProcessInstance"] = relationship("ProcessInstance")
```

---

### 需求 2：ProcessInstance.form_data_snapshot 字段

**用户故事**: 作为审批人，我想在审批时查看流程启动时的原始表单数据，以便了解申请的初始状态。

#### 验收标准

1. WHEN 流程实例被创建，THE System SHALL 在 form_data_snapshot 字段中保存当前的表单数据

2. WHEN 查询流程实例的审批时间线，THE System SHALL 返回 form_data_snapshot 中的表单数据

3. WHEN 表单数据被修改（如驳回后重新提交），THE System SHALL 保持原始的 form_data_snapshot 不变

4. WHEN 审批人查看审批详情，THE System SHALL 显示 form_data_snapshot 中的表单数据供参考

5. IF 表单数据为空或无效，THEN THE System SHALL 存储空对象 {} 而不是 NULL

6. WHEN 导出流程数据，THE System SHALL 包含 form_data_snapshot 字段

#### 数据模型

```python
class ProcessInstance(Base):
    # ... 现有字段 ...
    
    form_data_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # 在 __init__ 或创建时设置为当前表单数据
```

---

### 需求 3：Task 表扩展字段

**用户故事**: 作为系统，我想区分审批任务和抄送任务，并记录审批意见，以便支持完整的审批流程。

#### 验收标准

1. WHEN 创建任务，THE System SHALL 在 task_type 字段中设置任务类型（approve 或 cc）

2. WHEN 任务类型为 approve，THE System SHALL 要求任务接收人进行审批操作（通过或驳回）

3. WHEN 任务类型为 cc，THE System SHALL 仅将任务作为信息通知，不要求审批操作

4. WHEN 用户完成审批任务，THE System SHALL 在 comment 字段中保存审批意见

5. WHEN 查询任务列表，THE System SHALL 根据 task_type 区分审批任务和抄送任务

6. WHEN 任务类型为 cc，THE System SHALL 自动标记任务为已读状态

7. IF 审批意见超过 500 字符，THEN THE System SHALL 截断或返回错误提示

#### 数据模型

```python
class Task(Base):
    # ... 现有字段 ...
    
    task_type: Mapped[str] = mapped_column(String(50), default="approve", nullable=False)  # approve, cc
    comment: Mapped[Optional[str]] = mapped_column(String(500))
```

---

### 需求 4：表单字段 API

**用户故事**: 作为前端开发者，我想获取表单的字段定义，以便在条件构造器中显示可用的字段。

#### 验收标准

1. WHEN 调用 GET /api/v1/forms/{form_id}/fields，THE System SHALL 返回表单的所有字段定义

2. WHEN 返回字段定义，THE System SHALL 包含以下信息：
   - key: 字段唯一标识
   - name: 字段显示名称
   - type: 字段类型（text、number、select、date、checkbox 等）
   - options: 字段选项（仅对 select、checkbox 等有效）
   - required: 是否必填
   - description: 字段描述

3. WHEN 返回字段列表，THE System SHALL 包含系统字段：
   - sys_submitter: 提交人
   - sys_submitter_dept: 提交人部门
   - sys_submit_time: 提交时间

4. WHEN 表单不存在，THE System SHALL 返回 404 错误

5. WHEN 用户无权访问表单，THE System SHALL 返回 403 错误

6. WHEN 字段类型为 select 或 checkbox，THE System SHALL 返回 options 数组，每个选项包含 label 和 value

7. WHEN 调用此 API，THE System SHALL 返回 HTTP 200 状态码和 JSON 格式的字段列表

#### API 规范

**请求**:
```
GET /api/v1/forms/{form_id}/fields
Authorization: Bearer {token}
X-Tenant-ID: {tenant_id}
```

**响应 (200 OK)**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "fields": [
      {
        "key": "applicant_name",
        "name": "申请人",
        "type": "text",
        "required": true,
        "description": "申请人姓名"
      },
      {
        "key": "department",
        "name": "部门",
        "type": "select",
        "required": true,
        "options": [
          {"label": "技术部", "value": "tech"},
          {"label": "市场部", "value": "market"}
        ]
      },
      {
        "key": "amount",
        "name": "金额",
        "type": "number",
        "required": true
      },
      {
        "key": "sys_submitter",
        "name": "提交人",
        "type": "text",
        "system": true
      },
      {
        "key": "sys_submitter_dept",
        "name": "提交人部门",
        "type": "text",
        "system": true
      },
      {
        "key": "sys_submit_time",
        "name": "提交时间",
        "type": "date",
        "system": true
      }
    ]
  }
}
```

**响应 (404 Not Found)**:
```json
{
  "code": 404,
  "message": "Form not found"
}
```

#### 实现要点

1. 从 Form 模型中解析字段定义
2. 支持嵌套字段（如果表单支持）
3. 包含系统字段的定义
4. 缓存字段定义以提高性能
5. 验证用户权限

---

### 需求 5：CC 节点业务逻辑

**用户故事**: 作为流程设计者，我想在流程中添加 CC 节点，以便将流程信息发送给相关人员。

#### 验收标准

1. WHEN 流程推进到 CC 节点，THE System SHALL 根据 CC 节点配置创建抄送任务

2. WHEN 创建抄送任务，THE System SHALL 支持以下抄送人类型：
   - user: 指定用户
   - role: 指定角色的所有用户
   - department: 指定部门的所有用户
   - position: 指定职位的所有用户

3. WHEN CC 节点配置包含多个抄送人类型，THE System SHALL 为每个抄送人创建一个独立的任务

4. WHEN 创建抄送任务，THE System SHALL 设置 task_type 为 cc

5. WHEN 所有抄送任务创建完成，THE System SHALL 继续推进流程到下一个节点

6. WHEN 抄送任务被创建，THE System SHALL 不阻塞流程推进（异步创建）

7. IF CC 节点配置无效或抄送人列表为空，THEN THE System SHALL 记录警告日志并继续推进流程

8. WHEN 查询流程时间线，THE System SHALL 显示所有 CC 操作和相关的抄送人

#### CC 节点配置格式

```json
{
  "nodeId": "cc_node_1",
  "nodeType": "CC",
  "name": "抄送给相关人员",
  "assignees": [
    {
      "type": "user",
      "value": "user_id_1"
    },
    {
      "type": "role",
      "value": "role_id_1"
    },
    {
      "type": "department",
      "value": "dept_id_1"
    }
  ]
}
```

#### 实现要点

1. 在 ProcessService._dispatch_nodes() 中添加 CC 节点处理
2. 实现 _create_cc_task() 方法创建抄送任务
3. 实现 AssignmentService.select_cc_assignees() 方法解析抄送人
4. 在 FlowService 中添加 CC 节点校验
5. 记录 CC 操作到 WorkflowOperationLog
6. 支持 CC 任务的查询和展示

#### 数据流

```
流程推进到 CC 节点
  ↓
解析 CC 节点配置
  ↓
获取抄送人列表
  ↓
为每个抄送人创建任务（task_type=cc）
  ↓
记录操作日志
  ↓
继续推进流程到下一个节点
```

---

## 四、非功能需求

### 4.1 性能需求

- **操作日志记录**: 记录操作日志的时间 < 100ms
- **表单字段 API**: 响应时间 < 200ms（支持缓存）
- **CC 任务创建**: 创建单个 CC 任务的时间 < 50ms
- **数据库查询**: 查询操作日志的时间 < 300ms

### 4.2 可靠性需求

- **数据一致性**: 操作日志和流程状态保持一致
- **错误恢复**: 操作日志记录失败不应阻塞流程推进
- **数据完整性**: 所有操作都应被记录

### 4.3 安全需求

- **权限控制**: 只有有权访问表单的用户才能获取字段定义
- **数据隐私**: 操作日志中的敏感信息应被加密或脱敏
- **审计日志**: 所有操作都应被记录用于审计

### 4.4 可维护性需求

- **代码规范**: 遵循项目的 Python 和 Vue3 代码规范
- **文档完整**: 提供 API 文档和使用示例
- **易于扩展**: 支持新的操作类型和抄送人类型

---

## 五、数据流和交互流程

### 5.1 审批操作流程

```
用户执行审批操作（通过/驳回）
  ↓
验证权限和任务状态
  ↓
更新 Task 状态和 comment
  ↓
创建 WorkflowOperationLog 记录
  ↓
推进流程到下一个节点
  ↓
返回成功响应
```

### 5.2 CC 节点处理流程

```
流程推进到 CC 节点
  ↓
解析 CC 节点配置
  ↓
获取抄送人列表
  ↓
为每个抄送人创建 Task（task_type=cc）
  ↓
创建 WorkflowOperationLog 记录
  ↓
继续推进流程
```

### 5.3 审批时间线查询流程

```
用户查询流程时间线
  ↓
获取 ProcessInstance 和 form_data_snapshot
  ↓
查询所有 WorkflowOperationLog 记录
  ↓
按时间排序
  ↓
返回时间线数据
```

### 5.4 表单字段 API 调用流程

```
前端条件构造器加载
  ↓
调用 GET /api/v1/forms/{form_id}/fields
  ↓
后端解析表单字段定义
  ↓
添加系统字段
  ↓
返回字段列表
  ↓
前端显示可用字段
```

---

## 六、测试策略

### 6.1 单元测试

#### WorkflowOperationLog

- ✅ 测试操作日志记录的创建
- ✅ 测试操作日志的查询
- ✅ 测试 detail_json 的序列化
- ✅ 测试时间戳的自动设置

#### ProcessInstance.form_data_snapshot

- ✅ 测试快照的保存
- ✅ 测试快照的查询
- ✅ 测试快照的不可变性

#### Task 扩展字段

- ✅ 测试 task_type 的设置
- ✅ 测试 comment 的保存
- ✅ 测试任务类型的区分

#### 表单字段 API

- ✅ 测试字段定义的解析
- ✅ 测试系统字段的包含
- ✅ 测试权限验证
- ✅ 测试错误处理

#### CC 节点

- ✅ 测试 CC 节点的识别
- ✅ 测试抄送人的解析
- ✅ 测试 CC 任务的创建
- ✅ 测试流程的继续推进

### 6.2 集成测试

- ✅ 测试完整的审批流程（包括操作日志记录）
- ✅ 测试 CC 节点的完整流程
- ✅ 测试审批时间线的查询
- ✅ 测试表单字段 API 与条件构造器的集成

### 6.3 端到端测试

- ✅ 测试用户执行审批操作并查看时间线
- ✅ 测试 CC 节点的完整业务流程
- ✅ 测试条件构造器使用表单字段 API

---

## 七、验收标准总结

### P0 优先级（必须实现）

| 功能 | 验收标准 | 优先级 |
|-----|---------|--------|
| WorkflowOperationLog 表 | 所有操作都被记录 | P0 |
| form_data_snapshot 字段 | 表单数据被正确保存 | P0 |
| Task 扩展字段 | 任务类型和意见被正确记录 | P0 |
| 表单字段 API | API 返回正确的字段定义 | P0 |

### P1 优先级（应该实现）

| 功能 | 验收标准 | 优先级 |
|-----|---------|--------|
| CC 节点业务逻辑 | CC 任务被正确创建和处理 | P1 |

---

## 八、实现路线图

### 第一阶段（P0 - 预计 8-12 小时）

**Day 1-2**: 数据库迁移和模型扩展
- 创建 WorkflowOperationLog 表迁移脚本
- 添加 ProcessInstance.form_data_snapshot 字段
- 扩展 Task 表（task_type 和 comment）

**Day 3-4**: 表单字段 API 实现
- 实现 GET /api/v1/forms/{form_id}/fields 端点
- 实现字段解析逻辑
- 添加系统字段支持

**Day 5**: 操作日志记录集成
- 在审批操作中记录日志
- 在流程推进中记录日志
- 编写单元测试

### 第二阶段（P1 - 预计 6-8 小时）

**Day 1-2**: CC 节点业务逻辑
- 实现 _create_cc_task() 方法
- 在 _dispatch_nodes() 中添加 CC 处理
- 实现 select_cc_assignees() 方法

**Day 3**: CC 节点集成测试
- 编写集成测试
- 验证完整流程

---

## 九、相关文档

- `.kiro/APPROVAL_FLOW_COMPLETION_DESIGN_INDEX.md` - 设计导航
- `.kiro/APPROVAL_FLOW_COMPLETION_DESIGN_PART1.md` - 基础设计
- `.kiro/APPROVAL_FLOW_COMPLETION_DESIGN_PART2.md` - 核心功能
- `.kiro/APPROVAL_FLOW_FINAL_COMPLETION_REPORT.md` - 完成度报告

---

**文档版本**: 1.0  
**创建日期**: 2024-12-20  
**最后更新**: 2024-12-20  
**状态**: 待审核
