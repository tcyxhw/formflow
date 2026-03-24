<template>
  <div
    ref="canvasRef"
    class="flow-canvas"
    @pointerdown="handleCanvasPointerDown"
    @pointerup="handlePointerUp"
    @pointermove="handlePointerMove"
    @wheel="handleWheel"
    @contextmenu.prevent="handleContextMenu"
  >
    <!-- 网格背景 -->
    <div class="grid-background" :style="gridStyle"></div>

    <!-- 连线层 -->
    <svg class="edges-layer" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="flow-arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
          <polygon points="0 0, 10 3, 0 6" fill="#18a058" />
        </marker>
        <marker id="flow-arrow-muted" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
          <polygon points="0 0, 10 3, 0 6" fill="#c8d3df" />
        </marker>
      </defs>
      <g :style="{ transform: `translate(${panX}px, ${panY}px) scale(${scale})` }">
        <!-- 连线 -->
        <line
          v-for="(routeItem, idx) in routes"
          :key="`route-${idx}`"
          class="route-line"
          :class="{ 'is-selected': selectedRouteIndex === idx }"
          :x1="getRouteStartPos(routeItem)?.x"
          :y1="getRouteStartPos(routeItem)?.y"
          :x2="getRouteEndPos(routeItem)?.x"
          :y2="getRouteEndPos(routeItem)?.y"
          :stroke="routeItem.is_default ? '#18a058' : '#c8d3df'"
          :stroke-dasharray="routeItem.condition ? '8 4' : '0'"
          :marker-end="routeItem.is_default ? 'url(#flow-arrow)' : 'url(#flow-arrow-muted)'"
          @click.stop="selectRoute(idx)"
        />
      </g>
    </svg>

    <!-- 节点层 -->
    <div class="nodes-layer" :style="{ transform: `translate(${panX}px, ${panY}px) scale(${scale})` }">
      <div
        v-for="node in nodes"
        :key="getNodeKey(node)"
        class="flow-node"
        :class="{ 
          'is-selected': selectedNodeKey === getNodeKey(node),
          'is-multi-selected': isNodeMultiSelected(getNodeKey(node))
        }"
        :style="getNodeStyle(node)"
        @pointerdown.stop="event => startDrag(event, node)"
        @click.stop="event => selectNode(node, event)"
      >
        <div class="node-type-tag">{{ getNodeTypeLabel(node.type) }}</div>
        <div class="node-name">{{ node.name }}</div>
        <div class="node-meta">
          <span v-if="node.type === 'user'">{{ node.approve_policy.toUpperCase() }}</span>
          <span v-if="node.sla_hours">SLA {{ node.sla_hours }}h</span>
        </div>
        <!-- 连接点 -->
        <div class="connection-point connection-point-in" @pointerdown.stop="startConnection(event, node, 'in')" />
        <div class="connection-point connection-point-out" @pointerdown.stop="startConnection(event, node, 'out')" />
      </div>
    </div>

    <!-- 临时连线（拖拽中） -->
    <svg v-if="tempConnection" class="temp-connection-layer" xmlns="http://www.w3.org/2000/svg">
      <line
        :x1="tempConnection.startX"
        :y1="tempConnection.startY"
        :x2="tempConnection.endX"
        :y2="tempConnection.endY"
        stroke="#18a058"
        stroke-width="2"
        stroke-dasharray="4 4"
      />
    </svg>

    <!-- 选择框 -->
    <svg v-if="selectionBox" class="selection-box-layer" xmlns="http://www.w3.org/2000/svg">
      <rect
        :x="selectionBox.x"
        :y="selectionBox.y"
        :width="selectionBox.width"
        :height="selectionBox.height"
        fill="rgba(32, 128, 240, 0.1)"
        stroke="#2080f0"
        stroke-width="2"
        stroke-dasharray="4 4"
      />
    </svg>

    <!-- 工具栏 -->
    <div class="canvas-toolbar">
      <n-button-group>
        <n-button @click="zoomIn" :disabled="scale >= 2">
          <template #icon>
            <n-icon><ZoomIn /></n-icon>
          </template>
        </n-button>
        <n-button @click="zoomOut" :disabled="scale <= 0.5">
          <template #icon>
            <n-icon><ZoomOut /></n-icon>
          </template>
        </n-button>
        <n-button @click="resetZoom">
          <template #icon>
            <n-icon><Redo /></n-icon>
          </template>
        </n-button>
      </n-button-group>
      <n-divider vertical />
      <n-button-group>
        <n-button 
          @click="autoLayoutNodes"
          title="自动布局"
        >
          <template #icon>
            <n-icon><BorderOuter /></n-icon>
          </template>
          自动布局
        </n-button>
      </n-button-group>
      <n-divider vertical />
      <n-button-group>
        <n-button 
          :type="gridEnabled ? 'primary' : 'default'"
          @click="toggleGrid"
          title="切换网格对齐"
        >
          <template #icon>
            <n-icon><BorderOuter /></n-icon>
          </template>
        </n-button>
        <n-button 
          @click="decreaseGridSize"
          :disabled="gridSize <= 10"
          title="减小网格大小"
        >
          <template #icon>
            <n-icon><Minus /></n-icon>
          </template>
        </n-button>
        <n-button 
          @click="increaseGridSize"
          :disabled="gridSize >= 40"
          title="增大网格大小"
        >
          <template #icon>
            <n-icon><Plus /></n-icon>
          </template>
        </n-button>
      </n-button-group>
      <span class="zoom-indicator">{{ Math.round(scale * 100) }}%</span>
    </div>

    <!-- 右键菜单 -->
    <n-dropdown
      v-if="showContextMenu"
      :x="contextMenuX"
      :y="contextMenuY"
      :options="contextMenuOptions"
      @select="handleContextMenuSelect"
      @clickoutside="showContextMenu = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, h, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { NButton, NButtonGroup, NIcon, NDropdown, NDivider } from 'naive-ui'
