<!-- src/components/home/MySubmittedApprovals.vue - 用户发起的审批进度展示 -->
<template>
  <div class="my-approvals">
    <!-- 1. 顶部统计概览 - 玻璃拟态卡片 -->
    <div class="stats-section">
      <div class="stats-grid">
        <div class="stat-card" :class="{ 'has-data': stats.total > 0 }">
          <div class="stat-icon total">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.total }}</span>
            <span class="stat-label">发起总数</span>
          </div>
          <div class="stat-glow total"></div>
        </div>

        <div class="stat-card warning" :class="{ 'has-data': stats.running > 0 }">
          <div class="stat-icon warning">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.running }}</span>
            <span class="stat-label">审批中</span>
          </div>
          <div class="stat-glow warning"></div>
          <div v-if="stats.running > 0" class="stat-badge">进行中</div>
        </div>

        <div class="stat-card success" :class="{ 'has-data': stats.finished > 0 }">
          <div class="stat-icon success">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.finished }}</span>
            <span class="stat-label">已完成</span>
          </div>
          <div class="stat-glow success"></div>
        </div>

        <div class="stat-card error" :class="{ 'has-data': stats.canceled > 0 }">
          <div class="stat-icon error">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.canceled }}</span>
            <span class="stat-label">已取消</span>
          </div>
          <div class="stat-glow error"></div>
        </div>
      </div>
    </div>

    <!-- 主工作区：左右两栏布局 -->
    <div class="workspace">
      <!-- 左侧：审批列表 -->
      <div class="left-panel">
        <div class="panel-card">
          <div class="panel-header">
            <div class="panel-title">
              <span class="title-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </span>
              <h3>我发起的审批</h3>
            </div>
            <n-button size="small" quaternary circle @click="loadApprovals" class="refresh-btn">
              <template #icon>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="refresh-icon">
                  <polyline points="23 4 23 10 17 10"/>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                </svg>
              </template>
            </n-button>
          </div>

          <div class="panel-content">
            <n-spin :show="loading">
              <div v-if="!approvalList.length" class="empty-state">
                <div class="empty-illustration">
                  <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                    <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                  </svg>
                </div>
                <h4>暂无审批记录</h4>
                <p>您还没有发起过审批流程</p>
                <n-button type="primary" size="small" class="empty-action" @click="goToCreate">
                  发起新审批
                </n-button>
              </div>

              <div v-else class="approval-list">
                <div
                  v-for="approval in approvalList"
                  :key="approval.id"
                  class="approval-item"
                  :class="{ active: selectedApproval?.id === approval.id }"
                  @click="selectApproval(approval)"
                >
                  <div class="approval-status-bar" :class="getStateType(approval.process_state, approval.is_overdue)"></div>
                  <div class="approval-content">
                    <div class="approval-header">
                      <n-tag
                        :type="getStateType(approval.process_state, approval.is_overdue)"
                        size="small"
                        :bordered="false"
                        round
                        class="status-tag"
                      >
                        {{ getStateLabel(approval.process_state, approval.is_overdue) }}
                      </n-tag>
                      <span class="approval-time">{{ formatTime(approval.created_at) }}</span>
                    </div>
                    <h4 class="approval-title">{{ approval.form_name || '未知表单' }}</h4>
                    <div class="approval-meta">
                      <span class="approval-id">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <rect x="3" y="3" width="18" height="18" rx="2"/>
                          <path d="M9 3v18"/>
                        </svg>
                        {{ String(approval.id).slice(-8) }}
                      </span>
                    </div>
                  </div>
                  <div class="approval-arrow">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="9 18 15 12 9 6"/>
                    </svg>
                  </div>
                </div>
              </div>
            </n-spin>
          </div>
        </div>
      </div>

      <!-- 右侧：详情展示 -->
      <div class="right-panel">
        <div class="detail-card">
          <template v-if="selectedApproval">
            <div class="detail-content">
              <!-- 详情头部 -->
              <div class="detail-header">
                <div class="header-main">
                  <h2>{{ selectedApproval.form_name || '审批详情' }}</h2>
                  <n-tag
                    :type="getStateType(selectedApproval.process_state, selectedApproval.is_overdue)"
                    size="medium"
                    :bordered="false"
                    round
                    class="detail-status-tag"
                  >
                    {{ getStateLabel(selectedApproval.process_state, selectedApproval.is_overdue) }}
                  </n-tag>
                </div>
                <div class="header-meta">
                  <span class="header-subtitle">
                    提交编号: <span class="highlight">{{ selectedApproval.id }}</span>
                  </span>
                  <!-- SLA 截止时间 -->
                  <div v-if="slaRemainingText" class="sla-info" :class="slaStatusType">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"/>
                      <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    <span>{{ slaRemainingText }}</span>
                  </div>
                </div>
              </div>

              <!-- 认领状态提示 -->
              <div v-if="currentTaskClaimStatus" class="claim-status-card" :class="{ claimed: currentTaskClaimStatus.is_claimed }">
                <div class="claim-icon">
                  <svg v-if="currentTaskClaimStatus.is_claimed" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
                    <polyline points="22 4 12 14.01 9 11.01"/>
                  </svg>
                  <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12 6 12 12 16 14"/>
                  </svg>
                </div>
                <div class="claim-info">
                  <span class="claim-title">
                    {{ currentTaskClaimStatus.is_claimed ? '任务已认领' : '等待认领' }}
                  </span>
                  <span class="claim-desc">
                    节点: {{ currentTaskClaimStatus.node_name }}
                    <template v-if="currentTaskClaimStatus.assignee_name">
                      | 处理人: {{ currentTaskClaimStatus.assignee_name }}
                    </template>
                  </span>
                </div>
                <n-tag v-if="!currentTaskClaimStatus.is_claimed" type="warning" size="small">待认领</n-tag>
                <n-tag v-else type="success" size="small">已认领</n-tag>
              </div>

              <!-- 流程图 -->
              <div class="flow-diagram-section">
                <h4 class="section-title">审批流程图</h4>
                <n-spin :show="flowLoading">
                  <div v-if="flowNodes.length > 0" class="flow-diagram-container">
                    <FlowDiagram :nodes="flowNodes" :routes="flowRoutes" />
                  </div>
                  <div v-else class="empty-flow">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                      <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/>
                      <polyline points="13 2 13 9 20 9"/>
                    </svg>
                    <p>暂无流程配置</p>
                  </div>
                </n-spin>
              </div>

              <!-- 操作按钮 -->
              <div class="detail-actions">
                <n-button type="primary" size="large" class="action-btn primary" @click="viewDetail">
                  <template #icon>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                  </template>
                  查看详情
                </n-button>
                <n-button size="large" class="action-btn secondary" @click="goToSubmissions">
                  <template #icon>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                    </svg>
                  </template>
                  全部提交
                </n-button>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="empty-detail">
              <div class="empty-illustration large">
                <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                  <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                </svg>
              </div>
              <h3>选择审批查看详情</h3>
              <p>点击左侧列表中的审批记录，查看审批进度和详情</p>
              <div class="empty-hint">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="15 18 9 12 15 6"/>
                </svg>
                <span>从左侧列表选择一项</span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { storeToRefs } from 'pinia'
