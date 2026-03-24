<template>
  <div class="fill-workspace">
    <!-- 页面标题 -->
    <div class="workspace-header">
      <h1 class="workspace-title">表单填写工作区</h1>
      <p class="workspace-subtitle">查看和填写您有权限的表单</p>
    </div>

    <!-- 快捷入口 -->
    <QuickAccess />

    <!-- 搜索和筛选区域 -->
    <div class="workspace-toolbar">
      <div class="search-section">
        <SearchBar
          v-model="filters.keyword"
          placeholder="搜索表单标题或描述..."
          @search="handleSearch"
        />
      </div>

      <div class="filter-section">
        <n-button @click="showFilterPanel = !showFilterPanel">
          <template #icon>
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
              <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
            </svg>
          </template>
          筛选
        </n-button>
        
        <n-button @click="toggleBatchMode" :type="isBatchMode ? 'primary' : 'default'">
          <template #icon>
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
              <path d="M9 11l3 3L22 4"></path>
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
            </svg>
          </template>
          {{ isBatchMode ? '退出批量' : '批量操作' }}
        </n-button>
      </div>
    </div>

    <!-- 批量操作工具栏 -->
    <n-collapse-transition :show="isBatchMode && selectedFormIds.size > 0">
      <div class="batch-toolbar">
        <div class="batch-info">
          <n-checkbox
            :checked="isAllSelected()"
            :indeterminate="isIndeterminate()"
            @update:checked="handleSelectAllChange"
          >
            已选择 {{ selectedFormIds.size }} 个表单
          </n-checkbox>
        </div>
        
        <div class="batch-actions">
          <n-button type="primary" @click="handleBatchFill">
            <template #icon>
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
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </template>
            批量填写
          </n-button>
          
          <n-button @click="handleBatchExport">
            <template #icon>
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
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
            </template>
            批量导出
          </n-button>
          
          <n-button @click="deselectAll">
            清空选择
          </n-button>
        </div>
      </div>
    </n-collapse-transition>

    <!-- 筛选面板（可折叠） -->
    <n-collapse-transition :show="showFilterPanel">
      <div class="filter-panel-wrapper">
        <FilterPanel
          v-model="filters"
          :categories="availableCategories"
          @apply="handleFilterApply"
        />
      </div>
    </n-collapse-transition>

    <!-- 表单列表区域 -->
    <div class="workspace-content">
      <!-- 加载状态 - 使用骨架屏 -->
      <div v-if="loading" class="form-list">
        <FormCardSkeleton v-for="i in pagination.pageSize" :key="`skeleton-${i}`" />
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="error-state">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="error-icon"
        >
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <p class="error-text">{{ error }}</p>
        <n-button type="primary" @click="loadForms">
          重试
        </n-button>
      </div>

      <!-- 空状态 -->
      <div v-else-if="forms.length === 0" class="empty-state">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="empty-icon"
        >
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
        </svg>
        <p class="empty-text">
          {{ filters.keyword ? '未找到匹配的表单' : '暂无可填写的表单' }}
        </p>
        <p v-if="filters.keyword || filters.status || filters.category" class="empty-hint">
          尝试调整搜索关键词或清除筛选条件
        </p>
        <n-button
          v-if="filters.keyword || filters.status || filters.category"
          type="primary"
          @click="handleClearFilters"
          style="margin-top: 16px"
        >
          清除筛选条件
        </n-button>
      </div>

      <!-- 表单列表 -->
      <div v-else class="form-list">
        <FormCard
          v-for="(form, index) in forms"
          :key="form.id"
          :form="form"
          :is-batch-mode="isBatchMode"
          :is-selected="selectedFormIds.has(form.id)"
          :search-keyword="filters.keyword"
          :class="{ 'is-focused': selectedCardIndex === index }"
          :ref="el => setCardRef(el, index)"
          @toggle-selection="toggleFormSelection"
        />
      </div>
    </div>

    <!-- 分页控件 -->
    <div v-if="!loading && !error && forms.length > 0" class="workspace-pagination">
      <n-pagination
        v-model:page="pagination.page"
        :page-count="pagination.totalPages"
        :page-size="pagination.pageSize"
        :item-count="pagination.total"
        show-size-picker
        :page-sizes="[10, 20, 30, 50]"
        show-quick-jumper
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      >
        <template #prefix="{ itemCount }">
          共 {{ itemCount }} 个表单
        </template>
      </n-pagination>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NSpin, NPagination, NCollapseTransition, NCheckbox, useMessage } from 'naive-ui'