import { ZoomIn, ZoomOut, Redo, Delete, Minus, Plus, BorderOuter } from '@vicons/antd'
import type { FlowNodeConfig, FlowNodePosition, FlowRouteConfig } from '@/types/flow'
import { getShortcutAction } from '@/constants/shortcuts'
import type { ShortcutAction } from '@/constants/shortcuts'
import { autoLayout } from '@/services/layoutService'

interface Props {
  nodes: FlowNodeConfig[]
  routes: FlowRouteConfig[]
  nodesGraph: Record<string, FlowNodePosition>
  selectedNodeKey?: string
  selectedNodeKeys?: Set<string>
  selectedRouteIndex?: number | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'select-node', key: string, multiSelect?: boolean): void
  (e: 'select-route', index: number): void
  (e: 'update-position', payload: { key: string; position: FlowNodePosition }): void
  (e: 'add-route', payload: { from_node_key: string; to_node_key: string }): void
  (e: 'delete-node', key: string): void
  (e: 'delete-route', index: number): void
  (e: 'undo'): void
  (e: 'redo'): void
  (e: 'select-all'): void
  (e: 'copy'): void
  (e: 'paste'): void
  (e: 'duplicate'): void
  (e: 'save'): void
}>()

const canvasRef = ref<HTMLElement | null>(null)
const scale = ref(1)
const panX = ref(0)
const panY = ref(0)
const gridSize = ref(20) // 网格大小，单位像素
const gridEnabled = ref(true) // 是否启用网格对齐

const dragState = reactive({
  active: false,
  nodeKey: '',
  offsetX: 0,
  offsetY: 0
})

const connectionState = reactive({
  active: false,
  fromNodeKey: '',
  fromType: 'out' as 'in' | 'out',
  startX: 0,
  startY: 0,
  endX: 0,
  endY: 0
})

const selectionBoxState = reactive({
  active: false,
  startX: 0,
  startY: 0,
  endX: 0,
  endY: 0
})

const tempConnection = computed(() => {
  if (!connectionState.active) return null
  return {
    startX: connectionState.startX,
    startY: connectionState.startY,
    endX: connectionState.endX,
    endY: connectionState.endY
  }
})

const selectionBox = computed(() => {
  if (!selectionBoxState.active) return null
  const minX = Math.min(selectionBoxState.startX, selectionBoxState.endX)
  const minY = Math.min(selectionBoxState.startY, selectionBoxState.endY)
  const maxX = Math.max(selectionBoxState.startX, selectionBoxState.endX)
  const maxY = Math.max(selectionBoxState.startY, selectionBoxState.endY)
  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY
  }
})

const showContextMenu = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const contextMenuNodeKey = ref<string>('')

const contextMenuOptions = computed(() => {
  const options: any[] = []
  if (contextMenuNodeKey.value) {
    options.push({
      label: '删除节点',
      key: 'delete-node',
      icon: () => h(NIcon, null, { default: () => h(Delete) })
    })
  }
  return options
})

