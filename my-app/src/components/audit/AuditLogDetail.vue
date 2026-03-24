<template>
  <div class="audit-log-detail">
    <!-- 基本信息 -->
    <n-descriptions label-placement="left" :column="1" bordered size="small">
      <n-descriptions-item label="日志ID">
        {{ log.id }}
      </n-descriptions-item>
      <n-descriptions-item label="操作人">
        {{ log.actor_name || `用户#${log.actor_user_id}` || '系统' }}
      </n-descriptions-item>
      <n-descriptions-item label="动作">
        <n-tag :type="getActionType(log.action)">
          {{ log.action }}
        </n-tag>
      </n-descriptions-item>
      <n-descriptions-item label="资源类型">
        {{ log.resource_type }}
      </n-descriptions-item>
      <n-descriptions-item label="资源ID">
        {{ log.resource_id || '-' }}
      </n-descriptions-item>
      <n-descriptions-item label="IP地址">
        {{ log.ip || '-' }}
      </n-descriptions-item>
      <n-descriptions-item label="时间">
        {{ new Date(log.created_at).toLocaleString() }}
      </n-descriptions-item>
    </n-descriptions>

    <!-- 变更对比 -->
    <n-divider>变更详情</n-divider>

    <n-empty v-if="!changes.length" description="无变更记录" />

    <n-table v-else :bordered="true" size="small">
      <thead>
        <tr>
          <th style="width: 120px">字段</th>
          <th style="width: 80px">变更类型</th>
          <th>变更前</th>
          <th>变更后</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="change in changes" :key="change.field">
          <td>
            <n-text strong>{{ change.field }}</n-text>
          </td>
          <td>
            <n-tag :type="getChangeTypeTag(change.change_type)" size="small">
              {{ getChangeTypeLabel(change.change_type) }}
            </n-tag>
          </td>
          <td>
            <n-code
              v-if="change.before !== null && change.before !== undefined"
              :code="formatValue(change.before)"
              language="json"
            />
            <n-text v-else depth="3">-</n-text>
          </td>
          <td>
            <n-code
              v-if="change.after !== null && change.after !== undefined"
              :code="formatValue(change.after)"
              language="json"
            />
            <n-text v-else depth="3">-</n-text>
          </td>
        </tr>
      </tbody>
    </n-table>

    <!-- 原始数据（可折叠） -->
    <n-divider>原始数据</n-divider>

    <n-collapse>
      <n-collapse-item title="变更前 (before_json)">
        <n-code :code="formatJson(log.before_json)" language="json" show-line-numbers />
      </n-collapse-item>
      <n-collapse-item title="变更后 (after_json)">
        <n-code :code="formatJson(log.after_json)" language="json" show-line-numbers />
      </n-collapse-item>
    </n-collapse>
  </div>
</template>

<script setup lang="ts">
import type { AuditLog, ChangeComparisonItem } from '@/api/audit'

interface Props {
  log: AuditLog
  changes: ChangeComparisonItem[]
}

defineProps<Props>()

// 动作类型映射
const getActionType = (action: string): string => {
  const typeMap: Record<string, string> = {
    create: 'success',
    update: 'warning',
    delete: 'error',
    publish: 'success',
    approve: 'success',
    reject: 'error',
    claim_task: 'info',
    release_task: 'default',
    transfer_task: 'warning',
    delegate_task: 'warning',
  }
  return typeMap[action] || 'default'
}

// 变更类型标签
const getChangeTypeTag = (type: string): string => {
  const tagMap: Record<string, string> = {
    added: 'success',
    modified: 'warning',
    removed: 'error',
  }
  return tagMap[type] || 'default'
}

// 变更类型标签
const getChangeTypeLabel = (type: string): string => {
  const labelMap: Record<string, string> = {
    added: '新增',
    modified: '修改',
    removed: '删除',
  }
  return labelMap[type] || type
}

// 格式化值
const formatValue = (value: any): string => {
  if (value === null || value === undefined) {
    return 'null'
  }
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

// 格式化JSON
const formatJson = (data: any): string => {
  if (!data) {
    return '{}'
  }
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}
</script>

<style scoped>
.audit-log-detail {
  padding: 8px 0;
}
</style>
