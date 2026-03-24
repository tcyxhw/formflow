<template>
  <div class="route-inspector">
    <div class="inspector-header">
      <div class="title">路由属性</div>
      <div class="subtitle">配置路由优先级和 JsonLogic 条件</div>
    </div>

    <div v-if="routeComputed" class="inspector-body">
      <!-- 路由信息提示 -->
      <div class="route-info-banner">
        <div class="route-info-title">当前路由</div>
        <div class="route-info-description">{{ getRouteDescription(routeComputed) }}</div>
      </div>

      <n-form label-width="88" label-placement="left" size="small">
        <n-form-item label="来源节点">
          <n-select
            :value="routeComputed && routeComputed.from_node_key ? routeComputed.from_node_key : ''"
            :options="nodeOptions"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ from_node_key: val })"
          />
        </n-form-item>

        <n-form-item label="目标节点">
          <n-select
            :value="routeComputed && routeComputed.to_node_key ? routeComputed.to_node_key : ''"
            :options="nodeOptions"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ to_node_key: val })"
          />
        </n-form-item>

        <n-form-item label="优先级">
          <n-input-number
            :value="priorityValue"
            :min="1"
            :max="999"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ priority: val ?? 1 })"
          />
        </n-form-item>

        <n-form-item label="默认路由">
          <n-switch
            :value="isDefaultValue"
            :disabled="disabled"
            @update:value="(val) => emitPatch({ is_default: val })"
          />
        </n-form-item>

        <n-divider>条件设置</n-divider>

        <div class="condition-config">
          <div class="config-header">
            <span class="config-title">路由条件配置</span>
            <span class="condition-status">
              {{ routeComputed && routeComputed.condition ? '已设置条件' : '未设置条件' }}
            </span>
          </div>
          
          <!-- 条件详情展示 -->
          <div v-if="routeComputed && routeComputed.condition" class="condition-details">
            <div class="condition-content">
              {{ formatConditionForDisplay(routeComputed.condition) }}
            </div>
          </div>
          <div v-else class="condition-placeholder">
            <n-text depth="3" style="font-size: 12px;">未设置条件</n-text>
          </div>
          
          <div class="config-actions">
            <n-button type="primary" size="small" :disabled="disabled" @click="openConditionModal">
              编辑条件
            </n-button>
            <n-button
              v-if="routeComputed && routeComputed.condition"
              type="error"
              size="small"
              :disabled="disabled"
              @click="clearCondition"
            >
              清空条件
            </n-button>
            <n-button
              v-if="showJsonEditor"
              quaternary
              size="small"
              @click="showJsonEditor = false"
            >
              隐藏 JSON
            </n-button>
            <n-button
              v-else
              quaternary
              size="small"
              @click="showJsonEditor = true"
            >
              显示 JSON
            </n-button>
          </div>
        </div>

        <!-- JSON 编辑器（可选） -->
        <n-form-item
          v-if="showJsonEditor"
          :feedback="conditionError"
          :validation-status="conditionError ? 'error' : undefined"
          class="json-editor-item"
        >
          <template #label>
            <span class="json-label">JsonLogic JSON（高级）</span>
          </template>
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

    <!-- 条件编辑模态框 -->
    <n-modal
      v-model:show="showConditionModal"
      title="编辑路由条件"
      preset="dialog"
      :style="{ width: '90vw', maxWidth: '1200px' }"
      :mask-closable="false"
    >
      <template #header>
        <div class="modal-header-custom">
          <div class="modal-title-main">编辑路由条件</div>
          <div class="modal-subtitle">{{ getRouteDescription(routeComputed!) }}</div>
          <div class="modal-subtitle-secondary">配置表单字段的条件规则，支持多条件组合</div>
        </div>
      </template>
      <div class="condition-modal-content">
        <!-- 路由信息提示 -->
        <div class="route-info-section">
          <div class="route-info-label">当前编辑的路由</div>
          <div class="route-info-text">{{ getRouteDescription(routeComputed!) }}</div>
        </div>

        <!-- 已添加条件列表区域 -->
        <div v-if="conditionsList.length > 0" class="conditions-list-section">
          <div class="list-header">
            <span class="list-title">已添加的条件</span>
            <span class="list-count">共 {{ conditionsList.length }} 个</span>
          </div>
          <div class="conditions-list">
            <div v-for="(cond, idx) in conditionsList" :key="idx" class="condition-item">
              <div class="condition-text">
                {{ formatConditionForDisplay(cond) }}
              </div>
              <div class="condition-actions">
                <n-button
                  type="primary"
                  text
                  size="small"
                  @click="editConditionItem(idx)"
                >
                  编辑
                </n-button>
                <n-button
                  type="error"
                  text
                  size="small"
                  @click="deleteConditionItem(idx)"
                >
                  删除
                </n-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 新条件构建器区域 -->
        <div class="new-condition-section">
          <div class="section-header">
            <span class="section-title">{{ conditionsList.length > 0 ? '添加新条件' : '添加条件' }}</span>
          </div>
          <ConditionBuilderV2
            v-if="editingCondition"
            :form-schema="formSchema"
            :form-id="formId"
            :model-value="editingCondition"
            :disabled="disabled"
            @update:model-value="(val) => (editingCondition = val)"
          />
        </div>
      </div>
      <template #action>
        <n-space>
          <n-button @click="cancelCondition">取消</n-button>
          <n-button type="primary" @click="saveAllConditions">保存所有条件</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { NButton, NSpace, NDivider, NFormItem, NInput, NSelect, NInputNumber, NSwitch, NModal, NEmpty, NIcon, NText, NTag, useDialog } from 'naive-ui'
