<template>
  <div class="auto-condition-editor">
    <!-- 头部 -->
    <div class="editor-header">
      <div class="header-icon">
        <n-icon size="24">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 11l3 3L22 4"/>
            <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
          </svg>
        </n-icon>
      </div>
      <div class="header-content">
        <div class="title">{{ title }}</div>
        <div class="subtitle">{{ subtitle }}</div>
      </div>
    </div>

    <!-- 主体内容 - 左右分栏 -->
    <div class="editor-body">
      <!-- 左侧：条件列表 -->
      <div class="left-panel">
        <div class="panel-header">
          <span class="panel-title">
            <n-icon size="18" class="panel-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
              </svg>
            </n-icon>
            已添加的条件
          </span>
          <n-tag v-if="conditionCount > 0" type="success" size="small">{{ conditionCount }} 个</n-tag>
          <n-tag v-else type="default" size="small">无</n-tag>
        </div>

        <div class="panel-content">
          <div v-if="!hasConditions" class="empty-state">
            <n-empty description="暂无条件" size="small">
              <template #icon>
                <n-icon size="48" depth="3">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <path d="M9 12l2 2 4-4"/>
                  </svg>
                </n-icon>
              </template>
            </n-empty>
            <p class="empty-tip">请在右侧配置条件</p>
          </div>

          <div v-else class="conditions-list">
            <div
              v-for="(condition, index) in flattenedConditions"
              :key="index"
              class="condition-card"
              :class="{ 'is-group': condition.node.type === 'GROUP' }"
            >
              <div class="condition-number">{{ index + 1 }}</div>
              <div class="condition-info">
                <div class="condition-text">{{ condition.text }}</div>
                <div v-if="condition.node.type === 'GROUP'" class="condition-meta">
                  {{ condition.node.logic === 'AND' ? '全部满足' : '任意满足' }}
                </div>
              </div>
              <div class="condition-actions">
                <n-button quaternary circle size="small" type="primary" @click="editCondition(index)">
                  <template #icon>
                    <n-icon size="16">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                      </svg>
                    </n-icon>
                  </template>
                </n-button>
                <n-button quaternary circle size="small" type="error" @click="deleteCondition(index)">
                  <template #icon>
                    <n-icon size="16">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                      </svg>
                    </n-icon>
                  </template>
                </n-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：条件构建器 -->
      <div class="right-panel">
        <div class="panel-header">
          <span class="panel-title">
            <n-icon size="18" class="panel-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
              </svg>
            </n-icon>
            {{ hasConditions ? '添加新条件' : '配置条件' }}
          </span>
        </div>

        <div class="panel-content">
          <div class="builder-wrapper">
            <div class="builder-container">
              <ConditionBuilderV2
                :model-value="builderCondition"
                :form-schema="formSchema"
                :form-id="formId"
                :disabled="disabled"
                @update:model-value="(val) => (builderCondition = val)"
              />
            </div>

            <div class="builder-actions">
              <n-button
                type="primary"
                size="large"
                :disabled="disabled || !canAddCondition"
                @click="addCondition"
              >
                <template #icon>
                  <n-icon size="18">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="12" y1="5" x2="12" y2="19"/>
                      <line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                  </n-icon>
                </template>
                添加到列表
              </n-button>
              <n-button
                v-if="hasConditions"
                size="large"
                :disabled="disabled || !canAddCondition"
                @click="addConditionGroup"
              >
                <template #icon>
                  <n-icon size="18">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <rect x="3" y="3" width="18" height="18" rx="2"/>
                      <line x1="12" y1="8" x2="12" y2="16"/>
                      <line x1="8" y1="12" x2="16" y2="12"/>
                    </svg>
                  </n-icon>
                </template>
                添加为条件组
              </n-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="editor-footer">
      <n-button size="large" @click="emit('cancel')">取消</n-button>
      <n-button type="primary" size="large" :disabled="disabled" @click="saveAll">
        <template #icon>
          <n-icon size="18">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
              <polyline points="17 21 17 13 7 13 7 21"/>
              <polyline points="7 3 7 8 15 8"/>
            </svg>
          </n-icon>
        </template>
        保存所有条件
      </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { NButton, NIcon, NEmpty, NTag } from 'naive-ui'
