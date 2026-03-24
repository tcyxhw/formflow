<template>
    <div class="component-library">
      <div class="library-header">
        <h3>组件库</h3>
        <p class="library-desc">拖拽或点击添加字段</p>
      </div>
      
      <div class="library-body">
        <div
          v-for="group in FIELD_GROUPS"
          :key="group.name"
          class="field-group"
        >
          <div class="group-title">
            <Icon :icon="group.icon" />
            <span>{{ group.name }}</span>
          </div>
          
          <div class="field-list">
            <div
              v-for="type in group.types"
              :key="type"
              class="field-item"
              draggable="true"
              @dragstart="handleDragStart(type, $event)"
              @click="handleAddField(type)"
            >
              <div class="field-icon">
                <Icon :icon="getFieldTypeIcon(type)" />
              </div>
              <span class="field-label">{{ getFieldTypeLabel(type) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { Icon } from '@iconify/vue'
  import { FIELD_GROUPS, FIELD_TYPE_LABELS, FIELD_TYPE_ICONS, FieldType } from '@/constants/fieldTypes'
  
  const emit = defineEmits<{
    (e: 'add-field', fieldType: string): void
  }>()
  
  const handleDragStart = (fieldType: FieldType, event: DragEvent) => {
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'copy'
      event.dataTransfer.setData('fieldType', fieldType)
    }
  }
  
  const handleAddField = (fieldType: FieldType) => {
    emit('add-field', fieldType)
  }
  
  const getFieldTypeLabel = (type: FieldType): string => {
    return FIELD_TYPE_LABELS[type] || '未知类型'
  }
  
  const getFieldTypeIcon = (type: FieldType): string => {
    return FIELD_TYPE_ICONS[type] || 'carbon:unknown'
  }
  </script>
  
  <style scoped lang="scss">
  .component-library {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #ffffff;
  }
  
  .library-header {
    padding: 20px;
    border-bottom: 1px solid #e5e7eb;
    background: #ffffff;
    
    h3 {
      margin: 0 0 4px;
      font-size: 16px;
      font-weight: 600;
      color: #1f2937;
    }
    
    .library-desc {
      margin: 0;
      font-size: 13px;
      color: #6b7280;
    }
  }
  
  .library-body {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    background: #f9fafb;
  }
  
  .field-group {
    margin-bottom: 24px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .group-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    padding: 0 4px;
    font-size: 14px;
    font-weight: 500;
    color: #374151;
    
    svg {
      font-size: 16px;
      color: #18a058;
    }
  }
  
  .field-list {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  
  .field-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 16px 8px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    user-select: none;
    
    &:hover {
      background: #f0fdf4;
      border-color: #18a058;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(24, 160, 88, 0.15);
    }
    
    &:active {
      transform: translateY(0);
    }
    
    .field-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 40px;
      height: 40px;
      background: #f0fdf4;
      border-radius: 8px;
      color: #18a058;
      font-size: 20px;
    }
    
    .field-label {
      font-size: 13px;
      font-weight: 500;
      color: #374151;
      text-align: center;
    }
  }
  
  /* 滚动条 */
  .library-body::-webkit-scrollbar {
    width: 6px;
  }
  
  .library-body::-webkit-scrollbar-track {
    background: #f1f1f1;
  }
  
  .library-body::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
    
    &:hover {
      background: #a8a8a8;
    }
  }
  </style>