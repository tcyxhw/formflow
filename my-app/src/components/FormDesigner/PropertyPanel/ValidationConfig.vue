<template>
    <div class="validation-config">
      <n-scrollbar style="max-height: calc(100vh - 300px)">
        <div class="config-content">
          <n-form :model="localValidation" label-placement="top" size="medium">
            
            <!-- 正则表达式 -->
            <n-form-item>
              <template #label>
                <div class="form-label-with-icon">
                  <Icon icon="carbon:regex" />
                  <span>正则表达式</span>
                </div>
              </template>
              <n-input
                v-model:value="localValidation.pattern"
                placeholder="如: ^[0-9]+$"
                clearable
                @blur="handleUpdate"
              >
                <template #prefix>
                  <span class="regex-prefix">/</span>
                </template>
                <template #suffix>
                  <span class="regex-suffix">/</span>
                </template>
              </n-input>
              <template #feedback>
                <span class="field-hint">用于验证输入格式的正则表达式</span>
              </template>
            </n-form-item>
            
            <!-- 最小值/长度 -->
            <n-form-item v-if="supportsMinMax">
              <template #label>
                <div class="form-label-with-icon">
                  <Icon icon="carbon:text-align-left" />
                  <span>{{ isNumberField ? '最小值' : '最小长度' }}</span>
                </div>
              </template>
              <n-input-number
                v-model:value="localValidation.min"
                placeholder="不限制"
                style="width: 100%"
                @blur="handleUpdate"
              >
                <template #suffix>{{ isNumberField ? '' : '字符' }}</template>
              </n-input-number>
            </n-form-item>
            
            <!-- 最大值/长度 -->
            <n-form-item v-if="supportsMinMax">
              <template #label>
                <div class="form-label-with-icon">
                  <Icon icon="carbon:text-align-right" />
                  <span>{{ isNumberField ? '最大值' : '最大长度' }}</span>
                </div>
              </template>
              <n-input-number
                v-model:value="localValidation.max"
                placeholder="不限制"
                style="width: 100%"
                @blur="handleUpdate"
              >
                <template #suffix>{{ isNumberField ? '' : '字符' }}</template>
              </n-input-number>
            </n-form-item>
            
            <!-- 错误提示 -->
            <n-form-item>
              <template #label>
                <div class="form-label-with-icon">
                  <Icon icon="carbon:warning-alt" />
                  <span>错误提示</span>
                </div>
              </template>
              <n-input
                v-model:value="localValidation.message"
                placeholder="验证失败时显示的提示文本"
                clearable
                @blur="handleUpdate"
              />
              <template #feedback>
                <span class="field-hint">留空则使用默认提示</span>
              </template>
            </n-form-item>
            
            <!-- 触发时机 -->
            <n-form-item>
              <template #label>
                <div class="form-label-with-icon">
                  <Icon icon="carbon:time" />
                  <span>触发时机</span>
                </div>
              </template>
              <n-radio-group
                v-model:value="localValidation.trigger"
                @update:value="handleUpdate"
              >
                <n-space vertical :size="12">
                  <n-radio value="blur">
                    <div class="radio-option">
                      <div class="radio-label">失去焦点时</div>
                      <div class="radio-desc">用户离开输入框时验证</div>
                    </div>
                  </n-radio>
                  <n-radio value="change">
                    <div class="radio-option">
                      <div class="radio-label">值改变时</div>
                      <div class="radio-desc">用户输入时实时验证</div>
                    </div>
                  </n-radio>
                </n-space>
              </n-radio-group>
            </n-form-item>
            
            <!-- 快速设置 -->
            <n-divider title-placement="left">
              <span style="font-size: 13px; color: var(--n-text-color-3)">快速设置</span>
            </n-divider>
            
            <div class="preset-buttons">
              <n-button
                size="small"
                secondary
                @click="applyPreset('phone')"
              >
                <template #icon>
                  <Icon icon="carbon:phone" />
                </template>
                手机号验证
              </n-button>
              
              <n-button
                size="small"
                secondary
                @click="applyPreset('email')"
              >
                <template #icon>
                  <Icon icon="carbon:email" />
                </template>
                邮箱验证
              </n-button>
              
              <n-button
                size="small"
                secondary
                @click="applyPreset('idCard')"
              >
                <template #icon>
                  <Icon icon="carbon:id-management" />
                </template>
                身份证验证
              </n-button>
              
              <n-button
                size="small"
                secondary
                @click="applyPreset('url')"
              >
                <template #icon>
                  <Icon icon="carbon:link" />
                </template>
                网址验证
              </n-button>
            </div>
          </n-form>
        </div>
      </n-scrollbar>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, watch } from 'vue'
  import { Icon } from '@iconify/vue'
  import type { FormField, FieldValidation } from '@/types/field'
  import { FieldType } from '@/types/field'
  
  interface Props {
    field: FormField
  }
  
  const props = defineProps<Props>()
  
  const emit = defineEmits<{
    (e: 'update', updates: Partial<FormField>): void
  }>()
  
  const localValidation = ref<FieldValidation>({
    pattern: props.field.validation?.pattern || '',
    min: props.field.validation?.min,
    max: props.field.validation?.max,
    message: props.field.validation?.message || '',
    trigger: props.field.validation?.trigger || 'blur',
  })
  
  watch(
    () => props.field.validation,
    (newValidation) => {
      if (newValidation) {
        localValidation.value = { ...newValidation }
      }
    },
    { deep: true }
  )
  
  const supportsMinMax = computed(() => {
    return [
      FieldType.TEXT,
      FieldType.TEXTAREA,
      FieldType.NUMBER,
    ].includes(props.field.type as FieldType)
  })
  
  const isNumberField = computed(() => {
    return props.field.type === FieldType.NUMBER
  })
  
  const handleUpdate = () => {
    const validation: FieldValidation = {}
    
    if (localValidation.value.pattern) {
      validation.pattern = localValidation.value.pattern
    }
    
    if (localValidation.value.min !== undefined) {
      validation.min = localValidation.value.min
    }
    
    if (localValidation.value.max !== undefined) {
      validation.max = localValidation.value.max
    }
    
    if (localValidation.value.message) {
      validation.message = localValidation.value.message
    }
    
    validation.trigger = localValidation.value.trigger || 'blur'
    
    emit('update', { validation })
  }
  
  const applyPreset = (type: string) => {
    const presets: Record<string, FieldValidation> = {
      phone: {
        pattern: '^1[3-9]\\d{9}$',
        message: '请输入正确的手机号',
        trigger: 'blur',
      },
      email: {
        pattern: '^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
        message: '请输入正确的邮箱',
        trigger: 'blur',
      },
      idCard: {
        pattern: '^[1-9]\\d{5}(18|19|20)\\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\\d|3[01])\\d{3}[\\dXx]$',
        message: '请输入正确的身份证号',
        trigger: 'blur',
      },
      url: {
        pattern: '^https?:\\/\\/(www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b([-a-zA-Z0-9()@:%_\\+.~#?&//=]*)$',
        message: '请输入正确的网址',
        trigger: 'blur',
      },
    }
    
    const preset = presets[type]
    if (preset) {
      localValidation.value = { ...preset }
      handleUpdate()
    }
  }
  </script>
  
  <style scoped lang="scss">
  .validation-config {
    height: 100%;
  }
  
  .config-content {
    padding: 0 4px;
    
    :deep(.n-form-item) {
      margin-bottom: 24px;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
  }
  
  .form-label-with-icon {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 500;
    color: var(--n-text-color-1);
    
    svg {
      font-size: 16px;
      color: var(--n-color-target);
    }
  }
  
  .field-hint {
    font-size: 12px;
    color: var(--n-text-color-3);
    line-height: 1.5;
  }
  
  .regex-prefix,
  .regex-suffix {
    font-family: monospace;
    font-size: 14px;
    color: var(--n-text-color-3);
  }
  
  .radio-option {
    display: flex;
    flex-direction: column;
    gap: 4px;
    
    .radio-label {
      font-size: 14px;
      font-weight: 500;
      color: var(--n-text-color-1);
    }
    
    .radio-desc {
      font-size: 12px;
      color: var(--n-text-color-3);
      line-height: 1.5;
    }
  }
  
  .preset-buttons {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-top: 16px;
  }
  
  /* 响应式 */
  @media (max-width: 768px) {
    .config-content {
      padding: 0;
    }
    
    .preset-buttons {
      grid-template-columns: 1fr;
    }
  }
  </style>