const gridStyle = computed(() => ({
  backgroundImage: `
    linear-gradient(90deg, rgba(24, 160, 88, 0.08) 1px, transparent 0),
    linear-gradient(rgba(24, 160, 88, 0.08) 1px, transparent 0)
  `,
  backgroundSize: `${gridSize.value * scale.value}px ${gridSize.value * scale.value}px`,
  backgroundPosition: `${panX.value}px ${panY.value}px`
}))

const getNodeKey = (node: FlowNodeConfig): string => {
  return node.id?.toString() ?? node.temp_id ?? ''
}

// 将坐标对齐到网格
const snapToGrid = (value: number): number => {
  if (!gridEnabled.value) return value
  return Math.round(value / gridSize.value) * gridSize.value
}

const getNodeTypeLabel = (type: FlowNodeConfig['type']): string => {
  const map: Record<string, string> = {
    start: '开始',
    user: '审批',
    auto: '自动',
    condition: '条件',
    end: '结束'
  }
  return map[type] || '节点'
}

const getNodePosition = (key: string): FlowNodePosition => {
  return props.nodesGraph[key] || { x: 80, y: 80 }
}

const getNodeStyle = (node: FlowNodeConfig) => {
  const key = getNodeKey(node)
  const position = getNodePosition(key)
  return {
    transform: `translate(${position.x}px, ${position.y}px)`
  }
}

const getRouteStartPos = (route: FlowRouteConfig): FlowNodePosition | null => {
  const fromNode = props.nodes.find(n => getNodeKey(n) === route.from_node_key)
  if (!fromNode) return null
  const pos = getNodePosition(route.from_node_key)
  return { x: pos.x + 90, y: pos.y + 50 }
}

const getRouteEndPos = (route: FlowRouteConfig): FlowNodePosition | null => {
  const toNode = props.nodes.find(n => getNodeKey(n) === route.to_node_key)
  if (!toNode) return null
  const pos = getNodePosition(route.to_node_key)
  return { x: pos.x, y: pos.y + 50 }
}

const selectNode = (node: FlowNodeConfig, event?: PointerEvent | MouseEvent) => {
  const key = getNodeKey(node)
  if (!key) return
  const isMultiSelect = event ? (event.ctrlKey || event.metaKey) : false
  emit('select-node', key, isMultiSelect)
}

const isNodeMultiSelected = (key: string): boolean => {
  return props.selectedNodeKeys?.has(key) ?? false
}

const selectRoute = (index: number) => {
  emit('select-route', index)
}

const startDrag = (event: PointerEvent, node: FlowNodeConfig) => {
  const key = getNodeKey(node)
  if (!key) return
  const boardRect = canvasRef.value?.getBoundingClientRect()
  if (!boardRect) return
  const nodePos = getNodePosition(key)
  dragState.active = true
  dragState.nodeKey = key
  dragState.offsetX = (event.clientX - boardRect.left - panX.value) / scale.value - nodePos.x
  dragState.offsetY = (event.clientY - boardRect.top - panY.value) / scale.value - nodePos.y
  selectNode(node)
}

const startConnection = (event: PointerEvent, node: FlowNodeConfig, type: 'in' | 'out') => {
  const key = getNodeKey(node)
  if (!key) return
  const boardRect = canvasRef.value?.getBoundingClientRect()
  if (!boardRect) return
  const nodePos = getNodePosition(key)
  const pointX = nodePos.x + (type === 'in' ? 0 : 90)
  const pointY = nodePos.y + 50

  connectionState.active = true
  connectionState.fromNodeKey = key
  connectionState.fromType = type
  connectionState.startX = pointX
  connectionState.startY = pointY
  connectionState.endX = pointX
  connectionState.endY = pointY
}

const handlePointerMove = (event: PointerEvent) => {
  if (!canvasRef.value) return
  const boardRect = canvasRef.value.getBoundingClientRect()

  // 处理节点拖拽
  if (dragState.active && dragState.nodeKey) {
    let nextX = (event.clientX - boardRect.left - panX.value) / scale.value - dragState.offsetX
    let nextY = (event.clientY - boardRect.top - panY.value) / scale.value - dragState.offsetY
    
    // 应用网格对齐
    nextX = snapToGrid(nextX)
    nextY = snapToGrid(nextY)
    
    emit('update-position', {
      key: dragState.nodeKey,
      position: {
        x: Math.max(20, nextX),
        y: Math.max(20, nextY)
      }
    })
  }

  // 处理连线拖拽
  if (connectionState.active) {
    connectionState.endX = (event.clientX - boardRect.left - panX.value) / scale.value
    connectionState.endY = (event.clientY - boardRect.top - panY.value) / scale.value
  }

  // 处理选择框拖拽
  if (selectionBoxState.active) {
    selectionBoxState.endX = (event.clientX - boardRect.left - panX.value) / scale.value
    selectionBoxState.endY = (event.clientY - boardRect.top - panY.value) / scale.value
  }
}

