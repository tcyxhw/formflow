/**
 * 表单分类状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as categoryAPI from '@/api/category'
import type { Category, CategoryCreateRequest, CategoryUpdateRequest } from '@/types/category'

export const useCategoryStore = defineStore('category', () => {
  // 状态
  const categories = ref<Category[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const defaultCategory = computed(() => categories.value.find(cat => cat.is_default))

  const categoryMap = computed(() => {
    const map = new Map<number, Category>()
    categories.value.forEach(cat => map.set(cat.id, cat))
    return map
  })

  /**
   * 获取分类列表
   */
  const fetchCategories = async (page: number = 1, pageSize: number = 100) => {
    loading.value = true
    error.value = null
    try {
      const response = await categoryAPI.listCategories(page, pageSize)
      if (response.data?.items) {
        categories.value = response.data.items
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取分类列表失败'
      console.error('Failed to fetch categories:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建分类
   */
  const createCategory = async (name: string): Promise<Category | null> => {
    loading.value = true
    error.value = null
    try {
      const response = await categoryAPI.createCategory({ name })
      if (response.data) {
        categories.value.push(response.data)
        return response.data
      }
      return null
    } catch (err) {
      error.value = err instanceof Error ? err.message : '创建分类失败'
      console.error('Failed to create category:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新分类
   */
  const updateCategory = async (id: number, name: string): Promise<Category | null> => {
    loading.value = true
    error.value = null
    try {
      const response = await categoryAPI.updateCategory(id, { name })
      if (response.data) {
        const index = categories.value.findIndex(cat => cat.id === id)
        if (index !== -1) {
          categories.value[index] = response.data
        }
        return response.data
      }
      return null
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新分类失败'
      console.error('Failed to update category:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除分类
   */
  const deleteCategory = async (id: number): Promise<boolean> => {
    loading.value = true
    error.value = null
    try {
      await categoryAPI.deleteCategory(id)
      categories.value = categories.value.filter(cat => cat.id !== id)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除分类失败'
      console.error('Failed to delete category:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    // 状态
    categories: computed(() => categories.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    defaultCategory,
    categoryMap,

    // 方法
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory
  }
})
