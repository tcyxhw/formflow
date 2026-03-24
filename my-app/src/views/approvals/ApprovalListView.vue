<!-- src/views/approvals/ApprovalListView.vue -->
<template>
  <div class="approval-list-page">
    <n-page-header title="审批控制台" subtitle="待办任务管理" />

    <n-card class="summary-card" title="SLA 概览">
      <template #header-extra>
        <span class="summary-hint">与筛选条件保持同步</span>
      </template>
      <n-spin :show="summaryLoading">
        <n-empty v-if="!slaSummary" description="暂无任务数据" size="small" />
        <div v-else class="summary-grid">
          <div v-for="item in summaryMetrics" :key="item.key" class="summary-item">
            <div class="summary-label">
              <span>{{ item.label }}</span>
              <SlaBadge v-if="item.level" :level="item.level" :show-remaining="false" />
            </div>
            <div class="summary-value">{{ item.value }}</div>
          </div>
        </div>
      </n-spin>
    </n-card>

    <n-card class="filters-card" title="筛选条件">
      <n-form inline :model="filters" label-placement="left" label-width="auto">
        <n-form-item label="关键词">
          <n-input
            v-model:value="filters.keyword"
            placeholder="节点/流程名称"
            clearable
            @keyup.enter="handleSearch"
          />
        </n-form-item>

        <n-form-item label="状态">
          <n-select
            v-model:value="filters.status"
            :options="statusOptions"
            clearable
            class="status-select"
          />
        </n-form-item>

        <n-form-item label="SLA 级别">
          <n-select
            v-model:value="filters.sla_level"
            :options="slaLevelOptions"
            clearable
            class="sla-select"
          />
        </n-form-item>

        <n-form-item label="仅本人">
          <n-switch v-model:value="filters.only_mine" @update:value="handleImmediateFilter" />
        </n-form-item>

        <n-form-item label="含组待办">
          <n-switch v-model:value="filters.include_group_tasks" @update:value="handleImmediateFilter" />
        </n-form-item>

        <n-form-item>
          <n-button type="primary" @click="handleSearch">查询</n-button>
        </n-form-item>
        <n-form-item>
          <n-button tertiary @click="handleReset">重置</n-button>
        </n-form-item>
      </n-form>
      <n-alert type="info" class="filters-hint" show-icon>
        SLA 徽章：绿色=正常、黄色=预警、红色=紧急/逾期，可结合状态筛选快速定位风险任务。
      </n-alert>
    </n-card>

    <n-card class="table-card" title="待办列表">
      <n-spin :show="loading">
        <n-data-table
          :columns="columns"
          :data="tasks"
          :bordered="false"
          :row-key="rowKey"
          size="small"
        />
      </n-spin>
      <div class="table-footer">
        <n-pagination
          :page="pagination.page"
          :page-size="pagination.pageSize"
          :item-count="pagination.total"
          show-size-picker
          :page-sizes="[10, 20, 30, 50]"
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </n-card>

    <n-card
      v-if="filters.include_group_tasks"
      class="table-card"
      title="小组待办池"
      size="small"
    >
      <template #header-extra>
        <div class="group-hint">未被认领的组任务，可快速认领</div>
      </template>
      <n-spin :show="groupLoading">
        <n-data-table
          :columns="groupColumns"
          :data="groupTasks"
          :bordered="false"
          :row-key="rowKey"
          size="small"
          :loading="groupLoading"
        />
      </n-spin>
      <div class="table-footer">
        <n-pagination
          :page="groupPagination.page"
          :page-size="groupPagination.pageSize"
          :item-count="groupPagination.total"
          show-size-picker
          :page-sizes="[10, 20, 30, 50]"
          @update:page="handleGroupPageChange"
          @update:page-size="handleGroupPageSizeChange"
        />
      </div>
    </n-card>

    <n-modal v-model:show="actionModalVisible" preset="dialog" :title="actionTitle">
      <div class="action-form">
        <n-input
          v-model:value="actionComment"
          type="textarea"
          placeholder="请输入审批意见"
          :autosize="{ minRows: 3, maxRows: 6 }"
        />
        <div class="action-buttons">
          <n-button @click="actionModalVisible = false">取消</n-button>
          <n-button type="primary" :loading="actionLoading" @click="submitAction">确认</n-button>
        </div>
      </div>
    </n-modal>

    <n-modal v-model:show="transferModalVisible" preset="dialog" title="任务转交">
      <div class="action-form">
        <n-input-number
          v-model:value="transferForm.target_user_id"
          placeholder="输入目标用户 ID"
          :min="1"
        />
        <n-input v-model:value="transferForm.message" placeholder="备注信息（可选）" />
        <div class="action-buttons">
          <n-button @click="transferModalVisible = false">取消</n-button>
          <n-button type="primary" :loading="transferLoading" @click="submitTransfer">
            确认转交
          </n-button>
        </div>
      </div>
    </n-modal>

    <n-modal v-model:show="detailModalVisible" preset="card" title="审批详情" style="width: 1000px; max-width: 95vw;">
      <div v-if="detailTask" class="detail-content">
        <div class="detail-left">
          <n-card title="审批信息" size="small" :bordered="false" class="info-card">
            <n-descriptions label-placement="left" :column="1" bordered size="small">
              <n-descriptions-item label="流程名称">{{ detailTask.flow_name || '—' }}</n-descriptions-item>
              <n-descriptions-item label="节点名称">{{ detailTask.node_name || '—' }}</n-descriptions-item>
              <n-descriptions-item label="提交人">{{ detailTask.submitter_name || '—' }}</n-descriptions-item>
              <n-descriptions-item label="任务状态">
                <n-tag :type="statusTagType(detailTask.status, detailTask.is_overdue)" :bordered="false" size="small">{{ statusLabel(detailTask.status, detailTask.is_overdue) }}</n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="流程状态">
                <n-tag :type="processStateTag(detailTask.process_state, detailTask.is_overdue)" :bordered="false" size="small">{{ formatProcessState(detailTask.process_state, detailTask.is_overdue) }}</n-tag>
              </n-descriptions-item>
              <n-descriptions-item label="截止时间">{{ formatDate(detailTask.due_at) || '—' }}</n-descriptions-item>
              <n-descriptions-item label="创建时间">{{ formatDate(detailTask.created_at) }}</n-descriptions-item>
            </n-descriptions>
          </n-card>
        </div>
        <div class="detail-right">
          <n-card title="表单数据" size="small" :bordered="false" class="form-data-card">
            <n-scrollbar style="max-height: 500px">
              <div v-if="detailTask?.form_data_snapshot && Object.keys(detailTask.form_data_snapshot).length > 0" class="form-fields">
                <div
                  v-for="(item, index) in formattedFormData"
                  :key="item.key"
                  class="form-field-item"
                  :class="{ 'field-alt': index % 2 === 1 }"
                >
                  <div class="field-label">
                    <n-icon size="14" class="field-icon" :depth="2">
                      <component :is="getFieldIcon(item.type)" />
                    </n-icon>
                    <span>{{ item.label }}</span>
                  </div>
                  <div class="field-value">
                    <!-- 图片/附件字段 -->
                    <template v-if="item.type === 'attachment'">
                      <div v-if="item.attachments && item.attachments.length > 0" class="attachment-list">
                        <div
                          v-for="file in item.attachments"
                          :key="file.id"
                          class="attachment-item"
                        >
                          <template v-if="isImageFile(file.content_type)">
                            <div class="image-preview">
                              <n-image
                                :src="`/api/v1/attachments/${file.id}/download?inline=true`"
                                :alt="file.file_name"
                                width="120"
                                height="90"
                                object-fit="cover"
                                :preview-src="`/api/v1/attachments/${file.id}/download?inline=true`"
                                fallback-src="/image-placeholder.png"
                              />
                              <n-button
                                text
                                type="primary"
                                size="tiny"
                                class="download-btn"
                                @click="downloadAttachment(file)"
                              >
                                <template #icon>
                                  <n-icon><DownloadIcon /></n-icon>
                                </template>
                                下载
                              </n-button>
                            </div>
                          </template>
                          <template v-else>
                            <n-button
                              text
                              type="primary"
                              size="small"
                              @click="downloadAttachment(file)"
                            >
                              <template #icon>
                                <n-icon><DocumentIcon /></n-icon>
                              </template>
                              {{ file.file_name }}
                              <span class="file-size">({{ formatFileSize(file.size) }})</span>
                            </n-button>
                          </template>
                        </div>
                      </div>
                      <span v-else class="empty-value">未上传附件</span>
                    </template>

                    <!-- 日期范围字段 -->
                    <template v-else-if="item.type === 'date-range'">
                      <n-tag size="small" type="info" class="date-tag">
                        <n-icon size="12"><CalendarIcon /></n-icon>
                        {{ item.displayValue }}
                      </n-tag>
                    </template>

                    <!-- 日期字段 -->
                    <template v-else-if="item.type === 'date'">
                      <n-tag size="small" type="info" class="date-tag">
                        <n-icon size="12"><CalendarIcon /></n-icon>
                        {{ item.displayValue }}
                      </n-tag>
                    </template>

                    <!-- 选项字段 -->
                    <template v-else-if="item.type === 'select'">
                      <n-tag size="small" :type="getSelectTagType(item.value)" class="select-tag">
                        {{ item.displayValue }}
                      </n-tag>
                    </template>

                    <!-- 多选字段 -->
                    <template v-else-if="item.type === 'multi-select'">
                      <n-space size="small" wrap>
                        <n-tag
                          v-for="(tag, idx) in item.displayValueArray"
                          :key="idx"
                          size="small"
                          :type="getSelectTagType(tag)"
                        >
                          {{ tag }}
                        </n-tag>
                      </n-space>
                    </template>

                    <!-- 数字字段 -->
                    <template v-else-if="item.type === 'number'">
                      <span class="number-value">{{ item.displayValue }}</span>
                    </template>

                    <!-- 布尔字段 -->
                    <template v-else-if="item.type === 'boolean'">
                      <n-tag size="small" :type="item.value ? 'success' : 'default'">
                        {{ item.displayValue }}
                      </n-tag>
                    </template>

                    <!-- 长文本字段 -->
                    <template v-else-if="item.type === 'textarea'">
                      <div class="textarea-value">{{ item.displayValue }}</div>
                    </template>

                    <!-- 默认文本字段 -->
                    <template v-else>
                      <span class="text-value">{{ item.displayValue }}</span>
                    </template>
                  </div>
                </div>
              </div>
              <n-empty v-else description="暂无表单数据" size="small" />
            </n-scrollbar>
          </n-card>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from 'vue'
