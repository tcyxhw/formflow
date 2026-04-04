<template>
  <div class="flow-diagram-wrapper">
    <!-- 工具栏 -->
    <div class="flow-toolbar">
      <div class="toolbar-title">
        <span class="title-icon">📋</span>
        <span class="title-text">审批流程</span>
        <span class="status-badge" :class="flowStatus">{{ flowStatusText }}</span>
      </div>
      <div class="toolbar-actions">
        <button class="toolbar-btn" @click="zoomIn" title="放大">
          <span>+</span>
        </button>
        <button class="toolbar-btn" @click="zoomOut" title="缩小">
          <span>-</span>
        </button>
        <button class="toolbar-btn" @click="fitView" title="适应视图">
          <span>⛶</span>
        </button>
        <button class="toolbar-btn" @click="toggleFullscreen" title="全屏">
          <span>{{ isFullscreen ? '⤓' : '⤢' }}</span>
        </button>
      </div>
    </div>

    <!-- Vue Flow 画布 -->
    <div 
      class="graph-container" 
      :class="{ 'fullscreen': isFullscreen }"
      ref="graphContainerRef"
    >
      <VueFlow
        v-model:nodes="flowNodes"
        v-model:edges="flowEdges"
        fit-view-on-init
        :default-viewport="{ zoom: 1, x: 0, y: 0 }"
        :min-zoom="0.2"
        :max-zoom="4"
        :snap-to-grid="true"
        :snap-grid="[20, 20]"
        :nodes-draggable="!isSpacePressed"
        :nodes-connectable="false"
        :elements-selectable="false"
        :pan-on-drag="isSpacePressed"
        :pan-on-scroll="false"
      >
        <!-- 自定义开始节点 -->
        <template #node-start="{ data }">
          <div class="flow-node start-node" :style="{ '--node-color': data.color }">
            <span class="node-icon">{{ data.icon }}</span>
            <span class="node-label">{{ data.label }}</span>
          </div>
        </template>

        <!-- 自定义结束节点 -->
        <template #node-end="{ data }">
          <div class="flow-node end-node" :style="{ '--node-color': data.color }">
            <span class="node-icon">{{ data.icon }}</span>
            <span class="node-label">{{ data.label }}</span>
          </div>
        </template>

        <!-- 自定义审批节点 -->
        <template #node-approval="{ data }">
          <div class="flow-node approval-node" :style="{ '--node-color': data.color }">
            <div class="node-status-bar"></div>
            <div class="node-content">
              <div class="node-header">
                <span class="node-icon">{{ data.icon }}</span>
                <span class="node-title">{{ data.label }}</span>
                <span v-if="data.status === 'processing'" class="processing-badge">进行中</span>
              </div>
              <div class="node-subtitle">{{ data.typeLabel }}</div>
              <div v-if="data.assignee" class="node-footer">
                👤 {{ data.assignee }}
              </div>
            </div>
            <div v-if="data.status === 'processing'" class="pulse-ring"></div>
          </div>
        </template>

        <!-- 自定义条件节点 -->
        <template #node-condition="{ data }">
          <div class="flow-node condition-node" :style="{ '--node-color': data.color }">
            <div class="diamond-inner">
              <span class="node-icon">{{ data.icon }}</span>
              <span class="node-label">{{ data.label }}</span>
            </div>
          </div>
        </template>

        <!-- 背景 -->
        <Background variant="dots" :gap="20" :size="1" />

        <!-- 小地图 - 调整大小和样式 -->
        <MiniMap
          :node-color="(node) => node.data?.color || '#94a3b8'"
          :node-stroke-width="3"
          :pannable="true"
          :zoomable="true"
          :height="120"
          :width="180"
          :style="{
            background: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
          }"
        />

        <!-- 缩放控件已移除 -->
      </VueFlow>
    </div>

    <!-- 图例 -->
    <div class="flow-legend">
      <div class="legend-title">流程图例</div>
      <div class="legend-items">
        <div class="legend-item">
          <span class="legend-line normal"></span>
          <span>普通连线</span>
        </div>
        <div class="legend-item">
          <span class="legend-line condition"></span>
          <span>条件分支</span>
        </div>
        <div class="legend-item">
          <span class="legend-dot active"></span>
          <span>进行中</span>
        </div>
      </div>
      <div class="legend-hint">
        <span>拖动节点调整位置</span>
        <span class="hint-divider">|</span>
        <span :class="{ 'hint-active': isSpacePressed }">按住空格拖动画布</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { MiniMap } from '@vue-flow/minimap'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

