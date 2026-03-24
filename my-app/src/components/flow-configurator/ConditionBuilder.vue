<template>
  <div class="condition-builder">
    <!-- 规则列表 -->
    <div class="rules-container">
      <div v-for="(rule, index) in rules" :key="index" class="rule-row">
        <div class="rule-content">
          <!-- 字段选择 -->
          <n-select
            v-model:value="rule.field"
            :options="fieldOptions"
            placeholder="选择字段"
            clearable
            class="rule-field"
            @update:value="() => onRuleChange(index)"
          />

          <!-- 操作符选择 -->
          <n-select
            v-model:value="rule.operator"
            :options="getOperatorOptions(rule.field)"
            placeholder="选择操作符"
            clearable
            class="rule-operator"
            @update:value="() => onRuleChange(index)"
          />

          <!-- 值输入 -->
          <div class="rule-value">
            <n-input
              v-if="isSimpleType(rule.field)"
              v-model:value="rule.value"
              :type="getInputType(rule.field)"
              :placeholder="`输入${getFieldLabel(rule.field)}`"
              clearable
              @update:value="() => onRuleChange(index)"
            />
            <n-select
              v-else-if="isSelectType(rule.field)"
              v-model:value="rule.value"
              :options="getFieldOptions(rule.field)"
              placeholder="选择值"
              clearable
              @update:value="() => onRuleChange(index)"
            />
            <n-input
              v-else
              v-model:value="rule.value"
              placeholder="输入值"
              clearable
              @update:value="() => onRuleChange(index)"
            />
          </div>
        </div>

        <!-- 删除按钮 -->
        <n-button
          quaternary
          circle
          type="error"
          size="small"
          :disabled="disabled"
          @click="removeRule(index)"
        >
          <template #icon>
            <n-icon>
              <DeleteOutlined />
            </n-icon>
          </template>
        </n-button>
      </div>
    </div>

    <!-- 添加规则按钮 -->
    <n-button
      v-if="!disabled"
      dashed
      block
      type="primary"
      size="small"
      @click="addRule"
      class="add-rule-btn"
    >
      + 添加条件
    </n-button>

    <!-- 逻辑选择 -->
    <div v-if="rules.length > 1" class="logic-selector">
      <n-space align="center">
        <span class="logic-label">逻辑关系：</span>
        <n-radio-group v-model:value="logic" :disabled="disabled" @update:value="onLogicChange">
          <n-radio value="AND">全部满足 (AND)</n-radio>
          <n-radio value="OR">任意满足 (OR)</n-radio>
        </n-radio-group>
      </n-space>
    </div>

    <!-- 预览 -->
    <div v-if="rules.length > 0" class="preview-section">
      <div class="preview-label">条件预览：</div>
      <div class="preview-content">
        <code>{{ previewCondition }}</code>
      </div>
      <div class="preview-json">
        <div class="json-label">JsonLogic 格式：</div>
        <n-input
          type="textarea"
          :value="jsonLogicOutput"
          :autosize="{ minRows: 3, maxRows: 6 }"
          readonly
          class="json-output"
        />
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <n-empty description="暂无条件规则" size="small" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { NButton, NIcon, NInput, NSelect, NSpace, NRadioGroup, NRadio, NEmpty } from 'naive-ui'
import { DeleteOutlined } from '@vicons/antd'
import type { FormSchema } from '@/types/schema'
import type { JsonLogicExpression } from '@/types/flow'

interface Rule {
  field: string
  operator: string
  value: string | number | boolean | null
}

interface Props {
  formSchema?: FormSchema
  initialCondition?: JsonLogicExpression | null
  disabled?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:condition', value: JsonLogicExpression | null): void
}>()

const rules = ref<Rule[]>([])
const logic = ref<'AND' | 'OR'>('AND')

// 字段类型映射
const fieldTypeMap = new Map<string, string>()
const fieldOptionsMap = new Map<string, Array<{ label: string; value: string | number }>>()

// 初始化字段信息
const initializeFields = () => {
  fieldTypeMap.clear()
  fieldOptionsMap.clear()

  if (!props.formSchema?.properties) return

  Object.entries(props.formSchema.properties).forEach(([fieldName, fieldSchema]) => {
    const schema = fieldSchema as any
    fieldTypeMap.set(fieldName, schema.type || 'string')

    // 如果有枚举值，保存选项
    if (schema.enum) {
      fieldOptionsMap.set(
        fieldName,
        schema.enum.map((val: any) => ({
          label: val,
          value: val
        }))
      )
    }
  })
}

