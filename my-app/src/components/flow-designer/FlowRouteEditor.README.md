# FlowRouteEditor 组件文档

## 概述

`FlowRouteEditor` 是流程设计器中用于编辑路由配置的组件。它支持编辑路由的所有属性，包括条件表达式、优先级和默认路由设置。

## 功能特性

### 1. 基本信息编辑
- **来源节点选择**：选择路由的起点节点
- **目标节点选择**：选择路由的终点节点
- **优先级设置**：设置路由的执行优先级（1-999）

### 2. 条件表达式编辑
- **集成 ConditionBuilderV2**：使用可视化界面编辑复杂条件
- **条件预览**：显示当前条件的简要描述
- **切换编辑模式**：支持在预览和编辑模式之间切换

### 3. 默认路由设置
- **默认路由标记**：将路由标记为默认路由
- **提示信息**：当设置为默认路由时显示说明

## 使用示例

### 基本使用

```vue
<template>
  <FlowRouteEditor
    :route="selectedRoute"
    :all-nodes="nodes"
    :form-schema="formSchema"
    :form-id="formId"
    @update-route="handleRouteUpdate"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FlowRouteEditor from '@/components/flow-designer/FlowRouteEditor.vue'
import type { FlowRouteConfig, FlowNodeConfig } from '@/types/flow'
import type { FormSchema } from '@/types/schema'

const selectedRoute = ref<FlowRouteConfig>({
  from_node_key: '1',
  to_node_key: '2',
  priority: 1,
  condition: null,
  is_default: false,
})

const nodes = ref<FlowNodeConfig[]>([
  { id: 1, name: '开始', type: 'start', ... },
  { id: 2, name: '审批', type: 'user', ... },
  { id: 3, name: '结束', type: 'end', ... },
])

const formSchema = ref<FormSchema>({ ... })
const formId = ref(1)

const handleRouteUpdate = (payload: { key: string; patch: Partial<FlowRouteConfig> }) => {
  console.log('Route updated:', payload)
  // 更新路由配置
}
</script>
```

## Props

| 属性 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `route` | `FlowRouteConfig` | 否 | 当前编辑的路由配置 |
| `allNodes` | `FlowNodeConfig[]` | 否 | 所有可用的节点列表 |
| `formSchema` | `FormSchema` | 否 | 表单 schema，用于条件编辑 |
| `formId` | `number` | 否 | 表单 ID，用于从 API 加载字段 |
| `disabled` | `boolean` | 否 | 是否禁用编辑（默认 false） |

## Events

### update-route

当路由配置发生变化时触发。

**参数：**
```typescript
{
  key: string                          // 路由的唯一标识（ID 或 temp_id）
  patch: Partial<FlowRouteConfig>      // 变化的字段
}
```

**示例：**
```typescript
const handleRouteUpdate = (payload) => {
  const { key, patch } = payload
  // 更新对应的路由
  const route = routes.value.find(r => r.id?.toString() === key || r.temp_id === key)
  if (route) {
    Object.assign(route, patch)
  }
}
```

## 数据结构

### FlowRouteConfig

```typescript
interface FlowRouteConfig {
  // 路由 ID（草稿阶段可能不存在）
  id?: number
  
  // 前端临时 ID
  temp_id?: string
  
  // 来源节点 key（ID 或 temp_id）
  from_node_key: string
  
  // 目标节点 key（ID 或 temp_id）
  to_node_key: string
  
  // 优先级
  priority: number
  
  // 条件表达式（JsonLogic）
  condition?: JsonLogicExpression | null
  
  // 是否默认路由
  is_default: boolean
}
```

## 条件表达式格式

条件表达式使用 JsonLogic 格式，由 ConditionBuilderV2 组件生成。

**示例：**
```json
{
  "type": "GROUP",
  "logic": "AND",
  "children": [
    {
      "type": "RULE",
      "field": "amount",
      "operator": "gt",
      "value": 10000
    },
    {
      "type": "RULE",
      "field": "category",
      "operator": "eq",
      "value": "travel"
    }
  ]
}
```

## 样式定制

组件使用 Naive UI 组件库，可以通过 CSS 变量或深度选择器进行定制。

### 常用的深度选择器

```css
/* 编辑器容器 */
:deep(.flow-route-editor) { ... }

/* 表单项 */
:deep(.n-form-item) { ... }

/* 选择框 */
:deep(.n-select) { ... }

/* 条件编辑器 */
:deep(.condition-builder-v2) { ... }
```

## 集成指南

### 在 FlowDesigner 中使用

```vue
<template>
  <div class="flow-designer">
    <div class="canvas-area">
      <FlowCanvas :nodes="nodes" :routes="routes" @select-route="selectRoute" />
    </div>
    
    <div class="inspector-area">
      <FlowRouteEditor
        :route="selectedRoute"
        :all-nodes="nodes"
        :form-id="formId"
        @update-route="updateRoute"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FlowCanvas from './FlowCanvas.vue'
import FlowRouteEditor from './FlowRouteEditor.vue'

const nodes = ref([])
const routes = ref([])
const selectedRoute = ref(null)
const formId = ref(1)

const selectRoute = (route) => {
  selectedRoute.value = route
}

const updateRoute = (payload) => {
  const { key, patch } = payload
  const route = routes.value.find(r => r.id?.toString() === key || r.temp_id === key)
  if (route) {
    Object.assign(route, patch)
  }
}
</script>
```

## 注意事项

1. **节点选择**：来源节点和目标节点不能相同
2. **优先级**：优先级数字越小，执行优先级越高
3. **默认路由**：每个来源节点最多只能有一个默认路由
4. **条件表达式**：条件表达式由 ConditionBuilderV2 组件管理，确保格式正确
5. **表单字段**：条件编辑需要表单 ID 或 formSchema 来加载可用字段

## 相关组件

- **ConditionBuilderV2**：条件表达式编辑器
- **FlowCanvas**：流程画布
- **FlowNodeEditor**：节点编辑器
- **ConditionNodeEditor**：条件节点编辑器

## 类型定义

所有类型定义位于 `@/types/flow.ts` 和 `@/types/condition.ts`。