import dayjs from 'dayjs'
import type { DataTableColumns } from 'naive-ui'
import { NButton, NTag, useMessage, NIcon, NImage, NSpace } from 'naive-ui'
import {
  CalendarOutline as CalendarIcon,
  DocumentTextOutline as DocumentIcon,
  DownloadOutline as DownloadIcon,
  TextOutline as TextIcon,
  ListOutline as ListIcon,
  CheckmarkCircleOutline as CheckIcon,
  ImageOutline as ImageIcon,
  AttachOutline as AttachIcon,
  PricetagOutline as TagIcon
} from '@vicons/ionicons5'
import SlaBadge from '@/components/common/SlaBadge.vue'

import type {
  TaskActionRequest,
  TaskListQuery,
  TaskResponse,
  TaskSlaSummary,
  TaskStatus
} from '@/types/approval'
import type { SlaLevel } from '@/types/approval'
import type { AttachmentInfo } from '@/types/attachment'

import {
  claimTask,
  getTaskSlaSummary,
  listGroupTasks,
  listTasks,
  performTaskAction,
  releaseTask,
  transferTask
} from '@/api/approvals'

import { formatActionLabel, formatActorLabel } from '@/utils/audit'
import { formatProcessState, processStateTag } from '@/utils/sla'

interface PaginationState {
  page: number
  pageSize: number
  total: number
}

