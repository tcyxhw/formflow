# FlowNodeEditor 组件文档

## 概述

`FlowNodeEditor` 是一个用于编辑流程节点属性的 Vue 3 组件。它支持编辑节点的基本信息、审批人配置、驳回策略、条件分支等多种属性。

## 功能特性

### 基本信息编辑
- 节点名称编辑
- 节点类型选择（开始、人工审批、条件分支、自动节点、结束）

### 审批人配置（非条件节点）
- 审批人类型选择（用户、群组、角色、部门、岗位、表达式）
- 会签策略配置（任意一人、全部同意、自定义比例）
- 通过阈值设置（当会签策略为百分比时）
- 代理权限开关

### 驳回策略配置
- 驳回到发起人（TO_START）
- 驳回到上一个审批节点（TO_PREVIOUS）

### SLA 配置
- SLA 时长设置（小时）

### 自动审批配置
- 启用/禁用自动审批
- 抽检比例设置（0-100%）

### 条件分支配置（条件节点）
- 分支列表管理
- 条件表达式编辑
- 优先级排序
- 默认路由设置

### 路由模式
- 互斥路由（exclusive）
- 并行路由（parallel）

## 使用示例

### 基础用法

```vue
<template>
  <FlowNodeEditor
    :node="selectedNode"
    :all-nodes="allNodes"
    :form-id="formId"
    :disabled="false"
    @update-node="handleNodeUpdate"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FlowNodeEditor from '@/components/flow-designer/FlowNodeEditor.vue'
import type { FlowNodeConfig } from '@/types/flow'

const selectedNode = ref<FlowNodeConfig | undefined>()
const allNodes = ref<FlowNodeConfig[]>([])
const formId = ref(1)

const handleNodeUpdate = (payload: { key: string; patch: Partial<FlowNodeConfig> }) => {
  console.log('节点更新:', payload)
  // 处理节点更新逻辑
}
</script>
```

### 编辑审批节点

```typescript
const approvalNode: FlowNodeConfig = {
  id: 2,
  name: '部门经理审批',
  type: 'user',
  assignee_type: 'user',
  approve_policy: 'any',
  route_mode: 'exclusive',
  allow_delegate: true,
  auto_approve_enabled: false,
  auto_sample_ratio: 0,
  reject_strategy: 'TO_START',
  sla_hours: 24,
  metadata: {}
}
```

### 编辑条件节点

```typescript
const conditionNode: FlowNodeConfig = {
  id: 3,
  name: '金额判断',
  type: 'condition',
  approve_policy: 'any',
  route_mode: 'exclusive',
  allow_delegate: false,
  auto_approve_enabled: false,
  auto_sample_ratio: 0,
  reject_strategy: 'TO_START',
  condition_branches: {
    branches: [
      {
        priority: 1,
        label: '大额（>10000）',
        condition: {
          type: 'GROUP',
          logic: 'AND',
          children: [
            {
              type: 'RULE',
              field: 'amount',
              operator: 'GT',
              value: 10000
            }
          ]
        },
        target_node_id: 4
      },
      {
        priority: 2,
        label: '小额（<=10000）',
        condition: {
          type: 'GROUP',
          logic: 'AND',
          children: [
            {
              type: 'RULE',
              field: 'amount',
              operator: 'LTE',
              value: 10000
            }
          ]
        },
        target_node_id: 5
      }
    ],
    default_target_node_id: 5
  },
  metadata: {}
}
```

## Props

| 属性 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `node` | `FlowNodeConfig \| undefined` | 否 | 当前编辑的节点 |
| `allNodes` | `FlowNodeConfig[]` | 否 | 所有节点列表（用于条件分支的目标节点选择） |
| `formSchema` | `FormSchema` | 否 | 表单 schema（用于条件构造器） |
| `formId` | `number` | 否 | 表单 ID（用于加载表单字段） |
| `disabled` | `boolean` | 否 | 是否禁用编辑（默认 false） |

## Events

### update-node

当节点属性发生变化时触发。

```typescript
emit('update-node', {
  key: string,           // 节点的 ID 或 temp_id
  patch: Partial<FlowNodeConfig>  // 更新的属性补丁
})
```

**示例：**

```typescript
const handleNodeUpdate = (payload: { key: string; patch: Partial<FlowNodeConfig> }) => {
  const { key, patch } = payload
  // 更新节点
  const nodeIndex = nodes.value.findIndex(n => (n.id?.toString() ?? n.temp_id) === key)
  if (nodeIndex >= 0) {
    nodes.value[nodeIndex] = { ...nodes.value[nodeIndex], ...patch }
  }
}
```

## 节点类型说明

