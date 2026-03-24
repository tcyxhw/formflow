<template>
  <div class="flow-node-editor">
    <!-- 头部 -->
    <div class="editor-header">
      <div class="title">节点编辑器</div>
      <div class="subtitle">配置节点属性和审批策略</div>
    </div>

    <!-- 主体内容 -->
    <div v-if="node" class="editor-body">
      <n-form label-placement="left" label-width="100" size="small">
        <!-- 基本信息 -->
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

        <!-- 审批人配置（非条件节点） -->
        <template v-if="node.type !== 'condition' && node.type !== 'start' && node.type !== 'end'">
          <n-divider>审批人配置</n-divider>

          <n-form-item label="审批人类型">
            <n-select
              :value="node.assignee_type"
              :options="assigneeTypeOptions"
              :disabled="disabled"
              placeholder="选择审批人类型"
              @update:value="(val) => emitPatch({ assignee_type: val as FlowAssigneeType })"
            />
          </n-form-item>

          <n-form-item label="会签策略">
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

          <n-form-item label="允许代理">
            <n-switch
              :value="node.allow_delegate"
              :disabled="disabled"
              @update:value="(val) => emitPatch({ allow_delegate: val })"
            />
          </n-form-item>

          <!-- 驳回策略 -->
          <n-divider>驳回策略</n-divider>

          <n-form-item label="驳回策略">
            <n-select
              :value="node.reject_strategy"
              :options="rejectStrategyOptions"
              :disabled="disabled"
              @update:value="(val) => emitPatch({ reject_strategy: val as RejectStrategy })"
            />
          </n-form-item>

          <!-- SLA 配置 -->
          <n-divider>SLA 配置</n-divider>

          <n-form-item label="SLA 时长(小时)">
            <n-input-number
              :value="node.sla_hours ?? undefined"
              :min="1"
              :max="720"
              placeholder="可选"
              :disabled="disabled"
              @update:value="(val) => emitPatch({ sla_hours: val ?? undefined })"
            />
          </n-form-item>

          <!-- 自动审批 -->
          <n-divider>自动审批</n-divider>

          <n-form-item label="启用自动审批">
            <n-switch
              :value="node.auto_approve_enabled"
              :disabled="disabled"
              @update:value="(val) => emitPatch({ auto_approve_enabled: val })"
            />
          </n-form-item>

          <n-form-item v-if="node.auto_approve_enabled" label="抽检比例">
            <n-slider
              :value="Math.round((node.auto_sample_ratio ?? 0) * 100)"
              :step="5"
              :disabled="disabled"
              @update:value="(val) => emitPatch({ auto_sample_ratio: +(val / 100).toFixed(2) })"
            />
          </n-form-item>
        </template>

        <!-- 条件分支配置（条件节点） -->
        <template v-if="node.type === 'condition'">
          <n-divider>条件分支配置</n-divider>

          <ConditionNodeEditor
            :model-value="node.condition_branches"
            :all-nodes="allNodes"
            :form-schema="formSchema"
            :form-id="formId"
            :disabled="disabled"
            @update:model-value="(val) => emitPatch({ condition_branches: val })"
          />
        </template>

        <!-- 路由模式 -->
        <n-divider>路由模式</n-divider>

        <n-form-item label="路由模式">
          <n-select
            :value="node.route_mode"
            :options="routeModeOptions"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ route_mode: val as FlowRouteMode })"
          />
        </n-form-item>
      </n-form>
    </div>

    <!-- 空状态 -->
    <div v-else class="editor-empty">
      <n-empty description="请选择节点进行编辑" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NForm, NFormItem, NInput, NSelect, NSwitch, NInputNumber, NSlider, NDivider, NEmpty } from 'naive-ui'
import ConditionNodeEditor from '../flow-configurator/ConditionNodeEditor.vue'
import type {
  FlowNodeConfig,
  FlowNodeType,
  FlowAssigneeType,
  FlowApprovePolicy,
  FlowRouteMode,
  RejectStrategy
} from '@/types/flow'
import type { FormSchema } from '@/types/schema'

interface Props {
  node?: FlowNodeConfig
  allNodes?: FlowNodeConfig[]
  formSchema?: FormSchema
  formId?: number
  disabled?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update-node', payload: { key: string; patch: Partial<FlowNodeConfig> }): void
}>()

// 节点类型选项
const nodeTypeOptions = computed(() => [
  { label: '开始', value: 'start' },
  { label: '人工审批', value: 'user' },
  { label: '条件分支', value: 'condition' },
  { label: '自动节点', value: 'auto' },
  { label: '结束', value: 'end' }
])

// 审批人类型选项
const assigneeTypeOptions = computed(() => [
  { label: '用户', value: 'user' },
  { label: '群组', value: 'group' },
  { label: '角色', value: 'role' },
  { label: '部门', value: 'department' },
  { label: '岗位', value: 'position' },
  { label: '表达式', value: 'expr' }
])

// 会签策略选项
const approvePolicyOptions = computed(() => [
  { label: '任意一人', value: 'any' },
  { label: '全部同意', value: 'all' },
  { label: '自定义比例', value: 'percent' }
])

// 驳回策略选项
const rejectStrategyOptions = computed(() => [
  { label: '驳回到发起人', value: 'TO_START' },
  { label: '驳回到上一个审批节点', value: 'TO_PREVIOUS' }
])

// 路由模式选项
const routeModeOptions = computed(() => [
  { label: '互斥', value: 'exclusive' },
  { label: '并行', value: 'parallel' }
])

// 获取节点 key
const resolveNodeKey = (node: FlowNodeConfig): string | undefined => {
  return node.id?.toString() ?? node.temp_id ?? undefined
}

// 发送补丁更新
const emitPatch = (patch: Partial<FlowNodeConfig>) => {
  if (!props.node) return
  const key = resolveNodeKey(props.node)
  if (!key) return
  emit('update-node', { key, patch })
}
</script>

<style scoped>
.flow-node-editor {
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
</style>
