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
                                :src="getImageUrl(file)"
                                :alt="file.file_name"
                                width="120"
                                height="90"
                                object-fit="cover"
                                :preview-src="getImageUrl(file)"
                                fallback-src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='90' viewBox='0 0 120 90'%3E%3Crect fill='%23f0f0f0' width='120' height='90'/%3E%3Ctext fill='%23999' x='60' y='50' text-anchor='middle' font-size='12'%3E加载中...%3C/text%3E%3C/svg%3E"
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
import { computed, h, onMounted, reactive, ref, watch } from 'vue'
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
  TaskStatus,
  TaskTransferRequest
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
import { getAttachment } from '@/api/attachment'
import { useAuthStore } from '@/stores/auth'

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
const authStore = useAuthStore()

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
const attachmentDetails = ref<Map<number, AttachmentInfo>>(new Map())

// 监听详情变化，批量加载附件信息
watch(detailTask, async (task) => {
  if (!task?.form_data_snapshot) {
    attachmentDetails.value.clear()
    return
  }
  
  // 收集所有附件 ID
  const attachmentIds: number[] = []
  Object.entries(task.form_data_snapshot).forEach(([key, value]) => {
    const keyLower = key.toLowerCase()
    if (keyLower.includes('attachment') || keyLower.includes('proof') || keyLower.includes('file') || keyLower.includes('cert') || keyLower.includes('image')) {
      // 单个附件ID
      if (typeof value === 'number' && value > 0) {
        attachmentIds.push(value)
      }
      // 附件ID数组
      else if (Array.isArray(value) && value.length > 0 && typeof value[0] === 'number') {
        attachmentIds.push(...value)
      }
    }
  })
  
  if (attachmentIds.length === 0) {
    attachmentDetails.value.clear()
    return
  }
  
  // 批量加载附件详情
  const details = await loadAttachmentDetails(attachmentIds)
  const newMap = new Map<number, AttachmentInfo>()
  details.forEach(info => newMap.set(info.id, info))
  attachmentDetails.value = newMap
}, { immediate: true })

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
  medical_cert: '病假证明',
  medical_certificate: '病假证明',
  leave_type: '请假类型',
  leaveType: '请假类型',
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
  if (keyLower.includes('attachment') || keyLower.includes('proof') || keyLower.includes('file') || keyLower.includes('cert') || keyLower.includes('image')) {
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
        // 先尝试精确匹配，再尝试小写匹配
        return { displayValue: optionValueMap[value] || optionValueMap[value.toLowerCase()] || value }
      }
      return { displayValue: String(value) }
    
    case 'multi-select':
      if (Array.isArray(value)) {
        const mapped = value.map(v => {
          const str = String(v)
          return optionValueMap[str] || optionValueMap[str.toLowerCase()] || str
        })
        return { 
          displayValue: mapped.join('、'),
          displayValueArray: mapped
        }
      }
      return { displayValue: String(value) }
    
    case 'boolean':
      return { displayValue: value ? '是' : '否' }
    
    case 'attachment':
      // 处理单个附件ID
      if (typeof value === 'number' && value > 0) {
        const attachment = attachmentDetails.value.has(value) 
          ? attachmentDetails.value.get(value)!
          : {
              id: value,
              file_name: `附件_${value}`,
              content_type: 'application/octet-stream',
              size: 0,
              storage_path: '',
              download_url: `/api/v1/attachments/${value}/download`,
              created_at: ''
            }
        return {
          displayValue: '1 个附件',
          attachments: [attachment]
        }
      }
      // 处理附件ID数组
      if (Array.isArray(value) && value.length > 0 && typeof value[0] === 'number') {
        // 使用已加载的附件信息
        const attachments = value.map(id => {
          if (attachmentDetails.value.has(id)) {
            return attachmentDetails.value.get(id)!
          }
          // 如果还未加载，返回占位信息
          return {
            id,
            file_name: `附件_${id}`,
            content_type: 'application/octet-stream',
            size: 0,
            storage_path: '',
            download_url: `/api/v1/attachments/${id}/download`,
            created_at: ''
          }
        })
        return { 
          displayValue: `${value.length} 个附件`,
          attachments
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

// 检查文件是否为图片
function isImageFile(contentType: string): boolean {
  return contentType?.startsWith('image/') ?? false
}

// 附件信息缓存
const attachmentCache = new Map<number, AttachmentInfo>()

// 获取附件详情
async function loadAttachmentDetails(ids: number[]): Promise<AttachmentInfo[]> {
  const results: AttachmentInfo[] = []
  
  for (const id of ids) {
    if (attachmentCache.has(id)) {
      results.push(attachmentCache.get(id)!)
      continue
    }
    
    try {
      const { data } = await getAttachment(id)
      if (data) {
        attachmentCache.set(id, data)
        results.push(data)
      }
    } catch {
      // 如果获取失败，使用默认值
      const fallback: AttachmentInfo = {
        id,
        file_name: `附件_${id}`,
        content_type: 'application/octet-stream',
        size: 0,
        storage_path: '',
        download_url: `/api/v1/attachments/${id}/download`,
        created_at: ''
      }
      results.push(fallback)
    }
  }
  
  return results
}

// 获取带认证 token 的图片 URL
function getImageUrl(attachment: AttachmentInfo): string {
  if (!attachment.download_url) return ''
  const token = authStore.getAccessToken()
  const baseUrl = attachment.download_url.startsWith('http') 
    ? attachment.download_url 
    : `${attachment.download_url}`
  return `${baseUrl}?token=${encodeURIComponent(token)}`
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '未知'
  const units = ['B', 'KB', 'MB', 'GB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`
}

// 格式化时间戳
function formatTimestamp(value: unknown): string {
  if (!value) return '—'
  
  let timestamp: number
  if (typeof value === 'number') {
    timestamp = value
  } else if (typeof value === 'string') {
    timestamp = Date.parse(value)
  } else {
    return '—'
  }
  
  if (isNaN(timestamp)) return '—'
  
  // 判断是秒还是毫秒时间戳
  if (timestamp < 1e12) {
    timestamp *= 1000
  }
  
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
}

// 获取选项标签样式类型
function getSelectTagType(value: unknown): 'success' | 'warning' | 'error' | 'info' | 'default' {
  if (typeof value !== 'string') return 'default'
  
  // 审批状态
  if (value === '已通过') return 'success'
  if (value === '待审批') return 'warning'
  if (value === '已驳回') return 'error'
  
  // 优先级
  if (value === '紧急' || value === '高') return 'error'
  if (value === '中') return 'warning'
  if (value === '低') return 'success'
  
  return 'info'
}

// 下载附件
function downloadAttachment(file: AttachmentInfo): void {
  const token = authStore.getAccessToken()
  const url = file.download_url.startsWith('http')
    ? file.download_url
    : `${file.download_url}?token=${encodeURIComponent(token)}`
  window.open(url, '_blank')
}

// 获取字段图标
function getFieldIcon(type: string) {
  switch (type) {
    case 'attachment':
      return ImageIcon
    case 'date':
    case 'date-range':
      return CalendarIcon
    case 'select':
    case 'multi-select':
      return ListIcon
    case 'boolean':
      return CheckIcon
    case 'number':
      return TagIcon
    case 'textarea':
      return TextIcon
    default:
      return DocumentIcon
  }
}

// ========== 状态相关函数 ==========

// 获取任务状态标签类型
function statusTagType(status: TaskStatus, isOverdue?: boolean): 'success' | 'error' | 'info' | 'warning' | 'default' {
  if (isOverdue) return 'error'
  switch (status) {
    case 'open':
      return 'info'
    case 'claimed':
      return 'warning'
    case 'completed':
      return 'success'
    case 'canceled':
      return 'default'
    default:
      return 'default'
  }
}

// 获取任务状态标签文本
function statusLabel(status: TaskStatus, isOverdue?: boolean): string {
  if (isOverdue) return '已超时'
  switch (status) {
    case 'open':
      return '待认领'
    case 'claimed':
      return '已认领'
    case 'completed':
      return '已完成'
    case 'canceled':
      return '已取消'
    default:
      return status
  }
}

// 格式化日期
function formatDate(value?: string | null): string {
  if (!value) return '—'
  return dayjs(value).format('YYYY-MM-DD HH:mm:ss')
}

// ========== 数据加载函数 ==========

// 加载任务列表
async function loadTasks() {
  loading.value = true
  try {
    const params: TaskListQuery = {
      page: pagination.page,
      page_size: pagination.pageSize,
      status: filters.status,
      only_mine: filters.only_mine,
      include_group_tasks: filters.include_group_tasks,
      keyword: filters.keyword,
      sla_level: filters.sla_level
    }
    const { data } = await listTasks(params)
    tasks.value = data.items
    pagination.total = data.total
  } catch (error) {
    console.error('加载任务列表失败:', error)
    message.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

// 加载 SLA 摘要
async function loadSlaSummary() {
  summaryLoading.value = true
  try {
    const params: TaskListQuery = {
      status: filters.status,
      only_mine: filters.only_mine,
      include_group_tasks: filters.include_group_tasks,
      keyword: filters.keyword,
      sla_level: filters.sla_level
    }
    const { data } = await getTaskSlaSummary(params)
    slaSummary.value = data
  } catch (error) {
    console.error('加载 SLA 摘要失败:', error)
  } finally {
    summaryLoading.value = false
  }
}

// 加载组任务列表
async function loadGroupTasks() {
  groupLoading.value = true
  try {
    const { data } = await listGroupTasks({
      page: groupPagination.page,
      page_size: groupPagination.pageSize
    })
    groupTasks.value = data.items
    groupPagination.total = data.total
  } catch (error) {
    console.error('加载组任务失败:', error)
  } finally {
    groupLoading.value = false
  }
}

// ========== 筛选相关函数 ==========

// 搜索
function handleSearch() {
  pagination.page = 1
  loadTasks()
  loadSlaSummary()
}

// 重置筛选
function handleReset() {
  filters.keyword = ''
  filters.status = null
  filters.sla_level = null
  filters.only_mine = true
  filters.include_group_tasks = true
  pagination.page = 1
  loadTasks()
  loadSlaSummary()
}

// 即时筛选
function handleImmediateFilter() {
  pagination.page = 1
  loadTasks()
  loadSlaSummary()
}

// ========== 分页相关函数 ==========

function handlePageChange(page: number) {
  pagination.page = page
  loadTasks()
}

function handlePageSizeChange(size: number) {
  pagination.pageSize = size
  pagination.page = 1
  loadTasks()
}

function handleGroupPageChange(page: number) {
  groupPagination.page = page
  loadGroupTasks()
}

function handleGroupPageSizeChange(size: number) {
  groupPagination.pageSize = size
  groupPagination.page = 1
  loadGroupTasks()
}

// ========== 操作相关函数 ==========

// 查看详情
function handleViewDetail(row: TaskResponse) {
  detailTask.value = row
  detailModalVisible.value = true
}

// 认领任务
async function handleClaim(row: TaskResponse) {
  try {
    await claimTask(row.id)
    message.success('认领成功')
    loadTasks()
  } catch (error) {
    console.error('认领失败:', error)
    message.error('认领失败')
  }
}

// 释放任务
async function handleRelease(row: TaskResponse) {
  try {
    await releaseTask(row.id)
    message.success('释放成功')
    loadTasks()
  } catch (error) {
    console.error('释放失败:', error)
    message.error('释放失败')
  }
}

// 打开审批操作弹窗
function openActionModal(task: TaskResponse, intent: 'approve' | 'reject') {
  actionTask.value = task
  actionIntent.value = intent
  actionComment.value = ''
  actionModalVisible.value = true
}

// 打开转交弹窗
function openTransferModal(task: TaskResponse) {
  actionTask.value = task
  transferForm.target_user_id = null
  transferForm.message = ''
  transferModalVisible.value = true
}

// 提交审批操作
async function submitAction() {
  if (!actionTask.value) return
  
  actionLoading.value = true
  try {
    const payload: TaskActionRequest = {
      action: actionIntent.value,
      comment: actionComment.value || undefined
    }
    await performTaskAction(actionTask.value.id, payload)
    message.success(actionIntent.value === 'approve' ? '审批通过' : '已驳回')
    actionModalVisible.value = false
    actionComment.value = ''
    loadTasks()
    loadSlaSummary()
  } catch (error) {
    console.error('审批操作失败:', error)
    message.error('操作失败，请重试')
  } finally {
    actionLoading.value = false
  }
}

// 提交转交
async function submitTransfer() {
  if (!actionTask.value || !transferForm.target_user_id) {
    message.warning('请输入目标用户 ID')
    return
  }
  
  transferLoading.value = true
  try {
    const payload: TaskTransferRequest = {
      target_user_id: transferForm.target_user_id,
      message: transferForm.message || undefined
    }
    await transferTask(actionTask.value.id, payload)
    message.success('转交成功')
    transferModalVisible.value = false
    transferForm.target_user_id = null
    transferForm.message = ''
    loadTasks()
    loadSlaSummary()
  } catch (error) {
    console.error('转交失败:', error)
    message.error('转交失败，请重试')
  } finally {
    transferLoading.value = false
  }
}

// ========== 表格列定义 ==========

const columns: DataTableColumns<TaskResponse> = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '流程名称',
    key: 'flow_name',
    minWidth: 160,
    ellipsis: { tooltip: true },
    render(row) {
      return row.flow_name || '—'
    }
  },
  {
    title: '节点名称',
    key: 'node_name',
    minWidth: 120,
    render(row) {
      return row.node_name || '—'
    }
  },
  {
    title: '提交人',
    key: 'submitter_name',
    minWidth: 100,
    render(row) {
      return row.submitter_name || '—'
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      return h(
        NTag,
        { type: statusTagType(row.status, row.is_overdue), size: 'small', bordered: false },
        { default: () => statusLabel(row.status, row.is_overdue) }
      )
    }
  },
  {
    title: 'SLA',
    key: 'sla_level',
    width: 80,
    render(row) {
      const slaLevel = row.sla_level
      if (!slaLevel || slaLevel === 'unknown') {
        return h(NTag, { size: 'tiny', type: 'default', bordered: false }, { default: () => '未知' })
      }
      const slaMap: Record<string, { type: 'success' | 'warning' | 'error', label: string }> = {
        normal: { type: 'success', label: '正常' },
        warning: { type: 'warning', label: '预警' },
        critical: { type: 'warning', label: '紧急' },
        expired: { type: 'error', label: '超时' }
      }
      const config = slaMap[slaLevel] || { type: 'default', label: slaLevel }
      return h(NTag, { size: 'tiny', type: config.type, bordered: false }, { default: () => config.label })
    }
  },
  {
    title: '截止时间',
    key: 'due_at',
    width: 160,
    render(row) {
      return formatDate(row.due_at)
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 160,
    render(row) {
      return formatDate(row.created_at)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 320,
    fixed: 'right',
    render(row) {
      const buttons: ReturnType<typeof h>[] = []
      
      // 查看详情按钮
      buttons.push(
        h(NButton, { text: true, type: 'info', size: 'small', onClick: () => handleViewDetail(row) }, { default: () => '详情' })
      )
      
      if (row.status === 'open') {
        // 待认领状态：显示认领按钮
        buttons.push(
          h(NButton, { text: true, type: 'primary', size: 'small', onClick: () => handleClaim(row) }, { default: () => '认领' })
        )
      } else if (row.status === 'claimed') {
        // 已认领状态：显示审批操作按钮和释放按钮
        buttons.push(
          h(NButton, { text: true, type: 'success', size: 'small', onClick: () => openActionModal(row, 'approve') }, { default: () => '通过' })
        )
        buttons.push(
          h(NButton, { text: true, type: 'error', size: 'small', onClick: () => openActionModal(row, 'reject') }, { default: () => '驳回' })
        )
        buttons.push(
          h(NButton, { text: true, size: 'small', onClick: () => openTransferModal(row) }, { default: () => '转交' })
        )
        buttons.push(
          h(NButton, { text: true, type: 'warning', size: 'small', onClick: () => handleRelease(row) }, { default: () => '释放' })
        )
      }
      
      return h(NSpace, { size: 'small', wrap: true }, { default: () => buttons })
    }
  }
]

const groupColumns: DataTableColumns<TaskResponse> = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '流程名称',
    key: 'flow_name',
    minWidth: 160,
    ellipsis: { tooltip: true },
    render(row) {
      return row.flow_name || '—'
    }
  },
  {
    title: '节点名称',
    key: 'node_name',
    minWidth: 120,
    render(row) {
      return row.node_name || '—'
    }
  },
  {
    title: '提交人',
    key: 'submitter_name',
    minWidth: 100,
    render(row) {
      return row.submitter_name || '—'
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render(row) {
      return formatDate(row.created_at)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right',
    render(row) {
      return h(
        'div',
        { style: 'display: flex; gap: 8px;' },
        [
          h(NButton, { text: true, type: 'primary', size: 'small', onClick: () => handleClaim(row) }, { default: () => '认领' }),
          h(NButton, { text: true, type: 'info', size: 'small', onClick: () => handleViewDetail(row) }, { default: () => '详情' })
        ]
      )
    }
  }
]

// ========== 初始化 ==========

onMounted(() => {
  loadTasks()
  loadSlaSummary()
  loadGroupTasks()
})
</script>

<style scoped>
.approval-list-page {
  padding: 16px;
  background: #f5f7fa;
  min-height: 100vh;
}

.summary-card,
.filters-card,
.table-card {
  margin-bottom: 16px;
}

.summary-hint {
  font-size: 12px;
  color: #909399;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.summary-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: center;
}

.summary-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.status-select,
.sla-select {
  width: 120px;
}

.filters-hint {
  margin-top: 12px;
}

.table-footer {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.group-hint {
  font-size: 12px;
  color: #909399;
}

.action-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 审批详情弹窗样式 */
.detail-content {
  display: flex;
  gap: 16px;
  height: 100%;
}

.detail-left {
  width: 320px;
  flex-shrink: 0;
}

.detail-right {
  flex: 1;
  min-width: 0;
}

.info-card,
.form-data-card {
  height: 100%;
}

.info-card :deep(.n-card__content) {
  padding: 0;
}

.form-fields {
  display: flex;
  flex-direction: column;
}

.form-field-item {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.form-field-item:last-child {
  border-bottom: none;
}

.form-field-item:hover {
  background-color: #f8f9fa;
}

.form-field-item.field-alt {
  background-color: #fafbfc;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.field-icon {
  opacity: 0.7;
}

.field-value {
  font-size: 14px;
  color: #303133;
  word-break: break-word;
}

/* 附件样式 */
.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.attachment-item {
  padding: 8px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.image-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.image-preview :deep(.n-image) {
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.download-btn {
  margin-top: 4px;
}

.file-size {
  color: #909399;
  font-size: 12px;
  margin-left: 4px;
}

/* 日期标签 */
.date-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* 选项标签 */
.select-tag {
  font-weight: 500;
}

/* 数字值 */
.number-value {
  font-family: 'DIN Alternate', 'Helvetica Neue', sans-serif;
  font-size: 16px;
  font-weight: 600;
  color: #409eff;
}

/* 长文本 */
.textarea-value {
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 默认文本 */
.text-value {
  color: #606266;
}

/* 空值 */
.empty-value {
  color: #c0c4cc;
  font-style: italic;
}

@media (max-width: 768px) {
  .summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .detail-content {
    flex-direction: column;
  }
  
  .detail-left {
    width: 100%;
  }
}
</style>
