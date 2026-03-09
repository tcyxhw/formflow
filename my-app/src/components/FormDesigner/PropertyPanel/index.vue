<template>
    <div class="property-panel">
      <div class="panel-header">
        <div class="header-content">
          <h3 class="panel-title">字段属性</h3>
          <p class="panel-desc">配置选中字段的详细设置</p>
        </div>
        <n-button
          text
          size="large"
          @click="emit('close')"
        >
          <template #icon>
            <Icon icon="carbon:close" />
          </template>
        </n-button>
      </div>
      
      <div class="panel-body">
        <n-tabs
          type="line"
          animated
          :tab-style="{ padding: '12px 16px' }"
          :pane-style="{ padding: '24px 0 0' }"
        >
          <n-tab-pane name="basic" tab="基础">
            <template #tab>
              <div class="tab-label">
                <Icon icon="carbon:information" />
                <span>基础</span>
              </div>
            </template>
            <BasicConfig
              :field="field"
              @update="handleUpdate"
            />
          </n-tab-pane>
          
          <n-tab-pane name="props" tab="属性">
            <template #tab>
              <div class="tab-label">
                <Icon icon="carbon:settings-adjust" />
                <span>属性</span>
              </div>
            </template>
            <PropsConfig
              :field="field"
              :all-fields="allFields"
              @update="handleUpdate"
            />
          </n-tab-pane>
          
          <n-tab-pane name="validation" tab="验证">
            <template #tab>
              <div class="tab-label">
                <Icon icon="carbon:checkmark-outline" />
                <span>验证</span>
              </div>
            </template>
            <ValidationConfig
              :field="field"
              @update="handleUpdate"
            />
          </n-tab-pane>
        </n-tabs>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { Icon } from '@iconify/vue'
  import type { FormField } from '@/types/field'
  import BasicConfig from './BasicConfig.vue'
  import PropsConfig from './PropsConfig.vue'
  import ValidationConfig from './ValidationConfig.vue'
  
  interface Props {
    field: FormField
    allFields: FormField[]
  }
  
  defineProps<Props>()
  
  const emit = defineEmits<{
    (e: 'update', updates: Partial<FormField>): void
    (e: 'close'): void
  }>()
  
  const handleUpdate = (updates: Partial<FormField>) => {
    emit('update', updates)
  }
  </script>
  
  <style scoped lang="scss">
  .property-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .panel-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    padding: 24px 24px 16px;
    border-bottom: 1px solid var(--n-border-color);
    
    .header-content {
      flex: 1;
    }
    
    .panel-title {
      margin: 0 0 4px;
      font-size: 16px;
      font-weight: 600;
      color: var(--n-text-color-1);
      line-height: 1.3;
    }
    
    .panel-desc {
      margin: 0;
      font-size: 13px;
      color: var(--n-text-color-3);
      line-height: 1.5;
    }
  }
  
  .panel-body {
    flex: 1;
    overflow: hidden;
    padding: 0 24px 24px;
    
    :deep(.n-tabs) {
      height: 100%;
      display: flex;
      flex-direction: column;
    }
    
    :deep(.n-tabs-nav) {
      flex-shrink: 0;
    }
    
    :deep(.n-tabs-pane-wrapper) {
      flex: 1;
      overflow-y: auto;
      
      /* 滚动条优化 */
      &::-webkit-scrollbar {
        width: 6px;
      }
      
      &::-webkit-scrollbar-track {
        background: transparent;
      }
      
      &::-webkit-scrollbar-thumb {
        background: var(--n-scrollbar-color);
        border-radius: 3px;
        
        &:hover {
          background: var(--n-scrollbar-color-hover);
        }
      }
    }
  }
  
  .tab-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
  }
  
  /* 响应式 */
  @media (max-width: 768px) {
    .panel-header {
      padding: 16px 16px 12px;
    }
    
    .panel-body {
      padding: 0 16px 16px;
    }
  }
  </style>