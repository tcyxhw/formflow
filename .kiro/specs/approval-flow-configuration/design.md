# Design Document: Approval Flow Configuration

## Overview

本设计文档定义了审批流程配置功能的技术实现方案。该功能允许表单创建者在表单发布前配置审批流程，通过可视化流程配置器设计流程结构，并在发布前进行严格的拓扑和业务规则校验。

审批流程采用有向图模型，包含四种节点类型（开始、审批、条件、结束）和连线（路由）。系统支持草稿保存和版本快照管理，确保流程配置的可追溯性和安全性。

### Key Features

- 表单创建时自动创建关联的流程定义
- 可视化流程配置器，支持拖拽式节点和连线操作
- 草稿自动保存机制，支持乐观锁版本控制
- 发布前执行9项严格的拓扑和业务规则校验
- 流程快照管理，记录历史版本
- 权限控制，仅表单创建者可配置流程
- 表单发布前强制校验流程已发布

### Technology Stack

- Backend: Python 3.10, FastAPI, SQLAlchemy, PostgreSQL
- Frontend: Vue 3, TypeScript, Naive UI, Pinia
- Graph Algorithms: BFS/DFS for reachability, Tarjan for cycle detection

## Architecture

### System Architecture


```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  Form List          Form Designer        Flow Configurator      │
│  (List.vue)         (Designer.vue)       (Configurator.vue)     │
│      │                   │                       │              │
│      └───────────────────┴───────────────────────┘              │
│                          │                                       │
│                    Router (index.ts)                            │
│                          │                                       │
│                   Pinia Store (flowDraft)                       │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │ HTTP/JSON
┌──────────────────────────┼───────────────────────────────────────┐
│                    Backend API Layer                            │
├─────────────────────────────────────────────────────────────────┤
│   /api/v1/forms/*              /api/v1/flows/*                  │
│   (forms.py)                   (flows.py)                       │
│      │                              │                           │
│      ├─ POST /forms                 ├─ GET /{id}               │
│      ├─ POST /forms/{id}/publish    ├─ GET /{id}/draft         │
│      │                              ├─ PUT /{id}/draft         │
│      │                              └─ POST /{id}/publish      │
└──────┼──────────────────────────────┼───────────────────────────┘
       │                              │
┌──────┼──────────────────────────────┼───────────────────────────┐
│                    Service Layer                                │
├─────────────────────────────────────────────────────────────────┤
│   FormService                    FlowService                    │
│   (form_service.py)              (flow_service.py)              │
│      │                              │                           │
│      ├─ create_form()               ├─ get_definition_detail()  │
│      ├─ publish_form()              ├─ save_draft()            │
│      │                              ├─ publish_flow()          │
│      │                              └─ _validate_*()           │
└──────┼──────────────────────────────┼───────────────────────────┘
       │                              │
┌──────┼──────────────────────────────┼───────────────────────────┐
│                    Data Layer                                   │
├─────────────────────────────────────────────────────────────────┤
│   Form                FlowDefinition    FlowDraft    FlowSnapshot│
│   FormVersion         (workflow.py)                             │
│   (form.py)                                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

#### Flow 1: Form Creation with Auto Flow Definition

```
User → Form List → Create Form
  → FormService.create_form()
    → Create Form record
    → Create FlowDefinition (draft status, empty config)
    → Create FormVersion (v0, draft)
  → Return Form with flow_definition_id
```

#### Flow 2: Flow Configuration

```
User → Form List → Click "配置流程"
  → Navigate to /flow/configurator?id={flow_definition_id}
  → FlowService.get_definition_detail()
    → Load FlowDefinition
    → Load FlowDraft (if exists)
  → Render Flow Configurator
  → User edits nodes/routes
  → Auto-save or Manual save
    → FlowService.save_draft()
      → Validate version (optimistic lock)
      → Update/Create FlowDraft
```


#### Flow 3: Flow Publishing with Validation

```
User → Flow Configurator → Click "发布流程"
  → FlowService.publish_flow()
    → Load FlowDraft
    → Execute 9 validation rules:
      1. validate_single_start_node()
      2. validate_at_least_one_end_node()
      3. validate_at_least_one_approval_node()
      4. validate_non_end_nodes_have_outgoing_edges()
      5. validate_non_start_nodes_have_incoming_edges()
      6. validate_condition_nodes_have_two_branches()
      7. validate_approval_nodes_have_approver_config()
      8. validate_reachability()
      9. validate_no_dead_cycles()
    → If all pass:
      → Create FlowSnapshot
      → Update FlowDefinition.version++
      → Update FlowDefinition.active_snapshot_id
      → Update FlowDefinition.status = 'published'
    → If any fail:
      → Return validation error
```

#### Flow 4: Form Publishing with Flow Check

```
User → Form Designer → Click "发布表单"
  → FormService.publish_form()
    → Load Form
    → Check Form.flow_definition_id exists
    → Load FlowDefinition
    → Validate FlowDefinition.status == 'published'
    → If not published:
      → Return error: "表单发布前必须先配置并发布审批流程"
    → If published:
      → Create FormVersion (v++)
      → Update Form.status = 'published'
