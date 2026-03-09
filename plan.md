### 设计目标概览

- 构建覆盖 **流程定义 → 任务流转 → SLA/升级 → 审计 → 权限控制** 的统一审批能力。
- 在前端提供 **审批控制台、流程配置器、权限管理与审计可视化**。
- 以现有模型/服务为基底扩展，确保与 [Form](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/form.py:13:0-28:77)、[Submission](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/form.py:85:0-102:69)、`AuditLog` 等模块解耦。

---

### 一、后端设计

1. **数据建模**
   - 复用 `FlowDefinition/FlowNode/FlowRoute/ProcessInstance/Task/ParallelRuntime/TaskActionLog` 并补齐字段使用：
     - `FlowNode.approve_policy/route_mode/auto_*` 覆盖顺序审批、条件分支、会签/或签/比例签及自动审批策略。
     - `FlowRoute.condition_json` 存储金额、部门等表达式及 `priority/is_default` 规则，支持条件直达、动态路由与兜底路径。
     - `ParallelRuntime.join_policy/n_required` 记录并行/会签合流触发条件。  
       @backend/app/models/workflow.py#14-171
   - [FormPermission](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/form.py:48:0-60:76) 作为表单访问/填写/导出等动作的授权表，基于 `grant_type`（user/role/department/position）与有效期控制可见性与可操作性。  
     @backend/app/models/form.py#49-140

2. **服务层**
   - **ProcessService**：负责流程实例创建、节点推进、条件路由判断(`RouteEvaluator`)、并行分支管理以及结束态写回。
   - **AssignmentService**：结合 [Task](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/workflow.py:94:0-132:73) 历史完成时长与当前负载（查询 [TaskActionLog](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/workflow.py:135:0-149:35)）计算评分，写入 `Task.assignee_user_id/assignee_group_id`，支持“智能分配 + 小组待办池 + 宽限认领”。
   - **SLAService**（定时任务）：根据 `FlowNode.sla_hours` 计算 `Task.due_at`，超时触发多渠道提醒及升级策略（改派上级、回组池、转值班），并写 [TaskActionLog](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/workflow.py:135:0-149:35)。
   - **PermissionService**：在 [SubmissionService](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/services/submission_service.py:117:0-1014:9) 提交流程前检查 [FormPermission](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/form.py:48:0-60:76) 是否授予 `fill`；在管理端提供 CRUD API。  
     入口如 [SubmissionService.create_submission](cci:1://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/services/submission_service.py:128:4-289:25) 中插入校验逻辑。@backend/app/services/submission_service.py#130-699
   - **AuditService**：沿用 `@audit_log` 装饰器记录所有审批相关 API 的 `before/after` 数据、操作者、IP、UA。  
     @backend/app/utils/audit.py#19-336

3. **API 设计（FastAPI）**
   - 新增 `app/api/v1/approvals.py`：
     1. `GET /tasks`：待办、组待办池列表（支持 SLA 状态、关键词、表单、流程节点过滤）。
     2. `POST /tasks/{id}/claim|release|transfer|delegate|add-sign`：认领、释放、转交个人/小组、加签。
     3. `POST /tasks/{id}/actions`：通过/驳回/撤回，写入 [TaskActionLog](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/workflow.py:135:0-149:35) 并触发流程推进。
     4. `GET /processes/{id}/timeline`：聚合 [ProcessInstance](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/workflow.py:75:0-91:93)、[Task](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/workflow.py:94:0-132:73)、[TaskActionLog](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/workflow.py:135:0-149:35) 输出轨迹。
   - [FormPermission](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/form.py:48:0-60:76) 路由：`GET/POST/PUT/DELETE /forms/{id}/permissions`，配合前端管理授权。
   - [Form](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/form.py:13:0-28:77)/[Submission](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/form.py:85:0-102:69) API 中补充权限校验与流程触发逻辑（发布表单时绑定流程版本、提交时创建 [ProcessInstance](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/workflow.py:75:0-91:93) 等）。  
     参考 [forms.py](cci:7://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/api/v1/forms.py:0:0-0:0) 路由结构进行集成。@backend/app/api/v1/forms.py#28-465

---

### 二、前端设计（Vue 3 + Naive UI）

1. **审批控制台（/approvals）**
   - 将 `ApprovalListView.vue` 从占位升级为多区域布局：
     1. 左侧待办表（表格 + 快速筛选 + SLA 倒计时 + 风险提示）。
     2. “组待办池”标签页：支持认领、释放、宽限时间展示。
     3. 详情抽屉：包含流程轨迹（时间线/流程图）、表单快照、操作历史、审批动作表单。
   - 新建 `src/services/approvalService.ts` 封装任务/流程 API 调用。

2. **权限与表单入口**
   - 在表单填写页进入时请求 `/forms/{id}/permissions/me`：若无 fill 权限则提示无权并隐藏提交按钮。
   - Form 管理页面新增“权限配置”Tab（列表 + 弹窗编辑 `grant_type/grantee/permission/valid_from/to`）。

3. **流程配置器**
   - 在管理端提供“流程定义”页面（可嵌入于 Form Designer 或独立路由），使用流程图组件（如 vue-flow）拖拽节点、连线、配置审批策略/SLA/自动化条件，保存为结构化 JSON，提交给后端生成 `FlowDefinition/FlowNode/FlowRoute`。

4. **审计与轨迹可视化**
   - `SubmissionDetailView` 和审批入口中添加“轨迹”/“审计”Tab，展示 [TaskActionLog](cci:2://file:///c:/Users/Administrator/Desktop/%E9%9D%9E%E4%BD%9C%E4%B8%9A%E6%96%87%E4%BB%B6/%E6%AF%95%E8%AE%BE/formflow/backend/app/models/workflow.py:135:0-149:35)、`AuditLog` 列表，支持导出。
   - 提供筛选工具（时间、用户、动作类型）及一键导出 CSV。