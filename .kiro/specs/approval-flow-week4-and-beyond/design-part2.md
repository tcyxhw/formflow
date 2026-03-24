# 第五周：性能优化与监控完善

## 三、第五周：性能优化与监控完善

### 3.1 数据库性能优化

#### 3.1.1 索引优化

```sql
-- 后端：backend/alembic/versions/XXX_add_performance_indexes.py

-- 流程实例查询索引
CREATE INDEX idx_process_instance_tenant_status 
ON process_instance(tenant_id, status);

CREATE INDEX idx_process_instance_created_at 
ON process_instance(created_at DESC);

-- 任务查询索引
CREATE INDEX idx_task_assignee_status 
ON task(assignee_id, status);

CREATE INDEX idx_task_created_at 
ON task(created_at DESC);

-- 操作日志查询索引
CREATE INDEX idx_workflow_operation_log_instance 
ON workflow_operation_log(process_instance_id);

CREATE INDEX idx_workflow_operation_log_created_at 
ON workflow_operation_log(created_at DESC);

-- 条件评估缓存
CREATE INDEX idx_flow_node_type 
ON flow_node(flow_definition_id, type);
```

**工作量**：1 天

---

#### 3.1.2 查询优化

```python
# 后端：backend/app/services/process_service.py 优化

class ProcessService:
    """流程服务 - 查询优化"""
    
    async def get_pending_tasks_optimized(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        db: Session = None
    ) -> List[Task]:
        """获取待办任务 - 优化版本"""
        # 使用 select 而不是 query
        stmt = (
            select(Task)
            .where(Task.assignee_id == user_id)
            .where(Task.status == 'PENDING')
            .options(
                joinedload(Task.process_instance),
                joinedload(Task.flow_node)
            )
            .order_by(Task.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return db.execute(stmt).scalars().all()
    
    async def get_instance_timeline_optimized(
        self,
        instance_id: int,
        db: Session = None
    ) -> List[WorkflowOperationLog]:
        """获取流程时间线 - 优化版本"""
        # 使用单次查询而不是多次查询
        stmt = (
            select(WorkflowOperationLog)
            .where(WorkflowOperationLog.process_instance_id == instance_id)
            .order_by(WorkflowOperationLog.created_at.asc())
        )
        return db.execute(stmt).scalars().all()
```

**工作量**：2 天

---

### 3.2 缓存策略

#### 3.2.1 流程定义缓存

```python
# 后端：backend/app/services/cache_service.py 扩展

class CacheService:
    """缓存服务"""
    
    FLOW_DEFINITION_TTL = 3600  # 1 小时
    FLOW_VERSION_TTL = 3600
    TEMPLATE_TTL = 7200  # 2 小时
    
    async def get_flow_definition_cached(
        self,
        flow_id: int,
        db: Session = None
    ) -> FlowDefinition:
        """获取流程定义（带缓存）"""
        cache_key = f"flow:definition:{flow_id}"
        
        # 尝试从缓存获取
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # 从数据库获取
        flow = await db.get(FlowDefinition, flow_id)
        
        # 存入缓存
        await self.redis_client.setex(
            cache_key,
            self.FLOW_DEFINITION_TTL,
            json.dumps(flow.dict())
        )
        
        return flow
    
    async def invalidate_flow_cache(self, flow_id: int):
        """清除流程缓存"""
        cache_key = f"flow:definition:{flow_id}"
        await self.redis_client.delete(cache_key)
    
    async def get_condition_evaluation_cached(
        self,
        condition_key: str,
        form_data: dict
    ) -> bool:
        """获取条件评估结果（带缓存）"""
        cache_key = f"condition:eval:{condition_key}:{hash(str(form_data))}"
        
        cached = await self.redis_client.get(cache_key)
        if cached is not None:
            return cached == "true"
        
        # 评估条件
        evaluator = ConditionEvaluatorV2()
        result = evaluator.evaluate(condition_key, form_data)
        
        # 缓存结果（5 分钟）
        await self.redis_client.setex(
            cache_key,
            300,
            "true" if result else "false"
        )
        
        return result
```

**工作量**：2 天

---

#### 3.2.2 查询结果缓存

