<!-- src/views/submissions/SubmissionDetailView.vue -->
<template>
  <div class="submission-detail-page">
    <n-spin :show="loading">
      <n-page-header @back="goBack">
        <template #title>
          提交详情
        </template>
      </n-page-header>

      <n-alert
        v-if="!loading && !submission"
        type="warning"
        title="未找到对应的提交记录"
        class="mt-2"
      />

      <template v-else-if="submission">
        <n-grid :cols="24" :x-gap="16" :y-gap="16" responsive="screen">
          <!-- 基本信息 -->
          <n-gi :span="24" :md="12">
            <n-card title="基本信息" :bordered="false">
              <n-descriptions label-placement="left" :column="1" bordered size="small">
                <n-descriptions-item label="提交 ID">
                  {{ submission.id }}
                </n-descriptions-item>
                <n-descriptions-item label="表单名称">
                  {{ submission.form_name }}
                </n-descriptions-item>
                <n-descriptions-item label="提交人">
                  {{ submission.submitter_name }}
                </n-descriptions-item>
                <n-descriptions-item label="状态">
                  <n-space>
                    <n-tag :type="statusTagType(submission.status)">
                      {{ statusLabel(submission.status) }}
                    </n-tag>
                    <n-tag :type="processStateTag(submission.process_state)">
                      {{ formatProcessState(submission.process_state) }}
                    </n-tag>
                    <SlaBadge :level="timelineSlaLevel" :minutes="timelineRemainingMinutes" :show-remaining="true" />
                  </n-space>
                </n-descriptions-item>
                <n-descriptions-item label="提交时间">
                  {{ formatDate(submission.created_at) }}
                </n-descriptions-item>
                <n-descriptions-item label="耗时">
                  {{ formatDuration(submission.duration) }}
                </n-descriptions-item>
                <n-descriptions-item label="来源">
                  {{ submission.source || '-' }}
                </n-descriptions-item>
                <n-descriptions-item label="IP 地址">
                  {{ submission.ip_address || '-' }}
                </n-descriptions-item>
              </n-descriptions>
            </n-card>
          </n-gi>

          <!-- 快照信息 + 附件 -->
          <n-gi :span="24" :md="12">
            <n-space vertical :size="16">
              <n-card title="快照信息" :bordered="false">
                <n-descriptions label-placement="left" :column="1" bordered size="small">
                  <n-descriptions-item label="表单版本">
                    V{{ submission.snapshot_json?.version ?? '-' }}
                  </n-descriptions-item>
                  <n-descriptions-item label="发布于">
                    {{ submission.snapshot_json?.published_at ? formatDate(submission.snapshot_json.published_at) : '-' }}
                  </n-descriptions-item>
                  <n-descriptions-item label="字段数量">
                    {{ Object.keys(submission.snapshot_json?.field_labels || {}).length }}
                  </n-descriptions-item>
                </n-descriptions>
              </n-card>

              <n-card v-if="submission.attachments?.length" title="附件列表" :bordered="false">
                <n-data-table
                  :columns="attachmentColumns"
                  :data="submission.attachments"
                  :bordered="true"
                  size="small"
                  :single-line="false"
                />
              </n-card>
            </n-space>
          </n-gi>
        </n-grid>

        <!-- 表单数据 -->
        <n-card :bordered="false" class="data-card">
          <template #header>
            <div class="data-header">
              <h3>表单数据</h3>
              <n-button text type="primary" @click="toggleRawData">
                {{ showRawData ? '隐藏原始 JSON' : '查看原始 JSON' }}
              </n-button>
            </div>
          </template>

          <n-descriptions label-placement="left" :column="1" bordered size="small">
            <n-descriptions-item
              v-for="item in displayFields"
              :key="item.key"
              :label="item.label"
            >
              <template v-if="item.attachments">
                <n-space vertical :size="4">
                  <n-a
                    v-for="file in item.attachments"
                    :key="file.id"
                    :href="file.download_url"
                    target="_blank"
                  >
                    {{ file.file_name }}
                  </n-a>
                </n-space>
              </template>
              <template v-else>
                {{ formatFieldValue(item.value) }}
              </template>
            </n-descriptions-item>
          </n-descriptions>

          <n-collapse v-if="showRawData" style="margin-top: 16px;">
            <n-collapse-item title="原始数据 JSON" name="raw">
              <n-code :code="formattedRawData" language="json" show-line-numbers />
            </n-collapse-item>
          </n-collapse>
        </n-card>

        <!-- 流程轨迹 -->
        <n-card :bordered="false" class="timeline-card">
          <template #header>
            <div class="timeline-header">
              <h3>流程轨迹</h3>
              <n-space>
                <n-tag v-if="timelineStateLabel" size="small" :type="timelineStateTag">
                  {{ timelineStateLabel }}
                </n-tag>
                <SlaBadge :level="timelineSlaLevel" :minutes="timelineRemainingMinutes" :show-remaining="true" />
              </n-space>
            </div>
          </template>

          <n-spin :show="timelineLoading">
            <n-empty v-if="!hasProcessInstance" description="当前提交尚未进入流程" />
            <template v-else>
              <n-result
                v-if="timelineError"
                status="error"
                title="流程轨迹加载失败"
                :description="timelineError"
              >
                <template #footer>
                  <n-button size="small" type="primary" @click="loadTimeline">
                    重新加载
                  </n-button>
                </template>
              </n-result>
              <n-empty v-else-if="!timelineEntries.length" description="暂无轨迹记录" />
              <n-timeline v-else>
                <n-timeline-item
                  v-for="(entry, index) in timelineEntries"
                  :key="buildTimelineKey(entry, index)"
                  :type="timelineEntryVisualType(entry)"
                  :time="formatTimelineTime(entry)"
                >
                  <template #header>
                    <div class="timeline-node-header">
                      <span>{{ entry.node_name || '系统事件' }}</span>
                      <n-tag size="small" :type="timelineEntryVisualType(entry)">
                        {{ formatTimelineEntryLabel(entry) }}
                      </n-tag>
                    </div>
                  </template>
                  <div class="timeline-item-body">
                    <div class="timeline-meta">
                      <span>开始：{{ formatDate(entry.started_at) }}</span>
                      <span>完成：{{ formatDate(entry.completed_at) }}</span>
                    </div>
                    <div class="timeline-meta">
                      <span>截止：{{ formatDate(entry.due_at) || '—' }}</span>
                      <SlaBadge :level="entry.sla_level" :minutes="entry.remaining_sla_minutes" :show-remaining="true" />
                    </div>
                    <div class="timeline-meta">
                      <span>当前操作：{{ entry.action ? actionLabel(entry.action) : '待处理' }}</span>
                      <span>执行人：{{ formatActor(entry.actor_user_id, entry.actor_name) }}</span>
                    </div>
                    <p v-if="entry.comment" class="timeline-comment">
                      {{ entry.comment }}
                    </p>
                    <n-collapse v-if="entry.actions?.length" class="timeline-actions">
                      <n-collapse-item title="操作记录" :name="`actions-${index}`">
                        <n-timeline size="medium">
                          <n-timeline-item
                            v-for="(action, actionIndex) in entry.actions"
                            :key="`${entry.task_id || entry.node_id}-${actionIndex}`"
                            :type="timelineActionType(action)"
                            :time="formatDate(action.created_at)"
                          >
                            <div class="timeline-action-item">
                              <div class="timeline-meta">
                                <span>操作：{{ actionLabel(action.action) }}</span>
                                <span>执行人：{{ formatActor(action.actor_user_id, action.actor_name) }}</span>
                              </div>
                              <p v-if="action.comment" class="timeline-comment">
                                {{ action.comment }}
                              </p>
                            </div>
                          </n-timeline-item>
                        </n-timeline>
                      </n-collapse-item>
                    </n-collapse>
                  </div>
                </n-timeline-item>
              </n-timeline>
            </template>
          </n-spin>
        </n-card>
      </template>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage, NA, type DataTableColumns } from 'naive-ui'
