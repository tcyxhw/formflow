<template>
  <div class="condition-node-editor">
    <!-- 头部 -->
    <div class="editor-header">
      <div class="title">条件分支配置</div>
      <div class="subtitle">配置条件分支、优先级和默认路由</div>
    </div>

    <!-- 主体内容 -->
    <div class="editor-body">
      <!-- 分支列表 -->
      <div class="branches-section">
        <div class="section-header">
          <span class="section-title">分支列表</span>
          <n-button
            type="primary"
            size="small"
            :disabled="disabled"
            @click="addBranch"
          >
            + 添加分支
          </n-button>
        </div>

        <div v-if="branches.length === 0" class="empty-state">
          <n-empty description="暂无分支，点击上方按钮添加" size="small" />
        </div>

        <div v-else class="branches-list">
          <!-- 拖拽排序提示 -->
          <div class="sort-hint">
            <n-icon size="16">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="9" cy="5" r="1"></circle>
                <circle cx="9" cy="12" r="1"></circle>
                <circle cx="9" cy="19" r="1"></circle>
                <circle cx="20" cy="5" r="1"></circle>
                <circle cx="20" cy="12" r="1"></circle>
                <circle cx="20" cy="19" r="1"></circle>
              </svg>
            </n-icon>
            <span>拖拽调整优先级</span>
          </div>

          <!-- 分支项 -->
          <draggable
            v-model="branches"
            :disabled="disabled"
            class="branches-draggable"
            item-key="priority"
            @change="onBranchesReorder"
          >
            <template #item="{ element: branch, index }">
              <div class="branch-item">
                <div class="branch-header">
                  <div class="branch-info">
                    <span class="priority-badge">{{ index + 1 }}</span>
                    <n-input
                      :value="branch.label"
                      placeholder="分支标签"
                      size="small"
                      :disabled="disabled"
                      @update:value="(val) => updateBranch(index, { label: val })"
                    />
                  </div>
                  <div class="branch-actions">
                    <n-button
                      text
                      type="primary"
                      size="small"
                      :disabled="disabled"
                      @click="editBranch(index)"
                    >
                      编辑条件
                    </n-button>
                    <n-popconfirm
                      :disabled="disabled"
                      @positive-click="deleteBranch(index)"
                    >
                      <template #trigger>
                        <n-button
                          text
                          type="error"
                          size="small"
                          :disabled="disabled"
                        >
                          删除
                        </n-button>
                      </template>
                      确定删除此分支吗？
                    </n-popconfirm>
                  </div>
                </div>

                <!-- 条件预览 -->
                <div class="condition-preview">
                  <span class="preview-label">条件：</span>
                  <span class="preview-text">{{ formatConditionPreview(branch.condition) }}</span>
                </div>

                <!-- 目标节点 -->
                <div class="target-node">
                  <span class="label">目标节点：</span>
                  <n-select
                    :value="branch.target_node_id"
                    :options="nodeOptions"
                    size="small"
                    :disabled="disabled"
                    placeholder="选择目标节点"
                    @update:value="(val) => updateBranch(index, { target_node_id: val })"
                  />
                </div>
              </div>
            </template>
          </draggable>
        </div>
      </div>

      <!-- 默认路由 -->
      <div class="default-route-section">
        <div class="section-header">
          <span class="section-title">默认路由</span>
        </div>
        <div class="default-route-content">
          <span class="label">当所有条件都不匹配时，路由到：</span>
          <n-select
            :value="defaultTargetNodeId"
            :options="nodeOptions"
            size="small"
            :disabled="disabled"
            placeholder="选择默认目标节点"
            @update:value="(val) => updateDefaultTarget(val)"
          />
        </div>
      </div>
    </div>

    <!-- 条件编辑对话框 -->
    <n-modal
      v-model:show="showConditionModal"
      title="编辑条件表达式"
      preset="dialog"
      size="large"
      :mask-closable="false"
      @positive-click="saveCondition"
      @negative-click="cancelCondition"
    >
      <div class="condition-modal-content">
        <ConditionBuilderV2
          :model-value="editingCondition"
          :form-schema="formSchema"
          :form-id="formId"
          :disabled="disabled"
          @update:model-value="(val) => (editingCondition = val)"
        />
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { NButton, NInput, NSelect, NEmpty, NIcon, NPopconfirm, NModal } from 'naive-ui'
import draggable from 'vuedraggable'
import ConditionBuilderV2 from './ConditionBuilderV2.vue'
import type { ConditionBranch, ConditionBranchesConfig, ConditionNode } from '@/types/condition'
import type { FlowNodeConfig } from '@/types/flow'
import type { FormSchema } from '@/types/schema'
import type { FormField } from '@/types/field'

interface Props {
  modelValue?: ConditionBranchesConfig | null
  allNodes?: FlowNodeConfig[]
  formSchema?: FormSchema
  formId?: number
  disabled?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: ConditionBranchesConfig | null): void
}>()

// 本地状态
const branches = ref<ConditionBranch[]>([])
const defaultTargetNodeId = ref<number | null>(null)
const showConditionModal = ref(false)
const editingBranchIndex = ref<number | null>(null)
const editingCondition = ref<ConditionNode | null>(null)

