# 审批流程系统剩余功能 - 技术设计文档

## 一、概述

本设计文档为 FormFlow 审批流程系统的剩余 5 个核心功能提供完整的技术设计方案。这些功能是系统完整性的关键，直接支撑审批流程的追踪、数据保存、任务管理和抄送功能。

### 1.1 功能清单

| 序号 | 功能名称 | 优先级 | 状态 |
|-----|---------|--------|------|
| 1 | WorkflowOperationLog 表 | P0 | 设计中 |
| 2 | ProcessInstance.form_data_snapshot 字段 | P0 | 设计中 |
| 3 | Task 表扩展字段 | P0 | 设计中 |
| 4 | 表单字段 API | P0 | 设计中 |
| 5 | CC 节点业务逻辑 | P1 | 设计中 |

### 1.2 设计原则

- ✅ 基于现有代码架构进行扩展
- ✅ 保持代码风格一致（snake_case、async/await、完整类型注解）
- ✅ 遵循项目约定和规范
- ✅ 完整的错误处理和日志记录
- ✅ 支持多租户隔离
- ✅ 考虑性能和可扩展性

---

## 二、数据模型设计

### 2.1 WorkflowOperationLog 表

**表名**: `workflow_operation_log`

**用途**: 记录审批流程中的所有操作，用于审计和时间线展示

**字段定义**:

```python
class WorkflowOperationLog(DBBaseModel):
    """流程操作日志表"""
    __tablename__ = "workflow_operation_log"
    __table_args__ = (
        Index("idx_instance_created", "process_instance_id", "created_at"),
        Index("idx_operation_type", "operation_type", "created_at"),
        Index("idx_tenant_created", "tenant_id", "created_at"),
    )

    # 核心字段
    tenant_id: int = Column(Integer, nullable=False, comment="租户ID")
    process_instance_id: int = Column(
        Integer, 
        ForeignKey("process_instance.id"), 
        nullable=False, 
        comment="流程实例ID"
    )
    operation_type: str = Column(
        String(20), 
        nullable=False, 
        comment="操作类型：SUBMIT/APPROVE/REJECT/CANCEL/CC"
    )
    operator_id: int = Column(
        Integer, 
        ForeignKey("user.id"), 
        nullable=False, 
        comment="操作人ID"
    )
    comment: Optional[str] = Column(
        String(500), 
        nullable=True, 
        comment="操作备注"
    )
    detail_json: Optional[dict] = Column(
        JSONB, 
        nullable=True, 
        comment="操作详情JSON"
    )
```

**索引策略**:
- `idx_instance_created`: 查询特定流程的操作日志
- `idx_operation_type`: 按操作类型统计
- `idx_tenant_created`: 租户级别的时间线查询

**detail_json 格式示例**:

```json
{
  "action": "approve",
  "node_id": 123,
  "node_name": "部长审批",
  "previous_state": "pending",
  "new_state": "completed",
  "form_data_snapshot": {
    "amount": 15000,
    "category": "招待"
  },
  "timestamp": "2024-12-20T10:30:00Z"
}
```

### 2.2 ProcessInstance.form_data_snapshot 字段

**表名**: `process_instance`

**新增字段**:

```python
form_data_snapshot: Optional[dict] = Column(
    JSONB, 
    nullable=True, 
    comment="表单数据快照"
)
```

**用途**: 保存流程启动时的表单数据，用于审批时查看原始数据

**数据格式**:

```json
{
  "applicant_name": "张三",
  "department": "技术部",
  "amount": 15000,
  "category": "招待",
  "description": "客户招待费用",
  "sys_submitter": 1001,
  "sys_submitter_dept": "总裁办",
  "sys_submit_time": "2024-12-20T10:00:00Z"
}
```

**特性**:
- 在流程启动时自动保存
- 流程推进过程中保持不变
- 支持查询和导出

### 2.3 Task 表扩展字段

**表名**: `task`

**新增字段**:

```python
task_type: str = Column(
    String(20), 
    default="approve", 
    nullable=False,
    comment="任务类型：approve/cc"
)
comment: Optional[str] = Column(
    String(500), 
    nullable=True,
    comment="审批意见"
)
```

