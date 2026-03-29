<template>
  <div class="my-approvals-page">
    <!-- 页面头部 -->
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
          <h1>我的审批</h1>
          <p class="subtitle">查看我发起的审批进度与详情</p>
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

    <!-- 主要内容区域 -->
    <div class="main-container">
      <!-- 左侧：审批列表 -->
      <aside class="approval-list-sidebar">
        <div class="sidebar-header">
          <h3>审批列表</h3>
          <n-button text size="small" @click="refreshApprovals">
            <template #icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
                <path d="M21 3v5h-5"></path>
                <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
                <path d="M3 21v-5h5"></path>
              </svg>
            </template>
            刷新
          </n-button>
        </div>

        <!-- 搜索框 -->
        <div class="search-box">
          <n-input
            v-model:value="searchKeyword"
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

        <!-- 审批列表 -->
        <div class="approval-list" v-loading="loading">
          <div
            v-for="approval in filteredApprovals"
            :key="approval.id"
            class="approval-item"
            :class="{ active: selectedApproval?.id === approval.id }"
            @click="selectApproval(approval)"
          >
            <div class="approval-item-header">
              <div class="approval-title">{{ approval.form_name }}</div>
              <n-tag
                :type="getStateType(approval.process_state, approval.is_overdue)"
                size="small"
                :bordered="false"
              >
                {{ getStateLabel(approval.process_state, approval.is_overdue) }}
              </n-tag>
            </div>
            <div class="approval-item-meta">
              <div class="meta-item">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                  <line x1="16" y1="2" x2="16" y2="6"></line>
                  <line x1="8" y1="2" x2="8" y2="6"></line>
                  <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
                <span>{{ formatDate(approval.created_at) }}</span>
              </div>
              <div class="meta-item" v-if="approval.due_at">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
                <span :class="{ overdue: approval.is_overdue }">
                  {{ formatDate(approval.due_at) }}
                </span>
              </div>
            </div>
          </div>

          <n-empty v-if="filteredApprovals.length === 0 && !loading" description="暂无审批记录" />
        </div>
      </aside>

      <!-- 右侧：审批详情 -->
      <main class="approval-detail-main" v-if="selectedApproval">
        <!-- 审批详情头部 -->
        <div class="detail-header">
          <div class="detail-title">
            <h2>{{ selectedApproval.form_name }}</h2>
            <n-tag
              :type="getStateType(selectedApproval.process_state, selectedApproval.is_overdue)"
              :bordered="false"
            >
              {{ getStateLabel(selectedApproval.process_state, selectedApproval.is_overdue) }}
            </n-tag>
          </div>
          <div class="detail-meta">
            <div class="meta-item">
              <span class="meta-label">提交时间：</span>
              <span>{{ formatDateTime(selectedApproval.created_at) }}</span>
            </div>
            <div class="meta-item" v-if="selectedApproval.due_at">
              <span class="meta-label">截止时间：</span>
              <span :class="{ overdue: selectedApproval.is_overdue }">
                {{ formatDateTime(selectedApproval.due_at) }}
              </span>
            </div>
          </div>
        </div>

        <!-- 流程图区域 -->
        <div class="flow-diagram-section">
          <div class="section-header">
            <h3>审批流程</h3>
            <n-button text size="small" @click="refreshFlowData">
              <template #icon>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                  <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
                  <path d="M21 3v5h-5"></path>
                  <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
                  <path d="M3 21v-5h5"></path>
                </svg>
              </template>
              刷新
            </n-button>
          </div>

          <div class="flow-diagram-container" v-loading="flowLoading">
            <div v-if="flowNodes.length > 0" class="flow-diagram-wrapper">
              <FlowDiagram :nodes="flowNodes" :routes="flowRoutes" :fieldLabels="fieldLabels" />
            </div>
            <n-empty v-else description="暂无流程图数据" />
          </div>
        </div>

        <!-- 表单数据展示 -->
        <div class="form-data-section">
          <div class="section-header">
            <h3>表单数据</h3>
          </div>

          <div class="form-data-container" v-loading="loadingSubmissionDetail">
            <div v-if="displayFields.length > 0" class="form-fields">
              <div
                v-for="(item, index) in displayFields"
                :key="item.key"
                class="form-field-item"
                :class="{ 'field-alt': index % 2 === 1 }"
              >
                <div class="field-label">{{ item.label }}</div>
                <div class="field-value">
                  <!-- 附件/图片字段 -->
                  <template v-if="item.fieldType === 'upload' || item.fieldType === 'image'">
                    <template v-if="item.attachments && item.attachments.length > 0">
                      <div class="attachment-list">
                        <div
                          v-for="file in item.attachments"
                          :key="file.id"
                          class="attachment-item"
                        >
                          <template v-if="isImage(file.content_type)">
                            <div class="image-preview">
                              <img
                                :src="file.download_url"
                                :alt="file.file_name"
                                class="preview-image"
                              />
                              <n-a :href="file.download_url" target="_blank">
                                <n-button text type="primary" size="tiny">
                                  下载
                                </n-button>
                              </n-a>
                            </div>
                          </template>
                          <template v-else>
                            <n-a :href="file.download_url" target="_blank">
                              <n-button text type="primary" size="small">
                                {{ file.file_name }}
                              </n-button>
                            </n-a>
                          </template>
                        </div>
                      </div>
                    </template>
                    <span v-else class="empty-value">未上传</span>
                  </template>
                  <!-- 日期范围字段 -->
                  <template v-else-if="item.fieldType === 'date-range'">
                    {{ formatDateRange(item.value) }}
                  </template>
                  <!-- 日期字段 -->
                  <template v-else-if="item.fieldType === 'date'">
                    {{ formatDateTimeValue(item.value) }}
                  </template>
                  <!-- 其他字段 -->
                  <template v-else>
                    {{ formatFieldValue(item.value, item.options) }}
                  </template>
                </div>
              </div>
            </div>
            <n-empty v-else-if="!loadingSubmissionDetail" description="暂无表单数据" />
          </div>
        </div>

        <!-- 流程时间线 -->
        <div class="timeline-section">
          <div class="section-header">
            <h3>审批时间线</h3>
          </div>

          <div class="timeline-container" v-loading="flowLoading">
            <div v-if="processTimeline?.entries?.length" class="timeline">
              <div
                v-for="(entry, index) in processTimeline.entries"
                :key="index"
                class="timeline-item"
                :class="[`status-${entry.status}`, `action-${entry.action}`]"
              >
                <div class="timeline-marker">
                  <div class="marker-dot"></div>
                  <div class="marker-line" v-if="index < processTimeline.entries.length - 1"></div>
                </div>
                <div class="timeline-content">
                  <div class="timeline-header">
                    <div class="node-name">{{ entry.node_name }}</div>
                    <n-tag
                      :type="getTimelineStatusType(entry.status)"
                      size="small"
                      :bordered="false"
                    >
                      {{ getTimelineStatusLabel(entry.status) }}
                    </n-tag>
                  </div>
                  <div class="timeline-meta">
                    <div class="meta-item">
                      <span class="meta-label">处理人：</span>
                      <span>{{ entry.actor_name || '待处理' }}</span>
                    </div>
                    <div class="meta-item">
                      <span class="meta-label">开始时间：</span>
                      <span>{{ formatDateTime(entry.started_at) }}</span>
                    </div>
                    <div class="meta-item" v-if="entry.completed_at">
                      <span class="meta-label">完成时间：</span>
                      <span>{{ formatDateTime(entry.completed_at) }}</span>
                    </div>
                    <div class="meta-item" v-if="entry.due_at">
                      <span class="meta-label">截止时间：</span>
                      <span :class="{ overdue: entry.remaining_sla_minutes && entry.remaining_sla_minutes <= 0 }">
                        {{ formatDateTime(entry.due_at) }}
                      </span>
                    </div>
                    <div class="meta-item" v-if="entry.sla_level && entry.sla_level !== 'unknown'">
                      <span class="meta-label">SLA级别：</span>
                      <n-tag :type="getSLALevelType(entry.sla_level)" size="small" :bordered="false">
                        {{ getSLALevelLabel(entry.sla_level) }}
                      </n-tag>
                    </div>
                  </div>
                  <div class="timeline-comment" v-if="entry.comment">
                    <div class="comment-label">审批意见：</div>
                    <div class="comment-content">{{ entry.comment }}</div>
                  </div>
                </div>
              </div>
            </div>
            <n-empty v-else description="暂无审批时间线" />
          </div>
        </div>

        <!-- 操作区域 -->
        <div class="action-section" v-if="canEditSubmission || isPendingApproval">
          <div class="section-header">
            <h3>操作</h3>
          </div>
          <div class="action-buttons">
            <!-- 暂存待发状态：显示发起审批按钮 -->
            <n-button v-if="isPendingApproval" type="primary" @click="handleStartApproval" :loading="startApprovalLoading">
              <template #icon>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                  <path d="M22 2L11 13"></path>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              </template>
              发起审批
            </n-button>
            <n-button type="primary" @click="editSubmission">
              <template #icon>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
              </template>
              编辑表单
            </n-button>
            <n-button @click="viewSubmissionDetail">
              <template #icon>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                </svg>
              </template>
              查看详情
            </n-button>
          </div>
        </div>
      </main>

      <!-- 未选择审批时的占位 -->
      <main class="approval-detail-main empty-state" v-else>
        <div class="empty-content">
          <div class="empty-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>
          </div>
          <h3>选择审批记录</h3>
          <p>从左侧列表中选择一个审批记录查看详情</p>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMySubmittedApprovals } from '@/stores/mySubmittedApprovals'
