# Workspace Components

工作区相关组件，用于表单填写工作区功能。

## FilterPanel 组件

筛选面板组件，提供表单状态、类别和时间范围筛选功能。

### 功能特性

- ✅ 状态筛选（待填写、进行中、已截止）
- ✅ 类别筛选（动态类别选项）
- ✅ 时间范围筛选（创建时间）
- ✅ 清除所有筛选按钮
- ✅ 应用筛选按钮
- ✅ 使用 Naive UI 组件（Select、DatePicker、Button）
- ✅ 双向绑定支持（v-model）
- ✅ TypeScript 类型安全

### Props

| 属性 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| modelValue | FilterState | 是 | - | 筛选状态对象 |
| categories | string[] | 否 | [] | 可选的类别列表 |

### Events

| 事件名 | 参数 | 说明 |
|--------|------|------|
| update:modelValue | FilterState | 筛选条件变化时触发 |
| apply | - | 点击"应用筛选"按钮时触发 |

### 使用示例

```vue
<template>
  <div class="workspace">
    <!-- 筛选面板 -->
    <FilterPanel
      v-model="filters"
      :categories="['学生信息', '教师信息', '课程管理']"
      @apply="loadForms"
    />
    
    <!-- 表单列表 -->
    <div v-if="loading">加载中...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <FormCard
        v-for="form in forms"
        :key="form.id"
        :form="form"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useFillWorkspace } from '@/composables/useFillWorkspace'
import FilterPanel from '@/components/workspace/FilterPanel.vue'
import FormCard from '@/components/workspace/FormCard.vue'

const {
  forms,
  loading,
  error,
  filters,
  loadForms
} = useFillWorkspace()

// 初始加载
loadForms()
</script>
```

### FilterState 类型定义

```typescript
interface FilterState {
  keyword: string
  status: string | null
  category: string | null
  sortBy: string
  sortOrder: 'asc' | 'desc'
  dateRange?: { start: string; end: string } | null
}
```

### 状态选项

组件内置以下状态选项：

- `pending` - 待填写
- `active` - 进行中
- `expired` - 已截止

### 样式定制

组件使用 Naive UI 的主题变量，支持通过主题配置进行样式定制：

- `--n-color` - 背景色
- `--n-text-color` - 文本颜色

## SearchBar 组件

搜索栏组件，提供实时搜索功能。

（详见 SearchBar.vue）

## 相关文件

- `FilterPanel.vue` - 筛选面板组件
- `SearchBar.vue` - 搜索栏组件
- `@/types/workspace.ts` - 工作区类型定义
- `@/composables/useFillWorkspace.ts` - 工作区组合函数
- `@/api/workspace.ts` - 工作区 API 接口