```

## Components and Interfaces

### Backend Components

#### 1. FormService Enhancements

**Location**: `backend/app/services/form_service.py`

**New/Modified Methods**:

```python
@staticmethod
def create_form(
    request: FormCreateRequest,
    tenant_id: int,
    user_id: int,
    db: Session
) -> Form:
    """
    创建表单并自动创建关联的流程定义
    
    Modifications:
    - After creating Form, create FlowDefinition
    - Set form.flow_definition_id
    """
    # Existing form creation logic...
    
    # NEW: Create associated FlowDefinition
    flow_definition = FlowDefinition(
        tenant_id=tenant_id,
        form_id=form.id,
        name=f"{form.name} - 审批流程",
        version=0,
        active_snapshot_id=None
    )
    db.add(flow_definition)
    db.flush()
    
    # Link flow to form
    form.flow_definition_id = flow_definition.id
    
    db.commit()
    return form
```


```python
@staticmethod
def publish_form(
    form_id: int,
    tenant_id: int,
    user_id: int,
    db: Session,
    flow_definition_id: Optional[int] = None
) -> FormVersion:
    """
    发布表单，增加流程发布状态校验
    
    Modifications:
    - Add validation for FlowDefinition published status
    """
    form = FormService.get_form_by_id(form_id, tenant_id, db)
    
    # Existing permission check...
    
    # NEW: Validate flow is published
    if form.flow_definition_id:
        flow_def = db.query(FlowDefinition).filter(
            FlowDefinition.id == form.flow_definition_id,
            FlowDefinition.tenant_id == tenant_id
        ).first()
        
        if not flow_def:
            raise ValidationError("关联的流程定义不存在")
        
        if not flow_def.active_snapshot_id:
            raise ValidationError("表单发布前必须先配置并发布审批流程")
    
    # Existing publish logic...
```

#### 2. FlowService Enhancements

**Location**: `backend/app/services/flow_service.py`

**New Validation Methods**:

```python
class FlowService:
    
    @staticmethod
    def publish_flow(
        request: FlowPublishRequest,
        tenant_id: int,
        user_id: int,
        db: Session,
    ) -> FlowSnapshotResponse:
        """
        发布流程，执行完整的校验流程
        
        Enhancements:
        - Add comprehensive validation before publishing
        """
        definition = FlowService._get_flow_definition(
            request.flow_definition_id, tenant_id, db
        )
        draft = FlowService._get_draft_model(definition.id, tenant_id, db)
        
        if not draft:
            raise BusinessError("请先保存草稿后再发布")
        
        if request.version != draft.version:
            raise BusinessError("草稿版本已变更，请刷新后再发布")
        
        config = draft.config_json or {}
        nodes = config.get("nodes", [])
        routes = config.get("routes", [])
        
        # NEW: Execute all validation rules
        FlowService._validate_flow_structure(nodes, routes)
        
        # Existing snapshot creation logic...
    
    @staticmethod
    def _validate_flow_structure(
        nodes: List[Dict[str, Any]], 
        routes: List[Dict[str, Any]]
    ) -> None:
        """
        执行所有流程结构校验
        
        Raises:
            BusinessError: 如果任何校验失败
        """
        FlowService._validate_single_start_node(nodes)
        FlowService._validate_at_least_one_end_node(nodes)
        FlowService._validate_at_least_one_approval_node(nodes)
        FlowService._validate_node_edges(nodes, routes)
        FlowService._validate_condition_node_branches(nodes, routes)
        FlowService._validate_approval_node_config(nodes)
        FlowService._validate_reachability(nodes, routes)
        FlowService._validate_no_dead_cycles(nodes, routes)