import ConditionBuilderV2 from './ConditionBuilderV2.vue'
import { FlowNodeConfig, FlowRouteConfig, JsonLogicExpression } from '@/types/flow'
import { FormSchema } from '@/types/schema'
import { ConditionNode } from '@/types/condition'
import FieldLabelService from '@/services/fieldLabelService'
import { getFormFields } from '@/api/form'

// 将 ConditionNode 转换为 JsonLogic 格式
const conditionNodeToJsonLogic = (node: ConditionNode | null): JsonLogicExpression | null => {
  if (!node) return null
  
  if (node.type === 'RULE') {
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

// 将 JsonLogic 格式转换为可读文本
const formatConditionForDisplay = (json: any): string => {
  if (!json || Object.keys(json).length === 0) {
    return '未设置条件'
  }
  
  // 获取字段的显示名称（优先使用 API 加载的字段标签）
  const getFieldLabel = (fieldKey: string): string => {
    console.log('[FlowRouteInspector] getFieldLabel called:', {
      fieldKey,
      hasFieldLabelMap: Object.keys(fieldLabelMap.value).length > 0,
      fieldLabelMapKeys: Object.keys(fieldLabelMap.value),
      fieldLabelMapValue: fieldLabelMap.value[fieldKey],
      hasFormSchema: !!props.formSchema,
      formSchemaFields: props.formSchema?.fields?.length ?? 0,
      formSchemaFieldsSample: props.formSchema?.fields?.slice(0, 2).map((f: any) => ({ id: f.id, label: f.label }))
    })
    
    // 优先使用从 API 加载的字段标签映射
    if (fieldLabelMap.value[fieldKey]) {
      console.log('[FlowRouteInspector] getFieldLabel result:', {
        fieldKey,
        resolvedLabel: fieldLabelMap.value[fieldKey]
      })
      return fieldLabelMap.value[fieldKey]
    }
    
    // 备用方案：使用 FieldLabelService 从 formSchema 获取
    if (props.formSchema) {
      const label = FieldLabelService.getFieldLabel(fieldKey, props.formSchema)
      if (label !== fieldKey) {
        console.log('[FlowRouteInspector] getFieldLabel result (from formSchema):', {
          fieldKey,
          resolvedLabel: label
        })
        return label
      }
    }
    
    // 最后返回字段键本身
    console.log('[FlowRouteInspector] getFieldLabel result:', {
      fieldKey,
      resolvedLabel: fieldKey
    })
    return fieldKey
  }
  
  // 获取操作符的显示文本
  const getOperatorText = (operator: string): string => {
    const operatorMap: Record<string, string> = {
      '==': '等于',
      'eq': '等于',
      '!=': '不等于',
      'neq': '不等于',
      '>': '大于',
      'gt': '大于',
      '>=': '大于等于',
      'gte': '大于等于',
      '<': '小于',
      'lt': '小于',
      '<=': '小于等于',
      'lte': '小于等于',
      'in': '包含于',
      '!': '非'
    }
    return operatorMap[operator] || operator
  }
  
  // 格式化值的显示
  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return '空'
    if (Array.isArray(value)) return value.join(', ')
    if (typeof value === 'object') return JSON.stringify(value)
    return String(value)
  }
  
  // 递归处理 JsonLogic 表达式
  const formatExpression = (expr: any, depth: number = 0): string => {
    if (!expr || typeof expr !== 'object') return String(expr)
    
    // 处理 AND 逻辑组
    if (expr.and) {
      const conditions = Array.isArray(expr.and) ? expr.and : [expr.and]
      const formatted = conditions.map((c: any) => formatExpression(c, depth + 1))
      const separator = depth > 0 ? ' 且 ' : ' 且 '
      return depth > 0 ? `(${formatted.join(separator)})` : formatted.join(separator)
    }
    
    // 处理 OR 逻辑组
    if (expr.or) {
      const conditions = Array.isArray(expr.or) ? expr.or : [expr.or]
      const formatted = conditions.map((c: any) => formatExpression(c, depth + 1))
      const separator = depth > 0 ? ' 或 ' : ' 或 '
      return depth > 0 ? `(${formatted.join(separator)})` : formatted.join(separator)
    }
    
    // 处理 NOT 逻辑
    if (expr['!']) {
      const inner = formatExpression(expr['!'], depth + 1)
      return `非(${inner})`
    }
    
    // 处理二元操作符
    const operators = ['==', 'eq', '!=', 'neq', '>', 'gt', '>=', 'gte', '<', 'lt', '<=', 'lte']
    for (const op of operators) {
      if (expr[op]) {
        const [field, value] = expr[op]
        if (field?.var) {
          const fieldLabel = getFieldLabel(field.var)
          const operatorText = getOperatorText(op)
          const valueText = formatValue(value)
          return `${fieldLabel} ${operatorText} ${valueText}`
        }
      }
    }
    
    // 处理 IN 操作符
    if (expr.in) {
      const [value, field] = expr.in
      if (field?.var) {
        const fieldLabel = getFieldLabel(field.var)
        const valueText = formatValue(value)
        return `${valueText} 包含于 ${fieldLabel}`
      }
    }
    
    return JSON.stringify(expr)
  }
  
  return formatExpression(json)
}

// 从 JsonLogic 格式初始化 ConditionNode
const jsonLogicToConditionNode = (json: any): ConditionNode | null => {
  console.log('[jsonLogicToConditionNode] Input:', {
    hasInput: !!json,
    inputType: typeof json,
    inputKeys: json ? Object.keys(json) : [],
    inputValue: json
  })
  
  // 处理边界情况：null、undefined
  if (!json) {
    console.log('[jsonLogicToConditionNode] Input is null/undefined, returning null')
    return null
  }
  
  // 处理边界情况：空对象
  if (typeof json === 'object' && Object.keys(json).length === 0) {
    console.log('[jsonLogicToConditionNode] Input is empty object, returning null')
    return null
  }
  
  // 处理 AND/OR 逻辑组
  if (json.and || json.or) {
    const isAnd = !!json.and
    const conditions = isAnd ? json.and : json.or
    const logic: 'AND' | 'OR' = isAnd ? 'AND' : 'OR'
    
    console.log('[jsonLogicToConditionNode] Processing logic group:', {
      logic,
      conditionsType: typeof conditions,
      isArray: Array.isArray(conditions),
      conditionsLength: Array.isArray(conditions) ? conditions.length : 1
    })
    
    const children: ConditionNode[] = []
    const conditionArray = Array.isArray(conditions) ? conditions : [conditions]
    
    for (let i = 0; i < conditionArray.length; i++) {
      const condition = conditionArray[i]
      console.log(`[jsonLogicToConditionNode] Processing child ${i}:`, condition)
      
      const child = jsonLogicToConditionNode(condition)
      if (child) {
        console.log(`[jsonLogicToConditionNode] Child ${i} converted successfully:`, {
          type: child.type,
          fieldKey: child.type === 'RULE' ? child.fieldKey : undefined
        })
        children.push(child)
      } else {
        console.warn(`[jsonLogicToConditionNode] Child ${i} conversion returned null`)
      }
    }
    
    if (children.length === 0) {
      console.warn('[jsonLogicToConditionNode] No valid children, returning null')
      return null
    }
    
    const result = { type: 'GROUP' as const, logic, children }
    console.log('[jsonLogicToConditionNode] GROUP result:', {
      logic,
      childrenCount: children.length
    })
    return result
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
      console.log(`[jsonLogicToConditionNode] Found operator: ${jsonOp}`, json[jsonOp])
      
      const operands = json[jsonOp]
      if (!Array.isArray(operands) || operands.length < 2) {
        console.warn(`[jsonLogicToConditionNode] Invalid operands for ${jsonOp}:`, operands)
        continue
      }
      
      const [field, value] = operands
      console.log('[jsonLogicToConditionNode] Operands:', { field, value })
      
      if (field?.var) {
        const result = { 
          type: 'RULE' as const, 
          fieldKey: field.var, 
          fieldType: 'TEXT' as any, 
          operator: nodeOp as any, 
          value 
        }
        console.log('[jsonLogicToConditionNode] RULE result:', {
          fieldKey: result.fieldKey,
          operator: result.operator,
          value: result.value
        })
        return result
      } else {
        console.warn('[jsonLogicToConditionNode] Field does not have var property:', field)
      }
    }
  }
  
  // 处理 IN 操作符
  if (json.in) {
    console.log('[jsonLogicToConditionNode] Found IN operator:', json.in)
    
    const operands = json.in
    if (!Array.isArray(operands) || operands.length < 2) {
      console.warn('[jsonLogicToConditionNode] Invalid operands for IN:', operands)
    } else {
      const [value, field] = operands
      console.log('[jsonLogicToConditionNode] IN operands:', { value, field })
      
      if (field?.var) {
        const result = { 
          type: 'RULE' as const, 
          fieldKey: field.var, 
          fieldType: 'TEXT' as any, 
          operator: 'IN' as any, 
          value 
        }
        console.log('[jsonLogicToConditionNode] IN RULE result:', {
          fieldKey: result.fieldKey,
          operator: result.operator,
          value: result.value
        })
        return result
      } else {
        console.warn('[jsonLogicToConditionNode] Field does not have var property:', field)
      }
    }
  }
  
  console.warn('[jsonLogicToConditionNode] No matching pattern found, returning null')
  return null
}

