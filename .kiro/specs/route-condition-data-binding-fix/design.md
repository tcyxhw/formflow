# 路由和条件数据绑定修复 - 设计文档

## 1. 问题分析

### 1.1 数据结构

当前系统中的关键数据结构：

```typescript
// 节点配置
interface FlowNodeConfig {
  id?: number
  temp_id?: string
  name: string
  type: FlowNodeType  // 'start', 'end', 'user', 'cc', etc.
  // ... 其他属性
}

// 路由配置
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

### 1.2 问题根源

**问题 1：条件数据混乱**
- FlowRouteInspector 组件在显示条件时，没有正确关联到具体的路由
- 当用户切换节点时，如果新节点有相同的路由配置，会显示相同的条件
- 条件存储在 `route.condition` 中，但显示时没有考虑路由的 `from_node_key` 和 `to_node_key`

**问题 2：路由属性混乱**
- 路由是全局的，存储在 `routes` 数组中
- 每个路由有 `from_node_key` 和 `to_node_key`，定义了来源和目标节点
- 但在 UI 上，用户在编辑某个节点时，应该只看到与该节点相关的路由

**问题 3：编辑时显示错误的数据**
- 编辑节点 B 时，应该只显示进入节点 B 的路由（to_node_key = B）
- 但当前系统显示所有路由

## 2. 设计方案

### 2.1 路由过滤逻辑

在 FlowRouteInspector 组件中添加路由过滤：

```typescript
// 当编辑某个节点时，只显示进入该节点的路由
const relevantRoutes = computed(() => {
  if (!currentNode.value) return []
  
  const nodeKey = getNodeKey(currentNode.value)
  
  // 显示进入该节点的路由（to_node_key = 当前节点）
  return routes.value.filter(route => route.to_node_key === nodeKey)
})
```

### 2.2 条件显示与编辑

在条件构建器中明确显示路由信息：

```typescript
// 显示路由的来源和目标节点
const routeDescription = computed(() => {
  if (!currentRoute.value) return ''
  
  const fromNode = nodes.value.find(n => getNodeKey(n) === currentRoute.value.from_node_key)
  const toNode = nodes.value.find(n => getNodeKey(n) === currentRoute.value.to_node_key)
  
  return `从 ${fromNode?.name} 到 ${toNode?.name} 的条件`
})

// 确保条件编辑后保存到正确的路由
const saveCondition = (condition: JsonLogicExpression | null) => {
  if (!currentRoute.value) return
  
  // 更新当前路由的条件
  const routeIndex = routes.value.findIndex(r => 
    r.from_node_key === currentRoute.value.from_node_key &&
    r.to_node_key === currentRoute.value.to_node_key
  )
  
  if (routeIndex !== -1) {
    routes.value[routeIndex].condition = condition
  }
}
```

### 2.3 路由属性绑定

确保每个路由有独立的属性：

```typescript
// 修改路由优先级
const updateRoutePriority = (routeIndex: number, priority: number) => {
  if (routeIndex >= 0 && routeIndex < routes.value.length) {
    routes.value[routeIndex].priority = priority
  }
}

// 修改默认路由标记
const updateRouteDefault = (routeIndex: number, isDefault: boolean) => {
  if (routeIndex >= 0 && routeIndex < routes.value.length) {
    routes.value[routeIndex].is_default = isDefault
  }
}
```

## 3. 实现步骤

### 3.1 修复 FlowRouteInspector 组件

**文件**: `my-app/src/components/flow-configurator/FlowRouteInspector.vue`

**修改内容**:
1. 添加路由过滤逻辑
2. 修复路由选择逻辑
3. 修复条件显示逻辑
4. 修复条件编辑逻辑

### 3.2 修复 ConditionBuilderV2 组件

**文件**: `my-app/src/components/flow-configurator/ConditionBuilderV2.vue`

**修改内容**:
1. 添加路由信息显示
2. 修复条件保存逻辑
3. 确保条件保存到正确的路由

### 3.3 修复 flowDraft 状态管理

**文件**: `my-app/src/stores/flowDraft.ts`

**修改内容**:
1. 检查路由数据结构是否正确
2. 添加路由过滤方法
3. 添加路由更新方法

## 4. 测试策略

### 4.1 单元测试

**测试路由过滤**:
- 验证 `relevantRoutes` 计算属性是否正确过滤路由
- 验证只显示进入当前节点的路由

**测试条件显示**:
- 验证条件是否正确显示
- 验证路由信息是否正确显示

**测试条件编辑**:
- 验证条件编辑后是否保存到正确的路由
- 验证条件清除是否只清除当前路由的条件

**测试路由属性**:
- 验证优先级修改是否只影响当前路由
- 验证默认状态修改是否只影响当前路由

### 4.2 集成测试

**测试场景 1：多节点条件独立性**
- 创建三个节点：开始 → 审批 → 结束
- 在开始→审批的路由上添加条件 A
- 在审批→结束的路由上添加条件 B
- 验证切换节点时条件是否相互独立

**测试场景 2：路由属性独立性**
- 创建多个路由
- 修改第一个路由的优先级
- 验证其他路由的优先级是否不变

**测试场景 3：保存和加载**
- 创建审批流并配置条件
- 保存到数据库
- 重新加载
- 验证条件是否正确加载

### 4.3 回归测试

**基本功能**:
- 创建新的审批流
- 保存审批流配置
- 查看已保存的审批流
- 删除节点

## 5. 关键代码位置

1. **FlowRouteInspector.vue**：路由属性检查器组件
   - 需要修复：路由过滤、条件显示、条件编辑

2. **flowDraft.ts**：状态管理
   - 需要检查：路由数据的正确性

3. **ConditionBuilderV2.vue**：条件构建器
   - 需要修复：条件编辑时的路由关联

## 6. 验收标准

- [ ] 路由过滤逻辑正确实现
- [ ] 条件显示与编辑逻辑正确实现
- [ ] 路由属性绑定逻辑正确实现
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 手动测试验证通过
- [ ] 回归测试验证通过
- [ ] 代码审查通过

## 7. 风险与缓解

**风险 1：修改路由过滤逻辑可能影响其他功能**
- 缓解：编写充分的单元测试和集成测试

**风险 2：条件保存逻辑修改可能导致数据丢失**
- 缓解：在修改前备份数据，编写数据迁移脚本

**风险 3：修改可能影响已保存的审批流**
- 缓解：编写数据迁移脚本，确保向后兼容

## 8. 后续工作

- 优化路由显示的 UI/UX
- 添加路由冲突检测
- 添加路由优化建议