```


    @staticmethod
    def _validate_single_start_node(nodes: List[Dict[str, Any]]) -> None:
        """校验有且仅有一个开始节点"""
        start_nodes = [n for n in nodes if n.get("type") == "start"]
        if len(start_nodes) == 0:
            raise BusinessError("流程必须有一个开始节点")
        if len(start_nodes) > 1:
            raise BusinessError("流程只能有一个开始节点")
    
    @staticmethod
    def _validate_at_least_one_end_node(nodes: List[Dict[str, Any]]) -> None:
        """校验至少有一个结束节点"""
        end_nodes = [n for n in nodes if n.get("type") == "end"]
        if len(end_nodes) == 0:
            raise BusinessError("流程必须至少有一个结束节点")
    
    @staticmethod
    def _validate_at_least_one_approval_node(nodes: List[Dict[str, Any]]) -> None:
        """校验至少有一个审批节点"""
        approval_nodes = [n for n in nodes if n.get("type") == "approval"]
        if len(approval_nodes) == 0:
            raise BusinessError("流程必须至少有一个审批节点")
    
    @staticmethod
    def _validate_node_edges(
        nodes: List[Dict[str, Any]], 
        routes: List[Dict[str, Any]]
    ) -> None:
        """校验节点的入边和出边"""
        # Build adjacency lists
        node_ids = {n.get("id") or n.get("temp_id") for n in nodes}
        outgoing = {nid: [] for nid in node_ids}
        incoming = {nid: [] for nid in node_ids}
        
        for route in routes:
            from_id = route.get("from_node_id")
            to_id = route.get("to_node_id")
            if from_id in outgoing:
                outgoing[from_id].append(to_id)
            if to_id in incoming:
                incoming[to_id].append(from_id)
        
        # Check outgoing edges for non-end nodes
        for node in nodes:
            node_id = node.get("id") or node.get("temp_id")
            node_type = node.get("type")
            
            if node_type != "end" and len(outgoing.get(node_id, [])) == 0:
                raise BusinessError(f"节点 {node.get('name', node_id)} 必须有出边")
            
            if node_type != "start" and len(incoming.get(node_id, [])) == 0:
                raise BusinessError(f"节点 {node.get('name', node_id)} 必须有入边")
    
    @staticmethod
    def _validate_condition_node_branches(
        nodes: List[Dict[str, Any]], 
        routes: List[Dict[str, Any]]
    ) -> None:
        """校验条件节点至少有两条分支"""
        node_ids = {n.get("id") or n.get("temp_id") for n in nodes}
        outgoing = {nid: [] for nid in node_ids}
        
        for route in routes:
            from_id = route.get("from_node_id")
            if from_id in outgoing:
                outgoing[from_id].append(route)
        
        for node in nodes:
            if node.get("type") == "condition":
                node_id = node.get("id") or node.get("temp_id")
                if len(outgoing.get(node_id, [])) < 2:
                    raise BusinessError(
                        f"条件节点 {node.get('name', node_id)} 必须至少有两条分支"
                    )
```


    @staticmethod
    def _validate_approval_node_config(nodes: List[Dict[str, Any]]) -> None:
        """校验审批节点配置了审批人"""
        for node in nodes:
            if node.get("type") == "approval":
                config = node.get("config", {})
                approver_type = config.get("approver_type")
                approver_ids = config.get("approver_ids")
                
                if not approver_type or not approver_ids:
                    raise BusinessError(
                        f"审批节点 {node.get('name', node.get('id'))} 必须配置审批人"
                    )
    
    @staticmethod
    def _validate_reachability(
        nodes: List[Dict[str, Any]], 
        routes: List[Dict[str, Any]]
    ) -> None:
        """校验从开始节点可以到达至少一个结束节点 (BFS)"""
        # Find start node
        start_node = next((n for n in nodes if n.get("type") == "start"), None)
        if not start_node:
            return  # Already validated by _validate_single_start_node
        
        start_id = start_node.get("id") or start_node.get("temp_id")
        
        # Find end nodes
        end_node_ids = {
            n.get("id") or n.get("temp_id") 
            for n in nodes if n.get("type") == "end"
        }
        
        # Build adjacency list
        graph = {}
        for node in nodes:
            node_id = node.get("id") or node.get("temp_id")
            graph[node_id] = []
        
        for route in routes:
            from_id = route.get("from_node_id")
            to_id = route.get("to_node_id")
            if from_id in graph:
                graph[from_id].append(to_id)
        
        # BFS to find reachable nodes
        visited = set()
        queue = [start_id]
        visited.add(start_id)
        
        while queue:
            current = queue.pop(0)
            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # Check if any end node is reachable
        reachable_end_nodes = end_node_ids & visited
        if not reachable_end_nodes:
            raise BusinessError("流程不可达：无法从开始节点到达结束节点")
    
    @staticmethod
    def _validate_no_dead_cycles(
        nodes: List[Dict[str, Any]], 
        routes: List[Dict[str, Any]]
    ) -> None:
        """校验不存在死循环 (使用 DFS 检测环)"""
        # Build adjacency list
        graph = {}
        for node in nodes:
            node_id = node.get("id") or node.get("temp_id")
            graph[node_id] = []
        
        for route in routes:
            from_id = route.get("from_node_id")
            to_id = route.get("to_node_id")
            if from_id in graph:
                graph[from_id].append(to_id)
        
        # Get end node IDs
        end_node_ids = {
            n.get("id") or n.get("temp_id") 
            for n in nodes if n.get("type") == "end"
        }
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle_dfs(node_id: str, path: List[str]) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    if has_cycle_dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle, check if it contains an end node
                    cycle_start_idx = path.index(neighbor)
                    cycle_nodes = set(path[cycle_start_idx:])
                    if not (cycle_nodes & end_node_ids):
                        # Cycle without end node = dead loop
                        return True
            
            path.pop()
            rec_stack.remove(node_id)
            return False
        
        for node in nodes:
            node_id = node.get("id") or node.get("temp_id")
            if node_id not in visited:
                if has_cycle_dfs(node_id, []):
                    raise BusinessError("流程存在死循环")
```



### Frontend Components

#### 1. Router Configuration

**Location**: `my-app/src/router/index.ts`

**New Route**:

```typescript
// Add to authRoutes array
{
  path: '/flow',
  name: 'Flow',
  meta: { title: '流程管理' },
  children: [
    {
      path: 'configurator/:id',
      name: 'FlowConfigurator',
      component: () => import('@/views/flow/Configurator.vue'),
      meta: { 
        title: '流程配置器',
        requiresAuth: true 
      }
    }
  ]
}
```

#### 2. Form List Enhancements

**Location**: `my-app/src/views/form/List.vue`

**Modifications**:

```typescript
// Add to columns definition
{
  title: '操作',
  key: 'actions',
  width: 240,  // Increased width
  fixed: 'right',
  render: (row) => {
    return h(
      NSpace,
      {},
      {
        default: () => [
          // NEW: Configure Flow button
          h(
            NButton,
            {
              size: 'small',
              type: 'info',
              disabled: row.status !== FormStatus.DRAFT,
              onClick: () => handleConfigureFlow(row),
            },
            { default: () => '配置流程' }
          ),
          h(
            NButton,
            {
              size: 'small',
              onClick: () => handleEdit(row),
            },
            { default: () => '编辑' }
          ),
          // ... existing buttons
        ],
      }
    )
  },
}

