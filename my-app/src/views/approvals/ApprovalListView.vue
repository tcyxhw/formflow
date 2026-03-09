<!-- src/views/approvals/ApprovalListView.vue -->
<template>
  <div class="approval-list-page">
    <n-page-header title="审批控制台" subtitle="待办优先级与轨迹一览" />

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

    <n-drawer v-model:show="timelineVisible" placement="right" :width="420">
      <n-drawer-content :title="timelineTitle">
        <div class="timeline-header">
          <n-tag size="small" :type="currentTimelineStateTag">
            {{ currentTimelineStateLabel }}
          </n-tag>
          <SlaBadge :level="latestTimelineEntry?.sla_level" :minutes="latestTimelineRemaining" :show-remaining="true" />
        </div>
        <n-spin :show="timelineLoading">
          <n-result v-if="timelineError" status="error" title="轨迹加载失败" :description="timelineError">
            <template #footer>
              <n-button size="small" type="primary" :disabled="!lastTimelineTask" @click="handleReloadTimeline">
                重新加载
              </n-button>
            </template>
          </n-result>
          <n-empty v-else-if="!timelineEntries.length" description="暂无轨迹记录" />
          <n-timeline v-else size="large">
            <n-timeline-item
              v-for="(entry, idx) in timelineEntries"
              :key="timelineEntryKey(entry, idx)"
              :title="entry.node_name || '节点'"
              :time="formatDate(entry.started_at)"
              :type="timelineType(entry)"
            >
              <div class="timeline-item">
                <div class="timeline-meta">
                  <span>状态：{{ statusLabel(entry.status) }}</span>
                  <span>当前操作：{{ actionLabel(entry.action) }}</span>
                  <span>执行人：{{ formatActor(entry.actor_user_id, entry.actor_name) }}</span>
                </div>
                <div class="timeline-meta">
                  <span>截止：{{ formatDate(entry.due_at) || '—' }}</span>
                  <SlaBadge :level="entry.sla_level" :minutes="entry.remaining_sla_minutes" :show-remaining="true" />
                </div>
                <p v-if="entry.comment" class="timeline-comment">{{ entry.comment }}</p>
                <n-collapse v-if="entry.actions?.length">
                  <n-collapse-item :title="`操作记录 (${entry.actions.length})`" :name="`actions-${idx}`">
                    <n-timeline size="medium">
                      <n-timeline-item
                        v-for="(action, actionIdx) in entry.actions"
                        :key="`${entry.task_id || entry.node_id}-${actionIdx}`"
                        :time="formatDate(action.created_at)"
                        :type="timelineActionType(action)"
                      >
                        <div class="timeline-meta">
                          <span>操作：{{ actionLabel(action.action) }}</span>
                          <span>执行人：{{ formatActor(action.actor_user_id, action.actor_name) }}</span>
                        </div>
                        <p v-if="action.comment" class="timeline-comment">{{ action.comment }}</p>
                      </n-timeline-item>
                    </n-timeline>
                  </n-collapse-item>
                </n-collapse>
              </div>
            </n-timeline-item>
          </n-timeline>
        </n-spin>
      </n-drawer-content>
    </n-drawer>

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

    <n-modal v-model:show="delegateModalVisible" preset="dialog" title="任务委托">
      <div class="action-form">
        <n-input-number
          v-model:value="delegateForm.delegate_user_id"
          placeholder="输入受托人用户 ID"
          :min="1"
        />
        <n-input-number
          v-model:value="delegateForm.expire_hours"
          placeholder="委托时长（小时，可选）"
          :min="1"
        />
        <n-input v-model:value="delegateForm.message" placeholder="委托说明（可选）" />
        <div class="action-buttons">
          <n-button @click="delegateModalVisible = false">取消</n-button>
          <n-button type="primary" :loading="delegateLoading" @click="submitDelegate">
            确认委托
          </n-button>
        </div>
      </div>
    </n-modal>

    <n-modal v-model:show="addSignModalVisible" preset="dialog" title="添加加签处理人">
      <div class="action-form">
        <n-input
          v-model:value="addSignForm.userIdsInput"
          placeholder="输入用户 ID，使用逗号分隔"
        />
        <n-input v-model:value="addSignForm.message" placeholder="加签说明（可选）" />
        <div class="action-buttons">
          <n-button @click="addSignModalVisible = false">取消</n-button>
          <n-button type="primary" :loading="addSignLoading" @click="submitAddSign">
            创建加签任务
          </n-button>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from 'vue'