import SearchBar from '@/components/workspace/SearchBar.vue'
import FilterPanel from '@/components/workspace/FilterPanel.vue'
import FormCard from '@/components/workspace/FormCard.vue'
import FormCardSkeleton from '@/components/workspace/FormCardSkeleton.vue'
import QuickAccess from '@/components/workspace/QuickAccess.vue'
import { useFillWorkspace } from '@/composables/useFillWorkspace'
import { useTenantStore } from '@/stores/tenant'

// 使用工作区组合函数
const {
  forms,
  loading,
  error,
  pagination,
  filters,
  selectedFormIds,
  isBatchMode,
  loadForms,
  debouncedSearch,
  handleFilter,
  handlePageChange: changePage,
  handleSort,
  toggleBatchMode,
  toggleFormSelection,
  selectAll,
  deselectAll,
  isAllSelected,
  isIndeterminate,
  batchFill
} = useFillWorkspace()

const router = useRouter()
const message = useMessage()
const tenantStore = useTenantStore()

// 筛选面板显示状态
const showFilterPanel = ref(false)

// 键盘导航相关状态
const selectedCardIndex = ref<number>(-1)
const cardRefs = ref<Map<number, any>>(new Map())

// 自动刷新定时器
let refreshTimer: number | null = null

// 可用的类别列表（从表单列表中提取）
const availableCategories = computed(() => {
  const categories = new Set<string>()
  forms.value.forEach(form => {
    if (form.category) {
      categories.add(form.category)
    }
  })
  return Array.from(categories)
})

/**
 * 清除所有筛选条件
 */
const handleClearFilters = () => {
  filters.keyword = ''
  filters.status = null
  filters.category = null
  pagination.page = 1
  loadForms()
}

/**
 * 处理搜索
 */
const handleSearch = (keyword: string) => {
  debouncedSearch(keyword)
}

/**
 * 处理筛选应用
 */
const handleFilterApply = () => {
  loadForms()
}

/**
 * 处理分页变化
 */
const handlePageChange = (page: number) => {
  changePage(page)
  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

/**
 * 处理每页数量变化
 */
const handlePageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.page = 1 // 重置到第一页
  loadForms()
}

/**
 * 启动自动刷新
 * 每60秒自动刷新表单列表
 */
const startAutoRefresh = () => {
  refreshTimer = window.setInterval(() => {
    loadForms()
  }, 60000) // 60秒
}

/**
 * 停止自动刷新
 */
const stopAutoRefresh = () => {
  if (refreshTimer !== null) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

/**
 * 设置卡片引用
 */
const setCardRef = (el: any, index: number) => {
  if (el) {
    cardRefs.value.set(index, el)
  } else {
    cardRefs.value.delete(index)
  }
}

/**
 * 处理键盘事件
 */
const handleKeyDown = (event: KeyboardEvent) => {
  // 如果表单列表为空，不处理键盘事件
  if (forms.value.length === 0) {
    return
  }

  // 处理方向键
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    
    // 如果没有选中任何卡片，选中第一个
    if (selectedCardIndex.value === -1) {
      selectedCardIndex.value = 0
    } else if (selectedCardIndex.value < forms.value.length - 1) {
      // 向下移动选择
      selectedCardIndex.value++
    }
    
    // 滚动到选中的卡片
    scrollToSelectedCard()
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    
    // 如果没有选中任何卡片，选中最后一个
    if (selectedCardIndex.value === -1) {
      selectedCardIndex.value = forms.value.length - 1
    } else if (selectedCardIndex.value > 0) {
      // 向上移动选择
      selectedCardIndex.value--
    }
    
    // 滚动到选中的卡片
    scrollToSelectedCard()
  } else if (event.key === 'Enter') {
    // 按下 Enter 键导航到选中的表单
    if (selectedCardIndex.value >= 0 && selectedCardIndex.value < forms.value.length) {
      event.preventDefault()
      navigateToSelectedForm()
    }
  }
}

/**
 * 滚动到选中的卡片
 */
const scrollToSelectedCard = () => {
  const cardElement = cardRefs.value.get(selectedCardIndex.value)
  if (cardElement && cardElement.$el) {
    cardElement.$el.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest'
    })
  }
}

/**
 * 导航到选中的表单
 */
const navigateToSelectedForm = () => {
  const selectedForm = forms.value[selectedCardIndex.value]
  
  if (!selectedForm) {
    return
  }
  
  // 检查表单状态
  if (!selectedForm.can_fill) {
    message.warning('您没有权限填写此表单')
    return
  }
  
  if (selectedForm.is_expired) {
    message.warning('此表单已过期')
    return
  }
  
  if (selectedForm.is_closed) {
    message.warning('此表单已关闭')
    return
  }
  
  if (selectedForm.is_fill_limit_reached) {
    message.warning('此表单已达到填写上限')
    return
  }
  
  // 导航到表单填写页面
  router.push(`/forms/${selectedForm.id}/fill`)
}

