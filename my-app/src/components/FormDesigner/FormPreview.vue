<template>
    <div class="form-preview">
      <n-form
        ref="formRef"
        :model="formData"
        :label-width="config.uiSchema?.layout?.labelWidth || '120px'"
        :label-placement="getLabelPlacement()"
        :size="config.uiSchema?.layout?.size"
      >
        <template v-for="field in visibleFields" :key="field.id">
          <n-form-item
            v-if="!isLayoutField(field.type) && !isUploadField(field.type)"
            :label="field.label"
            :path="field.id"
            :rule="getFieldRule(field)"
          >
            <component
              :is="getFieldComponent(field.type)"
              v-model:value="formData[field.id]"
              v-bind="getFieldProps(field)"
              @update:value="handleFieldChange(field.id)"
            />
            
            <template v-if="field.description" #feedback>
              <span class="field-help">{{ field.description }}</span>
            </template>
          </n-form-item>
          
          <n-form-item
            v-else-if="isUploadField(field.type)"
            :label="field.label"
            :path="field.id"
            :rule="getFieldRule(field)"
          >
            <n-space vertical>
              <!-- 已上传文件列表 -->
              <n-space v-if="uploadFileLists[field.id] && uploadFileLists[field.id].length > 0" wrap>
                <div
                  v-for="(file, index) in uploadFileLists[field.id]"
                  :key="file.id || index"
                  class="uploaded-file-item"
                >
                  <!-- 图片预览 -->
                  <template v-if="isImageFile(file)">
                    <div class="image-preview-container">
                      <AuthImage
                        :src="file.url || file.thumbnailUrl || ''"
                        :alt="file.name"
                        :width="100"
                        :height="100"
                        object-fit="cover"
                        :preview-src="file.url || file.thumbnailUrl || ''"
                        fallback-src="/image-placeholder.png"
                      />
                      <n-button
                        class="delete-btn"
                        type="error"
                        size="small"
                        circle
                        @click="removeFile(field.id, index)"
                      >
                        <template #icon>
                          <n-icon>
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                              <line x1="18" y1="6" x2="6" y2="18"></line>
                              <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                          </n-icon>
                        </template>
                      </n-button>
                    </div>
                  </template>
                  <!-- 非图片文件 -->
                  <template v-else>
                    <div class="file-preview-container">
                      <n-button
                        text
                        type="primary"
                        @click="previewFile(file)"
                      >
                        {{ file.name }}
                      </n-button>
                      <n-button
                        class="delete-btn"
                        type="error"
                        size="small"
                        circle
                        @click="removeFile(field.id, index)"
                      >
                        <template #icon>
                          <n-icon>
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                              <line x1="18" y1="6" x2="6" y2="18"></line>
                              <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                          </n-icon>
                        </template>
                      </n-button>
                    </div>
                  </template>
                </div>
              </n-space>
              
              <!-- 上传按钮 -->
              <n-upload
                :action="getUploadAction()"
                :headers="getUploadHeaders()"
                :max="(field.props.maxCount as number) || 1"
                :multiple="((field.props.maxCount as number) || 1) > 1"
                :accept="field.props.accept as string"
                :file-list="uploadFileLists[field.id] || []"
                @update:file-list="(fileList: UploadFileInfo[]) => handleUploadChange(field.id, fileList)"
                @finish="(event: { file: UploadFileInfo; event?: ProgressEvent }) => handleUploadFinish(field.id, event)"
                @error="(event: { file: UploadFileInfo }) => handleUploadError(field.id, event)"
                :show-file-list="false"
              >
                <n-button>
                  <template #icon>
                    <n-icon :component="uploadIcon" />
                  </template>
                  点击上传
                </n-button>
              </n-upload>
              <span v-if="field.description" class="field-help">{{ field.description }}</span>
            </n-space>
          </n-form-item>
          
          <n-divider v-else-if="field.type === FieldType.DIVIDER" />
          
          <div v-else-if="field.type === FieldType.DESCRIPTION" class="description-text">
            {{ field.props.content }}
          </div>
        </template>
        
        <n-form-item>
          <n-space>
            <template v-if="editMode">
              <n-button type="primary" @click="handleSubmit">
                保存
              </n-button>
            </template>
            <template v-else>
              <n-button type="primary" @click="handleSubmit">
                提交并发起审批
              </n-button>
              <n-button @click="handleSaveAsDraft">
                暂存待发
              </n-button>
            </template>
            <n-button @click="handleReset">
              重置
            </n-button>
          </n-space>
        </n-form-item>
      </n-form>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, reactive, watch, computed } from 'vue'
  import { useMessage, NIcon } from 'naive-ui'
  import type { FormInst, FormItemRule, UploadFileInfo } from 'naive-ui'
  import { CloudUploadOutline as UploadIcon } from '@vicons/ionicons5'
  import type { FormConfig, FormSubmissionPayload } from '@/types/form'
  import type { FormField } from '@/types/field'
  import { FieldType } from '@/types/field'
  import type { LogicRule } from '@/types/logic'
  import { useAuthStore } from '@/stores/auth'
  import AuthImage from '@/components/AuthImage.vue'

  interface Props {
    config: FormConfig
    editMode?: boolean
  }

  const props = withDefaults(defineProps<Props>(), {
    editMode: false
  })
  const emit = defineEmits<{
    (e: 'submit', payload: FormSubmissionPayload): void
    (e: 'saveAsDraft', payload: FormSubmissionPayload): void
  }>()

  const message = useMessage()
  const authStore = useAuthStore()
  const formRef = ref<FormInst | null>(null)
  type FormValues = Record<string, unknown>
  const formData = reactive<FormValues>({})
  const fieldVisibility = reactive<Record<string, boolean>>({})
  const fieldRequired = reactive<Record<string, boolean>>({})
  const uploadFileLists: Record<string, UploadFileInfo[]> = reactive({})

  const uploadIcon = UploadIcon

  const resolveErrorMessage = (error: unknown, fallback: string) =>
    error instanceof Error ? error.message : fallback

  const getLabelPlacement = () => {
    const placement = props.config.uiSchema?.layout?.labelPosition
    if (placement === 'left' || placement === 'top') {
      return placement
    }
    return 'left'
  }

  const getUploadAction = () => {
    return '/api/v1/attachments/upload'
  }

  const getUploadHeaders = () => {
    const token = authStore.accessToken || localStorage.getItem('access_token')
    return {
      Authorization: token ? `Bearer ${token}` : ''
    }
  }

  const handleUploadChange = (fieldId: string, fileList: UploadFileInfo[]) => {
    uploadFileLists[fieldId] = fileList
  }

  const handleUploadFinish = (fieldId: string, event: { file: UploadFileInfo; event?: ProgressEvent }) => {
    const file = event.file
    
    let response = file.response
    
    if (!response && event.event) {
      const xhr = (event.event.target as XMLHttpRequest)
      if (xhr && xhr.responseText) {
        try {
          response = JSON.parse(xhr.responseText)
        } catch (e) {
          console.error('Parse upload response error:', e)
        }
      }
    }
    
    if (response && response.code === 200 && response.data) {
      // 使用下载URL作为图片预览源
      file.url = response.data.download_url || `/api/v1/attachments/${response.data.id}/download`
      file.name = response.data.file_name || file.name
      file.thumbnailUrl = response.data.download_url || `/api/v1/attachments/${response.data.id}/download`
      ;(file as unknown as { attachmentId?: number }).attachmentId = response.data.id
      
      const currentIds: number[] = (formData[fieldId] as number[]) || []
      if (!currentIds.includes(response.data.id)) {
        formData[fieldId] = [...currentIds, response.data.id]
      }
    }
    message.success(`${file.name} 上传成功`)
  }

  const handleUploadError = (fieldId: string, event: { file: UploadFileInfo }) => {
    message.error(`${event.file.name} 上传失败`)
  }

  const removeFile = (fieldId: string, index: number) => {
    const fileList = uploadFileLists[fieldId]
    if (fileList && fileList.length > index) {
      const file = fileList[index]
      fileList.splice(index, 1)
      // 更新表单数据
      const remainingIds = fileList
        .filter(f => f.attachmentId)
        .map(f => f.attachmentId as number)
      formData[fieldId] = remainingIds
      message.success('文件已删除')
    }
  }

  const previewFile = (file: UploadFileInfo) => {
    const url = file.url || file.thumbnailUrl
    if (url) {
      window.open(url, '_blank')
    } else {
      message.error('文件链接不可用')
    }
  }

  const isLayoutField = (type: string) => {
    return [FieldType.DIVIDER, 'divider', FieldType.DESCRIPTION, 'description'].includes(type)
  }

  const isDateRangeField = (type: string) => {
    return type === FieldType.DATE_RANGE || type === 'date-range'
  }

  const isUploadField = (type: string) => {
    return type === FieldType.UPLOAD || type === 'upload' || type === 'image'
  }

  const isImageFile = (file: UploadFileInfo): boolean => {
    const contentType = file.type || file.file?.type
    if (contentType) {
      return contentType.startsWith('image/')
    }
    // 根据文件扩展名判断
    const name = file.name || ''
    const ext = name.split('.').pop()?.toLowerCase()
    return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(ext || '')
  }

  const isCalculatedField = (type: string) => {
    return type === FieldType.CALCULATED || type === 'calculated'
  }

  // 日期范围格式转换：时间戳数组 -> 字典格式
  const convertDateRangeForSubmit = (value: unknown, fieldType: string): unknown => {
    if (isDateRangeField(fieldType) && Array.isArray(value) && value.length === 2) {
      const [start, end] = value
      const startDate = new Date(start)
      const endDate = new Date(end)
      if (!isNaN(startDate.getTime()) && !isNaN(endDate.getTime())) {
        const formatDate = (d: Date) => {
          const year = d.getFullYear()
          const month = String(d.getMonth() + 1).padStart(2, '0')
          const day = String(d.getDate()).padStart(2, '0')
          return `${year}-${month}-${day}`
        }
        return { start: formatDate(startDate), end: formatDate(endDate) }
      }
    }
    return value
  }

  const initFormData = () => {
    if (!props.config?.formSchema?.fields || !Array.isArray(props.config.formSchema.fields)) {
      return
    }
    
    const attachmentMap = new Map<number, { name: string; url: string }>()
    if (props.config.attachments) {
      props.config.attachments.forEach(att => {
        attachmentMap.set(att.id, {
          name: att.file_name,
          url: att.download_url,
        })
      })
    }
    
    props.config.formSchema.fields.forEach(field => {
      let value = field.defaultValue
      // 日期范围字段格式转换：字典格式 -> 时间戳数组
      if (isDateRangeField(field.type) && value && typeof value === 'object' && !Array.isArray(value)) {
        if ('start' in value && 'end' in value) {
          const startTs = new Date(value.start as string).getTime()
          const endTs = new Date(value.end as string).getTime()
          if (!isNaN(startTs) && !isNaN(endTs)) {
            value = [startTs, endTs]
          }
        }
      }
      if (value !== undefined) {
        formData[field.id] = value
      } else {
        formData[field.id] = getDefaultValueForType(field.type)
      }
      fieldVisibility[field.id] = true
      fieldRequired[field.id] = field.required || false
      
      if (isUploadField(field.type)) {
        const existingIds = formData[field.id]
        if (Array.isArray(existingIds) && existingIds.length > 0) {
          uploadFileLists[field.id] = existingIds.map((id: number) => {
            const attInfo = attachmentMap.get(id)
            // 使用后端代理 URL，而不是 MinIO 的直接 URL
            // 对于图片，添加 inline=true 参数以便在浏览器中直接显示
            const isImage = attInfo?.name?.match(/\.(jpg|jpeg|png|gif|bmp|webp|svg)$/i)
            const proxyUrl = `/api/v1/attachments/${id}/download${isImage ? '?inline=true' : ''}`
            return {
              id: `existing-${id}`,
              name: attInfo?.name || `附件 ${id}`,
              status: 'finished' as const,
              url: proxyUrl,
              thumbnailUrl: proxyUrl,
              attachmentId: id,
            }
          })
        } else {
          uploadFileLists[field.id] = []
        }
      } else {
        uploadFileLists[field.id] = []
      }
    })
    
    applyLogicRules()
  }

  const getDefaultValueForType = (type: string) => {
    switch (type) {
      case FieldType.NUMBER:
      case 'number':
        return null
      case FieldType.CHECKBOX:
      case 'checkbox':
        return []
      case FieldType.DATE_RANGE:
      case 'date-range':
        return null
      case FieldType.UPLOAD:
      case 'upload':
      case 'image':
        return []
      default:
        return null
    }
  }

  const visibleFields = computed(() => {
    if (!props.config?.formSchema?.fields) return []
    return props.config.formSchema.fields.filter(field => fieldVisibility[field.id] !== false)
  })

  const getFieldComponent = (type: string) => {
    const componentMap: Record<string, string> = {
      [FieldType.TEXT]: 'n-input',
      'text': 'n-input',
      [FieldType.TEXTAREA]: 'n-input',
      'textarea': 'n-input',
      [FieldType.NUMBER]: 'n-input-number',
      'number': 'n-input-number',
      [FieldType.PHONE]: 'n-input',
      'phone': 'n-input',
      [FieldType.EMAIL]: 'n-input',
      'email': 'n-input',
      [FieldType.SELECT]: 'n-select',
      'select': 'n-select',
      [FieldType.RADIO]: 'n-radio-group',
      'radio': 'n-radio-group',
      [FieldType.CHECKBOX]: 'n-checkbox-group',
      'checkbox': 'n-checkbox-group',
      [FieldType.SWITCH]: 'n-switch',
      'switch': 'n-switch',
      [FieldType.DATE]: 'n-date-picker',
      'date': 'n-date-picker',
      [FieldType.DATE_RANGE]: 'n-date-picker',
      'date-range': 'n-date-picker',
      [FieldType.TIME]: 'n-time-picker',
      'time': 'n-time-picker',
      [FieldType.DATETIME]: 'n-date-picker',
      'datetime': 'n-date-picker',
      [FieldType.RATE]: 'n-rate',
      'rate': 'n-rate',
      [FieldType.UPLOAD]: 'n-upload',
      'upload': 'n-upload',
      [FieldType.CALCULATED]: 'n-input',
      'calculated': 'n-input',
    }
    return componentMap[type] || 'n-input'
  }

  const getFieldProps = (field: FormField) => {
    const baseProps: Record<string, unknown> = { ...field.props }

    if (field.type === FieldType.TEXTAREA || field.type === 'textarea') {
      baseProps.type = 'textarea'
    }

    if (isDateRangeField(field.type)) {
      baseProps.type = 'daterange'
      baseProps.clearable = true
    }

    if (field.type === FieldType.DATETIME || field.type === 'datetime') {
      baseProps.type = 'datetime'
    }

    if (field.type === FieldType.NUMBER || field.type === 'number') {
      baseProps.style = { width: '100%' }
    }

    if (isCalculatedField(field.type)) {
      baseProps.readonly = true
      baseProps.placeholder = '自动计算'
    }

    if (isUploadField(field.type)) {
      baseProps.action = '/api/v1/attachments/upload'
      baseProps.responseType = 'json'
      const maxCount = field.props.maxCount as number | undefined
      baseProps.multiple = maxCount ? maxCount > 1 : false
      baseProps.max = maxCount || 1
      baseProps.listType = 'text'
    }

    if (field.type === FieldType.RADIO || field.type === 'radio') {
      baseProps.name = field.id
    }

    return baseProps
  }

  const getFieldRule = (field: FormField): FormItemRule[] => {
    const rules: FormItemRule[] = []
    const isRequired = fieldRequired[field.id] ?? field.required

    if (isRequired) {
      rules.push({
        required: true,
        validator: (rule, value) => {
          if (isDateRangeField(field.type)) {
            if (!value || !Array.isArray(value) || value.length !== 2 || !value[0] || !value[1]) {
              return new Error(`请选择${field.label}`)
            }
          } else if (isUploadField(field.type)) {
            if (!value || (Array.isArray(value) && value.length === 0)) {
              return new Error(`请上传${field.label}`)
            }
          } else if (value === null || value === undefined || value === '') {
            return new Error(`请输入${field.label}`)
          }
          return true
        },
        trigger: ['blur', 'change'],
      })
    }

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

  const handleFieldChange = (fieldId: string) => {
    updateCalculatedFields()
    applyLogicRules()
  }

  const updateCalculatedFields = () => {
    if (!props.config?.formSchema?.fields || !Array.isArray(props.config.formSchema.fields)) {
      return
    }
    
    const calculatedFields = props.config.formSchema.fields.filter(
      f => isCalculatedField(f.type)
    )

    calculatedFields.forEach(field => {
      const formula = field.props.formula as string | undefined
      const dependencies = Array.isArray(field.props.dependencies)
        ? (field.props.dependencies as string[])
        : []

      const hasAllDeps = dependencies.every((dep: string) => {
        const val = formData[dep]
        if (val === null || val === undefined) return false
        if (Array.isArray(val) && val.length === 0) return false
        return true
      })

      if (hasAllDeps && formula) {
        try {
          const result = evaluateFormula(formula, formData)
          if (result !== null && result !== undefined && !Number.isNaN(result)) {
            formData[field.id] = result
          }
        } catch (error) {
          console.error('Formula evaluation error:', error)
        }
      }
    })
  }

  const evaluateFormula = (formula: string, context: FormValues) => {
    let expression = formula

    expression = expression.replace(/\$\{(\w+)\}\.(\w+)/g, (match, fieldId, prop) => {
      const value = context[fieldId]
      
      if (value === null || value === undefined) {
        return 'null'
      }
      
      if (Array.isArray(value)) {
        if (value.length >= 2) {
          let dateValue: number | null = null
          if (prop === 'start') {
            const startVal = value[0]
            if (typeof startVal === 'number') {
              dateValue = startVal
            } else if (startVal) {
              const dateStr = String(startVal)
              const parsed = new Date(dateStr + 'T00:00:00')
              dateValue = isNaN(parsed.getTime()) ? null : parsed.getTime()
            }
          } else if (prop === 'end') {
            const endVal = value[1]
            if (typeof endVal === 'number') {
              dateValue = endVal
            } else if (endVal) {
              const dateStr = String(endVal)
              const parsed = new Date(dateStr + 'T00:00:00')
              dateValue = isNaN(parsed.getTime()) ? null : parsed.getTime()
            }
          }
          return dateValue !== null ? `new Date(${dateValue})` : 'null'
        }
      }
      return 'null'
    })

    expression = expression.replace(/\$\{(\w+)\.(\w+)\}/g, (match, fieldId, prop) => {
      const value = context[fieldId]
      
      if (value === null || value === undefined) {
        return 'null'
      }
      
      if (Array.isArray(value)) {
        if (value.length >= 2) {
          let dateValue: number | null = null
          if (prop === 'start') {
            const startVal = value[0]
            if (typeof startVal === 'number') {
              dateValue = startVal
            } else if (startVal) {
              const dateStr = String(startVal)
              const parsed = new Date(dateStr + 'T00:00:00')
              dateValue = isNaN(parsed.getTime()) ? null : parsed.getTime()
            }
          } else if (prop === 'end') {
            const endVal = value[1]
            if (typeof endVal === 'number') {
              dateValue = endVal
            } else if (endVal) {
              const dateStr = String(endVal)
              const parsed = new Date(dateStr + 'T00:00:00')
              dateValue = isNaN(parsed.getTime()) ? null : parsed.getTime()
            }
          }
          return dateValue !== null ? `new Date(${dateValue})` : 'null'
        }
      }
      return 'null'
    })

    expression = expression.replace(/\$\{(\w+)\}/g, (match, fieldId) => {
      const value = context[fieldId]
      if (value === null || value === undefined) return 'null'
      if (typeof value === 'number') return String(value)
      if (typeof value === 'string') return `"${value}"`
      if (Array.isArray(value)) return JSON.stringify(value)
      return String(value)
    })

    const diffDays = (end: Date | null, start: Date | null): number => {
      if (!end || !start) {
        return 0
      }
      const diffTime = end.getTime() - start.getTime()
      const days = Math.round(diffTime / (1000 * 60 * 60 * 24))
      return days
    }

    const diffHours = (end: Date | null, start: Date | null): number => {
      if (!end || !start) return 0
      return (end.getTime() - start.getTime()) / (1000 * 60 * 60)
    }

    const today = () => new Date()
    const now = () => new Date()
    const abs = Math.abs
    const round = Math.round
    const min = Math.min
    const max = Math.max
    const sum = (...args: number[]) => args.reduce((a, b) => a + b, 0)
    const avg = (...args: number[]) => args.length > 0 ? sum(...args) / args.length : 0
    const floor = Math.floor
    const ceil = Math.ceil
    const concat = (...args: unknown[]) => args.join('')
    const length = (s: string) => s?.length || 0
    const upper = (s: string) => s?.toUpperCase() || ''
    const lower = (s: string) => s?.toLowerCase() || ''
    const trim = (s: string) => s?.trim() || ''

    try {
      const fn = new Function(
        'diffDays', 'diffHours', 'today', 'now', 
        'abs', 'round', 'min', 'max', 'sum', 'avg', 'floor', 'ceil',
        'concat', 'length', 'upper', 'lower', 'trim',
        `return ${expression}`
      )
      const result = fn(diffDays, diffHours, today, now, abs, round, min, max, sum, avg, floor, ceil, concat, length, upper, lower, trim)
      return result
    } catch (error) {
      console.error('Formula evaluation error:', error, 'Expression:', expression)
      return null
    }
  }

  const applyLogicRules = () => {
    const logicSchema = props.config?.logicSchema
    if (!logicSchema?.rules || !Array.isArray(logicSchema.rules)) {
      return
    }

    logicSchema.rules.forEach((rule: LogicRule) => {
      if (rule.enabled === false) return

      const conditionMet = evaluateCondition(rule)
      
      const actions = rule.actions || []
      actions.forEach((action: { type?: string; target?: string; value?: unknown }) => {
        const targetField = action.target
        if (!targetField) return

        const actionType = action.type as string
        switch (actionType) {
          case 'visible':
          case 'show':
            if (conditionMet) {
              fieldVisibility[targetField] = true
            } else {
              fieldVisibility[targetField] = false
            }
            break
          case 'hidden':
          case 'hide':
            if (conditionMet) {
              fieldVisibility[targetField] = false
            } else {
              fieldVisibility[targetField] = true
            }
            break
          case 'required':
            if (conditionMet) {
              fieldRequired[targetField] = true
            }
            break
          case 'optional':
            if (conditionMet) {
              fieldRequired[targetField] = false
            }
            break
          case 'set_value':
          case 'setValue':
            if (conditionMet && action.value !== undefined) {
              formData[targetField] = action.value
            }
            break
          case 'clear_value':
          case 'clearValue':
            if (conditionMet) {
              formData[targetField] = null
            }
            break
        }
      })
    })
  }

  const evaluateCondition = (rule: LogicRule): boolean => {
    const conditionStr = rule.condition
    if (!conditionStr) return false

    try {
      let expression = conditionStr
      
      expression = expression.replace(/\$\{(\w+)\}/g, (match, fieldId) => {
        const value = formData[fieldId]
        if (value === null || value === undefined) return 'null'
        if (typeof value === 'number') return String(value)
        if (typeof value === 'string') return `"${value}"`
        return String(value)
      })

      const fn = new Function(`return ${expression}`)
      return !!fn()
    } catch (error) {
      console.error('Condition evaluation error:', error)
      return false
    }
  }

  const handleSubmit = async () => {
    try {
      await formRef.value?.validate()
      
      const submitData: FormValues = {}
      const fields = props.config?.formSchema?.fields || []
      const fieldTypes: Record<string, string> = {}
      fields.forEach(f => { fieldTypes[f.id] = f.type })
      
      Object.keys(formData).forEach(key => {
        const value = formData[key]
        if (value !== null && value !== undefined) {
          const fieldType = fieldTypes[key] || ''
          submitData[key] = convertDateRangeForSubmit(value, fieldType)
        }
      })
      
      emit('submit', submitData)
    } catch (error) {
      message.error(resolveErrorMessage(error, '请检查表单填写'))
    }
  }

  const handleSaveAsDraft = async () => {
    try {
      // 暂存待发不需要校验必填字段
      const submitData: FormValues = {}
      const fields = props.config?.formSchema?.fields || []
      const fieldTypes: Record<string, string> = {}
      fields.forEach(f => { fieldTypes[f.id] = f.type })
      
      Object.keys(formData).forEach(key => {
        const value = formData[key]
        if (value !== null && value !== undefined) {
          const fieldType = fieldTypes[key] || ''
          submitData[key] = convertDateRangeForSubmit(value, fieldType)
        }
      })
      
      emit('saveAsDraft', submitData)
    } catch (error) {
      message.error(resolveErrorMessage(error, '暂存失败'))
    }
  }

  const handleReset = () => {
    try {
      formRef.value?.restoreValidation()
      
      Object.keys(formData).forEach(key => {
        formData[key] = null
      })
      
      Object.keys(fieldVisibility).forEach(key => {
        fieldVisibility[key] = true
      })
      
      Object.keys(fieldRequired).forEach(key => {
        const field = props.config?.formSchema?.fields?.find(f => f.id === key)
        fieldRequired[key] = field?.required || false
      })
      
      initFormData()
      message.success('表单已重置')
    } catch (error) {
      message.error(resolveErrorMessage(error, '重置失败'))
    }
  }
  
    // 监听 config 变化，重新初始化表单数据（用于编辑模式加载历史数据）
    watch(
      () => ({
        fields: props.config?.formSchema?.fields,
        attachments: props.config?.attachments
      }),
      (newVal, oldVal) => {
        if (newVal.fields) {
          const fieldsChanged = newVal.fields !== oldVal?.fields
          const attachmentsChanged = newVal.attachments !== oldVal?.attachments
          if (fieldsChanged || attachmentsChanged || !oldVal) {
            initFormData()
          }
        }
      },
      { deep: true, immediate: true }
    )
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

  .uploaded-file-item {
    display: flex;
    align-items: center;
  }

  .image-preview-container {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px;
    background: #f9fafb;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
  }

  .file-preview-container {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: #f9fafb;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
  }

  .delete-btn {
    flex-shrink: 0;
  }
  </style>
