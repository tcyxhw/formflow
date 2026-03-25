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
            <div v-if="flowNodes.length > 0" class="flow-diagram">
              <!-- 这里可以集成流程图组件 -->
              <div class="flow-nodes">
                <div
                  v-for="node in flowNodes"
                  :key="node.id"
                  class="flow-node"
                  :class="[`node-${node.type}`, `status-${node.status}`]"
                >
                  <div class="node-icon">
                    <svg v-if="node.type === 'start'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                      <circle cx="12" cy="12" r="10"></circle>
                      <polygon points="10 8 16 12 10 16 10 8"></polygon>
                    </svg>
                    <svg v-else-if="node.type === 'approval'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                      <line x1="16" y1="13" x2="8" y2="13"></line>
                      <line x1="16" y1="17" x2="8" y2="17"></line>
                    </svg>
                    <svg v-else-if="node.type === 'end'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                      <circle cx="12" cy="12" r="10"></circle>
                      <line x1="15" y1="9" x2="9" y2="15"></line>
                      <line x1="9" y1="9" x2="15" y2="15"></line>
                    </svg>
                  </div>
                  <div class="node-info">
                    <div class="node-name">{{ node.name }}</div>
                    <div class="node-assignee" v-if="node.assignee_name">
                      {{ node.assignee_name }}
                    </div>
                    <div class="node-due" v-if="node.due_at">
                      截止: {{ formatDate(node.due_at) }}
                    </div>
                  </div>
                  <div class="node-status-badge">
                    <span v-if="node.status === 'completed'" class="status-dot completed"></span>
                    <span v-else-if="node.status === 'processing'" class="status-dot processing"></span>
                    <span v-else-if="node.status === 'rejected'" class="status-dot rejected"></span>
                    <span v-else class="status-dot pending"></span>
                  </div>
                </div>
              </div>
            </div>
            <n-empty v-else description="暂无流程图数据" />
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
        <div class="action-section" v-if="canEditSubmission">
          <div class="section-header">
            <h3>操作</h3>
          </div>
          <div class="action-buttons">
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

const router = useRouter()
const authStore = useAuthStore()
const approvalStore = useMySubmittedApprovals()

// 响应式数据
const searchKeyword = ref('')
const selectedApproval = ref<MyApprovalItem | null>(null)

// 计算属性
const loading = computed(() => approvalStore.loading)
const flowLoading = computed(() => approvalStore.flowLoading)
const flowNodes = computed(() => approvalStore.flowNodes)
const processTimeline = computed(() => approvalStore.processTimeline)

// 过滤后的审批列表
const filteredApprovals = computed(() => {
  if (!searchKeyword.value) return approvalStore.approvalList
  const keyword = searchKeyword.value.toLowerCase()
  return approvalStore.approvalList.filter(item =>
    item.form_name.toLowerCase().includes(keyword)
  )
})

// 是否可以编辑提交（未认领且未处理）
const canEditSubmission = computed(() => {
  if (!selectedApproval.value) return false
  // 检查当前是否有待处理的节点
  const currentEntry = processTimeline.value?.entries?.find(
    entry => entry.status === 'open' || entry.status === 'claimed'
  )
  // 如果有待处理节点且当前用户是审批人，可以编辑
  // 这里简化处理，实际应该检查更复杂的逻辑
  return selectedApproval.value.process_state === 'running'
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

const getStateType = (state: string | null, isOverdue?: boolean): 'success' | 'warning' | 'error' | 'info' => {
  return approvalStore.getStateType(state, isOverdue)
}

const getStateLabel = (state: string | null, isOverdue?: boolean): string => {
  return approvalStore.getStateLabel(state, isOverdue)
}

const getTimelineStatusType = (status: string): 'success' | 'warning' | 'error' | 'info' => {
  switch (status) {
    case 'completed': return 'success'
    case 'claimed':
    case 'open': return 'warning'
    case 'rejected': return 'error'
    default: return 'info'
  }
}

const getTimelineStatusLabel = (status: string): string => {
  switch (status) {
    case 'completed': return '已完成'
    case 'claimed': return '已认领'
    case 'open': return '待处理'
    case 'rejected': return '已拒绝'
    default: return '未知'
  }
}

const getSLALevelType = (level: string): 'success' | 'warning' | 'error' | 'info' => {
  switch (level) {
    case 'normal': return 'success'
    case 'warning': return 'warning'
    case 'critical': return 'error'
    default: return 'info'
  }
}

const getSLALevelLabel = (level: string): string => {
  switch (level) {
    case 'normal': return '正常'
    case 'warning': return '警告'
    case 'critical': return '紧急'
    case 'unknown': return '未知'
    default: return level
  }
}

const formatDate = (dateString: string): string => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const formatDateTime = (dateString: string): string => {
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

// 监听选择变化
watch(selectedApproval, (newVal) => {
  if (newVal) {
    refreshFlowData()
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
  min-height: 200px;
  background: #f8fafc;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e2e8f0;
}

.flow-nodes {
  display: flex;
  align-items: center;
  gap: 16px;
  overflow-x: auto;
  padding: 8px 0;
}

.flow-node {
  flex-shrink: 0;
  width: 140px;
  padding: 16px;
  background: #ffffff;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  text-align: center;
  transition: all 0.2s ease;
  position: relative;
}

.flow-node:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.flow-node.node-start {
  border-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
}

.flow-node.node-approval {
  border-color: #667eea;
  background: linear-gradient(135deg, #f0f5ff 0%, #e0e7ff 100%);
}

.flow-node.node-end {
  border-color: #8b5cf6;
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
}

.flow-node.status-completed {
  border-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
}

.flow-node.status-processing {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
}

.flow-node.status-rejected {
  border-color: #ef4444;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
}

.flow-node.status-pending {
  border-color: #e2e8f0;
  background: #ffffff;
}

.node-icon {
  margin-bottom: 8px;
}

.node-name {
  font-weight: 600;
  font-size: 14px;
  color: #1a202c;
  margin-bottom: 4px;
}

.node-assignee {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

.node-due {
  font-size: 11px;
  color: #94a3b8;
}

.node-status-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-dot.completed {
  background: #10b981;
}

.status-dot.processing {
  background: #f59e0b;
  animation: pulse 2s infinite;
}

.status-dot.rejected {
  background: #ef4444;
}

.status-dot.pending {
  background: #e2e8f0;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
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