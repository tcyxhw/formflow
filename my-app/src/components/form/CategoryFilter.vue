<template>
  <div class="category-filter">
    <n-select
      v-model:value="selectedCategory"
      :options="categoryOptions"
      :loading="categoryStore.loading"
      placeholder="按分类筛选"
      clearable
      @update:value="handleFilterChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { NSelect } from 'naive-ui'
import { useCategoryStore } from '@/stores/useCategory'

interface Props {
  modelValue?: number | null
}

interface Emits {
  (e: 'update:modelValue', value: number | null): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null
})

const emit = defineEmits<Emits>()

const categoryStore = useCategoryStore()
const selectedCategory = ref<number | null>(props.modelValue)

const categoryOptions = computed(() => [
  { label: '全部分类', value: null },
  ...categoryStore.categories.map(cat => ({
    label: cat.name,
    value: cat.id
  }))
])

const handleFilterChange = (value: number | null) => {
  selectedCategory.value = value
  emit('update:modelValue', value)
  // 持久化到sessionStorage
  if (value === null) {
    sessionStorage.removeItem('selectedCategoryFilter')
  } else {
    sessionStorage.setItem('selectedCategoryFilter', String(value))
  }
}

onMounted(async () => {
  if (categoryStore.categories.length === 0) {
    await categoryStore.fetchCategories()
  }
  // 从sessionStorage恢复筛选
  const savedFilter = sessionStorage.getItem('selectedCategoryFilter')
  if (savedFilter) {
    selectedCategory.value = parseInt(savedFilter)
    emit('update:modelValue', parseInt(savedFilter))
  }
})

watch(() => props.modelValue, (newValue) => {
  selectedCategory.value = newValue
})
</script>

<style scoped>
.category-filter {
  width: 100%;
}
</style>