interface Props {
  route?: FlowRouteConfig
  nodeOptions: { label: string; value: string }[]
  selectedIndex: number | null
  disabled?: boolean
  formSchema?: FormSchema
  formId?: number
  nodes?: FlowNodeConfig[]
  routes?: FlowRouteConfig[]
  currentNodeKey?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update-route', payload: { index: number; patch: Partial<FlowRouteConfig> }): void
}>()

const routeComputed = computed(() => props.route)

// 获取与当前节点相关的路由（进入该节点的路由）
const relevantRoutes = computed(() => {
  if (!props.currentNodeKey || !props.routes) return []
  
  // 只显示进入当前节点的路由（to_node_key = 当前节点）
  const filtered = props.routes.filter(route => route.to_node_key === props.currentNodeKey)
  console.log('[FlowRouteInspector] relevantRoutes computed:', {
    currentNodeKey: props.currentNodeKey,
    totalRoutes: props.routes.length,
    filteredRoutes: filtered.length,
    routes: filtered.map(r => ({ id: r.id, from: r.from_node_key, to: r.to_node_key }))
  })
  return filtered
})

// 获取路由的描述信息（从哪个节点到哪个节点）
const getRouteDescription = (route: FlowRouteConfig): string => {
  if (!props.nodes) return ''
  
  const fromNode = props.nodes.find(n => {
    // 优先使用 temp_id，其次使用 id 转换为字符串
    const nodeKey = n.temp_id || (n.id ? String(n.id) : '')
    return nodeKey === route.from_node_key
  })
  
  const toNode = props.nodes.find(n => {
    // 优先使用 temp_id，其次使用 id 转换为字符串
    const nodeKey = n.temp_id || (n.id ? String(n.id) : '')
    return nodeKey === route.to_node_key
  })
  
  const fromName = fromNode?.name || '未知节点'
  const toName = toNode?.name || '未知节点'
  
  return `从 ${fromName} 到 ${toName}`
}
const conditionDraft = ref('')
const conditionError = ref('')
const showJsonEditor = ref(false)

