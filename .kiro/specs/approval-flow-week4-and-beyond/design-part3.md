# 第六周及之后：系统集成与扩展

## 四、第六周及之后：系统集成与扩展

### 4.1 高级审批功能

#### 4.1.1 并行审批优化

```python
# 后端：backend/app/services/parallel_runtime_service.py 扩展

class ParallelRuntimeService:
    """并行审批运行时服务 - 优化版本"""
    
    async def execute_parallel_approvals(
        self,
        instance_id: int,
        node_id: int,
        db: Session = None
    ) -> List[Task]:
        """执行并行审批"""
        # 1. 获取节点配置
        node = await db.get(FlowNode, node_id)
        
        # 2. 解析审批人
        assignees = await self.assignment_service.select_assignees(
            node.assignee_type,
            node.assignee_value,
            db
        )
        
        # 3. 创建并行任务
        tasks = []
        for assignee in assignees:
            task = Task(
                process_instance_id=instance_id,
                flow_node_id=node_id,
                assignee_id=assignee.id,
                status='PENDING',
                created_at=datetime.utcnow()
            )
            tasks.append(task)
        
        db.add_all(tasks)
        await db.commit()
        
        return tasks
    
    async def check_parallel_completion(
        self,
        instance_id: int,
        node_id: int,
        strategy: str = 'any',  # any/all/percent
        db: Session = None
    ) -> bool:
        """检查并行审批完成情况"""
        # 获取该节点的所有任务
        tasks = await db.execute(
            select(Task).where(
                Task.process_instance_id == instance_id,
                Task.flow_node_id == node_id
            )
        )
        tasks = tasks.scalars().all()
        
        completed = sum(1 for t in tasks if t.status in ['APPROVED', 'REJECTED'])
        total = len(tasks)
        
        if strategy == 'any':
            return completed > 0
        elif strategy == 'all':
            return completed == total
        elif strategy == 'percent':
            # 假设 50% 通过即可
            return completed / total >= 0.5
        
        return False
```

**工作量**：2 天

---

#### 4.1.2 委托审批

```python
# 后端：backend/app/models/workflow.py 扩展

class TaskDelegation(DBBaseModel):
    """任务委托"""
    id: int
    task_id: int
    delegated_from_id: int  # 原审批人
    delegated_to_id: int    # 委托人
    
    reason: str = None
    start_date: datetime
    end_date: datetime = None
    
    status: str = 'ACTIVE'  # ACTIVE/EXPIRED/REVOKED
    created_at: datetime
    revoked_at: datetime = None

# 后端：backend/app/api/v1/approvals.py 扩展

@router.post("/tasks/{task_id}/delegate")
async def delegate_task(
    task_id: int,
    request: DelegateTaskRequest,
    db: Session = Depends(get_db)
) -> TaskResponse:
    """委托任务给其他人"""
    pass

@router.post("/tasks/{task_id}/revoke-delegation")
async def revoke_delegation(
    task_id: int,
    db: Session = Depends(get_db)
) -> TaskResponse:
    """撤销委托"""
    pass
```

**工作量**：2 天

---

#### 4.1.3 加签/减签

```python
# 后端：backend/app/models/workflow.py 扩展

class TaskModification(DBBaseModel):
    """任务修改记录"""
    id: int
    task_id: int
    modification_type: str  # ADD_APPROVER/REMOVE_APPROVER
    
    modified_by_id: int
    target_user_id: int
    
    reason: str = None
    created_at: datetime

# 后端：backend/app/api/v1/approvals.py 扩展

@router.post("/tasks/{task_id}/add-approver")
async def add_approver(
    task_id: int,
    request: AddApproverRequest,
    db: Session = Depends(get_db)
) -> TaskResponse:
    """加签：添加审批人"""
    pass

@router.post("/tasks/{task_id}/remove-approver")
async def remove_approver(
    task_id: int,
    request: RemoveApproverRequest,
    db: Session = Depends(get_db)
) -> TaskResponse:
    """减签：移除审批人"""
    pass
```

**工作量**：2 天

---

