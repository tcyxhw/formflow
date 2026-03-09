<template>
    <div class="options-editor">
      <div class="options-list">
        <div
          v-for="(option, index) in localOptions"
          :key="index"
          class="option-item"
        >
          <div class="option-drag-handle">
            <Icon icon="carbon:draggable" />
          </div>
          
          <n-input
            v-model:value="option.label"
            placeholder="选项文本"
            size="small"
            @blur="handleUpdate"
          />
          
          <n-input
            :value="String(option.value)"
            @update:value="(val) => updateOptionValue(index, val)"
            placeholder="值"
            size="small"
            style="width: 100px"
          />
          
          <n-button
            size="small"
            quaternary
            circle
            :disabled="localOptions.length === 1"
            @click="handleRemove(index)"
          >
            <template #icon>
              <Icon icon="carbon:close" />
            </template>
          </n-button>
        </div>
      </div>
      
      <n-button
        size="small"
        dashed
        block
        class="add-option-btn"
        @click="handleAdd"
      >
        <template #icon>
          <Icon icon="carbon:add" />
        </template>
        添加选项
      </n-button>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, watch } from 'vue'
  import { Icon } from '@iconify/vue'
  import type { SelectOption } from '@/types/field'
  
  interface Props {
    options: SelectOption[]
  }
  
  const props = defineProps<Props>()
  
  const emit = defineEmits<{
    (e: 'update:options', options: SelectOption[]): void
  }>()
  
  const localOptions = ref<SelectOption[]>([...props.options])
  
  watch(
    () => props.options,
    (newOptions) => {
      localOptions.value = [...newOptions]
    },
    { deep: true }
  )
  
  const handleAdd = () => {
    const newValue = localOptions.value.length + 1
    localOptions.value.push({
      label: `选项${newValue}`,
      value: String(newValue),
    })
    handleUpdate()
  }
  
  const handleRemove = (index: number) => {
    if (localOptions.value.length <= 1) {
      return
    }
    localOptions.value.splice(index, 1)
    handleUpdate()
  }
  
  const updateOptionValue = (index: number, value: string) => {
    localOptions.value[index].value = value
    handleUpdate()
  }
  
  const handleUpdate = () => {
    emit('update:options', [...localOptions.value])
  }
  </script>
  
  <style scoped lang="scss">
  .options-editor {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .options-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .option-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px;
    background: var(--n-color-target);
    border: 1px solid var(--n-border-color);
    border-radius: 6px;
    transition: all 220ms cubic-bezier(0.2, 0.8, 0.2, 1);
    
    &:hover {
      border-color: var(--n-border-color-hover);
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
    }
  }
  
  .option-drag-handle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    color: var(--n-text-color-3);
    cursor: move;
    flex-shrink: 0;
    
    &:hover {
      color: var(--n-color-target);
    }
  }
  
  .add-option-btn {
    margin-top: 4px;
  }
  
  /* 运动减弱支持 */
  @media (prefers-reduced-motion: reduce) {
    .option-item {
      transition: none;
    }
  }
  </style>