import { useMySubmittedApprovals } from '@/stores/mySubmittedApprovals'
import FlowDiagram from '@/components/form/FlowDiagram.vue'

const router = useRouter()
const message = useMessage()
const store = useMySubmittedApprovals()

const { approvalList, loading, selectedApproval, stats, flowNodes, flowRoutes, flowLoading } = storeToRefs(store)
const { loadMyApprovals, selectApproval, getStateType, getStateLabel } = store

onMounted(() => {
  loadMyApprovals()
})

const loadApprovals = () => {
  loadMyApprovals()
  message.success('已刷新')
}

const goToSubmissions = () => {
  router.push('/submissions')
}

const goToCreate = () => {
  router.push('/form/fill-center')
}

const viewDetail = () => {
  if (!selectedApproval.value) return
  router.push(`/submissions/${selectedApproval.value.id}`)
}

const formatTime = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))

  if (hours < 1) return '刚刚'
  if (hours < 24) return `${hours}小时前`
  if (hours < 48) return '昨天'
  return date.toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr: string): string => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    submitted: '已提交',
    draft: '草稿',
    approved: '已通过',
    rejected: '已驳回'
  }
  return statusMap[status] || status
}

// 计算SLA剩余时间
const slaRemainingText = computed(() => {
  if (!selectedApproval.value?.due_at) return null
  const dueAt = new Date(selectedApproval.value.due_at)
  const now = new Date()
  const diff = dueAt.getTime() - now.getTime()

  if (diff < 0) {
    const hours = Math.floor(Math.abs(diff) / (1000 * 60 * 60))
    if (hours < 24) return `已超时 ${hours} 小时`
    const days = Math.floor(hours / 24)
    return `已超时 ${days} 天`
  }

  const hours = Math.floor(diff / (1000 * 60 * 60))
  if (hours < 24) return `剩余 ${hours} 小时`
  const days = Math.floor(hours / 24)
  return `剩余 ${days} 天`
})