### start（开始节点）
- 流程的起点
- 不需要配置审批人
- 不支持驳回策略

### user（人工审批节点）
- 需要人工审批
- 支持所有审批配置
- 支持驳回策略

### condition（条件分支节点）
- 根据条件分支流程
- 需要配置条件分支
- 不需要配置审批人

### auto（自动节点）
- 自动执行的节点
- 支持自动审批配置
- 不需要人工干预

### end（结束节点）
- 流程的终点
- 不需要配置审批人
- 不支持驳回策略

## 审批人类型说明

| 类型 | 说明 |
|------|------|
| `user` | 指定具体用户 |
| `group` | 指定用户群组 |
| `role` | 指定角色 |
| `department` | 指定部门 |
| `position` | 指定岗位 |
| `expr` | 使用表达式动态指定 |

## 会签策略说明

| 策略 | 说明 |
|------|------|
| `any` | 任意一人同意即可通过 |
| `all` | 全部人员同意才能通过 |
| `percent` | 按指定比例同意即可通过 |

## 驳回策略说明

| 策略 | 说明 |
|------|------|
| `TO_START` | 驳回到流程发起人 |
| `TO_PREVIOUS` | 驳回到上一个审批节点 |

## 路由模式说明

| 模式 | 说明 |
|------|------|
| `exclusive` | 互斥路由，只能走一条分支 |
| `parallel` | 并行路由，可以同时走多条分支 |

## 样式定制

组件使用 scoped CSS，主要样式类：

- `.flow-node-editor` - 根容器
- `.editor-header` - 头部区域
- `.editor-body` - 主体内容区域
- `.editor-empty` - 空状态

## 集成示例

### 在流程设计器中使用

```vue
<template>
  <div class="flow-designer">
    <div class="canvas-area">
      <FlowCanvas
        :nodes="nodes"
        :routes="routes"
        @select-node="selectedNodeId = $event"
      />
    </div>
    
    <div class="inspector-area">
      <FlowNodeEditor
        :node="selectedNode"
        :all-nodes="nodes"
        :form-id="formId"
        @update-node="handleNodeUpdate"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import FlowCanvas from './FlowCanvas.vue'
import FlowNodeEditor from './FlowNodeEditor.vue'
import type { FlowNodeConfig } from '@/types/flow'

const nodes = ref<FlowNodeConfig[]>([])
const routes = ref([])
const formId = ref(1)
const selectedNodeId = ref<number | string | null>(null)

const selectedNode = computed(() => {
  if (!selectedNodeId.value) return undefined
  return nodes.value.find(n => (n.id?.toString() ?? n.temp_id) === selectedNodeId.value?.toString())
})

const handleNodeUpdate = (payload: { key: string; patch: Partial<FlowNodeConfig> }) => {
  const { key, patch } = payload
  const nodeIndex = nodes.value.findIndex(n => (n.id?.toString() ?? n.temp_id) === key)
  if (nodeIndex >= 0) {
    nodes.value[nodeIndex] = { ...nodes.value[nodeIndex], ...patch }
  }
}
</script>
```

## 测试

组件包含完整的单元测试和集成测试：

```bash
# 运行单元测试
npm run test:run -- src/components/flow-designer/__tests__/FlowNodeEditor.test.ts

# 运行集成测试
npm run test:run -- src/components/flow-designer/__tests__/FlowNodeEditorIntegration.test.ts

# 运行所有测试
npm run test:run
```

## 常见问题

### Q: 如何在条件节点中添加新的分支？
A: 条件分支的编辑由 `ConditionNodeEditor` 子组件处理。当节点类型为 `condition` 时，会自动显示条件编辑器。

### Q: 如何验证节点配置的有效性？
A: 组件本身不进行验证，验证应该在父组件或后端进行。建议在保存前进行以下检查：
- 审批节点必须指定审批人类型
- 条件节点必须至少有一个分支
- 所有目标节点必须存在

### Q: 如何处理节点的临时 ID？
A: 组件会自动处理节点的 ID 和 temp_id。在发送更新事件时，会使用 `id?.toString() ?? temp_id` 作为节点的唯一标识。

### Q: 如何禁用编辑？
A: 设置 `disabled` prop 为 `true` 即可禁用所有输入。

## 相关组件

- `FlowCanvas` - 流程画布组件
- `ConditionNodeEditor` - 条件节点编辑器
- `ConditionBuilderV2` - 条件构造器
- `FlowNodeInspector` - 节点检查器（旧版本）

## 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本
- 支持所有节点类型的编辑
- 支持条件分支配置
- 支持驳回策略配置
- 完整的单元测试和集成测试
