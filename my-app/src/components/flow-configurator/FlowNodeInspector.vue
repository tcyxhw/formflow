<template>
  <div class="inspector">
    <div class="inspector-header">
      <div class="title">节点属性</div>
      <div class="subtitle">配置审批策略与自动化参数</div>
    </div>

    <div v-if="node" class="inspector-body">
      <n-form label-placement="left" label-width="88" size="small">
        <n-form-item label="节点名称">
          <n-input
            :value="node.name"
            placeholder="请输入节点名称"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ name: val })"
          />
        </n-form-item>

        <n-form-item label="节点类型">
          <n-select
            :value="node.type"
            :options="nodeTypeOptions"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ type: val as FlowNodeType })"
          />
        </n-form-item>

        <n-form-item label="负责人类型">
          <n-select
            :value="node.assignee_type"
            :options="assigneeOptions"
            :disabled="disabled"
            placeholder="暂未指定"
            @update:value="(val) => emitPatch({ assignee_type: val as FlowAssigneeType })"
          />
        </n-form-item>

        <n-form-item label="审批策略">
          <n-select
            :value="node.approve_policy"
            :options="approvePolicyOptions"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ approve_policy: val as FlowApprovePolicy })"
          />
        </n-form-item>

        <n-form-item v-if="node.approve_policy === 'percent'" label="通过阈值">
          <n-input-number
            :value="node.approve_threshold ?? 50"
            :min="1"
            :max="100"
            :disabled="disabled"
            suffix="%"
            @update:value="(val) => emitPatch({ approve_threshold: val ?? undefined })"
          />
        </n-form-item>

        <n-form-item label="SLA(小时)">
          <n-input-number
            :value="node.sla_hours ?? undefined"
            :min="1"
            :max="720"
            placeholder="可选"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ sla_hours: val ?? undefined })"
          />
        </n-form-item>

        <n-form-item label="允许代理">
          <n-switch
            :value="node.allow_delegate"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ allow_delegate: val })"
          />
        </n-form-item>

        <n-divider>自动审批</n-divider>

        <n-form-item label="启用自动">
          <n-switch
            :value="node.auto_approve_enabled"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ auto_approve_enabled: val })"
          />
        </n-form-item>

        <n-form-item label="抽检比例">
          <n-slider
            :value="Math.round((node.auto_sample_ratio ?? 0) * 100)"
            :step="5"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ auto_sample_ratio: +(val / 100).toFixed(2) })"
          />
        </n-form-item>

        <n-alert type="info" :bordered="false">
          条件编辑器将在下一步接入，当前可在节点详情中配置核心策略。
        </n-alert>
      </n-form>
    </div>

    <div v-else class="inspector-empty">
      <n-empty description="请选择画布中的节点" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type {
  FlowApprovePolicy,
  FlowAssigneeType,
  FlowNodeConfig,
  FlowNodeType
} from '@/types/flow'

interface Props {
  node?: FlowNodeConfig
  disabled?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update-node', payload: { key: string; patch: Partial<FlowNodeConfig> }): void
}>()

const nodeTypeOptions = computed(() => [
  { label: '开始', value: 'start' },
  { label: '人工审批', value: 'user' },
  { label: '自动节点', value: 'auto' },
  { label: '结束', value: 'end' }
])

const assigneeOptions = computed(() => [
  { label: '用户', value: 'user' },
  { label: '群组', value: 'group' },
  { label: '角色', value: 'role' },
  { label: '部门', value: 'department' },
  { label: '岗位', value: 'position' },
  { label: '表达式', value: 'expr' }
])

const approvePolicyOptions = computed(() => [
  { label: '任意一人', value: 'any' },
  { label: '全部同意', value: 'all' },
  { label: '自定义比例', value: 'percent' }
])

const resolveNodeKey = (node: FlowNodeConfig): string | undefined => {
  return node.id?.toString() ?? node.temp_id ?? undefined
}

const emitPatch = (patch: Partial<FlowNodeConfig>) => {
  if (!props.node) return
  const key = resolveNodeKey(props.node)
  if (!key) return
  emit('update-node', { key, patch })
}
</script>

<style scoped>
.inspector {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.inspector-header {
  margin-bottom: 12px;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.subtitle {
  font-size: 12px;
  color: #6b7385;
}

.inspector-body {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.inspector-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