interface FlowNode {
  id?: string | number | null
  temp_id?: string
  name: string
  type: string
  assignee_type?: string
  assignee_value?: string | number | boolean | Record<string, unknown> | unknown[]
  status?: 'pending' | 'processing' | 'completed' | 'rejected'
}

interface FlowRoute {
  id?: string | number | null
  temp_id?: string
  from_node_id?: string | number | null
  to_node_id?: string | number | null
  from_node_key?: string | number | null
  to_node_key?: string | number | null
  priority?: number
  condition_json?: Record<string, unknown> | string | null
  condition?: Record<string, unknown> | string | null
  is_default?: boolean
  enabled?: boolean
}

interface Props {
  nodes: FlowNode[]
  routes: FlowRoute[]
  fieldLabels?: Record<string, string>
}

const props = defineProps<Props>()

const flowStatus = ref('running')
const flowStatusText = ref('运行中')
const isFullscreen = ref(false)
const graphContainerRef = ref<HTMLElement | null>(null)
const isSpacePressed = ref(false)

// 空格键监听 - 按住空格拖动画布，松开拖动节点
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.code === 'Space' && !e.repeat) {
    e.preventDefault()
    isSpacePressed.value = true
  }
}

const handleKeyUp = (e: KeyboardEvent) => {
  if (e.code === 'Space') {
    isSpacePressed.value = false
  }
}

// 全屏切换
const toggleFullscreen = () => {
  if (!graphContainerRef.value) return
  
  if (!isFullscreen.value) {
    // 进入全屏
    if (graphContainerRef.value.requestFullscreen) {
      graphContainerRef.value.requestFullscreen()
    } else if ((graphContainerRef.value as any).webkitRequestFullscreen) {
      (graphContainerRef.value as any).webkitRequestFullscreen()
    }
  } else {
    // 退出全屏
    if (document.exitFullscreen) {
      document.exitFullscreen()
    } else if ((document as any).webkitExitFullscreen) {
      (document as any).webkitExitFullscreen()
    }
  }
}

// 监听全屏状态变化
const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

// Vue Flow 实例
const { zoomIn: vueFlowZoomIn, zoomOut: vueFlowZoomOut, fitView: vueFlowFitView } = useVueFlow()

onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange)
  document.addEventListener('keydown', handleKeyDown)
  document.addEventListener('keyup', handleKeyUp)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('webkitfullscreenchange', handleFullscreenChange)
  document.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('keyup', handleKeyUp)
})

// 获取节点的有效ID
const getNodeId = (node: FlowNode): string | number => {
  return node.id ?? node.temp_id ?? ''
}

// 获取路由的来源和目标节点ID
const getRouteSourceId = (route: FlowRoute): string | number | undefined => {
  const id = route.from_node_id ?? route.from_node_key
  return id !== null ? id : undefined
}

const getRouteTargetId = (route: FlowRoute): string | number | undefined => {
  const id = route.to_node_id ?? route.to_node_key
  return id !== null ? id : undefined
}

// 获取路由的有效ID
const getRouteId = (route: FlowRoute, index: number): string | number => {
  return route.id ?? route.temp_id ?? `route-${index}`
}

// 获取节点状态颜色
const getNodeColor = (type: string, status?: string): string => {
  if (status === 'completed') return '#22c55e'
  if (status === 'rejected') return '#ef4444'
  if (status === 'processing') return '#6366f1'

  const colorMap: Record<string, string> = {
    'start': '#22c55e',
    'end': '#6366f1',
    'user': '#3b82f6',
    'auto': '#f97316',
    'condition': '#f97316'
  }
  return colorMap[type] || '#94a3b8'
}

// 获取节点图标
const getNodeIcon = (type: string): string => {
  const iconMap: Record<string, string> = {
    'start': '▶',
    'end': '■',
    'user': '👤',
    'auto': '⚙',
    'condition': '🔀'
  }
  return iconMap[type] || '●'
}

