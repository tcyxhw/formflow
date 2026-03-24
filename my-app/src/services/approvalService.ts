/**
 * 审批业务逻辑服务
 * 封装任务操作的业务流程和状态管理
 */

import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import { useMessage } from 'naive-ui'
import {
  listTasks,
  claimTask,
  releaseTask,
  performTaskAction,
  transferTask,
  delegateTask,
  addSignTask,
  getProcessTimeline,
  listGroupTasks,
  getTaskSlaSummary,
} from '@/api/approvals'
import type {
  TaskListQuery,
  TaskResponse,
  TaskActionRequest,
  TaskTransferRequest,
  TaskDelegateRequest,
  TaskAddSignRequest,
  ProcessTimelineResponse,
} from '@/types/approval'

export interface UseApprovalServiceOptions {
  /** 自动刷新间隔（毫秒），0表示不自动刷新 */
  autoRefreshInterval?: number
  /** 默认页大小 */
  defaultPageSize?: number
}

export interface TaskFilters {
  keyword?: string
  status?: string
  sla_level?: string
  only_mine?: boolean
  include_group_tasks?: boolean
}

/**
 * 审批服务 Composable
 * 封装任务列表、操作、轨迹等业务逻辑
 */
export function useApprovalService(options: UseApprovalServiceOptions = {}) {
  const message = useMessage()
  const { autoRefreshInterval = 0, defaultPageSize = 20 } = options

  // 状态
  const loading = ref(false)
  const tasks: Ref<TaskResponse[]> = ref([])
  const groupTasks: Ref<TaskResponse[]> = ref([])
  const pagination = ref({
    page: 1,
    pageSize: defaultPageSize,
    total: 0,
  })

  // SLA概览
  const slaSummary = ref<any>(null)
  const summaryLoading = ref(false)

  // 当前选中任务
  const currentTask: Ref<TaskResponse | null> = ref(null)
  const timeline: Ref<ProcessTimelineResponse | null> = ref(null)
  const timelineLoading = ref(false)

  // 操作状态
  const actionLoading = ref(false)

  /**
   * 加载任务列表
   */
  const loadTasks = async (filters: TaskFilters = {}) => {
    loading.value = true
    try {
      const params: TaskListQuery = {
        page: pagination.value.page,
        page_size: pagination.value.pageSize,
        ...filters,
      }

      const { data } = await listTasks(params)
      tasks.value = data?.items || []
      pagination.value.total = data?.total || 0
    } catch (error) {
      message.error('加载任务列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 认领任务（带业务校验）
   */
  const handleClaimTask = async (taskId: number) => {
    actionLoading.value = true
    try {
      // 业务校验：检查任务是否已被认领
      const task = tasks.value.find((t) => t.id === taskId)
      if (task?.status === 'claimed') {
        message.warning('该任务已被认领')
        return false
      }

      await claimTask(taskId)
      message.success('认领成功')

      // 自动刷新列表
      await loadTasks()
      return true
    } catch (error) {
      message.error('认领失败')
      throw error
    } finally {
      actionLoading.value = false
    }
  }

  /**
   * 释放任务回组池
   */
  const handleReleaseTask = async (taskId: number) => {
    actionLoading.value = true
    try {
      await releaseTask(taskId)
      message.success('已释放回组池')
      await loadTasks()
      return true
    } catch (error) {
      message.error('释放失败')
      throw error
    } finally {
      actionLoading.value = false
    }
  }

  /**
   * 执行审批动作（通过/驳回）
   */
  const handlePerformAction = async (
    taskId: number,
    action: 'approve' | 'reject',
    comment?: string,
    payload?: Record<string, any>
  ) => {
    actionLoading.value = true
    try {
      const request: TaskActionRequest = {
        action,
        comment,
        payload,
      }

      await performTaskAction(taskId, request)
      message.success(action === 'approve' ? '已通过' : '已驳回')

      // 刷新任务和轨迹
      await Promise.all([
        loadTasks(),
        currentTask.value?.id === taskId ? loadTimeline(taskId) : Promise.resolve(),
      ])

      return true
    } catch (error) {
      message.error('操作失败')
      throw error
    } finally {
      actionLoading.value = false
    }
  }

  /**
   * 转交任务
   */
  const handleTransferTask = async (
    taskId: number,
    targetUserId: number,
    comment?: string
  ) => {
    actionLoading.value = true
    try {
      const request: TaskTransferRequest = {
        target_user_id: targetUserId,
        comment,
      }

      await transferTask(taskId, request)
      message.success('转交成功')
      await loadTasks()
      return true
    } catch (error) {
      message.error('转交失败')
      throw error
    } finally {
      actionLoading.value = false
    }
  }

  /**
   * 委托任务
   */
  const handleDelegateTask = async (
    taskId: number,
    delegateUserId: number,
    comment?: string
  ) => {
    actionLoading.value = true
    try {
      const request: TaskDelegateRequest = {
        delegate_user_id: delegateUserId,
        comment,
      }

      await delegateTask(taskId, request)
      message.success('委托成功')
      await loadTasks()
      return true
    } catch (error) {
      message.error('委托失败')
      throw error
    } finally {
      actionLoading.value = false
    }
  }

  /**
   * 加签
   */
  const handleAddSignTask = async (
    taskId: number,
    addSignUserIds: number[],
    comment?: string
  ) => {
    actionLoading.value = true
    try {
      const request: TaskAddSignRequest = {
        add_sign_user_ids: addSignUserIds,
        comment,
      }

      await addSignTask(taskId, request)
      message.success('加签成功')
      await loadTasks()
      return true
    } catch (error) {
      message.error('加签失败')
      throw error
    } finally {
      actionLoading.value = false
    }
  }

  /**
   * 加载流程轨迹
   */
  const loadTimeline = async (processInstanceId: number) => {
    timelineLoading.value = true
    try {
      const { data } = await getProcessTimeline(processInstanceId)
      timeline.value = data
    } catch (error) {
      message.error('加载轨迹失败')
      throw error
    } finally {
      timelineLoading.value = false
    }
  }

  /**
   * 加载SLA概览
   */
  const loadSlaSummary = async (filters: TaskFilters = {}) => {
    summaryLoading.value = true
    try {
      const { data } = await getTaskSlaSummary(filters)
      slaSummary.value = data
    } catch (error) {
      console.error('加载SLA概览失败', error)
    } finally {
      summaryLoading.value = false
    }
  }

  /**
   * 加载组任务
   */
  const loadGroupTasks = async () => {
    try {
      const { data } = await listGroupTasks({
        page: 1,
        page_size: 50,
      })
      groupTasks.value = data?.items || []
    } catch (error) {
      console.error('加载组任务失败', error)
    }
  }

  // 自动刷新逻辑
  let refreshTimer: ReturnType<typeof setInterval> | null = null

  const startAutoRefresh = () => {
    if (autoRefreshInterval > 0 && !refreshTimer) {
      refreshTimer = setInterval(() => {
        loadTasks()
        loadSlaSummary()
      }, autoRefreshInterval)
    }
  }

  const stopAutoRefresh = () => {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  // 计算属性
  const hasTasks = computed(() => tasks.value.length > 0)
  const overdueTasks = computed(() =>
    tasks.value.filter((t) => t.sla_level === 'urgent' || t.sla_level === 'overdue')
  )

  return {
    // 状态
    loading,
    actionLoading,
    summaryLoading,
    timelineLoading,
    tasks,
    groupTasks,
    slaSummary,
    timeline,
    currentTask,
    pagination,

    // 计算属性
    hasTasks,
    overdueTasks,

    // 方法
    loadTasks,
    loadGroupTasks,
    loadSlaSummary,
    loadTimeline,
    handleClaimTask,
    handleReleaseTask,
    handlePerformAction,
    handleTransferTask,
    handleDelegateTask,
    handleAddSignTask,
    startAutoRefresh,
    stopAutoRefresh,
  }
}
