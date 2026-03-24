<!-- src\components\FormDesigner\FieldPreview.vue -->
<template>
    <div class="field-preview-wrapper">
      <!-- 文本输入 -->
      <n-input
        v-if="field.type === FieldType.TEXT || field.type === FieldType.PHONE || field.type === FieldType.EMAIL"
        :placeholder="field.props.placeholder"
        :disabled="field.props.disabled"
        size="small"
        readonly
      />
      
      <!-- 多行文本 -->
      <n-input
        v-else-if="field.type === FieldType.TEXTAREA"
        type="textarea"
        :placeholder="field.props.placeholder"
        :rows="field.props.rows || 4"
        :disabled="field.props.disabled"
        size="small"
        readonly
      />
      
      <!-- 数字 -->
      <n-input-number
        v-else-if="field.type === FieldType.NUMBER"
        :placeholder="field.props.placeholder"
        :disabled="field.props.disabled"
        size="small"
        style="width: 100%"
      />
      
      <!-- 下拉选择 -->
      <n-select
        v-else-if="field.type === FieldType.SELECT"
        :placeholder="field.props.placeholder"
        :options="field.props.options || []"
        :disabled="field.props.disabled"
        size="small"
      />
      
      <!-- 单选框 -->
      <n-radio-group
        v-else-if="field.type === FieldType.RADIO"
        :disabled="field.props.disabled"
        size="small"
      >
        <n-space>
          <n-radio
            v-for="option in field.props.options || []"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </n-radio>
        </n-space>
      </n-radio-group>
      
      <!-- 复选框 -->
      <n-checkbox-group
        v-else-if="field.type === FieldType.CHECKBOX"
        :disabled="field.props.disabled"
        size="small"
      >
        <n-space>
          <n-checkbox
            v-for="option in field.props.options || []"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </n-checkbox>
        </n-space>
      </n-checkbox-group>
      
      <!-- 开关 -->
      <n-switch
        v-else-if="field.type === FieldType.SWITCH"
        :disabled="field.props.disabled"
        size="small"
      />
      
      <!-- 日期 -->
      <n-date-picker
        v-else-if="field.type === FieldType.DATE || field.type === FieldType.DATETIME"
        :placeholder="field.props.placeholder"
        :type="field.props.type || 'date'"
        :disabled="field.props.disabled"
        size="small"
        style="width: 100%"
      />
      
      <!-- 日期范围 -->
      <n-date-picker
        v-else-if="field.type === FieldType.DATE_RANGE"
        type="daterange"
        :disabled="field.props.disabled"
        size="small"
        style="width: 100%"
      />
      
      <!-- 时间 -->
      <n-time-picker
        v-else-if="field.type === FieldType.TIME"
        :placeholder="field.props.placeholder"
        :disabled="field.props.disabled"
        size="small"
        style="width: 100%"
      />
      
      <!-- 评分 -->
      <n-rate
        v-else-if="field.type === FieldType.RATE"
        :count="field.props.count || 5"
        :allow-half="field.props.allowHalf"
        :disabled="field.props.disabled"
        size="small"
      />
      
      <!-- 上传 -->
      <n-upload
        v-else-if="field.type === FieldType.UPLOAD"
        :disabled="field.props.disabled"
        :max="field.props.maxCount"
      >
        <n-button size="small">
          <Icon icon="carbon:upload" class="mr-1" />
          点击上传
        </n-button>
      </n-upload>
      
      <!-- 计算字段 -->
      <n-input
        v-else-if="field.type === FieldType.CALCULATED"
        placeholder="自动计算"
        readonly
        size="small"
      >
        <template #prefix>
          <Icon icon="carbon:calculator" />
        </template>
      </n-input>
      
      <!-- 分割线 -->
      <n-divider v-else-if="field.type === FieldType.DIVIDER" />
      
      <!-- 描述文本 -->
      <div v-else-if="field.type === FieldType.DESCRIPTION" class="description-preview">
        {{ field.props.content || '描述文本' }}
      </div>
      
      <!-- 其他 -->
      <div v-else class="unknown-field">
        未知字段类型: {{ field.type }}
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { Icon } from '@iconify/vue'
  import type { FormField } from '@/types/field'
  import { FieldType } from '@/types/field'
  
  interface Props {
    field: FormField
  }
  
  defineProps<Props>()
  </script>
  
  <style scoped lang="scss">
  .field-preview-wrapper {
    pointer-events: none;
    
    :deep(.n-input),
    :deep(.n-select),
    :deep(.n-date-picker) {
      cursor: default;
    }
  }
  
  .description-preview {
    padding: 8px 12px;
    background: #f9fafb;
    border-radius: 4px;
    font-size: 13px;
    color: #6b7280;
  }
  
  .unknown-field {
    padding: 8px 12px;
    background: #fef2f2;
    border-radius: 4px;
    font-size: 13px;
    color: #ef4444;
  }
  
  .mr-1 {
    margin-right: 4px;
  }
  </style>