```python
# 后端：backend/app/services/approval_service.py 扩展

class ApprovalService:
    """审批服务 - 查询缓存"""
    
    async def list_pending_tasks_cached(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        db: Session = None
    ) -> List[Task]:
        """获取待办任务（带缓存）"""
        # 缓存键包含分页信息
        cache_key = f"pending:tasks:{user_id}:{skip}:{limit}"
        
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # 从数据库查询
        tasks = await self.get_pending_tasks_optimized(
            user_id, skip, limit, db
        )
        
        # 缓存 10 分钟
        await self.redis_client.setex(
            cache_key,
            600,
            json.dumps([t.dict() for t in tasks])
        )
        
        return tasks
    
    async def invalidate_user_task_cache(self, user_id: int):
        """清除用户任务缓存"""
        # 使用 SCAN 清除所有相关缓存
        pattern = f"pending:tasks:{user_id}:*"
        cursor = 0
        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern)
            if keys:
                await self.redis_client.delete(*keys)
            if cursor == 0:
                break
```

**工作量**：1 天

---

### 3.3 监控与日志完善

#### 3.3.1 性能监控

```python
# 后端：backend/app/services/monitor_service.py

class MonitorService:
    """监控服务"""
    
    async def record_operation_metrics(
        self,
        operation_type: str,
        duration_ms: float,
        success: bool,
        metadata: dict = None
    ):
        """记录操作指标"""
        metric = {
            'operation_type': operation_type,
            'duration_ms': duration_ms,
            'success': success,
            'timestamp': datetime.utcnow(),
            'metadata': metadata or {}
        }
        
        # 存储到时间序列数据库或 Redis
        await self.store_metric(metric)
    
    async def get_performance_stats(
        self,
        operation_type: str,
        time_range: str = '1h'  # 1h, 1d, 7d
    ) -> PerformanceStats:
        """获取性能统计"""
        # 查询指标数据
        metrics = await self.query_metrics(operation_type, time_range)
        
        # 计算统计数据
        return {
            'avg_duration': statistics.mean([m['duration_ms'] for m in metrics]),
            'max_duration': max([m['duration_ms'] for m in metrics]),
            'min_duration': min([m['duration_ms'] for m in metrics]),
            'success_rate': sum(1 for m in metrics if m['success']) / len(metrics),
            'total_count': len(metrics)
        }
```

**工作量**：2 天

---

#### 3.3.2 操作日志完善

```python
# 后端：backend/app/models/workflow.py 扩展

class WorkflowOperationLog(DBBaseModel):
    """工作流操作日志 - 扩展"""
    id: int
    process_instance_id: int
    task_id: int = None
    
    # 操作信息
    operation_type: str  # SUBMIT/APPROVE/REJECT/CANCEL/REASSIGN
    operator_id: int
    operator_name: str
    
    # 操作详情
    comment: str = None
    old_status: str = None
    new_status: str = None
    
    # 性能指标
    duration_ms: float = None  # 操作耗时
    
    # 审计信息
    ip_address: str = None
    user_agent: str = None
    
    created_at: datetime
```

**工作量**：1 天

---

#### 3.3.3 日志聚合

```python
# 后端：backend/app/core/logger.py 扩展

import logging
from pythonjsonlogger import jsonlogger

class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
        # JSON 格式化
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_operation(
        self,
        operation_type: str,
        status: str,
        duration_ms: float,
        metadata: dict = None
    ):
        """记录操作日志"""
        self.logger.info(
            "operation_executed",
            extra={
                'operation_type': operation_type,
                'status': status,
                'duration_ms': duration_ms,
                'metadata': metadata or {}
            }
        )
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        context: dict = None
    ):
        """记录错误日志"""
        self.logger.error(
            "error_occurred",
            extra={
                'error_type': error_type,
                'error_message': error_message,
                'context': context or {}
            }
        )
```

**工作量**：1 天

---

### 3.4 第五周工作量总结

| 功能 | 工作量 | 优先级 |
|------|--------|--------|
| 数据库索引优化 | 1d | P0 |
| 查询优化 | 2d | P0 |
| 流程定义缓存 | 2d | P1 |
| 查询结果缓存 | 1d | P1 |
| 性能监控 | 2d | P1 |
| 操作日志完善 | 1d | P1 |
| 日志聚合 | 1d | P1 |
| **第五周总计** | **10-11d** | - |

---