// 获取指派标签
const getAssigneeLabel = (type: string): string => {
  const typeMap: Record<string, string> = {
    'role': '指定角色',
    'position': '指定岗位',
    'group': '审批组',
    'user': '指定人员',
    'expr': '动态计算'
  }
  return typeMap[type] || type
}

// 获取字段中文标签
const getFieldLabel = (fieldId: string): string => {
  return props.fieldLabels?.[fieldId] || fieldId
}

// 格式化条件（支持 JsonLogic 格式和 RouteRule 格式）
const formatCondition = (condition: Record<string, unknown> | string | null): string => {
  if (!condition) return ''
  if (typeof condition === 'string') return condition

  // 操作符映射
  const opMap: Record<string, string> = {
    '==': '等于', 'eq': '等于', 'equals': '等于',
    '!=': '不等于', 'neq': '不等于', 'not_equals': '不等于',
    '>': '大于', 'gt': '大于',
    '>=': '大于等于', 'gte': '大于等于',
    '<': '小于', 'lt': '小于',
    '<=': '小于等于', 'lte': '小于等于',
    'in': '包含于', 'not_in': '不包含于',
    'contains': '包含', 'not_contains': '不包含',
    'starts_with': '开头是', 'ends_with': '结尾是',
    'is_null': '为空', 'not_null': '不为空',
    'between': '介于', 'has_any': '包含任一', 'has_all': '包含全部',
    'is_empty': '为空', 'is_not_empty': '不为空'
  }

  const formatValue = (value: unknown): string => {
    if (value === null || value === undefined) return '空'
    if (Array.isArray(value)) return value.join(', ')
    if (typeof value === 'object') return JSON.stringify(value)
    return String(value)
  }

  const getOperatorText = (op: string): string => opMap[op] || op

  // 递归解析 JsonLogic 表达式
  const parseJsonLogic = (expr: any, depth: number = 0): string => {
    if (!expr || typeof expr !== 'object') return String(expr)

    // 处理 AND 逻辑组
    if (expr.and) {
      const conditions = Array.isArray(expr.and) ? expr.and : [expr.and]
      const formatted = conditions.map((c: any) => parseJsonLogic(c, depth + 1))
      return formatted.join(' 且 ')
    }

    // 处理 OR 逻辑组
    if (expr.or) {
      const conditions = Array.isArray(expr.or) ? expr.or : [expr.or]
      const formatted = conditions.map((c: any) => parseJsonLogic(c, depth + 1))
      return formatted.join(' 或 ')
    }

    // 处理 NOT 逻辑
    if (expr['!']) {
      const inner = parseJsonLogic(expr['!'], depth + 1)
      return `非(${inner})`
    }

    // 处理二元操作符 (==, !=, >, >=, <, <=)
    const binaryOps = ['==', 'eq', '!=', 'neq', '>', 'gt', '>=', 'gte', '<', 'lt', '<=', 'lte']
    for (const op of binaryOps) {
      if (expr[op]) {
        const [field, value] = expr[op] as any[]
        if (field && typeof field === 'object' && 'var' in field) {
          const fieldLabel = getFieldLabel(field.var)
          const operatorText = getOperatorText(op)
          const valueText = formatValue(value)
          return `${fieldLabel} ${operatorText} ${valueText}`
        }
      }
    }

    // 处理 IN 操作符
    if (expr.in) {
      const [value, field] = expr.in as any[]
      if (field && typeof field === 'object' && 'var' in field) {
        return `${formatValue(value)} 包含于 ${getFieldLabel(field.var)}`
      }
    }

    return JSON.stringify(expr)
  }

  // 尝试解析 RouteRule 格式: { logic, rules: [...] } 或 { field, operator, value }
  const parseRouteRule = (rule: Record<string, unknown>): string => {
    if (rule.field && rule.operator) {
      const opText = getOperatorText(String(rule.operator))
      return `${getFieldLabel(String(rule.field))} ${opText} ${formatValue(rule.value)}`
    }
    return JSON.stringify(rule)
  }

  // 检测并解析 RouteRule 格式: { logic: "and"|"or", rules: [...] }
  const logic = (condition.logic as string || '').toLowerCase()
  const rules = condition.rules as Array<Record<string, unknown>> | undefined
  if ((logic === 'and' || logic === 'or') && rules && rules.length) {
    const sep = logic === 'and' ? ' 且 ' : ' 或 '
    return rules.map(r => parseRouteRule(r)).join(sep)
  }

  // 检测并解析 RouteRule 格式: { field, operator, value }
  if (condition.field && condition.operator) {
    return parseRouteRule(condition)
  }

  // 尝试解析 JsonLogic 格式（检查是否有 JsonLogic 操作符）
  const jsonLogicOps = ['and', 'or', '!', '==', '!=', '>', '>=', '<', '<=', 'in']
  const hasJsonLogicOp = Object.keys(condition).some(k => jsonLogicOps.includes(k))
  if (hasJsonLogicOp) {
    return parseJsonLogic(condition)
  }

  // 无法解析时展示 key: value 对
  const entries = Object.entries(condition).filter(
    ([k]) => !['logic', 'rules', 'fieldLabel'].includes(k)
  )
  if (entries.length === 1) {
    const [k, v] = entries[0]
    return `${k}: ${formatValue(v)}`
  }

  return JSON.stringify(condition)
}

