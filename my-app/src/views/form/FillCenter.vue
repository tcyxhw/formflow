<template>
  <div class="fill-center">
    <!-- 左侧边栏 -->
    <aside class="left-sidebar">
      <div class="sidebar-header">
        <div class="header-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="28" height="28">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
        </div>
        <div class="header-text">
          <h1>表单填写中心</h1>
          <p class="subtitle">填写您有权限的表单</p>
        </div>
      </div>

      <!-- 搜索和筛选区域 -->
      <div class="filter-section">
        <div class="search-box">
          <n-input
            v-model:value="filters.keyword"
            placeholder="搜索表单名称..."
            clearable
            @update:value="handleSearch"
          >
            <template #prefix>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
            </template>
          </n-input>
        </div>

        <div class="filter-group">
          <n-select
            v-model:value="filters.category"
            placeholder="全部分类"
            clearable
            filterable
            size="small"
            :options="categoryOptions"
            @update:value="handleFilterChange"
          />
          <n-button @click="handleReset" quaternary circle size="small" title="重置筛选">
            <template #icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
                <path d="M21 3v5h-5"></path>
                <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
                <path d="M3 21v-5h5"></path>
              </svg>
            </template>
          </n-button>
        </div>
      </div>

      <!-- 表单列表 -->
      <div class="form-list-section">
        <div class="section-header">
          <h3>可填写的表单</h3>
          <span class="count">{{ filteredForms.length }} / {{ fillableForms.length }}</span>
        </div>

        <!-- 加载状态 -->
        <div v-if="loadingFillable" class="loading-state">
          <n-spin size="medium" />
          <p>加载中...</p>
        </div>

        <!-- 错误状态 -->
        <div v-else-if="fillableError" class="error-state">
          <p>{{ fillableError }}</p>
          <n-button @click="loadFillableForms" size="small">重新加载</n-button>
        </div>

        <!-- 空状态 -->
        <div v-else-if="filteredForms.length === 0" class="empty-state">
          <p>暂无可填写的表单</p>
        </div>

        <!-- 表单列表 -->
        <div v-else class="form-list">
          <div
            v-for="form in filteredForms"
            :key="form.id"
            class="form-list-item"
            :class="{ 'submitted': hasSubmitted(form.id), 'active': selectedFormId === form.id }"
            @click="selectForm(form)"
          >
            <div class="form-item-header">
              <div class="form-name">{{ form.name }}</div>
              <n-tag v-if="form.category" size="tiny" :type="getCategoryType(form.category)">
                {{ form.category }}
              </n-tag>
            </div>
            <div class="form-item-meta">
              <span class="meta-item">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
                {{ form.owner_name }}
              </span>
              <span class="meta-item" v-if="form.submit_deadline">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
                {{ formatDate(form.submit_deadline) }}
              </span>
            </div>
            <div class="form-item-status" v-if="hasSubmitted(form.id)">
              <n-tag size="tiny" type="success">已填写</n-tag>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 右侧主内容区 -->
    <main class="main-content">
      <!-- 顶部导航 -->
      <header class="content-header">
        <div class="header-left">
          <n-button text @click="goHome" class="back-btn">
            <template #icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                <polyline points="9 22 9 12 15 12 15 22"></polyline>
              </svg>
            </template>
            返回主页
          </n-button>
          <div class="breadcrumb" v-if="selectedForm">
            <span class="breadcrumb-item">填写中心</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item active">{{ selectedForm.name }}</span>
          </div>
        </div>
        <div class="header-right">
          <n-button type="primary" @click="selectedForm && handleFillForm(selectedForm.id)" :disabled="!selectedForm">
            <template #icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </template>
            {{ selectedForm && hasSubmitted(selectedForm.id) ? '再次填写' : '开始填写' }}
          </n-button>
        </div>
      </header>

      <!-- 内容区域 -->
      <div class="content-body">
        <!-- 未选择表单时的占位 -->
        <div v-if="!selectedForm" class="empty-placeholder">
          <div class="placeholder-content">
            <div class="placeholder-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="64" height="64">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
              </svg>
            </div>
            <h3>选择表单开始填写</h3>
            <p>从左侧列表中选择一个表单开始填写</p>
          </div>
        </div>

        <!-- 选择表单后的详情 -->
        <div v-else class="form-detail">
          <!-- 表单信息 -->
          <div class="form-info-card">
            <div class="info-header">
              <h2>{{ selectedForm.name }}</h2>
              <n-tag v-if="selectedForm.category" :type="getCategoryType(selectedForm.category)">
                {{ selectedForm.category }}
              </n-tag>
            </div>
            <div class="info-meta">
              <div class="meta-row">
                <span class="meta-label">发布人：</span>
                <span class="meta-value">{{ selectedForm.owner_name }}</span>
              </div>
              <div class="meta-row" v-if="selectedForm.submit_deadline">
                <span class="meta-label">截止时间：</span>
                <span class="meta-value" :class="{ 'urgent': isDeadlineUrgent(selectedForm.submit_deadline) }">
                  {{ formatDateTime(selectedForm.submit_deadline) }}
                </span>
              </div>
              <div class="meta-row" v-if="selectedForm.description">
                <span class="meta-label">表单描述：</span>
                <span class="meta-value">{{ selectedForm.description }}</span>
              </div>
            </div>
          </div>

          <!-- 填写记录 -->
          <div class="submission-history">
            <div class="section-header">
              <h3>我的填写记录</h3>
              <span class="count">{{ filteredSubmissions.length }} 条记录</span>
            </div>

            <!-- 搜索区域 -->
            <div class="submission-search">
              <n-input
                v-model:value="submissionKeyword"
                placeholder="搜索填写记录..."
                clearable
                size="small"
              >
                <template #prefix>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="m21 21-4.35-4.35"></path>
                  </svg>
                </template>
              </n-input>
            </div>

            <!-- 记录列表 -->
            <div class="submission-list">
              <div
                v-for="submission in filteredSubmissions"
                :key="submission.id"
                class="submission-list-item"
                :class="submission.status"
              >
                <div class="submission-item-header">
                  <div class="submission-time">{{ formatDateTime(submission.created_at) }}</div>
                  <n-tag :type="getStatusType(submission.status)" size="small">
                    {{ getStatusText(submission.status) }}
                  </n-tag>
                </div>
                <div class="submission-item-meta">
                  <span class="record-id">记录编号: #{{ submission.id }}</span>
                </div>
                <div class="submission-item-actions">
                  <n-button size="small" quaternary @click.stop="handleViewSubmission(submission.id)">
                    查看详情
                  </n-button>
                  <n-button size="small" type="primary" quaternary @click.stop="handleEditSubmission(submission)">
                    编辑
                  </n-button>
                </div>
              </div>

              <div v-if="filteredSubmissions.length === 0" class="empty-submissions">
                <p>暂无填写记录</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 提交详情弹窗 -->
    <SubmissionDetailModal
      v-model:show="showSubmissionModal"
      :submission-id="selectedSubmissionId"
    />
  </div>
