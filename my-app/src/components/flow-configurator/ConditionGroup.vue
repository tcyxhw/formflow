<template>
  <div class="condition-group" :class="{ 'is-nested': isNested, [`depth-${nestingDepth}`]: isNested }">
    <!-- 组头：逻辑关系选择 -->
    <div class="group-header">
      <div class="header-left">
        <span v-if="isNested" class="group-label">条件组</span>
        <div class="logic-selector">
          <span class="logic-label">满足</span>
          <n-select
            :value="group.logic"
            :options="logicOptions"
            :disabled="disabled"
            class="logic-select"
            @update:value="updateLogic"
          />
          <span class="logic-label">条件</span>
        </div>
      </div>
      <div v-if="isNested" class="header-right">
        <n-button
          quaternary
          type="error"
          size="small"
          :disabled="disabled"
          @click="$emit('delete')"
          class="delete-group-btn"
        >
          × 删除组
        </n-button>
      </div>
    </div>

    <!-- 组内容 -->
    <div class="group-content">
      <!-- 规则列表 -->
      <div class="rules-list">
        <template v-for="(child, index) in group.children" :key="index">
          <!-- 规则 -->
          <div v-if="child.type === 'RULE'" class="rule-wrapper">
            <ConditionRule
              :rule="child"
              :fields="fields"
              :form-schema="formSchema"
              :disabled="disabled"
              @update="updateChild(index, $event)"
              @delete="deleteChild(index)"
            />
          </div>

          <!-- 嵌套组 -->
          <div v-else class="nested-group-wrapper">
            <ConditionGroup
              :group="child"
              :fields="fields"
              :form-schema="formSchema"
              :is-nested="true"
              :nesting-depth="nestingDepth + 1"
              :disabled="disabled"
              @update="updateChild(index, $event)"
              @delete="deleteChild(index)"
            />
          </div>

          <!-- 逻辑连接符 -->
          <div v-if="index < group.children.length - 1" class="logic-connector">
            {{ group.logic }}
          </div>
        </template>
      </div>

      <!-- 操作按钮 -->
      <div class="group-actions-bottom">
        <n-space>
          <n-tooltip v-if="isAtMaxChildren" placement="top">
            <template #trigger>
              <n-button
                dashed
                type="primary"
                size="small"
                disabled
              >
                + 添加条件
              </n-button>
            </template>
            条件项数量已达上限（{{ MAX_CHILDREN_COUNT }}）
          </n-tooltip>
          <n-button
            v-else-if="!disabled"
            dashed
            type="primary"
            size="small"
            @click="addRule"
          >
            + 添加条件
          </n-button>
          <n-tooltip v-if="isAtMaxDepth" placement="top">
            <template #trigger>
              <n-button
                dashed
                type="primary"
                size="small"
                disabled
              >
                + 添加条件组
              </n-button>
            </template>
            嵌套深度已达上限（{{ MAX_NESTING_DEPTH }}）
          </n-tooltip>
          <n-button
            v-else-if="!disabled && !isAtMaxDepth"
            dashed
            type="primary"
            size="small"
            @click="addGroup"
          >
            + 添加条件组
          </n-button>
        </n-space>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { NButton, NSelect, NSpace, NTooltip } from 'naive-ui'
import ConditionRule from './ConditionRule.vue'
import type { ConditionGroup as ConditionGroupType, ConditionRule as ConditionRuleType, FieldDefinition, LogicType } from '@/types/condition'

const MAX_NESTING_DEPTH = 5
const MAX_CHILDREN_COUNT = 50

interface Props {
  group: ConditionGroupType
  fields: FieldDefinition[]
  isNested?: boolean
  nestingDepth?: number
  disabled?: boolean
  formSchema?: any
}

const props = withDefaults(defineProps<Props>(), {
  isNested: false,
  nestingDepth: 0,
  disabled: false,
})

// 监控 fields prop 变化
watch(
  () => props.fields,
  (fields) => {
    console.log('[ConditionGroup] fields prop updated:', {
      count: fields.length,
      fields: fields.map(f => ({ key: f.key, name: f.name, type: f.type }))
    })
  },
  { immediate: true }
)

const emit = defineEmits<{
  (e: 'update', group: ConditionGroupType): void
  (e: 'delete'): void
}>()

const logicOptions = [
  { label: '所有条件 (AND)', value: 'AND' },
  { label: '任一条件 (OR)', value: 'OR' },
]

// 检查是否达到最大嵌套深度
const isAtMaxDepth = computed(() => {
  return props.nestingDepth >= MAX_NESTING_DEPTH
})

// 检查是否达到最大条件项数量
const isAtMaxChildren = computed(() => {
  return props.group.children.length >= MAX_CHILDREN_COUNT
})

const updateLogic = (logic: LogicType) => {
  emit('update', {
    ...props.group,
    logic,
  })
}

const updateChild = (index: number, child: any) => {
  const newChildren = [...props.group.children]
  newChildren[index] = child
  emit('update', {
    ...props.group,
    children: newChildren,
  })
}

const deleteChild = (index: number) => {
  // 确保 index 有效
  if (index < 0 || index >= props.group.children.length) {
    return
  }
  
  const newChildren = [...props.group.children]
  newChildren.splice(index, 1)
  emit('update', {
    ...props.group,
    children: newChildren,
  })
}