// SLA状态类型
const slaStatusType = computed(() => {
  if (!selectedApproval.value?.due_at) return 'default'
  if (selectedApproval.value.is_overdue) return 'error'
  const dueAt = new Date(selectedApproval.value.due_at)
  const now = new Date()
  const diff = dueAt.getTime() - now.getTime()
  const hours = diff / (1000 * 60 * 60)

  if (hours < 24) return 'warning'
  return 'success'
})

// 获取当前处理节点的认领状态
const currentTaskClaimStatus = computed(() => {
  const processingNode = flowNodes.value.find(n => n.status === 'processing')
  if (!processingNode) return null

  return {
    node_name: processingNode.name,
    is_claimed: processingNode.is_claimed,
    assignee_name: processingNode.assignee_name
  }
})
</script>

<style scoped>
/* 主容器 */
.my-approvals {
  width: 100%;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

/* ===== 统计卡片区域 ===== */
.stats-section {
  width: 100%;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.stat-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.05),
    0 10px 30px -10px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.08),
    0 20px 40px -15px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  color: #64748b;
  transition: all 0.3s ease;
}

.stat-icon.total {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  color: #3b82f6;
}

.stat-icon.warning {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  color: #f59e0b;
}

.stat-icon.success {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  color: #22c55e;
}

.stat-icon.error {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  color: #ef4444;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.stat-glow {
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.3s ease;
  filter: blur(40px);
}

.stat-glow.total {
  background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%);
}

.stat-glow.warning {
  background: radial-gradient(circle, rgba(245, 158, 11, 0.15) 0%, transparent 70%);
}

.stat-glow.success {
  background: radial-gradient(circle, rgba(34, 197, 94, 0.15) 0%, transparent 70%);
}

.stat-glow.error {
  background: radial-gradient(circle, rgba(239, 68, 68, 0.15) 0%, transparent 70%);
}

.stat-card:hover .stat-glow {
  opacity: 1;
}

.stat-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 3px 8px;
  font-size: 10px;
  font-weight: 600;
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
  border-radius: 999px;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

/* ===== 工作区布局 ===== */
.workspace {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 24px;
  min-height: 600px;
}

/* ===== 左侧面板 ===== */
.left-panel {
  display: flex;
  flex-direction: column;
}

.panel-card {
  background: #ffffff;
  border-radius: 20px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.05),
    0 10px 30px -10px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 580px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid #f1f5f9;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  color: #3b82f6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel-title h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
}

.refresh-btn {
  color: #64748b;
  transition: all 0.2s ease;
}

.refresh-btn:hover {
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.08);
}

.refresh-icon {
  transition: transform 0.3s ease;
}

.refresh-btn:hover .refresh-icon {
  transform: rotate(180deg);
}

.panel-content {
  flex: 1;
  overflow: hidden;
  padding: 16px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.empty-illustration {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #cbd5e1;
  margin-bottom: 20px;
}

.empty-illustration.large {
  width: 120px;
  height: 120px;
  border-radius: 28px;
}

.empty-state h4 {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}

.empty-state p {
  margin: 0 0 20px;
  font-size: 13px;
  color: #64748b;
}

.empty-action {
  border-radius: 10px;
}

/* 审批列表 */
.approval-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  max-height: 480px;
  padding-right: 6px;
}

.approval-item {
  position: relative;
  display: flex;
  align-items: stretch;
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.approval-item:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  transform: translateX(4px);
}

.approval-item.active {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
  box-shadow:
    0 4px 12px rgba(59, 130, 246, 0.12),
    inset 0 0 0 1px rgba(59, 130, 246, 0.1);
}

.approval-status-bar {
  width: 4px;
  flex-shrink: 0;
}

