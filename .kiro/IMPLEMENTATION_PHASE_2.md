# 审批流程优化 - 第二阶段实施计划（P1 优先级）

## 📅 时间表：第 3-4 周

### 第 3 周：流程设计器 UI + 查询接口

#### Day 1-3：流程设计器 UI

**目标**：实现完整的流程设计器前端

**任务清单**：

1. **前端：画布组件**
   - 文件：`my-app/src/components/flow-designer/FlowCanvas.vue`
   - 功能：
     - 节点拖拽
     - 连线绘制
     - 节点删除
     - 连线删除
     - 缩放和平移
   - 依赖：VueFlow 或 G6 库

2. **前端：节点编辑器**
   - 文件：`my-app/src/components/flow-designer/FlowNodeEditor.vue`
   - 功能：
     - 基本信息编辑（名称、类型）
     - 审批人配置
     - 驳回策略配置
     - 条件分支配置（CONDITION 节点）
     - SLA 配置
     - 自动审批配置

3. **前端：路由编辑器**
   - 文件：`my-app/src/components/flow-designer/FlowRouteEditor.vue`
   - 功能：
     - 条件表达式编辑
     - 优先级设置
     - 默认路由设置

4. **前端：节点调色板**
   - 文件：`my-app/src/components/flow-designer/FlowNodePalette.vue`
   - 功能：
     - 节点类型选择
     - 拖拽添加节点

5. **前端：主容器**
   - 文件：`my-app/src/views/FlowDesigner.vue`
   - 功能：
     - 整合所有子组件
     - 管理流程状态
     - 保存和发布流程

6. **前端：Pinia 状态管理**
   - 文件：`my-app/src/stores/useFlowStore.ts`
   - 功能：
     - 管理节点列表
     - 管理路由列表
     - 管理选中节点
     - 管理编辑状态

7. **测试**：
   - 单元测试：组件逻辑
   - 集成测试：组件交互
   - 端到端测试：完整设计流程

**交付物**：
- ✅ 画布组件
- ✅ 节点编辑器
- ✅ 路由编辑器
- ✅ 节点调色板
- ✅ 主容器
- ✅ Pinia 状态管理
- ✅ 单元测试

---

#### Day 4-5：查询接口

**目标**：实现待办、已办、我发起的、时间线查询接口

**任务清单**：

1. **后端：待办列表 API**
   - 文件：`backend/app/api/v1/approvals.py`
   - 端点：`GET /api/v1/approvals/pending`
   ```python
   @router.get("/pending", summary="待办列表")
   async def list_pending_tasks(
       page: int = Query(1, ge=1),
       size: int = Query(10, ge=1, le=100),
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       """获取当前用户的待办任务列表"""
       query = db.query(Task).filter(
           Task.assignee_user_id == current_user.id,
           Task.status == 'open'
       ).order_by(Task.created_at.desc())
       
       total = query.count()
       items = query.offset((page - 1) * size).limit(size).all()
       
       return success_response(data={
           'total': total,
           'items': [item.to_dict() for item in items]
       })
   ```

2. **后端：已办列表 API**
   - 端点：`GET /api/v1/approvals/completed`
   ```python
   @router.get("/completed", summary="已办列表")
   async def list_completed_tasks(
       page: int = Query(1, ge=1),
       size: int = Query(10, ge=1, le=100),
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       """获取当前用户的已办任务列表"""
       query = db.query(Task).filter(
           Task.assignee_user_id == current_user.id,
           Task.status.in_(['approved', 'rejected', 'canceled'])
       ).order_by(Task.completed_at.desc())
       
       total = query.count()
       items = query.offset((page - 1) * size).limit(size).all()
       
       return success_response(data={
           'total': total,
           'items': [item.to_dict() for item in items]
       })
   ```

