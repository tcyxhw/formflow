// src/composables/useFillWorkspace.ts
/**
 * 表单填写工作区组合函数
 * 
 * 功能:
 * - 管理表单列表状态（forms, loading, error）
 * - 管理分页状态（page, pageSize, total, totalPages）
 * - 管理筛选状态（keyword, status, category, sortBy, sortOrder）
 * - 提供表单加载、搜索、筛选、分页、排序等方法
 * 
 * 依赖: @vueuse/core (useDebounceFn), workspace API
 */

import { ref, reactive } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import { getFillableForms } from '@/api/workspace'
import type {
  FillableFormItem,
  FilterState,
  PaginationState
} from '@/types/workspace'

/**
 * 表单填写工作区组合函数
 * 
 * @returns 工作区状态和方法
 */
export function useFillWorkspace() {
  // 表单列表数据
  const forms = ref<FillableFormItem[]>([])
  
  // 加载状态
  const loading = ref(false)
  
  // 错误信息
  const error = ref<string | null>(null)
  
  // 分页状态
  const pagination = reactive<PaginationState>({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0
  })
  
  // 筛选状态
  const filters = reactive<FilterState>({
    keyword: '',
    status: null,
    category: null,
    sortBy: 'created_at',
    sortOrder: 'desc'
  })
  
  // 批量选择状态
  const selectedFormIds = ref<Set<number>>(new Set())
  const isBatchMode = ref(false)
  
  /**
   * 加载表单列表
   * 根据当前的分页和筛选状态从API获取表单数据
   */
  const loadForms = async () => {
    loading.value = true
    error.value = null
    
    try {
      const { data } = await getFillableForms({
        page: pagination.page,
        page_size: pagination.pageSize,
        keyword: filters.keyword || undefined,
        status: filters.status || undefined,
        category: filters.category || undefined,
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder
      })
      
      forms.value = data.items
      pagination.total = data.total
      pagination.totalPages = data.total_pages
    } catch (e: any) {
      error.value = e?.message || '加载表单列表失败'
      forms.value = []
      pagination.total = 0
      pagination.totalPages = 0
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 防抖搜索方法
   * 使用300ms防抖延迟，避免频繁请求
   * 
   * @param keyword 搜索关键词
   */
  const debouncedSearch = useDebounceFn((keyword: string) => {
    filters.keyword = keyword
    pagination.page = 1 // 搜索时重置到第一页
    loadForms()
  }, 300)
  
  /**
   * 处理筛选条件变化
   * 
   * @param newFilters 新的筛选条件（部分更新）
   */
  const handleFilter = (newFilters: Partial<FilterState>) => {
    Object.assign(filters, newFilters)
    pagination.page = 1 // 筛选时重置到第一页
    loadForms()
  }
  
  /**
   * 处理分页变化
   * 
   * @param page 新的页码
   */
  const handlePageChange = (page: number) => {
    pagination.page = page
    loadForms()
  }
  
  /**
   * 处理排序变化
   * 
   * @param sortBy 排序字段
   * @param sortOrder 排序方向
   */
  const handleSort = (sortBy: string, sortOrder: 'asc' | 'desc') => {
    filters.sortBy = sortBy
    filters.sortOrder = sortOrder
    pagination.page = 1 // 排序时重置到第一页
    loadForms()
  }
  
  /**
   * 切换批量模式
   */
  const toggleBatchMode = () => {
    isBatchMode.value = !isBatchMode.value
    if (!isBatchMode.value) {
      // 退出批量模式时清空选择
      selectedFormIds.value.clear()
    }
  }
  
  /**
   * 切换表单选择状态
   * 
   * @param formId 表单ID
   */
  const toggleFormSelection = (formId: number) => {
    if (selectedFormIds.value.has(formId)) {
      selectedFormIds.value.delete(formId)
    } else {
      selectedFormIds.value.add(formId)
    }
  }
  
  /**
   * 全选当前页面的表单
   */
  const selectAll = () => {
    forms.value.forEach(form => {
      selectedFormIds.value.add(form.id)
    })
  }
  
  /**
   * 取消全选
   */
  const deselectAll = () => {
    selectedFormIds.value.clear()
  }
  
  /**
   * 检查是否全选
   */
  const isAllSelected = () => {
    if (forms.value.length === 0) return false
    return forms.value.every(form => selectedFormIds.value.has(form.id))
  }
  
  /**
   * 检查是否部分选择
   */
  const isIndeterminate = () => {
    const selectedCount = forms.value.filter(form => 
      selectedFormIds.value.has(form.id)
    ).length
    return selectedCount > 0 && selectedCount < forms.value.length
  }
  
  /**
   * 批量打开填写页面
   */
  const batchFill = () => {
    const selectedForms = forms.value.filter(form => 
      selectedFormIds.value.has(form.id)
    )
    
    selectedForms.forEach(form => {
      // 在新标签页中打开表单填写页面
      const url = `/forms/${form.id}/fill`
      window.open(url, '_blank')
    })
  }
  
  return {
    // 状态
    forms,
    loading,
    error,
    pagination,
    filters,
    selectedFormIds,
    isBatchMode,
    
    // 方法
    loadForms,
    debouncedSearch,
    handleFilter,
    handlePageChange,
    handleSort,
    toggleBatchMode,
    toggleFormSelection,
    selectAll,
    deselectAll,
    isAllSelected,
    isIndeterminate,
    batchFill
  }
}