// 节点和边的类型定义
interface LayoutNode {
  id: string
  type: string
  position: { x: number; y: number }
  data: {
    label: string
    type: string
    status?: string
    color: string
    icon: string
    typeLabel: string
    assignee: string
  }
  style: {
    width: string
    height: string
  }
}

interface LayoutEdge {
  source: string
  target: string
}

interface FlowEdge {
  id: string
  source: string
  target: string
  animated: boolean
  label?: string
  style: {
    stroke: string
    strokeWidth: number
  }
  markerEnd: string
}

// 计算简单布局
const calculateLayout = (nodes: LayoutNode[], edges: LayoutEdge[]) => {
  const levels: string[][] = []
  const visited = new Set<string>()

  // 找到起始节点
  const startNodes = nodes.filter(n => n.data?.type === 'start').map(n => n.id)
  const endNodes = nodes.filter(n => n.data?.type === 'end').map(n => n.id)
  const otherNodes = nodes.filter(n => !['start', 'end'].includes(n.data?.type)).map(n => n.id)

  // 第一层：起始节点
  if (startNodes.length) {
    levels.push(startNodes)
    startNodes.forEach(id => visited.add(id))
  }

  // BFS 分层
  let currentLevel = startNodes
  while (currentLevel.length) {
    const nextLevel: string[] = []
    for (const nodeId of currentLevel) {
      const outgoingEdges = edges.filter(e => e.source === nodeId)
      for (const edge of outgoingEdges) {
        if (!visited.has(edge.target)) {
          nextLevel.push(edge.target)
          visited.add(edge.target)
        }
      }
    }
    if (nextLevel.length) {
      levels.push(nextLevel)
    }
    currentLevel = nextLevel
  }

  // 添加未访问的节点
  const unvisited = otherNodes.filter(id => !visited.has(id))
  if (unvisited.length) {
    levels.push(unvisited)
  }

  // 添加结束节点
  const unvisitedEndNodes = endNodes.filter(id => !visited.has(id))
  if (unvisitedEndNodes.length) {
    levels.push(unvisitedEndNodes)
  }

  // 计算坐标
  const horizontalGap = 280
  const verticalGap = 140
  const positionedNodes = nodes.map(node => {
    let levelIndex = -1
    let nodeIndex = -1
    levels.forEach((level, li) => {
      const ni = level.indexOf(node.id)
      if (ni !== -1) {
        levelIndex = li
        nodeIndex = ni
      }
    })

    if (levelIndex === -1) {
      levelIndex = levels.length
      nodeIndex = 0
    }

    const levelWidth = levels[levelIndex]?.length || 1
    const levelStartX = (levelWidth - 1) * horizontalGap / 2
    const x = levelStartX - nodeIndex * horizontalGap
    const y = levelIndex * verticalGap

    return {
      ...node,
      position: { x, y }
    }
  })

  return positionedNodes
}