**task_type 取值**:
- `approve`: 审批任务，需要用户进行审批操作
- `cc`: 抄送任务，仅作为信息通知

**comment 用途**: 存储用户的审批意见或备注

---

## 三、API 设计

### 3.1 表单字段 API

**端点**: `GET /api/v1/forms/{form_id}/fields`

**功能**: 获取表单的字段定义，用于条件构造器

**请求参数**:

```python
@router.get(
    "/forms/{form_id}/fields",
    summary="获取表单字段定义",
    response_model=FormFieldsResponse
)
async def get_form_fields(
    form_id: int = Path(..., description="表单ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """获取表单的所有字段定义"""
    pass
```

**响应格式**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "form_id": 123,
    "form_name": "出差申请表",
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
        "required": true,
        "min": 0,
        "max": 1000000
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

**字段类型支持**:
- `text`: 文本
- `number`: 数字
- `select`: 单选
- `checkbox`: 多选
- `date`: 日期
- `datetime`: 日期时间
- `textarea`: 多行文本
- `radio`: 单选按钮

**系统字段**:
- `sys_submitter`: 提交人ID
- `sys_submitter_dept`: 提交人部门
- `sys_submit_time`: 提交时间

**错误响应**:

```json
{
  "code": 404,
  "message": "Form not found"
}
```

---

## 四、服务层设计

### 4.1 ProcessService 扩展

**新增方法**:

```python
@staticmethod
def _create_cc_tasks(
    process: ProcessInstance,
    node: FlowNode,
    tenant_id: int,
    db: Session,
) -> List[Task]:
    """为 CC 节点创建抄送任务
    
    :param process: 流程实例
    :param node: CC 节点
    :param tenant_id: 租户 ID
    :param db: 数据库会话
    :return: 创建的抄送任务列表
    
    Time: O(N), Space: O(N)
    """
    cc_tasks = []
    
    # 获取抄送人列表
    assignee_user_ids = AssignmentService.select_cc_assignees(
        node, tenant_id, db
    )
    
    for user_id in assignee_user_ids:
        task = Task(
            tenant_id=tenant_id,
            process_instance_id=process.id,
            node_id=node.id,
            assignee_user_id=user_id,
            task_type="cc",  # 标记为抄送任务
            due_at=SLAService.calculate_due_at(node.sla_hours),
        )
        db.add(task)
        cc_tasks.append(task)
    
    return cc_tasks
```

### 4.2 AssignmentService 扩展

**新增方法**:

```python
@staticmethod
def select_cc_assignees(
    node: FlowNode,
    tenant_id: int,
    db: Session,
) -> List[int]:
    """解析 CC 节点配置，获取抄送人列表
    
    :param node: CC 节点
    :param tenant_id: 租户 ID
    :param db: 数据库会话
    :return: 抄送人用户ID列表
    
    Time: O(N), Space: O(N)
    """
    
    assignee_user_ids = []
    
    if not node.assignee_value:
        return assignee_user_ids
    
    config = node.assignee_value
    if not isinstance(config, dict):
        return assignee_user_ids
    
    assignees = config.get("assignees", [])
    
    for assignee in assignees:
        assignee_type = assignee.get("type")
        assignee_value = assignee.get("value")
        
        if assignee_type == "user":
            assignee_user_ids.append(assignee_value)
        
        elif assignee_type == "role":
            # 获取角色下的所有用户
            role_users = AssignmentService._get_users_by_role(
                assignee_value, tenant_id, db
            )
            assignee_user_ids.extend(role_users)
        
        elif assignee_type == "department":
            # 获取部门下的所有用户
            dept_users = AssignmentService._get_users_by_department(
                assignee_value, tenant_id, db
            )
            assignee_user_ids.extend(dept_users)
        
        elif assignee_type == "position":
            # 获取职位下的所有用户
            pos_users = AssignmentService._get_users_by_position(
                assignee_value, tenant_id, db
            )
            assignee_user_ids.extend(pos_users)
    
    # 去重
    return list(set(assignee_user_ids))
```

### 4.3 FormFieldService 新增

**新增服务类**:

```python
class FormFieldService:
    """表单字段服务"""
    
    @staticmethod
    def get_form_fields(
        form_id: int,
        tenant_id: int,
        db: Session,
    ) -> Dict[str, Any]:
        """获取表单的字段定义
        
        :param form_id: 表单ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 字段定义字典
        
        Time: O(N), Space: O(N)
        """
        
        form = (
            db.query(Form)
            .filter(
                Form.id == form_id,
                Form.tenant_id == tenant_id,
            )
            .first()
        )
        
        if not form:
            raise BusinessError("表单不存在")
        
        # 获取最新版本的表单
        form_version = (
            db.query(FormVersion)
            .filter(
                FormVersion.form_id == form_id,
                FormVersion.tenant_id == tenant_id,
            )
            .order_by(FormVersion.version.desc())
            .first()
        )
        
        if not form_version:
            return {"fields": []}
        
        # 解析表单字段
        fields = FormFieldService._parse_form_fields(
            form_version.schema_json
        )
        
        # 添加系统字段
        fields.extend(FormFieldService._get_system_fields())
        
        return {
            "form_id": form_id,
            "form_name": form.name,
            "fields": fields,
        }
    
    @staticmethod
    def _parse_form_fields(schema: dict) -> List[Dict[str, Any]]:
        """解析表单 schema，提取字段定义"""
        
        fields = []
        
        if not schema or not isinstance(schema, dict):
            return fields
        
        # 遍历表单字段
        form_fields = schema.get("fields", [])
        
        for field in form_fields:
            field_def = {
                "key": field.get("key"),
                "name": field.get("label", field.get("key")),
                "type": field.get("type", "text"),
                "required": field.get("required", False),
                "description": field.get("description", ""),
            }
            
            # 处理选项字段
            if field_def["type"] in ["select", "checkbox", "radio"]:
                options = field.get("options", [])
                field_def["options"] = [
                    {
                        "label": opt.get("label", opt.get("value")),
                        "value": opt.get("value"),
                    }
                    for opt in options
                ]
            
            # 处理数字字段
            if field_def["type"] == "number":
                if "min" in field:
                    field_def["min"] = field["min"]
                if "max" in field:
                    field_def["max"] = field["max"]
            
            fields.append(field_def)
        
        return fields
    
    @staticmethod
    def _get_system_fields() -> List[Dict[str, Any]]:
        """获取系统字段定义"""
        
        return [
            {
                "key": "sys_submitter",
                "name": "提交人",
                "type": "text",
                "system": True,
                "required": False,
            },
            {
                "key": "sys_submitter_dept",
                "name": "提交人部门",
                "type": "text",
                "system": True,
                "required": False,
            },
            {
                "key": "sys_submit_time",
                "name": "提交时间",
                "type": "date",
                "system": True,
                "required": False,
            },
        ]
```

---

## 五、流程推进逻辑

### 5.1 CC 节点处理流程

在 `ProcessService._dispatch_nodes()` 中添加 CC 节点处理：

```python
if node.type == "cc":
    # 处理抄送节点
    ProcessService._create_cc_tasks(process, node, tenant_id, db)
    
    # 记录操作日志
    WorkflowOperationLogService.create_log(
        tenant_id=tenant_id,
        process_instance_id=process.id,
        operation_type="CC",
        operator_id=SYSTEM_USER_ID,
        detail_json={
            "node_id": node.id,
            "node_name": node.name,
            "cc_count": len(cc_tasks),
        },
        db=db,
    )
    
    # CC 节点后继续推进流程
    cc_next = ProcessService._resolve_next_nodes(
        flow_definition_id=process.flow_definition_id,
        from_node=node,
        tenant_id=tenant_id,
        db=db,
        context=context,
    )
    tasks.extend(
        ProcessService._dispatch_nodes(
            process=process,
            candidate_nodes=cc_next,
            tenant_id=tenant_id,
            db=db,
            context=context,
            visited=visited,
            origin_node=node,
        )
    )
    continue
```

### 5.2 操作日志记录

在审批操作完成时记录日志：