### 4.2 数据分析与报表

#### 4.2.1 流程统计 API

```python
# 后端：backend/app/api/v1/analytics.py

@router.get("/analytics/flows/statistics")
async def get_flow_statistics(
    flow_id: int = None,
    start_date: datetime = None,
    end_date: datetime = None,
    db: Session = Depends(get_db)
) -> FlowStatistics:
    """获取流程统计数据"""
    pass

@router.get("/analytics/flows/performance")
async def get_flow_performance(
    flow_id: int,
    metric: str = 'avg_duration',  # avg_duration/approval_rate/rejection_rate
    db: Session = Depends(get_db)
) -> PerformanceMetrics:
    """获取流程性能指标"""
    pass

@router.get("/analytics/flows/trend")
async def get_flow_trend(
    flow_id: int,
    period: str = 'daily',  # daily/weekly/monthly
    db: Session = Depends(get_db)
) -> List[TrendData]:
    """获取流程趋势数据"""
    pass
```

**工作量**：2 天

---

#### 4.2.2 用户统计 API

```python
# 后端：backend/app/api/v1/analytics.py

@router.get("/analytics/users/workload")
async def get_user_workload(
    user_id: int = None,
    start_date: datetime = None,
    end_date: datetime = None,
    db: Session = Depends(get_db)
) -> UserWorkload:
    """获取用户工作量统计"""
    pass

@router.get("/analytics/users/performance")
async def get_user_performance(
    user_id: int,
    metric: str = 'avg_approval_time',
    db: Session = Depends(get_db)
) -> UserPerformance:
    """获取用户性能指标"""
    pass

@router.get("/analytics/users/ranking")
async def get_user_ranking(
    metric: str = 'approval_count',
    limit: int = 10,
    db: Session = Depends(get_db)
) -> List[UserRanking]:
    """获取用户排名"""
    pass
```

**工作量**：2 天

---

#### 4.2.3 报表生成

```python
# 后端：backend/app/services/report_service.py

class ReportService:
    """报表生成服务"""
    
    async def generate_flow_report(
        self,
        flow_id: int,
        report_type: str = 'summary',  # summary/detailed/trend
        format: str = 'pdf',  # pdf/excel/html
        db: Session = None
    ) -> bytes:
        """生成流程报表"""
        # 1. 收集数据
        # 2. 生成报表
        # 3. 返回文件
        pass
    
    async def generate_user_report(
        self,
        user_id: int,
        report_type: str = 'workload',
        format: str = 'pdf',
        db: Session = None
    ) -> bytes:
        """生成用户报表"""
        pass
    
    async def schedule_report_generation(
        self,
        report_config: ReportConfig,
        schedule: str = 'daily',  # daily/weekly/monthly
        db: Session = None
    ) -> ScheduledReport:
        """定时生成报表"""
        pass
```

**工作量**：3 天

---

### 4.3 系统集成

#### 4.3.1 第三方系统集成

```python
# 后端：backend/app/services/integration_service.py

class IntegrationService:
    """第三方系统集成服务"""
    
    async def send_to_external_system(
        self,
        instance_id: int,
        system_type: str,  # dingtalk/wechat/email/webhook
        config: dict,
        db: Session = None
    ) -> bool:
        """发送数据到外部系统"""
        instance = await db.get(ProcessInstance, instance_id)
        
        if system_type == 'dingtalk':
            return await self._send_to_dingtalk(instance, config)
        elif system_type == 'wechat':
            return await self._send_to_wechat(instance, config)
        elif system_type == 'email':
            return await self._send_email(instance, config)
        elif system_type == 'webhook':
            return await self._send_webhook(instance, config)
    
    async def _send_to_dingtalk(
        self,
        instance: ProcessInstance,
        config: dict
    ) -> bool:
        """发送到钉钉"""
        # 调用钉钉 API
        pass
    
    async def _send_to_wechat(
        self,
        instance: ProcessInstance,
        config: dict
    ) -> bool:
        """发送到企业微信"""
        # 调用企业微信 API
        pass
    
    async def _send_email(
        self,
        instance: ProcessInstance,
        config: dict
    ) -> bool:
        """发送邮件"""
        # 调用邮件服务
        pass
    
    async def _send_webhook(
        self,
        instance: ProcessInstance,
        config: dict
    ) -> bool:
        """发送 Webhook"""
        # 调用 Webhook
        pass
```

