# 路由条件数据绑定关系分析

## 问题描述

当前系统存在数据混乱的问题：

1. **条件数据混乱**：在一个审批节点添加的条件，切换到其他节点时仍然显示该条件
2. **路由属性混乱**：所有节点共用同一个路由属性，而不是每个节点有自己的路由属性

## 当前数据结构

### 1. 节点结构 (FlowNodeConfig)
```typescript
interface FlowNodeConfig {
  id?: number
  temp_id?: string
  name: string
  type: FlowNodeType  // 'start', 'end', 'user', 'cc', etc.
  // ... 其他节点属性
}
```

### 2. 路由结构 (FlowRouteConfig)
```typescript
interface FlowRouteConfig {
  id?: number
  temp_id?: string
  from_node_key: string      // 来源节点 key
  to_node_key: string        // 目标节点 key
  priority: number
  condition?: JsonLogicExpression | null  // 条件
  is_default: boolean
}
```

### 3. 当前的绑定关系

```
nodes: FlowNodeConfig[]
  ↓
routes: FlowRouteConfig[]
  ├─ from_node_key → 指向某个节点
  ├─ to_node_key → 指向某个节点
  └─ condition → 条件数据
```

## 问题根源

### 问题 1：条件数据混乱

**原因**：
- FlowRouteInspector 组件在显示条件时，没有正确关联到具体的路由
- 当用户切换节点时，如果新节点有相同的路由配置，会显示相同的条件
- 条件是存储在 `route.condition` 中的，但显示时没有考虑路由的 `from_node_key` 和 `to_node_key`

**当前流程**：
```
用户在节点 A 添加条件
  ↓
条件保存到某个 route.condition
  ↓
用户切换到节点 B
  ↓
如果节点 B 有相同的 route，就显示相同的条件 ❌
```

### 问题 2：路由属性混乱

**原因**：
- 路由是全局的，存储在 `routes` 数组中
- 每个路由有 `from_node_key` 和 `to_node_key`，定义了来源和目标节点
- 但在 UI 上，用户在编辑某个节点时，应该只看到与该节点相关的路由

**当前流程**：
```
节点 A（开始）→ 节点 B（审批）→ 节点 C（结束）

routes 数组：
[
  { from: A, to: B, condition: {...} },
  { from: B, to: C, condition: {...} }
]

用户在节点 B 编辑时：
- 应该看到：from=A, to=B 的路由（来源是 A，目标是自己）
- 不应该看到：from=B, to=C 的路由（这是从 B 出发的路由）
```

## 正确的数据绑定关系

### 1. 条件应该与路由绑定

```
Route 1: A → B
  ├─ from_node_key: A
  ├─ to_node_key: B
  └─ condition: { "==": [{ "var": "amount" }, 1000] }

Route 2: B → C
  ├─ from_node_key: B
  ├─ to_node_key: C
  └─ condition: { ">": [{ "var": "amount" }, 500] }
```

### 2. 节点编辑时应该显示正确的路由

当用户编辑节点 B 时：
- **进入路由**（Incoming Routes）：from_node_key = B 的所有路由
  - 这些是进入节点 B 的路由
  - 用户可以配置这些路由的条件
- **出出路由**（Outgoing Routes）：to_node_key = B 的所有路由
  - 这些是从节点 B 出发的路由
  - 用户可以配置这些路由的条件

等等，我理解错了。让我重新理解：

- `from_node_key` = 来源节点（路由的起点）
- `to_node_key` = 目标节点（路由的终点）

所以：
- Route: A → B 表示从 A 到 B 的路由
- 当编辑节点 B 时，应该看到 to_node_key = B 的路由（进入 B 的路由）
- 当编辑节点 A 时，应该看到 from_node_key = A 的路由（从 A 出发的路由）

## 解决方案

### 1. 修复 FlowRouteInspector 组件

**问题**：组件没有正确过滤路由

**解决**：
```typescript
// 当编辑某个节点时，应该只显示与该节点相关的路由
const relevantRoutes = computed(() => {
  if (!currentNode.value) return []
  
  const nodeKey = getNodeKey(currentNode.value)
  
  // 显示进入该节点的路由（to_node_key = 当前节点）
  return routes.value.filter(route => route.to_node_key === nodeKey)
})
```

### 2. 修复条件显示逻辑

**问题**：条件显示时没有考虑路由的来源和目标

**解决**：
```typescript
// 在显示条件时，明确指出这是哪个路由的条件
// 例如：显示"从开始节点到审批节点的条件"
const routeDescription = computed(() => {
  if (!currentRoute.value) return ''
  
  const fromNode = nodes.value.find(n => getNodeKey(n) === currentRoute.value.from_node_key)
  const toNode = nodes.value.find(n => getNodeKey(n) === currentRoute.value.to_node_key)
  
  return `从 ${fromNode?.name} 到 ${toNode?.name} 的条件`
})
```

### 3. 修复路由属性编辑

**问题**：编辑路由时没有正确关联到具体的路由

**解决**：
```typescript
// 在编辑路由时，应该明确指出是哪个路由
const selectRoute = (routeIndex: number) => {
  selectedRouteIndex.value = routeIndex
  // 此时应该显示该路由的所有属性（优先级、条件、是否默认等）
}
```

## 实现步骤

### 第一步：理清数据结构
- 确认 `routes` 数组中每个路由的 `from_node_key` 和 `to_node_key` 是否正确
- 确认路由的条件是否正确存储在 `route.condition` 中

### 第二步：修复 FlowRouteInspector 组件
- 添加路由过滤逻辑，只显示与当前节点相关的路由
- 修复条件显示逻辑，明确显示是哪个路由的条件
- 修复条件编辑逻辑，确保编辑的是正确的路由

### 第三步：修复条件编辑弹窗
- 在弹窗中显示路由的来源和目标节点
- 确保条件编辑后保存到正确的路由

### 第四步：测试
- 测试在不同节点编辑条件是否相互独立
- 测试路由属性是否正确关联到具体的路由

## 关键代码位置

1. **FlowRouteInspector.vue**：路由属性检查器组件
   - 需要修复：路由过滤、条件显示、条件编辑

2. **flowDraft.ts**：状态管理
   - 需要检查：路由数据的正确性

3. **ConditionBuilderV2.vue**：条件构建器
   - 需要修复：条件编辑时的路由关联

## 总结

核心问题是：**条件和路由属性没有正确关联到具体的路由**

解决方案是：**在编辑节点时，只显示与该节点相关的路由，并在编辑条件时明确指出是哪个路由的条件**