interface FormFieldItem {
  key: string
  label: string
  type: string
  value: unknown
  displayValue: string
  displayValueArray?: string[]
  attachments?: AttachmentInfo[]
}

const message = useMessage()

const loading = ref(false)
const summaryLoading = ref(false)
const tasks = ref<TaskResponse[]>([])
const slaSummary = ref<TaskSlaSummary | null>(null)
const groupLoading = ref(false)
const groupTasks = ref<TaskResponse[]>([])

const pagination = reactive<PaginationState>({
  page: 1,
  pageSize: 10,
  total: 0
})

const groupPagination = reactive<PaginationState>({
  page: 1,
  pageSize: 10,
  total: 0
})

const filters = reactive<TaskListQuery>({
  status: null,
  only_mine: true,
  include_group_tasks: true,
  keyword: '',
  sla_level: null
})

const slaLevelOptions: Array<{ label: string; value: SlaLevel }> = [
  { label: '状态未知', value: 'unknown' },
  { label: '正常', value: 'normal' },
  { label: '预警', value: 'warning' },
  { label: '紧急', value: 'critical' },
  { label: '已超时', value: 'expired' }
]

const statusOptions: Array<{ label: string; value: TaskStatus }> = [
  { label: '待认领', value: 'open' },
  { label: '已认领', value: 'claimed' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'canceled' }
]