```python
@staticmethod
def record_operation_log(
    tenant_id: int,
    process_instance_id: int,
    operation_type: str,
    operator_id: int,
    comment: Optional[str] = None,
    detail_json: Optional[dict] = None,
    db: Session = None,
) -> WorkflowOperationLog:
    """记录流程操作日志
    
    :param tenant_id: 租户ID
    :param process_instance_id: 流程实例ID
    :param operation_type: 操作类型
    :param operator_id: 操作人ID
    :param comment: 操作备注
    :param detail_json: 操作详情
    :param db: 数据库会话
    :return: 创建的日志记录
    """
    
    log = WorkflowOperationLog(
        tenant_id=tenant_id,
        process_instance_id=process_instance_id,
        operation_type=operation_type,
        operator_id=operator_id,
        comment=comment,
        detail_json=detail_json or {},
    )
    
    db.add(log)
    db.flush()
    
    return log
```

---

## 六、缓存策略

### 6.1 表单字段缓存

使用 Redis 缓存表单字段定义，提高性能：

```python
@staticmethod
def get_form_fields_cached(
    form_id: int,
    tenant_id: int,
    db: Session,
    redis_client = None,
) -> Dict[str, Any]:
    """获取表单字段定义（带缓存）
    
    缓存键: form:fields:{tenant_id}:{form_id}
    缓存时间: 1 小时
    """
    
    if redis_client:
        cache_key = f"form:fields:{tenant_id}:{form_id}"
        cached = redis_client.get(cache_key)
        
        if cached:
            return json.loads(cached)
    
    # 从数据库获取
    fields = FormFieldService.get_form_fields(
        form_id, tenant_id, db
    )
    
    # 存入缓存
    if redis_client:
        redis_client.setex(
            cache_key,
            3600,  # 1 小时
            json.dumps(fields),
        )
    
    return fields
```

---

## 七、错误处理

### 7.1 常见错误场景

```python
# 表单不存在
if not form:
    raise BusinessError("表单不存在", code=404)

# 无权访问表单
if form.tenant_id != tenant_id:
    raise PermissionError("无权访问该表单")

# CC 节点配置无效
if not node.assignee_value:
    logger.warning(f"CC node {node.id} has no assignee config")
    # 继续推进流程，不阻塞

# 抄送人列表为空
if not assignee_user_ids:
    logger.warning(f"CC node {node.id} has no assignees")
    # 继续推进流程，不阻塞
```

---

## 八、性能考虑

### 8.1 性能指标

| 操作 | 目标 | 说明 |
|-----|------|------|
| 记录操作日志 | < 100ms | 异步操作，不阻塞流程 |
| 获取表单字段 | < 200ms | 支持缓存 |
| 创建 CC 任务 | < 50ms/个 | 批量创建 |
| 查询操作日志 | < 300ms | 使用索引 |

### 8.2 优化建议

- 使用数据库索引加速查询
- 使用 Redis 缓存表单字段定义
- 异步记录操作日志
- 批量创建 CC 任务

---

## 九、测试策略

### 9.1 单元测试

- ✅ WorkflowOperationLog 的创建和查询
- ✅ form_data_snapshot 的保存和查询
- ✅ Task 扩展字段的设置
- ✅ 表单字段 API 的解析
- ✅ CC 节点的抄送人解析

### 9.2 集成测试

- ✅ 完整的审批流程（包括操作日志记录）
- ✅ CC 节点的完整流程
- ✅ 审批时间线的查询
- ✅ 表单字段 API 与条件构造器的集成

---

## 十、实现路线图

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
- 实现 _create_cc_tasks() 方法
- 在 _dispatch_nodes() 中添加 CC 处理
- 实现 select_cc_assignees() 方法

**Day 3**: CC 节点集成测试
- 编写集成测试
- 验证完整流程

---

**文档版本**: 1.0  
**创建日期**: 2024-12-20  
**状态**: 待审核


---

## 十一、详细实现指南

### 11.1 数据库迁移脚本

**文件**: `backend/alembic/versions/XXX_add_remaining_features.py`