// 字段标签映射（从 API 加载）
const fieldLabelMap = ref<Record<string, string>>({})
// 添加一个标志位，用于触发条件显示的重新计算
const fieldLabelsLoaded = ref(false)

// 加载字段标签映射
const loadFieldLabels = async () => {
  console.log('[FlowRouteInspector] loadFieldLabels called:', {
    formId: props.formId,
    hasFormId: !!props.formId
  })
  
  if (!props.formId) {
    console.warn('[FlowRouteInspector] No formId, cannot load field labels')
    return
  }
  
  try {
    console.log('[FlowRouteInspector] Calling getFormFields API with formId:', props.formId)
    const response = await getFormFields(props.formId)
    console.log('[FlowRouteInspector] getFormFields API response:', {
      hasResponse: !!response,
      hasData: !!response.data,
      dataKeys: response.data ? Object.keys(response.data) : [],
      fullResponse: response
    })
    
    const map: Record<string, string> = {}
    
    // 处理表单字段
    if (response.data?.fields) {
      console.log('[FlowRouteInspector] Processing fields:', {
        count: response.data.fields.length,
        sample: response.data.fields.slice(0, 2)
      })
      response.data.fields.forEach((field: any) => {
        map[field.key] = field.name
      })
    } else {
      console.warn('[FlowRouteInspector] No fields in response.data')
    }
    
    // 处理系统字段
    if (response.data?.system_fields) {
      console.log('[FlowRouteInspector] Processing system_fields:', {
        count: response.data.system_fields.length,
        sample: response.data.system_fields.slice(0, 2)
      })
      response.data.system_fields.forEach((field: any) => {
        map[field.key] = field.name
      })
    } else {
      console.warn('[FlowRouteInspector] No system_fields in response.data')
    }
    
    fieldLabelMap.value = map
    fieldLabelsLoaded.value = true
    console.log('[FlowRouteInspector] Field labels loaded successfully:', {
      count: Object.keys(map).length,
      keys: Object.keys(map),
      map
    })
  } catch (error) {
    console.error('[FlowRouteInspector] Failed to load field labels:', error)
    fieldLabelsLoaded.value = true
  }
}