import type { MyApprovalItem } from '@/stores/mySubmittedApprovals'
import FlowDiagram from '@/components/form/FlowDiagram.vue'
import { startApproval, getSubmissionDetail } from '@/api/submission'
import { useMessage, NA } from 'naive-ui'
import type { SubmissionDetail } from '@/types/submission'
import type { AttachmentInfo } from '@/types/attachment'

const router = useRouter()
const authStore = useAuthStore()
const approvalStore = useMySubmittedApprovals()
const message = useMessage()

// 响应式数据
const searchKeyword = ref('')
const selectedApproval = ref<MyApprovalItem | null>(null)
const startApprovalLoading = ref(false)

// 提交详情数据（用于表单数据展示）
const submissionDetail = ref<SubmissionDetail | null>(null)
const loadingSubmissionDetail = ref(false)

// 计算属性
const loading = computed(() => approvalStore.loading)
const flowLoading = computed(() => approvalStore.flowLoading)
const flowNodes = computed(() => approvalStore.flowNodes)
const flowRoutes = computed(() => approvalStore.flowRoutes)
const fieldLabels = computed(() => approvalStore.fieldLabels)
const processTimeline = computed(() => approvalStore.processTimeline)

// 过滤后的审批列表
const filteredApprovals = computed(() => {
  if (!searchKeyword.value) return approvalStore.approvalList
  const keyword = searchKeyword.value.toLowerCase()
  return approvalStore.approvalList.filter(item =>
    item.form_name.toLowerCase().includes(keyword)
  )
})

