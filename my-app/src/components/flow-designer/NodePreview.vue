<template>
  <div class="node-preview">
    <!-- 头部 -->
    <div class="preview-header">
      <div class="title">节点预览</div>
      <div class="subtitle">{{ node?.name || '未选择节点' }}</div>
    </div>

    <!-- 主体内容 -->
    <div v-if="node" class="preview-body">
      <!-- 基本信息 -->
      <div class="section">
        <div class="section-title">基本信息</div>
        <n-descriptions :columns="1" size="small">
          <n-descriptions-item label="节点名称">
            {{ node.name }}
          </n-descriptions-item>
          <n-descriptions-item label="节点类型">
            <n-tag :type="getNodeTypeColor(node.type)">
              {{ getNodeTypeLabel(node.type) }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item v-if="node.id" label="节点 ID">
            {{ node.id }}
          </n-descriptions-item>
          <n-descriptions-item v-if="node.temp_id" label="临时 ID">
            {{ node.temp_id }}
          </n-descriptions-item>
        </n-descriptions>
      </div>

      <!-- 审批配置（非条件节点） -->
      <div v-if="node.type !== 'condition' && node.type !== 'start' && node.type !== 'end'" class="section">
        <div class="section-title">审批配置</div>
        <n-descriptions :columns="1" size="small">
          <n-descriptions-item label="审批人类型">
            {{ node.assignee_type || '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="会签策略">
            {{ getApprovePolicyLabel(node.approve_policy) }}
          </n-descriptions-item>
          <n-descriptions-item v-if="node.approve_policy === 'percent'" label="通过阈值">
            {{ node.approve_threshold ?? '-' }}%
          </n-descriptions-item>
          <n-descriptions-item label="允许代理">
            <n-tag :type="node.allow_delegate ? 'success' : 'error'">
              {{ node.allow_delegate ? '是' : '否' }}
            </n-tag>
          </n-descriptions-item>
        </n-descriptions>
      </div>

      <!-- 驳回策略 -->
      <div v-if="node.type !== 'condition' && node.type !== 'start' && node.type !== 'end'" class="section">
        <div class="section-title">驳回策略</div>
        <n-descriptions :columns="1" size="small">
          <n-descriptions-item label="驳回策略">
            {{ getRejectStrategyLabel(node.reject_strategy) }}
          </n-descriptions-item>
        </n-descriptions>
      </div>

      <!-- SLA 配置 -->
      <div v-if="node.type !== 'condition' && node.type !== 'start' && node.type !== 'end'" class="section">
        <div class="section-title">SLA 配置</div>
        <n-descriptions :columns="1" size="small">
          <n-descriptions-item label="SLA 时长">
            {{ node.sla_hours ? `${node.sla_hours} 小时` : '未设置' }}
          </n-descriptions-item>
        </n-descriptions>
      </div>

      <!-- 自动审批 -->
      <div v-if="node.type !== 'condition' && node.type !== 'start' && node.type !== 'end'" class="section">
        <div class="section-title">自动审批</div>
        <n-descriptions :columns="1" size="small">
          <n-descriptions-item label="启用自动审批">
            <n-tag :type="node.auto_approve_enabled ? 'success' : 'default'">
              {{ node.auto_approve_enabled ? '是' : '否' }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item v-if="node.auto_approve_enabled" label="抽检比例">
            {{ (node.auto_sample_ratio * 100).toFixed(1) }}%
          </n-descriptions-item>
        </n-descriptions>
      </div>

      <!-- 路由模式 -->
      <div class="section">
        <div class="section-title">路由模式</div>
        <n-descriptions :columns="1" size="small">
          <n-descriptions-item label="路由模式">
            {{ getRouteModeLabel(node.route_mode) }}
          </n-descriptions-item>
        </n-descriptions>
      </div>

      <!-- 条件分支配置（条件节点） -->
      <div v-if="node.type === 'condition' && node.condition_branches" class="section">
        <div class="section-title">条件分支</div>
        <div class="branches-list">
          <div
            v-for="(branch, index) in node.condition_branches.branches"
            :key="index"
            class="branch-item"
          >
            <div class="branch-header">
              <span class="branch-label">{{ branch.label }}</span>
              <n-tag type="info" size="small">优先级: {{ branch.priority }}</n-tag>
            </div>
            <div class="branch-condition">
              <code>{{ JSON.stringify(branch.condition) }}</code>
            </div>
          </div>
          <div class="branch-item default">
            <div class="branch-header">
              <span class="branch-label">默认分支</span>
            </div>
            <div class="branch-target">
              目标节点 ID: {{ node.condition_branches.default_target_node_id }}
            </div>
          </div>
        </div>
      </div>

      <!-- 元数据 -->
      <div v-if="Object.keys(node.metadata).length > 0" class="section">
        <div class="section-title">元数据</div>
        <n-code
          :code="JSON.stringify(node.metadata, null, 2)"
          language="json"
          :show-line-numbers="false"
        />
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="preview-empty">
      <n-empty description="请选择节点进行预览" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  NDescriptions,
  NDescriptionsItem,
  NTag,
  NEmpty,
  NCode
} from 'naive-ui'
import type { FlowNodeConfig } from '@/types/flow'

interface Props {
  node?: FlowNodeConfig
}

defineProps<Props>()

// 获取节点类型标签
const getNodeTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    start: '开始',
    user: '人工审批',
    condition: '条件分支',
    auto: '自动节点',
    end: '结束'
  }
  return labels[type] || type
}

// 获取节点类型颜色
const getNodeTypeColor = (type: string): string => {
  const colors: Record<string, string> = {
    start: 'success',
    user: 'info',
    condition: 'warning',
    auto: 'default',
    end: 'error'
  }
  return colors[type] || 'default'
}

// 获取会签策略标签
const getApprovePolicyLabel = (policy: string): string => {
  const labels: Record<string, string> = {
    any: '任意一人',
    all: '全部同意',
    percent: '自定义比例'
  }
  return labels[policy] || policy
}

// 获取驳回策略标签
const getRejectStrategyLabel = (strategy: string): string => {
  const labels: Record<string, string> = {
    TO_START: '驳回到发起人',
    TO_PREVIOUS: '驳回到上一个节点'
  }
  return labels[strategy] || strategy
}

// 获取路由模式标签
const getRouteModeLabel = (mode: string): string => {
  const labels: Record<string, string> = {
    exclusive: '互斥',
    parallel: '并行'
  }
  return labels[mode] || mode
}
</script>

<style scoped>
.node-preview {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e0e5ec;
  overflow: hidden;
}

.preview-header {
  padding: 20px 24px;
  background: linear-gradient(135deg, #f6fbf8 0%, #f0f6ff 100%);
  border-bottom: 1px solid #e0e5ec;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.subtitle {
  font-size: 12px;
  color: #6b7385;
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preview-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.preview-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.branches-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.branch-item {
  padding: 12px;
  border: 1px solid #e0e5ec;
  border-radius: 6px;
  background: #fafbfc;
}

.branch-item.default {
  background: #f0f6ff;
  border-color: #0ea5e9;
}

.branch-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 8px;
}

.branch-label {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}

.branch-condition {
  font-size: 12px;
  color: #6b7385;
  overflow-x: auto;
}

.branch-condition code {
  background: #ffffff;
  padding: 8px;
  border-radius: 4px;
  display: block;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

.branch-target {
  font-size: 12px;
  color: #6b7385;
}

:deep(.n-descriptions) {
  --n-item-padding: 8px 0;
}

:deep(.n-descriptions-item__label) {
  font-size: 12px;
  color: #6b7385;
}

:deep(.n-descriptions-item__content) {
  font-size: 13px;
  color: #1f2937;
}

:deep(.n-code) {
  margin-top: 8px;
}
</style>