const addRule = () => {
  if (isAtMaxChildren.value) return
  
  const newRule: ConditionRuleType = {
    type: 'RULE',
    fieldKey: '',
    fieldType: 'TEXT',
    operator: null, // 默认 null，符合设计方案
    value: null,
  }
  emit('update', {
    ...props.group,
    children: [...props.group.children, newRule],
  })
}

const addGroup = () => {
  if (isAtMaxDepth.value) return
  
  const newGroup: ConditionGroupType = {
    type: 'GROUP',
    logic: 'AND',
    children: [],
  }
  emit('update', {
    ...props.group,
    children: [...props.group.children, newGroup],
  })
}
</script>

<style scoped>
.condition-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 根组样式 */
.condition-group:not(.is-nested) {
  background: #ffffff;
  border: 2px solid #e0e5ec;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

/* 嵌套组样式 */
.condition-group.is-nested {
  border-radius: 10px;
  padding: 16px;
  background: #f9fbfc;
  border: 2px solid #d3e8e0;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.03);
}

/* 嵌套深度颜色 */
.condition-group.is-nested.depth-1 {
  border-color: #18a058;
  background: #f6fbf8;
}

.condition-group.is-nested.depth-2 {
  border-color: #2080f0;
  background: #f0f6ff;
}

.condition-group.is-nested.depth-3 {
  border-color: #a060d0;
  background: #faf5ff;
}

.condition-group.is-nested.depth-4,
.condition-group.is-nested.depth-5 {
  border-color: #f0a020;
  background: #fffaf0;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f6fbf8 0%, #f0f9f4 100%);
  border-radius: 8px;
  border: 1px solid #d3e8e0;
  gap: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
}

.condition-group.is-nested.depth-1 .group-header {
  background: linear-gradient(135deg, #e7f5f0 0%, #d9f0e6 100%);
  border-color: #18a058;
}

.condition-group.is-nested.depth-2 .group-header {
  background: linear-gradient(135deg, #e6f2ff 0%, #d9ebff 100%);
  border-color: #2080f0;
}

.condition-group.is-nested.depth-3 .group-header {
  background: linear-gradient(135deg, #f5e6ff 0%, #ead9ff 100%);
  border-color: #a060d0;
}

.condition-group.is-nested.depth-4 .group-header,
.condition-group.is-nested.depth-5 .group-header {
  background: linear-gradient(135deg, #fff5e6 0%, #ffe9d9 100%);
  border-color: #f0a020;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-label {
  font-size: 13px;
  font-weight: 700;
  color: #18a058;
  padding: 6px 12px;
  background: rgba(24, 160, 88, 0.1);
  border-radius: 6px;
  border: 1px solid rgba(24, 160, 88, 0.2);
}

.condition-group.is-nested.depth-1 .group-label {
  color: #18a058;
  background: rgba(24, 160, 88, 0.1);
  border-color: rgba(24, 160, 88, 0.2);
}

.condition-group.is-nested.depth-2 .group-label {
  color: #2080f0;
  background: rgba(32, 128, 240, 0.1);
  border-color: rgba(32, 128, 240, 0.2);
}

.condition-group.is-nested.depth-3 .group-label {
  color: #a060d0;
  background: rgba(160, 96, 208, 0.1);
  border-color: rgba(160, 96, 208, 0.2);
}

.condition-group.is-nested.depth-4 .group-label,
.condition-group.is-nested.depth-5 .group-label {
  color: #f0a020;
  background: rgba(240, 160, 32, 0.1);
  border-color: rgba(240, 160, 32, 0.2);
}

.logic-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logic-label {
  font-size: 13px;
  color: #6b7385;
  font-weight: 600;
  white-space: nowrap;
}

.logic-select {
  min-width: 160px;
}

.delete-group-btn {
  flex-shrink: 0;
}

.group-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.rules-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rule-wrapper {
  animation: slideIn 0.2s ease-out;
}

.nested-group-wrapper {
  animation: slideIn 0.2s ease-out;
}

.logic-connector {
  text-align: center;
  font-size: 13px;
  font-weight: 700;
  color: #18a058;
  padding: 8px 0;
  margin: 8px 0;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.condition-group.is-nested.depth-1 .logic-connector {
  color: #18a058;
}

.condition-group.is-nested.depth-2 .logic-connector {
  color: #2080f0;
}

.condition-group.is-nested.depth-3 .logic-connector {
  color: #a060d0;
}

.condition-group.is-nested.depth-4 .logic-connector,
.condition-group.is-nested.depth-5 .logic-connector {
  color: #f0a020;
}

.group-actions-bottom {
  padding: 12px 0 0 0;
  border-top: 2px solid #e0e5ec;
  margin-top: 4px;
}

.condition-group.is-nested .group-actions-bottom {
  border-top-color: rgba(0, 0, 0, 0.08);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .condition-group:not(.is-nested) {
    padding: 12px;
  }

  .condition-group.is-nested {
    padding: 8px;
  }

  .group-header {
    padding: 8px;
    flex-direction: column;
    align-items: flex-start;
  }

  .header-left {
    width: 100%;
  }

  .header-right {
    width: 100%;
    justify-content: flex-end;
  }

  .logic-select {
    min-width: 120px;
  }
}
</style>
