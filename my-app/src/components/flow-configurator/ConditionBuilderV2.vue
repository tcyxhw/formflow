<template>
  <div class="condition-builder-v2">
    <!-- 主体内容 -->
    <div class="builder-body">
      <!-- 根条件组 -->
      <div class="condition-container">
        <ConditionGroup
          v-if="rootGroup"
          :group="rootGroup"
          :fields="allFields"
          :form-schema="props.formSchema"
          :disabled="disabled"
          @update="updateRootGroup"
        />
      </div>

      <!-- JSON 预览区域 -->
      <div class="preview-section">
        <div v-if="showJsonPreview" class="json-preview">
          <div class="preview-header">
            <span class="preview-title">JSON 预览</span>
            <n-button
              quaternary
              size="small"
              @click="showJsonPreview = false"
            >
              隐藏
            </n-button>
          </div>
          <n-input
            type="textarea"
            :value="jsonOutput"
            :autosize="{ minRows: 4, maxRows: 8 }"
            readonly
            class="json-output"
          />
        </div>

        <div v-else class="show-json-btn">
          <n-button
            quaternary
            size="small"
            @click="showJsonPreview = true"
          >
            显示 JSON 预览
          </n-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { NButton, NInput } from 'naive-ui'
import ConditionGroup from './ConditionGroup.vue'
import { ConditionGroup as ConditionGroupType } from '@/types/condition'
import { ConditionRule as ConditionRuleType } from '@/types/condition'
import { FieldDefinition } from '@/types/condition'
import { ConditionNode } from '@/types/condition'
import { getFormFields } from '@/api/form'

type FormSchemaType = {
  version?: string
  fields?: any[]
  fieldOrder?: string[]
}

interface Props {
  modelValue?: ConditionNode | null
  formSchema?: FormSchemaType
  formId?: number
  disabled?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: ConditionNode | null): void
}>()

const showJsonPreview = ref(false)
const apiFields = ref<FieldDefinition[]>([])
const isLoadingFields = ref(false)

// 初始化根组
const rootGroup = ref<ConditionGroupType>({
  type: 'GROUP',
  logic: 'AND',
  children: [],
})

// 将 ConditionNode 转换为 JsonLogic 格式
const conditionNodeToJsonLogic = (node: ConditionNode | null): any => {
  if (!node) return null
  
  if (node.type === 'RULE') {
    // 转换规则为 JsonLogic
    const { fieldKey, operator, value } = node
    const fieldVar = { var: fieldKey }
    
    switch (operator) {
      case 'EQUALS':
        return { '==': [fieldVar, value] }
      case 'NOT_EQUALS':
        return { '!=': [fieldVar, value] }
      case 'GREATER_THAN':
        return { '>': [fieldVar, value] }
      case 'GREATER_EQUAL':
        return { '>=': [fieldVar, value] }
      case 'LESS_THAN':
        return { '<': [fieldVar, value] }
      case 'LESS_EQUAL':
        return { '<=': [fieldVar, value] }
      case 'BETWEEN':
        if (Array.isArray(value) && value.length === 2) {
          // 使用变量避免解析器对 >= 和 <= 的问题
          const opGte = '>='
          const opLte = '<='
          return { and: [{ [opGte]: [fieldVar, value[0]] }, { [opLte]: [fieldVar, value[1]] }] }
        }
        return { '==': [fieldVar, value] }
      case 'CONTAINS':
        return { 'in': [value, fieldVar] }
      case 'NOT_CONTAINS':
        return { '!': [{ 'in': [value, fieldVar] }] }
      case 'IN':
        return { 'in': [fieldVar, value] }
      case 'NOT_IN':
        return { '!': [{ 'in': [fieldVar, value] }] }
      case 'HAS_ANY':
        return { 'or': value.map((v: any) => ({ 'in': [v, fieldVar] })) }
      case 'HAS_ALL':
        return { 'and': value.map((v: any) => ({ 'in': [v, fieldVar] })) }
      case 'IS_EMPTY':
        return { '==': [fieldVar, ''] }
      case 'IS_NOT_EMPTY':
        return { '!=': [fieldVar, ''] }
      default:
        return { '==': [fieldVar, value] }
    }
  } else {
    // 转换组为 JsonLogic
    const conditions = node.children
      .map(child => conditionNodeToJsonLogic(child))
      .filter(Boolean)
    
    if (conditions.length === 0) return null
    if (conditions.length === 1) return conditions[0]
    
    if (node.logic === 'AND') {
      return { and: conditions }
    } else {
      return { or: conditions }
    }
  }
}

