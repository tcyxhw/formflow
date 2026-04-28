// src/stores/mySubmittedApprovals.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getSubmissionList } from '@/api/submission'
import { getFlowDefinitionDetail } from '@/api/flow'
import { getFormFields } from '@/api/form'
import { getProcessTimeline } from '@/api/approvals'
import { useAuthStore } from '@/stores/auth'
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'
import type { TimelineEntry } from '@/types/approval'

export interface MyApprovalItem {
  id: number
  form_id: number
  form_name: string
  status: string
  process_state: string | null
  created_at: string
  process_instance_id: number | null
  due_at?: string | null
  is_overdue?: boolean
  flow_definition_id?: number | null
}

export interface FlowDiagramNode {
  id: string
  name: string
  type: string
  assignee_type?: string
  status?: 'pending' | 'processing' | 'completed' | 'rejected'
  assignee_name?: string | null
  due_at?: string | null
  is_claimed?: boolean
}

export interface FlowDiagramRoute {
  id?: string | number | null
  from_node_id?: string | number | null
  to_node_id?: string | number | null
  from_node_key?: string | number | null
  to_node_key?: string | number | null
  condition_json?: Record<string, unknown> | string | null
  condition?: Record<string, unknown> | string | null
  is_default?: boolean
  enabled?: boolean
}

export interface ProcessTimelineInfo {
  process_instance_id: number
  state: string
  entries: TimelineEntry[]
}