import { getSubmissionDetail } from '@/api/submission'
import { getProcessTimeline } from '@/api/approvals'
import type { SubmissionDetail } from '@/types/submission'
import type { AttachmentInfo } from '@/types/attachment'
import type { ProcessTimelineResponse, TimelineEntry, TimelineAction } from '@/types/approval'
import { formatActionLabel, formatActorLabel, timelineActionTag } from '@/utils/audit'
import { formatRemainingMinutes, formatProcessState, processStateTag } from '@/utils/sla'
import SlaBadge from '@/components/common/SlaBadge.vue'

type TagType = 'default' | 'success' | 'error' | 'info' | 'warning'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const loading = ref(false)
const submission = ref<SubmissionDetail | null>(null)
const showRawData = ref(false)
const timelineLoading = ref(false)
const timelineError = ref<string | null>(null)
const timeline = ref<ProcessTimelineResponse | null>(null)

const attachmentMap = computed(() => {
  const map = new Map<number, AttachmentInfo>()
  const attachments = submission.value?.attachments ?? []
  attachments.forEach((item) => {
    map.set(item.id, item)
  })
  return map
})

interface DisplayField {
  key: string
  label: string
  value: unknown
  attachments?: AttachmentInfo[]
}

const displayFields = computed<DisplayField[]>(() => {
  if (!submission.value) return []
  const labels = submission.value.snapshot_json?.field_labels || {}
  const raw = submission.value.data_jsonb || {}
  return Object.entries(raw).map(([key, value]) => {
    const attachmentValue = resolveAttachmentValue(value)
    return {
      key,
      label: labels[key] || key,
      value,
      attachments: attachmentValue || undefined,
    }
  })
})

