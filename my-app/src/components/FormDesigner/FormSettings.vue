<template>
    <div class="form-settings">
      <div class="settings-header">
        <h3>表单设置</h3>
        <p class="settings-desc">配置表单的基础信息</p>
      </div>
      
      <div class="settings-body">
        <n-form :model="localConfig" label-placement="top" size="medium">
          
          <!-- 基础设置 -->
          <div class="settings-section">
            <h4 class="section-title">基础设置</h4>
            
            <n-form-item label="表单分类">
              <n-input
                v-model:value="localConfig.category"
                placeholder="如：请假申请、活动报名"
                clearable
                @blur="handleUpdate"
              />
            </n-form-item>
            
            <n-form-item label="访问模式">
              <n-radio-group
                v-model:value="localConfig.accessMode"
                @update:value="handleUpdate"
              >
                <n-space vertical>
                  <n-radio :value="AccessMode.AUTHENTICATED">需要登录</n-radio>
                  <n-radio :value="AccessMode.PUBLIC">公开访问</n-radio>
                </n-space>
              </n-radio-group>
            </n-form-item>
            
            <n-form-item label="提交截止时间">
              <n-date-picker
                v-model:value="deadlineTimestamp"
                type="datetime"
                clearable
                placeholder="选择截止时间"
                style="width: 100%"
                @update:value="handleDeadlineUpdate"
              />
            </n-form-item>
          </div>
          
          <!-- 提交设置 -->
          <div class="settings-section">
            <h4 class="section-title">提交设置</h4>
            
            <n-form-item label="允许修改">
              <n-switch
                v-model:value="localConfig.allowEdit"
                @update:value="handleUpdate"
              />
            </n-form-item>
            
            <n-form-item v-if="localConfig.allowEdit" label="最大修改次数">
              <n-input-number
                v-model:value="localConfig.maxEditCount"
                :min="0"
                placeholder="0 表示不限制"
                style="width: 100%"
                @blur="handleUpdate"
              />
            </n-form-item>
          </div>
          
          <!-- 布局设置 -->
          <div class="settings-section">
            <h4 class="section-title">布局设置</h4>
            
            <n-form-item label="布局方式">
              <n-radio-group
                v-model:value="localConfig.uiSchema.layout.type"
                @update:value="handleUpdate"
              >
                <n-space vertical>
                  <n-radio value="vertical">垂直布局</n-radio>
                  <n-radio value="horizontal">水平布局</n-radio>
                  <n-radio value="grid">栅格布局</n-radio>
                </n-space>
              </n-radio-group>
            </n-form-item>
            
            <n-form-item label="标签宽度">
              <n-input-number
                v-model:value="labelWidthValue"
                :min="60"
                :max="240"
                style="width: 100%"
                @blur="handleUpdate"
              />
            </n-form-item>
            
            <n-form-item label="标签位置">
              <n-radio-group
                v-model:value="localConfig.uiSchema.layout.labelPosition"
                @update:value="handleUpdate"
              >
                <n-space>
                  <n-radio value="left">左侧</n-radio>
                  <n-radio value="right">右侧</n-radio>
                  <n-radio value="top">顶部</n-radio>
                </n-space>
              </n-radio-group>
            </n-form-item>
            
            <n-form-item label="组件尺寸">
              <n-radio-group
                v-model:value="localConfig.uiSchema.layout.size"
                @update:value="handleUpdate"
              >
                <n-space>
                  <n-radio value="small">小</n-radio>
                  <n-radio value="medium">中</n-radio>
                  <n-radio value="large">大</n-radio>
                </n-space>
              </n-radio-group>
            </n-form-item>
          </div>
          
        </n-form>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { AccessMode } from '@/types/form'
import type { UISchema } from '@/types/schema'

interface FormSettingsConfig {
  category?: string
  accessMode: AccessMode
  submitDeadline?: string
  allowEdit: boolean
  maxEditCount: number
  uiSchema: UISchema
}

const props = defineProps<{
  config: FormSettingsConfig
}>()

const emit = defineEmits<{
  (e: 'update', updates: Partial<FormSettingsConfig>): void
}>()

const localConfig = ref<FormSettingsConfig>({ ...props.config })
  
  watch(
    () => props.config,
    (newConfig) => {
      localConfig.value = { ...newConfig }
    },
    { deep: true }
  )
  
  const deadlineTimestamp = computed({
  get(): number | null {
    return localConfig.value.submitDeadline
      ? new Date(localConfig.value.submitDeadline).getTime()
      : null
  },
  set(value: number | null) {
    localConfig.value.submitDeadline = value
      ? new Date(value).toISOString()
      : undefined
  },
})

const labelWidthValue = computed({
  get(): number {
    const raw = localConfig.value.uiSchema.layout.labelWidth
    if (typeof raw === 'number') {
      return raw
    }
    if (typeof raw === 'string') {
      const parsed = Number(raw)
      return Number.isNaN(parsed) ? 120 : parsed
    }
    return 120
  },
  set(value: number | null) {
    localConfig.value.uiSchema.layout.labelWidth = value ?? 120
  },
})

const handleDeadlineUpdate = () => {
  handleUpdate()
}

/**
 * 同步设置变更
 */
const handleUpdate = () => {
  emit('update', {
    category: localConfig.value.category,
    accessMode: localConfig.value.accessMode,
    submitDeadline: localConfig.value.submitDeadline,
    allowEdit: localConfig.value.allowEdit,
    maxEditCount: localConfig.value.maxEditCount,
    uiSchema: localConfig.value.uiSchema,
  })
}
  </script>
  
  <style scoped lang="scss">
  .form-settings {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #ffffff;
  }
  
  .settings-header {
    padding: 20px;
    border-bottom: 1px solid #e5e7eb;
    
    h3 {
      margin: 0 0 4px;
      font-size: 16px;
      font-weight: 600;
      color: #1f2937;
    }
    
    .settings-desc {
      margin: 0;
      font-size: 13px;
      color: #6b7280;
    }
  }
  
  .settings-body {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }
  
  .settings-section {
    margin-bottom: 32px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .section-title {
    margin: 0 0 16px;
    font-size: 14px;
    font-weight: 500;
    color: #374151;
  }
  
  /* 滚动条 */
  .settings-body::-webkit-scrollbar {
    width: 6px;
  }
  
  .settings-body::-webkit-scrollbar-track {
    background: #f1f1f1;
  }
  
  .settings-body::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
  }
  </style>