// 监听 formId 变化，重新加载字段标签
watch(
  () => props.formId,
  (newFormId) => {
    fieldLabelsLoaded.value = false
    if (newFormId) {
      loadFieldLabels()
    }
  },
  { immediate: true }
)

// 组件挂载时加载字段标签
onMounted(() => {
  if (props.formId) {
    loadFieldLabels()
  }
})

// 优先级计算属性
const priorityValue = computed(() => {
  if (routeComputed.value && routeComputed.value.priority) {
    return routeComputed.value.priority
  }
  return 1
})

// 默认路由计算属性
const isDefaultValue = computed(() => {
  if (routeComputed.value && routeComputed.value.is_default) {
    return true
  }
  return false
})

// 条件编辑模态框状态
const showConditionModal = ref(false)
const editingCondition = ref<ConditionNode | null>(null)
const conditionsList = ref<JsonLogicExpression[]>([])
const editingIndex = ref<number | null>(null)

// 使用 Naive UI 的对话框
let dialog: any = null
try {
  dialog = useDialog()
} catch (e) {
  // 在测试环境中可能没有 NDialogProvider，使用 null 作为备选
  console.warn('[FlowRouteInspector] Failed to initialize dialog:', e)
}

// 清空条件
const clearCondition = () => {
  if (!dialog) {
    // 在测试环境中直接清空条件
    handleConditionUpdate(null)
    conditionDraft.value = ''
    conditionError.value = ''
    return
  }
  
  dialog.warning({
    title: '确认清空条件',
    content: '确定要清空当前路由的所有条件吗？此操作不可撤销。',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: () => {
      console.log('[FlowRouteInspector] Clearing condition', {
        routeKey: `${routeComputed.value?.from_node_key} -> ${routeComputed.value?.to_node_key}`,
        selectedIndex: props.selectedIndex
      })
      // 将条件设置为 null
      handleConditionUpdate(null)
      // 清空 JSON 编辑器的内容
      conditionDraft.value = ''
      conditionError.value = ''
    }
  })
}

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
  
  console.log('[FlowRouteInspector] Emitting route patch', {
    selectedIndex: props.selectedIndex,
    routeKey: `${routeComputed.value?.from_node_key} -> ${routeComputed.value?.to_node_key}`,
    patch
  })
  
  emit('update-route', { index: props.selectedIndex, patch })
}