</template>


<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { getFillableForms } from '@/api/workspace'
import { getSubmissionList } from '@/api/submission'
import type { FillableFormItem } from '@/types/workspace'
import type { SubmissionListItem } from '@/types/submission'
import SubmissionDetailModal from '@/components/submission/SubmissionDetailModal.vue'

const router = useRouter()
const message = useMessage()

// 提交详情弹窗状态
const showSubmissionModal = ref(false)
const selectedSubmissionId = ref<number | undefined>(undefined)

// 可填写表单列表
const fillableForms = ref<FillableFormItem[]>([])
const loadingFillable = ref(false)
const fillableError = ref<string | null>(null)

// 选中的表单
const selectedFormId = ref<number | null>(null)
const selectedForm = computed(() => {
  if (!selectedFormId.value) return null
  return fillableForms.value.find(f => f.id === selectedFormId.value) || null
})

const selectForm = (form: FillableFormItem) => {
  selectedFormId.value = form.id
}

// 我的提交记录
const mySubmissions = ref<SubmissionListItem[]>([])
const loadingSubmissions = ref(false)
const submissionsError = ref<string | null>(null)
const submissionKeyword = ref('')

// 填写记录筛选后的列表
const filteredSubmissions = computed(() => {
  if (!submissionKeyword.value) {
    return mySubmissions.value
  }
  const keyword = submissionKeyword.value.toLowerCase()
  return mySubmissions.value.filter(submission =>
    submission.form_name.toLowerCase().includes(keyword)
  )
})