const handlePointerUp = (event: PointerEvent) => {
  dragState.active = false
  dragState.nodeKey = ''

  // 处理连线完成
  if (connectionState.active) {
    const boardRect = canvasRef.value?.getBoundingClientRect()
    if (boardRect) {
      const endX = (event.clientX - boardRect.left - panX.value) / scale.value
      const endY = (event.clientY - boardRect.top - panY.value) / scale.value

      // 检查是否在某个节点的连接点上
      for (const node of props.nodes) {
        const key = getNodeKey(node)
        const pos = getNodePosition(key)
        const pointX = pos.x
        const pointY = pos.y + 50
        const distance = Math.sqrt((endX - pointX) ** 2 + (endY - pointY) ** 2)
        if (distance < 20) {
          emit('add-route', {
            from_node_key: connectionState.fromNodeKey,
            to_node_key: key
          })
          break
        }
      }
    }
    connectionState.active = false
  }

  // 处理选择框完成
  if (selectionBoxState.active) {
    const minX = Math.min(selectionBoxState.startX, selectionBoxState.endX)
    const minY = Math.min(selectionBoxState.startY, selectionBoxState.endY)
    const maxX = Math.max(selectionBoxState.startX, selectionBoxState.endX)
    const maxY = Math.max(selectionBoxState.startY, selectionBoxState.endY)

    // 检查哪些节点在选择框内
    const selectedKeys: string[] = []
    for (const node of props.nodes) {
      const key = getNodeKey(node)
      const pos = getNodePosition(key)
      const nodeLeft = pos.x
      const nodeTop = pos.y
      const nodeRight = pos.x + 180
      const nodeBottom = pos.y + 100

      // 检查节点是否与选择框相交
      if (nodeRight >= minX && nodeLeft <= maxX && nodeBottom >= minY && nodeTop <= maxY) {
        selectedKeys.push(key)
      }
    }

    // 发出多选事件
    if (selectedKeys.length > 0) {
      selectedKeys.forEach((key, index) => {
        emit('select-node', key, index > 0 || event.ctrlKey || event.metaKey)
      })
    }

    selectionBoxState.active = false
  }
}

const handleCanvasPointerDown = (event: PointerEvent) => {
  if (event.button === 2) return // 右键
  if (event.target === canvasRef.value) {
    // 在空白处按下，开始选择框
    const boardRect = canvasRef.value?.getBoundingClientRect()
    if (!boardRect) return
    
    const startX = (event.clientX - boardRect.left - panX.value) / scale.value
    const startY = (event.clientY - boardRect.top - panY.value) / scale.value
    
    selectionBoxState.active = true
    selectionBoxState.startX = startX
    selectionBoxState.startY = startY
    selectionBoxState.endX = startX
    selectionBoxState.endY = startY
    
    // 如果不是多选，清除之前的选择
    if (!event.ctrlKey && !event.metaKey) {
      emit('select-node', '', false)
    }
  }
}

const handleWheel = (event: WheelEvent) => {
  event.preventDefault()
  const delta = event.deltaY > 0 ? -0.1 : 0.1
  const newScale = Math.max(0.5, Math.min(2, scale.value + delta))
  scale.value = newScale
}

const handleContextMenu = (event: MouseEvent) => {
  const boardRect = canvasRef.value?.getBoundingClientRect()
  if (!boardRect) return

  const x = (event.clientX - boardRect.left - panX.value) / scale.value
  const y = (event.clientY - boardRect.top - panY.value) / scale.value

  // 检查是否在节点上
  for (const node of props.nodes) {
    const key = getNodeKey(node)
    const pos = getNodePosition(key)
    if (
      x >= pos.x &&
      x <= pos.x + 180 &&
      y >= pos.y &&
      y <= pos.y + 100
    ) {
      contextMenuNodeKey.value = key
      contextMenuX.value = event.clientX
      contextMenuY.value = event.clientY
      showContextMenu.value = true
      return
    }
  }
}

const handleContextMenuSelect = (key: string) => {
  if (key === 'delete-node' && contextMenuNodeKey.value) {
    emit('delete-node', contextMenuNodeKey.value)
  }
  showContextMenu.value = false
}