// 转换节点数据为 Vue Flow 格式
const flowNodes = computed(() => {
  if (!props.nodes.length) return []

  // 先构建边数据用于布局计算
  const edgesForLayout = props.routes
    .filter(r => r.enabled !== false)
    .map((route) => {
      const source = getRouteSourceId(route)
      const target = getRouteTargetId(route)
      if (!source || !target) return null
      return {
        source: String(source),
        target: String(target)
      }
    })
    .filter((edge): edge is LayoutEdge => edge !== null)

  // 转换节点
  const nodes = props.nodes.map(node => {
    const id = String(getNodeId(node))
    const color = getNodeColor(node.type, node.status)
    const icon = getNodeIcon(node.type)

    // 确定节点类型
    let nodeType = 'default'
    if (node.type === 'start') nodeType = 'start'
    else if (node.type === 'end') nodeType = 'end'
    else if (node.type === 'condition') nodeType = 'condition'
    else nodeType = 'approval'

    // 确定节点尺寸
    let width = 200
    let height = 100
    if (node.type === 'start' || node.type === 'end') {
      width = 120
      height = 40
    } else if (node.type === 'condition') {
      width = 120
      height = 80
    }

    return {
      id,
      type: nodeType,
      position: { x: 0, y: 0 }, // 临时位置，会被布局算法覆盖
      data: {
        label: node.name,
        type: node.type,
        status: node.status,
        color,
        icon,
        typeLabel: node.type === 'user' ? '审批节点' : (node.type === 'auto' ? '自动处理' : ''),
        assignee: node.assignee_name || (node.assignee_type ? getAssigneeLabel(node.assignee_type) : '')
      },
      style: {
        width: `${width}px`,
        height: `${height}px`
      }
    }
  })

  // 计算布局
  const positionedNodes = calculateLayout(nodes, edgesForLayout)

  return positionedNodes
})

// 转换边数据为 Vue Flow 格式
const flowEdges = computed(() => {
  if (!props.routes.length) return []

  const validNodeIds = new Set(flowNodes.value.map(n => n.id))

  return props.routes
    .filter(r => r.enabled !== false)
    .map((route, index) => {
      const source = getRouteSourceId(route)
      const target = getRouteTargetId(route)
      if (!source || !target) return null

      const sourceId = String(source)
      const targetId = String(target)

      // 确保source和target节点都存在
      if (!validNodeIds.has(sourceId) || !validNodeIds.has(targetId)) {
        return null
      }

      const condition = route.condition_json ?? route.condition
      const label = condition ? formatCondition(condition) : ''
      const isCondition = !!condition

      return {
        id: `edge-${getRouteId(route, index)}`,
        source: sourceId,
        target: targetId,
        animated: isCondition,
        label: label || undefined,
        labelStyle: label ? {
          fill: isCondition ? '#ea580c' : '#4338ca',
          fontWeight: 600,
          fontSize: 12
        } : undefined,
        labelShowBg: !!label,
        labelBgStyle: {
          fill: '#fff',
          fillOpacity: 0.9,
          stroke: isCondition ? '#f97316' : '#6366f1',
          strokeWidth: 1,
          rx: 4,
          ry: 4
        },
        labelBgPadding: [6, 4] as [number, number],
        style: {
          stroke: isCondition ? '#f97316' : '#6366f1',
          strokeWidth: 2
        },
        markerEnd: 'arrowclosed'
      }
    })
    .filter((edge): edge is FlowEdge => edge !== null)
})

// 缩放控制
const zoomIn = () => {
  vueFlowZoomIn()
}

const zoomOut = () => {
  vueFlowZoomOut()
}

const fitView = () => {
  vueFlowFitView()
}
</script>

<style lang="scss">
/* Vue Flow 样式 - 不能加 scoped */
.vue-flow {
  background: transparent;
}

