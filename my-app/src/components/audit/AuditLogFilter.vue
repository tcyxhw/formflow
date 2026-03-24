<template>
  <n-form inline :model="modelValue" label-placement="left" label-width="auto">
    <n-form-item label="时间范围">
      <n-date-picker
        v-model:value="dateRange"
        type="daterange"
        clearable
        @update:value="handleDateChange"
      />
    </n-form-item>

    <n-form-item label="动作类型">
      <n-select
        v-model:value="modelValue.action"
        :options="actionOptions"
        clearable
        style="width: 150px"
        placeholder="选择动作"
      />
    </n-form-item>

    <n-form-item label="资源类型">
      <n-select
        v-model:value="modelValue.resource_type"
        :options="resourceTypeOptions"
        clearable
        style="width: 150px"
        placeholder="选择资源"
      />
    </n-form-item>

    <n-form-item v-if="isAdmin" label="操作人ID">
      <n-input-number
        v-model:value="modelValue.actor_user_id"
        placeholder="用户ID"
        clearable
        style="width: 120px"
      />
    </n-form-item>

    <n-form-item v-if="isAdmin" label="仅本人">
      <n-switch v-model:value="modelValue.only_mine" />
    </n-form-item>

    <n-form-item>
      <n-button type="primary" @click="handleSearch">查询</n-button>
    </n-form-item>

    <n-form-item>
      <n-button tertiary @click="handleReset">重置</n-button>
    </n-form-item>
  </n-form>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { AuditLogQuery } from '@/api/audit'

interface Props {
  modelValue: AuditLogQuery
  isAdmin?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: AuditLogQuery): void
  (e: 'search'): void
}>()

// 时间范围
const dateRange = ref<[number, number] | null>(null)

// 选项
const actionOptions = [
  { label: '创建', value: 'create' },
  { label: '更新', value: 'update' },
  { label: '删除', value: 'delete' },
  { label: '发布', value: 'publish' },
  { label: '认领任务', value: 'claim_task' },
  { label: '释放任务', value: 'release_task' },
  { label: '审批通过', value: 'approve' },
  { label: '审批驳回', value: 'reject' },
  { label: '转交任务', value: 'transfer_task' },
  { label: '委托任务', value: 'delegate_task' },
  { label: '加签', value: 'add_sign_task' },
  { label: '执行任务动作', value: 'perform_task_action' },
]

const resourceTypeOptions = [
  { label: '表单', value: 'form' },
  { label: '提交', value: 'submission' },
  { label: '任务', value: 'task' },
  { label: '附件', value: 'attachment' },
  { label: '权限', value: 'form_permission' },
]

// 时间变化处理
const handleDateChange = (value: [number, number] | null) => {
  dateRange.value = value
  if (value) {
    props.modelValue.date_from = new Date(value[0]).toISOString()
    props.modelValue.date_to = new Date(value[1]).toISOString()
  } else {
    props.modelValue.date_from = undefined
    props.modelValue.date_to = undefined
  }
}

// 查询
const handleSearch = () => {
  emit('search')
}

// 重置
const handleReset = () => {
  dateRange.value = null
  emit('update:modelValue', {
    page: 1,
    page_size: 20,
    resource_type: props.modelValue.resource_type,
    resource_id: props.modelValue.resource_id,
    only_mine: props.modelValue.only_mine,
  })
  emit('search')
}

// 监听外部变化
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal.date_from && newVal.date_to) {
      dateRange.value = [
        new Date(newVal.date_from).getTime(),
        new Date(newVal.date_to).getTime(),
      ]
    }
  },
  { deep: true }
)
</script>