.approval-status-bar.default {
  background: linear-gradient(180deg, #94a3b8 0%, #64748b 100%);
}

.approval-status-bar.warning {
  background: linear-gradient(180deg, #fbbf24 0%, #f59e0b 100%);
}

.approval-status-bar.success {
  background: linear-gradient(180deg, #4ade80 0%, #22c55e 100%);
}

.approval-status-bar.error {
  background: linear-gradient(180deg, #f87171 0%, #ef4444 100%);
}

.approval-content {
  flex: 1;
  padding: 14px 14px 14px 12px;
  min-width: 0;
}

.approval-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.status-tag {
  font-weight: 500;
}

.approval-time {
  font-size: 11px;
  color: #94a3b8;
}

.approval-title {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.approval-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.approval-id {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #94a3b8;
  font-family: 'Monaco', 'Menlo', monospace;
}

.approval-arrow {
  width: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #cbd5e1;
  transition: all 0.2s ease;
}

.approval-item:hover .approval-arrow {
  color: #3b82f6;
}

.approval-item.active .approval-arrow {
  color: #3b82f6;
}

/* ===== 右侧面板 ===== */
.right-panel {
  display: flex;
  flex-direction: column;
}

.detail-card {
  background: #ffffff;
  border-radius: 20px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.05),
    0 10px 30px -10px rgba(0, 0, 0, 0.08);
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 580px;
}

.detail-content {
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
}

.detail-header {
  padding-bottom: 20px;
  border-bottom: 1px solid #f1f5f9;
}

.header-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 8px;
}

.header-main h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.3;
  flex: 1;
}

.detail-status-tag {
  font-weight: 600;
  font-size: 13px;
  padding: 6px 14px;
}

/* Header 元信息 */
.header-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.header-subtitle {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

.header-subtitle .highlight {
  font-family: 'Monaco', 'Menlo', monospace;
  color: #0f172a;
  font-weight: 500;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 6px;
  margin-left: 4px;
}

/* SLA 信息 */
.sla-info {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
}

.sla-info.success {
  background: #dcfce7;
  color: #16a34a;
}

.sla-info.warning {
  background: #fef3c7;
  color: #d97706;
}

.sla-info.error {
  background: #fee2e2;
  color: #dc2626;
  animation: pulse-warning 2s ease-in-out infinite;
}

@keyframes pulse-warning {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* 认领状态卡片 */
.claim-status-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.claim-status-card.claimed {
  background: #dcfce7;
  border-color: #86efac;
}

.claim-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(251, 191, 36, 0.2);
  color: #d97706;
}

.claim-status-card.claimed .claim-icon {
  background: rgba(34, 197, 94, 0.2);
  color: #16a34a;
}

.claim-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.claim-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.claim-desc {
  font-size: 12px;
  color: #64748b;
}

/* 流程图区域 */
.flow-diagram-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.section-title {
  margin: 0 0 12px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.flow-diagram-container {
  flex: 1;
  min-height: 400px;
  border-radius: 16px;
  overflow: hidden;
}

.empty-flow {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: #94a3b8;
  background: #f8fafc;
  border-radius: 16px;
  border: 1px dashed #e2e8f0;
}

.empty-flow p {
  margin: 12px 0 0;
  font-size: 14px;
}

/* 详情网格 */
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 14px;
  border: 1px solid #f1f5f9;
  transition: all 0.2s ease;
}

.info-card:hover {
  background: #f1f5f9;
  border-color: #e2e8f0;
}

.info-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.info-value.warning {
  color: #f59e0b;
}

.info-value.success {
  color: #22c55e;
}

.info-value.error {
  color: #ef4444;
}

.info-value.instance-id {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
}

/* 操作按钮 */
.detail-actions {
  display: flex;
  gap: 12px;
  margin-top: auto;
  padding-top: 8px;
}

.action-btn {
  flex: 1;
  border-radius: 12px;
  font-weight: 600;
}

.action-btn.primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35);
}

.action-btn.primary:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.45);
  transform: translateY(-1px);
}

.action-btn.secondary {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #475569;
}

.action-btn.secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

/* 空详情状态 */
.empty-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  text-align: center;
}

.empty-detail h3 {
  margin: 20px 0 8px;
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

.empty-detail p {
  margin: 0 0 24px;
  font-size: 14px;
  color: #64748b;
}

.empty-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #f1f5f9;
  border-radius: 10px;
  font-size: 13px;
  color: #64748b;
  animation: slide-hint 2s ease-in-out infinite;
}

@keyframes slide-hint {
  0%, 100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(-4px);
  }
}

/* ===== 宽屏优化 ===== */
@media (min-width: 1400px) {
  .workspace {
    grid-template-columns: 420px 1fr;
    gap: 32px;
  }

  .stats-grid {
    gap: 20px;
  }

  .stat-card {
    padding: 24px 22px;
  }

  .stat-value {
    font-size: 32px;
  }

  .detail-content {
    padding: 36px;
  }

  .header-main h2 {
    font-size: 26px;
  }
}

@media (min-width: 1600px) {
  .workspace {
    grid-template-columns: 440px 1fr;
    gap: 40px;
  }
}

/* ===== 响应式适配 ===== */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .workspace {
    grid-template-columns: 1fr;
  }

  .left-panel {
    order: 2;
  }

  .right-panel {
    order: 1;
  }

  .detail-content {
    padding: 20px;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .stat-card {
    padding: 16px 14px;
  }

  .stat-value {
    font-size: 24px;
  }

  .detail-actions {
    flex-direction: column;
  }

  .progress-track {
    gap: 4px;
  }

  .step-label {
    font-size: 11px;
  }
}

/* 滚动条美化 */
.approval-list::-webkit-scrollbar {
  width: 4px;
}

.approval-list::-webkit-scrollbar-track {
  background: transparent;
}

.approval-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}

.approval-list::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