const handleKeyDown = (event: KeyboardEvent) => {
  // 获取快捷键操作
  const action = getShortcutAction(event)

  if (!action) return

  // 检查是否在输入框中
  const target = event.target as HTMLElement
  const isInInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA'

  // 某些快捷键在输入框中应该被禁用
  const disableInInputActions: ShortcutAction[] = ['selectAll', 'delete']
  if (isInInput && disableInInputActions.includes(action)) {
    return
  }

  event.preventDefault()

  // 处理快捷键操作
  switch (action) {
    case 'undo':
      emit('undo')
      break
    case 'redo':
      emit('redo')
      break
    case 'selectAll':
      emit('select-all')
      break
    case 'delete':
      emit('delete')
      break
    case 'copy':
      emit('copy')
      break
    case 'paste':
      emit('paste')
      break
    case 'duplicate':
      emit('duplicate')
      break
    case 'save':
      emit('save')
      break
  }
}

const zoomIn = () => {
  scale.value = Math.min(2, scale.value + 0.1)
}

const zoomOut = () => {
  scale.value = Math.max(0.5, scale.value - 0.1)
}

const resetZoom = () => {
  scale.value = 1
  panX.value = 0
  panY.value = 0
}

const toggleGrid = () => {
  gridEnabled.value = !gridEnabled.value
}

const increaseGridSize = () => {
  if (gridSize.value < 40) {
    gridSize.value += 10
  }
}

const decreaseGridSize = () => {
  if (gridSize.value > 10) {
    gridSize.value -= 10
  }
}

const autoLayoutNodes = () => {
  // 使用布局服务计算新位置
  const newPositions = autoLayout(props.nodes, props.routes)
  
  // 为每个节点发出更新位置事件
  props.nodes.forEach((node) => {
    const key = getNodeKey(node)
    if (newPositions[key]) {
      emit('update-position', {
        key,
        position: newPositions[key]
      })
    }
  })
}

onMounted(() => {
  window.addEventListener('pointermove', handlePointerMove)
  window.addEventListener('pointerup', handlePointerUp)
  window.addEventListener('keydown', handleKeyDown)
})

onBeforeUnmount(() => {
  window.removeEventListener('pointermove', handlePointerMove)
  window.removeEventListener('pointerup', handlePointerUp)
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.flow-canvas {
  position: relative;
  flex: 1;
  border-radius: 8px;
  min-height: 520px;
  overflow: hidden;
  background-color: #fafbfc;
  user-select: none;
}

.grid-background {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.edges-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.edges-layer g {
  transform-origin: 0 0;
}

.route-line {
  stroke-width: 2;
  fill: none;
  cursor: pointer;
  transition: stroke-width 0.2s ease;
}

.route-line:hover {
  stroke-width: 3;
}

.route-line.is-selected {
  stroke-width: 3;
  stroke: #18a058 !important;
}

.nodes-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  transform-origin: 0 0;
}

.flow-node {
  position: absolute;
  width: 180px;
  height: 100px;
  padding: 12px;
  border-radius: 10px;
  background-color: white;
  box-shadow: 0 8px 24px rgba(15, 22, 36, 0.12);
  border: 2px solid transparent;
  cursor: grab;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.flow-node:hover {
  box-shadow: 0 8px 32px rgba(15, 22, 36, 0.18);
}

.flow-node.is-selected {
  border-color: #18a058;
  box-shadow: 0 8px 32px rgba(24, 160, 88, 0.35);
}

.flow-node.is-multi-selected {
  border-color: #2080f0;
  box-shadow: 0 8px 32px rgba(32, 128, 240, 0.25);
}

.node-type-tag {
  font-size: 12px;
  color: #18a058;
  font-weight: 600;
  text-transform: uppercase;
}

.node-name {
  font-size: 16px;
  font-weight: 600;
  margin: 6px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-meta {
  font-size: 12px;
  color: #5c6370;
  display: flex;
  gap: 8px;
}

.connection-point {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #18a058;
  border: 2px solid white;
  cursor: crosshair;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.flow-node:hover .connection-point {
  opacity: 1;
}

.connection-point-in {
  left: -6px;
}

.connection-point-out {
  right: -6px;
}

.temp-connection-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.selection-box-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.canvas-toolbar {
  position: absolute;
  bottom: 20px;
  right: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  background-color: white;
  padding: 8px 12px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(15, 22, 36, 0.12);
}

.zoom-indicator {
  font-size: 12px;
  color: #5c6370;
  min-width: 40px;
  text-align: center;
}

:deep(.n-divider--vertical) {
  margin: 0 8px;
}
</style>
