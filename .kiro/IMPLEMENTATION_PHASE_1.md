# 审批流程优化 - 第一阶段实施计划（P0 优先级）

## 📅 时间表：第 1-2 周

### 第 1 周：条件格式统一 + CONDITION 节点

#### Day 1-2：条件表达式格式统一

**目标**：统一前后端条件表达式格式

**任务清单**：

1. **后端：实现新的条件评估器**
   - 文件：`backend/app/services/condition_evaluator_v2.py`
   - 功能：支持设计格式的条件树
   - 代码框架：
   ```python
   class ConditionEvaluatorV2:
       @staticmethod
       def evaluate(condition: Dict, data: Dict) -> bool:
           """评估设计格式的条件树"""
           if not condition:
               return True
           
           if condition.get('type') == 'RULE':
               return ConditionEvaluatorV2._evaluate_rule(condition, data)
           elif condition.get('type') == 'GROUP':
               return ConditionEvaluatorV2._evaluate_group(condition, data)
           
           return False
       
       @staticmethod
       def _evaluate_rule(rule: Dict, data: Dict) -> bool:
           """评估单条规则"""
           field_key = rule.get('fieldKey')
           operator = rule.get('operator')
           value = rule.get('value')
           
           actual = data.get(field_key)
           return ConditionEvaluatorV2._compare(actual, operator, value, rule.get('fieldType'))
       
       @staticmethod
       def _evaluate_group(group: Dict, data: Dict) -> bool:
           """评估条件组"""
           logic = group.get('logic', 'AND').upper()
           children = group.get('children', [])
           
           results = [
               ConditionEvaluatorV2.evaluate(child, data)
               for child in children
           ]
           
           if logic == 'AND':
               return all(results)
           elif logic == 'OR':
               return any(results)
           
           return False
       
       @staticmethod
       def _compare(actual, operator, expected, field_type):
           """比较操作"""
           # 实现所有 15 种运算符
           pass
   ```

2. **后端：添加转换层（JsonLogic → 设计格式）**
   - 文件：`backend/app/services/condition_converter.py`
   - 功能：将现有 JsonLogic 条件转换为设计格式
   - 用于数据迁移

3. **后端：更新 RouteEvaluator**
   - 使用新的 ConditionEvaluatorV2
   - 保持 API 兼容性

4. **前端：保持不变**
   - 条件构造器已经生成设计格式
   - 无需修改

5. **测试**：
   - 单元测试：所有运算符
   - 集成测试：条件评估
   - 数据迁移测试

**交付物**：
- ✅ ConditionEvaluatorV2 类
- ✅ ConditionConverter 类
- ✅ 单元测试
- ✅ 迁移脚本

---

#### Day 3-4：CONDITION 节点实现

**目标**：实现条件分支节点

**任务清单**：

1. **后端：数据库变更**
   - 文件：`backend/alembic/versions/008_add_condition_node_support.py`
   - 变更：
   ```python
   # 在 FlowNode 中添加字段
   condition_branches = Column(JSON, nullable=True, comment="条件分支配置")
   
   # 格式：
   # {
   #   "branches": [
   #     {
   #       "priority": 1,
   #       "label": "大额招待费",
   #       "condition": { "type": "GROUP", ... },
   #       "target_node_id": 123
   #     }
   #   ],
   #   "default_target_node_id": 456
   # }
   ```

2. **后端：流程推进逻辑**
   - 文件：`backend/app/services/process_service.py`
   - 方法：`_dispatch_nodes()` 中添加 CONDITION 处理
   ```python
   if node.type == 'condition':
       branches = node.condition_branches.get('branches', [])
       branches.sort(key=lambda b: b['priority'])
       
       for branch in branches:
           condition = branch['condition']
           if ConditionEvaluatorV2.evaluate(condition, context):
               target_node_id = branch['target_node_id']
               target_node = db.query(FlowNode).filter(FlowNode.id == target_node_id).first()
               return ProcessService._dispatch_nodes([target_node], ...)
       
       # 所有分支都不匹配，走默认路由
       default_target_id = node.condition_branches.get('default_target_node_id')
       # ...
   ```

3. **后端：流程校验**
   - 文件：`backend/app/services/flow_service.py`
   - 方法：添加 `_validate_condition_node_config()`
   ```python
   @staticmethod
   def _validate_condition_node_config(nodes: List[Dict]) -> None:
       """校验 CONDITION 节点配置"""
       for node in nodes:
           if node.get('type') == 'condition':
               branches = node.get('condition_branches', {}).get('branches', [])
               if len(branches) < 2:
                   raise BusinessError(f"{node['name']} 必须至少有 2 条分支")
               
               for branch in branches:
                   condition = branch.get('condition')
                   if not condition:
                       raise BusinessError(f"{node['name']} 的分支 {branch['label']} 缺少条件")
   ```

