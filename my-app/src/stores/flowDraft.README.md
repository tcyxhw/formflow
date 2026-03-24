# 流程草稿状态管理 (useFlowDraftStore)

## 概述

`useFlowDraftStore` 是 FormFlow 前端的核心状态管理模块，负责管理流程设计器中的所有状态，包括节点、路由、选择状态和编辑历史。

## 核心功能

### 1. 节点管理

#### 添加节点
```typescript
store.addNode('user')  // 添加用户审批节点
store.addNode('condition')  // 添加条件分支节点
store.addNode('end')  // 添加结束节点
```

#### 更新节点
```typescript
store.updateNode(nodeKey, {
  name: '部门经理审批',
  assignee_type: 'role',
  assignee_value: { role_id: 123 }
})
```

#### 删除节点
```typescript
store.removeNode(nodeKey)
// 自动删除相关路由
```

#### 更新节点位置
```typescript
store.updateNodePosition(nodeKey, { x: 100, y: 200 })
```

### 2. 路由管理

#### 添加路由
```typescript
store.addRoute({
  from_node_key: startNodeKey,
  to_node_key: approvalNodeKey,
  priority: 1,
  is_default: true,
  condition: null
})
```

#### 更新路由
```typescript
store.updateRoute(routeIndex, {
  priority: 2,
  condition: { '==': [{ var: 'amount' }, 1000] }
})
```

#### 删除路由
```typescript
store.removeRoute(routeIndex)
```

### 3. 选择管理

#### 选择节点
```typescript
store.selectNodeByKey(nodeKey)
// 获取当前选中节点
const currentNode = store.currentNode
```

#### 选择路由
```typescript
store.selectRouteByIndex(routeIndex)
// 获取当前选中路由
const currentRoute = store.currentRoute
```

### 4. 流程定义加载

#### 加载流程定义
```typescript
const result = await store.loadDefinition(definitionId)
// 自动加载草稿或构建默认草稿
```

### 5. 保存和发布

#### 保存草稿
```typescript
await store.saveDraftRemote()
// 更新版本号和最后保存时间
```

#### 发布流程
```typescript
await store.publishCurrentDraft({
  changelog: '初始版本',
  versionTag: 'v1.0'
})
```

## 状态属性

### 基本信息
- `flowDefinitionId`: 流程定义 ID
- `flowName`: 流程名称
- `version`: 当前版本号

### 数据
- `nodes`: 节点列表
- `routes`: 路由列表
- `nodesGraph`: 节点位置信息

### 选择状态
- `selectedNodeKey`: 当前选中节点的 key
- `selectedRouteIndex`: 当前选中路由的索引

### 操作状态
- `dirty`: 是否有未保存的更改
- `loading`: 是否正在加载
- `saving`: 是否正在保存
- `publishing`: 是否正在发布

### 历史信息
- `snapshots`: 流程快照列表
- `lastSnapshotId`: 最后同步的快照 ID
- `lastSavedAt`: 最后保存时间
- `lastPublishedAt`: 最后发布时间

## 计算属性

### currentNode
获取当前选中的节点对象
```typescript
const node = store.currentNode
```

### currentRoute
获取当前选中的路由对象
```typescript
const route = store.currentRoute
```

### nodeOptions
获取所有节点的选项列表（用于下拉菜单）
```typescript
const options = store.nodeOptions
// [{ label: '开始', value: 'tmp-xxx' }, ...]
```

### definitionLoaded
检查是否已加载流程定义
```typescript
if (store.definitionLoaded) {
  // 可以进行编辑操作
}
```

## 节点类型

支持的节点类型：
- `start`: 开始节点
- `user`: 用户审批节点
- `auto`: 自动审批节点
- `condition`: 条件分支节点
- `end`: 结束节点

## 节点配置示例

