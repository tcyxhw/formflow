<template>
  <div class="auto-condition-editor">
    <!-- 头部 -->
    <div class="editor-header">
      <div class="header-icon">①</div>
      <div class="header-content">
        <div class="title">{{ title }}</div>
        <div class="subtitle">{{ subtitle }}</div>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="editor-body">
      <!-- 已添加的条件 -->
      <div v-if="hasConditions" class="conditions-section">
        <div class="section-header">
          <span class="section-title">已添加的条件</span>
          <span class="condition-count">共 {{ conditionCount }} 个</span>
        </div>

        <div class="conditions-list">
          <div v-for="(condition, index) in flattenedConditions" :key="index" class="condition-item">
            <div class="condition-content">
              <span class="condition-text">{{ condition.text }}</span>
            </div>
            <div class="condition-actions">
              <n-button text type="primary" size="small" @click="editCondition(index)">
                编辑
              </n-button>
              <n-button text type="error" size="small" @click="deleteCondition(index)">
                删除
              </n-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 添加新条件 -->
      <div class="add-condition-section">
        <div class="section-header">
          <span class="section-title">{{ hasConditions ? '添加新条件' : '添加条件' }}</span>
        </div>

        <div class="condition-builder-wrapper">
          <ConditionBuilderV2
            :model-value="builderCondition"
            :form-schema="formSchema"
            :form-id="formId"
            :disabled="disabled"
            @update:model-value="(val) => (builderCondition = val)"
          />
        </div>

        <div class="add-actions">
          <n-button type="primary" size="small" :disabled="disabled || !canAddCondition" @click="addCondition">
            + 添加条件
          </n-button>
          <n-button v-if="hasConditions" size="small" :disabled="disabled" @click="addConditionGroup">
            + 添加条件组
          </n-button>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="editor-footer">
      <n-button size="small" @click="emit('cancel')">取消</n-button>
      <n-button type="primary" size="small" :disabled="disabled" @click="saveAll">
        保存所有条件
      </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { NButton } from 'naive-ui'
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
  background: #ffffff;
  border-radius: 8px;
  overflow: hidden;
  min-height: 400px;
}

.editor-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #f6fbf8 0%, #f0f6ff 100%);
  border-bottom: 1px solid #e0e5ec;
}

.header-icon {
  width: 32px;
  height: 32px;
  background: #18a058;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
}

.subtitle {
  font-size: 13px;
  color: #6b7385;
}

.editor-body {
  flex: 1;
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
  margin-bottom: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.condition-count {
  font-size: 13px;
  color: #6b7385;
  background: #f0f0f0;
  padding: 2px 10px;
  border-radius: 10px;
}

.conditions-section {
  display: flex;
  flex-direction: column;
}

.conditions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.condition-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f9fbfc;
  border: 1px solid #e0e5ec;
  border-radius: 6px;
}

.condition-content {
  flex: 1;
}

.condition-text {
  font-size: 13px;
  color: #1f2937;
  font-family: 'Monaco', 'Menlo', monospace;
}

.condition-actions {
  display: flex;
  gap: 12px;
}

.add-condition-section {
  display: flex;
  flex-direction: column;
  padding: 16px;
  background: #f9fbfc;
  border: 1px solid #e0e5ec;
  border-radius: 6px;
}

.condition-builder-wrapper {
  margin-bottom: 16px;
}

.add-actions {
  display: flex;
  gap: 12px;
}

.editor-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  background: #f9fbfc;
  border-top: 1px solid #e0e5ec;
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

  .condition-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .condition-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .editor-footer {
    padding: 12px 16px;
  }
}
</style>