```python
"""Add remaining features for approval flow

Revision ID: xxx
Revises: yyy
Create Date: 2024-12-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'xxx'
down_revision = 'yyy'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 添加 ProcessInstance.form_data_snapshot 字段
    op.add_column(
        'process_instance',
        sa.Column(
            'form_data_snapshot',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='表单数据快照'
        )
    )
    
    # 2. 扩展 Task 表
    op.add_column(
        'task',
        sa.Column(
            'task_type',
            sa.String(20),
            server_default='approve',
            nullable=False,
            comment='任务类型：approve/cc'
        )
    )
    op.add_column(
        'task',
        sa.Column(
            'comment',
            sa.String(500),
            nullable=True,
            comment='审批意见'
        )
    )
    
    # 3. 创建 WorkflowOperationLog 表
    op.create_table(
        'workflow_operation_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('process_instance_id', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(20), nullable=False),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('comment', sa.String(500), nullable=True),
        sa.Column(
            'detail_json',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True
        ),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['process_instance_id'], ['process_instance.id']),
        sa.ForeignKeyConstraint(['operator_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index(
        'idx_instance_created',
        'workflow_operation_log',
        ['process_instance_id', 'created_at']
    )
    op.create_index(
        'idx_operation_type',
        'workflow_operation_log',
        ['operation_type', 'created_at']
    )
    op.create_index(
        'idx_tenant_created',
        'workflow_operation_log',
        ['tenant_id', 'created_at']
    )


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_tenant_created', table_name='workflow_operation_log')
    op.drop_index('idx_operation_type', table_name='workflow_operation_log')
    op.drop_index('idx_instance_created', table_name='workflow_operation_log')
    
    # 删除表
    op.drop_table('workflow_operation_log')
    
    # 删除字段
    op.drop_column('task', 'comment')
    op.drop_column('task', 'task_type')
    op.drop_column('process_instance', 'form_data_snapshot')
```

### 11.2 表单字段 API 实现

**文件**: `backend/app/api/v1/forms.py`

```python
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_tenant_id, get_current_user
from app.core.database import get_db
from app.core.response import success_response
from app.models.user import User
from app.schemas.form_schemas import FormFieldsResponse
from app.services.form_field_service import FormFieldService

router = APIRouter()


@router.get(
    "/{form_id}/fields",
    summary="获取表单字段定义",
    response_model=FormFieldsResponse,
)
async def get_form_fields(
    form_id: int = Path(..., description="表单ID"),
    current_user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """获取表单的所有字段定义，用于条件构造器
    
    :param form_id: 表单ID
    :param current_user: 当前用户
    :param tenant_id: 租户ID
    :param db: 数据库会话
    :return: 字段定义列表
    
    Time: O(N), Space: O(N)
    """
    
    fields_data = FormFieldService.get_form_fields(
        form_id=form_id,
        tenant_id=tenant_id,
        db=db,
    )
    
    return success_response(data=fields_data)
```

### 11.3 操作日志服务

**文件**: `backend/app/services/workflow_operation_log_service.py`