// 从 JsonLogic 格式初始化 ConditionNode（修复：添加fields参数以获取正确的字段类型）
const jsonLogicToConditionNode = (json: any, fields: FieldDefinition[] = []): ConditionNode | null => {
  if (!json || Object.keys(json).length === 0) return null

  // 处理 and/or
  if (json.and || json.or) {
    const isAnd = !!json.and
    const conditions = isAnd ? json.and : json.or
    const logic = isAnd ? 'AND' : 'OR'

    const children: ConditionNode[] = []
    const conditionArray = Array.isArray(conditions) ? conditions : [conditions]

    for (const condition of conditionArray) {
      const child = jsonLogicToConditionNode(condition, fields)
      if (child) {
        children.push(child)
      }
    }

    if (children.length === 0) return null

    return {
      type: 'GROUP',
      logic,
      children,
    }
  }

  // 处理二元操作符（支持新旧两种键名格式）
  const operatorMap: Record<string, string> = {
    // 新格式
    'eq': 'EQUALS',
    'neq': 'NOT_EQUALS',
    'gt': 'GREATER_THAN',
    'gte': 'GREATER_EQUAL',
    'lt': 'LESS_THAN',
    'lte': 'LESS_EQUAL',
    // 旧格式（向后兼容）
    '==': 'EQUALS',
    '!=': 'NOT_EQUALS',
    '>': 'GREATER_THAN',
    '>=': 'GREATER_EQUAL',
    '<': 'LESS_THAN',
    '<=': 'LESS_EQUAL',
  }

  for (const [jsonOp, nodeOp] of Object.entries(operatorMap)) {
    if (json[jsonOp]) {
      const [field, value] = json[jsonOp]
      if (field && field.var) {
        // 修复：根据fieldKey查找正确的字段类型
        const fieldDef = fields.find(f => f.key === field.var)
        const fieldType = fieldDef?.type || 'TEXT'

        return {
          type: 'RULE',
          fieldKey: field.var,
          fieldType: fieldType,
          operator: nodeOp as any,
          value,
        }
      }
    }
  }

  // 处理 in 操作符
  if (json.in) {
    const [value, field] = json.in
    if (field && field.var) {
      // 修复：根据fieldKey查找正确的字段类型
      const fieldDef = fields.find(f => f.key === field.var)
      const fieldType = fieldDef?.type || 'TEXT'

      return {
        type: 'RULE',
        fieldKey: field.var,
        fieldType: fieldType,
        operator: 'IN',
        value,
      }
    }
  }

  return null
}

// 从 API 加载表单字段
const loadFormFields = async () => {
  if (!props.formId) {
    console.warn('[ConditionBuilderV2] No formId provided, using schema or default fields')
    console.log('[ConditionBuilderV2] formSchema available:', !!props.formSchema)
    console.log('[ConditionBuilderV2] formSchema.fields:', props.formSchema?.fields)
    return
  }
  
  // 避免重复加载：如果已经有 API 字段且 formId 没有变化，则跳过
  if (apiFields.value.length > 0 && isLoadingFields.value === false) {
    console.log('[ConditionBuilderV2] Fields already loaded, skipping reload')
    return
  }
  
  try {
    isLoadingFields.value = true
    console.log('[ConditionBuilderV2] Loading fields for formId:', props.formId)
    const response = await getFormFields(props.formId)
    
    console.log('[ConditionBuilderV2] API response:', response)
    
    if (response.data) {
      const fields: FieldDefinition[] = []
      
      // 处理表单字段 - 优先添加，确保不被系统字段替换
      if (response.data.fields) {
        console.log('[ConditionBuilderV2] Processing form fields:', response.data.fields)
        response.data.fields.forEach((field: any) => {
          fields.push({
            key: field.key,
            name: field.name,
            type: mapFieldTypeToFieldType(field.type),
            options: field.options?.map((opt: any) => ({
              label: typeof opt === 'string' ? opt : opt.label,
              value: typeof opt === 'string' ? opt : opt.value,
            })),
            isSystem: false, // 明确标记为非系统字段
          })
        })
      }
      
      // 处理系统字段 - 后添加，确保不会覆盖表单字段
      if (response.data.system_fields) {
        console.log('[ConditionBuilderV2] Processing system fields:', response.data.system_fields)
        response.data.system_fields.forEach((field: any) => {
          fields.push({
            key: field.key,
            name: field.name,
            type: mapFieldTypeToFieldType(field.type),
            options: field.options?.map((opt: any) => ({
              label: typeof opt === 'string' ? opt : opt.label,
              value: typeof opt === 'string' ? opt : opt.value,
            })),
            isSystem: true,
          })
        })
      }
      
      console.log('[ConditionBuilderV2] Loaded fields from API:', {
        total: fields.length,
        formFields: fields.filter(f => !f.isSystem).length,
        systemFields: fields.filter(f => f.isSystem).length
      })
      
      // 只在字段真正变化时才更新，避免触发不必要的响应式更新
      const hasChanged = JSON.stringify(apiFields.value) !== JSON.stringify(fields)
      if (hasChanged) {
        console.log('[ConditionBuilderV2] Fields changed, updating apiFields')
        apiFields.value = fields
      } else {
        console.log('[ConditionBuilderV2] Fields unchanged, skipping update')
      }
    } else {
      console.warn('[ConditionBuilderV2] API response has no data')
    }
  } catch (error) {
    console.error('[ConditionBuilderV2] Failed to load form fields:', error)
    console.error('[ConditionBuilderV2] Error details:', {
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined
    })
  } finally {
    isLoadingFields.value = false
  }
}

