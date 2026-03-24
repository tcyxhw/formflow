# 审批流程优化 - 设计文档

## 一、系统架构

### 1.1 整体架构图

```mermaid
graph TB
    subgraph Frontend["前端层"]
        Designer["流程设计器"]
        ConditionBuilder["条件构造器"]
        ApprovalUI["审批界面"]
        QueryUI["查询界面"]
    end
    
    subgraph Backend["后端层"]
        FlowAPI["流程 API"]
        ApprovalAPI["审批 API"]
        QueryAPI["查询 API"]
        ProcessService["流程服务"]
        ConditionEvaluator["条件评估器"]
        ApprovalService["审批服务"]
    end
    
    subgraph Database["数据层"]
        FlowDef["流程定义"]
        FlowNode["流程节点"]
        ProcessInst["流程实例"]
        Task["任务"]
        TaskLog["任务日志"]
    end
    
    Designer --> FlowAPI
    ConditionBuilder --> FlowAPI
    ApprovalUI --> ApprovalAPI
    QueryUI --> QueryAPI
    
    FlowAPI --> ProcessService
    ApprovalAPI --> ApprovalService
    QueryAPI --> ProcessService
    
    ProcessService --> ConditionEvaluator
    ProcessService --> FlowDef
    ProcessService --> FlowNode
    ProcessService --> ProcessInst
    ProcessService --> Task
    
    ApprovalService --> Task
    ApprovalService --> TaskLog
```

### 1.2 核心流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Designer as 设计器
    participant Backend as 后端
    participant DB as 数据库
    
    User->>Designer: 1. 创建流程
    Designer->>Backend: 2. 保存草稿
    Backend->>DB: 2.1 存储节点和路由
    
    User->>Designer: 3. 配置条件
    Designer->>Backend: 4. 保存条件
    Backend->>DB: 4.1 存储条件表达式
    
    User->>Designer: 5. 发布流程
    Designer->>Backend: 6. 发布请求
    Backend->>Backend: 6.1 校验流程结构
    Backend->>Backend: 6.2 校验条件表达式
    Backend->>DB: 6.3 创建快照
    
    User->>Backend: 7. 提交表单
    Backend->>Backend: 8. 启动流程
    Backend->>Backend: 9. 评估条件
    Backend->>DB: 10. 创建任务
    
    User->>Backend: 11. 审批/驳回
    Backend->>Backend: 12. 处理审批
    Backend->>Backend: 13. 推进流程
    Backend->>DB: 14. 更新状态
```

---

## 二、数据模型

### 2.1 核心表结构

#### FlowNode（流程节点）

```python
class FlowNode(DBBaseModel):
    id: int                          # 主键
    flow_definition_id: int          # 流程定义 ID
    name: str                        # 节点名称
    type: str                        # 节点类型：start/approval/condition/cc/end
    
    # 审批人配置（APPROVAL 节点）
    assignee_type: str               # 审批人类型：user/group/role/department/position/expr
    assignee_value: str              # 审批人值
    
    # 驳回策略（APPROVAL 节点）
    reject_strategy: str = 'TO_START'  # TO_START/TO_PREVIOUS
    
    # 条件分支配置（CONDITION 节点）
    condition_branches: dict = None  # 条件分支配置
    # 格式：{
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
    
    # 其他配置
    sla_hours: int = None            # SLA 时长（小时）
    auto_approve_enabled: bool = False  # 是否启用自动审批
    
    position_x: float = 0            # 画布 X 坐标
    position_y: float = 0            # 画布 Y 坐标
```

#### FlowRoute（流程路由）

```python
class FlowRoute(DBBaseModel):
    id: 