// 字段选项
const fieldOptions = computed(() => {
  if (!props.formSchema?.properties) return []
  return Object.entries(props.formSchema.properties).map(([name, schema]) => {
    const s = schema as any
    return {
      label: s.title || name,
      value: name
    }
  })
})

// 获取字段标签
const getFieldLabel = (fieldName: string) => {
  if (!props.formSchema?.properties) return fieldName
  const schema = props.formSchema.properties[fieldName] as any
  return schema?.title || fieldName
}

// 获取字段类型
const getFieldType = (fieldName: string): string => {
  return fieldTypeMap.get(fieldName) || 'string'
}

// 判断是否为简单类型（数字、文本、布尔）
const isSimpleType = (fieldName: string): boolean => {
  const type = getFieldType(fieldName)
  return ['string', 'number', 'integer', 'boolean'].includes(type)
}

// 判断是否为选择类型
const isSelectType = (fieldName: string): boolean => {
  return fieldOptionsMap.has(fieldName)
}

// 获取输入框类型
const getInputType = (fieldName: string): string => {
  const type = getFieldType(fieldName)
  if (type === 'number' || type === 'integer') return 'number'
  if (type === 'boolean') return 'checkbox'
  return 'text'
}

// 获取字段的选项
const getFieldOptions = (fieldName: string) => {
  return fieldOptionsMap.get(fieldName) || []
}

// 获取操作符选项
const getOperatorOptions = (fieldName: string) => {
  if (!fieldName) return []

  const type = getFieldType(fieldName)
  const operatorMap: Record<string, Array<{ label: string; value: string }>> = {
    number: [
      { label: '等于 (=)', value: '==' },
      { label: '不等于 (≠)', value: '!=' },
      { label: '大于 (>)', value: '>' },
      { label: '小于 (<)', value: '<' },
      { label: '大于等于 (≥)', value: '>=' },
      { label: '小于等于 (≤)', value: '<=' }
    ],
    integer: [
      { label: '等于 (=)', value: '==' },
      { label: '不等于 (≠)', value: '!=' },
      { label: '大于 (>)', value: '>' },
      { label: '小于 (<)', value: '<' },
      { label: '大于等于 (≥)', value: '>=' },
      { label: '小于等于 (≤)', value: '<=' }
    ],
    string: [
      { label: '等于 (=)', value: '==' },
      { label: '不等于 (≠)', value: '!=' },
      { label: '包含', value: 'contains' },
      { label: '不包含', value: '!contains' },
      { label: '开头是', value: 'startsWith' },
      { label: '结尾是', value: 'endsWith' }
    ],
    boolean: [
      { label: '是', value: '==' },
      { label: '否', value: '!=' }
    ]
  }

  return operatorMap[type] || operatorMap.string
}

// 条件预览
const previewCondition = computed(() => {
  if (rules.value.length === 0) return '无条件'

  return rules.value
    .map((r) => {
      const fieldLabel = getFieldLabel(r.field)
      const operatorLabel = getOperatorOptions(r.field).find((op) => op.value === r.operator)?.label || r.operator
      return `${fieldLabel} ${operatorLabel} ${r.value}`
    })
    .join(` ${logic.value === 'AND' ? '且' : '或'} `)
})

// 生成 JsonLogic 格式
const jsonLogicOutput = computed(() => {
  if (rules.value.length === 0) return ''

  const conditions = rules.value.map((r) => {
    const operator = r.operator
    const field = r.field
    let value: any = r.value

    // 类型转换
    const fieldType = getFieldType(field)
    if (fieldType === 'number' || fieldType === 'integer') {
      value = Number(value)
    } else if (fieldType === 'boolean') {
      value = value === 'true' || value === true
    }

    // 根据操作符生成不同的 JsonLogic 结构
    switch (operator) {
      case '==':
        return { '==': [{ var: field }, value] }
      case '!=':
        return { '!=': [{ var: field }, value] }
      case '>':
        return { '>': [{ var: field }, value] }
      case '<':
        return { '<': [{ var: field }, value] }
      case '>=':
        return { '>=': [{ var: field }, value] }
      case '<=':
        return { '<=': [{ var: field }, value] }
      case 'contains':
        return { 'in': [value, { var: field }] }
      case '!contains':
        return { '!': [{ 'in': [value, { var: field }] }] }
      case 'startsWith':
        return { 'startsWith': [{ var: field }, value] }
      case 'endsWith':
        return { 'endsWith': [{ var: field }, value] }
      default:
        return { '==': [{ var: field }, value] }
    }
  })

  let result: JsonLogicExpression
  if (conditions.length === 1) {
    result = conditions[0]
  } else if (logic.value === 'AND') {
    result = { and: conditions }
  } else {
    result = { or: conditions }
  }

  return JSON.stringify(result, null, 2)
})