// 打开条件编辑模态框
const openConditionModal = () => {
  console.log('[FlowRouteInspector] Opening condition modal')
  
  // 初始化条件列表
  const currentCondition = routeComputed.value?.condition
  
  if (currentCondition) {
    // 如果是 AND/OR 组，则列表中包含所有子条件
    if (currentCondition.and) {
      conditionsList.value = Array.isArray(currentCondition.and) ? currentCondition.and : [currentCondition.and]
    } else if (currentCondition.or) {
      conditionsList.value = Array.isArray(currentCondition.or) ? currentCondition.or : [currentCondition.or]
    } else {
      // 单个条件
      conditionsList.value = [currentCondition]
    }
  } else {
    conditionsList.value = []
  }
  
  // 初始化编辑条件为空的 GROUP（用于添加新条件）
  editingCondition.value = {
    type: 'GROUP',
    logic: 'AND' as const,
    children: []
  }
  
  editingIndex.value = null
  
  showConditionModal.value = true
}

// 编辑条件项
const editConditionItem = (idx: number) => {
  const jsonLogic = conditionsList.value[idx]
  const converted = jsonLogicToConditionNode(jsonLogic)
  
  if (converted?.type === 'RULE') {
    editingCondition.value = {
      type: 'GROUP',
      logic: 'AND' as const,
      children: [converted]
    }
  } else if (converted?.type === 'GROUP') {
    editingCondition.value = converted
  } else {
    editingCondition.value = {
      type: 'GROUP',
      logic: 'AND' as const,
      children: []
    }
  }
  editingIndex.value = idx
}

// 删除条件项
const deleteConditionItem = (idx: number) => {
  if (!dialog) {
    // 在测试环境中直接删除条件
    conditionsList.value.splice(idx, 1)
    // 如果删除的是正在编辑的条件，清空编辑器
    if (editingIndex.value === idx) {
      editingCondition.value = {
        type: 'GROUP',
        logic: 'AND' as const,
        children: []
      }
      editingIndex.value = null
    }
    return
  }
  
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这个条件吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: () => {
      conditionsList.value.splice(idx, 1)
      // 如果删除的是正在编辑的条件，清空编辑器
      if (editingIndex.value === idx) {
        editingCondition.value = {
          type: 'GROUP',
          logic: 'AND' as const,
          children: []
        }
        editingIndex.value = null
      }
    }
  })
}

// 保存所有条件
const saveAllConditions = () => {
  console.log('[FlowRouteInspector] Saving all conditions', {
    currentRoute: routeComputed.value,
    selectedIndex: props.selectedIndex,
    conditionsListLength: conditionsList.value.length,
    editingConditionHasChildren: editingCondition.value?.children?.length ?? 0
  })

  // 如果编辑器中有新条件，先添加到列表
  if (editingCondition.value && editingCondition.value.children && editingCondition.value.children.length > 0) {
    const newJsonLogic = conditionNodeToJsonLogic(editingCondition.value)
    if (newJsonLogic) {
      if (editingIndex.value !== null) {
        // 更新现有条件
        console.log('[FlowRouteInspector] Updating existing condition at index', editingIndex.value)
        conditionsList.value[editingIndex.value] = newJsonLogic
      } else {
        // 添加新条件
        console.log('[FlowRouteInspector] Adding new condition')
        conditionsList.value.push(newJsonLogic)
      }
    }
  }
  
  // 将条件列表转换为最终的 JsonLogic 格式
  let finalCondition: JsonLogicExpression | null = null
  
  if (conditionsList.value.length === 0) {
    finalCondition = null
  } else if (conditionsList.value.length === 1) {
    finalCondition = conditionsList.value[0]
  } else {
    // 多个条件用 AND 连接
    finalCondition = { and: conditionsList.value }
  }
  
  console.log('[FlowRouteInspector] Final condition to save', {
    finalCondition,
    routeKey: `${routeComputed.value?.from_node_key} -> ${routeComputed.value?.to_node_key}`
  })

  handleConditionUpdate(finalCondition)
  showConditionModal.value = false
  editingCondition.value = null
  conditionsList.value = []
  editingIndex.value = null
}