3. **后端：我发起的 API**
   - 端点：`GET /api/v1/approvals/initiated`
   ```python
   @router.get("/initiated", summary="我发起的")
   async def list_initiated_instances(
       page: int = Query(1, ge=1),
       size: int = Query(10, ge=1, le=100),
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       """获取当前用户发起的流程实例"""
       query = db.query(ProcessInstance).join(Submission).filter(
           Submission.created_by == current_user.id
       ).order_by(ProcessInstance.created_at.desc())
       
       total = query.count()
       items = query.offset((page - 1) * size).limit(size).all()
       
       return success_response(data={
           'total': total,
           'items': [item.to_dict() for item in items]
       })
   ```

4. **后端：审批时间线 API**
   - 端点：`GET /api/v1/approvals/instances/{instance_id}/timeline`
   ```python
   @router.get("/instances/{instance_id}/timeline", summary="审批时间线")
   async def get_instance_timeline(
       instance_id: int,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       """获取流程实例的审批时间线"""
       logs = db.query(TaskActionLog).filter(
           TaskActionLog.instance_id == instance_id
       ).order_by(TaskActionLog.created_at.asc()).all()
       
       return success_response(data=[log.to_dict() for log in logs])
   ```

5. **前端：API 接口**
   - 文件：`my-app/src/api/approval.ts`
   ```typescript
   export const listPendingTasks = (page: number, size: number) => {
       return request.get('/api/v1/approvals/pending', { params: { page, size } })
   }
   
   export const listCompletedTasks = (page: number, size: number) => {
       return request.get('/api/v1/approvals/completed', { params: { page, size } })
   }
   
   export const listInitiatedInstances = (page: number, size: number) => {
       return request.get('/api/v1/approvals/initiated', { params: { page, size } })
   }
   
   export const getInstanceTimeline = (instanceId: number) => {
       return request.get(`/api/v1/approvals/instances/${instanceId}/timeline`)
   }
   ```

6. **前端：待办列表页面**
   - 文件：`my-app/src/views/PendingApprovals.vue`
   - 功能：显示待办任务列表，支持分页、搜索、排序

7. **前端：已办列表页面**
   - 文件：`my-app/src/views/CompletedApprovals.vue`
   - 功能：显示已办任务列表

8. **前端：我发起的页面**
   - 文件：`my-app/src/views/InitiatedInstances.vue`
   - 功能：显示发起的流程实例列表

9. **前端：审批时间线页面**
   - 文件：`my-app/src/views/ApprovalTimeline.vue`
   - 功能：显示流程实例的审批时间线

10. **测试**：
    - 单元测试：查询逻辑
    - 集成测试：API 调用
    - 端到端测试：页面交互

**交付物**：
- ✅ 4 个后端 API 端点
- ✅ 4 个前端 API 接口
- ✅ 4 个前端页面
- ✅ 单元测试
- ✅ 集成测试

---

### 第 4 周：条件评估器完善 + 优化

#### Day 1-2：条件评估器完善

**目标**：支持所有 15 种运算符

**任务清单**：