// 计算属性
const nodeOptions = computed(() => {
  return (props.allNodes || [])
    .filter(node => node.type !== 'start' && node.type !== 'condition')
    .map(node => ({
      label: node.name,
      value: node.id || node.temp_id || '',
    }))
    .filter(opt => opt.value)
})

// 初始化
watch(
  () => props.modelValue,
  (value) => {
    if (value) {
      branches.value = [...value.branches].sort((a, b) => a.priority - b.priority)
      defaultTargetNodeId.value = value.default_target_node_id
    } else {
      branches.value = []
      defaultTargetNodeId.value = null
    }
  },
  { immediate: true }
)

// 方法
const addBranch = () => {
  const newPriority = branches.value.length > 0
    ? Math.max(...branches.value.map(b => b.priority)) + 1
    : 1

  branches.value.push({
    priority: newPriority,
    label: `分支 ${branches.value.length + 1}`,
    condition: { type: 'GROUP', logic: 'AND', children: [] },
    target_node_id: 0,
  })

  emitUpdate()
}

const updateBranch = (index: number, patch: Partial<ConditionBranch>) => {
  if (index >= 0 && index < branches.value.length) {
    branches.value[index] = { ...branches.value[index], ...patch }
    emitUpdate()
  }
}

const deleteBranch = (index: number) => {
  branches.value.splice(index, 1)
  emitUpdate()
}

const editBranch = (index: number) => {
  editingBranchIndex.value = index
  editingCondition.value = branches.value[index].condition
  showConditionModal.value = true
}

const saveCondition = () => {
  if (editingBranchIndex.value !== null && editingCondition.value) {
    updateBranch(editingBranchIndex.value, { condition: editingCondition.value })
  }
  showConditionModal.value = false
  editingBranchIndex.value = null
  editingCondition.value = null
}

const cancelCondition = () => {
  showConditionModal.value = false
  editingBranchIndex.value = null
  editingCondition.value = null
}

const updateDefaultTarget = (nodeId: number | null) => {
  defaultTargetNodeId.value = nodeId
  emitUpdate()
}

const onBranchesReorder = () => {
  // 重新计算优先级
  branches.value.forEach((branch, index) => {
    branch.priority = index + 1
  })
  emitUpdate()
}

const formatConditionPreview = (condition: ConditionNode): string => {
  if (!condition || condition.type !== 'GROUP') {
    return '未设置'
  }
  const group = condition
  if (group.children.length === 0) {
    return '未设置'
  }
  return `${group.logic} (${group.children.length} 个条件)`
}

const emitUpdate = () => {
  if (branches.value.length === 0 || defaultTargetNodeId.value === null) {
    emit('update:modelValue', null)
    return
  }

  const config: ConditionBranchesConfig = {
    branches: branches.value,
    default_target_node_id: defaultTargetNodeId.value,
  }
  emit('update:modelValue', config)
}
</script>

<style scoped>
.condition-node-editor {
  display: flex;
  flex-direction: column;
  gap: 0;
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
  font-weight: 700;
  color: #1f2937;
}

.subtitle {
  font-size: 13px;
  color: #6b7385;
  margin-top: 4px;
}

.editor-body {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px;
  overflow-y: auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.branches-section {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.empty-state {
  padding: 32px 16px;
  text-align: center;
}

.sort-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #6b7385;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f9fbfc;
  border-radius: 4px;
}

.branches-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.branches-draggable {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.branch-item {
  padding: 16px;
  background: #f9fbfc;
  border: 1px solid #e0e5ec;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.branch-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.branch-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.priority-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: #e8f5e9;
  color: #2e7d32;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.branch-actions {
  display: flex;
  gap: 8px;
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

.target-node {
  display: flex;
  align-items: center;
  gap: 12px;
}

.label {
  font-size: 12px;
  color: #6b7385;
  font-weight: 500;
  white-space: nowrap;
}

.target-node :deep(.n-select) {
  flex: 1;
}

.default-route-section {
  padding: 16px;
  background: #f0f6ff;
  border: 1px solid #b3d8ff;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.default-route-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.default-route-content :deep(.n-select) {
  flex: 1;
}

.condition-modal-content {
  padding: 16px 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .editor-header {
    padding: 16px 20px;
  }

  .editor-body {
    padding: 20px;
    gap: 20px;
  }

  .title {
    font-size: 15px;
  }

  .subtitle {
    font-size: 12px;
  }

  .branch-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .branch-actions {
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 768px) {
  .editor-header {
    padding: 12px 16px;
  }

  .editor-body {
    padding: 16px;
    gap: 16px;
  }

  .title {
    font-size: 14px;
  }

  .subtitle {
    font-size: 11px;
  }

  .branch-item {
    padding: 12px;
  }

  .branch-info {
    gap: 8px;
  }

  .priority-badge {
    width: 24px;
    height: 24px;
    font-size: 11px;
  }

  .condition-preview {
    font-size: 11px;
    padding: 6px 10px;
  }

  .target-node {
    flex-direction: column;
    align-items: flex-start;
  }

  .default-route-content {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
