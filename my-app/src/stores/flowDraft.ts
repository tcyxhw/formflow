/**
 * 流程草稿配置状态管理
 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type {
  FlowDefinitionDetailResponse,
  FlowDraftResponse,
  FlowDraftSaveRequest,
  FlowNodeConfig,
  FlowNodePosition,
  FlowNodeType,
  FlowRouteConfig,
  FlowSnapshotResponse
} from '@/types/flow'
import {
  getFlowDefinitionDetail,
  publishFlow,
  saveFlowDraft
} from '@/api/flow'

interface DraftLoadResult {
  detail: FlowDefinitionDetailResponse
  draft: FlowDraftResponse | null | undefined
}

interface HistorySnapshot {
  nodes: FlowNodeConfig[]
  routes: FlowRouteConfig[]
  nodesGraph: Record<string, FlowNodePosition>
  selectedNodeKey?: string
  timestamp: number
}

const DEFAULT_NODE_METADATA: () => FlowNodeConfig = () => ({
  name: '新节点',
  type: 'user',
  approve_policy: 'any',
  route_mode: 'exclusive',
  allow_delegate: true,
  auto_approve_enabled: false,
  auto_sample_ratio: 0,
  metadata: {},
  assignee_value: null,
  auto_approve_cond: null,
  auto_reject_cond: null,
  reject_strategy: 'TO_START',
  condition_branches: null,
})

const DEFAULT_NODE_POSITIONS: FlowNodePosition[] = [
  { x: 80, y: 160 },
  { x: 280, y: 160 },
  { x: 480, y: 160 },
  { x: 680, y: 160 }
]

const generateTempId = (): string => {
  return `tmp-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`
}

const getNodeKey = (node: FlowNodeConfig): string => {
  if (node.id) {
    return String(node.id)
  }
  if (!node.temp_id) {
    node.temp_id = generateTempId()
  }
  return node.temp_id
}

const ensurePosition = (
  key: string,
  originGraph: Record<string, FlowNodePosition>
): FlowNodePosition => {
  if (!originGraph[key]) {
    const index = Object.keys(originGraph).length % DEFAULT_NODE_POSITIONS.length
    originGraph[key] = { ...DEFAULT_NODE_POSITIONS[index] }
  }
  return originGraph[key]
}

export const useFlowDraftStore = defineStore('flowDraft', () => {
  const flowDefinitionId = ref<number>()
  const flowName = ref('')
  const version = ref(1)
  const nodes = ref<FlowNodeConfig[]>([])
  const routes = ref<FlowRouteConfig[]>([])
  const nodesGraph = ref<Record<string, FlowNodePosition>>({})
  const snapshots = ref<FlowSnapshotResponse[]>([])
  const lastSnapshotId = ref<number | null>(null)
  const lastSavedAt = ref<string | null>(null)
  const lastPublishedAt = ref<string | null>(null)
  const selectedNodeKey = ref<string>()
  const selectedNodeKeys = ref<Set<string>>(new Set())
  const selectedRouteIndex = ref<number | null>(null)
  const loading = ref(false)
  const saving = ref(false)
  const publishing = ref(false)
  const dirty = ref(false)
  
  // 历史记录栈 - 初始化时创建一个空快照
  const history = ref<HistorySnapshot[]>([{
    nodes: [],
    routes: [],
    nodesGraph: {},
    timestamp: Date.now()
  }])
  const historyIndex = ref(0)
  const maxHistorySize = 50

  const currentNode = computed(() => {
    if (!selectedNodeKey.value) return undefined
    return nodes.value.find(node => getNodeKey(node) === selectedNodeKey.value)
  })

  const currentRoute = computed(() => {
    if (selectedRouteIndex.value === null) return undefined
    return routes.value[selectedRouteIndex.value]
  })

  const nodeOptions = computed(() => {
    return nodes.value.map(node => ({
      label: node.name,
      value: getNodeKey(node)
    }))
  })

  const definitionLoaded = computed(() => Boolean(flowDefinitionId.value))

  const canUndo = computed(() => historyIndex.value > 0)

  const canRedo = computed(() => historyIndex.value < history.value.length - 1)

  const createSnapshot = (): HistorySnapshot => {
    return {
      nodes: JSON.parse(JSON.stringify(nodes.value)),
      routes: JSON.parse(JSON.stringify(routes.value)),
      nodesGraph: JSON.parse(JSON.stringify(nodesGraph.value)),
      selectedNodeKey: selectedNodeKey.value,
      timestamp: Date.now()
    }
  }

  const pushHistory = () => {
    // 如果当前不在历史末尾，删除后续的历史记录
    if (historyIndex.value < history.value.length - 1) {
      history.value = history.value.slice(0, historyIndex.value + 1)
    }
    
    // 添加新的快照
    const snapshot = createSnapshot()
    history.value.push(snapshot)
    historyIndex.value = history.value.length - 1
    
    // 限制历史记录大小
    if (history.value.length > maxHistorySize) {
      history.value.shift()
      historyIndex.value -= 1
    }
  }

  const undo = () => {
    if (!canUndo.value) return
    historyIndex.value -= 1
    const snapshot = history.value[historyIndex.value]
    if (snapshot) {
      nodes.value = JSON.parse(JSON.stringify(snapshot.nodes))
      routes.value = JSON.parse(JSON.stringify(snapshot.routes))
      nodesGraph.value = JSON.parse(JSON.stringify(snapshot.nodesGraph))
      selectedNodeKey.value = snapshot.selectedNodeKey
    }
  }

  const redo = () => {
    if (!canRedo.value) return
    historyIndex.value += 1
    const snapshot = history.value[historyIndex.value]
    if (snapshot) {
      nodes.value = JSON.parse(JSON.stringify(snapshot.nodes))
      routes.value = JSON.parse(JSON.stringify(snapshot.routes))
      nodesGraph.value = JSON.parse(JSON.stringify(snapshot.nodesGraph))
      selectedNodeKey.value = snapshot.selectedNodeKey
    }
  }

  const setDirty = () => {
    dirty.value = true
    pushHistory()
  }

  const selectNodeByKey = (key?: string) => {
    selectedNodeKey.value = key

    // 联动 selectedRouteIndex：切换节点时自动选中该节点关联的路由
    if (!key) {
      selectedRouteIndex.value = null
      return
    }

    // 只选中归属于该节点的路由（来源节点是该节点的路由）
    const outIndex = routes.value.findIndex(r => r.from_node_key === key)
    if (outIndex !== -1) {
      selectedRouteIndex.value = outIndex
      return
    }

    // 该节点没有归属路由，不自动选中任何路由
    selectedRouteIndex.value = null
  }

  const selectRouteByIndex = (index?: number | null) => {
    if (typeof index !== 'number' || index < 0 || index >= routes.value.length) {
      selectedRouteIndex.value = null
      return
    }
    selectedRouteIndex.value = index
    
    // 联动节点选择：选中路由时自动跳转到归属节点（来源节点）
    const route = routes.value[index]
    if (route && route.from_node_key) {
      selectedNodeKey.value = route.from_node_key
    }
  }

  const toggleNodeSelection = (key: string, multiSelect: boolean = false) => {
    if (multiSelect) {
      if (selectedNodeKeys.value.has(key)) {
        selectedNodeKeys.value.delete(key)
      } else {
        selectedNodeKeys.value.add(key)
      }
    } else {
      selectedNodeKeys.value.clear()
      selectedNodeKeys.value.add(key)
    }
    selectedNodeKey.value = key
  }

  const clearNodeSelection = () => {
    selectedNodeKeys.value.clear()
    selectedNodeKey.value = undefined
  }

  const isNodeSelected = (key: string): boolean => {
    return selectedNodeKeys.value.has(key)
  }

  const getSelectedNodeKeys = (): string[] => {
    return Array.from(selectedNodeKeys.value)
  }

  const hydrateNodes = (draftNodes: FlowNodeConfig[], graph: Record<string, FlowNodePosition>) => {
    const filledGraph: Record<string, FlowNodePosition> = { ...graph }
    nodes.value = draftNodes.map(node => {
      const hydrated = {
        ...node,
        metadata: node.metadata || {},
        assignee_value: node.assignee_value ?? null,
        auto_approve_cond: node.auto_approve_cond ?? null,
        auto_reject_cond: node.auto_reject_cond ?? null,
      }
      const nodeKey = getNodeKey(hydrated)
      ensurePosition(nodeKey, filledGraph)
      return hydrated
    })
    nodesGraph.value = filledGraph
  }

  const hydrateRoutes = (draftRoutes: FlowRouteConfig[]) => {
    routes.value = draftRoutes.map(route => ({
      ...route,
      condition: route.condition ?? null,
    }))
    if (routes.value.length > 0) {
      selectedRouteIndex.value = 0
    } else {
      selectedRouteIndex.value = null
    }
  }

  const selectFirstNode = () => {
    if (nodes.value.length === 0) {
      selectedNodeKey.value = undefined
      return
    }
    selectedNodeKey.value = getNodeKey(nodes.value[0])
  }

  const buildDefaultDraft = () => {
    const startNode: FlowNodeConfig = {
      ...DEFAULT_NODE_METADATA(),
      name: '开始节点',
      type: 'start',
      allow_delegate: false,
      auto_approve_enabled: false,
    }
    const approveNode: FlowNodeConfig = {
      ...DEFAULT_NODE_METADATA(),
      name: '审批节点',
      type: 'user',
    }
    const endNode: FlowNodeConfig = {
      ...DEFAULT_NODE_METADATA(),
      name: '结束节点',
      type: 'end',
      allow_delegate: false,
    }
    hydrateNodes([startNode, approveNode, endNode], {})
    routes.value = [
      {
        from_node_key: getNodeKey(startNode),
        to_node_key: getNodeKey(approveNode),
        is_default: true,
        priority: 1,
      },
      {
        from_node_key: getNodeKey(approveNode),
        to_node_key: getNodeKey(endNode),
        is_default: true,
        priority: 1,
      }
    ]
    version.value = 1
    nodes.value.forEach((node, index) => {
      const key = getNodeKey(node)
      nodesGraph.value[key] = DEFAULT_NODE_POSITIONS[index] || { x: 100 + index * 140, y: 200 }
    })
    selectFirstNode()
  }

  const applyDraftData = (draft: FlowDraftResponse | null | undefined) => {
    if (draft) {
      version.value = draft.version
      hydrateNodes(draft.nodes, draft.nodes_graph || {})
      hydrateRoutes(draft.routes)
      lastSnapshotId.value = draft.last_snapshot_id ?? null
      selectedNodeKey.value = getNodeKey(draft.nodes[0])
      dirty.value = false
      // 初始化历史记录
      history.value = [createSnapshot()]
      historyIndex.value = 0
      return
    }
    buildDefaultDraft()
    dirty.value = true
    // 初始化历史记录
    history.value = [createSnapshot()]
    historyIndex.value = 0
  }

  const loadDefinition = async (definitionId: number): Promise<DraftLoadResult> => {
    loading.value = true
    try {
      const response = await getFlowDefinitionDetail(definitionId)
      const detail = response.data
      flowDefinitionId.value = detail.definition.id
      flowName.value = detail.definition.name
      snapshots.value = detail.snapshots || []
      applyDraftData(detail.draft)
      return { detail, draft: detail.draft }
    } finally {
      loading.value = false
    }
  }

  const ensureDefinitionReady = () => {
    if (!flowDefinitionId.value) {
      throw new Error('请先加载流程定义')
    }
  }

  const validateJsonLogic = (expression: unknown): boolean => {
    if (!expression) return true
    if (typeof expression !== 'object') return false
    return true
  }

  const validateNodeBeforeSave = (node: FlowNodeConfig) => {
    if (!validateJsonLogic(node.auto_approve_cond)) {
      throw new Error(`${node.name} 自动通过条件格式错误`)
    }
    if (!validateJsonLogic(node.auto_reject_cond)) {
      throw new Error(`${node.name} 自动驳回条件格式错误`)
    }
  }

  const buildPayload = (): FlowDraftSaveRequest => {
    ensureDefinitionReady()
    nodes.value.forEach(validateNodeBeforeSave)
    return {
      flow_definition_id: flowDefinitionId.value!,
      version: version.value,
      nodes: nodes.value.map(node => ({
        ...node,
        metadata: node.metadata || {},
      })),
      routes: routes.value.map(route => ({
        ...route,
      })),
      nodes_graph: { ...nodesGraph.value },
    }
  }

  const saveDraftRemote = async () => {
    ensureDefinitionReady()
    saving.value = true
    try {
      const payload = buildPayload()
      const { data } = await saveFlowDraft(flowDefinitionId.value!, payload)
      version.value = data.version
      hydrateNodes(data.nodes, data.nodes_graph || {})
      hydrateRoutes(data.routes)
      lastSnapshotId.value = data.last_snapshot_id ?? null
      lastSavedAt.value = new Date().toISOString()
      dirty.value = false
      return data
    } finally {
      saving.value = false
    }
  }

  const publishCurrentDraft = async (options?: { changelog?: string; versionTag?: string }) => {
    ensureDefinitionReady()
    publishing.value = true
    try {
      // 发布前先保存草稿，确保服务端版本与前端一致，避免乐观锁冲突
      if (dirty.value) {
        await saveDraftRemote()
      }

      const payload = buildPayload()
      const snapshot = await publishFlow(flowDefinitionId.value!, {
        flow_definition_id: payload.flow_definition_id,
        version: payload.version,
        changelog: options?.changelog,
        version_tag: options?.versionTag,
      })
      dirty.value = false
      lastPublishedAt.value = new Date().toISOString()
      return snapshot.data
    } finally {
      publishing.value = false
    }
  }

  const addNode = (type: FlowNodeType) => {
    const base = DEFAULT_NODE_METADATA()
    const node: FlowNodeConfig = {
      ...base,
      type,
    }
    const key = getNodeKey(node)
    nodes.value.push(node)
    nodesGraph.value[key] = ensurePosition(key, nodesGraph.value)
    selectedNodeKey.value = key
    setDirty()
  }

  const updateNode = (nodeKey: string, patch: Partial<FlowNodeConfig>) => {
    const target = nodes.value.find(node => getNodeKey(node) === nodeKey)
    if (!target) return
    Object.assign(target, patch)
    validateNodeBeforeSave(target)
    setDirty()
  }

  const removeNode = (nodeKey: string) => {
    const index = nodes.value.findIndex(node => getNodeKey(node) === nodeKey)
    if (index === -1) return
    nodes.value.splice(index, 1)
    delete nodesGraph.value[nodeKey]
    routes.value = routes.value.filter(route => route.from_node_key !== nodeKey && route.to_node_key !== nodeKey)
    if (selectedNodeKey.value === nodeKey) {
      selectFirstNode()
    }
    if (routes.value.length === 0) {
      selectedRouteIndex.value = null
    }
    setDirty()
  }

  const addRoute = (route: FlowRouteConfig) => {
    routes.value.push({
      ...route,
      condition: route.condition ?? null,
    })
    selectedRouteIndex.value = routes.value.length - 1
    setDirty()
  }

  const updateRoute = (index: number, patch: Partial<FlowRouteConfig>) => {
    if (!routes.value[index]) return
    routes.value[index] = {
      ...routes.value[index],
      ...patch,
    }
    setDirty()
  }

  const removeRoute = (index: number) => {
    if (!routes.value[index]) return
    routes.value.splice(index, 1)
    if (selectedRouteIndex.value !== null) {
      if (selectedRouteIndex.value === index) {
        selectedRouteIndex.value = null
      } else if (selectedRouteIndex.value > index) {
        selectedRouteIndex.value -= 1
      }
    }
    setDirty()
  }

  const updateNodePosition = (nodeKey: string, position: FlowNodePosition) => {
    nodesGraph.value[nodeKey] = position
    setDirty()
  }

  return {
    flowDefinitionId,
    flowName,
    version,
    nodes,
    routes,
    nodesGraph,
    snapshots,
    lastSnapshotId,
    lastSavedAt,
    lastPublishedAt,
    selectedNodeKey,
    selectedNodeKeys,
    selectedRouteIndex,
    loading,
    saving,
    publishing,
    dirty,
    history,
    historyIndex,
    currentNode,
    nodeOptions,
    currentRoute,
    definitionLoaded,
    canUndo,
    canRedo,
    loadDefinition,
    saveDraftRemote,
    publishCurrentDraft,
    addNode,
    updateNode,
    removeNode,
    addRoute,
    updateRoute,
    removeRoute,
    updateNodePosition,
    setDirty,
    selectFirstNode,
    selectNodeByKey,
    selectRouteByIndex,
    toggleNodeSelection,
    clearNodeSelection,
    isNodeSelected,
    getSelectedNodeKeys,
    buildPayload,
    undo,
    redo,
    pushHistory,
  }
})
