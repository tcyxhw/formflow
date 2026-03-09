<template>
    <div class="form-preview">
      <n-form
        ref="formRef"
        :model="formData"
        :label-width="config.uiSchema.layout.labelWidth"
        :label-placement="getLabelPlacement()"
        :size="config.uiSchema.layout.size"
      >
        <template v-for="field in config.formSchema.fields" :key="field.id">
          <!-- 普通字段 -->
          <n-form-item
            v-if="!isLayoutField(field.type)"
            :label="field.label"
            :path="field.id"
            :rule="getFieldRule(field)"
          >
            <!-- 字段组件 -->
            <component
              :is="getFieldComponent(field.type)"
              v-model:value="formData[field.id]"
              v-bind="getFieldProps(field)"
            />
            
            <!-- 帮助文本 -->
            <template v-if="field.description" #feedback>
              <span class="field-help">{{ field.description }}</span>
            </template>
          </n-form-item>
          
          <!-- 分割线 -->
          <n-divider v-else-if="field.type === FieldType.DIVIDER" />
          
          <!-- 描述文本 -->
          <div v-else-if="field.type === FieldType.DESCRIPTION" class="description-text">
            {{ field.props.content }}
          </div>
        </template>
        
        <!-- 提交按钮 -->
        <n-form-item>
          <n-space>
            <n-button type="primary" @click="handleSubmit">
              提交
            </n-button>
            <n-button @click="handleReset">
              重置
            </n-button>
          </n-space>
        </n-form-item>
      </n-form>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, reactive, watch, onMounted } from 'vue'
  import { useMessage } from 'naive-ui'
  import type { FormInst, FormItemRule } from 'naive-ui'
  import type { FormConfig, FormSubmissionPayload } from '@/types/form'
  import type { FormField } from '@/types/field'
  import { FieldType } from '@/types/field'

  interface Props {
    config: FormConfig
  }

  const props = defineProps<Props>()
  const emit = defineEmits<{ (e: 'submit', payload: FormSubmissionPayload): void }>()

  const message = useMessage()
  const formRef = ref<FormInst | null>(null)
  type FormValues = Record<string, unknown>
  const formData = reactive<FormValues>({})

  const resolveErrorMessage = (error: unknown, fallback: string) =>
    error instanceof Error ? error.message : fallback

  // ✅ 修复：获取标签位置（确保类型正确）
  const getLabelPlacement = () => {
    const placement = props.config.uiSchema.layout.labelPosition
    // Naive UI 只支持 'left' 和 'top'
    if (placement === 'left' || placement === 'top') {
      return placement
    }
    // 'right' 转换为 'left'（Naive UI 不支持 right）
    return 'left'
  }

  // 初始化表单数据
  const initFormData = () => {
    props.config.formSchema.fields.forEach(field => {
      if (field.defaultValue !== undefined) {
        formData[field.id] = field.defaultValue
      }
    })
  }

  // 是否是布局字段
  const isLayoutField = (type: string) => {
    return [FieldType.DIVIDER, FieldType.DESCRIPTION].includes(type as FieldType)
  }

  // 获取字段组件
  const getFieldComponent = (type: string) => {
    const componentMap: Record<string, string> = {
      [FieldType.TEXT]: 'n-input',
      [FieldType.TEXTAREA]: 'n-input',
      [FieldType.NUMBER]: 'n-input-number',
      [FieldType.PHONE]: 'n-input',
      [FieldType.EMAIL]: 'n-input',
      [FieldType.SELECT]: 'n-select',
      [FieldType.RADIO]: 'n-radio-group',
      [FieldType.CHECKBOX]: 'n-checkbox-group',
      [FieldType.SWITCH]: 'n-switch',
      [FieldType.DATE]: 'n-date-picker',
      [FieldType.DATE_RANGE]: 'n-date-picker',
      [FieldType.TIME]: 'n-time-picker',
      [FieldType.DATETIME]: 'n-date-picker',
      [FieldType.RATE]: 'n-rate',
      [FieldType.UPLOAD]: 'n-upload',
      [FieldType.CALCULATED]: 'n-input',
    }

    return componentMap[type] || 'n-input'
  }

  // 获取字段属性
  const getFieldProps = (field: FormField) => {
    const baseProps = { ...field.props }

    // 特殊处理
    if (field.type === FieldType.TEXTAREA) {
      baseProps.type = 'textarea'
    }

    if (field.type === FieldType.DATE_RANGE) {
      baseProps.type = 'daterange'
    }

    if (field.type === FieldType.DATETIME) {
      baseProps.type = 'datetime'
    }

    if (field.type === FieldType.NUMBER) {
      baseProps.style = { width: '100%' }
    }

    if (field.type === FieldType.CALCULATED) {
      baseProps.readonly = true
    }

    return baseProps
  }

  // 获取字段验证规则
  const getFieldRule = (field: FormField): FormItemRule[] => {
    const rules: FormItemRule[] = []

    // 必填
    if (field.required) {
      rules.push({
        required: true,
        message: `请输入${field.label}`,
        trigger: field.validation?.trigger || 'blur',
      })
    }

    // 自定义验证
    if (field.validation) {
      const { pattern, min, max, message: msg } = field.validation

      if (pattern) {
        rules.push({
          pattern: new RegExp(pattern),
          message: msg || `${field.label}格式不正确`,
          trigger: field.validation.trigger || 'blur',
        })
      }

      if (min !== undefined || max !== undefined) {
        rules.push({
          type: field.type === FieldType.NUMBER ? 'number' : 'string',
          min,
          max,
          message: msg || `${field.label}长度或值不符合要求`,
          trigger: field.validation.trigger || 'blur',
        })
      }
    }

    return rules
  }

  // 计算字段的值更新
  watch(
    () => formData,
    () => {
      updateCalculatedFields()
    },
    { deep: true }
  )

  // ✅ 修复：更新计算字段（添加类型）
  const updateCalculatedFields = () => {
    const calculatedFields = props.config.formSchema.fields.filter(
      f => f.type === FieldType.CALCULATED
    )

    calculatedFields.forEach(field => {
      const formula = field.props.formula as string | undefined
      const dependencies = Array.isArray(field.props.dependencies)
        ? (field.props.dependencies as string[])
        : []

      // 检查依赖字段是否都有值
      const hasAllDeps = dependencies.every((dep: string) => formData[dep] !== undefined)

      if (hasAllDeps && formula) {
        try {
          // 简单的公式计算
          const result = evaluateFormula(formula, formData)
          formData[field.id] = result
        } catch (error) {
          console.error('Formula evaluation error:', error)
        }
      }
    })
  }

  // 简单的公式计算
  const evaluateFormula = (formula: string, context: FormValues) => {
    // 替换变量
    let expression = formula.replace(/\$\{(\w+)\}/g, (match, fieldId) => {
      const value = context[fieldId]
      return typeof value === 'string' ? `"${value}"` : String(value)
    })

    // 简单示例：只处理基本运算
    try {
      // 注意：实际生产环境应该使用安全的表达式计算库

      return eval(expression)
    } catch {
      return null
    }
  }

  // 提交
  const handleSubmit = async () => {
    try {
      await formRef.value?.validate()
      emit('submit', { ...formData })
    } catch (error) {
      message.error(resolveErrorMessage(error, '请检查表单填写'))
    }
  }

  // 重置
  const handleReset = () => {
    formRef.value?.restoreValidation()
    Object.keys(formData).forEach(key => {
      delete formData[key]
    })
    initFormData()
  }
  
  onMounted(() => {
    initFormData()
  })
  </script>
  
  <style scoped lang="scss">
  .form-preview {
    padding: 24px;
    background: #fff;
    border-radius: 8px;
  }
  
  .field-help {
    font-size: 12px;
    color: #6b7280;
  }
  
  .description-text {
    padding: 12px 16px;
    margin-bottom: 24px;
    background: #f9fafb;
    border-radius: 6px;
    font-size: 14px;
    color: #6b7280;
    line-height: 1.6;
  }
  </style>