// 从 formSchema 提取字段（备用方案）
const schemaFields = computed(() => {
  const fields: FieldDefinition[] = []
  const fieldKeys = new Set<string>()

  // 调试日志：检查 formSchema 是否正确传递
  console.log('[ConditionBuilderV2] schemaFields computed, formSchema:', {
    hasFormSchema: !!props.formSchema,
    fieldsCount: props.formSchema?.fields?.length || 0,
    fields: props.formSchema?.fields?.map((f: any) => ({ id: f.id, label: f.label, type: f.type }))
  })

  // 表单字段 - 优先从 formSchema.fields 提取
  if (props.formSchema?.fields && Array.isArray(props.formSchema.fields)) {
    console.log('[ConditionBuilderV2] Processing formSchema.fields:', props.formSchema.fields.length)
    props.formSchema.fields.forEach((field: any) => {
      // 跳过隐藏字段
      if (field.hidden) return

      const fieldKey = field.id || field.key
      if (!fieldKeys.has(fieldKey)) {
        fieldKeys.add(fieldKey)
        const mappedType = mapFieldTypeToFieldType(field.type)
        console.log('[ConditionBuilderV2] Field type mapping:', {
          key: fieldKey,
          originalType: field.type,
          mappedType: mappedType
        })
        fields.push({
          key: fieldKey,
          name: field.label || field.name || field.id || field.key,
          type: mappedType,
          options: field.options?.map((opt: any) => ({
            label: typeof opt === 'string' ? opt : opt.label,
            value: typeof opt === 'string' ? opt : opt.value,
          })),
          isSystem: false, // 明确标记为非系统字段
        })
        console.log('[ConditionBuilderV2] Added field from schema:', {
          key: fieldKey,
          name: field.label || field.name || field.id || field.key,
          type: mappedType
        })
      }
    })
  }

  // 如果没有表单字段，添加一些默认字段用于测试
  if (fields.length === 0) {
    console.log('[ConditionBuilderV2] No fields from schema, using default fields')
    const defaultFields = [
      {
        key: 'amount',
        name: '报销金额',
        type: 'NUMBER' as any,
        isSystem: false,
      },
      {
        key: 'category',
        name: '费用类别',
        type: 'SINGLE_SELECT' as any,
        options: [
          { label: '差旅', value: '差旅' },
          { label: '办公', value: '办公' },
          { label: '招待', value: '招待' },
          { label: '其他', value: '其他' },
        ],
        isSystem: false,
      },
      {
        key: 'reason',
        name: '报销原因',
        type: 'TEXT' as any,
        isSystem: false,
      }
    ]
    
    defaultFields.forEach(field => {
      if (!fieldKeys.has(field.key)) {
        fieldKeys.add(field.key)
        fields.push(field)
      }
    })
  }

  // 系统字段 - 后添加，确保不会覆盖表单字段
  const systemFields = [
    {
      key: 'sys_submitter',
      name: '提交人',
      type: 'USER' as any,
      isSystem: true,
    },
    {
      key: 'sys_submitter_dept',
      name: '提交人部门',
      type: 'DEPARTMENT' as any,
      isSystem: true,
    },
    {
      key: 'sys_submit_time',
      name: '提交时间',
      type: 'DATETIME' as any,
      isSystem: true,
    }
  ]
  
  systemFields.forEach(field => {
    if (!fieldKeys.has(field.key)) {
      fieldKeys.add(field.key)
      fields.push(field)
    } else {
      console.warn('[ConditionBuilderV2] System field key conflicts with form field:', field.key)
    }
  })

  console.log('[ConditionBuilderV2] schemaFields result:', {
    total: fields.length,
    fields: fields.map(f => ({ key: f.key, name: f.name, type: f.type, isSystem: f.isSystem }))
  })

  return fields
})