### 用户审批节点
```typescript
{
  name: '部门经理审批',
  type: 'user',
  assignee_type: 'role',
  assignee_value: { role_id: 123 },
  approve_policy: 'any',  // any | all | percent
  allow_delegate: true,
  reject_strategy: 'TO_START',  // TO_START | TO_PREVIOUS
  auto_approve_enabled: false,
  auto_approve_cond: null,
  auto_reject_cond: null,
  metadata: {}
}
```

### 条件分支节点
```typescript
{
  name: '金额判断',
  type: 'condition',
  condition_branches: {
    branches: [
      {
        priority: 1,
        label: '大额',
        condition: { '>=': [{ var: 'amount' }, 10000] },
        target_node_id: 123
      }
    ],
    default_target_node_id: 456
  },
  metadata: {}
}
```

## 路由配置示例

### 简单路由
```typescript
{
  from_node_key: '1',
  to_node_key: '2',
  priority: 1,
  is_default: true,
  condition: null
}
```

### 条件路由
```typescript
{
  from_node_key: '2',
  to_node_key: '3',
  priority: 1,
  is_default: false,
  condition: { '==': [{ var: 'department' }, 'finance'] }
}
```

## 工作流示例

### 完整的流程设计流程

```typescript
import { useFlowDraftStore } from '@/stores/flowDraft'

const store = useFlowDraftStore()

// 1. 加载流程定义
await store.loadDefinition(123)

// 2. 编辑流程
const startKey = store.nodes[0].temp_id!
const approvalKey = store.nodes[1].temp_id!

store.updateNode(approvalKey, {
  name: '部门经理审批',
  assignee_type: 'role',
  assignee_value: { role_id: 1 }
})

// 3. 添加新节点
store.addNode('condition')
const conditionKey = store.nodes[store.nodes.length - 1].temp_id!

// 4. 添加路由
store.addRoute({
  from_node_key: approvalKey,
  to_node_key: conditionKey,
  priority: 1,
  is_default: true
})

// 5. 保存草稿
await store.saveDraftRemote()

// 6. 发布流程
await store.publishCurrentDraft({
  changelog: '添加条件分支',
  versionTag: 'v1.1'
})
```

## 测试覆盖

### 单元测试 (32 个测试)
- 初始化状态
- 节点管理 (添加、更新、删除、位置)
- 路由管理 (添加、更新、删除)
- 选择管理
- 脏标记
- 验证
- 负载构建

### 集成测试 (12 个测试)
- 加载流程定义
- 保存草稿
- 发布流程
- 完整工作流
- 多节点编辑场景

## 最佳实践

### 1. 始终检查定义是否已加载
```typescript
if (!store.definitionLoaded) {
  await store.loadDefinition(id)
}
```

### 2. 监听脏标记以提示用户保存
```typescript
watch(() => store.dirty, (isDirty) => {
  if (isDirty) {
    showSavePrompt()
  }
})
```

### 3. 使用计算属性获取节点选项
```typescript
const nodeOptions = computed(() => store.nodeOptions)
```

### 4. 验证路由的有效性
```typescript
// 不能从结束节点添加出边
const fromNode = store.nodes.find(n => getNodeKey(n) === route.from_node_key)
if (fromNode?.type === 'end') {
  throw new Error('结束节点不能有出边')
}
```

### 5. 处理异步操作的错误
```typescript
try {
  await store.saveDraftRemote()
} catch (error) {
  console.error('保存失败:', error)
  showErrorMessage('保存失败，请重试')
}
```

## 常见问题

### Q: 如何获取节点的唯一标识？
A: 使用 `node.id`（已保存的节点）或 `node.temp_id`（新节点）

### Q: 删除节点时会发生什么？
A: 自动删除所有相关的路由，并调整选中状态

### Q: 如何验证流程结构的有效性？
A: 在保存或发布前，系统会自动验证所有节点和路由

### Q: 支持撤销/重做吗？
A: 当前版本不支持，可以通过加载之前的快照来恢复

## 相关文件

- `src/types/flow.ts`: 类型定义
- `src/api/flow.ts`: API 接口
- `src/components/flow-designer/`: 设计器组件
- `src/stores/__tests__/`: 测试文件