// 筛选条件
const filters = ref({
  keyword: '',
  category: null as string | null,
  ownerName: null as string | null
})

// 计算分类选项（从表单列表中提取）
const categoryOptions = computed(() => {
  const categories = new Set<string>()
  fillableForms.value.forEach(form => {
    if (form.category) {
      categories.add(form.category)
    }
  })
  return Array.from(categories).map(cat => ({
    label: cat,
    value: cat
  }))
})

// 计算发布人选项（从表单列表中提取）
const ownerOptions = computed(() => {
  const owners = new Set<string>()
  fillableForms.value.forEach(form => {
    if (form.owner_name) {
      owners.add(form.owner_name)
    }
  })
  return Array.from(owners).map(owner => ({
    label: owner,
    value: owner
  }))
})

// 筛选后的表单列表
const filteredForms = computed(() => {
  let result = fillableForms.value

  // 关键词搜索
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase()
    result = result.filter(form => 
      form.name.toLowerCase().includes(keyword)
    )
  }

  // 分类筛选
  if (filters.value.category) {
    result = result.filter(form => form.category === filters.value.category)
  }

  // 发布人筛选
  if (filters.value.ownerName) {
    result = result.filter(form => form.owner_name === filters.value.ownerName)
  }

  return result
})

/**
 * 检查截止时间是否紧急（24小时内）
 */
const isDeadlineUrgent = (deadline: string): boolean => {
  const deadlineDate = new Date(deadline)
  const now = new Date()
  const diffHours = (deadlineDate.getTime() - now.getTime()) / (1000 * 60 * 60)
  return diffHours > 0 && diffHours <= 24
}

/**
 * 加载可填写的表单列表
 */
const loadFillableForms = async () => {
  loadingFillable.value = true
  fillableError.value = null
  
  try {
    const { data } = await getFillableForms({
      page: 1,
      page_size: 100,
      sort_by: 'created_at',
      sort_order: 'desc'
    })
    
    fillableForms.value = data.items
  } catch (e: any) {
    fillableError.value = e?.message || '加载失败'
    console.error('加载可填写表单失败:', e)
  } finally {
    loadingFillable.value = false
  }
}

/**
 * 加载我的提交记录
 */
const loadMySubmissions = async () => {
  loadingSubmissions.value = true
  submissionsError.value = null
  
  try {
    const { data } = await getSubmissionList({
      page: 1,
      page_size: 50,
    })
    
    mySubmissions.value = data.items
  } catch (e: any) {
    submissionsError.value = e?.message || '加载失败'
    console.error('加载提交记录失败:', e)
  } finally {
    loadingSubmissions.value = false
  }
}

/**
 * 检查是否已填写过某个表单
 */
const hasSubmitted = (formId: number): boolean => {
  return mySubmissions.value.some(s => s.form_id === formId)
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  // 搜索会自动触发 computed 重新计算
}

/**
 * 处理筛选变化
 */
const handleFilterChange = () => {
  // 筛选会自动触发 computed 重新计算
}

/**
 * 重置筛选
 */
const handleReset = () => {
  filters.value = {
    keyword: '',
    category: null,
    ownerName: null
  }
}

/**
 * 处理填写表单
 */
const handleFillForm = (formId: number) => {
  router.push(`/form/${formId}/fill`)
}

/**
 * 编辑提交记录
 */
const handleEditSubmission = (submission: SubmissionListItem) => {
  router.push(`/form/${submission.form_id}/fill?edit_submission_id=${submission.id}`)
}

/**
 * 查看提交详情（弹窗方式）
 */
const handleViewSubmission = (submissionId: number) => {
  selectedSubmissionId.value = submissionId
  showSubmissionModal.value = true
}

/**
 * 获取分类标签类型
 */