// NEW: Handler function
const handleConfigureFlow = (row: FormResponse) => {
  if (!row.flow_definition_id) {
    message.error('该表单没有关联的流程定义')
    return
  }
  
  router.push({
    path: `/flow/configurator/${row.flow_definition_id}`,
  })
}
```

#### 3. Form Designer Enhancements

**Location**: `my-app/src/components/FormDesigner/index.vue`

**Modifications**:

```typescript
// Add notification after save
const handleSave = async () => {
  try {
    // ... existing save logic
    
    // NEW: Show flow configuration prompt
    if (formData.status === FormStatus.DRAFT) {
      notification.info({
        title: '下一步：配置审批流程',
        content: '表单已保存。发布前需要配置审批流程。',
        action: () =>
          h(
            NButton,
            {
              text: true,
              type: 'primary',
              onClick: () => {
                if (formData.flow_definition_id) {
                  router.push(`/flow/configurator/${formData.flow_definition_id}`)
                }
              }
            },
            { default: () => '立即配置' }
          ),
        duration: 8000
      })
    }
  } catch (error) {
    // ... error handling
  }
}
```



#### 4. Flow Configurator Component

**Location**: `my-app/src/views/flow/Configurator.vue`

**Status**: Already exists and functional

**Key Features**:
- Node palette for dragging nodes (start, approval, condition, end)
- Canvas for visual flow design
- Node inspector for editing node properties
- Route inspector for editing connections
- Auto-save mechanism with configurable delay
- Draft save and publish functionality
- Optimistic locking for concurrent editing

**Required Enhancements**: None (component is complete)

## Data Models

### Database Schema

#### FlowDefinition

```python
class FlowDefinition(DBBaseModel):
    """流程定义表"""
    __tablename__ = "flow_definition"
    
    form_id = Column(Integer, ForeignKey("form.id"), nullable=False)
    version = Column(Integer, nullable=False, default=0)
    name = Column(String(100), nullable=False)
    active_snapshot_id = Column(Integer, ForeignKey("flow_snapshot.id"), nullable=True)
    
    # Relationships
    form = relationship("Form", back_populates="flow_definition")
    drafts = relationship("FlowDraft", back_populates="flow_definition")
    snapshots = relationship("FlowSnapshot", back_populates="flow_definition")
```

#### FlowDraft

```python
class FlowDraft(DBBaseModel):
    """流程草稿表"""
    __tablename__ = "flow_draft"
    
    flow_definition_id = Column(Integer, ForeignKey("flow_definition.id"), nullable=False)
    version = Column(Integer, nullable=False, default=1)  # Optimistic lock
    nodes_graph = Column(JSONB, nullable=True)  # Canvas positions
    config_json = Column(JSONB, nullable=False)  # Nodes and routes
    updated_by = Column(Integer, ForeignKey("user.id"), nullable=True)
    last_snapshot_id = Column(Integer, ForeignKey("flow_snapshot.id"), nullable=True)
```

**config_json Structure**:

```json
{
  "nodes": [
    {
      "id": "node_1",
      "temp_id": "temp_abc123",
      "type": "start|approval|condition|end",
      "name": "节点名称",
      "config": {
        "approver_type": "user|role|position|group",
        "approver_ids": [1, 2, 3],
        "approve_policy": "any|all|percent",
        "condition_expr": "field1 > 100"
      }
    }
  ],
  "routes": [
    {
      "id": "route_1",
      "from_node_id": "node_1",
      "to_node_id": "node_2",
      "condition": "field1 == 'approved'",
      "priority": 1
    }
  ]
}
```

#### FlowSnapshot

```python
class FlowSnapshot(DBBaseModel):
    """流程快照表"""
    __tablename__ = "flow_snapshot"
    
    flow_definition_id = Column(Integer, ForeignKey("flow_definition.id"), nullable=False)
    version_tag = Column(String(50), nullable=False)
    rules_payload = Column(JSONB, nullable=False)  # Immutable config
    metadata_json = Column(JSONB, nullable=True)  # Changelog, etc.
    created_by = Column(Integer, ForeignKey("user.id"), nullable=True)
```

### API Schemas

#### FlowDraftSaveRequest

```python
class FlowDraftSaveRequest(BaseModel):
    flow_definition_id: int
    version: int  # For optimistic locking
    nodes: List[FlowNodeConfig]
    routes: List[FlowRouteConfig]
    nodes_graph: Optional[Dict[str, Any]] = None
```

#### FlowPublishRequest

```python
class FlowPublishRequest(BaseModel):
    flow_definition_id: int
    version: int  # Draft version
    version_tag: Optional[str] = None
    changelog: Optional[str] = None