// 合并 API 字段和 schema 字段
const allFields = computed(() => {
  // 优先使用 API 加载的字段，如果没有则使用 schema 字段
  const fields = apiFields.value.length > 0 ? apiFields.value : schemaFields.value
  
  // 字段去重逻辑：基于 field.key 进行唯一性判断
  const uniqueFields: FieldDefinition[] = []
  const seenKeys = new Set<string>()
  
  for (const field of fields) {
    if (!seenKeys.has(field.key)) {
      seenKeys.add(field.key)
      uniqueFields.push(field)
    } else {
      console.log('[ConditionBuilderV2] Duplicate field key detected and skipped:', field.key)
    }
  }
  
  return uniqueFields
})

// 将表单字段类型映射到条件字段类型
const mapFieldTypeToFieldType = (fieldType: string): any => {
  const typeMap: Record<string, any> = {
    // 小写格式
    'text': 'TEXT',
    'textarea': 'TEXTAREA',
    'number': 'NUMBER',
    'select': 'SINGLE_SELECT',
    'multiselect': 'MULTI_SELECT',
    'checkbox': 'MULTI_SELECT',
    'radio': 'SINGLE_SELECT',
    'date': 'DATE',
    'datetime': 'DATETIME',
    'daterange': 'DATE_RANGE',
    'date-range': 'DATE_RANGE',  // 添加带连字符的格式
    'time': 'TEXT',
    'user': 'USER',
    'usermulti': 'USER_MULTI',
    'department': 'DEPARTMENT',
    'file': 'FILE',
    'upload': 'FILE',  // 添加upload类型
    'attachment': 'FILE',
    'string': 'TEXT',
    'phone': 'TEXT',  // 手机号当作TEXT
    'email': 'TEXT',  // 邮箱当作TEXT
    'calculated': 'NUMBER',  // 计算字段当作NUMBER
    'switch': 'SINGLE_SELECT',  // 开关当作单选
    // 大写格式（后端可能返回大写）
    'TEXT': 'TEXT',
    'TEXTAREA': 'TEXTAREA',
    'NUMBER': 'NUMBER',
    'SINGLE_SELECT': 'SINGLE_SELECT',
    'MULTI_SELECT': 'MULTI_SELECT',
    'DATE': 'DATE',
    'DATETIME': 'DATETIME',
    'DATE_RANGE': 'DATE_RANGE',
    'USER': 'USER',
    'USER_MULTI': 'USER_MULTI',
    'DEPARTMENT': 'DEPARTMENT',
    'FILE': 'FILE',
    'CALCULATED': 'NUMBER',
    'UPLOAD': 'FILE',
    'PHONE': 'TEXT',
    'EMAIL': 'TEXT',
  }
  return typeMap[fieldType.toLowerCase()] || typeMap[fieldType] || 'TEXT'
}

// JSON 输出（转换为 JsonLogic 格式）
const jsonOutput = computed(() => {
  const jsonLogic = conditionNodeToJsonLogic(rootGroup.value)
  return jsonLogic ? JSON.stringify(jsonLogic, null, 2) : ''
})

const updateRootGroup = (group: ConditionGroupType) => {
  rootGroup.value = group
  // 如果根组有子节点，发送更新；否则发送 null
  if (group.children.length > 0) {
    emit('update:modelValue', group)
  } else {
    emit('update:modelValue', null)
  }
}

