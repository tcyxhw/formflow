<template>
  <div class="flow-route-editor">
    <!-- 头部 -->
    <div class="editor-header">
      <div class="title">路由编辑器</div>
      <div class="subtitle">配置路由条件、优先级和默认路由</div>
    </div>

    <!-- 主体内容 -->
    <div v-if="route" class="editor-body">
      <n-form label-placement="left" label-width="100" size="small">
        <!-- 基本信息 -->
        <n-form-item label="来源节点">
          <n-select
            :value="route.from_node_key"
            :options="fromNodeOptions"
            :disabled="disabled"
            placeholder="选择来源节点"
            @update:value="(val) => emitPatch({ from_node_key: val })"
          />
        </n-form-item>

        <n-form-item label="目标节点">
          <n-select
            :value="route.to_node_key"
            :options="toNodeOptions"
            :disabled="disabled"
            placeholder="选择目标节点"
            @update:value="(val) => emitPatch({ to_node_key: val })"
          />
        </n-form-item>

        <n-form-item label="优先级">
          <n-input-number
            :value="route.priority"
            :min="1"
            :max="999"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ priority: val ?? 1 })"
          />
        </n-form-item>

        <!-- 条件表达式编辑 -->
        <n-divider>条件表达式</n-divider>

        <div class="condition-editor-section">
          <div class="condition-editor-header">
            <span class="label">条件配置</span>
            <n-switch
              :value="showConditionBuilder"
              :disabled="disabled"
              @update:value="(val) => (showConditionBuilder = val)"
            />
          </div>

          <div v-if="showConditionBuilder" class="condition-builder-wrapper">
            <ConditionBuilderV2
              :model-value="route.condition"
              :form-schema="formSchema"
              :form-id="formId"
              :disabled="disabled"
              @update:model-value="(val) => emitPatch({ condition: val })"
            />
          </div>

          <div v-else class="condition-preview">
            <span class="preview-label">当前条件：</span>
            <span class="preview-text">{{ formatConditionPreview(route.condition) }}</span>
          </div>
        </div>

        <!-- 默认路由设置 -->
        <n-divider>默认路由</n-divider>

        <n-form-item label="是否默认路由">
          <n-switch
            :value="route.is_default"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ is_default: val })"
          />
        </n-form-item>

        <div v-if="route.is_default" class="default-route-hint">
          <n-alert type="info" closable>
            此路由将作为默认路由，当所有其他条件都不匹配时使用
          </n-alert>
        </div>
      </n-form>
    </div>

    <!-- 空状态 -->
    <div v-else class="editor-empty">
      <n-empty description="请选择路由进行编辑" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { NForm, NFormItem, NSelect, NSwitch, NInputNumber, NDivider, NEmpty, NAlert } from 'naive-ui'
import ConditionBuilderV2 from '../flow-configurator/ConditionBuilderV2.vue'
import type { FlowRouteConfig, FlowNodeConfig } from '@/types/flow'
import type { FormSchema } from '@/types/schema'
import type { ConditionNode } from '@/types/condition'

interface Props {
  route?: FlowRouteConfig
  allNodes?: FlowNodeConfig[]
  formSchema?: FormSchema
  formId?: number
  disabled?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update-route', payload: { key: string; patch: Partial<FlowRouteConfig> }): void
}>()

const showConditionBuilder = ref(false)

// 计算属性：来源节点选项
const fromNodeOptions = computed(() => {
  return (props.allNodes || [])
    .map(node => ({
      label: node.name,
      value: node.id?.toString() || node.temp_id || '',
    }))
    .filter(opt => opt.value)
})

// 计算属性：目标节点选项
const toNodeOptions = computed(() => {
  return (props.allNodes || [])
    .filter(node => node.id?.toString() !== props.route?.from_node_key && node.temp_id !== props.route?.from_node_key)
    .map(node => ({
      label: node.name,
      value: node.id?.toString() || node.temp_id || '',
    }))
    .filter(opt => opt.value)
})

// 获取路由 key
const resolveRouteKey = (route: FlowRouteConfig): string | undefined => {
  return route.id?.toString() ?? route.temp_id ?? undefined
}

// 发送补丁更新
const emitPatch = (patch: Partial<FlowRouteConfig>) => {
  if (!props.route) return
  const key = resolveRouteKey(props.route)
  if (!key) return
  emit('update-route', { key, patch })
}

// 格式化条件预览
const formatConditionPreview = (condition: ConditionNode | undefined | null): string => {
  if (!condition || condition.type !== 'GROUP') {
    return '未设置'
  }
  const group = condition
  if (group.children.length === 0) {
    return '未设置'
  }
  return `${group.logic} (${group.children.length} 个条件)`
}

// 监听 route 变化，重置条件编辑器显示状态
watch(
  () => props.route,
  () => {
    showConditionBuilder.value = false
  }
)
</script>

<style scoped>
.flow-route-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e0e5ec;
  overflow: hidden;
}

.editor-header {
  padding: 20px 24px;
  background: linear-gradient(135deg, #f6fbf8 0%, #f0f6ff 100%);
  border-bottom: 1px solid #e0e5ec;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.subtitle {
  font-size: 12px;
  color: #6b7385;
  margin-top: 4px;
}

.editor-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.editor-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.n-form) {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

:deep(.n-form-item) {
  margin-bottom: 0;
}

:deep(.n-divider) {
  margin: 16px 0 12px 0;
}

.condition-editor-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: #f9fbfc;
  border-radius: 6px;
  border: 1px solid #e0e5ec;
}

.condition-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}

.condition-builder-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.condition-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  padding: 8px 12px;
  background: #ffffff;
  border-radius: 4px;
  border: 1px solid #e0e5ec;
}

.preview-label {
  color: #6b7385;
  font-weight: 500;
}

.preview-text {
  color: #1f2937;
  font-family: 'Monaco', 'Menlo', monospace;
}

.default-route-hint {
  margin-top: 12px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .editor-header {
    padding: 16px 20px;
  }

  .editor-body {
    padding: 20px;
  }

  .title {
    font-size: 15px;
  }

  .subtitle {
    font-size: 11px;
  }

  .condition-editor-section {
    padding: 12px;
  }
}

@media (max-width: 768px) {
  .editor-header {
    padding: 12px 16px;
  }

  .editor-body {
    padding: 16px;
  }

  .title {
    font-size: 14px;
  }

  .subtitle {
    font-size: 10px;
  }

  .condition-editor-section {
    padding: 10px;
  }

  .condition-editor-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