```

#### FlowNodeConfig

```python
class FlowNodeConfig(BaseModel):
    id: Optional[int] = None
    temp_id: Optional[str] = None
    type: Literal["start", "approval", "condition", "end"]
    name: str
    config: Optional[Dict[str, Any]] = None
```

#### FlowRouteConfig

```python
class FlowRouteConfig(BaseModel):
    id: Optional[int] = None
    from_node_id: str  # Can be temp_id or id
    to_node_id: str
    condition: Optional[str] = None
    priority: int = 0
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

Before defining the final properties, I performed a reflection to eliminate redundancy:

**Redundancy Analysis**:

1. **Validation timing properties (6.4, 7.4, 8.4, 9.4, 10.4, 11.4, 12.4)**: All specify that validation occurs before persistence. This can be combined into a single property about transaction atomicity.

2. **Node counting properties (6.1, 7.1, 8.1)**: These all test node type counting. While they validate different node types, each provides unique validation value and should remain separate.

3. **Edge validation properties (9.1, 10.1)**: These test incoming and outgoing edges. Both are necessary as they validate different aspects of graph connectivity.

4. **Form creation properties (1.1, 1.2, 1.3, 1.4)**: These can be combined into a single comprehensive property about form-flow initialization.

5. **Draft round-trip properties (16.1, 16.2, 16.4)**: These can be combined into a single property about draft persistence and retrieval.

6. **Publishing properties (17.2, 17.3, 17.4)**: These can be combined into a single property about successful publication effects.

**Consolidated Properties**: After reflection, 38 testable criteria reduced to 22 unique properties.



### Backend Properties

#### Property 1: Form Creation Initializes Flow Definition

*For any* form creation request with valid tenant_id and user_id, creating the form should automatically create an associated FlowDefinition with matching form_id, tenant_id, draft status, and empty configuration.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

#### Property 2: Only Form Creator Can Access Flow Configuration

*For any* flow definition and user, attempting to access or modify the flow configuration should succeed only if the user is the form creator (owner_user_id matches).

**Validates: Requirements 5.1, 5.2**

#### Property 3: Tenant Isolation for Flow Access

*For any* flow definition and user from a different tenant, attempting to access the flow configuration should be rejected regardless of user permissions.

**Validates: Requirements 5.4**

#### Property 4: Single Start Node Validation

*For any* flow configuration, publishing should succeed only if exactly one node has type "start".

**Validates: Requirements 6.1**

#### Property 5: At Least One End Node Validation

*For any* flow configuration, publishing should succeed only if at least one node has type "end".

**Validates: Requirements 7.1**

#### Property 6: At Least One Approval Node Validation

*For any* flow configuration, publishing should succeed only if at least one node has type "approval".

**Validates: Requirements 8.1**

#### Property 7: Non-End Nodes Have Outgoing Edges

*For any* flow configuration, publishing should succeed only if every node that is not of type "end" has at least one outgoing route.

**Validates: Requirements 9.1**

#### Property 8: Non-Start Nodes Have Incoming Edges

*For any* flow configuration, publishing should succeed only if every node that is not of type "start" has at least one incoming route.

**Validates: Requirements 10.1**

#### Property 9: Condition Nodes Have Two Branches

*For any* flow configuration, publishing should succeed only if every node of type "condition" has at least two outgoing routes.

**Validates: Requirements 11.1**

#### Property 10: Approval Nodes Have Approver Configuration

*For any* flow configuration, publishing should succeed only if every node of type "approval" has approver_type and approver_ids configured in its config field.

**Validates: Requirements 12.1**



#### Property 11: End Node Reachability

*For any* flow configuration with a start node and at least one end node, publishing should succeed only if at least one end node is reachable from the start node via the defined routes.

**Validates: Requirements 13.2**

#### Property 12: No Dead Cycles

*For any* flow configuration, publishing should succeed only if there are no cycles in the graph that do not include at least one end node.

**Validates: Requirements 14.1**

#### Property 13: Validation Atomicity

*For any* flow configuration that fails any validation rule, the publish operation should not persist any changes to the database (no FlowSnapshot created, no version incremented, no status changed).

**Validates: Requirements 6.4, 7.4, 8.4, 9.4, 10.4, 11.4, 12.4**

#### Property 14: Form Publish Requires Published Flow

*For any* form with an associated flow_definition_id, publishing the form should succeed only if the FlowDefinition has an active_snapshot_id (indicating it has been published).

**Validates: Requirements 15.1**

#### Property 15: Form Publish Atomicity

*For any* form publish attempt that fails flow validation, the form status should remain unchanged and no new FormVersion should be created.

**Validates: Requirements 15.4**

#### Property 16: Draft Save Without Validation

*For any* flow configuration (valid or invalid), saving as a draft should succeed without performing any validation rules, and the draft should store the complete configuration.

**Validates: Requirements 16.3**

#### Property 17: Draft Round-Trip Preservation

*For any* flow configuration saved as a draft, loading the draft should return an equivalent configuration with all nodes, routes, and graph positions preserved.

**Validates: Requirements 16.1, 16.2, 16.4**

#### Property 18: Successful Publish Creates Snapshot

*For any* valid flow configuration that passes all validation rules, publishing should create a FlowSnapshot, increment the FlowDefinition version, update the active_snapshot_id, and preserve the configuration immutably.

**Validates: Requirements 17.2, 17.3, 17.4**

