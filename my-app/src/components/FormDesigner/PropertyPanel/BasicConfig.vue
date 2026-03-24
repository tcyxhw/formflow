<template>
    <div class="basic-config">
      <n-scrollbar style="max-height: calc(100vh - 300px)">
        <div class="config-content">
          <n-form :model="localField" label-placement="top" size="medium">
            <!-- 字段ID -->
            <n-form-item>
              <template #label>
                <div class="form-label-with-icon">
                  <Icon icon="carbon:fingerprint" />
                  <span>字段ID</span>
                </div>
              </template>
              <n-input :value="field.id" readonly>
                <template #suffix>
                  <n-button
                    text
                    size="tiny"
                    @click="copyToClipboard(field.id)"
                  >
                    <Icon icon="carbon:copy" />
                  </n-button>
                </template>
              </n-input>
              <template #feedback>
                <span class="field-hint">字段的唯一标识符，系统自动生成</span>
              </template>
            </n-form-item>
            
            <!-- 字段类型 -->
            <n-form-item>
              <template #label>
                <div class="form-label-with-icon">
                  <Icon icon="carbon:category" />
                  <span>字段类型</span>
                </div>
              </template>
              <n-tag type="info" size="medium" :bordered="false">
                <template #icon>
                  <Icon :icon="FIELD_TYPE_ICONS[field.type]" />
                </template>
                {{ FIELD_TYPE_LABELS[field.type] }}
              </n-tag>
            </n-form-item>
            
            <!-- 字段标签 -->
            <n-form-item required>
              <template #label>
                <div class="form-label-with-icon">
                  <Icon icon="carbon:text-annotation-toggle" />
                  <span>字段标签</span>
                </div>
              </template>
              <n-input
                v-model:value="localField.label"
                placeholder="请输入字段标签"
                :maxlength="100"
                show-count
                @blur="handleUpdate"
              />
              <template #feedback>
                <span class="field-hint">在表单中显示的字段名称</span>
              </template>
            </n-form-item>
            
            <!-- 帮助文本 -->
            <n-form-item>
              <template #label>
                <div class="form-label-with-icon">
                  <Icon icon="carbon:information" />
                  <span>帮助文本</span>
                </div>
              </template>
              <n-input
                v-model:value="localField.description"
                type="textarea"
                placeholder="请输入帮助文本，将显示在字段下方"
                :rows="3"
                :maxlength="200"
                show-count
                @blur="handleUpdate"
              />
            </n-form-item>
            
            <!-- 是否必填 -->
            <n-form-item>
              <template #label>
                <div class="form-label-with-icon">
                  <Icon icon="carbon:asterisk" />
                  <span>是否必填</span>
                </div>
              </template>
              <n-switch
                v-model:value="localField.required"
                @update:value="handleUpdate"
              >
                <template #checked>
                  <span class="switch-text">必填</span>
                </template>
                <template #unchecked>
                  <span class="switch-text">可选</span>
                </template>
              </n-switch>
              <template #feedback>
                <span class="field-hint">
                  开启后，用户必须填写此字段才能提交
                </span>
              </template>
            </n-form-item>
            
            <!-- 默认值 -->
            <n-form-item
              v-if="!isLayoutField(field.type)"
            >
              <template #label>
                <div class="form-label-with-icon">
                  <Icon icon="carbon:settings-adjust" />
                  <span>默认值</span>
                </div>
              </template>
              <DefaultValueInput
                :model-value="localField.defaultValue"
                :field="field"
                @update:value="handleUpdate"
              />
              <template #feedback>
                <span class="field-hint">表单加载时的初始值</span>
              </template>
            </n-form-item>
          </n-form>
        </div>
      </n-scrollbar>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, watch } from 'vue'
  import { useMessage } from 'naive-ui'
  import { Icon } from '@iconify/vue'
  import type { FormField } from '@/types/field'
  import { FieldType, FIELD_TYPE_LABELS, FIELD_TYPE_ICONS } from '@/constants/fieldTypes'
  import DefaultValueInput from './DefaultValueInput.vue'
  
  interface Props {
    field: FormField
  }
  
  const props = defineProps<Props>()
  
  const emit = defineEmits<{
    (e: 'update', updates: Partial<FormField>): void
  }>()
  
  const message = useMessage()
  const localField = ref<FormField>({ ...props.field })
  
  watch(
    () => props.field,
    (newField) => {
      localField.value = { ...newField }
    },
    { deep: true }
  )
  
  const isLayoutField = (type: FieldType) => {
    return [FieldType.DIVIDER, FieldType.DESCRIPTION].includes(type)
  }
  
  const handleUpdate = () => {
    emit('update', {
      label: localField.value.label,
      description: localField.value.description,
      required: localField.value.required,
      defaultValue: localField.value.defaultValue,
    })
  }
  
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      message.success('已复制到剪贴板')
    })
  }
  </script>
  
  <style scoped lang="scss">
  .basic-config {
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
  
  .switch-text {
    font-size: 12px;
  }
  
  /* 响应式 */
  @media (max-width: 768px) {
    .config-content {
      padding: 0;
    }
  }
  </style>