# 节点模板库 (NodeTemplateLibrary)

## 概述

节点模板库是一个预定义节点配置的集合，用于快速创建常见的审批流程节点。用户可以通过搜索、分类筛选等方式快速找到合适的模板，并一键应用到流程设计器中。

## 功能特性

### 1. 内置模板库
- **审批类模板** (6+)
  - 经理审批：由直属经理进行审批
  - 部门负责人审批：由部门负责人进行审批
  - 并行审批：多人并行审批，任意一人同意即可
  - 全部同意审批：多人审批，全部同意才能通过
  - 比例审批：多人审批，达到指定比例即可通过
  - 带 SLA 的审批：带有时限的审批节点
  - 自动抽检审批：启用自动抽检的审批节点

- **条件分支模板** (3+)
  - 金额条件分支：根据金额进行条件分支
  - 部门条件分支：根据部门进行条件分支
  - 用户类型条件分支：根据用户类型进行条件分支

- **自动节点模板** (2+)
  - 自动通知：自动发送邮件或短信通知
  - 自动 Webhook：调用外部系统的 Webhook 接口

### 2. 搜索功能
- 按模板名称搜索
- 按模板描述搜索
- 按模板 ID 搜索
- 不区分大小写

### 3. 分类筛选
- 按分类筛选（审批、条件、自动等）
- 支持多分类组织
- 快速切换分类

### 4. 模板预览
- 查看模板详细信息
- 查看模板配置（JSON 格式）
- 预览后可直接应用

### 5. 模板应用
- 一键应用模板
- 自动填充节点配置
- 支持自定义修改

## 使用方式

### 基本使用

```vue
<template>
  <NodeTemplateLibrary
    :disabled="false"
    @apply-template="handleApplyTemplate"
  />
</template>

<script setup lang="ts">
import NodeTemplateLibrary from '@/components/flow-designer/NodeTemplateLibrary.vue'
import type { NodeTemplate } from '@/types/nodeTemplate'

const handleApplyTemplate = (template: NodeTemplate) => {
  // 使用模板创建新节点
  const newNode = {
    ...template.config,
    name: template.config.name || template.name,
    temp_id: `node_${Date.now()}`
  }
  // 添加到流程设计器
}
</script>
```

### 搜索模板

```typescript
// 按名称搜索
searchQuery.value = '经理'

// 按描述搜索
searchQuery.value = '审批'

// 清空搜索
searchQuery.value = ''
```

### 按分类筛选

```typescript
// 筛选审批类模板
selectedCategory.value = 'approval'

// 筛选条件分支模板
selectedCategory.value = 'condition'

// 清除筛选
selectedCategory.value = null
```

### 预览模板

```typescript
// 预览模板
selectTemplate(template)

// 关闭预览
showPreview.value = false
```

### 应用模板

```typescript
// 应用模板
applyTemplate(template)

// 监听应用事件
@apply-template="handleApplyTemplate"
```

## API 参考

### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| disabled | boolean | false | 是否禁用 |

### Events

| 事件 | 参数 | 说明 |
|------|------|------|
| apply-template | template: NodeTemplate | 应用模板时触发 |

### 类型定义

```typescript
interface NodeTemplate {
  id: string                          // 模板 ID
  name: string                        // 模板名称
  description: string                 // 模板描述
  type: FlowNodeType                  // 节点类型
  category: NodeTemplateCategory      // 模板分类
  config: Partial<FlowNodeConfig>     // 模板配置
  icon?: string                       // 图标
  isBuiltin: boolean                  // 是否为系统内置模板
  usageCount?: number                 // 使用次数
  createdAt?: string                  // 创建时间
  lastUsedAt?: string                 // 最后使用时间
}
```

## 内置模板详情

### 审批类模板

#### 经理审批 (approval-manager)
- **类型**: 人工审批
- **审批人**: 角色（经理）
- **会签策略**: 全部同意
- **允许代理**: 是
- **驳回策略**: 驳回到发起人

#### 并行审批 (approval-parallel)
- **类型**: 人工审批
- **审批人**: 群组
- **会签策略**: 任意一人
- **路由模式**: 并行
- **允许代理**: 是

#### 比例审批 (approval-percent)
- **类型**: 人工审批
- **审批人**: 群组
- **会签策略**: 自定义比例（66%）
- **路由模式**: 并行
- **允许代理**: 是

#### 带 SLA 的审批 (approval-with-sla)
- **类型**: 人工审批
- **SLA 时长**: 24 小时
- **审批人**: 角色（经理）
- **会签策略**: 全部同意

#### 自动抽检审批 (approval-auto-sample)
- **类型**: 人工审批
- **自动审批**: 启用
- **抽检比例**: 10%
- **审批人**: 角色（经理）