#### Property 19: Version Increment Monotonicity

*For any* flow definition, publishing multiple times should result in strictly increasing version numbers with no gaps or duplicates.

**Validates: Requirements 17.4**



### Frontend Properties

#### Property 20: Flow Configuration Button State

*For any* form in the form list, the "配置流程" button should be enabled if and only if the form status is "draft".

**Validates: Requirements 3.2, 3.3**

#### Property 21: Node Deletion Cascades to Routes

*For any* node in the flow configurator, deleting the node should also remove all routes that have that node as either from_node_id or to_node_id.

**Validates: Requirements 18.3**

#### Property 22: End Nodes Cannot Have Outgoing Routes

*For any* node of type "end" in the flow configurator, attempting to create an outgoing route from that node should be prevented.

**Validates: Requirements 19.4**

## Error Handling

### Validation Error Responses

All validation errors should return structured error responses with:

```python
{
  "code": 4001,  # Business error code
  "message": "具体的错误信息",
  "data": {
    "validation_type": "node_count|edge_validation|reachability|cycle",
    "failed_nodes": ["node_id_1", "node_id_2"],  # If applicable
    "details": "Additional context"
  }
}
```

### Error Categories

1. **Structure Errors** (4001):
   - Missing start node
   - Multiple start nodes
   - No end nodes
   - No approval nodes
   - Missing edges

2. **Configuration Errors** (4001):
   - Approval node without approver
   - Condition node with < 2 branches

3. **Graph Errors** (4001):
   - Unreachable end nodes
   - Dead cycles

4. **Authorization Errors** (4003):
   - Non-creator access attempt
   - Cross-tenant access attempt

5. **Concurrency Errors** (4001):
   - Optimistic lock version mismatch

### Frontend Error Handling

```typescript
try {
  await FlowService.publishFlow(request)
  message.success('流程发布成功')
} catch (error) {
  if (error.response?.data?.code === 4001) {
    const errorData = error.response.data.data
    
    // Show detailed validation error
    dialog.error({
      title: '流程校验失败',
      content: error.response.data.message,
      positiveText: '知道了'
    })
    
    // Highlight failed nodes in canvas
    if (errorData?.failed_nodes) {
      highlightNodes(errorData.failed_nodes)
    }
  } else if (error.response?.data?.code === 4003) {
    message.error('无权限操作')
    router.push('/403')
  } else {
    message.error('发布失败，请稍后重试')
  }
}
```



## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and integration points
- **Property tests**: Verify universal properties across randomized inputs

Both approaches are complementary and necessary. Unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across a wide input space.

### Property-Based Testing

**Library Selection**: 
- Backend: `hypothesis` (Python)
- Frontend: `fast-check` (TypeScript)

**Configuration**:
- Minimum 100 iterations per property test
- Each test must reference its design property in a comment
- Tag format: `# Feature: approval-flow-configuration, Property {number}: {property_text}`

**Example Property Test**:

```python
from hypothesis import given, strategies as st
import pytest

# Feature: approval-flow-configuration, Property 4: Single Start Node Validation
@given(
    nodes=st.lists(
        st.fixed_dictionaries({
            'id': st.integers(min_value=1),
            'type': st.sampled_from(['start', 'approval', 'condition', 'end']),
            'name': st.text(min_size=1, max_size=50),
            'config': st.just({})
        }),
        min_size=1,
        max_size=20
    )
)
@pytest.mark.property_test
def test_single_start_node_validation(nodes):
    """For any flow configuration, publishing should succeed only if exactly one start node exists."""
    
    start_count = sum(1 for n in nodes if n['type'] == 'start')
    routes = []  # Minimal valid routes
    
    if start_count == 1:
        # Should not raise validation error for start node count
        try:
            FlowService._validate_single_start_node(nodes)
        except BusinessError as e:
            if "开始节点" in str(e):
                pytest.fail(f"Should not fail with exactly 1 start node: {e}")
    else:
        # Should raise validation error
        with pytest.raises(BusinessError) as exc_info:
            FlowService._validate_single_start_node(nodes)
        
        assert "开始节点" in str(exc_info.value)
```

### Unit Testing

**Focus Areas**:
1. Specific validation scenarios (0 start nodes, 2 start nodes, etc.)
2. Integration between FormService and FlowService
3. API endpoint authorization checks
4. Frontend component interactions
5. Edge cases (empty graphs, single-node graphs, etc.)

**Example Unit Test**:

```python
def test_form_creation_creates_flow_definition(db_session, test_tenant, test_user):
    """Test that creating a form automatically creates a FlowDefinition."""
    
    request = FormCreateRequest(
        name="测试表单",
        category="survey",
        access_mode="public"
    )
    
    form = FormService.create_form(
        request=request,
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        db=db_session
    )
    
    # Verify form was created
    assert form.id is not None
    assert form.name == "测试表单"
    
    # Verify FlowDefinition was created
    assert form.flow_definition_id is not None
    
    flow_def = db_session.query(FlowDefinition).filter(
        FlowDefinition.id == form.flow_definition_id
    ).first()
    
    assert flow_def is not None
    assert flow_def.form_id == form.id
    assert flow_def.tenant_id == test_tenant.id
    assert flow_def.version == 0
    assert flow_def.active_snapshot_id is None
```