// 规则变化时更新
const onRuleChange = () => {
  emitCondition()
}

// 逻辑变化时更新
const onLogicChange = () => {
  emitCondition()
}

// 发送条件更新
const emitCondition = () => {
  if (rules.value.length === 0) {
    emit('update:condition', null)
    return
  }

  try {
    const jsonLogic = JSON.parse(jsonLogicOutput.value)
    emit('update:condition', jsonLogic)
  } catch {
    // 如果 JSON 解析失败，不发送
  }
}

// 添加规则
const addRule = () => {
  rules.value.push({
    field: '',
    operator: '==',
    value: ''
  })
}

// 删除规则
const removeRule = (index: number) => {
  rules.value.splice(index, 1)
  emitCondition()
}

// 从 JsonLogic 初始化规则
const initializeFromJsonLogic = (condition: JsonLogicExpression | null | undefined) => {
  if (!condition) {
    rules.value = []
    logic.value = 'AND'
    return
  }

  // 简单的 JsonLogic 解析（支持基本情况）
  const newRules: Rule[] = []

  if (condition.and) {
    logic.value = 'AND'
    const conditions = Array.isArray(condition.and) ? condition.and : [condition.and]
    conditions.forEach((cond: any) => {
      parseCondition(cond, newRules)
    })
  } else if (condition.or) {
    logic.value = 'OR'
    const conditions = Array.isArray(condition.or) ? condition.or : [condition.or]
    conditions.forEach((cond: any) => {
      parseCondition(cond, newRules)
    })
  } else {
    parseCondition(condition, newRules)
  }

  rules.value = newRules
}

// 解析单个条件
const parseCondition = (cond: any, rules: Rule[]) => {
  if (cond['==']) {
    const [field, value] = cond['==']
    if (field.var) {
      rules.push({ field: field.var, operator: '==', value })
    }
  } else if (cond['!=']) {
    const [field, value] = cond['!=']
    if (field.var) {
      rules.push({ field: field.var, operator: '!=', value })
    }
  } else if (cond['>']) {
    const [field, value] = cond['>']
    if (field.var) {
      rules.push({ field: field.var, operator: '>', value })
    }
  } else if (cond['<']) {
    const [field, value] = cond['<']
    if (field.var) {
      rules.push({ field: field.var, operator: '<', value })
    }
  } else if (cond['>=']) {
    const [field, value] = cond['>=']
    if (field.var) {
      rules.push({ field: field.var, operator: '>=', value })
    }
  } else if (cond['<=']) {
    const [field, value] = cond['<=']
    if (field.var) {
      rules.push({ field: field.var, operator: '<=', value })
    }
  }
}

// 初始化
watch(
  () => props.formSchema,
  () => {
    initializeFields()
  },
  { immediate: true }
)

watch(
  () => props.initialCondition,
  (condition) => {
    initializeFromJsonLogic(condition)
  },
  { immediate: true }
)
</script>

<style scoped>
.condition-builder {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rules-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rule-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.rule-content {
  display: grid;
  grid-template-columns: 1fr 1fr 1.5fr;
  gap: 8px;
  flex: 1;
}

.rule-field,
.rule-operator {
  width: 100%;
}

.rule-value {
  width: 100%;
}

.add-rule-btn {
  margin-top: 4px;
}

.logic-selector {
  padding: 8px 12px;
  background: #f6fbf8;
  border-radius: 6px;
  border: 1px solid #d3e8e0;
}

.logic-label {
  font-size: 12px;
  color: #6b7385;
  font-weight: 500;
}

.preview-section {
  padding: 12px;
  background: #f6fbf8;
  border-radius: 6px;
  border: 1px solid #d3e8e0;
}

.preview-label {
  font-size: 12px;
  font-weight: 500;
  color: #6b7385;
  margin-bottom: 6px;
}

.preview-content {
  padding: 8px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #e0e5ec;
  font-size: 12px;
  color: #333;
  margin-bottom: 8px;
  word-break: break-all;
}

.preview-content code {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  color: #d03050;
}

.preview-json {
  margin-top: 8px;
}

.json-label {
  font-size: 12px;
  font-weight: 500;
  color: #6b7385;
  margin-bottom: 6px;
}

.json-output {
  font-size: 11px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.empty-state {
  padding: 24px 0;
  text-align: center;
}
</style>