import dayjs from 'dayjs'
import type { DataTableColumns } from 'naive-ui'
import { NButton, NTag, useMessage } from 'naive-ui'
import SlaBadge from '@/components/common/SlaBadge.vue'

import type {
  ProcessTimelineResponse,
  TaskActionRequest,
  TaskListQuery,
  TaskResponse,
  TaskSlaSummary,
  TaskStatus,
  TimelineAction,
  TimelineEntry
} from '@/types/approval'
import type { SlaLevel } from '@/types/approval'

import {
  claimTask,
  getProcessTimeline,
  getTaskSlaSummary,
  listGroupTasks,
  listTasks,
  addSignTask,
  delegateTask,
  performTaskAction,
  releaseTask,
  transferTask
} from '@/api/approvals'

import { formatActionLabel, formatActorLabel, timelineActionTag } from '@/utils/audit'
import { formatProcessState, processStateTag } from '@/utils/sla'

interface PaginationState {
  page: number
  pageSize: number
  total: number
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
  status: 'open',
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
const delegateModalVisible = ref(false)
const delegateLoading = ref(false)
const addSignModalVisible = ref(false)
const addSignLoading = ref(false)

const timelineVisible = ref(false)
const timelineData = ref<ProcessTimelineResponse | null>(null)
const timelineLoading = ref(false)
const timelineError = ref<string | null>(null)
const lastTimelineTask = ref<TaskResponse | null>(null)

const transferForm = reactive({
  target_user_id: null as number | null,
  message: ''
})

const delegateForm = reactive({
  delegate_user_id: null as number | null,
  expire_hours: null as number | null,
  message: ''
})

const addSignForm = reactive({
  userIdsInput: '',
  message: ''
})

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
    { key: 'expired', label: '已超时', value: summary?.expired ?? 0, level: 'expired' },
    { key: 'unknown', label: '无截止', value: summary?.unknown ?? 0, level: 'unknown' }
  ]
})

const rowKey = (row: TaskResponse) => row.id.toString()

const actionTitle = computed(() =>
  actionIntent.value === 'approve' ? '通过审批' : '驳回审批'
)

const timelineTitle = computed(() =>
  timelineData.value ? `流程轨迹 - #${timelineData.value.process_instance_id}` : '流程轨迹'
)

const timelineEntries = computed<TimelineEntry[]>(() => timelineData.value?.entries || [])

const latestTimelineEntry = computed(() => {
  const list = timelineEntries.value
  if (!list.length) return null
  return list[list.length - 1]
})

const latestTimelineRemaining = computed(() => latestTimelineEntry.value?.remaining_sla_minutes ?? null)

const currentTimelineStateLabel = computed(() =>
  formatProcessState(timelineData.value?.state || lastTimelineTask.value?.process_state)
)

const currentTimelineStateTag = computed(() =>
  processStateTag(timelineData.value?.state || lastTimelineTask.value?.process_state)
)

function timelineEntryKey(entry: { task_id?: number | null; node_id?: number | null }, index: number) {
  if (entry.task_id !== null && entry.task_id !== undefined) {
    return `task-${entry.task_id}`
  }
  if (entry.node_id !== null && entry.node_id !== undefined) {
    return `node-${entry.node_id}-${index}`
  }
  return `timeline-${index}`
}