import ConditionBuilderV2 from './ConditionBuilderV2.vue'
import type { ConditionNode, ConditionRule, ConditionGroup } from '@/types/condition'
import type { FormSchema } from '@/types/schema'

interface Props {
  modelValue?: ConditionNode | null
  title?: string
  subtitle?: string
  formSchema?: FormSchema
  formId?: number
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '编辑自动审批条件',
  subtitle: '配置表单字段的条件规则，支持多条件组合',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: ConditionNode | null): void
  (e: 'save'): void
  (e: 'cancel'): void
}>()

// 本地状态
const rootGroup = ref<ConditionGroup>({
  type: 'GROUP',
  logic: 'AND',
  children: [],
})

const builderCondition = ref<ConditionNode | null>(null)

// 计算属性
const hasConditions = computed(() => rootGroup.value.children.length > 0)

const conditionCount = computed(() => rootGroup.value.children.length)

const canAddCondition = computed(() => {
  if (!builderCondition.value) return false
  if (builderCondition.value.type === 'RULE') {
    return !!builderCondition.value.fieldKey && !!builderCondition.value.operator
  }
  if (builderCondition.value.type === 'GROUP') {
    return builderCondition.value.children.length > 0
  }
  return false
})

// 扁平化条件列表用于展示
const flattenedConditions = computed(() => {
  return rootGroup.value.children.map((child, index) => {
    if (child.type === 'RULE') {
      return {
        index,
        text: formatRuleText(child),
        node: child,
      }
    } else {
      return {
        index,
        text: formatGroupText(child),
        node: child,
      }
    }
  })
})

// 初始化
watch(
  () => props.modelValue,
  (value) => {
    if (value && value.type === 'GROUP') {
      rootGroup.value = { ...value }
    } else if (value && value.type === 'RULE') {
      rootGroup.value = {
        type: 'GROUP',
        logic: 'AND',
        children: [value],
      }
    } else {
      rootGroup.value = {
        type: 'GROUP',
        logic: 'AND',
        children: [],
      }
    }
  },
  { immediate: true }
)

// 方法
const formatRuleText = (rule: ConditionRule): string => {
  const operatorMap: Record<string, string> = {
    'EQUALS': '等于',
    'NOT_EQUALS': '不等于',
    'GREATER_THAN': '大于',
    'GREATER_EQUAL': '大于等于',
    'LESS_THAN': '小于',
    'LESS_EQUAL': '小于等于',
    'BETWEEN': '介于',
    'CONTAINS': '包含',
    'NOT_CONTAINS': '不包含',
    'IN': '属于',
    'NOT_IN': '不属于',
    'HAS_ANY': '包含任意',
    'HAS_ALL': '包含全部',
    'IS_EMPTY': '为空',
    'IS_NOT_EMPTY': '不为空',
  }
  const operatorText = operatorMap[rule.operator] || rule.operator
  const valueText = Array.isArray(rule.value) ? rule.value.join(', ') : String(rule.value ?? '')
  return `${rule.fieldKey} ${operatorText} ${valueText}`
}

const formatGroupText = (group: ConditionGroup): string => {
  const logicText = group.logic === 'AND' ? '且' : '或'
  const childTexts = group.children.map((child) => {
    if (child.type === 'RULE') {
      return formatRuleText(child)
    }
    return '子条件组'
  })
  return childTexts.join(` ${logicText} `)
}

const addCondition = () => {
  if (!builderCondition.value) return

  if (builderCondition.value.type === 'GROUP') {
    // 如果是组，将子条件添加到根组
    rootGroup.value.children.push(...builderCondition.value.children)
  } else {
    // 如果是单条规则，直接添加
    rootGroup.value.children.push(builderCondition.value)
  }

  // 重置构建器
  builderCondition.value = null
  emitUpdate()
}

