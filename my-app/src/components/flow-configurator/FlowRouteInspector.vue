<template>
  <div class="route-inspector">
    <div class="inspector-header">
      <div class="title">路由属性</div>
      <div class="subtitle">配置路由优先级和 JsonLogic 条件</div>
    </div>

    <div v-if="routeComputed" class="inspector-body">
      <n-form label-width="88" label-placement="left" size="small">
        <n-form-item label="来源节点">
          <n-select
            :value="routeComputed?.from_node_key ?? ''"
            :options="nodeOptions"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ from_node_key: val })"
          />
        </n-form-item>

        <n-form-item label="目标节点">
          <n-select
            :value="routeComputed?.to_node_key ?? ''"
            :options="nodeOptions"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ to_node_key: val })"
          />
        </n-form-item>

        <n-form-item label="优先级">
          <n-input-number
            :value="routeComputed?.priority ?? 1"
            :min="1"
            :max="999"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ priority: val ?? routeComputed?.priority ?? 1 })"
          />
        </n-form-item>

        <n-form-item label="默认路由">
          <n-switch
            :value="routeComputed?.is_default ?? false"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ is_default: val })"
          />
        </n-form-item>

        <n-divider>条件设置</n-divider>

        <n-space align="center" justify="space-between">
          <span class="condition-tip">JsonLogic 条件（暂用 JSON 文本）</span>
          <n-button quaternary size="small" disabled>可视化编排（即将上线）</n-button>
        </n-space>

        <n-form-item :feedback="conditionError" :validation-status="conditionError ? 'error' : undefined">
          <n-input
            type="textarea"
            :value="conditionDraft"
            :autosize="{ minRows: 4, maxRows: 10 }"
            placeholder='{"and": [{"==": [{"var": "amount"}, 100]}]}'
            :disabled="disabled"
            @update:value="(val) => (conditionDraft = val)"
            @blur="handleConditionBlur"
          />
        </n-form-item>
      </n-form>
    </div>
    <div v-else class="inspector-empty">
      <n-empty description="请选择一条路由" size="small" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

interface Props {
  route?: FlowRouteConfig
  nodeOptions: { label: string; value: string }[]
  selectedIndex: number | null
  disabled?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update-route', payload: { index: number; patch: Partial<FlowRouteConfig> }): void
}>()

const routeComputed = computed(() => props.route)
const conditionDraft = ref('')
const conditionError = ref('')

watch(
  () => routeComputed.value,
  (route) => {
    if (!route) {
      conditionDraft.value = ''
      conditionError.value = ''
      return
    }
    conditionDraft.value = route.condition ? JSON.stringify(route.condition, null, 2) : ''
    conditionError.value = ''
  },
  { immediate: true }
)

const emitPatch = (patch: Partial<FlowRouteConfig>) => {
  if (props.selectedIndex === null || props.selectedIndex === undefined) return
  emit('update-route', { index: props.selectedIndex, patch })
}

const handleConditionBlur = () => {
  if (props.selectedIndex === null || props.selectedIndex === undefined) return
  const content = conditionDraft.value.trim()
  if (!content) {
    conditionError.value = ''
    emitPatch({ condition: null })
    return
  }
  try {
    const parsed = JSON.parse(content)
    conditionError.value = ''
    emitPatch({ condition: parsed })
  } catch (error) {
    conditionError.value = 'JsonLogic JSON 格式错误，请检查语法'
  }
}
</script>

<style scoped>
.route-inspector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.inspector-header .title {
  font-size: 14px;
  font-weight: 600;
}

.inspector-header .subtitle {
  font-size: 12px;
  color: #6b7385;
}

.inspector-body {
  flex: 1;
  overflow-y: auto;
}

.inspector-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 160px;
}

.condition-tip {
  font-size: 12px;
  color: #6b7385;
}
</style>