const actionModalVisible = ref(false)
const actionLoading = ref(false)
const actionIntent = ref<'approve' | 'reject'>('approve')
const actionComment = ref('')
const actionTask = ref<TaskResponse | null>(null)
const transferModalVisible = ref(false)
const transferLoading = ref(false)
const detailModalVisible = ref(false)
const detailTask = ref<TaskResponse | null>(null)

const transferForm = reactive({
  target_user_id: null as number | null,
  message: ''
})

// 选项值映射表
const optionValueMap: Record<string, string> = {
  // 请假类型
  sick: '病假',
  personal: '事假',
  annual: '年假',
  marriage: '婚假',
  maternity: '产假',
  paternity: '陪产假',
  bereavement: '丧假',
  other: '其他',
  // 审批状态
  pending: '待审批',
  approved: '已通过',
  rejected: '已驳回',
  // 优先级
  high: '高',
  medium: '中',
  low: '低',
  urgent: '紧急',
  // 是否
  yes: '是',
  no: '否',
  true: '是',
  false: '否'
}

// 字段标签映射
const fieldLabelMap: Record<string, string> = {
  name: '姓名',
  title: '标题',
  content: '内容',
  description: '描述',
  reason: '原因',
  department: '部门',
  email: '邮箱',
  phone: '电话',
  address: '地址',
  date: '日期',
  time: '时间',
  amount: '金额',
  quantity: '数量',
  status: '状态',
  type: '类型',
  category: '分类',
  remark: '备注',
  comment: '意见',
  applicant: '申请人',
  approver: '审批人',
  start_date: '开始日期',
  end_date: '结束日期',
  create_time: '创建时间',
  update_time: '更新时间',
  student_name: '学生姓名',
  student_id: '学号',
  days: '请假天数',
  advisor: '指导老师',
  thesis_title: '论文题目',
  thesis_type: '论文类型',
  abstract: '摘要',
  word_count: '字数',
  major: '专业',
  preferred_date: '期望日期',
  attachment: '附件',
  proof: '证明材料',
  leave_type: '请假类型',
  startDate: '开始日期',
  endDate: '结束日期',
  leaveDays: '请假天数'
}

interface SummaryMetric {
  key: string
  label: string
  value: number
  level?: SlaLevel | null
}

const summaryMetrics = computed<SummaryMetric[]>(() => {
  const summary = slaSummary.value
  return [
    { key: 'total', label: '全部任务', value: summary?.total ?? 0 },
    { key: 'normal', label: '正常', value: summary?.normal ?? 0, level: 'normal' },
    { key: 'warning', label: '预警', value: summary?.warning ?? 0, level: 'warning' },
    { key: 'critical', label: '紧急', value: summary?.critical ?? 0, level: 'critical' },
    { key: 'expired', label: '已超时', value: summary?.expired ?? 0, level: 'expired' }
  ]
})

const rowKey = (row: TaskResponse) => row.id.toString()

const actionTitle = computed(() =>
  actionIntent.value === 'approve' ? '通过审批' : '驳回审批'
)

// 格式化表单数据
const formattedFormData = computed<FormFieldItem[]>(() => {
  if (!detailTask.value?.form_data_snapshot) return []
  
  const snapshot = detailTask.value.form_data_snapshot
  return Object.entries(snapshot).map(([key, value]) => {
    const type = detectFieldType(key, value)
    const label = getFieldLabel(key)
    const { displayValue, displayValueArray, attachments } = formatValueByType(value, type, key)
    
    return {
      key,
      label,
      type,
      value,
      displayValue,
      displayValueArray,
      attachments
    }
  })
})