const getCategoryType = (category: string) => {
  const typeMap: Record<string, any> = {
    '学工': 'success',
    '教学': 'info',
    '科研': 'warning',
    '行政': 'default',
    '财务': 'error'
  }
  return typeMap[category] || 'default'
}

/**
 * 格式化日期
 */
const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 格式化日期时间
 */
const formatDateTime = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 获取状态标签类型
 */
const getStatusType = (status: string) => {
  const typeMap: Record<string, any> = {
    'submitted': 'info',
    'draft': 'default',
    'approved': 'success',
    'rejected': 'error'
  }
  return typeMap[status] || 'default'
}

/**
 * 获取状态文本
 */
const getStatusText = (status: string): string => {
  const textMap: Record<string, string> = {
    'submitted': '已提交',
    'draft': '草稿',
    'approved': '已通过',
    'rejected': '已拒绝'
  }
  return textMap[status] || status
}

const goHome = () => {
  router.push('/')
}

// 组件挂载时加载数据
onMounted(() => {
  loadFillableForms()
  loadMySubmissions()
})
</script>


<style scoped>
.fill-center {
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px 24px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  min-height: 100vh;
}

/* 页面标题 */
.page-header {
  margin-bottom: 24px;
  padding: 28px 32px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
  border: 1px solid #e2e8f0;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  border-radius: 14px;
  color: white;
  flex-shrink: 0;
}

.header-text h1 {
  margin: 0 0 6px 0;
  font-size: 26px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.5px;
}

.subtitle {
  margin: 0;
  font-size: 15px;
  color: #64748b;
  font-weight: 400;
}

.header-actions {
  margin-left: auto;
}

.home-btn {
  color: #64748b;
  font-weight: 500;
}

.home-btn:hover {
  color: #3b82f6;
  background: #eff6ff;
}

/* 筛选区域 */
.filter-section {
  margin-bottom: 24px;
  padding: 20px 24px;
  background: white;
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
  border: 1px solid #e2e8f0;
}

.filter-content {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 280px;
  max-width: 420px;
}

.filter-divider {
  width: 1px;
  height: 36px;
  background: #e2e8f0;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-group :deep(.n-select) {
  width: 160px;
}

/* 区块 */
.section {
  margin-bottom: 28px;
  background: white;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
  border: 1px solid #e2e8f0;
}

.section-header {
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 14px;
}

.title-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  flex-shrink: 0;
}

.title-icon.blue {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #2563eb;
}

.title-icon.green {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  color: #16a34a;
}

.title-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-text h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

.count {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

/* 加载/错误/空状态 */
.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.loading-state p,
.error-state p,
.empty-state p {
  margin: 16px 0 0 0;
  font-size: 14px;
  color: #94a3b8;
}

.empty-state h3 {
  margin: 20px 0 8px 0;
  font-size: 17px;
  font-weight: 600;
  color: #334155;
}

.empty-icon {
  color: #cbd5e1;
}

.error-icon {
  color: #f87171;
}

/* 表单列表容器 */
.form-list-container {
  max-height: 640px;
  overflow-y: auto;
  padding-right: 4px;
  margin-right: -4px;
}

/* 自定义滚动条 */
.form-list-container::-webkit-scrollbar {
  width: 6px;
}

.form-list-container::-webkit-scrollbar-track {
  background: transparent;
}

.form-list-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.form-list-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 表单网格 */
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

/* 表单卡片 */
.form-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 22px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.form-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6, #6366f1);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.form-card.submitted::before {
  background: linear-gradient(90deg, #22c55e, #16a34a);
}

.form-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 10px 40px -10px rgba(59, 130, 246, 0.25);
  transform: translateY(-3px);
}

.form-card.submitted:hover {
  border-color: #22c55e;
  box-shadow: 0 10px 40px -10px rgba(34, 197, 94, 0.25);
}

.form-card:hover::before {
  opacity: 1;
}

.form-card-header {
  margin-bottom: 16px;
}

.form-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.form-title-row h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  flex: 1;
  line-height: 1.5;
}

.category-tag {
  flex-shrink: 0;
}

.submitted-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  color: #16a34a;
  background: #dcfce7;
  padding: 4px 10px;
  border-radius: 20px;
}

.form-card-body {
  flex: 1;
  margin-bottom: 18px;
}

