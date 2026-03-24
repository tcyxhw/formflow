# FlowCanvas 组件文档

## 概述

FlowCanvas 是一个功能完整的流程设计画布组件，支持节点拖拽、连线绘制、缩放平移等交互功能。

## 功能特性

### 6.1.1 节点拖拽
- 支持在画布上拖拽节点移动
- 实时更新节点位置
- 自动约束节点在画布范围内

### 6.1.2 连线绘制
- 支持从节点的连接点拖拽绘制连线
- 实时显示临时连线
- 自动检测目标节点并完成连接
- 支持条件路由（虚线显示）和默认路由（实线显示）

### 6.1.3 节点删除
- 右键点击节点显示上下文菜单
- 支持删除节点及其相关连线

### 6.1.4 缩放和平移
- 鼠标滚轮缩放（0.5x - 2x）
- 工具栏缩放按钮
- 重置缩放和平移功能
- 实时显示缩放百分比

## Props

```typescript
interface Props {
  // 节点列表
  nodes: FlowNodeConfig[]
  
  // 路由列表
  routes: FlowRouteConfig[]
  
  // 节点位置映射
  nodesGraph: Record<string, FlowNodePosition>
  
  // 当前选中的节点 key
  selectedNodeKey?: string
  
  // 当前选中的路由索引
  selectedRouteIndex?: number | null
}
```

## Events

```typescript
// 选中节点
emit('select-node', key: string)

// 选中路由
emit('select-route', index: number)

// 更新节点位置
emit('update-position', payload: { key: string; position: FlowNodePosition })

// 添加路由
emit('add-route', payload: { from_node_key: string; to_node_key: string })

// 删除节点
emit('delete-node', key: string)

// 删除路由
emit('delete-route', index: number)
```

## 使用示例

```vue
<template>
  <FlowCanvas
    :nodes="flowStore.nodes"
    :routes="flowStore.routes"
    :nodesGraph="flowStore.nodesGraph"
    :selectedNodeKey="flowStore.selectedNodeKey"
    :selectedRouteIndex="flowStore.selectedRouteIndex"
    @select-node="flowStore.selectNodeByKey"
    @select-route="flowStore.selectRouteByIndex"
    @update-position="handleUpdatePosition"
    @add-route="handleAddRoute"
    @delete-node="flowStore.removeNode"
    @delete-route="flowStore.removeRoute"
  />
</template>

<script setup lang="ts">
import { useFlowDraftStore } from '@/stores/flowDraft'
import FlowCanvas from '@/components/flow-designer/FlowCanvas.vue'
import type { FlowNodePosition } from '@/types/flow'

const flowStore = useFlowDraftStore()

const handleUpdatePosition = (payload: { key: string; position: FlowNodePosition }) => {
  flowStore.updateNodePosition(payload.key, payload.position)
}

const handleAddRoute = (payload: { from_node_key: string; to_node_key: string }) => {
  flowStore.addRoute({
    from_node_key: payload.from_node_key,
    to_node_key: payload.to_node_key,
    priority: 1,
    is_default: false
  })
}
</script>
```

## 交互说明

### 节点操作
- **选中节点**：点击节点
- **拖拽节点**：按住节点并拖动
- **删除节点**：右键点击节点 → 选择"删除节点"

### 连线操作
- **绘制连线**：从节点右侧的绿色连接点拖拽到目标节点的左侧连接点
- **选中连线**：点击连线
- **删除连线**：选中连线后按 Delete 键（需要在父组件实现）

### 画布操作
- **缩放**：鼠标滚轮或工具栏按钮
- **重置**：点击工具栏的重置按钮

## 样式定制

组件使用 scoped CSS，主要样式类：

```css
.flow-canvas          /* 画布容器 */
.grid-background      /* 网格背景 */
.flow-node            /* 节点 */
.flow-node.is-selected /* 选中的节点 */
.route-line           /* 连线 */
.route-line.is-selected /* 选中的连线 */
.connection-point     /* 连接点 */
.canvas-toolbar       /* 工具栏 */
```

## 性能优化

- 使用 computed 计算派生状态
- 事件委托处理多个节点
- 高效的位置计算算法
- 支持大规模流程图（100+ 节点）

## 测试覆盖

- 单元测试：21 个测试用例
- 集成测试：17 个测试用例
- 测试覆盖率：> 90%

## 已知限制

1. 不支持节点分组
2. 不支持自环（节点连接到自己）
3. 不支持多条连线合并
4. 连线不支持弯曲（直线连接）

## 后续改进

- [ ] 支持节点分组和折叠
- [ ] 支持连线弯曲和路由优化
- [ ] 支持撤销/重做功能
- [ ] 支持导出为图片
- [ ] 支持键盘快捷键