export const useMySubmittedApprovals = defineStore('mySubmittedApprovals', () => {
  const authStore = useAuthStore()

  // 审批列表
  const approvalList = ref<MyApprovalItem[]>([])

  // 加载状态
  const loading = ref(false)

  // 当前选中的审批
  const selectedApproval = ref<MyApprovalItem | null>(null)

  // 流程图数据（按 process_instance_id 缓存）
  const flowDataMap = ref<Map<number, { nodes: FlowDiagramNode[]; routes: FlowDiagramRoute[]; timeline: ProcessTimelineInfo | null }>>(new Map())
  const flowLoading = ref(false)
  const fieldLabels = ref<Record<string, string>>({})

  // 当前加载的流程实例 ID（用于追踪 reactivity）
  const currentFlowInstanceId = ref<number | null>(null)

  // 获取指定流程实例的流程图数据
  const getFlowData = (processInstanceId: number | null) => {
    if (!processInstanceId) return { nodes: [], routes: [], timeline: null }
    return flowDataMap.value.get(processInstanceId) || { nodes: [], routes: [], timeline: null }
  }

  // 兼容旧引用（供 FlowDiagram 组件使用）
  const flowNodes = computed(() => {
    const pid = currentFlowInstanceId.value
    if (!pid) return []
    return getFlowData(pid).nodes
  })
  const flowRoutes = computed(() => {
    const pid = currentFlowInstanceId.value
    if (!pid) return []
    return getFlowData(pid).routes
  })
  const processTimeline = computed(() => {
    const pid = currentFlowInstanceId.value
    if (!pid) return null
    return getFlowData(pid).timeline
  })

  // 用于取消请求的 AbortController
  let currentFlowRequest: AbortController | null = null

  // 统计信息
  const stats = computed(() => ({
    total: approvalList.value.length,
    running: approvalList.value.filter(a => a.process_state === 'running').length,
    finished: approvalList.value.filter(a => a.process_state === 'finished').length,
    canceled: approvalList.value.filter(a => a.process_state === 'canceled').length
  }))

  // 加载我发起的审批列表
  const loadMyApprovals = async () => {
    if (!authStore.isLoggedIn) return

    loading.value = true
    try {
      const res = await getSubmissionList({
        page: 1,
        page_size: 100,
        submitter_user_id: authStore.userInfo?.id
      })

      // 保留所有提交（包括草稿）
      const items = res.data.items || []
      approvalList.value = items
        .map(item => ({
          id: item.id,
          form_id: item.form_id,
          form_name: item.form_name,
          status: item.status,
          process_state: item.process_state || null,
          created_at: item.created_at,
          process_instance_id: item.process_instance_id || null,
          due_at: item.due_at || null,
          is_overdue: item.is_overdue || false,
          flow_definition_id: (item as any).flow_definition_id || null
        }))
    } catch (error) {
      console.error('加载我的审批失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 加载流程图数据
  const loadFlowDiagram = async (formId: number, processInstanceId: number | null, flowDefinitionId?: number | null) => {
    // 取消之前的请求
    if (currentFlowRequest) {
      currentFlowRequest.abort()
    }
    currentFlowRequest = new AbortController()

    flowLoading.value = true
    fieldLabels.value = {}

    // 设置当前流程实例 ID，触发 computed refs 更新
    if (processInstanceId) {
      currentFlowInstanceId.value = processInstanceId
    }

    try {
      // 获取表单字段标签映射
      try {
        const fieldsRes = await getFormFields(formId)
        if (fieldsRes.data?.fields) {
          const labels: Record<string, string> = {}
          for (const field of fieldsRes.data.fields) {
            if (field.key && field.name) {
              labels[field.key] = field.name
            }
          }
          fieldLabels.value = labels
        }
      } catch (e) {
        console.warn('获取表单字段失败，将使用字段ID显示:', e)
      }
      // 获取流程定义 ID
      let realFlowDefId = flowDefinitionId

      // 如果没有 flow_definition_id，尝试通过表单获取
      if (!realFlowDefId) {
        const { getOrCreateFlowDefinition } = await import('@/api/form')
        const flowDefRes = await getOrCreateFlowDefinition(formId)
        realFlowDefId = flowDefRes.data?.flow_definition_id
      }

      if (!realFlowDefId) {
        console.warn('无法获取流程定义 ID')
        return
      }

      // 并行获取流程定义和流程轨迹
      const [flowRes, timelineRes] = await Promise.all([
        getFlowDefinitionDetail(realFlowDefId).catch((e) => {
          if (e?.message === 'canceled' || e?.code === 'ERR_CANCELED') return null
          throw e
        }),
        processInstanceId ? getProcessTimeline(processInstanceId).catch((e) => {
          if (e?.message === 'canceled' || e?.code === 'ERR_CANCELED') return null
          throw e
        }) : Promise.resolve(null)
      ])

      // 处理流程定义数据
      if (flowRes?.data) {
        const draft = flowRes.data.draft
        const snapshot = flowRes.data.active_snapshot

        let nodes: FlowNodeConfig[] = []
        let routes: FlowRouteConfig[] = []

        // 优先使用草稿，其次使用快照
        if (draft?.nodes && Array.isArray(draft.nodes) && draft?.routes && Array.isArray(draft.routes)) {
          nodes = draft.nodes
          routes = draft.routes
        } else if (snapshot?.rules_payload) {
          const payload = snapshot.rules_payload as any
          nodes = Array.isArray(payload.nodes) ? payload.nodes : []
          routes = Array.isArray(payload.routes) ? payload.routes : []
        }

        // 获取轨迹信息用于标记节点状态
        const timelineEntries = timelineRes?.data?.entries || []

        // 转换节点数据
        const allStatuses: Array<'pending' | 'processing' | 'completed' | 'rejected'> = []
        const computedNodes = nodes.map((node: any, index: number) => {
          const nodeId = String(node.id ?? node.temp_id ?? `node-${index}`)

          // 从轨迹中查找节点状态（兼容 string/number 类型）
          const timelineEntry = timelineEntries.find(
            (e: any) => String(e.node_id) === nodeId || String(e.node_id) === String(node.id) || e.node_name === node.name
          )

          let status: 'pending' | 'processing' | 'completed' | 'rejected' = 'pending'
          let assigneeName: string | null = null
          let dueAt: string | null = null
          let isClaimed = false

          if (timelineEntry) {
            if (timelineEntry.status === 'completed') {
              status = timelineEntry.action === 'reject' ? 'rejected' : 'completed'
            } else if (timelineEntry.status === 'claimed' || timelineEntry.status === 'open') {
              status = 'processing'
              isClaimed = timelineEntry.status === 'claimed'
            }
            assigneeName = timelineEntry.assignee_name ?? timelineEntry.actor_name ?? null
            dueAt = timelineEntry.due_at ?? null
          } else if (node.type === 'start') {
            status = 'completed'
          }
          allStatuses.push(status)

          return {
            id: nodeId,
            name: node.name,
            type: node.type,
            assignee_type: node.assignee_type,
            status,
            assignee_name: assigneeName,
            due_at: dueAt,
            is_claimed: isClaimed
          }
        })

        // 兜底：如果流程运行中但没有节点标记为 processing，将第一个未完成的审批节点标记为进行中
        if (!allStatuses.includes('processing') && processInstanceId && timelineRes?.data?.state === 'running') {
          const firstPendingIdx = computedNodes.findIndex(
            (_n: any, i: number) => allStatuses[i] === 'pending' && computedNodes[i].type !== 'start' && computedNodes[i].type !== 'end'
          )
          if (firstPendingIdx >= 0) {
            computedNodes[firstPendingIdx].status = 'processing'
            allStatuses[firstPendingIdx] = 'processing'
          }
        }

        // 转换路由数据
        const computedRoutes = routes.map((route: any, index: number) => ({
          id: route.id ?? route.temp_id ?? `route-${index}`,
          from_node_id: route.from_node_key,
          to_node_id: route.to_node_key,
          condition_json: route.condition,
          is_default: route.is_default,
          enabled: true
        }))

        // 构建时间线数据
        const computedTimeline: ProcessTimelineInfo | null = timelineRes?.data ? {
          process_instance_id: timelineRes.data.process_instance_id,
          state: timelineRes.data.state,
          entries: timelineRes.data.entries
        } : null

        // 存入 Map（按 process_instance_id 缓存）
        if (processInstanceId) {
          flowDataMap.value.set(processInstanceId, {
            nodes: computedNodes,
            routes: computedRoutes,
            timeline: computedTimeline
          })
        }
      }
    } catch (error: any) {
      // 忽略取消错误
      if (error?.name === 'AbortError' || error?.message === 'canceled' || error?.code === 'ERR_CANCELED') {
        return
      }
      console.error('加载流程图数据失败:', error)
    } finally {
      flowLoading.value = false
      currentFlowRequest = null
    }
  }

  // 选择审批
  const selectApproval = async (approval: MyApprovalItem) => {
    selectedApproval.value = approval
    // 草稿没有流程数据，跳过加载
    if (approval.process_instance_id) {
      await loadFlowDiagram(approval.form_id, approval.process_instance_id, approval.flow_definition_id)
    }
  }

  // 清除选择
  const clearSelection = () => {
    selectedApproval.value = null
    currentFlowInstanceId.value = null
    // 不清除 flowDataMap，数据按 process_instance_id 缓存
  }

  /**
   * 流程状态说明：
   * - running: 进行中 - 审批未到达结束节点且未超时
   * - finished: 已完成 - 到达结束节点
   * - stopped/canceled: 已停止 - 未完成并超时
   * - pending_approval: 暂存待发 - 未发起审批
   */
  // 获取流程状态类型
  const getStateType = (state: string | null, isOverdue?: boolean): 'success' | 'warning' | 'error' | 'info' => {
    if (isOverdue) {
      return 'error' // 超时显示为错误状态
    }
    switch (state) {
      case 'running': return 'info'
      case 'finished': return 'success'
      case 'stopped': return 'error'
      case 'canceled': return 'warning'  // 撤回后显示为警告状态（待提交）
      case 'pending_approval': return 'warning'  // 暂存待发显示为警告状态
      default: return 'info'
    }
  }

  // 获取流程状态文本
  const getStateLabel = (state: string | null, isOverdue?: boolean, status?: string): string => {
    if (status === 'draft') return '待通过'
    if (isOverdue) {
      return '已停止'
    }
    switch (state) {
      case 'running': return '进行中'
      case 'finished': return '已完成'
      case 'stopped': return '已停止'
      case 'canceled': return '待提交'
      case 'pending_approval': return '暂存待发'
      default: return '待提交'
    }
  }

  return {
    approvalList,
    loading,
    selectedApproval,
    stats,
    flowNodes,
    flowRoutes,
    flowLoading,
    fieldLabels,
    processTimeline,
    getFlowData,
    loadMyApprovals,
    loadFlowDiagram,
    selectApproval,
    clearSelection,
    getStateType,
    getStateLabel
  }
})