```python
"""
模块用途: 流程操作日志服务
依赖配置: 无
数据流向: 操作事件 -> 日志记录 -> 数据库
函数清单:
    - create_log(): 创建操作日志
    - get_process_logs(): 查询流程日志
    - get_operation_timeline(): 获取操作时间线
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.workflow import WorkflowOperationLog
from app.core.logger import logger


class WorkflowOperationLogService:
    """流程操作日志服务"""
    
    @staticmethod
    def create_log(
        tenant_id: int,
        process_instance_id: int,
        operation_type: str,
        operator_id: int,
        comment: Optional[str] = None,
        detail_json: Optional[Dict[str, Any]] = None,
        db: Session = None,
    ) -> WorkflowOperationLog:
        """创建操作日志
        
        :param tenant_id: 租户ID
        :param process_instance_id: 流程实例ID
        :param operation_type: 操作类型
        :param operator_id: 操作人ID
        :param comment: 操作备注
        :param detail_json: 操作详情
        :param db: 数据库会话
        :return: 创建的日志记录
        
        Time: O(1), Space: O(1)
        """
        
        try:
            log = WorkflowOperationLog(
                tenant_id=tenant_id,
                process_instance_id=process_instance_id,
                operation_type=operation_type,
                operator_id=operator_id,
                comment=comment,
                detail_json=detail_json or {},
            )
            
            db.add(log)
            db.flush()
            
            logger.info(
                f"Created operation log",
                extra={
                    "process_instance_id": process_instance_id,
                    "operation_type": operation_type,
                    "operator_id": operator_id,
                }
            )
            
            return log
        
        except Exception as e:
            logger.error(
                f"Failed to create operation log: {e}",
                exc_info=True,
                extra={
                    "process_instance_id": process_instance_id,
                    "operation_type": operation_type,
                }
            )
            raise
    
    @staticmethod
    def get_process_logs(
        process_instance_id: int,
        tenant_id: int,
        db: Session,
        limit: int = 100,
    ) -> List[WorkflowOperationLog]:
        """查询流程的操作日志
        
        :param process_instance_id: 流程实例ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :param limit: 返回数量限制
        :return: 操作日志列表
        
        Time: O(N), Space: O(N)
        """
        
        logs = (
            db.query(WorkflowOperationLog)
            .filter(
                WorkflowOperationLog.process_instance_id == process_instance_id,
                WorkflowOperationLog.tenant_id == tenant_id,
            )
            .order_by(WorkflowOperationLog.created_at.asc())
            .limit(limit)
            .all()
        )
        
        return logs
    
    @staticmethod
    def get_operation_timeline(
        process_instance_id: int,
        tenant_id: int,
        db: Session,
    ) -> List[Dict[str, Any]]:
        """获取操作时间线
        
        :param process_instance_id: 流程实例ID
        :param tenant_id: 租户ID
        :param db: 数据库会话
        :return: 时间线数据
        
        Time: O(N), Space: O(N)
        """
        
        logs = WorkflowOperationLogService.get_process_logs(
            process_instance_id=process_instance_id,
            tenant_id=tenant_id,
            db=db,
        )
        
        timeline = []
        
        for log in logs:
            timeline.append({
                "id": log.id,
                "operation_type": log.operation_type,
                "operator_id": log.operator_id,
                "comment": log.comment,
                "detail": log.detail_json,
                "created_at": log.created_at.isoformat(),
            })
        
        return timeline
```

### 11.4 CC 节点处理实现

**在 ProcessService 中添加**:

```python
@staticmethod
def _create_cc_tasks(
    process: ProcessInstance,
    node: FlowNode,
    tenant_id: int,
    db: Session,
) -> List[Task]:
    """为 CC 节点创建抄送任务
    
    :param process: 流程实例
    :param node: CC 节点
    :param tenant_id: 租户 ID
    :param db: 数据库会话
    :return: 创建的抄送任务列表
    
    Time: O(N), Space: O(N)
    """
    
    cc_tasks = []
    
    try:
        # 获取抄送人列表
        assignee_user_ids = AssignmentService.select_cc_assignees(
            node, tenant_id, db
        )
        
        if not assignee_user_ids:
            logger.warning(
                f"CC node {node.id} has no assignees",
                extra={"process_instance_id": process.id}
            )
            return cc_tasks
        
        # 为每个抄送人创建任务
        for user_id in assignee_user_ids:
            task = Task(
                tenant_id=tenant_id,
                process_instance_id=process.id,
                node_id=node.id,
                assignee_user_id=user_id,
                task_type="cc",  # 标记为抄送任务
                due_at=SLAService.calculate_due_at(node.sla_hours),
            )
            db.add(task)
            cc_tasks.append(task)
        
        # 记录操作日志
        WorkflowOperationLogService.create_log(
            tenant_id=tenant_id,
            process_instance_id=process.id,
            operation_type="CC",
            operator_id=SYSTEM_USER_ID,
            detail_json={
                "node_id": node.id,
                "node_name": node.name,
                "cc_count": len(cc_tasks),
                "assignees": assignee_user_ids,
            },
            db=db,
        )
        
        logger.info(
            f"Created {len(cc_tasks)} CC tasks",
            extra={
                "process_instance_id": process.id,
                "node_id": node.id,
                "cc_count": len(cc_tasks),
            }
        )
        
        return cc_tasks
    
    except Exception as e:
        logger.error(
            f"Failed to create CC tasks: {e}",
            exc_info=True,
            extra={"process_instance_id": process.id, "node_id": node.id}
        )
        return cc_tasks
```

### 11.5 AssignmentService 扩展

**添加 CC 抄送人解析**:

```python
@staticmethod
def select_cc_assignees(
    node: FlowNode,
    tenant_id: int,
    db: Session,
) -> List[int]:
    """解析 CC 节点配置，获取抄送人列表
    
    :param node: CC 节点
    :param tenant_id: 租户 ID
    :param db: 数据库会话
    :return: 抄送人用户ID列表
    
    Time: O(N), Space: O(N)
    """
    
    assignee_user_ids = []
    
    if not node.assignee_value:
        return assignee_user_ids
    
    config = node.assignee_value
    if not isinstance(config, dict):
        return assignee_user_ids
    
    assignees = config.get("assignees", [])
    
    for assignee in assignees:
        assignee_type = assignee.get("type")
        assignee_value = assignee.get("value")
        
        if not assignee_type or not assignee_value:
            continue
        
        try:
            if assignee_type == "user":
                assignee_user_ids.append(assignee_value)
            
            elif assignee_type == "role":
                # 获取角色下的所有用户
                role_users = AssignmentService._get_users_by_role(
                    assignee_value, tenant_id, db
                )
                assignee_user_ids.extend(role_users)
            
            elif assignee_type == "department":
                # 获取部门下的所有用户
                dept_users = AssignmentService._get_users_by_department(
                    assignee_value, tenant_id, db
                )
                assignee_user_ids.extend(dept_users)
            
            elif assignee_type == "position":
                # 获取职位下的所有用户
                pos_users = AssignmentService._get_users_by_position(
                    assignee_value, tenant_id, db
                )
                assignee_user_ids.extend(pos_users)
        
        except Exception as e:
            logger.warning(
                f"Failed to resolve CC assignee: {e}",
                extra={
                    "assignee_type": assignee_type,
                    "assignee_value": assignee_value,
                }
            )
            continue
    
    # 去重并排序
    return sorted(list(set(assignee_user_ids)))

@staticmethod
def _get_users_by_role(
    role_id: int,
    tenant_id: int,
    db: Session,
) -> List[int]:
    """获取角色下的所有用户"""
    # 实现细节：查询 user_role 表
    pass

@staticmethod
def _get_users_by_department(
    dept_id: int,
    tenant_id: int,
    db: Session,
) -> List[int]:
    """获取部门下的所有用户"""
    # 实现细节：查询 user 表，按 department_id 过滤
    pass

@staticmethod
def _get_users_by_position(
    position_id: int,
    tenant_id: int,
    db: Session,
) -> List[int]:
    """获取职位下的所有用户"""
    # 实现细节：查询 user 表，按 position_id 过滤
    pass
```

---

## 十二、Pydantic 数据模型

### 12.1 表单字段响应模型

**文件**: `backend/app/schemas/form_schemas.py`

```python
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FormFieldOption(BaseModel):
    """字段选项"""
    label: str = Field(..., description="选项标签")
    value: Any = Field(..., description="选项值")


class FormField(BaseModel):
    """表单字段定义"""
    key: str = Field(..., description="字段唯一标识")
    name: str = Field(..., description="字段显示名称")
    type: str = Field(..., description="字段类型")
    required: bool = Field(default=False, description="是否必填")
    description: Optional[str] = Field(default=None, description="字段描述")
    system: bool = Field(default=False, description="是否为系统字段")
    options: Optional[List[FormFieldOption]] = Field(
        default=None, description="字段选项"
    )
    min: Optional[float] = Field(default=None, description="最小值")
    max: Optional[float] = Field(default=None, description="最大值")


class FormFieldsResponse(BaseModel):
    """表单字段列表响应"""
    form_id: int = Field(..., description="表单ID")
    form_name: str = Field(..., description="表单名称")
    fields: List[FormField] = Field(..., description="字段列表")
```

---

## 十三、集成测试场景

### 13.1 CC 节点完整流程测试