4. **前端：类型定义更新**
   - 文件：`my-app/src/types/flow.ts`
   - 更新 `FlowNodeConfig` 接口
   ```typescript
   export interface FlowNodeConfig {
     // 现有字段...
     
     // 新增：条件分支（仅 CONDITION 节点使用）
     condition_branches?: {
       branches: Array<{
         priority: number
         label: string
         condition: ConditionNode
         target_node_key: string
       }>
       default_target_node_key: string
     }
   }
   ```

5. **前端：条件节点编辑器**
   - 文件：`my-app/src/components/flow-configurator/ConditionNodeEditor.vue`
   - 功能：编辑条件分支
   - 包含：分支列表、条件编辑、优先级排序、默认路由

6. **测试**：
   - 单元测试：条件分支逻辑
   - 集成测试：完整流程
   - 端到端测试：设计 → 发布 → 执行

**交付物**：
- ✅ 数据库迁移脚本
- ✅ 后端逻辑实现
- ✅ 前端类型定义
- ✅ 前端编辑器组件
- ✅ 单元测试
- ✅ 集成测试

---

#### Day 5：表单字段 API

**目标**：实现表单字段查询接口

**任务清单**：

1. **后端：实现 API 端点**
   - 文件：`backend/app/api/v1/forms.py`
   - 端点：`GET /api/v1/forms/{form_id}/fields`
   ```python
   @router.get("/{form_id}/fields", summary="获取表单字段列表")
   async def get_form_fields(
       form_id: int,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       """获取表单字段列表，用于条件构造器"""
       form = db.query(Form).filter(Form.id == form_id).first()
       form_version = db.query(FormVersion).filter(
           FormVersion.form_id == form_id
       ).order_by(FormVersion.version.desc()).first()
       
       fields = []
       for field_def in form_version.fields:
           fields.append({
               'key': field_def['key'],
               'name': field_def['name'],
               'type': field_def['type'],
               'options': field_def.get('options'),
               'isSystem': False
           })
       
       # 添加系统字段
       system_fields = [
           {'key': 'sys_submitter', 'name': '提交人', 'type': 'USER', 'isSystem': True},
           {'key': 'sys_submitter_dept', 'name': '提交人部门', 'type': 'DEPARTMENT', 'isSystem': True},
           {'key': 'sys_submit_time', 'name': '提交时间', 'type': 'DATETIME', 'isSystem': True}
       ]
       fields.extend(system_fields)
       
       return success_response(data=fields)
   ```

2. **前端：API 接口**
   - 文件：`my-app/src/api/form.ts`
   - 函数：`getFormFields()`

3. **前端：条件构造器集成**
   - 在条件构造器中调用 API 获取字段列表
   - 用于字段选择下拉框

4. **测试**：
   - 单元测试：字段解析
   - 集成测试：API 调用

**交付物**：
- ✅ 后端 API 端点
- ✅ 前端 API 接口
- ✅ 集成测试

---

### 第 2 周：驳回策略 + 审批操作 API

#### Day 1-2：驳回策略实现

**目标**：实现审批驳回策略

**任务清单**：

1. **后端：数据库变更**
   - 文件：`backend/alembic/versions/009_add_reject_strategy.py`
   - 变更：
   ```python
   # 在 FlowNode 中添加字段
   reject_strategy = Column(
       String(20),
       default='TO_START',
       comment="驳回策略：TO_START/TO_PREVIOUS"
   )
   ```

2. **后端：驳回处理逻辑**
   - 文件：`backend/app/services/approval_service.py`
   - 方法：`_handle_rejection()`
   ```python
   @staticmethod
   def _handle_rejection(task: Task, process: ProcessInstance, db: Session):
       """处理任务驳回"""
       node = task.node
       
       if node.reject_strategy == 'TO_START':
           # 驳回到发起人
           process.state = 'rejected'
           # 通知发起人
       elif node.reject_strategy == 'TO_PREVIOUS':
           # 驳回到上一个审批节点
           previous_node = ApprovalService._find_previous_approval_node(process, node, db)
           if previous_node:
               # 重新派发任务
               ProcessService._create_task_for_node(process, previous_node, ...)
           else:
               # 找不到上一个节点，按 TO_START 处理
               process.state = 'rejected'
   ```

3. **前端：类型定义**
   - 文件：`my-app/src/types/flow.ts`
   - 添加 `RejectStrategy` 类型

4. **前端：审批节点编辑器**
   - 在节点编辑器中添加驳回策略选择

5. **测试**：
   - 单元测试：驳回逻辑
   - 集成测试：完整驳回流程