// 监听表单列表变化，重置选中状态
watch(forms, () => {
  selectedCardIndex.value = -1
  cardRefs.value.clear()
})

// 监听分页变化，清空批量选择
watch(() => pagination.page, () => {
  if (isBatchMode.value) {
    deselectAll()
  }
})

// 监听租户切换，重新加载表单列表
watch(() => tenantStore.tenantId, (newTenantId, oldTenantId) => {
  // 只有在租户ID真正变化时才重新加载
  if (newTenantId !== oldTenantId && newTenantId !== undefined) {
    // 清除筛选和搜索状态
    filters.keyword = ''
    filters.status = null
    filters.category = null
    filters.sortBy = 'created_at'
    filters.sortOrder = 'desc'
    
    // 重置分页
    pagination.page = 1
    pagination.pageSize = 20
    
    // 清空批量选择
    if (isBatchMode.value) {
      deselectAll()
    }
    
    // 重新加载表单列表
    loadForms()
  }
})

/**
 * 处理全选/取消全选
 */
const handleSelectAllChange = (checked: boolean) => {
  if (checked) {
    selectAll()
  } else {
    deselectAll()
  }
}

/**
 * 处理批量填写
 */
const handleBatchFill = () => {
  if (selectedFormIds.value.size === 0) {
    message.warning('请先选择要填写的表单')
    return
  }
  
  // 检查选择的表单是否都可以填写
  const selectedForms = forms.value.filter(form => selectedFormIds.value.has(form.id))
  const invalidForms = selectedForms.filter(form => 
    !form.can_fill || form.is_expired || form.is_closed || form.is_fill_limit_reached
  )
  
  if (invalidForms.length > 0) {
    message.warning(`有 ${invalidForms.length} 个表单无法填写，已自动跳过`)
  }
  
  batchFill()
  message.success(`已在新标签页中打开 ${selectedForms.length - invalidForms.length} 个表单`)
}

/**
 * 处理批量导出
 */
const handleBatchExport = () => {
  if (selectedFormIds.value.size === 0) {
    message.warning('请先选择要导出的表单')
    return
  }
  
  // TODO: 实现批量导出功能
  message.info('批量导出功能开发中...')
}

// 组件挂载时加载表单列表并启动自动刷新
onMounted(() => {
  loadForms()
  startAutoRefresh()
  
  // 添加键盘事件监听
  window.addEventListener('keydown', handleKeyDown)
})

// 组件卸载时停止自动刷新
onUnmounted(() => {
  stopAutoRefresh()
  
  // 移除键盘事件监听
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.fill-workspace {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

/* 页面标题 */
.workspace-header {
  margin-bottom: 24px;
}

.workspace-title {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: var(--n-text-color);
}

.workspace-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--n-text-color-3);
}

/* 工具栏 */
.workspace-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.search-section {
  flex: 1;
}

.filter-section {
  flex-shrink: 0;
  display: flex;
  gap: 8px;
}

/* 批量操作工具栏 */
.batch-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  margin-bottom: 16px;
  background-color: var(--n-color);
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
}

.batch-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--n-text-color-2);
}

.batch-actions {
  display: flex;
  gap: 8px;
}

/* 筛选面板 */
.filter-panel-wrapper {
  margin-bottom: 16px;
}

/* 内容区域 */
.workspace-content {
  min-height: 400px;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
}

.loading-text {
  margin-top: 16px;
  font-size: 14px;
  color: var(--n-text-color-3);
}

/* 错误状态 */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
}

.error-icon {
  width: 64px;
  height: 64px;
  color: var(--n-error-color);
  margin-bottom: 16px;
}

.error-text {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: var(--n-text-color-2);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
}

.empty-icon {
  width: 64px;
  height: 64px;
  color: var(--n-text-color-3);
  margin-bottom: 16px;
}

.empty-text {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: var(--n-text-color-2);
}

.empty-hint {
  margin: 0;
  font-size: 14px;
  color: var(--n-text-color-3);
}

/* 表单列表 */
.form-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

/* 键盘导航焦点样式 */
.form-list :deep(.form-card.is-focused) {
  outline: 2px solid var(--n-color-target);
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(24, 160, 88, 0.1);
}

/* 分页控件 */
.workspace-pagination {
  display: flex;
  justify-content: center;
  padding: 24px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .fill-workspace {
    padding: 16px;
  }

  .workspace-title {
    font-size: 24px;
  }

  .workspace-toolbar {
    flex-direction: column;
  }

  .form-list {
    grid-template-columns: 1fr;
  }
}
</style>