### Frontend Testing

**Component Tests**:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import FormList from '@/views/form/List.vue'

// Feature: approval-flow-configuration, Property 20: Flow Configuration Button State
describe('FormList - Flow Configuration Button', () => {
  it('should enable configure flow button for draft forms', async () => {
    const wrapper = mount(FormList, {
      global: {
        plugins: [createPinia()]
      }
    })
    
    // Mock form data
    const draftForm = {
      id: 1,
      name: 'Draft Form',
      status: 'draft',
      flow_definition_id: 10
    }
    
    wrapper.vm.tableData = [draftForm]
    await wrapper.vm.$nextTick()
    
    const configButton = wrapper.find('[data-test="config-flow-btn"]')
    expect(configButton.attributes('disabled')).toBeUndefined()
  })
  
  it('should disable configure flow button for published forms', async () => {
    const wrapper = mount(FormList, {
      global: {
        plugins: [createPinia()]
      }
    })
    
    const publishedForm = {
      id: 2,
      name: 'Published Form',
      status: 'published',
      flow_definition_id: 20
    }
    
    wrapper.vm.tableData = [publishedForm]
    await wrapper.vm.$nextTick()
    
    const configButton = wrapper.find('[data-test="config-flow-btn"]')
    expect(configButton.attributes('disabled')).toBeDefined()
  })
})
```

### Test Coverage Goals

- **Backend Service Layer**: 90%+ coverage
- **Backend API Layer**: 85%+ coverage
- **Frontend Components**: 80%+ coverage
- **Property Tests**: All 22 properties implemented

### Integration Testing

**End-to-End Flow**:

```python
def test_complete_flow_configuration_workflow(
    client, db_session, test_tenant, test_user, auth_headers
):
    """Test the complete workflow from form creation to flow publishing."""
    
    # Step 1: Create form
    response = client.post(
        "/api/v1/forms",
        json={
            "name": "E2E Test Form",
            "category": "survey",
            "access_mode": "public"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    form_data = response.json()["data"]
    flow_def_id = form_data["flow_definition_id"]
    
    # Step 2: Save flow draft
    draft_config = {
        "flow_definition_id": flow_def_id,
        "version": 1,
        "nodes": [
            {"temp_id": "n1", "type": "start", "name": "开始", "config": {}},
            {"temp_id": "n2", "type": "approval", "name": "审批", 
             "config": {"approver_type": "user", "approver_ids": [test_user.id]}},
            {"temp_id": "n3", "type": "end", "name": "结束", "config": {}}
        ],
        "routes": [
            {"from_node_id": "n1", "to_node_id": "n2", "priority": 1},
            {"from_node_id": "n2", "to_node_id": "n3", "priority": 1}
        ]
    }
    
    response = client.put(
        f"/api/v1/flows/{flow_def_id}/draft",
        json=draft_config,
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # Step 3: Publish flow
    response = client.post(
        f"/api/v1/flows/{flow_def_id}/publish",
        json={
            "flow_definition_id": flow_def_id,
            "version": 1,
            "changelog": "Initial version"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # Step 4: Verify flow is published
    flow_def = db_session.query(FlowDefinition).get(flow_def_id)
    assert flow_def.active_snapshot_id is not None
    assert flow_def.version == 1
    
    # Step 5: Publish form (should succeed now)
    response = client.post(
        f"/api/v1/forms/{form_data['id']}/publish",
        headers=auth_headers
    )
    assert response.status_code == 200
```



## Implementation Notes

### Graph Algorithm Complexity

**Reachability Check (BFS)**:
- Time Complexity: O(V + E) where V = nodes, E = routes
- Space Complexity: O(V) for visited set and queue

**Cycle Detection (DFS)**:
- Time Complexity: O(V + E)
- Space Complexity: O(V) for recursion stack and visited sets

**Performance Considerations**:
- For typical flows (< 50 nodes), performance is negligible
- For large flows (> 100 nodes), consider caching validation results
- Validation runs only on publish, not on draft save

### Optimistic Locking Strategy

The draft version field implements optimistic locking to handle concurrent edits:

```python
# Client sends current version
request = FlowDraftSaveRequest(
    flow_definition_id=1,
    version=5,  # Current version client has
    nodes=[...],
    routes=[...]
)

# Server checks version
draft = db.query(FlowDraft).filter(...).first()
if request.version != draft.version:
    raise BusinessError("草稿版本已变更，请刷新后重试")

# Increment version on save
draft.version += 1
```

**Conflict Resolution**:
- On version mismatch, client must refresh and merge changes manually
- No automatic merge strategy (too complex for graph structures)
- Frontend shows warning dialog prompting user to refresh

### Security Considerations

1. **Authorization**: All flow operations check `form.owner_user_id == current_user.id`
2. **Tenant Isolation**: All queries filter by `tenant_id`
3. **Input Validation**: All node/route data validated by Pydantic schemas
4. **SQL Injection**: Using SQLAlchemy ORM prevents SQL injection
5. **XSS Prevention**: Frontend sanitizes all user input in node names

### Migration Strategy

**Database Migration**:

```python
# alembic/versions/xxx_add_flow_definition_to_forms.py

def upgrade():
    # Add flow_definition_id to forms table
    op.add_column('form', 
        sa.Column('flow_definition_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_form_flow_definition',
        'form', 'flow_definition',
        ['flow_definition_id'], ['id']
    )
    
    # Create FlowDefinition for existing forms
    connection = op.get_bind()
    forms = connection.execute(sa.text("SELECT id, tenant_id, name FROM form"))
    
    for form in forms:
        # Insert FlowDefinition
        result = connection.execute(
            sa.text("""
                INSERT INTO flow_definition (tenant_id, form_id, name, version, created_at, updated_at)
                VALUES (:tenant_id, :form_id, :name, 0, NOW(), NOW())
                RETURNING id
            """),
            {
                'tenant_id': form.tenant_id,
                'form_id': form.id,
                'name': f"{form.name} - 审批流程"
            }
        )
        flow_def_id = result.fetchone()[0]
        
        # Update form with flow_definition_id
        connection.execute(
            sa.text("UPDATE form SET flow_definition_id = :flow_id WHERE id = :form_id"),
            {'flow_id': flow_def_id, 'form_id': form.id}
        )

def downgrade():
    op.drop_constraint('fk_form_flow_definition', 'form', type_='foreignkey')
    op.drop_column('form', 'flow_definition_id')
```



### Rollout Plan

**Phase 1: Backend Implementation** (Week 1)
1. Add FlowDefinition creation to FormService.create_form()
2. Implement 9 validation methods in FlowService
3. Add flow validation to FormService.publish_form()
4. Write unit tests for all validation methods
5. Create database migration

**Phase 2: Frontend Integration** (Week 2)
1. Add flow configuration route to router
2. Add "配置流程" button to Form List
3. Add flow configuration prompt to Form Designer
4. Test flow configurator with new backend validation
5. Add error handling for validation failures

**Phase 3: Testing & Documentation** (Week 3)
1. Write property-based tests for all 22 properties
2. Perform integration testing
3. Update API documentation
4. Create user guide for flow configuration
5. Performance testing with large flows

**Phase 4: Deployment** (Week 4)
1. Deploy to staging environment
2. User acceptance testing
3. Fix any issues found
4. Deploy to production
5. Monitor for errors

### Monitoring & Observability

**Metrics to Track**:
- Flow publish success rate
- Validation failure breakdown by type
- Average flow complexity (node count, edge count)
- Draft save frequency
- Time to publish (from creation to first publish)

**Logging**:

```python
logger.info(
    "Flow validation started",
    extra={
        "flow_definition_id": flow_def_id,
        "node_count": len(nodes),
        "route_count": len(routes),
        "user_id": user_id
    }
)

logger.warning(
    "Flow validation failed",
    extra={
        "flow_definition_id": flow_def_id,
        "validation_type": "single_start_node",
        "error": str(error)
    }
)
```

### Future Enhancements

1. **Visual Validation Feedback**: Highlight problematic nodes/routes in the configurator
2. **Auto-Fix Suggestions**: Suggest fixes for common validation errors
3. **Flow Templates**: Pre-built flow templates for common scenarios
4. **Version Comparison**: Visual diff between flow versions
5. **Parallel Approval Paths**: Support for parallel approval branches
6. **Conditional Routing**: Advanced condition expressions with formula builder
7. **Flow Simulation**: Test flow execution with sample data
8. **Performance Optimization**: Cache validation results for large flows

## Appendix

### API Endpoint Summary

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/forms` | Create form (auto-creates flow) | User |
| POST | `/api/v1/forms/{id}/publish` | Publish form (validates flow) | Owner |
| GET | `/api/v1/flows/{id}` | Get flow definition detail | Owner |
| GET | `/api/v1/flows/{id}/draft` | Get flow draft | Owner |
| PUT | `/api/v1/flows/{id}/draft` | Save flow draft | Owner |
| POST | `/api/v1/flows/{id}/publish` | Publish flow (with validation) | Owner |
| GET | `/api/v1/flows/{id}/snapshots` | List flow snapshots | Owner |

### Frontend Route Summary

| Path | Component | Description | Auth |
|------|-----------|-------------|------|
| `/form/list` | FormList | Form list with config button | Yes |
| `/form/designer` | FormDesigner | Form designer with flow prompt | Yes |
| `/flow/configurator/:id` | FlowConfigurator | Visual flow editor | Yes |

### Validation Rules Summary

| Rule | Description | Error Message |
|------|-------------|---------------|
| 1 | Exactly one start node | "流程必须有一个开始节点" / "流程只能有一个开始节点" |
| 2 | At least one end node | "流程必须至少有一个结束节点" |
| 3 | At least one approval node | "流程必须至少有一个审批节点" |
| 4 | Non-end nodes have outgoing edges | "节点 {name} 必须有出边" |
| 5 | Non-start nodes have incoming edges | "节点 {name} 必须有入边" |
| 6 | Condition nodes have ≥2 branches | "条件节点 {name} 必须至少有两条分支" |
| 7 | Approval nodes have approver config | "审批节点 {name} 必须配置审批人" |
| 8 | End nodes reachable from start | "流程不可达：无法从开始节点到达结束节点" |
| 9 | No dead cycles | "流程存在死循环" |

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-XX  
**Author**: Kiro AI Assistant  
**Status**: Ready for Review
