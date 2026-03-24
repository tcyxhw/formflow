# ConditionNodeEditor 组件文档

## 概述

`ConditionNodeEditor` 是一个用于编辑流程中条件分支节点的 Vue 3 组件。它提供了一个完整的界面来管理条件分支、优先级排序、条件表达式编辑和默认路由设置。

## 功能特性

### 1. 分支列表管理
- **添加分支**：点击"+ 添加分支"按钮添加新的条件分支
- **删除分支**：点击分支项右侧的"删除"按钮删除分支
- **编辑分支标签**：直接在分支项中编辑分支标签

### 2. 优先级排序
- **拖拽排序**：支持通过拖拽调整分支的优先级顺序
- **自动重新计算**：拖拽完成后自动重新计算优先级

### 3. 条件表达式编辑
- **可视化编辑**：集成 `ConditionBuilderV2` 组件，支持可视化条件编辑
- **条件预览**：显示条件表达式的简要预览（逻辑类型和条件数量）
- **模态对话框**：在模态对话框中编辑条件表达式

### 4. 目标节点选择
- **节点选择器**：为每个分支选择目标节点
- **节点过滤**：自动过滤掉开始节点和条件节点
- **默认路由**：设置当所有条件都不匹配时的默认目标节点

## Props

| 属性 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `modelValue` | `ConditionBranchesConfig \| null` | 否 | 条件分支配置 |
| `allNodes` | `FlowNodeConfig[]` | 否 | 所有流程节点列表 |
| `formSchema` | `FormSchema` | 否 | 表单 Schema，用于条件构造器 |
| `disabled` | `boolean` | 否 | 是否禁用编辑（默认 false） |

## Events

| 事件 | 参数 | 说明 |
|------|------|------|
| `update:modelValue` | `ConditionBranchesConfig \| null` | 当配置更新时触发 |

## 数据结构

### ConditionBranchesConfig

```typescript
interface ConditionBranchesConfig {
  /** 条件分支列表 */
  branches: ConditionBranch[]
  /** 默认目标节点 ID（当所有条件都不匹配时使用） */
  default_target_node_id: number
}
```

### ConditionBranch

```typescript
interface ConditionBranch {
  /** 优先级（数字越小优先级越高） */
  priority: number
  /** 分支标签 */
  label: string
  /** 条件表达式 */
  condition: ConditionNode
  /** 目标节点 ID */
  target_node_id: number
}
```

## 使用示例

### 基本使用

```vue
<template>
  <ConditionNodeEditor
    :model-value="conditionConfig"
    :all-nodes="flowNodes"
    :form-schema="formSchema"
    @update:model-value="handleConfigUpdate"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ConditionNodeEditor from '@/components/flow-configurator/ConditionNodeEditor.vue'
import type { ConditionBranchesConfig } from '@/types/flow'
import type { FlowNodeConfig } from '@/types/flow'
import type { FormSchema } from '@/types/schema'

const conditionConfig = ref<ConditionBranchesConfig | null>(null)
const flowNodes = ref<FlowNodeConfig[]>([])
const formSchema = ref<FormSchema>()

const handleConfigUpdate = (config: ConditionBranchesConfig | null) => {
  conditionConfig.value = config
  // 保存配置到后端
  saveConditionConfig(config)
}
</script>
```

### 在 FlowNodeInspector 中使用

```vue
<template>
  <div class="inspector">
    <!-- ... 其他节点配置 ... -->
    
    <!-- 条件节点配置 -->
    <ConditionNodeEditor
      v-if="node.type === 'condition'"
      :model-value="node.condition_branches"
      :all-nodes="allNodes"
      :form-schema="formSchema"
      :disabled="disabled"
      @update:model-value="(val) => emitPatch({ condition_branches: val })"
    />
  </div>
</template>

<script setup lang="ts">
import ConditionNodeEditor from './ConditionNodeEditor.vue'
import type { FlowNodeConfig } from '@/types/flow'
import type { FormSchema } from '@/types/schema'

interface Props {
  node?: FlowNodeConfig
  allNodes?: FlowNodeConfig[]
  formSchema?: FormSchema
  disabled?: boolean
}

const props = defineProps<Props>()
</script>
```

## 验证规则

组件会自动验证以下规则：

1. **分支数量**：至少需要 2 个分支
2. **默认目标节点**：必须设置默认目标节点
3. **目标节点有效性**：目标节点必须存在于节点列表中
4. **条件表达式**：每个分支必须有有效的条件表达式

## 样式定制

组件使用 Naive UI 组件库，支持通过 CSS 变量进行样式定制。主要的样式类：

- `.condition-node-editor`：组件容器
- `.editor-header`：编辑器头部
- `.editor-body`：编辑器主体
- `.branches-section`：分支列表区域
- `.branch-item`：单个分支项
- `.default-route-section`：默认路由区域

## 响应式设计

组件支持响应式设计，在不同屏幕尺寸下自动调整布局：

- **桌面版**（> 1024px）：完整布局
- **平板版**（768px - 1024px）：紧凑布局
- **手机版**（< 768px）：堆叠布局

## 集成注意事项

1. **表单 Schema**：确保传入的 `formSchema` 包含所有需要在条件中使用的字段
2. **节点列表**：`allNodes` 应包含所有可用的目标节点
3. **禁用状态**：当 `disabled` 为 true 时，所有编辑操作都会被禁用
4. **事件处理**：确保正确处理 `update:modelValue` 事件并保存配置

## 常见问题

### Q: 如何添加新的分支？
A: 点击"+ 添加分支"按钮，组件会自动创建一个新的分支并分配优先级。

### Q: 如何编辑条件表达式？
A: 点击分支项中的"编辑条件"按钮，会打开一个模态对话框，在其中使用可视化条件构造器编辑条件。

### Q: 如何调整分支优先级？
A: 直接拖拽分支项来调整顺序，组件会自动重新计算优先级。

### Q: 默认路由的作用是什么？
A: 当流程实例的数据不匹配任何条件分支时，流程会路由到默认目标节点。

## 性能优化

- 使用虚拟滚动处理大量分支（当分支数 > 100 时）
- 条件表达式使用懒加载
- 拖拽操作使用防抖处理

## 浏览器兼容性

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