**交付物**：
- ✅ 数据库迁移脚本
- ✅ 后端驳回处理逻辑
- ✅ 前端类型定义
- ✅ 前端 UI 组件
- ✅ 单元测试

---

#### Day 3-5：审批操作 API

**目标**：实现审批、驳回、撤回 API

**任务清单**：

1. **后端：新增 API 路由**
   - 文件：`backend/app/api/v1/approvals.py`
   - 端点：
   ```python
   @router.post("/tasks/{task_id}/approve", summary="审批通过")
   async def approve_task(
       task_id: int,
       request: ApproveTaskRequest,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       """审批通过"""
       task = db.query(Task).filter(Task.id == task_id).first()
       
       # 权限检查
       if task.assignee_user_id != current_user.id:
           raise AuthorizationError("无权操作此任务")
       
       # 更新任务
       task.status = 'approved'
       task.action = 'approve'
       task.comment = request.comment
       task.completed_by = current_user.id
       task.completed_at = datetime.now()
       
       # 继续推进流程
       process = task.process_instance
       node = task.node
       ProcessService.advance_from_node(process, node, ...)
       
       db.commit()
       return success_response(message="已通过")
   
   @router.post("/tasks/{task_id}/reject", summary="审批驳回")
   async def reject_task(
       task_id: int,
       request: RejectTaskRequest,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       """审批驳回"""
       task = db.query(Task).filter(Task.id == task_id).first()
       
       # 权限检查
       if task.assignee_user_id != current_user.id:
           raise AuthorizationError("无权操作此任务")
       
       # 更新任务
       task.status = 'rejected'
       task.action = 'reject'
       task.comment = request.comment
       task.completed_by = current_user.id
       task.completed_at = datetime.now()
       
       # 处理驳回
       ApprovalService._handle_rejection(task, task.process_instance, db)
       
       db.commit()
       return success_response(message="已驳回")
   
   @router.post("/instances/{instance_id}/cancel", summary="撤回申请")
   async def cancel_instance(
       instance_id: int,
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       """发起人撤回"""
       process = db.query(ProcessInstance).filter(ProcessInstance.id == instance_id).first()
       
       # 权限检查
       submission = process.submission
       if submission.created_by != current_user.id:
           raise AuthorizationError("只有发起人可以撤回")
       
       # 取消所有待处理任务
       db.query(Task).filter(
           Task.process_instance_id == instance_id,
           Task.status == 'open'
       ).update({'status': 'canceled'})
       
       # 更新流程状态
       process.state = 'canceled'
       
       db.commit()
       return success_response(message="已撤回")
   ```

2. **后端：Pydantic 模型**
   - 文件：`backend/app/schemas/approval_schemas.py`
   ```python
   class ApproveTaskRequest(BaseModel):
       comment: str = Field(..., description="审批意见")
   
   class RejectTaskRequest(BaseModel):
       comment: str = Field(..., description="驳回原因")
   ```

3. **前端：API 接口**
   - 文件：`my-app/src/api/approval.ts`
   ```typescript
   export const approveTask = (taskId: number, comment: string) => {
       return request.post(`/api/v1/approvals/tasks/${taskId}/approve`, { comment })
   }
   
   export const rejectTask = (taskId: number, comment: string) => {
       return request.post(`/api/v1/approvals/tasks/${taskId}/reject`, { comment })
   }
   
   export const cancelInstance = (instanceId: number) => {
       return request.post(`/api/v1/approvals/instances/${instanceId}/cancel`)
   }
   ```

4. **前端：审批页面**
   - 文件：`my-app/src/views/ApprovalDetail.vue`
   - 功能：显示待办任务详情，提供审批/驳回/撤回操作

5. **测试**：
   - 单元测试：权限检查、状态更新
   - 集成测试：完整审批流程
   - 端到端测试：提交 → 审批 → 完成

**交付物**：
- ✅ 后端 API 端点
- ✅ Pydantic 模型
- ✅ 前端 API 接口
- ✅ 前端审批页面
- ✅ 单元测试
- ✅ 集成测试

---

## 📊 第一阶段总结

**完成内容**：
- ✅ 条件表达式格式统一
- ✅ CONDITION 节点实现
- ✅ 驳回策略实现
- ✅ 审批操作 API
- ✅ 表单字段 API

**工作量**：10-12 个工作日

**交付物**：
- 后端：3 个新服务类、2 个数据库迁移、3 个 API 端点
- 前端：2 个新组件、1 个新页面、3 个 API 接口
- 测试：单元测试、集成测试、端到端测试

**验收标准**：
- ✅ 所有单元测试通过
- ✅ 所有集成测试通过
- ✅ 完整流程可正常执行
- ✅ 条件分支正确评估
- ✅ 驳回流程正确处理
- ✅ 审批操作正常工作

