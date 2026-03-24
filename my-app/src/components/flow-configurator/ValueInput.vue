<template>
  <div class="value-input">
    <!-- 文本输入 -->
    <n-input
      v-if="inputType === 'text'"
      :value="modelValue"
      placeholder="输入值"
      clearable
      @update:value="$emit('update:modelValue', $event)"
    />

    <!-- 数字输入 -->
    <n-input-number
      v-else-if="inputType === 'number'"
      :value="modelValue"
      placeholder="输入数字"
      clearable
      @update:value="$emit('update:modelValue', $event)"
    />

    <!-- 区间输入（两个数字） -->
    <div v-else-if="inputType === 'range'" class="range-input">
      <n-input-number
        :value="Array.isArray(modelValue) ? modelValue[0] : null"
        placeholder="最小值"
        clearable
        @update:value="updateRange(0, $event)"
      />
      <span class="range-separator">~</span>
      <n-input-number
        :value="Array.isArray(modelValue) ? modelValue[1] : null"
        placeholder="最大值"
        clearable
        @update:value="updateRange(1, $event)"
      />
    </div>

    <!-- 日期选择 -->
    <n-date-picker
      v-else-if="inputType === 'date'"
      :value="modelValue ? new Date(modelValue).getTime() : null"
      type="date"
      placeholder="选择日期"
      clearable
      @update:value="$emit('update:modelValue', $event ? new Date($event).toISOString().split('T')[0] : null)"
    />

    <!-- 日期时间选择 -->
    <n-date-picker
      v-else-if="inputType === 'datetime'"
      :value="modelValue ? new Date(modelValue).getTime() : null"
      type="datetime"
      placeholder="选择日期时间"
      clearable
      @update:value="$emit('update:modelValue', $event ? new Date($event).toISOString() : null)"
    />

    <!-- 日期范围选择 -->
    <n-date-picker
      v-else-if="inputType === 'dateRange'"
      :value="Array.isArray(modelValue) ? [new Date(modelValue[0]).getTime(), new Date(modelValue[1]).getTime()] : null"
      type="daterange"
      placeholder="选择日期范围"
      clearable
      @update:value="updateDateRange"
    />

    <!-- 下拉选择 -->
    <n-select
      v-else-if="inputType === 'select'"
      :value="modelValue"
      :options="selectOptions"
      placeholder="选择值"
      clearable
      @update:value="$emit('update:modelValue', $event)"
    />

    <!-- 多选 -->
    <n-select
      v-else-if="inputType === 'multiSelect'"
      :value="modelValue"
      :options="selectOptions"
      multiple
      placeholder="选择值"
      clearable
      @update:value="$emit('update:modelValue', $event)"
    />

    <!-- 人员选择（使用 Select 组件，后续可替换为真实的人员选择器） -->
    <n-select
      v-else-if="inputType === 'user'"
      :value="modelValue"
      :options="userOptions"
      placeholder="选择人员"
      filterable
      clearable
      @update:value="$emit('update:modelValue', $event)"
    />

    <!-- 人员多选 -->
    <n-select
      v-else-if="inputType === 'userMulti'"
      :value="modelValue"
      :options="userOptions"
      multiple
      placeholder="选择人员"
      filterable
      clearable
      @update:value="$emit('update:modelValue', $event)"
    />

    <!-- 部门选择（使用 Select 组件，后续可替换为真实的部门选择器） -->
    <n-select
      v-else-if="inputType === 'department'"
      :value="modelValue"
      :options="departmentOptions"
      placeholder="选择部门"
      filterable
      clearable
      @update:value="$emit('update:modelValue', $event)"
    />

    <!-- 部门多选 -->
    <n-select
      v-else-if="inputType === 'departmentMulti'"
      :value="modelValue"
      :options="departmentOptions"
      multiple
      placeholder="选择部门"
      filterable
      clearable
      @update:value="$emit('update:modelValue', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NInput, NInputNumber, NDatePicker, NSelect } from 'naive-ui'
import type { FieldType, Operator } from '@/types/condition'

interface Props {
  modelValue: any
  fieldType: FieldType
  operator: Operator
  selectOptions?: Array<{ label: string; value: string | number }>
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: any): void
}>()

// 根据字段类型和运算符确定输入类型
const inputType = computed(() => {
  // 空值判断不需要输入
  if (props.operator === 'IS_EMPTY' || props.operator === 'IS_NOT_EMPTY') {
    return 'none'
  }

  // 区间类型
  if (props.operator === 'BETWEEN') {
    if (props.fieldType === 'DATE' || props.fieldType === 'DATETIME') {
      return 'dateRange'
    }
    return 'range'
  }

  // 多值类型（IN, NOT_IN, HAS_ANY, HAS_ALL）
  if (['IN', 'NOT_IN', 'HAS_ANY', 'HAS_ALL'].includes(props.operator)) {
    if (props.fieldType === 'SINGLE_SELECT' || props.fieldType === 'MULTI_SELECT') {
      return 'multiSelect'
    }
    if (props.fieldType === 'USER') {
      return 'userMulti'
    }
    if (props.fieldType === 'DEPARTMENT') {
      return 'departmentMulti'
    }
    return 'multiSelect'
  }

  // 根据字段类型
  switch (props.fieldType) {
    case 'TEXT':
      return 'text'
    case 'NUMBER':
      return 'number'
    case 'DATE':
      return 'date'
    case 'DATETIME':
      return 'datetime'
    case 'SINGLE_SELECT':
      return 'select'
    case 'MULTI_SELECT':
      return 'multiSelect'
    case 'USER':
      return 'user'
    case 'DEPARTMENT':
      return 'department'
    default:
      return 'text'
  }
})

const selectOptions = computed(() => {
  return props.selectOptions || []
})

// 人员选项（模拟数据，后续可替换为真实的人员选择器 API）
const userOptions = computed(() => {
  return [
    { label: '张三', value: 101 },
    { label: '李四', value: 102 },
    { label: '王五', value: 103 },
    { label: '赵六', value: 104 },
    { label: '钱七', value: 105 },
  ]
})

// 部门选项（模拟数据，后续可替换为真实的部门选择器 API）
const departmentOptions = computed(() => {
  return [
    { label: '技术部', value: 'dept_tech' },
    { label: '产品部', value: 'dept_product' },
    { label: '运营部', value: 'dept_ops' },
    { label: '市场部', value: 'dept_marketing' },
    { label: '人力资源部', value: 'dept_hr' },
    { label: '财务部', value: 'dept_finance' },
    { label: '总裁办', value: 'dept_ceo' },
  ]
})

const updateRange = (index: number, value: number | null) => {
  const current = Array.isArray(props.modelValue) ? [...props.modelValue] : [null, null]
  current[index] = value
  emit('update:modelValue', current)
}

const updateDateRange = (value: [number, number] | null) => {
  if (!value) {
    emit('update:modelValue', null)
    return
  }
  const [start, end] = value
  emit('update:modelValue', [
    new Date(start).toISOString().split('T')[0],
    new Date(end).toISOString().split('T')[0],
  ])
}
</script>

<style scoped>
.value-input {
  width: 100%;
}

.range-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-input :deep(.n-input-number) {
  flex: 1;
}

.range-separator {
  color: #6b7385;
  font-weight: 500;
  flex-shrink: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .range-input {
    gap: 6px;
  }

  .range-separator {
    font-size: 12px;
  }
}
</style>