// 是否可以编辑提交（暂存待发状态）
const canEditSubmission = computed(() => {
  if (!selectedApproval.value) return false
  // 暂存待发状态可以编辑
  return selectedApproval.value.process_state === 'pending_approval'
})

// 是否是暂存待发状态
const isPendingApproval = computed(() => {
  if (!selectedApproval.value) return false
  return selectedApproval.value.process_state === 'pending_approval'
})

// 方法
const goHome = () => {
  router.push('/')
}

const refreshApprovals = async () => {
  await approvalStore.loadMyApprovals()
}

const selectApproval = async (approval: MyApprovalItem) => {
  selectedApproval.value = approval
  await approvalStore.selectApproval(approval)
}

const refreshFlowData = async () => {
  if (selectedApproval.value) {
    await approvalStore.loadFlowDiagram(
      selectedApproval.value.form_id,
      selectedApproval.value.process_instance_id,
      selectedApproval.value.flow_definition_id
    )
  }
}

const handleSearch = () => {
  // 搜索逻辑已在计算属性中实现
}

const editSubmission = () => {
  if (selectedApproval.value) {
    // 跳转到表单编辑页面
    router.push(`/form/${selectedApproval.value.form_id}/fill?submission=${selectedApproval.value.id}`)
  }
}

const viewSubmissionDetail = () => {
  if (selectedApproval.value) {
    router.push(`/submissions/${selectedApproval.value.id}`)
  }
}