// 初始化：如果有初始值，加载它
watch(
  () => props.modelValue,
  (value, oldValue) => {
    console.log('[ConditionBuilderV2] modelValue changed:', {
      hasValue: !!value,
      valueType: value?.type,
      oldValueType: oldValue?.type,
      isInitialLoad: oldValue === undefined
    })
    
    // 处理边界情况：null 或 undefined
    if (!value) {
      console.log('[ConditionBuilderV2] Resetting to empty group')
      rootGroup.value = {
        type: 'GROUP',
        logic: 'AND',
        children: []
      }
      return
    }
    
    // 处理空对象的边界情况
    if (typeof value === 'object' && Object.keys(value).length === 0) {
      console.log('[ConditionBuilderV2] Empty object detected, resetting to empty group')
      rootGroup.value = {
        type: 'GROUP',
        logic: 'AND',
        children: []
      }
      return
    }
    
    // 处理 GROUP 类型的条件节点
    if (value.type === 'GROUP') {
      console.log('[ConditionBuilderV2] Loading GROUP condition:', {
        logic: value.logic,
        childrenCount: value.children?.length || 0
      })
      rootGroup.value = value
      return
    }

    // 处理 RULE 类型的条件节点（单个规则）
    if (value.type === 'RULE') {
      console.log('[ConditionBuilderV2] Loading RULE condition, wrapping in GROUP:', {
        fieldKey: value.fieldKey,
        operator: value.operator
      })
      // 将单个规则包装在一个 GROUP 中
      rootGroup.value = {
        type: 'GROUP',
        logic: 'AND',
        children: [value]
      }
      return
    }

    // 处理 JsonLogic 格式的条件（转换为 ConditionNode）
    // 修复：传入 fields 参数以获取正确的字段类型
    const conditionNode = jsonLogicToConditionNode(value, allFields.value)
    if (conditionNode) {
      console.log('[ConditionBuilderV2] Converting JsonLogic to ConditionNode:', conditionNode)
      if (conditionNode.type === 'GROUP') {
        rootGroup.value = conditionNode
      } else {
        rootGroup.value = {
          type: 'GROUP',
          logic: 'AND',
          children: [conditionNode]
        }
      }
      return
    }

    // 未知类型，重置为空组
    console.warn('[ConditionBuilderV2] Unknown condition type, resetting to empty group:', value)
    rootGroup.value = {
      type: 'GROUP',
      logic: 'AND',
      children: []
    }
  },
  { immediate: true, deep: true }
)

// 当 formId 变化时，加载字段
watch(
  () => props.formId,
  (newFormId, oldFormId) => {
    console.log('[ConditionBuilderV2] formId changed:', {
      old: oldFormId,
      new: newFormId
    })
    
    // 只在 formId 真正变化时才重新加载
    if (newFormId && newFormId !== oldFormId) {
      // 清空现有字段，强制重新加载
      apiFields.value = []
      loadFormFields()
    }
  }
)

// 组件挂载时加载字段
onMounted(() => {
  console.log('[ConditionBuilderV2] Component mounted, props:', {
    formId: props.formId,
    hasFormSchema: !!props.formSchema,
    formSchemaFields: props.formSchema?.fields?.length || 0
  })
  loadFormFields()
})

// 监控 allFields 变化
watch(
  () => allFields.value,
  (fields) => {
    console.log('[ConditionBuilderV2] allFields updated:', {
      count: fields.length,
      fields: fields.map(f => ({ key: f.key, name: f.name, type: f.type }))
    })
  },
  { immediate: true }
)
</script>

<style scoped>
.condition-builder-v2 {
  display: flex;
  flex-direction: column;
  gap: 0;
  background: #ffffff;
  border-radius: 10px;
  overflow: hidden;
}

.builder-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 0;
}

.condition-container {
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow: auto;
  max-height: 350px;
}

.preview-section {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-top: 8px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.json-preview {
  padding: 14px;
  background: #1e293b;
  border-radius: 8px;
  border: 1px solid #334155;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.preview-title {
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.preview-header .n-button {
  color: #64748b;
}

.preview-header .n-button:hover {
  color: #94a3b8;
}

.json-output {
  font-size: 11px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: transparent;
  border: none;
}

.json-output :deep(.n-input__textarea) {
  background: transparent;
  color: #e2e8f0;
  border: none;
  resize: none;
}

.show-json-btn {
  text-align: center;
  padding: 8px 0;
}

.show-json-btn .n-button {
  color: #64748b;
  font-size: 12px;
}

.show-json-btn .n-button:hover {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .builder-body {
    gap: 14px;
  }
}

@media (max-width: 768px) {
  .builder-body {
    gap: 12px;
  }

  .json-preview {
    padding: 12px;
  }

  .preview-header {
    margin-bottom: 8px;
  }

  .preview-title {
    font-size: 11px;
  }

  .json-output {
    font-size: 10px;
  }
}
</style>