.vue-flow__node {
  padding: 0;
  border: none;
  background: transparent;
  border-radius: 0;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.vue-flow__edge-path {
  stroke: #6366f1;
  stroke-width: 2;
}

.vue-flow__edge.animated .vue-flow__edge-path {
  stroke-dasharray: 8 4;
  animation: flow-line 1s linear infinite;
}

@keyframes flow-line {
  from {
    stroke-dashoffset: 0;
  }
  to {
    stroke-dashoffset: -12;
  }
}

.vue-flow__minimap {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.vue-flow__controls {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.vue-flow__controls-button {
  background: white;
  border: none;
  border-bottom: 1px solid #e2e8f0;
  width: 28px;
  height: 28px;
}

.vue-flow__controls-button:hover {
  background: #f1f5f9;
}
</style>

<style scoped lang="scss">
.flow-diagram-wrapper {
  width: 100%;
  height: 500px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}

// 工具栏
.flow-toolbar {
  height: 48px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 10;

  .toolbar-title {
    display: flex;
    align-items: center;
    gap: 8px;

    .title-icon {
      font-size: 18px;
    }

    .title-text {
      font-size: 14px;
      font-weight: 600;
      color: #1e293b;
    }

    .status-badge {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 10px;
      font-weight: 500;

      &.running {
        background: #dcfce7;
        color: #16a34a;
      }

      &.completed {
        background: #dbeafe;
        color: #2563eb;
      }

      &.stopped {
        background: #fee2e2;
        color: #dc2626;
      }
    }
  }

  .toolbar-actions {
    display: flex;
    gap: 8px;

    .toolbar-btn {
      width: 28px;
      height: 28px;
      border: none;
      background: rgba(255, 255, 255, 0.6);
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      color: #64748b;
      transition: all 0.2s ease;

      &:hover {
        background: rgba(255, 255, 255, 0.9);
        color: #1e293b;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      }
    }
  }
}

// 画布容器
.graph-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  
  &.fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 9999;
    background: white;
    border-radius: 0;
    
    .flow-diagram-wrapper {
      height: 100%;
      border-radius: 0;
    }
  }
}

// 图例
.flow-legend {
  position: absolute;
  bottom: 16px;
  left: 16px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.6);
  z-index: 10;

  .legend-title {
    font-size: 12px;
    font-weight: 600;
    color: #475569;
    margin-bottom: 8px;
  }

  .legend-items {
    display: flex;
    gap: 16px;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #64748b;

    .legend-line {
      width: 20px;
      height: 2px;
      border-radius: 1px;

      &.normal {
        background: #6366f1;
      }

      &.condition {
        background: repeating-linear-gradient(
          to right,
          #f97316 0px,
          #f97316 4px,
          transparent 4px,
          transparent 8px
        );
        height: 2px;
      }
    }

    .legend-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #6366f1;
      animation: pulse 1.5s ease-in-out infinite;
    }
  }

  .legend-hint {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px dashed #e2e8f0;
    font-size: 11px;
    color: #94a3b8;

    .hint-divider {
      color: #cbd5e1;
    }

    .hint-active {
      color: #6366f1;
      font-weight: 500;
    }
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.3);
    opacity: 0.6;
  }
}

// 边标签样式
.edge-label {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  pointer-events: none;
  z-index: 1000;
}

// ========== 自定义节点样式 ==========

// 基础节点样式
.flow-node {
  position: relative;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
  }
}

// 开始/结束节点 - 胶囊形
.start-node,
.end-node {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--node-color);
  border-radius: 999px;
  color: white;
  font-size: 13px;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  min-width: 100px;

  .node-icon {
    font-size: 12px;
  }

  .node-label {
    white-space: nowrap;
  }

  &:hover {
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
  }
}

// 审批节点 - 卡片形
.approval-node {
  width: 200px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  position: relative;

  .node-status-bar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: var(--node-color);
  }

  .node-content {
    padding: 12px 16px;
    padding-left: 20px;
  }

  .node-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;

    .node-icon {
      font-size: 16px;
    }

    .node-title {
      flex: 1;
      font-size: 14px;
      font-weight: 600;
      color: #1e293b;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .processing-badge {
      font-size: 10px;
      padding: 2px 6px;
      background: #dbeafe;
      color: #2563eb;
      border-radius: 4px;
      font-weight: 500;
    }
  }

  .node-subtitle {
    font-size: 12px;
    color: #64748b;
    margin-bottom: 8px;
  }

  .node-footer {
    font-size: 11px;
    color: #94a3b8;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .pulse-ring {
    position: absolute;
    top: 8px;
    right: 8px;
    width: 8px;
    height: 8px;
    background: #6366f1;
    border-radius: 50%;
    animation: pulse-ring 1.5s ease-out infinite;
  }

  &:hover {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(0, 0, 0, 0.1);
  }
}

@keyframes pulse-ring {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(3);
    opacity: 0;
  }
}

// 条件节点 - 菱形
.condition-node {
  width: 120px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--node-color);
  clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);

  .diamond-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    color: white;
    font-size: 10px;
    text-align: center;

    .node-icon {
      font-size: 16px;
    }

    .node-label {
      font-weight: 500;
      max-width: 60px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  &:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
  }
}
</style>