const addConditionGroup = () => {
  if (!builderCondition.value) return

  // 创建一个新的条件组
  const newGroup: ConditionGroup = {
    type: 'GROUP',
    logic: 'AND',
    children: [],
  }

  if (builderCondition.value.type === 'GROUP') {
    newGroup.children.push(...builderCondition.value.children)
  } else {
    newGroup.children.push(builderCondition.value)
  }

  rootGroup.value.children.push(newGroup)

  // 重置构建器
  builderCondition.value = null
  emitUpdate()
}

const editCondition = (index: number) => {
  const condition = rootGroup.value.children[index]
  if (condition) {
    builderCondition.value = { ...condition }
    // 删除原条件
    rootGroup.value.children.splice(index, 1)
    emitUpdate()
  }
}

const deleteCondition = (index: number) => {
  rootGroup.value.children.splice(index, 1)
  emitUpdate()
}

const saveAll = () => {
  emit('save')
}

const emitUpdate = () => {
  if (rootGroup.value.children.length === 0) {
    emit('update:modelValue', null)
  } else if (rootGroup.value.children.length === 1) {
    emit('update:modelValue', rootGroup.value.children[0])
  } else {
    emit('update:modelValue', rootGroup.value)
  }
}
</script>

<style scoped>
.auto-condition-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8fafc;
  overflow: hidden;
}

/* 头部样式 */
.editor-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.header-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.3;
}

.subtitle {
  font-size: 13px;
  color: #64748b;
  line-height: 1.4;
}

/* 主体内容 - 左右分栏 */
.editor-body {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px 24px;
  overflow: hidden;
  min-height: 0;
}

/* 左右面板通用样式 */
.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  min-height: 0;
}

/* 左侧面板：固定宽度 */
.left-panel {
  width: 360px;
  flex-shrink: 0;
}

/* 右侧面板：自适应宽度 */
.right-panel {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.panel-icon {
  color: #10b981;
}

.panel-content {
  flex: 1;
  padding: 16px;
  overflow: hidden;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

/* 左侧：条件列表 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #94a3b8;
}

.empty-tip {
  margin-top: 12px;
  font-size: 13px;
  color: #94a3b8;
}

.conditions-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.condition-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.condition-card:hover {
  border-color: #10b981;
  background: #f0fdf4;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.1);
}

.condition-card.is-group {
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border-color: #a7f3d0;
}

.condition-number {
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.condition-info {
  flex: 1;
  min-width: 0;
}

.condition-text {
  font-size: 13px;
  color: #334155;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  word-break: break-word;
  line-height: 1.5;
}

.condition-meta {
  margin-top: 6px;
  font-size: 11px;
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-block;
}

.condition-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.condition-card:hover .condition-actions {
  opacity: 1;
}

/* 右侧：条件构建器 */
.builder-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.builder-container {
  flex: 1;
  background: #f8fafc;
  border-radius: 10px;
  padding: 16px;
  border: 1px solid #e2e8f0;
  overflow: auto;
  min-height: 0;
}

.builder-actions {
  display: flex;
  gap: 10px;
  padding: 12px 0 0 0;
  flex-shrink: 0;
  border-top: 1px solid #e2e8f0;
  margin-top: 12px;
}

/* 底部操作栏 */
.editor-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 24px;
  background: #ffffff;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .editor-body {
    flex-direction: column;
  }

  .left-panel,
  .right-panel {
    flex: none;
    width: 100%;
    height: 300px;
  }
}

@media (max-width: 768px) {
  .editor-header {
    padding: 16px 16px;
  }

  .header-icon {
    width: 40px;
    height: 40px;
  }

  .title {
    font-size: 16px;
  }

  .subtitle {
    font-size: 12px;
  }

  .editor-body {
    padding: 12px 16px;
    gap: 12px;
  }

  .left-panel {
    width: 100%;
  }

  .panel-header {
    padding: 12px 14px;
  }

  .panel-content {
    padding: 12px;
  }

  .condition-card {
    padding: 12px;
  }

  .condition-actions {
    opacity: 1;
  }

  .editor-footer {
    padding: 12px 16px;
  }
}
</style>