// 检测字段类型
function detectFieldType(key: string, value: unknown): string {
  const keyLower = key.toLowerCase()
  
  // 附件字段
  if (keyLower.includes('attachment') || keyLower.includes('proof') || keyLower.includes('file')) {
    return 'attachment'
  }
  
  // 日期范围
  if (keyLower.includes('range') || (Array.isArray(value) && value.length === 2 && isTimestamp(value[0]))) {
    return 'date-range'
  }
  
  // 日期字段
  if (keyLower.includes('date') || keyLower.includes('time')) {
    return 'date'
  }
  
  // 布尔字段
  if (typeof value === 'boolean') {
    return 'boolean'
  }
  
  // 数字字段
  if (typeof value === 'number' && !isTimestamp(value)) {
    return 'number'
  }
  
  // 多选字段（数组但不是附件）
  if (Array.isArray(value) && value.length > 0 && typeof value[0] === 'string') {
    return 'multi-select'
  }
  
  // 选项字段
  if (typeof value === 'string' && (optionValueMap[value] || ['sick', 'personal', 'annual', 'pending', 'approved', 'high', 'medium', 'low'].includes(value))) {
    return 'select'
  }
  
  // 长文本
  if (typeof value === 'string' && value.length > 50) {
    return 'textarea'
  }
  
  return 'text'
}

// 判断是否为时间戳
function isTimestamp(value: unknown): boolean {
  if (typeof value !== 'number') return false
  // 时间戳通常在 2000-2030 年之间
  const minTimestamp = 946656000000 // 2000-01-01
  const maxTimestamp = 1893456000000 // 2030-01-01
  return value >= minTimestamp && value <= maxTimestamp
}

// 获取字段标签
function getFieldLabel(key: string): string {
  // 直接匹配
  if (fieldLabelMap[key]) return fieldLabelMap[key]
  
  // 小写匹配
  const keyLower = key.toLowerCase()
  for (const [k, v] of Object.entries(fieldLabelMap)) {
    if (keyLower === k.toLowerCase()) return v
  }
  
  // 包含匹配
  for (const [k, v] of Object.entries(fieldLabelMap)) {
    if (keyLower.includes(k.toLowerCase())) return v
  }
  
  return key
}

// 根据类型格式化值
function formatValueByType(value: unknown, type: string, key: string): { 
  displayValue: string
  displayValueArray?: string[]
  attachments?: AttachmentInfo[]
} {
  if (value === null || value === undefined) {
    return { displayValue: '—' }
  }
  
  switch (type) {
    case 'date':
      return { displayValue: formatTimestamp(value) }
    
    case 'date-range':
      if (Array.isArray(value) && value.length === 2) {
        const start = formatTimestamp(value[0])
        const end = formatTimestamp(value[1])
        return { displayValue: `${start} 至 ${end}` }
      }
      return { displayValue: String(value) }
    
    case 'select':
      if (typeof value === 'string') {
        return { displayValue: optionValueMap[value] || value }
      }
      return { displayValue: String(value) }
    
    case 'multi-select':
      if (Array.isArray(value)) {
        const mapped = value.map(v => optionValueMap[String(v)] || String(v))
        return { 
          displayValue: mapped.join('、'),
          displayValueArray: mapped
        }
      }
      return { displayValue: String(value) }
    
    case 'boolean':
      return { displayValue: value ? '是' : '否' }
    
    case 'attachment':
      // 处理附件ID数组
      if (Array.isArray(value) && value.length > 0 && typeof value[0] === 'number') {
        // 这里需要从后端获取附件信息，暂时显示为ID列表
        return { 
          displayValue: `${value.length} 个附件`,
          attachments: value.map(id => ({
            id,
            file_name: `附件 ${id}`,
            content_type: 'application/octet-stream',
            size: 0,
            download_url: `/api/v1/attachments/${id}/download`
          }))
        }
      }
      return { displayValue: '无附件' }
    
    case 'number':
      return { displayValue: String(value) }
    
    case 'textarea':
    case 'text':
    default:
      if (typeof value === 'string') {
        return { displayValue: value || '—' }
      }
      if (Array.isArray(value)) {
        return { displayValue: value.join('、') }
      }
      if (typeof value === 'object') {
        return { displayValue: JSON.stringify(value) }
      }
      return { displayValue: String(value) }
  }
}

// 格式化时间戳
function formatTimestamp(value: unknown): string {
  if (!value) return '—'
  
  let timestamp: number
  if (typeof value === 'number') {
