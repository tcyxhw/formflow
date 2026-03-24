<script setup lang="ts">
import { ref, watch } from 'vue'
import { NInput } from 'naive-ui'
import { useDebounceFn } from '@vueuse/core'

interface Props {
  modelValue: string
  placeholder?: string
  debounce?: number
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '搜索表单...',
  debounce: 300
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  search: [keyword: string]
}>()

const inputValue = ref(props.modelValue)

// 防抖搜索
const debouncedSearch = useDebounceFn((value: string) => {
  emit('search', value)
}, props.debounce)

// 监听输入变化
watch(inputValue, (newValue) => {
  emit('update:modelValue', newValue)
  debouncedSearch(newValue)
})

// 监听外部值变化
watch(() => props.modelValue, (newValue) => {
  if (newValue !== inputValue.value) {
    inputValue.value = newValue
  }
})

// 清除搜索
const handleClear = () => {
  inputValue.value = ''
}

// ESC键清除
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    handleClear()
  }
}
</script>

<template>
  <NInput
    v-model:value="inputValue"
    :placeholder="placeholder"
    clearable
    @clear="handleClear"
    @keydown="handleKeydown"
  >
    <template #prefix>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        style="width: 16px; height: 16px"
      >
        <circle cx="11" cy="11" r="8"></circle>
        <path d="m21 21-4.35-4.35"></path>
      </svg>
    </template>
  </NInput>
</template>

<style scoped>
/* 样式由 Naive UI 提供 */
</style>