1. **后端：完善 ConditionEvaluatorV2**
   - 文件：`backend/app/services/condition_evaluator_v2.py`
   - 实现所有运算符：
   ```python
   @staticmethod
   def _compare(actual, operator, expected, field_type):
       """比较操作"""
       
       # 处理不需要值的运算符
       if operator == 'IS_EMPTY':
           return actual is None or actual == '' or (isinstance(actual, (list, dict)) and len(actual) == 0)
       elif operator == 'IS_NOT_EMPTY':
           return not (actual is None or actual == '' or (isinstance(actual, (list, dict)) and len(actual) == 0))
       
       # actual 为空时直接返回 false
       if actual is None:
           return False
       
       # 类型转换
       if field_type == 'NUMBER':
           try:
               actual = float(actual)
               expected = float(expected) if not isinstance(expected, list) else [float(e) for e in expected]
           except (TypeError, ValueError):
               return False
       elif field_type in ['DATE', 'DATETIME']:
           # 转换为日期对象
           pass
       elif field_type == 'MULTI_SELECT':
           actual = actual if isinstance(actual, list) else [actual]
           expected = expected if isinstance(expected, list) else [expected]
       
       # 执行比较
       if operator == 'EQUALS':
           return actual == expected
       elif operator == 'NOT_EQUALS':
           return actual != expected
       elif operator == 'GREATER_THAN':
           return actual > expected
       elif operator == 'GREATER_EQUAL':
           return actual >= expected
       elif operator == 'LESS_THAN':
           return actual < expected
       elif operator == 'LESS_EQUAL':
           return actual <= expected
       elif operator == 'BETWEEN':
           return expected[0] <= actual <= expected[1]
       elif operator == 'CONTAINS':
           return str(expected) in str(actual)
       elif operator == 'NOT_CONTAINS':
           return str(expected) not in str(actual)
       elif operator == 'IN':
           return actual in expected
       elif operator == 'NOT_IN':
           return actual not in expected
       elif operator == 'HAS_ANY':
           return any(item in actual for item in expected)
       elif operator == 'HAS_ALL':
           return all(item in actual for item in expected)
       
       return False
   ```

2. **后端：单元测试**
   - 文件：`backend/tests/test_condition_evaluator_v2.py`
   - 测试所有 15 种运算符
   - 测试类型转换
   - 测试嵌套条件

3. **前端：条件构造器测试**
   - 测试条件生成
   - 测试条件验证

**交付物**：
- ✅ 完善的条件评估器
- ✅ 单元测试

---

#### Day 3-4：性能优化和错误处理

**目标**：优化系统性能和错误处理

**任务清单**：

1. **后端：性能优化**
   - 添加数据库索引
   - 优化查询语句
   - 添加缓存

2. **后端：错误处理**
   - 完善异常处理
   - 添加详细的错误日志
   - 返回有意义的错误信息

3. **前端：错误处理**
   - 完善 API 错误处理
   - 添加用户友好的错误提示
   - 添加重试机制

4. **测试**：
   - 性能测试
   - 错误场景测试

**交付物**：
- ✅ 性能优化
- ✅ 错误处理完善
- ✅ 性能测试

---

#### Day 5：集成测试和文档

**目标**：完整的集成测试和文档

**任务清单**：

1. **集成测试**
   - 完整流程测试：设计 → 发布 → 提交 → 审批 → 完成
   - 条件分支测试
   - 驳回流程测试
   - 撤回流程测试

2. **文档**
   - API 文档
   - 前端组件文档
   - 使用指南
   - 故障排查指南

3. **部署**
   - 数据库迁移
   - 代码部署
   - 功能验证

**交付物**：
- ✅ 集成测试
- ✅ 完整文档
- ✅ 部署清单

---

## 📊 第二阶段总结

**完成内容**：
- ✅ 流程设计器 UI
- ✅ 查询接口（待办、已办、我发起的、时间线）
- ✅ 条件评估器完善
- ✅ 性能优化和错误处理
- ✅ 集成测试和文档

**工作量**：10-12 个工作日

**交付物**：
- 前端：1 个设计器、4 个页面、多个组件
- 后端：4 个 API 端点、完善的条件评估器
- 测试：集成测试、性能测试
- 文档：API 文档、使用指南

**验收标准**：
- ✅ 流程设计器可正常使用
- ✅ 所有查询接口正常工作
- ✅ 条件评估器支持所有运算符
- ✅ 系统性能满足要求
- ✅ 错误处理完善
- ✅ 文档完整

---

## 🎯 总体时间表

| 阶段 | 周次 | 工作量 | 主要任务 |
|------|------|--------|--------|
| P0 | 1-2 | 10-12d | 条件格式、CONDITION、驳回、审批 API |
| P1 | 3-4 | 10-12d | 设计器 UI、查询接口、评估器完善 |
| P2 | 5-6 | 5-7d | CC 节点、状态统一、优化 |

**总计**：约 25-31 个工作日（5-6 周）

