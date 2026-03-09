<template>
  <div 
    class="design-canvas"
    @drop="handleDrop"
    @dragover.prevent="handleDragOver"
  >
    <!-- 空状态 -->
    <div v-if="fields.length === 0" class="empty-canvas">
      <div class="empty-icon">
        <Icon icon="carbon:application" />
      </div>
      <p class="empty-title">从左侧拖拽组件到这里</p>
      <p class="empty-desc">或点击组件快速添加</p>
    </div>
    
    <!-- 字段列表 -->
    <div v-else class="field-list">
      <div
        v-for="(element, index) in fields"
        :key="element.id"
        class="field-wrapper"
        :class="{ 'is-active': element.id === selectedFieldId }"
        draggable="true"
        @dragstart="handleFieldDragStart(index, $event)"
        @drop="handleFieldDrop(index, $event)"
        @dragover.prevent
        @click="handleSelectField(element.id)"
      >
        <div class="field-card">
          <!-- 拖拽手柄 -->
          <div class="drag-handle">
            <Icon icon="carbon:draggable" />
          </div>
          
          <!-- 字段图标 -->
          <div class="field-icon">
            <Icon :icon="getFieldTypeIcon(element.type)" />
          </div>
          
          <!-- 字段内容 -->
          <div class="field-content">
            <div class="field-header">
              <span class="field-label">
                {{ element.label }}
                <span v-if="element.required" class="required-star">*</span>
              </span>
              <n-tag size="small" :bordered="false">
                {{ getFieldTypeLabel(element.type) }}
              </n-tag>
            </div>
            
            <!-- 字段预览 -->
            <div class="field-preview">
              <FieldPreview :field="element" />
            </div>
            
            <div v-if="element.description" class="field-description">
              {{ element.description }}
            </div>
          </div>
          
          <!-- 操作按钮 -->
          <div class="field-actions">
            <n-button
              size="small"
              quaternary
              circle
              @click.stop="handleCopyField(element)"
            >
              <template #icon>
                <Icon icon="carbon:copy" />
              </template>
            </n-button>
            
            <n-button
              size="small"
              quaternary
              circle
              @click.stop="handleDeleteField(element.id)"
            >
              <template #icon>
                <Icon icon="carbon:trash-can" />
              </template>
            </n-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'
import { useMessage } from 'naive-ui'
import type { FormField } from '@/types/field'
import { FieldType, FIELD_TYPE_LABELS, FIELD_TYPE_ICONS } from '@/constants/fieldTypes'
import { FIELD_TEMPLATES } from '@/constants/fieldTemplates'
import { generateFieldId } from '@/utils/idGenerator'
import FieldPreview from './FieldPreview.vue'

interface Props {
  fields: FormField[]
  selectedFieldId?: string
}

const { fields, selectedFieldId } = defineProps<Props>()

const emit = defineEmits<{
  (e: 'select-field', fieldId: string): void
  (e: 'delete-field', fieldId: string): void
  (e: 'move-field', fromIndex: number, toIndex: number): void
  (e: 'add-field', field: FormField): void
}>()

const message = useMessage()
const draggedFieldIndex = ref<number | null>(null)

// 从组件库拖拽到画布
const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  const fieldType = event.dataTransfer?.getData('fieldType')
  
  if (fieldType) {
    const template = FIELD_TEMPLATES[fieldType as FieldType]
    if (template) {
      const newField: FormField = {
        ...template,
        id: generateFieldId(),
        type: template.type!,
        label: template.label!,
        required: template.required ?? false,
        props: { ...template.props },
      } as FormField
      
      emit('add-field', newField)
      message.success(`已添加「${newField.label}」`)
    }
  }
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'copy'
  }
}

// 字段内部拖拽开始
const handleFieldDragStart = (index: number, event: DragEvent) => {
  draggedFieldIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

// 字段内部拖拽放置
const handleFieldDrop = (targetIndex: number, event: DragEvent) => {
  event.stopPropagation()
  
  if (draggedFieldIndex.value !== null && draggedFieldIndex.value !== targetIndex) {
    emit('move-field', draggedFieldIndex.value, targetIndex)
  }
  
  draggedFieldIndex.value = null
}

// 选择字段
const handleSelectField = (fieldId: string) => {
  emit('select-field', fieldId)
}

// 删除字段
const handleDeleteField = (fieldId: string) => {
  emit('delete-field', fieldId)
}

// 复制字段
const handleCopyField = (field: FormField) => {
  const newField: FormField = {
    ...field,
    id: generateFieldId(),
    label: `${field.label} (副本)`,
    props: { ...field.props },
  }
  
  emit('add-field', newField)
  message.success('复制成功')
}

const getFieldTypeLabel = (type: FieldType): string => {
  return FIELD_TYPE_LABELS[type] || '未知类型'
}

const getFieldTypeIcon = (type: FieldType): string => {
  return FIELD_TYPE_ICONS[type] || 'carbon:unknown'
}
</script>

<style scoped lang="scss">
.design-canvas {
  min-height: 100%;
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.empty-canvas {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 480px;
  padding: 48px 24px;
  
  .empty-icon {
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f3f4f6;
    border-radius: 50%;
    font-size: 40px;
    color: #9ca3af;
    margin-bottom: 24px;
  }
  
  .empty-title {
    margin: 0 0 8px;
    font-size: 18px;
    font-weight: 500;
    color: #374151;
  }
  
  .empty-desc {
    margin: 0;
    font-size: 14px;
    color: #6b7280;
  }
}

.field-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-wrapper {
  border-radius: 8px;
  cursor: move;
  
  &.is-active {
    .field-card {
      border-color: #18a058;
      background: #f0fdf4;
      box-shadow: 0 0 0 3px rgba(24, 160, 88, 0.1);
    }
  }
}

.field-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #ffffff;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    border-color: #d1d5db;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    
    .field-actions {
      opacity: 1;
    }
  }
}

.drag-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  color: #9ca3af;
  cursor: move;
  border-radius: 4px;
  
  &:hover {
    color: #18a058;
    background: #f0fdf4;
  }
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
  flex-shrink: 0;
}

.field-content {
  flex: 1;
  min-width: 0;
}

.field-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  
  .field-label {
    font-size: 15px;
    font-weight: 500;
    color: #1f2937;
    
    .required-star {
      color: #ef4444;
      margin-left: 2px;
    }
  }
}

.field-preview {
  margin-bottom: 8px;
}

.field-description {
  font-size: 13px;
  color: #6b7280;
}

.field-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  flex-shrink: 0;
}
</style>