const columns = computed<DataTableColumns<TaskResponse>>(() => {
  return [
    {
      title: '节点/流程',
      key: 'node_name',
      render: (row) =>
        h('div', { class: 'cell-title' }, [
          h('div', row.node_name || '未命名节点'),
          h('small', { class: 'cell-desc' }, row.flow_name || '—')
        ])
    },
    {
      title: '流程状态',
      key: 'process_state',
      width: 130,
      render: (row) =>
        h(
          NTag,
          { type: processStateTag(row.process_state), bordered: false },
          { default: () => formatProcessState(row.process_state) }
        )
    },
    {
      title: '任务状态',
      key: 'status',
      width: 120,
      render: (row) =>
        h(
          NTag,
          { type: statusTagType(row.status), bordered: false },
          { default: () => statusLabel(row.status) }
        )
    },
    {
      title: '截止时间',
      key: 'due_at',
      width: 160,
      render: (row) => formatDate(row.due_at) || '—'
    },
    {
      title: '剩余 SLA',
      key: 'remaining_sla_minutes',
      width: 180,
      render: (row) =>
        h(
          SlaBadge,
          {
            level: row.sla_level,
            minutes: row.remaining_sla_minutes,
            showRemaining: true
          }
        )
    },
    {
      title: '操作',
      key: 'actions',
      width: 260,
      render: (row) =>
        h('div', { class: 'table-actions' }, [
          h(
            NButton,
            { size: 'small', tertiary: true, onClick: () => openTimeline(row) },
            { default: () => '轨迹' }
          ),
          row.status === 'open'
            ? h(
                NButton,
                { size: 'small', onClick: () => handleClaim(row) },
                { default: () => '认领' }
              )
            : null,
          row.status === 'claimed' && row.claimed_by
            ? h(
                NButton,
                { size: 'small', tertiary: true, onClick: () => handleRelease(row) },
                { default: () => '释放' }
              )
            : null,
          row.status !== 'completed'
            ? h(
                NButton,
                {
                  size: 'small',
                  type: 'primary',
                  onClick: () => openActionModal(row, 'approve')
                },
                { default: () => '通过' }
              )
            : null,
          row.status !== 'completed'
            ? h(
                NButton,
                {
                  size: 'small',
                  type: 'error',
                  ghost: true,
                  onClick: () => openActionModal(row, 'reject')
                },
                { default: () => '驳回' }
              )
            : null,
          row.status !== 'completed'
            ? h(
                NButton,
                {
                  size: 'small',
                  tertiary: true,
                  onClick: () => openTransferModal(row)
                },
                { default: () => '转交' }
              )
            : null,
          row.status !== 'completed'
            ? h(
                NButton,
                {
                  size: 'small',
                  tertiary: true,
                  onClick: () => openDelegateModal(row)
                },
                { default: () => '委托' }
              )
            : null,
          row.status !== 'completed'
            ? h(
                NButton,
                {
                  size: 'small',
                  tertiary: true,
                  onClick: () => openAddSignModal(row)
                },
                { default: () => '加签' }
              )
            : null
        ])
    }
  ]
})

const groupColumns = computed<DataTableColumns<TaskResponse>>(() => {
  return [
    {
      title: '节点/流程',
      key: 'node_name',
      render: (row) =>
        h('div', { class: 'cell-title' }, [
          h('div', row.node_name || '未命名节点'),
          h('small', { class: 'cell-desc' }, row.flow_name || '—')
        ])
    },
    {
      title: '截止时间',
      key: 'due_at',
      width: 160,
      render: (row) => formatDate(row.due_at) || '—'
    },
    {
      title: 'SLA(小时)',
      key: 'sla_hours',
      width: 100,
      render: (row) => row.sla_hours ?? '—'
    },
    {
      title: '操作',
      key: 'group_actions',
      width: 200,
      render: (row) =>
        h('div', { class: 'table-actions' }, [
          h(
            NButton,
            { size: 'small', tertiary: true, onClick: () => openTimeline(row) },
            { default: () => '轨迹' }
          ),
          h(
            NButton,
            { size: 'small', type: 'primary', onClick: () => handleClaim(row) },
            { default: () => '认领' }
          )
        ])
    }
  ]
})

function statusTagType(status: TaskStatus) {
  switch (status) {
    case 'open':
      return 'warning'
    case 'claimed':
      return 'info'
    case 'completed':
      return 'success'
    case 'canceled':
      return 'default'
    default:
      return 'default'
  }
}

function statusLabel(status?: TaskStatus | null) {
  const map: Record<string, string> = {
    open: '待认领',
    claimed: '处理中',
    completed: '已完成',
    canceled: '已取消'
  }
  return status ? map[status] : '—'
}

function formatDate(value?: string | null) {
  if (!value) return ''
  return dayjs(value).format('YYYY-MM-DD HH:mm')
}

function timelineType(entry: { status?: TaskStatus | null }) {
  if (!entry.status) return 'default'
  if (entry.status === 'completed') return 'success'
  if (entry.status === 'canceled') return 'warning'
  return 'info'
}