**工作量**：3-4 天

---

#### 4.3.2 Webhook 支持

```python
# 后端：backend/app/models/workflow.py 扩展

class WebhookConfig(DBBaseModel):
    """Webhook 配置"""
    id: int
    flow_definition_id: int
    
    url: str
    event_type: str  # instance_created/task_created/task_completed/instance_completed
    
    headers: dict = None
    retry_count: int = 3
    timeout_seconds: int = 30
    
    is_active: bool = True
    created_at: datetime

# 后端：backend/app/api/v1/webhooks.py

@router.post("/webhooks")
async def create_webhook(
    request: CreateWebhookRequest,
    db: Session = Depends(get_db)
) -> WebhookConfigResponse:
    """创建 Webhook"""
    pass

@router.get("/webhooks/{webhook_id}/logs")
async def get_webhook_logs(
    webhook_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> List[WebhookLogResponse]:
    """获取 Webhook 日志"""
    pass
```

**工作量**：2 天

---

### 4.4 用户体验增强

#### 4.4.1 流程搜索

```python
# 后端：backend/app/api/v1/flows.py 扩展

@router.get("/flows/search")
async def search_flows(
    q: str,
    category: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> List[FlowDefinitionResponse]:
    """搜索流程"""
    # 使用全文搜索或模糊匹配
    pass
```

**工作量**：1 天

---

#### 4.4.2 流程推荐

```python
# 后端：backend/app/services/recommendation_service.py

class RecommendationService:
    """推荐服务"""
    
    async def get_recommended_flows(
        self,
        user_id: int,
        limit: int = 5,
        db: Session = None
    ) -> List[FlowDefinition]:
        """获取推荐流程"""
        # 基于用户历史和热度推荐
        pass
    
    async def get_similar_flows(
        self,
        flow_id: int,
        limit: int = 5,
        db: Session = None
    ) -> List[FlowDefinition]:
        """获取相似流程"""
        # 基于流程结构和标签推荐
        pass
```

**工作量**：2 天

---

#### 4.4.3 快捷操作

```typescript
// 前端：my-app/src/components/flow-designer/QuickActions.vue

interface QuickAction {
  id: string
  name: string
  icon: string
  action: () => void
  shortcut?: string
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'save',
    name: '保存',
    icon: 'save',
    action: () => saveFlow(),
    shortcut: 'Ctrl+S'
  },
  {
    id: 'publish',
    name: '发布',
    icon: 'publish',
    action: () => publishFlow(),
    shortcut: 'Ctrl+P'
  },
  {
    id: 'preview',
    name: '预览',
    icon: 'preview',
    action: () => previewFlow(),
    shortcut: 'Ctrl+Shift+P'
  },
  {
    id: 'export',
    name: '导出',
    icon: 'download',
    action: () => exportFlow(),
    shortcut: 'Ctrl+E'
  }
]
```

**工作量**：1 天

---

### 4.5 第六周及之后工作量总结

| 功能 | 工作量 | 优先级 | 周期 |
|------|--------|--------|------|
| 并行审批优化 | 2d | P1 | W6 |
| 委托审批 | 2d | P2 | W6 |
| 加签/减签 | 2d | P2 | W6 |
| 流程统计 API | 2d | P1 | W6 |
| 用户统计 API | 2d | P1 | W6 |
| 报表生成 | 3d | P2 | W7 |
| 第三方集成 | 3-4d | P2 | W7 |
| Webhook 支持 | 2d | P2 | W7 |
| 流程搜索 | 1d | P2 | W7 |
| 流程推荐 | 2d | P3 | W8 |
| 快捷操作 | 1d | P3 | W8 |
| **总计** | **22-24d** | - | **W6-W8** |

---

