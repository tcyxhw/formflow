# FlowNodePalette 组件

## 概述

`FlowNodePalette` 是流程设计器的节点调色板组件，用于展示所有可用的节点类型，支持拖拽添加节点到画布。

## 功能特性

- 📦 展示所有可用的节点类型（基础节点和高级节点）
- 🎯 支持拖拽操作，将节点拖到画布上
- 🎨 清晰的分类展示，易于查找
- ⚡ 轻量级实现，无复杂依赖

## 节点类型

### 基础节点
- **开始 (start)**: 流程起点，每个流程必须有一个开始节点
- **结束 (end)**: 流程终点，表示流程完成

### 高级节点
- **审批 (user)**: 人工审批节点，需要指定审批人
- **条件 (condition)**: 条件分支节点，根据条件路由到不同的分支
- **抄送 (auto)**: 抄送通知节点，用于通知相关人员

## 使用方式

### 基本用法

```vue
<template>
  <div class="flow-designer">
    <FlowNodePalette />
    <FlowCanvas 
      :nodes="nodes"
      :routes="routes"
      @add-node="handleAddNode"
    />
  </div>
</template>

<script setup lang="ts">
import FlowNodePalette from '@/components/flow-designer/FlowNodePalette.vue'
import FlowCanvas from '@/components/flow-designer/FlowCanvas.vue'

const nodes = ref([])
const routes = ref([])

const handleAddNode = (nodeData) => {
  // 处理添加节点
  nodes.value.push(nodeData)
}
</script>
```

### 拖拽集成

组件通过 HTML5 Drag and Drop API 实现拖拽功能。当用户拖拽节点时，会设置以下数据：

```javascript
{
  type: 'node',
  nodeType: 'user',  // 节点类型
  defaultName: '审批'  // 默认节点名称
}
```

在画布组件中接收拖拽事件：

```typescript
const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  event.dataTransfer!.dropEffect = 'copy'
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  const data = JSON.parse(event.dataTransfer!.getData('application/json'))
  
  if (data.type === 'node') {
    const x = (event.clientX - boardRect.left - panX.value) / scale.value
    const y = (event.clientY - boardRect.top - panY.value) / scale.value
    
    const newNode = {
      temp_id: `node_${Date.now()}`,
      name: data.defaultName,
      type: data.nodeType,
      position_x: x,
      position_y: y,
      // ... 其他默认配置
    }
    
    nodes.value.push(newNode)
  }
}
```

## 组件 Props

该组件不接收任何 props，所有节点类型都是内置的。

## 组件事件

该组件不发出任何事件，通过 HTML5 Drag and Drop API 与父组件通信。

## 样式定制

组件使用 scoped styles，可以通过以下 CSS 变量进行定制：

```css
/* 节点图标颜色 */
.node-icon {
  color: #18a058;  /* 绿色 */
}

/* 悬停效果 */
.palette-node:hover {
  background-color: #f3f4f6;
  border-color: #d1d5db;
}
```

## 最佳实践

1. **放置位置**: 通常将调色板放在设计器的左侧或右侧
2. **响应式设计**: 在小屏幕上可以考虑使用模态框或抽屉展示
3. **拖拽反馈**: 在画布中提供清晰的拖拽反馈（如高亮区域）
4. **节点验证**: 在添加节点后进行验证，确保流程结构有效

## 相关组件

- `FlowCanvas`: 流程画布组件
- `FlowNodeEditor`: 节点编辑器组件
- `FlowRouteEditor`: 路由编辑器组件

## 技术细节

- **框架**: Vue 3 + TypeScript
- **UI 库**: Naive UI
- **图标库**: @vicons/antd
- **拖拽 API**: HTML5 Drag and Drop API