// 发起审批
const handleStartApproval = async () => {
  if (!selectedApproval.value) return
  
  startApprovalLoading.value = true
  try {
    await startApproval(selectedApproval.value.id)
    message.success('审批流程已发起')
    // 刷新列表
    await approvalStore.loadMyApprovals()
    // 更新选中项的状态
    selectedApproval.value.process_state = 'running'
  } catch (error: any) {
    message.error(error?.message || '发起审批失败')
  } finally {
    startApprovalLoading.value = false
  }
}

const getStateType = (state: string | null, isOverdue?: boolean): 'success' | 'warning' | 'error' | 'info' => {
  return approvalStore.getStateType(state, isOverdue)
}

const getStateLabel = (state: string | null, isOverdue?: boolean): string => {
  return approvalStore.getStateLabel(state, isOverdue)
}

const getTimelineStatusType = (status: string | null | undefined): 'success' | 'warning' | 'error' | 'info' => {
  switch (status) {
    case 'completed': return 'success'
    case 'claimed':
    case 'open': return 'warning'
    case 'canceled': return 'error'
    case 'rejected': return 'error'
    default: return 'info'
  }
}

const getTimelineStatusLabel = (status: string | null | undefined): string => {
  switch (status) {
    case 'completed': return '已完成'
    case 'approved': return '已通过'
    case 'claimed': return '已认领'
    case 'open': return '待处理'
    case 'canceled': return '已取消'
    case 'rejected': return '已拒绝'
    default: return status || '未知'
  }
}

const getSLALevelType = (level: string | null | undefined): 'success' | 'warning' | 'error' | 'info' => {
  switch (level) {
    case 'normal': return 'success'
    case 'warning': return 'warning'
    case 'critical': return 'error'
    default: return 'info'
  }
}

const getSLALevelLabel = (level: string | null | undefined): string => {
  switch (level) {
    case 'normal': return '正常'
    case 'warning': return '警告'
    case 'critical': return '紧急'
    case 'unknown': return '未知'
    default: return level || '未知'
  }
}

const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const formatDateTime = (dateString: string | null | undefined): string => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 加载提交详情（用于表单数据展示）
const loadSubmissionDetail = async (submissionId: number) => {
  loadingSubmissionDetail.value = true
  try {
    const res = await getSubmissionDetail(submissionId)
    if (res.code === 200 && res.data) {
      submissionDetail.value = res.data
    } else {
      submissionDetail.value = null
      message.warning('未找到提交详情')
    }
  } catch (error) {
    console.error('加载提交详情失败:', error)
    submissionDetail.value = null
    message.error('加载表单数据失败，请稍后重试')
  } finally {
    loadingSubmissionDetail.value = false
  }
}

// 表单字段展示数据
interface DisplayField {
  key: string
  label: string
  value: unknown
  fieldType?: string
  options?: Array<{ label: string; value: unknown }>
  attachments?: AttachmentInfo[]
}

const attachmentMap = computed(() => {
  const map = new Map<number, AttachmentInfo>()
  const attachments = submissionDetail.value?.attachments ?? []
  attachments.forEach((item) => {
    map.set(item.id, item)
  })
  return map
})

