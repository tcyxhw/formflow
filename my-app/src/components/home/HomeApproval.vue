<!-- src/components/home/HomeApproval.vue - 用户审批进度展示 -->
<template>
  <div class="home-approval command-center">
    <!-- 1. 顶部全局区：统计概览 -->
    <div class="header-global">
      <div class="stats-tabs" role="tablist" aria-label="审批统计">
        <div class="stats-item">
          <span class="stats-value">{{ stats.total }}</span>
          <span class="stats-label">待办总数</span>
        </div>
        <div class="stats-item urgent">
          <span class="stats-value">{{ stats.urgent }}</span>
          <span class="stats-label">紧急处理</span>
        </div>
        <div class="stats-item warning">
          <span class="stats-value">{{ stats.warning }}</span>
          <span class="stats-label">即将超时</span>
        </div>
        <div class="stats-item normal">
          <span class="stats-value">{{ stats.normal }}</span>
          <span class="stats-label">正常处理</span>
        </div>
      </div>
    </div>

    <!-- 主工作区：左右两栏布局 -->
    <div class="playground-workspace">
      <!-- 2. 左侧控制栏 (固定宽度 380px) -->
      <div class="left-panel">
        <!-- 卡片 A：待办任务列表 -->
        <div class="task-card">
          <div class="card-header">
            <h3 class="card-title">待办任务</h3>
            <n-button size="small" quaternary @click="loadTasks">
              <template #icon>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 4 23 10 17 10"></polyline>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                </svg>
              </template>
            </n-button>
          </div>
          <div class="card-content">
            <n-spin :show="loading">
              <div v-if="!pendingTasks.length" class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <p>暂无待办任务</p>
                <span>太棒了，所有审批都已处理完毕！</span>
              </div>
              <div v-else class="task-list">
                <div
                  v-for="task in pendingTasks"
                  :key="task.id"
                  class="task-item"
                  :class="{ active: selectedTask?.id === task.id }"
                  @click="selectTask(task)"
                >
                  <div class="task-header">
                    <n-tag
                      :type="getStatusType(task.sla_level)"
                      size="small"
                      :bordered="false"
                      round
                    >
                      {{ getStatusLabel(task.sla_level) }}
                    </n-tag>
                    <span class="task-time">{{ formatTime(task.created_at) }}</span>
                  </div>
                  <div class="task-body">
                    <h4 class="task-title">{{ task.flow_name || '未知流程' }}</h4>
                    <p class="task-node">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                      </svg>
                      {{ task.node_name || '当前节点' }}
                    </p>
                  </div>
                  <div class="task-footer">
                    <span v-if="task.remaining_sla_minutes !== null" class="sla-info">
                      剩余 {{ Math.ceil(task.remaining_sla_minutes / 60) }} 小时
                    </span>
                    <span v-else class="sla-info">无 SLA 要求</span>
                  </div>
                </div>
              </div>
            </n-spin>
          </div>
        </div>

        <!-- 卡片 B：SLA 预警信息 -->
        <div class="sla-card">
          <div class="sla-header">
            <span class="sla-label">SLA 状态分布</span>
          </div>
          <div class="sla-chart">
            <div class="sla-bar">
              <div
                v-if="slaSummary?.critical"
                class="sla-segment critical"
                :style="{ width: getSlaPercent('critical') + '%' }"
                :title="'紧急: ' + slaSummary.critical"
              ></div>
              <div
                v-if="slaSummary?.warning"
                class="sla-segment warning"
                :style="{ width: getSlaPercent('warning') + '%' }"
                :title="'预警: ' + slaSummary.warning"
              ></div>
              <div
                v-if="slaSummary?.normal"
                class="sla-segment normal"
                :style="{ width: getSlaPercent('normal') + '%' }"
                :title="'正常: ' + slaSummary.normal"
              ></div>
              <div
                v-if="slaSummary?.unknown"
                class="sla-segment unknown"
                :style="{ width: getSlaPercent('unknown') + '%' }"
                :title="'未知: ' + slaSummary.unknown"
              ></div>
            </div>
            <div class="sla-legend">
              <div class="legend-item">
                <span class="legend-dot critical"></span>
                <span>紧急 {{ slaSummary?.critical || 0 }}</span>
              </div>
              <div class="legend-item">
                <span class="legend-dot warning"></span>
                <span>预警 {{ slaSummary?.warning || 0 }}</span>
              </div>
              <div class="legend-item">
                <span class="legend-dot normal"></span>
                <span>正常 {{ slaSummary?.normal || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. 右侧展示区 (flex: 1) -->
      <div class="right-panel">
        <!-- 任务详情/流程图区域 -->
        <div class="flow-visual">
          <template v-if="selectedTask">
            <div class="task-detail">
              <div class="detail-header">
                <h3>{{ selectedTask.flow_name || '审批任务' }}</h3>
                <n-tag :type="getStatusType(selectedTask.sla_level)" :bordered="false">
                  {{ getStatusLabel(selectedTask.sla_level) }}
                </n-tag>
              </div>
              <div class="detail-info">
                <div class="info-row">
                  <span class="info-label">当前节点</span>
                  <span class="info-value">{{ selectedTask.node_name || '未知' }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">任务状态</span>
                  <span class="info-value">{{ formatStatus(selectedTask.status) }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">创建时间</span>
                  <span class="info-value">{{ formatDateTime(selectedTask.created_at) }}</span>
                </div>
                <div v-if="selectedTask.due_at" class="info-row">
                  <span class="info-label">截止时间</span>
                  <span class="info-value">{{ formatDateTime(selectedTask.due_at) }}</span>
                </div>
                <div v-if="selectedTask.remaining_sla_minutes !== null" class="info-row">
                  <span class="info-label">剩余时间</span>
                  <span class="info-value" :class="{ urgent: selectedTask.is_overdue }">
                    {{ formatRemainingTime(selectedTask.remaining_sla_minutes) }}
                  </span>
                </div>
              </div>
              <div class="detail-actions">
                <n-button type="primary" size="large" @click="handleApprove">
                  审批通过
                </n-button>
                <n-button size="large" @click="handleReject">
                  驳回
                </n-button>
                <n-button size="large" tertiary @click="handleTransfer">
                  转交
                </n-button>
              </div>
            </div>
          </template>
          <template v-else>
            <div class="empty-detail">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
              </svg>
              <h4>选择任务查看详情</h4>
              <p>点击左侧任务列表中的项目，查看审批详情并进行处理</p>
            </div>
          </template>
        </div>

        <!-- 审批历史/时间线 -->
        <div class="stage-timeline">
          <div class="timeline-header">
            <h4>审批历史</h4>
            <n-tag size="small" :bordered="false" type="info">
              {{ selectedTask ? '当前任务' : '暂无' }}
            </n-tag>
          </div>
          <ul class="stage-list">
            <li v-if="!selectedTask" class="stage-empty">
              请先选择一个任务查看审批历史
            </li>
            <template v-else>
              <li class="stage-item completed">
                <span class="stage-index">✓</span>
                <div class="stage-body">
                  <p class="stage-name">提交申请</p>
                  <span class="stage-desc">申请人已提交表单</span>
                </div>
                <span class="stage-time">{{ formatTime(selectedTask.created_at) }}</span>
              </li>
              <li class="stage-item current">
                <span class="stage-index">{{ selectedTask.node_name?.charAt(0) || '?' }}</span>
                <div class="stage-body">
                  <p class="stage-name">{{ selectedTask.node_name || '当前节点' }}</p>
                  <span class="stage-desc">等待审批处理</span>
                </div>
                <n-tag type="warning" size="small" :bordered="false">进行中</n-tag>
              </li>
              <li class="stage-item pending">
                <span class="stage-index">→</span>
                <div class="stage-body">
                  <p class="stage-name">后续节点</p>
                  <span class="stage-desc">流程将继续推进</span>
                </div>
              </li>
            </template>
          </ul>
        </div>
      </div>
    </div>

    <!-- 4. 底部悬浮区：快捷操作 -->
    <div class="cli-float">
      <div class="cli-shell">
        <div class="cli-header">
          <div class="cli-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="4 17 10 11 4 5"></polyline>
              <line x1="12" y1="19" x2="20" y2="19"></line>
            </svg>
            <span>快捷审批</span>
          </div>
          <n-button size="small" quaternary @click="goToApprovals">
            查看全部
          </n-button>
        </div>
        <pre><code>npx formflow approval:batch --status=open</code></pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useHomeApproval } from '@/stores/homeApproval'
import type { TaskResponse } from '@/types/approval'

const router = useRouter()
const message = useMessage()
const store = useHomeApproval()

const { pendingTasks, slaSummary, loading, selectedTask, stats } = store
const { loadPendingTasks, selectTask, getStatusType, getStatusLabel } = store

onMounted(() => {
  loadPendingTasks()
})

const loadTasks = () => {
  loadPendingTasks()
  message.success('已刷新')
}

const goToApprovals = () => {
  router.push('/approvals')
}

const handleApprove = () => {
  if (!selectedTask.value) return
  message.success('审批通过')
  loadPendingTasks()
}

const handleReject = () => {
  if (!selectedTask.value) return
  message.warning('已驳回')
  loadPendingTasks()
}

const handleTransfer = () => {
  if (!selectedTask.value) return
  message.info('转交功能开发中')
}

const getSlaPercent = (level: string): number => {
  if (!slaSummary.value) return 0
  const total = (slaSummary.value.critical || 0) + 
                (slaSummary.value.warning || 0) + 
                (slaSummary.value.normal || 0) + 
                (slaSummary.value.unknown || 0)
  if (total === 0) return 0
  const value = slaSummary.value[level as keyof TaskSlaSummary] as number || 0
  return Math.round((value / total) * 100)
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

const formatRemainingTime = (minutes: number): string => {
  if (minutes <= 0) return '已超时'
  const hours = Math.floor(minutes / 60)
  if (hours < 1) return `${minutes}分钟`
  if (hours < 24) return `${hours}小时`
  return `${Math.floor(hours / 24)}天${hours % 24}小时`
}

const formatStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    open: '待处理',
    claimed: '已认领',
    completed: '已完成',
    canceled: '已取消'
  }
  return statusMap[status] || status
}
</script>

<style scoped>
/* 全局容器 - 控制台模式 */
.home-approval {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: clamp(24px, 3vw, 32px);
  background: #F7F8FA;
  border-radius: 16px;
}

/* 1. 顶部全局区：统计概览 */
.header-global {
  width: 100%;
}

.stats-tabs {
  display: flex;
  gap: 16px;
  padding: 20px 24px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(12, 16, 32, 0.06);
}

.stats-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px;
  border-radius: 10px;
  background: rgba(15, 18, 23, 0.02);
  transition: all 0.2s ease;
}

.stats-item:hover {
  background: rgba(15, 18, 23, 0.04);
}

.stats-item.urgent {
  background: rgba(245, 63, 63, 0.08);
}

.stats-item.warning {
  background: rgba(240, 185, 11, 0.08);
}

.stats-item.normal {
  background: rgba(24, 160, 88, 0.08);
}

.stats-value {
  font-size: 28px;
  font-weight: 700;
  color: #1d2129;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.stats-item.urgent .stats-value {
  color: #F53F3F;
}

.stats-item.warning .stats-value {
  color: #F0B90B;
}

.stats-item.normal .stats-value {
  color: #18A058;
}

.stats-label {
  font-size: 12px;
  color: #86909c;
}

/* 主工作区：左右两栏布局 */
.playground-workspace {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 20px;
  min-height: 600px;
}

/* 2. 左侧控制栏 */
.left-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 待办任务卡片 */
.task-card {
  border-radius: 16px;
  border: 1px solid rgba(12, 16, 32, 0.08);
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  padding: 24px;
  flex-shrink: 0;
  max-height: 500px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.card-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  letter-spacing: -0.01em;
}

.card-content {
  flex: 1;
  overflow: hidden;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  color: #86909c;
}

.empty-state svg {
  margin-bottom: 16px;
  opacity: 0.4;
}

.empty-state p {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
}

.empty-state span {
  font-size: 12px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  max-height: 400px;
  padding-right: 8px;
}

.task-item {
  padding: 16px;
  border-radius: 12px;
  background: rgba(15, 18, 23, 0.02);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.task-item:hover {
  background: rgba(15, 18, 23, 0.04);
  border-color: rgba(12, 16, 32, 0.08);
}

.task-item.active {
  background: rgba(64, 133, 245, 0.08);
  border-color: rgba(64, 133, 245, 0.2);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.task-time {
  font-size: 11px;
  color: #86909c;
}

.task-body {
  margin-bottom: 8px;
}

.task-title {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  line-height: 1.4;
}

.task-node {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #86909c;
}

.task-footer {
  display: flex;
  justify-content: flex-end;
}

.sla-info {
  font-size: 11px;
  color: #86909c;
  padding: 2px 8px;
  background: rgba(15, 18, 23, 0.04);
  border-radius: 4px;
}

/* SLA 卡片 */
.sla-card {
  border-radius: 16px;
  border: 1px solid rgba(12, 16, 32, 0.08);
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  padding: 24px;
  flex-shrink: 0;
}

.sla-header {
  margin-bottom: 16px;
}

.sla-label {
  font-size: 11px;
  font-weight: 500;
  color: #86909c;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}

.sla-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sla-bar {
  display: flex;
  height: 12px;
  border-radius: 999px;
  background: #F2F3F5;
  overflow: hidden;
}

.sla-segment {
  height: 100%;
  transition: width 0.3s ease;
}

.sla-segment.critical {
  background: linear-gradient(90deg, #F53F3F 0%, #F7786E 100%);
}

.sla-segment.warning {
  background: linear-gradient(90deg, #F0B90B 0%, #F5C358 100%);
}

.sla-segment.normal {
  background: linear-gradient(90deg, #18A058 0%, #3AC885 100%);
}

.sla-segment.unknown {
  background: #E5E6EB;
}

.sla-legend {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #4E5969;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot.critical {
  background: #F53F3F;
}

.legend-dot.warning {
  background: #F0B90B;
}

.legend-dot.normal {
  background: #18A058;
}

/* 3. 右侧展示区 */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 流程图区域 */
.flow-visual {
  flex: 1;
  min-height: 400px;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(12, 16, 32, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  position: relative;
}

.task-detail {
  width: 100%;
  max-width: 500px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.detail-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1d2129;
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 32px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(15, 18, 23, 0.02);
  border-radius: 8px;
}

.info-label {
  font-size: 13px;
  color: #86909c;
}

.info-value {
  font-size: 14px;
  font-weight: 500;
  color: #1d2129;
}

.info-value.urgent {
  color: #F53F3F;
}

.detail-actions {
  display: flex;
  gap: 12px;
}

.detail-actions :deep(.n-button) {
  flex: 1;
}

.empty-detail {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #86909c;
}

.empty-detail svg {
  margin-bottom: 20px;
  opacity: 0.3;
}

.empty-detail h4 {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}

.empty-detail p {
  margin: 0;
  font-size: 13px;
  max-width: 280px;
}

/* 审批历史时间线 */
.stage-timeline {
  border-radius: 12px;
  border: 1px solid rgba(12, 16, 32, 0.08);
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  padding: 20px;
  flex-shrink: 0;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.timeline-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  letter-spacing: -0.01em;
}

.stage-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stage-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: rgba(15, 18, 23, 0.02);
  transition: all 0.2s ease;
}

.stage-item:hover {
  background: rgba(15, 18, 23, 0.04);
}

.stage-item.completed {
  background: rgba(24, 160, 88, 0.05);
}

.stage-item.current {
  background: rgba(240, 185, 11, 0.05);
  border: 1px solid rgba(240, 185, 11, 0.2);
}

.stage-item.pending {
  opacity: 0.6;
}

.stage-index {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(15, 18, 23, 0.08);
  font-size: 12px;
  font-weight: 600;
  color: #1d2129;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stage-item.completed .stage-index {
  background: #18A058;
  color: #fff;
}

.stage-item.current .stage-index {
  background: #F0B90B;
  color: #fff;
}

.stage-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stage-name {
  margin: 0;
  font-weight: 600;
  color: #1d2129;
  font-size: 13px;
}

.stage-desc {
  font-size: 11px;
  color: #86909c;
}

.stage-time {
  font-size: 11px;
  color: #86909c;
}

.stage-empty {
  text-align: center;
  color: #86909c;
  font-size: 12px;
  padding: 20px 0;
}

/* 4. 底部悬浮区：快捷操作 */
.cli-float {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 100;
}

.cli-shell {
  background: #1E1E1E;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  backdrop-filter: blur(12px);
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
  max-width: 400px;
}

.cli-shell:hover {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}

.cli-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.cli-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
}

.cli-label svg {
  opacity: 0.6;
}

.cli-shell pre {
  font-size: 13px;
  padding: 16px;
  margin: 0;
  background: transparent;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.9);
}

/* 响应式适配 */
@media (max-width: 1024px) {
  .playground-workspace {
    grid-template-columns: 1fr;
  }

  .left-panel {
    gap: 16px;
  }

  .right-panel {
    gap: 16px;
  }

  .flow-visual {
    min-height: 350px;
    padding: 24px;
  }

  .cli-float {
    bottom: 16px;
    right: 16px;
  }
}

@media (max-width: 768px) {
  .home-approval {
    padding: 16px;
  }

  .stats-tabs {
    flex-wrap: wrap;
    gap: 12px;
  }

  .stats-item {
    flex: 1 1 40%;
  }

  .task-card {
    max-height: 300px;
  }

  .task-list {
    max-height: 200px;
  }

  .detail-actions {
    flex-direction: column;
  }
}

@media (prefers-reduced-motion: reduce) {
  .stats-item,
  .task-item,
  .stage-item,
  .cli-shell {
    transition: none;
  }
}
</style>