.form-meta {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.meta-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  flex-shrink: 0;
}

.meta-icon.user {
  background: #eff6ff;
  color: #3b82f6;
}

.meta-icon.deadline {
  background: #fef3c7;
  color: #f59e0b;
}

.meta-label {
  color: #94a3b8;
  min-width: 56px;
}

.meta-value {
  color: #475569;
  font-weight: 500;
}

.meta-value.urgent {
  color: #ef4444;
  font-weight: 600;
}

.form-card-footer {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.action-btn {
  font-weight: 500;
}

/* 提交记录搜索 */
.submission-search-section {
  margin-bottom: 20px;
  max-width: 400px;
}

/* 提交记录列表容器 - 固定高度可滚动 */
.submission-list-container {
  max-height: 480px;
  overflow-y: auto;
  padding-right: 4px;
  margin-right: -4px;
}

/* 自定义滚动条 */
.submission-list-container::-webkit-scrollbar {
  width: 6px;
}

.submission-list-container::-webkit-scrollbar-track {
  background: transparent;
}

.submission-list-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.submission-list-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 提交记录列表 */
.submission-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 提交记录卡片 */
.submission-card {
  display: flex;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.25s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.submission-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

/* 左侧状态条 */
.status-bar {
  width: 4px;
  flex-shrink: 0;
}

.status-bar.submitted {
  background: #3b82f6;
}

.status-bar.approved {
  background: #22c55e;
}

.status-bar.rejected {
  background: #ef4444;
}

.status-bar.draft {
  background: #94a3b8;
}

/* 卡片内容 */
.card-content {
  flex: 1;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 内容头部 */
.content-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.form-info {
  flex: 1;
  min-width: 0;
}

.form-name {
  margin: 0 0 6px 0;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.submit-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #64748b;
}

.submit-time svg {
  color: #94a3b8;
  flex-shrink: 0;
}

/* 状态徽章 */
.status-wrapper {
  flex-shrink: 0;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge.submitted {
  background: #eff6ff;
  color: #2563eb;
}

.status-badge.approved {
  background: #f0fdf4;
  color: #16a34a;
}

.status-badge.rejected {
  background: #fef2f2;
  color: #dc2626;
}

.status-badge.draft {
  background: #f1f5f9;
  color: #64748b;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-badge.submitted .status-dot {
  background: #3b82f6;
}

.status-badge.approved .status-dot {
  background: #22c55e;
}

.status-badge.rejected .status-dot {
  background: #ef4444;
}

.status-badge.draft .status-dot {
  background: #94a3b8;
}

/* 内容分隔线 */
.content-divider {
  height: 1px;
  background: #f1f5f9;
}

/* 内容底部 */
.content-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.record-id {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #94a3b8;
}

.record-id svg {
  opacity: 0.6;
  flex-shrink: 0;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.action-btn {
  font-weight: 500;
}

.action-btn.view {
  color: #64748b;
}

.action-btn.view:hover {
  color: #3b82f6;
  background: #eff6ff;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .form-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
}

@media (max-width: 768px) {
  .fill-center {
    padding: 16px;
  }

  .page-header {
    padding: 20px;
  }

  .header-content {
    flex-direction: column;
    text-align: center;
  }

  .header-icon {
    width: 48px;
    height: 48px;
  }

  .filter-section {
    padding: 16px;
  }

  .filter-content {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box {
    max-width: none;
  }

  .filter-divider {
    width: 100%;
    height: 1px;
  }

  .filter-group {
    justify-content: flex-start;
  }

  .section {
    padding: 20px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .submission-card {
    border-radius: 10px;
  }

  .card-content {
    padding: 14px 16px;
    gap: 10px;
  }

  .content-header {
    flex-direction: column;
    gap: 10px;
  }

  .form-name {
    font-size: 14px;
    white-space: normal;
    overflow: visible;
    text-overflow: clip;
  }

  .status-badge {
    padding: 5px 10px;
    font-size: 11px;
  }

  .content-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .action-buttons {
    width: 100%;
  }

  .action-buttons :deep(.n-button) {
    flex: 1;
  }
}

/* 新的左右布局样式 */
.fill-center {
  display: grid;
  grid-template-columns: 380px 1fr;
  min-height: 100vh;
  background: #f8fafc;
  margin: 0;
  padding: 0;
  max-width: none;
}

/* 左侧边栏 */
.left-sidebar {
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 24px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
}

.sidebar-header .header-icon {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-header .header-text h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #ffffff;
}

.sidebar-header .header-text .subtitle {
  margin: 4px 0 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

/* 过滤区域 */
.filter-section {
  padding: 16px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.search-box {
  margin-bottom: 12px;
}

.filter-group {
  display: flex;
  gap: 8px;
}

.filter-group .n-select {
  flex: 1;
}

/* 表单列表区域 */
.form-list-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.form-list-section .section-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-list-section .section-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a202c;
}

.form-list-section .section-header .count {
  font-size: 14px;
  color: #64748b;
}

.form-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.form-list-item {
  padding: 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 8px;
  border: 1px solid transparent;
}

.form-list-item:hover {
  background: #f8fafc;
  border-color: #e2e8f0;
}

.form-list-item.active {
  background: #f0f5ff;
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.form-list-item.submitted {
  border-left: 4px solid #10b981;
}

.form-item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.form-item-header .form-name {
  font-weight: 600;
  color: #1a202c;
  font-size: 14px;
  line-height: 1.4;
  flex: 1;
  margin-right: 8px;
}

.form-item-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-item-meta .meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
}

.form-item-status {
  margin-top: 8px;
}

/* 右侧主内容区 */
.main-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-header {
  padding: 16px 24px;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  color: #64748b;
}

.back-btn:hover {
  color: #667eea;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.breadcrumb-item {
  color: #64748b;
}

.breadcrumb-item.active {
  color: #1a202c;
  font-weight: 500;
}

.breadcrumb-separator {
  color: #cbd5e0;
}

.header-right {
  display: flex;
  gap: 12px;
}

.content-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: #f8fafc;
}

/* 空占位符 */
.empty-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-content {
  text-align: center;
  color: #64748b;
}

.placeholder-icon {
  width: 120px;
  height: 120px;
  background: #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
}

.placeholder-content h3 {
  margin: 0 0 8px;
  font-size: 20px;
  color: #1a202c;
}

.placeholder-content p {
  margin: 0;
  font-size: 14px;
}

/* 表单详情 */
.form-detail {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-info-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.info-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #1a202c;
}

.info-meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-row {
  display: flex;
  gap: 8px;
}

.meta-label {
  color: #64748b;
  font-size: 14px;
  min-width: 80px;
}

.meta-value {
  color: #1a202c;
  font-size: 14px;
}

.meta-value.urgent {
  color: #ef4444;
  font-weight: 500;
}

/* 填写记录 */
.submission-history {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.submission-history .section-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.submission-history .section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a202c;
}

.submission-search {
  padding: 16px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.submission-list {
  padding: 8px;
}

.submission-list-item {
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 8px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.submission-list-item:hover {
  border-color: #cbd5e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.submission-list-item.submitted {
  border-left: 4px solid #3b82f6;
}

.submission-list-item.draft {
  border-left: 4px solid #f59e0b;
}

.submission-list-item.approved {
  border-left: 4px solid #10b981;
}

.submission-list-item.rejected {
  border-left: 4px solid #ef4444;
}

.submission-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.submission-time {
  font-weight: 500;
  color: #1a202c;
  font-size: 14px;
}

.submission-item-meta {
  margin-bottom: 12px;
}

.record-id {
  font-size: 12px;
  color: #64748b;
}

.submission-item-actions {
  display: flex;
  gap: 8px;
}

.empty-submissions {
  text-align: center;
  padding: 40px 24px;
  color: #64748b;
}

/* 加载和错误状态 */
.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 40px 24px;
  color: #64748b;
}

.loading-state p,
.error-state p,
.empty-state p {
  margin: 12px 0 0;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .fill-center {
    grid-template-columns: 1fr;
  }
  
  .left-sidebar {
    max-height: 400px;
    border-right: none;
    border-bottom: 1px solid #e2e8f0;
  }
}
</style>
