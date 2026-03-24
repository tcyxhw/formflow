<template>
  <div class="condition-rule-card">
    <!-- 卡片头部：标题和删除按钮 -->
    <div class="card-header">
      <span class="card-title">条件</span>
      <n-button
        quaternary
        circle
        type="error"
        size="small"
        :disabled="disabled"
        @click="$emit('delete')"
        class="delete-btn"
      >
        <template #icon>
          <n-icon>
            <DeleteOutlined />
          </n-icon>
        </template>
      </n-button>
    </div>

    <!-- 卡片内容：竖排布局 -->
    <div class="card-content">
      <!-- 字段选择 -->
      <div class="form-group">
        <label class="form-label">字段</label>
        <n-select
          :value="rule.fieldKey"
          :options="fieldOptions"
          placeholder="选择字段"
          clearable
          class="form-control"
          @update:value="updateField"
        />
      </div>

      <!-- 运算符选择 -->
      <div class="form-group">
        <label class="form-label">运算符</label>
        <n-select
          :value="rule.operator"
          :options="operatorOptions"
          placeholder="选择运算符"
          :disabled="!rule.fieldKey"
          clearable
          class="form-control"
          @update:value="updateOperator"
        />
        <div v-if="rule.fieldKey && !rule.operator" class="form-hint">
          请先选择运算符
        </div>
      </div>

      <!-- 值输入 -->
      <div v-if="rule.fieldKey && rule.operator" class="form-group">
        <label class="form-label">值</label>
        <ValueInput
          :model-value="rule.value"
          :field-type="rule.fieldType"
          :operator="rule.operator"
          :select-options="currentFieldOptions"
          class="form-control"
          @update:model-value="updateValue"
        />
        <div v-if="validationError" class="form-error">
          {{ validationError }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NButton, NIcon, NSelect } from 'naive-ui'
import { DeleteOutlined } from '@vicons/antd'
import ValueInput from './ValueInput.vue'
import type { ConditionRule as ConditionRuleType, FieldDefinition, OperatorConfig } from '@/types/condition'
import { getOperatorLabel, OPERATOR_MAP } from '@/types/condition'
import FieldLabelService from '@/services/fieldLabelService'
import type { FormSchema } from '@/types/schema'

interface Props {
  rule: ConditionRuleType
  fields: FieldDefinition[]
  disabled?: boolean
  formSchema?: FormSchema
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update', rule: ConditionRuleType): void
  (e: 'delete'): void
}>()

// 字段选项（分组显示）
const fieldOptions = computed(() => {
  // 直接使用 fields prop 中的 name 字段，这已经是从 API 返回的中文名称
  const formFields = props.fields
    .filter(f => !f.isSystem)
    .map(f => ({
      label: f.name, // 直接使用 name，这是从 API 返回的中文标签
      value: f.key,
      key: f.key, // 添加唯一 key，避免虚拟滚动渲染问题
    }))

  const systemFields = props.fields
    .filter(f => f.isSystem)
    .map(f => ({
      label: f.name, // 直接使用 name
      value: f.key,
      key: f.key, // 添加唯一 key
    }))

  const options: any[] = []

  if (formFields.length > 0) {
    options.push({
      type: 'group',
      label: '表单字段',
      key: 'group-form-fields', // 为分组添加唯一 key
      children: formFields,
    })
  }

  if (systemFields.length > 0) {
    options.push({
      type: 'group',
      label: '系统字段',
      key: 'group-system-fields', // 为分组添加唯一 key
      children: systemFields,
    })
  }

  return options.length > 0 ? options : formFields
})

// 当前字段
const currentField = computed(() => {
  const field = props.fields.find(f => f.key === props.rule.fieldKey)
  console.log('[ConditionRule] currentField computed:', {
    fieldKey: props.rule.fieldKey,
    foundField: field ? { key: field.key, name: field.name, type: field.type } : null,
    totalFields: props.fields.length,
    availableFieldKeys: props.fields.map(f => f.key).slice(0, 5)
  })
  return field
})

// 当前字段的选项（用于下拉选择）
const currentFieldOptions = computed(() => {
  return currentField.value?.options || []
})

// 检查当前运算符是否需要值
const needsValue = computed(() => {
  if (!props.rule.operator) return false
  return !['IS_EMPTY', 'IS_NOT_EMPTY'].includes(props.rule.operator)
})