const formattedRawData = computed(() => {
  if (!submission.value) return ''
  return JSON.stringify(submission.value.data_jsonb || {}, null, 2)
})

const hasProcessInstance = computed(() => Boolean(submission.value?.process_instance_id))
const timelineEntries = computed<TimelineEntry[]>(() => timeline.value?.entries ?? [])
const latestTimelineEntry = computed(() => {
  const list = timelineEntries.value
  if (!list.length) return null
  return list[list.length - 1]
})
const timelineRemainingMinutes = computed(() => latestTimelineEntry.value?.remaining_sla_minutes ?? null)
const timelineSlaLevel = computed(() => latestTimelineEntry.value?.sla_level ?? null)

const timelineStateLabel = computed(() => {
  const state = timeline.value?.state || submission.value?.process_state
  if (!state) return ''
  switch (state) {
    case 'running':
      return '运行中'
    case 'finished':
      return '已完成'
    case 'canceled':
      return '已终止'
    default:
      return '未知状态'
  }
})

const timelineStateTag = computed<TagType>(() => {
  const state = timeline.value?.state || submission.value?.process_state
  if (!state) return 'default'
  if (state === 'finished') return 'success'
  if (state === 'running') return 'info'
  if (state === 'canceled') return 'warning'
  return 'default'
})

const ACTION_LABEL_MAP: Record<string, string> = {
  approve: '已通过',
  reject: '已拒绝',
  transfer: '已转交',
  delegate: '已委托',
  add_sign: '已加签',
  claim: '已认领',
  release: '已释放',
  cancel: '已撤销',
  auto_pass: '系统通过',
}

// 附件表格列定义
const attachmentColumns: DataTableColumns<AttachmentInfo> = [
  {
    title: '文件名',
    key: 'file_name',
    minWidth: 160,
    ellipsis: {
      tooltip: true
    },
    render(row) {
      return h(
        NA,
        {
          href: row.download_url,
          target: '_blank'
        },
        { default: () => row.file_name }
      )
    }
  },
  {
    title: '大小',
    key: 'size',
    width: 120,
    render(row) {
      return formatFileSize(row.size)
    }
  },
  {
    title: '类型',
    key: 'content_type',
    minWidth: 140
  },
  {
    title: '上传时间',
    key: 'created_at',
    width: 180,
    render(row) {
      return formatDate(row.created_at)
    }
  }
]

const resetTimelineState = () => {
  timeline.value = null
  timelineError.value = null
  timelineLoading.value = false
}

const loadTimeline = async () => {
  if (!submission.value?.process_instance_id) {
    resetTimelineState()
    return
  }
  timelineLoading.value = true
  timelineError.value = null
  try {
    const res = await getProcessTimeline(submission.value.process_instance_id)
    if (res.code === 200 && res.data) {
      timeline.value = res.data
    } else {
      timelineError.value = res.message || '获取流程轨迹失败'
    }
  } catch (error) {
    timelineError.value = '获取流程轨迹失败'
    console.error('Failed to load process timeline:', error)
  } finally {
    timelineLoading.value = false
  }
}

