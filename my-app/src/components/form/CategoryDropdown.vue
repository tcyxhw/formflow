<template>
  <div class="category-dropdown">
    <n-select
      v-model:value="selectedCategory"
      :options="categoryOptions"
      :loading="categoryStore.loading"
      :disabled="disabled"
      placeholder="选择分类"
      clearable
      @update:value="handleCategoryChange"
    />
    <n-empty
      v-if="categoryOptions.length === 0 && !categoryStore.loading"
      description="暂无分类"
      style="margin-top: 12px"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { NSelect, NEmpty } from 'naive-ui'
import { useCategoryStore } from '@/stores/useCategory'

interface Props {
  modelValue?: number | null
  disabled?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: number | null): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  disabled: false
})

const emit = defineEmits<Emits>()

const categoryStore = useCategoryStore()
const selectedCategory = ref<number | null>(props.modelValue)

const categoryOptions = computed(() => {
  return categoryStore.categories.map(cat => ({
    label: cat.name,
    value: cat.id
  }))
})

const handleCategoryChange = (value: number | null) => {
  selectedCategory.value = value
  emit('update:modelValue', value)
}

onMounted(async () => {
  if (categoryStore.categories.length === 0) {
    await categoryStore.fetchCategories()
  }
})

watch(() => props.modelValue, (newValue) => {
  selectedCategory.value = newValue
})
</script>

<style scoped>
.category-dropdown {
  width: 100%;
}
</style>
