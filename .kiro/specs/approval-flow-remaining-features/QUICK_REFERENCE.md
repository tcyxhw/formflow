# 审批流程系统剩余功能 - 快速参考指南

## 功能概览

| 功能 | 优先级 | 工作量 | 关键文件 |
|-----|--------|--------|---------|
| WorkflowOperationLog 表 | P0 | 2h | `backend/alembic/versions/XXX_add_remaining_features.py` |
| form_data_snapshot 字段 | P0 | 1h | `backend/app/models/workflow.py` |
| Task 扩展字段 | P0 | 1h | `backend/app/models/workflow.py` |
| 表单字段 API | P0 | 3h | `backend/app/api/v1/forms.py` |
| CC 节点业务逻辑 | P1 | 5h | `backend/app/services/process_service.py` |

---

## 快速开始

### 1. 数据库迁移

```bash
# 创建迁移脚本
alembic revision --autogenerate -m "Add remaining features"

# 执行迁移
alembic upgrade head

# 验证迁移
psql -U postgres -d formflow -c "\dt workflow_operation_log"
```

### 2. 表单字段 API

```bash
# 测试 API
curl -X GET "http://localhost:8000/api/v1/forms/1/fields" \
  -H "Authorization: Bearer {token}" \
  -H "X-Tenant-ID: 1"
```

### 3. CC 节点配置

```json
{
  "nodeId": "cc_node_1",
  "nodeType": "CC",
  "name": "抄送给相关人员",
  "assignees": [
    {
      "type": "user",
      "value": 1001
    },
    {
      "type": "role",
      "value": "manager"
    },
    {
      "type": "department",
      "value": "tech"
    }
  ]
}
```

---

## 关键代码片段

### 创建操作日志

```python
from app.services.workflow_operation_log_service import WorkflowOperationLogService

log = WorkflowOperationLogService.create_log(
    tenant_id=1,
    process_instance_id=123,
    operation_type="APPROVE",
    operator_id=1001,
    comment="同意",
    detail_json={"node_id": 456},
    db=db,
)
```

### 获取表单字段

```python
from app.services.form_field_service import FormFieldService

fields = FormFieldService.get_form_fields(
    form_id=1,
    tenant_id=1,
    db=db,
)
```

### 创建 CC 任务

```python
from app.services.process_service import ProcessService

cc_tasks = ProcessService._create_cc_tasks(
    process=process,
    node=cc_node,
    tenant_id=1,
    db=db,
)
```

---

## 测试命令

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_workflow_operation_log.py

# 运行特定测试函数
pytest tests/test_workflow_operation_log.py::test_create_log

# 运行测试并显示覆盖率
pytest --cov=app tests/
```

---

## 常见问题

### Q: 如何验证迁移脚本？
A: 运行 `alembic upgrade head` 后，检查数据库表结构：
```sql
\d workflow_operation_log
\d task
\d process_instance
```

### Q: 表单字段 API 返回 404？
A: 检查表单是否存在，以及用户是否有权访问该表单。

### Q: CC 任务没有被创建？
A: 检查 CC 节点配置是否正确，以及抄送人列表是否为空。

### Q: 操作日志记录失败？
A: 检查数据库连接和权限，查看日志文件获取详细错误信息。

---

## 性能优化建议

1. **使用索引**: 已在迁移脚本中创建必要的索引
2. **缓存字段定义**: 使用 Redis 缓存表单字段定义
3. **异步记录日志**: 考虑使用消息队列异步记录操作日志
4. **批量创建任务**: 使用 `db.bulk_insert_mappings()` 批量创建 CC 任务

---

## 代码规范检查清单

- [ ] 使用 `snake_case` 命名函数和变量
- [ ] 使用 `PascalCase` 命名类
- [ ] 添加完整的类型注解
- [ ] 添加文档注释（docstring）
- [ ] 添加错误处理
- [ ] 添加日志记录
- [ ] 编写单元测试
- [ ] 编写集成测试

---

## 相关文档

- [完整设计文档](./design.md)
- [需求文档](./requirements.md)
- [任务清单](./tasks.md)

---

## 联系方式

如有问题，请参考设计文档或联系项目负责人。

---

**最后更新**: 2024-12-20