const loadDetail = async () => {
  const id = Number(route.params.id)
  if (!id) {
    message.error('无效的提交 ID')
    router.back()
    return
  }

  loading.value = true
  resetTimelineState()
  try {
    const res = await getSubmissionDetail(id)
    if (res.code === 200 && res.data) {
      submission.value = res.data
      await loadTimeline()
    } else {
      submission.value = null
    }
  } catch (error) {
    console.error('Failed to load submission detail:', error)
    message.error('加载详情失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const resolveAttachmentValue = (value: unknown): AttachmentInfo[] | null => {
  if (!Array.isArray(value)) return null
  const files = value
    .map((id) => (typeof id === 'number' ? attachmentMap.value.get(id) : null))
    .filter((item): item is AttachmentInfo => Boolean(item))
  return files.length ? files : null
}

const formatFieldValue = (value: unknown): string => {
  if (Array.isArray(value)) {
    return value.map((item) => String(item)).join('、')
  }
  if (value && typeof value === 'object') {
    return JSON.stringify(value)
  }
  return value != null ? String(value) : '-'
}

const statusLabel = (status: string) => {
  switch (status) {
    case 'approved':
      return '已通过'
    case 'rejected':
      return '已拒绝'
    case 'draft':
      return '草稿'
    default:
      return '已提交'
  }
}

const statusTagType = (status: string): 'success' | 'error' | 'info' | 'default' => {
  switch (status) {
    case 'approved':
      return 'success'
    case 'rejected':
      return 'error'
    case 'draft':
      return 'info'
    default:
      return 'default'
  }
}

const formatDuration = (seconds?: number) => {
  if (!seconds || seconds <= 0) return '-'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins <= 0) return `${secs} 秒`
  return `${mins} 分 ${secs} 秒`
}

const formatDate = (time?: string | null) => {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

const formatFileSize = (bytes?: number) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }
  return `${size.toFixed(size >= 10 || size === Math.floor(size) ? 0 : 1)} ${units[unitIndex]}`
}

const toggleRawData = () => {
  showRawData.value = !showRawData.value
}

const buildTimelineKey = (entry: TimelineEntry, index: number) => `${entry.task_id || entry.node_id || 'sys'}-${index}`

const timelineEntryVisualType = (entry: TimelineEntry): TagType => {
  const action = (entry.action || '').toLowerCase()
  if (action === 'approve' || entry.status === 'completed') return 'success'
  if (action === 'reject' || entry.status === 'canceled') return 'error'
  if (action === 'transfer' || action === 'delegate' || action === 'add_sign') return 'warning'
  if (entry.status === 'claimed') return 'info'
  return 'default'
}

const formatTimelineEntryLabel = (entry: TimelineEntry) => {
  const action = (entry.action || '').toLowerCase()
  if (ACTION_LABEL_MAP[action]) {
    return ACTION_LABEL_MAP[action]
  }
  switch (entry.status) {
    case 'completed':
      return '已完成'
    case 'claimed':
      return '处理中'
    case 'canceled':
      return '已终止'
    default:
      return '待处理'
  }
}

const formatTimelineTime = (entry: TimelineEntry) => {
  return formatDate(entry.completed_at || entry.started_at)
}

const actionLabel = (action?: string | null) => formatActionLabel(action)

const formatActor = (userId?: number | null, actorName?: string | null) =>
  formatActorLabel(userId, actorName)

const timelineActionType = (action: TimelineAction): TagType => timelineActionTag(action.action)

const goBack = () => {
  router.back()
}

onMounted(loadDetail)
</script>

<style scoped>
.submission-detail-page {
  padding: 20px;
}

.mt-2 {
  margin-top: 16px;
}

.data-card {
  margin-top: 16px;
}

.data-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.data-header h3 {
  margin: 0;
}

.timeline-card {
  margin-top: 16px;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.timeline-node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.timeline-item-body {
  margin-top: 8px;
}

.timeline-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 12px;
  color: #666;
}

.timeline-comment {
  margin-top: 6px;
  font-size: 13px;
  color: #333;
}
</style>