```python
def test_cc_node_complete_flow(db: Session, tenant_id: int):
    """测试 CC 节点的完整流程"""
    
    # 1. 创建表单和流程定义
    form = create_test_form(db, tenant_id)
    flow_def = create_test_flow_with_cc_node(db, tenant_id, form.id)
    
    # 2. 创建提交和流程实例
    submission = create_test_submission(db, tenant_id, form.id)
    process = ProcessService.start_process(
        form_id=form.id,
        form_version_id=form.latest_version_id,
        submission_id=submission.id,
        tenant_id=tenant_id,
        db=db,
    )
    
    # 3. 验证初始任务被创建
    initial_tasks = db.query(Task).filter(
        Task.process_instance_id == process.id,
        Task.task_type == "approve",
    ).all()
    assert len(initial_tasks) > 0
    
    # 4. 完成初始审批任务
    initial_task = initial_tasks[0]
    initial_task.status = "completed"
    initial_task.action = "approve"
    initial_task.completed_by = 1001
    initial_task.completed_at = datetime.utcnow()
    
    # 5. 推进流程到 CC 节点
    ProcessService.handle_task_completion(
        task=initial_task,
        tenant_id=tenant_id,
        db=db,
    )
    
    # 6. 验证 CC 任务被创建
    cc_tasks = db.query(Task).filter(
        Task.process_instance_id == process.id,
        Task.task_type == "cc",
    ).all()
    assert len(cc_tasks) > 0
    
    # 7. 验证操作日志被记录
    cc_logs = db.query(WorkflowOperationLog).filter(
        WorkflowOperationLog.process_instance_id == process.id,
        WorkflowOperationLog.operation_type == "CC",
    ).all()
    assert len(cc_logs) > 0
    
    # 8. 验证流程继续推进
    assert process.state == "running" or process.state == "finished"
```

### 13.2 表单字段 API 测试

```python
def test_get_form_fields_api(client, db: Session, tenant_id: int):
    """测试表单字段 API"""
    
    # 1. 创建测试表单
    form = create_test_form(db, tenant_id)
    
    # 2. 调用 API
    response = client.get(
        f"/api/v1/forms/{form.id}/fields",
        headers={"X-Tenant-ID": str(tenant_id)},
    )
    
    # 3. 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "data" in data
    assert "fields" in data["data"]
    
    # 4. 验证字段内容
    fields = data["data"]["fields"]
    assert len(fields) > 0
    
    # 5. 验证系统字段存在
    system_fields = [f for f in fields if f.get("system")]
    assert len(system_fields) >= 3  # sys_submitter, sys_submitter_dept, sys_submit_time
```

### 13.3 操作日志记录测试

```python
def test_operation_log_recording(db: Session, tenant_id: int):
    """测试操作日志记录"""
    
    # 1. 创建流程实例
    process = create_test_process_instance(db, tenant_id)
    
    # 2. 记录操作日志
    log = WorkflowOperationLogService.create_log(
        tenant_id=tenant_id,
        process_instance_id=process.id,
        operation_type="APPROVE",
        operator_id=1001,
        comment="同意",
        detail_json={"node_id": 123, "node_name": "部长审批"},
        db=db,
    )
    
    # 3. 验证日志被创建
    assert log.id is not None
    assert log.operation_type == "APPROVE"
    assert log.operator_id == 1001
    
    # 4. 查询日志
    logs = WorkflowOperationLogService.get_process_logs(
        process_instance_id=process.id,
        tenant_id=tenant_id,
        db=db,
    )
    
    # 5. 验证查询结果
    assert len(logs) > 0
    assert logs[0].id == log.id
```

---

## 十四、验收标准

### 14.1 功能验收

| 功能 | 验收标准 | 状态 |
|-----|---------|------|
| WorkflowOperationLog 表 | 所有操作都被记录 | ⏳ |
| form_data_snapshot 字段 | 表单数据被正确保存 | ⏳ |
| Task 扩展字段 | 任务类型和意见被正确记录 | ⏳ |
| 表单字段 API | API 返回正确的字段定义 | ⏳ |
| CC 节点业务逻辑 | CC 任务被正确创建和处理 | ⏳ |

### 14.2 性能验收

| 指标 | 目标 | 状态 |
|-----|------|------|
| 操作日志记录 | < 100ms | ⏳ |
| 表单字段 API | < 200ms | ⏳ |
| CC 任务创建 | < 50ms/个 | ⏳ |
| 操作日志查询 | < 300ms | ⏳ |

---

**文档版本**: 1.0  
**最后更新**: 2024-12-20  
**状态**: 完成