function actionLabel(action?: string | null) {
  return formatActionLabel(action, '—')
}

function formatActor(userId?: number | null, actorName?: string | null) {
  return formatActorLabel(userId, actorName)
}

function timelineActionType(action: TimelineAction): 'default' | 'success' | 'error' | 'info' | 'warning' {
  return timelineActionTag(action.action)
}

async function fetchTasks() {
  loading.value = true
  try {
    const params: TaskListQuery = {
      ...filters,
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      sla_level: filters.sla_level || undefined
    }
    const response = await listTasks(params)
    if (response.data) {
      tasks.value = response.data.items
      pagination.total = response.data.total
    }
  } catch (error) {
    console.error(error)
    message.error('加载任务失败')
  } finally {
    loading.value = false
  }
}

async function fetchGroupTasks() {
  if (!filters.include_group_tasks) {
    groupTasks.value = []
    groupPagination.total = 0
    return
  }
  groupLoading.value = true
  try {
    const response = await listGroupTasks({
      page: groupPagination.page,
      page_size: groupPagination.pageSize
    })
    if (response.data) {
      groupTasks.value = response.data.items
      groupPagination.total = response.data.total
    }
  } catch (error) {
    console.error(error)
    message.error('加载小组任务失败')
  } finally {
    groupLoading.value = false
  }
}

function handlePageChange(page: number) {
  pagination.page = page
  fetchTasks()
}

function handlePageSizeChange(size: number) {
  pagination.pageSize = size
  pagination.page = 1
  fetchTasks()
}

function handleSearch() {
  pagination.page = 1
  refreshTasksAndSummary()
}

function handleGroupPageChange(page: number) {
  groupPagination.page = page
  fetchGroupTasks()
}

function handleGroupPageSizeChange(size: number) {
  groupPagination.pageSize = size
  groupPagination.page = 1
  fetchGroupTasks()
}

function handleReset() {
  filters.keyword = ''
  filters.status = null
  filters.only_mine = true
  filters.include_group_tasks = true
  pagination.page = 1
  pagination.pageSize = 10
  refreshTasksAndSummary()
  fetchGroupTasks()
}

function handleImmediateFilter() {
  pagination.page = 1
  refreshTasksAndSummary()
  fetchGroupTasks()
}

async function refreshTasksAndSummary() {
  await Promise.all([fetchTasks(), fetchSlaSummary()])
}

async function fetchSlaSummary() {
  summaryLoading.value = true
  try {
    const params: TaskListQuery = {
      status: filters.status || undefined,
      only_mine: filters.only_mine,
      include_group_tasks: filters.include_group_tasks,
      keyword: filters.keyword || undefined,
      sla_level: filters.sla_level || undefined
    }
    const response = await getTaskSlaSummary(params)
    slaSummary.value = response.data ?? null
  } catch (error) {
    console.error(error)
    message.error('加载 SLA 汇总失败')
    slaSummary.value = null
  } finally {
    summaryLoading.value = false
  }
}

async function handleClaim(row: TaskResponse) {
  try {
    await claimTask(row.id)
    message.success('任务认领成功')
    refreshTasksAndSummary()
    fetchGroupTasks()
  } catch (error) {
    console.error(error)
    message.error('认领失败')
  }
}

async function handleRelease(row: TaskResponse) {
  try {
    await releaseTask(row.id)
    message.success('任务已释放')
    refreshTasksAndSummary()
    fetchGroupTasks()
  } catch (error) {
    console.error(error)
    message.error('释放失败')
  }
}

function openActionModal(row: TaskResponse, intent: 'approve' | 'reject') {
  actionTask.value = row
  actionIntent.value = intent
  actionComment.value = ''
  actionModalVisible.value = true
}

function openTransferModal(row: TaskResponse) {
  if (row.status === 'completed') {
    message.warning('已完成任务无法转交')
    return
  }
  actionTask.value = row
  transferForm.target_user_id = null
  transferForm.message = ''
  transferModalVisible.value = true
}

function openDelegateModal(row: TaskResponse) {
  if (row.status === 'completed') {
    message.warning('已完成任务无法委托')
    return
  }
  actionTask.value = row
  delegateForm.delegate_user_id = null
  delegateForm.expire_hours = null
  delegateForm.message = ''
  delegateModalVisible.value = true
}

