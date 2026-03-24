# 审批流程优化 - 快速启动清单

## 🚀 立即行动（今天）

### 1. 确认优先级和资源分配

- [ ] 与产品团队确认 P0 优先级任务
- [ ] 分配后端开发人员（1-2 人）
- [ ] 分配前端开发人员（1-2 人）
- [ ] 分配测试人员（1 人）
- [ ] 建立每日站会（15 分钟）

### 2. 建立开发环境

**后端**：
```bash
# 创建新分支
git checkout -b feature/approval-flow-optimization

# 安装依赖
pip install -r requirements.txt

# 运行现有测试
pytest

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

**前端**：
```bash
# 创建新分支
git checkout -b feature/approval-flow-optimization

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 3. 创建任务跟踪

- [ ] 在项目管理工具中创建 Epic：审批流程优化
- [ ] 创建 P0 阶段的 Story（10-12 个任务）
- [ ] 创建 P1 阶段的 Story（10-12 个任务）
- [ ] 设置每个任务的优先级和工作量估算

---

## 📋 第 1 周任务清单

### Day 1-2：条件表达式格式统一

**后端**：
- [ ] 创建 `backend/app/services/condition_evaluator_v2.py`
- [ ] 实现 `ConditionEvaluatorV2` 类
- [ ] 创建 `backend/app/services/condition_converter.py`
- [ ] 编写单元测试
- [ ] 测试通过

**前端**：
- [ ] 验证条件构造器生成的格式
- [ ] 无需修改

**测试**：
- [ ] 单元测试通过率 100%
- [ ] 集成测试通过

---

### Day 3-4：CONDITION 节点实现

**后端**：
- [ ] 创建数据库迁移：`008_add_condition_node_support.py`
- [ ] 运行迁移：`alembic upgrade head`
- [ ] 在 `ProcessService` 中添加 CONDITION 处理
- [ ] 在 `FlowService` 中添加 CONDITION 校验
- [ ] 编写单元测试
- [ ] 测试通过

**前端**：
- [ ] 更新 `my-app/src/types/flow.ts`
- [ ] 创建 `ConditionNodeEditor.vue` 组件
- [ ] 集成到流程设计器
- [ ] 编写单元测试

**测试**：
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试：创建条件节点 → 配置分支 → 发布 → 执行

---

### Day 5：表单字段 API

**后端**：
- [ ] 在 `backend/app/api/v1/forms.py` 中添加 `get_form_fields()` 端点
- [ ] 编写单元测试
- [ ] 测试通过

**前端**：
- [ ] 在 `my-app/src/api/form.ts` 中添加 `getFormFields()` 函数
- [ ] 在条件构造器中集成
- [ ] 编写单元测试

**测试**：
- [ ] API 测试通过
- [ ] 集成测试通过

---

## 📋 第 2 周任务清单

### Day 1-2：驳回策略实现

**后端**：
- [ ] 创建数据库迁移：`009_add_reject_strategy.py`
- [ ] 运行迁移
- [ ] 在 `ApprovalService` 中实现 `_handle_rejection()`
- [ ] 编写单元测试

**前端**：
- [ ] 更新类型定义
- [ ] 在审批节点编辑器中添加驳回策略选择
- [ ] 编写单元测试

**测试**：
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试：驳回 → TO_START 和 TO_PREVIOUS

---

### Day 3-5：审批操作 API

**后端**：
- [ ] 创建 `backend/app/api/v1/approvals.py`
- [ ] 实现 `approve_task()` 端点
- [ ] 实现 `reject_task()` 端点
- [ ] 实现 `cancel_instance()` 端点
- [ ] 创建 `backend/app/schemas/approval_schemas.py`
- [ ] 编写单元测试
- [ ] 测试通过

**前端**：
- [ ] 创建 `my-app/src/api/approval.ts`
- [ ] 实现 API 接口
- [ ] 创建 `ApprovalDetail.vue` 页面
- [ ] 编写单元测试

**测试**：
- [ ] API 测试通过
- [ ] 集成测试通过
- [ ] 手动测试：完整审批流程

---

## 🔍 代码审查清单

### 后端代码审查

