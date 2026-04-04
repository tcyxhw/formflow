/**
 * 表单设计器状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { FormField } from '@/types/field'
import type { FormSchema, UISchema, LayoutConfig } from '@/types/schema'
import type { LogicSchema } from '@/types/logic'
import type { FormConfig, FormDetailResponse } from '@/types/form'

import { AccessMode } from '@/types/form'
import { generateFieldId } from '@/utils/idGenerator'
import { FIELD_TEMPLATES } from '@/constants/fieldTemplates'

export const useFormDesignerStore = defineStore('formDesigner', () => {
  // 基础信息
  const formId = ref<number>()
  const formName = ref('未命名表单')
  const formCategory = ref('')
  const accessMode = ref<AccessMode>(AccessMode.AUTHENTICATED)
  const allowEdit = ref(false)
  const maxEditCount = ref(0)
  const submitDeadline = ref<string>()
  const flowDefinitionId = ref<number>()
  
  // 字段列表
  const fields = ref<FormField[]>([])
  
  // 选中的字段
  const selectedFieldId = ref<string>()
  
  // UI配置
  const uiSchema = ref<UISchema>({
    layout: {
      type: 'vertical',
      labelWidth: 120,
      labelPosition: 'right',
      size: 'medium',
    },
    rows: [],
    groups: [],
  })
  
  // 逻辑规则
  const logicSchema = ref<LogicSchema>({
    rules: [],
  })
  
  // 脏标记：是否有未保存的更改
  const dirty = ref(false)
  
  // 计算属性
  const selectedField = computed(() => {
    return fields.value.find(f => f.id === selectedFieldId.value)
  })
  
  const fieldMap = computed(() => {
    const map = new Map<string, FormField>()
    fields.value.forEach(f => map.set(f.id, f))
    return map
  })
  
  // 方法
  const toAccessMode = (value: string | undefined): AccessMode => {
    if (value === AccessMode.PUBLIC) {
      return AccessMode.PUBLIC
    }
    return AccessMode.AUTHENTICATED
  }

  const addField = (fieldType: string) => {
    const template = FIELD_TEMPLATES[fieldType as keyof typeof FIELD_TEMPLATES]
    if (!template) return
    
    const newField: FormField = {
      ...template,
      id: generateFieldId(),
      type: template.type!,
      label: template.label!,
      required: template.required ?? false,
      props: { ...template.props },
    } as FormField
    
    fields.value.push(newField)
    selectedFieldId.value = newField.id
    dirty.value = true

    console.log('✅ Field added:', newField)
    console.log('✅ Total fields:', fields.value.length)
    console.log('✅ Fields array:', fields.value)
  }
  
  const updateField = (fieldId: string, updates: Partial<FormField>) => {
    const index = fields.value.findIndex(f => f.id === fieldId)
    if (index !== -1) {
      fields.value[index] = { ...fields.value[index], ...updates }
      dirty.value = true
    }
  }
  
  const deleteField = (fieldId: string) => {
    const index = fields.value.findIndex(f => f.id === fieldId)
    if (index !== -1) {
      fields.value.splice(index, 1)
      if (selectedFieldId.value === fieldId) {
        selectedFieldId.value = undefined
      }
      dirty.value = true
    }
  }
  
  const moveField = (fromIndex: number, toIndex: number) => {
    const field = fields.value.splice(fromIndex, 1)[0]
    fields.value.splice(toIndex, 0, field)
    dirty.value = true
  }
  
  const selectField = (fieldId: string) => {
    selectedFieldId.value = fieldId
  }
  
  const clearSelection = () => {
    selectedFieldId.value = undefined
  }
  
  const getFormConfig = (): FormConfig => {
    return {
      id: formId.value,
      name: formName.value,
      category: formCategory.value,
      accessMode: accessMode.value,
      allowEdit: allowEdit.value,
      maxEditCount: maxEditCount.value,
      submitDeadline: submitDeadline.value,
      formSchema: {
        version: '1.0.0',
        fields: fields.value,
        fieldOrder: fields.value.map(f => f.id),
      },
      uiSchema: uiSchema.value,
      logicSchema: logicSchema.value,
    }
  }
  
  const loadFormConfig = (config: FormDetailResponse) => {
    formId.value = config.id
    formName.value = config.name
    formCategory.value = config.category || ''

    accessMode.value = toAccessMode(config.access_mode)

    allowEdit.value = config.allow_edit || false
    maxEditCount.value = config.max_edit_count || 0
    submitDeadline.value = config.submit_deadline
    flowDefinitionId.value = config.flow_definition_id
    
    if (config.schema_json) {
      fields.value = config.schema_json.fields || []
    }
    
    if (config.ui_schema_json) {
      uiSchema.value = config.ui_schema_json
    }
    
    if (config.logic_json) {
      logicSchema.value = config.logic_json
    }
    
    dirty.value = false
  }
  
  const reset = () => {
    formId.value = undefined
    formName.value = '未命名表单'
    formCategory.value = ''
    accessMode.value = AccessMode.AUTHENTICATED
    allowEdit.value = false
    maxEditCount.value = 0
    submitDeadline.value = undefined
    flowDefinitionId.value = undefined
    fields.value = []
    selectedFieldId.value = undefined
    uiSchema.value = {
      layout: {
        type: 'vertical',
        labelWidth: 120,
        labelPosition: 'right',
        size: 'medium',
      },
      rows: [],
      groups: [],
    }
    logicSchema.value = {
      rules: [],
    }
    dirty.value = false
  }
  
  return {
    // 状态
    formId,
    formName,
    formCategory,
    accessMode,
    allowEdit,
    maxEditCount,
    submitDeadline,
    flowDefinitionId,
    fields,
    selectedFieldId,
    uiSchema,
    logicSchema,
    dirty,
    
    // 计算属性
    selectedField,
    fieldMap,
    
    // 方法
    addField,
    updateField,
    deleteField,
    moveField,
    selectField,
    clearSelection,
    getFormConfig,
    loadFormConfig,
    reset,
  }
})