function openAddSignModal(row: TaskResponse) {
  if (row.status === 'completed') {
    message.warning('已完成任务无需加签')
    return
  }
  actionTask.value = row
  addSignForm.userIdsInput = ''
  addSignForm.message = ''
  addSignModalVisible.value = true
}

async function submitAction() {
  if (!actionTask.value) return
  actionLoading.value = true
  try {
    const payload: TaskActionRequest = {
      action: actionIntent.value,
      comment: actionComment.value
    }
    await performTaskAction(actionTask.value.id, payload)
    message.success('操作成功')
    actionModalVisible.value = false
    refreshTasksAndSummary()
  } catch (error) {
    console.error(error)
    message.error('操作失败')
  } finally {
    actionLoading.value = false
  }
}

async function submitTransfer() {
  if (!actionTask.value || !transferForm.target_user_id) {
    message.warning('请先输入目标用户 ID')
    return
  }
  transferLoading.value = true
  try {
    await transferTask(actionTask.value.id, {
      target_user_id: transferForm.target_user_id,
      message: transferForm.message || undefined
    })
    message.success('任务已转交')
    transferModalVisible.value = false
    refreshTasksAndSummary()
  } catch (error) {
    console.error(error)
    message.error('转交失败')
  } finally {
    transferLoading.value = false
  }
}

async function submitDelegate() {
  if (!actionTask.value || !delegateForm.delegate_user_id) {
    message.warning('请先输入受托人 ID')
    return
  }
  delegateLoading.value = true
  try {
    await delegateTask(actionTask.value.id, {
      delegate_user_id: delegateForm.delegate_user_id,
      expire_hours: delegateForm.expire_hours || undefined,
      message: delegateForm.message || undefined
    })
    message.success('已创建委托任务')
    delegateModalVisible.value = false
    refreshTasksAndSummary()
  } catch (error) {
    console.error(error)
    message.error('委托失败')
  } finally {
    delegateLoading.value = false
  }
}

async function submitAddSign() {
  if (!actionTask.value) {
    message.warning('请选择任务')
    return
  }
  const userIds = addSignForm.userIdsInput
    .split(',')
    .map((id) => Number(id.trim()))
    .filter((id) => !Number.isNaN(id) && id > 0)
  if (!userIds.length) {
    message.warning('请至少输入一个合法的用户 ID')
    return
  }
  addSignLoading.value = true
  try {
    await addSignTask(actionTask.value.id, {
      user_ids: userIds,
      message: addSignForm.message || undefined
    })
    message.success('加签任务已创建')
    addSignModalVisible.value = false
    refreshTasksAndSummary()
  } catch (error) {
    console.error(error)
    message.error('加签失败')
  } finally {
    addSignLoading.value = false
  }
}

async function openTimeline(row: TaskResponse) {
  lastTimelineTask.value = row
  timelineVisible.value = true
  timelineData.value = null
  timelineError.value = null
  timelineLoading.value = true
  try {
    const response = await getProcessTimeline(row.process_instance_id)
    if (response.code === 200 && response.data) {
      timelineData.value = response.data
    } else {
      timelineError.value = response.message || '获取轨迹失败'
    }
  } catch (error) {
    console.error(error)
    timelineError.value = '获取轨迹失败'
  } finally {
    timelineLoading.value = false
  }
}

function handleReloadTimeline() {
  if (lastTimelineTask.value) {
    openTimeline(lastTimelineTask.value)
  }
}

onMounted(() => {
  refreshTasksAndSummary()
  fetchGroupTasks()
})
</script>

<style scoped>
.approval-list-page {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filters-card,
.table-card {
  border-radius: 12px;
}

.summary-card {
  border-radius: 12px;
}

.summary-hint {
  font-size: 12px;
  color: var(--text-color-3);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.summary-item {
  padding: 12px;
  border-radius: 10px;
  background-color: var(--card-color);
  border: 1px solid var(--divider-color);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-color-2);
}

.summary-value {
  font-size: 26px;
  font-weight: 600;
  color: var(--text-color-1);
}

.group-hint {
  font-size: 13px;
  color: var(--text-color-3);
}

.status-select {
  width: 160px;
}

.table-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.table-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.cell-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cell-desc {
  color: var(--text-color-3);
}

.timeline-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: var(--text-color-2);
}

.action-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>