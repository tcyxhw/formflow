// src/stores/homeApproval.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { listTasks, getTaskSlaSummary } from '@/api/approvals'
import type { TaskResponse, TaskSlaSummary, TaskListQuery } from '@/types/approval'

export const useHomeApproval = defineStore('homeApproval', () => {
  // 待办任务列表
  const pendingTasks = ref<TaskResponse[]>([])
  
  // SLA 概览
  const slaSummary = ref<TaskSlaSummary | null>(null)
  
  // 加载状态
  const loading = ref(false)
  
  // 当前选中的任务
  const selectedTask = ref<TaskResponse | null>(null)

  // 统计信息
  const stats = computed(() => ({
    total: pendingTasks.value.length,
    urgent: pendingTasks.value.filter(t => t.sla_level === 'critical' || t.sla_level === 'expired').length,
    warning: pendingTasks.value.filter(t => t.sla_level === 'warning').length,
    normal: pendingTasks.value.filter(t => t.sla_level === 'normal').length
  }))

  // 加载待办任务
  const loadPendingTasks = async () => {
    loading.value = true
    try {
      const params: TaskListQuery = {
        page: 1,
        page_size: 10,
        status: 'open',
        only_mine: true
      }
      const res = await listTasks(params)
      pendingTasks.value = res.data.items || []
      
      // 加载 SLA 概览
      const slaRes = await getTaskSlaSummary(params)
      slaSummary.value = slaRes.data
    } catch (error) {
      console.error('加载待办任务失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 选择任务
  const selectTask = (task: TaskResponse) => {
    selectedTask.value = task
  }

  // 清除选择
  const clearSelection = () => {
    selectedTask.value = null
  }

  // 获取任务状态标签类型
  const getStatusType = (level: string | null | undefined): 'success' | 'warning' | 'error' | 'info' => {
    switch (level) {
      case 'normal': return 'success'
      case 'warning': return 'warning'
      case 'critical':
      case 'expired': return 'error'
      default: return 'info'
    }
  }

  // 获取状态标签文本
  const getStatusLabel = (level: string | null | undefined): string => {
    switch (level) {
      case 'normal': return '正常'
      case 'warning': return '预警'
      case 'critical': return '紧急'
      case 'expired': return '超时'
      default: return '未知'
    }
  }

  return {
    pendingTasks,
    slaSummary,
    loading,
    selectedTask,
    stats,
    loadPendingTasks,
    selectTask,
    clearSelection,
    getStatusType,
    getStatusLabel
  }
})