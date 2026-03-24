<template>
  <div class="filter-panel">
    <n-space vertical :size="16">
      <!-- 状态筛选 -->
      <div class="filter-item">
        <label class="filter-label">表单状态</label>
        <n-select
          v-model:value="localFilters.status"
          :options="statusOptions"
          placeholder="选择状态"
          clearable
          @update:value="handleFilterChange"
        />
      </div>

      <!-- 类别筛选 -->
      <div class="filter-item">
        <label class="filter-label">表单类别</label>
        <n-select
          v-model:value="localFilters.category"
          :options="categoryOptions"
          placeholder="选择类别"
          clearable
          @update:value="handleFilterChange"
        />
      </div>

      <!-- 时间范围筛选 -->
      <div class="filter-item">
        <label class="filter-label">创建时间</label>
        <n-date-picker
          v-model:value="dateRange"
          type="daterange"
          clearable
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          @update:value="handleDateRangeChange"
        />
      </div>

      <!-- 操作按钮 -->
      <n-space justify="end">
        <n-button @click="handleClearAll">
          清除所有筛选
        </n-button>
        <n-button type="primary" @click="handleApply">
          应用筛选
        </n-button>
      </n-space>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { NSpace, NSelect, NDatePicker, NButton } from 'naive-ui'
import type { FilterState } from '@/types/workspace'

interface Props {
  modelValue: FilterState
  categories?: string[]
}

interface Emits {
  (e: 'update:modelValue', value: FilterState): void
  (e: 'apply'): void
}

const props = withDefaults(defineProps<Props>(), {
  categories: () => []
})

const emit = defineEmits<Emits>()

// 本地筛选状态
const localFilters = ref<FilterState>({ ...props.modelValue })

// 日期范围（用于DatePicker的双向绑定）
const dateRange = ref<[number, number] | null>(null)

// 状态选项
const statusOptions = [
  { label: '待填写', value: 'pending' },
  { label: '进行中', value: 'active' },
  { label: '已截止', value: 'expired' }
]

// 类别选项（动态生成）
const categoryOptions = computed(() => {
  return props.categories.map(cat => ({
    label: cat,
    value: cat
  }))
})

// 监听外部modelValue变化
watch(
  () => props.modelValue,
  (newValue) => {
    localFilters.value = { ...newValue }
  },
  { deep: true }
)

// 处理筛选条件变化
const handleFilterChange = () => {
  emit('update:modelValue', { ...localFilters.value })
}

// 处理日期范围变化
const handleDateRangeChange = (value: [number, number] | null) => {
  if (value) {
    // 将时间戳转换为ISO字符串（仅日期部分）
    const startDate = new Date(value[0]).toISOString().split('T')[0]
    const endDate = new Date(value[1]).toISOString().split('T')[0]
    localFilters.value.dateRange = { start: startDate, end: endDate }
  } else {
    localFilters.value.dateRange = null
  }
  handleFilterChange()
}

// 清除所有筛选
const handleClearAll = () => {
  localFilters.value = {
    keyword: '',
    status: null,
    category: null,
    sortBy: 'created_at',
    sortOrder: 'desc',
    dateRange: null
  }
  dateRange.value = null
  emit('update:modelValue', { ...localFilters.value })
  emit('apply')
}

// 应用筛选
const handleApply = () => {
  emit('apply')
}
</script>

<style scoped>
.filter-panel {
  padding: 16px;
  background-color: var(--n-color);
  border-radius: 4px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--n-text-color);
}
</style>