const displayFields = computed<DisplayField[]>(() => {
  if (!submissionDetail.value) return []
  const snapshot = submissionDetail.value.snapshot_json || {}
  const labels = snapshot.field_labels || {}
  const types = snapshot.field_types || {}
  const options = snapshot.field_options || {}
  const raw = submissionDetail.value.data_jsonb || {}

  return Object.entries(raw).map(([key, value]) => {
    const fieldType = types[key]
    const fieldOptions = options[key]
    const attachmentValue = resolveAttachmentValue(value, fieldType)

    return {
      key,
      label: labels[key] || key,
      value,
      fieldType,
      options: fieldOptions,
      attachments: attachmentValue || undefined,
    }
  })
})

const resolveAttachmentValue = (value: unknown, fieldType?: string): AttachmentInfo[] | null => {
  if (!fieldType || !['upload', 'image'].includes(fieldType)) {
    return null
  }
  if (!Array.isArray(value)) {
    return null
  }
  const files = value
    .map((id) => (typeof id === 'number' ? attachmentMap.value.get(id) : null))
    .filter((item): item is AttachmentInfo => Boolean(item))
  return files.length ? files : null
}

const formatFieldValue = (value: unknown, options?: Array<{ label: string; value: unknown }>): string => {
  if (value == null) return '-'
  if (options && options.length > 0) {
    if (Array.isArray(value)) {
      const labels = value.map(v => {
        const option = options.find(opt => opt.value === v)
        return option?.label || String(v)
      })
      return labels.join('、')
    } else {
      const option = options.find(opt => opt.value === value)
      return option?.label || String(value)
    }
  }
  if (Array.isArray(value)) {
    return value.map((item) => String(item)).join('、')
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

const formatDateRange = (value: unknown): string => {
  if (!value) return '-'
  if (Array.isArray(value) && value.length === 2) {
    const [start, end] = value
    return `${formatDateOnly(start)} - ${formatDateOnly(end)}`
  }
  if (typeof value === 'object' && value !== null) {
    const obj = value as Record<string, unknown>
    if ('start' in obj && 'end' in obj) {
      return `${formatDateOnly(obj.start)} - ${formatDateOnly(obj.end)}`
    }
  }
  return String(value)
}

const formatDateOnly = (value: unknown): string => {
  if (!value) return '-'
  let date: Date
  if (typeof value === 'number') {
    date = new Date(value)
  } else if (typeof value === 'string') {
    date = new Date(value)
  } else {
    return String(value)
  }
  if (isNaN(date.getTime())) {
    return String(value)
  }
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const formatDateTimeValue = (value: unknown): string => {
  if (!value) return '-'
  if (typeof value === 'number') {
    const date = new Date(value)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }
  if (typeof value === 'string') {
    const date = new Date(value)
    if (!isNaN(date.getTime())) {
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    }
  }
  return String(value)
}

const isImage = (contentType?: string): boolean => {
  if (!contentType) return false
  return contentType.startsWith('image/')
}

// 监听选择变化
watch(selectedApproval, (newVal) => {
  if (newVal) {
    refreshFlowData()
    // 加载提交详情用于表单数据展示
    loadSubmissionDetail(newVal.id)
  } else {
    submissionDetail.value = null
  }
})

// 初始化
onMounted(async () => {
  if (authStore.isLoggedIn) {
    await approvalStore.loadMyApprovals()
  }
})
</script>

<style scoped>
.my-approvals-page {
  min-height: 100vh;
  background: #f8fafc;
}

/* 页面头部 */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 32px 0;
  color: #ffffff;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-icon {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-text {
  flex: 1;
}

.header-text h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
}

.header-text .subtitle {
  margin: 4px 0 0;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.home-btn {
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.3);
}

.home-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

/* 主要内容区域 */
.main-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 24px;
  min-height: calc(100vh - 140px);
}

/* 左侧审批列表 */
.approval-list-sidebar {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a202c;
}