### 条件分支模板

#### 金额条件分支 (condition-amount)
- **类型**: 条件分支
- **用途**: 根据表单中的金额字段进行条件分支

#### 部门条件分支 (condition-department)
- **类型**: 条件分支
- **用途**: 根据表单中的部门字段进行条件分支

### 自动节点模板

#### 自动通知 (auto-notification)
- **类型**: 自动节点
- **用途**: 自动发送邮件或短信通知

#### 自动 Webhook (auto-webhook)
- **类型**: 自动节点
- **用途**: 调用外部系统的 Webhook 接口

## 工具函数

### getTemplatesByCategory(category: string)
获取指定分类的所有模板

```typescript
import { getTemplatesByCategory } from '@/constants/nodeTemplates'

const approvalTemplates = getTemplatesByCategory('approval')
```

### getTemplatesByType(type: string)
获取指定类型的所有模板

```typescript
import { getTemplatesByType } from '@/constants/nodeTemplates'

const userTemplates = getTemplatesByType('user')
```

### getAllCategories()
获取所有可用分类

```typescript
import { getAllCategories } from '@/constants/nodeTemplates'

const categories = getAllCategories()
// ['approval', 'condition', 'auto', 'other']
```

### getTemplateById(id: string)
根据 ID 获取模板

```typescript
import { getTemplateById } from '@/constants/nodeTemplates'

const template = getTemplateById('approval-manager')
```

## 集成示例

### 在 FlowNodeEditor 中集成

```vue
<template>
  <div class="node-editor-with-templates">
    <n-tabs>
      <n-tab-pane name="editor" tab="编辑器">
        <FlowNodeEditor
          :node="selectedNode"
          @update-node="handleUpdateNode"
        />
      </n-tab-pane>
      <n-tab-pane name="templates" tab="模板库">
        <NodeTemplateLibrary
          @apply-template="handleApplyTemplate"
        />
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FlowNodeEditor from './FlowNodeEditor.vue'
import NodeTemplateLibrary from './NodeTemplateLibrary.vue'
import type { NodeTemplate } from '@/types/nodeTemplate'

const selectedNode = ref(null)

const handleApplyTemplate = (template: NodeTemplate) => {
  // 创建新节点
  selectedNode.value = {
    ...template.config,
    temp_id: `node_${Date.now()}`
  }
}

const handleUpdateNode = (payload: any) => {
  // 更新节点
}
</script>
```

## 测试覆盖

- ✅ 模板库初始化
- ✅ 模板搜索功能
- ✅ 模板分类筛选
- ✅ 模板预览
- ✅ 模板应用
- ✅ 模板配置验证
- ✅ 模板元数据
- ✅ 组合搜索和筛选
- ✅ 完整工作流
- ✅ 性能测试

**测试覆盖率**: > 85%

## 性能指标

- 模板过滤: < 100ms
- 分类切换: < 100ms
- 模板预览: 即时
- 模板应用: 即时

## 扩展性

### 添加自定义模板

```typescript
// 在 nodeTemplates.ts 中添加
const CUSTOM_TEMPLATES: NodeTemplate[] = [
  {
    id: 'custom-approval',
    name: '自定义审批',
    description: '自定义审批模板',
    type: 'user',
    category: 'approval',
    isBuiltin: false,
    config: {
      // 自定义配置
    }
  }
]
```

### 从后端加载模板

```typescript
// 创建 API 接口
export async function loadNodeTemplates() {
  const response = await axios.get('/api/v1/node-templates')
  return response.data.templates
}

// 在组件中使用
const templates = ref<NodeTemplate[]>([])

onMounted(async () => {
  templates.value = await loadNodeTemplates()
})
```

## 常见问题

### Q: 如何添加新的模板？
A: 在 `nodeTemplates.ts` 中的 `BUILTIN_NODE_TEMPLATES` 数组中添加新的模板对象。

### Q: 如何自定义模板配置？
A: 修改模板的 `config` 属性，包含所有需要的节点配置。

### Q: 如何跟踪模板使用情况？
A: 在应用模板时，可以记录 `usageCount` 和 `lastUsedAt` 字段。

### Q: 如何支持用户自定义模板？
A: 创建后端 API 来保存和加载用户自定义模板，然后在组件中合并内置模板和自定义模板。

## 相关文件

- `src/types/nodeTemplate.ts` - 类型定义
- `src/constants/nodeTemplates.ts` - 模板常量和工具函数
- `src/components/flow-designer/NodeTemplateLibrary.vue` - 组件实现
- `src/components/flow-designer/__tests__/NodeTemplateLibrary.test.ts` - 单元测试
- `src/components/flow-designer/__tests__/NodeTemplateLibraryIntegration.test.ts` - 集成测试