- [ ] 遵循 snake_case 命名规范
- [ ] 所有函数都有类型注解
- [ ] 所有异常都被正确处理
- [ ] 所有 API 都有权限检查
- [ ] 所有数据库操作都在事务中
- [ ] 所有日志都使用结构化日志
- [ ] 所有测试都通过
- [ ] 代码覆盖率 > 80%

### 前端代码审查

- [ ] 遵循 PascalCase 命名规范
- [ ] 所有组件都使用 `<script setup lang="ts">`
- [ ] 所有类型都有 TypeScript 定义
- [ ] 所有 API 调用都有错误处理
- [ ] 所有组件都有单元测试
- [ ] 代码覆盖率 > 80%

---

## 🧪 测试清单

### 单元测试

- [ ] 条件评估器：所有 15 种运算符
- [ ] 条件评估器：类型转换
- [ ] 条件评估器：嵌套条件
- [ ] 路由推进：CONDITION 节点
- [ ] 驳回处理：TO_START 策略
- [ ] 驳回处理：TO_PREVIOUS 策略
- [ ] 审批操作：权限检查
- [ ] 审批操作：状态更新

### 集成测试

- [ ] 完整流程：设计 → 发布 → 提交 → 审批 → 完成
- [ ] 条件分支：多条件分支 → 正确路由
- [ ] 驳回流程：驳回 → 重新审批 → 通过
- [ ] 撤回流程：撤回 → 流程取消

### 端到端测试

- [ ] 流程设计器：创建节点 → 连线 → 配置 → 保存 → 发布
- [ ] 审批流程：填写表单 → 提交 → 待办 → 审批 → 完成
- [ ] 条件分支：多条件分支 → 正确路由
- [ ] 驳回流程：驳回 → 重新审批 → 通过

---

## 📊 进度跟踪

### 第 1 周进度

| 日期 | 任务 | 状态 | 备注 |
|------|------|------|------|
| Day 1-2 | 条件格式统一 | ⬜ | - |
| Day 3-4 | CONDITION 节点 | ⬜ | - |
| Day 5 | 表单字段 API | ⬜ | - |

### 第 2 周进度

| 日期 | 任务 | 状态 | 备注 |
|------|------|------|------|
| Day 1-2 | 驳回策略 | ⬜ | - |
| Day 3-5 | 审批操作 API | ⬜ | - |

---

## 🚨 常见问题

### Q1：条件表达式格式如何转换？

**A**：使用 `ConditionConverter` 类将 JsonLogic 转换为设计格式。

```python
from app.services.condition_converter import ConditionConverter

# JsonLogic 格式
jsonlogic_condition = {
    "and": [
        { ">=": [{ "var": "amount" }, 10000] },
        { "==": [{ "var": "category" }, "招待"] }
    ]
}

# 转换为设计格式
design_condition = ConditionConverter.convert(jsonlogic_condition)
```

### Q2：如何测试 CONDITION 节点？

**A**：创建一个包含 CONDITION 节点的流程，配置多个分支，然后提交表单验证路由。

### Q3：驳回策略如何工作？

**A**：
- TO_START：驳回到发起人，流程结束
- TO_PREVIOUS：驳回到上一个审批节点，重新审批

### Q4：如何处理权限检查？

**A**：在所有 API 端点中添加权限检查：

```python
if task.assignee_user_id != current_user.id:
    raise AuthorizationError("无权操作此任务")
```

---

## 📞 联系方式

- **技术负责人**：[名字]
- **产品负责人**：[名字]
- **测试负责人**：[名字]
- **每日站会**：[时间]
- **周进度评审**：[时间]

---

## 📚 参考文档

- ✅ APPROVAL_FLOW_DESIGN_ANALYSIS.md - 详细分析
- ✅ APPROVAL_FLOW_OPTIMIZATION_PLAN.md - 优化方案
- ✅ APPROVAL_FLOW_CODE_MAPPING.md - 代码对照
- ✅ IMPLEMENTATION_PHASE_1.md - 第一阶段详细计划
- ✅ IMPLEMENTATION_PHASE_2.md - 第二阶段详细计划

---

**最后更新**：2026-03-15
**版本**：1.0