// 取消条件编辑
const cancelCondition = () => {
  showConditionModal.value = false
  editingCondition.value = null
  conditionsList.value = []
  editingIndex.value = null
}

const handleConditionUpdate = (condition: JsonLogicExpression | null) => {
  conditionDraft.value = condition ? JSON.stringify(condition, null, 2) : ''
  conditionError.value = ''
  emitPatch({ condition })
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

.condition-config {
  padding: 12px;
  background: #f9fbfc;
  border-radius: 6px;
  border: 1px solid #e0e5ec;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 12px;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-title {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}

.condition-status {
  font-size: 12px;
  color: #6b7385;
}

.condition-details {
  padding: 10px 12px;
  background: #ffffff;
  border-radius: 4px;
  border: 1px solid #d1d5db;
}

.condition-content {
  font-size: 13px;
  color: #374151;
  line-height: 1.6;
  word-break: break-word;
}

.condition-placeholder {
  padding: 10px 12px;
  text-align: center;
}

.config-actions {
  display: flex;
  gap: 8px;
}

.condition-header {
  margin-bottom: 8px;
}

.condition-tip {
  font-size: 12px;
  color: #6b7385;
  font-weight: 500;
}

.json-label {
  font-size: 12px;
  font-weight: 500;
  color: #6b7385;
}

.json-editor-item {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e0e5ec;
}

.condition-modal-content {
  padding: 16px 0;
  max-height: 60vh;
  overflow-y: auto;
}

.modal-header-custom {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.modal-title-main {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.modal-subtitle {
  font-size: 14px;
  color: #0369a1;
  font-weight: 600;
}

.modal-subtitle-secondary {
  font-size: 13px;
  color: #6b7385;
  font-weight: 400;
}

/* 路由信息横幅 */
.route-info-banner {
  padding: 12px 16px;
  background: linear-gradient(135deg, #e0f2fe 0%, #f0f9ff 100%);
  border-radius: 6px;
  border-left: 4px solid #0284c7;
  margin-bottom: 16px;
}

.route-info-title {
  font-size: 12px;
  font-weight: 600;
  color: #0c4a6e;
  margin-bottom: 4px;
}

.route-info-description {
  font-size: 13px;
  color: #0369a1;
  font-weight: 500;
}

/* 条件编辑弹窗中的路由信息 */
.route-info-section {
  padding: 12px 16px;
  background: linear-gradient(135deg, #e0f2fe 0%, #f0f9ff 100%);
  border-radius: 6px;
  border-left: 4px solid #0284c7;
  margin-bottom: 16px;
}

.route-info-label {
  font-size: 12px;
  font-weight: 600;
  color: #0c4a6e;
  margin-bottom: 4px;
}

.route-info-text {
  font-size: 13px;
  color: #0369a1;
  font-weight: 500;
}

.condition-preview-section {
  margin-bottom: 20px;
  padding: 12px 16px;
  background: #f0f7ff;
  border-radius: 6px;
  border: 1px solid #bfdbfe;
}

.preview-header {
  margin-bottom: 8px;
}

.preview-label {
  font-size: 12px;
  font-weight: 600;
  color: #1e40af;
}

.preview-content {
  padding: 8px 12px;
  background: #ffffff;
  border-radius: 4px;
  border: 1px solid #dbeafe;
  line-height: 1.6;
}

.conditions-list-section {
  margin-bottom: 24px;
  padding: 16px;
  background: #f0f7ff;
  border-radius: 6px;
  border: 1px solid #bfdbfe;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.list-title {
  font-size: 13px;
  font-weight: 600;
  color: #1e40af;
}

.list-count {
  font-size: 12px;
  color: #6b7385;
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
  padding: 12px;
  background: #ffffff;
  border-radius: 4px;
  border: 1px solid #dbeafe;
}

.condition-text {
  flex: 1;
  font-size: 13px;
  color: #374151;
  line-height: 1.6;
  word-break: break-word;
}

.condition-actions {
  display: flex;
  gap: 8px;
  margin-left: 12px;
  flex-shrink: 0;
}

.new-condition-section {
  padding: 16px;
  background: #f9fbfc;
  border-radius: 6px;
  border: 1px solid #e0e5ec;
}

.section-header {
  margin-bottom: 16px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}
</style>