.search-box {
  padding: 16px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.approval-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.approval-item {
  padding: 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 8px;
  border: 1px solid transparent;
}

.approval-item:hover {
  background: #f8fafc;
  border-color: #e2e8f0;
}

.approval-item.active {
  background: #f0f5ff;
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.approval-item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.approval-title {
  font-weight: 600;
  color: #1a202c;
  font-size: 15px;
  line-height: 1.4;
  flex: 1;
  margin-right: 12px;
}

.approval-item-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #64748b;
}

.meta-item svg {
  flex-shrink: 0;
}

.meta-item .overdue {
  color: #ef4444;
  font-weight: 500;
}

/* 右侧审批详情 */
.approval-detail-main {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-content {
  text-align: center;
  color: #64748b;
}

.empty-icon {
  width: 80px;
  height: 80px;
  background: #f1f5f9;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  color: #94a3b8;
}

.empty-content h3 {
  margin: 0 0 8px;
  font-size: 18px;
  color: #1a202c;
}

.empty-content p {
  margin: 0;
  font-size: 14px;
}

/* 详情头部 */
.detail-header {
  padding: 24px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.detail-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.detail-title h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #1a202c;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}

.detail-meta .meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #64748b;
}

.meta-label {
  color: #94a3b8;
}

.detail-meta .overdue {
  color: #ef4444;
  font-weight: 500;
}

/* 各个部分 */
.flow-diagram-section,
.form-data-section,
.timeline-section,
.action-section {
  padding: 24px;
  border-bottom: 1px solid #e2e8f0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a202c;
}

/* 流程图 */
.flow-diagram-container {
  min-height: 300px;
  background: #f8fafc;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e2e8f0;
}

.flow-diagram-wrapper {
  min-height: 300px;
  border-radius: 12px;
  overflow: hidden;
}

/* 时间线 */
.timeline-container {
  min-height: 200px;
}

.timeline {
  position: relative;
}

.timeline-item {
  display: flex;
  gap: 16px;
  padding-bottom: 24px;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-marker {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.marker-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #e2e8f0;
  border: 3px solid #ffffff;
  box-shadow: 0 0 0 2px #e2e8f0;
  z-index: 1;
}

.timeline-item.status-completed .marker-dot {
  background: #10b981;
  box-shadow: 0 0 0 2px #10b981;
}

.timeline-item.status-claimed .marker-dot,
.timeline-item.status-open .marker-dot {
  background: #f59e0b;
  box-shadow: 0 0 0 2px #f59e0b;
}

.timeline-item.status-rejected .marker-dot {
  background: #ef4444;
  box-shadow: 0 0 0 2px #ef4444;
}

.marker-line {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: calc(100% + 8px);
  background: #e2e8f0;
}

.timeline-content {
  flex: 1;
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.timeline-header .node-name {
  font-weight: 600;
  font-size: 15px;
  color: #1a202c;
}

.timeline-meta {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.timeline-meta .meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #64748b;
}

.timeline-comment {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.comment-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 4px;
}

.comment-content {
  font-size: 14px;
  color: #1a202c;
  line-height: 1.5;
}

/* 表单数据展示 */
.form-data-container {
  min-height: 150px;
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.form-fields {
  display: flex;
  flex-direction: column;
}

.form-field-item {
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  transition: background-color 0.2s;
}

.form-field-item:last-child {
  border-bottom: none;
}

.form-field-item:hover {
  background-color: #f1f5f9;
}

.form-field-item.field-alt {
  background-color: #fafbfc;
}

.form-field-item .field-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

.form-field-item .field-value {
  font-size: 14px;
  color: #1a202c;
  word-break: break-word;
}

.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-item {
  padding: 8px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.image-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.preview-image {
  max-width: 200px;
  max-height: 150px;
  border-radius: 6px;
  object-fit: cover;
}

.empty-value {
  color: #94a3b8;
  font-style: italic;
}

/* 操作区域 */
.action-buttons {
  display: flex;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .main-container {
    grid-template-columns: 1fr;
  }

  .approval-list-sidebar {
    max-height: 400px;
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }

  .detail-meta {
    flex-direction: column;
    gap: 8px;
  }

  .timeline-meta {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    flex-direction: column;
  }
}
</style>