// 校验值
const validationError = computed(() => {
  if (!props.rule.operator || !needsValue.value) {
    return null
  }

  const value = props.rule.value
  const operator = props.rule.operator
  const fieldType = props.rule.fieldType

  // 1. 检查值是否为空
  if (value === null || value === undefined || value === '') {
    return '请输入值'
  }

  // 2. BETWEEN 运算符的特殊校验
  if (operator === 'BETWEEN') {
    if (!Array.isArray(value) || value.length !== 2) {
      return '请输入两个值'
    }
    if (value[0] === null || value[0] === undefined || value[1] === null || value[1] === undefined) {
      return '两个值都不能为空'
    }

    // 检查大小关系
    if (fieldType === 'NUMBER') {
      const min = parseFloat(value[0])
      const max = parseFloat(value[1])
      if (isNaN(min) || isNaN(max)) {
        return '请输入有效的数字'
      }
      if (min > max) {
        return '最小值不能大于最大值'
      }
    } else if (fieldType === 'DATE' || fieldType === 'DATETIME') {
      try {
        const startDate = new Date(value[0])
        const endDate = new Date(value[1])
        if (startDate > endDate) {
          return '开始日期不能晚于结束日期'
        }
      } catch {
        return '请输入有效的日期'
      }
    }
    return null
  }

  // 3. IN/NOT_IN/HAS_ANY/HAS_ALL 的数组校验
  if (['IN', 'NOT_IN', 'HAS_ANY', 'HAS_ALL'].includes(operator)) {
    if (!Array.isArray(value) || value.length === 0) {
      return '至少选择一个值'
    }
    return null
  }

  // 4. NUMBER 类型的值校验
  if (fieldType === 'NUMBER') {
    const num = parseFloat(value)
    if (isNaN(num)) {
      return '请输入有效的数字'
    }
    return null
  }

  // 5. DATE 类型的值校验
  if (fieldType === 'DATE') {
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/
    if (!dateRegex.test(value)) {
      return '请输入有效的日期格式 (YYYY-MM-DD)'
    }
    return null
  }

  // 6. DATETIME 类型的值校验
  if (fieldType === 'DATETIME') {
    try {
      new Date(value)
      return null
    } catch {
      return '请输入有效的日期时间'
    }
  }

  return null
})

// 运算符选项
const operatorOptions = computed(() => {
  if (!currentField.value) {
    console.log('[ConditionRule] operatorOptions: no currentField')
    return []
  }

  const fieldType = currentField.value.type
  const operators = OPERATOR_MAP[fieldType] || []

  console.log('[ConditionRule] operatorOptions computed:', {
    fieldType: fieldType,
    operatorsCount: operators.length,
    operators: operators.map(op => op.value)
  })

  return operators.map((op: OperatorConfig) => ({
    label: getOperatorLabel(op.value, fieldType),
    value: op.value,
  }))
})

const updateField = (fieldKey: string | null) => {
  // 如果清除字段选择（null 或空字符串）
  if (!fieldKey) {
    console.log('[ConditionRule] updateField: clearing field')
    emit('update', {
      ...props.rule,
      fieldKey: '',
      fieldType: 'TEXT',
      operator: null,
      value: null,
    })
    return
  }

  const field = props.fields.find(f => f.key === fieldKey)
  if (!field) {
    console.log('[ConditionRule] updateField: field not found', fieldKey)
    return
  }

  console.log('[ConditionRule] updateField:', {
    fieldKey: fieldKey,
    fieldType: field.type,
    fieldName: field.name
  })

  emit('update', {
    ...props.rule,
    fieldKey,
    fieldType: field.type,
    operator: null, // 重置运算符
    value: null, // 重置值
  })
}

const updateOperator = (operator: string | null) => {
  // 如果清除运算符选择（null 或空字符串）
  if (!operator) {
    emit('update', {
      ...props.rule,
      operator: null,
      value: null,
    })
    return
  }

  emit('update', {
    ...props.rule,
    operator: operator as any,
    value: null, // 重置值
  })
}

const updateValue = (value: any) => {
  emit('update', {
    ...props.rule,
    value,
  })
}
</script>

<style scoped>
.condition-rule-card {
  display: flex;
  flex-direction: column;
  gap: 0;
  background: #ffffff;
  border: 2px solid #e0e5ec;
  border-radius: 10px;
  overflow: hidden;
  animation: slideIn 0.2s ease-out;
  transition: all 0.2s ease-out;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.04);
}

.condition-rule-card:hover {
  background: #fafbfc;
  border-color: #18a058;
  box-shadow: 0 4px 16px rgba(24, 160, 88, 0.12);
  transform: translateY(-1px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: linear-gradient(135deg, #f6fbf8 0%, #f0f9f4 100%);
  border-bottom: 1px solid #e0e5ec;
}

.card-title {
  font-size: 14px;
  font-weight: 700;
  color: #1f2937;
  letter-spacing: 0.3px;
}

.delete-btn {
  flex-shrink: 0;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group:not(:last-child) {
  margin-bottom: 16px;
}

.form-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  letter-spacing: 0.2px;
}

.form-control {
  width: 100%;
}

.form-hint {
  font-size: 12px;
  color: #f0a020;
  margin-top: 4px;
  padding: 6px 10px;
  background: rgba(240, 160, 32, 0.08);
  border-radius: 4px;
  border-left: 3px solid #f0a020;
}

.form-error {
  font-size: 12px;
  color: #d03050;
  margin-top: 4px;
  padding: 6px 10px;
  background: rgba(208, 48, 80, 0.08);
  border-radius: 4px;
  border-left: 3px solid #d03050;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-header {
    padding: 12px 16px;
  }

  .card-content {
    padding: 16px;
  }

  .card-title {
    font-size: 13px;
  }

  .form-label {
    font-size: 12px;
  }

  .form-group:not(:last-child) {
    margin-bottom: 12px;
  }
}
</style>
