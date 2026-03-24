<template>
  <div class="fill-center">
    <!-- 页面标题 -->
    <header class="page-header">
      <div class="header-content">
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
          <p class="subtitle">填写您有权限的表单，查看历史提交记录</p>
        </div>
        <div class="header-actions">
          <n-button @click="goHome" quaternary class="home-btn">
            <template #icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                <polyline points="9 22 9 12 15 12 15 22"></polyline>
              </svg>
            </template>
            返回主页
          </n-button>
        </div>
      </div>
    </header>

    <!-- 搜索和筛选区域 -->
    <div class="filter-section">
      <div class="filter-content">
        <div class="search-box">
          <n-input
            v-model:value="filters.keyword"
            placeholder="搜索表单名称..."
            clearable
            size="large"
            @update:value="handleSearch"
          >
            <template #prefix>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
            </template>
          </n-input>
        </div>

        <div class="filter-divider"></div>

        <div class="filter-group">
          <n-select
            v-model:value="filters.category"
            placeholder="全部分类"
            clearable
            filterable
            size="medium"
            :options="categoryOptions"
            @update:value="handleFilterChange"
          />

          <n-select
            v-model:value="filters.ownerName"
            placeholder="全部发布人"
            clearable
            filterable
            size="medium"
            :options="ownerOptions"
            @update:value="handleFilterChange"
          />

          <n-button @click="handleReset" quaternary circle size="large" title="重置筛选">
            <template #icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
                <path d="M21 3v5h-5"></path>
                <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
                <path d="M3 21v-5h5"></path>
              </svg>
            </template>
          </n-button>
        </div>
      </div>
    </div>

    <!-- 第一部分：可填写的表单列表 -->
    <section class="section">
      <div class="section-header">
        <div class="section-title">
          <div class="title-icon blue">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
          </div>
          <div class="title-text">
            <h2>可填写的表单</h2>
            <span class="count">{{ filteredForms.length }} / {{ fillableForms.length }} 个表单</span>
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loadingFillable" class="loading-state">
        <n-spin size="large" />
        <p>正在加载表单列表...</p>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="fillableError" class="error-state">
        <div class="error-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        </div>
        <p>{{ fillableError }}</p>
        <n-button @click="loadFillableForms" type="primary">重新加载</n-button>
      </div>

      <!-- 空状态 -->
      <div v-else-if="filteredForms.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="64" height="64">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
          </svg>
        </div>
        <h3>{{ fillableForms.length === 0 ? '暂无可填写的表单' : '没有符合条件的表单' }}</h3>
        <p v-if="fillableForms.length === 0">请联系管理员为您分配表单填写权限</p>
        <p v-else>请尝试调整筛选条件</p>
      </div>

      <!-- 表单列表 -->
      <div v-else class="form-list-container">
        <div class="form-grid">
          <div
            v-for="form in filteredForms"
            :key="form.id"
            class="form-card"
            :class="{ 'submitted': hasSubmitted(form.id) }"
            @click="handleFillForm(form.id)"
          >
            <div class="form-card-header">
              <div class="form-title-row">
                <h3>{{ form.name }}</h3>
                <n-tag v-if="form.category" size="small" :type="getCategoryType(form.category)" class="category-tag">
                  {{ form.category }}
                </n-tag>
              </div>
              <div v-if="hasSubmitted(form.id)" class="submitted-badge">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="14" height="14">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                已填写
              </div>
            </div>
            
            <div class="form-card-body">
              <div class="form-meta">
                <span class="meta-item">
                  <span class="meta-icon user">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                      <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                  </span>
                  <span class="meta-label">发布人</span>
                  <span class="meta-value">{{ form.owner_name }}</span>
                </span>
                
                <span v-if="form.submit_deadline" class="meta-item">
                  <span class="meta-icon deadline">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                      <circle cx="12" cy="12" r="10"></circle>
                      <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                  </span>
                  <span class="meta-label">截止时间</span>
                  <span class="meta-value" :class="{ 'urgent': isDeadlineUrgent(form.submit_deadline) }">
                    {{ formatDate(form.submit_deadline) }}
                  </span>
                </span>
              </div>
            </div>
            
            <div class="form-card-footer">
              <n-button 
                :type="hasSubmitted(form.id) ? 'default' : 'primary'" 
                size="medium" 
                block
                class="action-btn"
              >
                <template #icon>
                  <svg v-if="!hasSubmitted(form.id)" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                  </svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                  </svg>
                </template>
                {{ hasSubmitted(form.id) ? '再次填写' : '开始填写' }}
              </n-button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 第二部分：已填写的表单记录 -->
    <section class="section">
      <div class="section-header">
        <div class="section-title">
          <div class="title-icon green">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
          </div>
          <div class="title-text">
            <h2>我的填写记录</h2>
            <span class="count">{{ filteredSubmissions.length }} / {{ mySubmissions.length }} 条记录</span>
          </div>
        </div>
      </div>

      <!-- 搜索区域 -->
      <div class="submission-search-section">
        <n-input
          v-model:value="submissionKeyword"
          placeholder="搜索已提交的表单..."
          clearable
          size="medium"
        >
          <template #prefix>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
          </template>
        </n-input>
      </div>

      <!-- 加载状态 -->
      <div v-if="loadingSubmissions" class="loading-state">
        <n-spin size="large" />
        <p>正在加载填写记录...</p>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="submissionsError" class="error-state">
        <div class="error-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        </div>
        <p>{{ submissionsError }}</p>
        <n-button @click="loadMySubmissions" type="primary">重新加载</n-button>
      </div>

      <!-- 空状态 -->
      <div v-else-if="mySubmissions.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="64" height="64">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
        </div>
        <h3>暂无填写记录</h3>
        <p>您还没有提交过任何表单</p>
      </div>

      <!-- 无搜索结果 -->
      <div v-else-if="filteredSubmissions.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="64" height="64">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
        </div>
        <h3>没有找到匹配的记录</h3>
        <p>请尝试其他搜索关键词</p>
      </div>

      <!-- 提交记录列表 -->
      <div v-else class="submission-list-container">
        <div class="submission-list">
          <div
            v-for="submission in filteredSubmissions"
            :key="submission.id"
            class="submission-card"
            :class="submission.status"
          >
            <!-- 左侧状态条 -->
            <div class="status-bar" :class="submission.status"></div>
            
            <!-- 主体内容 -->
            <div class="card-content">
              <div class="content-header">
                <div class="form-info">
                  <h4 class="form-name">{{ submission.form_name }}</h4>
                  <div class="submit-time">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                      <line x1="16" y1="2" x2="16" y2="6"></line>
                      <line x1="8" y1="2" x2="8" y2="6"></line>
                      <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg>
                    <span>{{ formatDateTime(submission.created_at) }}</span>
                  </div>
                </div>
                
                <div class="status-wrapper">
                  <div class="status-badge" :class="submission.status">
                    <span class="status-dot"></span>
                    <span class="status-text">{{ getStatusText(submission.status) }}</span>
                  </div>
                </div>
              </div>
              
              <div class="content-divider"></div>
              
              <div class="content-footer">
                <div class="record-id">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12">
                    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                  </svg>
                  <span>记录编号: #{{ submission.id }}</span>
                </div>
                
                <div class="action-buttons">
                  <n-button 
                    size="small" 
                    quaternary 
                    class="action-btn view"
                    @click.stop="handleViewSubmission(submission.id)"
                  >
                    <template #icon>
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                      </svg>
                    </template>
                    查看详情
                  </n-button>
                  <n-button 
                    type="primary" 
                    size="small" 
                    class="action-btn edit"
                    @click.stop="handleEditSubmission(submission)"
                  >
                    <template #icon>
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                      </svg>
                    </template>
                    编辑
                  </n-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
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

const router = useRouter()
const message = useMessage()

// 可填写表单列表
const fillableForms = ref<FillableFormItem[]>([])
const loadingFillable = ref(false)
const fillableError = ref<string | null>(null)

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
 * 查看提交详情
 */
const handleViewSubmission = (submissionId: number) => {
  router.push(`/submissions/${submissionId}`)
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
</style>
