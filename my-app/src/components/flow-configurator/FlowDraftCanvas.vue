<template>
  <div
    ref="boardRef"
    class="draft-canvas"
    @pointerup="handlePointerUp"
  >
    <svg class="connection-layer" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="flow-arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
          <polygon points="0 0, 10 3, 0 6" fill="#18a058" />
        </marker>
      </defs>
      <g>
        <g v-for="(routeItem, index) in renderRoutes" :key="getRouteKey(routeItem)">
          <line
            v-if="getRoutePosition(routeItem)"
            class="route-line"
            :x1="getRoutePosition(routeItem)?.from.x"
            :y1="getRoutePosition(routeItem)?.from.y"
            :x2="getRoutePosition(routeItem)?.to.x"
            :y2="getRoutePosition(routeItem)?.to.y"
            :stroke="themeColors.primary"
            :stroke-width="getRouteStrokeWidth(routeItem)"
            :stroke-dasharray="routeItem.condition ? '8 4' : '0'"
            marker-end="url(#flow-arrow)"
          />
          <g v-if="getRoutePosition(routeItem)">
            <circle
              :cx="getRouteLabelPosition(routeItem).x"
              :cy="getRouteLabelPosition(routeItem).y"
              r="12"
              :fill="getRouteLabelBg(routeItem)"
              stroke="white"
              stroke-width="2"
            />
            <text
              :x="getRouteLabelPosition(routeItem).x"
              :y="getRouteLabelPosition(routeItem).y"
              class="route-label"
              :fill="getRouteLabelColor(routeItem)"
            >
              {{ index + 1 }}
            </text>
          </g>
        </g>
      </g>
    </svg>

    <div
      v-for="node in renderNodes"
      :key="getNodeKey(node)"
      class="draft-node"
      :class="{ 'is-selected': selectedKeyValue === getNodeKey(node) }"
      :style="getNodeStyle(node)"
      @pointerdown.stop="event => startDrag(event, node)"
      @click.stop="() => emitSelect(node)"
    >
      <div class="node-type-tag">{{ getNodeTypeLabel(node.type) }}</div>
      <div class="node-name">{{ node.name }}</div>
      <div class="node-meta">
        <span>{{ node.approve_policy.toUpperCase() }} · SLA {{ node.sla_hours ?? '-' }}h</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import type { FlowNodeConfig, FlowNodePosition, FlowRouteConfig } from '@/types/flow'

interface Props {
  nodes: FlowNodeConfig[]
  routes: FlowRouteConfig[]
  nodesGraph: Record<string, FlowNodePosition>
  selectedKey?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'select-node', key: string): void
  (e: 'update-position', payload: { key: string; position: FlowNodePosition }): void
}>()

const boardRef = ref<HTMLElement | null>(null)
const renderNodes = computed(() => props.nodes)
const renderRoutes = computed(() => props.routes)
const nodesGraph = computed(() => props.nodesGraph)
const selectedKeyValue = computed(() => props.selectedKey)

const dragState = reactive({
  active: false,
  key: '' as string,
  offsetX: 0,
  offsetY: 0
})

const themeColors = computed(() => ({
  primary: '#18a058',
  muted: '#c8d3df'
}))

const getNodeKey = (node: FlowNodeConfig) => node.id?.toString() ?? node.temp_id ?? ''
const getRouteKey = (route: FlowRouteConfig) =>
  route.id?.toString() ?? route.temp_id ?? `${route.from_node_key}-${route.to_node_key}`

const getNodeTypeLabel = (type: FlowNodeConfig['type']) => {
  const map: Record<string, string> = {
    start: '开始节点',
    user: '人工审批',
    auto: '自动节点',
    end: '结束节点'
  }
  return map[type] || '节点'
}

const getNodePosition = (key: string): FlowNodePosition => {
  return nodesGraph.value[key] || { x: 80, y: 80 }
}

const getNodeStyle = (node: FlowNodeConfig) => {
  const key = getNodeKey(node)
  const position = getNodePosition(key)
  return {
    transform: `translate(${position.x}px, ${position.y}px)`
  }
}

const emitSelect = (node: FlowNodeConfig) => {
  const key = getNodeKey(node)
  if (!key) return
  emit('select-node', key)
}

const startDrag = (event: PointerEvent, node: FlowNodeConfig) => {
  const key = getNodeKey(node)
  if (!key) return
  const boardRect = boardRef.value?.getBoundingClientRect()
  if (!boardRect) return
  const nodePos = getNodePosition(key)
  dragState.active = true
  dragState.key = key
  dragState.offsetX = event.clientX - (boardRect.left + nodePos.x)
  dragState.offsetY = event.clientY - (boardRect.top + nodePos.y)
  emitSelect(node)
}

const handlePointerMove = (event: PointerEvent) => {
  if (!dragState.active || !dragState.key || !boardRef.value) return
  const boardRect = boardRef.value.getBoundingClientRect()
  const nextX = event.clientX - boardRect.left - dragState.offsetX
  const nextY = event.clientY - boardRect.top - dragState.offsetY
  emit('update-position', {
    key: dragState.key,
    position: {
      x: Math.max(20, nextX),
      y: Math.max(20, nextY)
    }
  })
}

const handlePointerUp = () => {
  dragState.active = false
  dragState.key = ''
}

const getRoutePosition = (route: FlowRouteConfig) => {
  const from = getNodePosition(route.from_node_key)
  const to = getNodePosition(route.to_node_key)
  if (!from || !to) return null
  return { from, to }
}

const getRouteLabelPosition = (route: FlowRouteConfig) => {
  const pos = getRoutePosition(route)
  if (!pos) return { x: 0, y: 0 }
  return {
    x: (pos.from.x + pos.to.x) / 2,
    y: (pos.from.y + pos.to.y) / 2
  }
}

const getRouteLabelBg = (route: FlowRouteConfig) => {
  const priority = route.priority || 1
  // 优先级越高，颜色越深
  const opacity = Math.max(0.4, 1 - (priority - 1) * 0.2)
  return `rgba(24, 160, 88, ${opacity})`
}

const getRouteLabelColor = (route: FlowRouteConfig) => {
  return 'white'
}

const getRouteStrokeWidth = (route: FlowRouteConfig) => {
  const priority = route.priority || 1
  // 优先级越高，线越粗
  return Math.max(1.5, 3.5 - (priority - 1) * 0.5)
}

onMounted(() => {
  window.addEventListener('pointermove', handlePointerMove)
})

onBeforeUnmount(() => {
  window.removeEventListener('pointermove', handlePointerMove)
})
</script>

<style scoped>
.draft-canvas {
  position: relative;
  flex: 1;
  background-image: linear-gradient(90deg, rgba(24, 160, 88, 0.06) 1px, transparent 0),
    linear-gradient(rgba(24, 160, 88, 0.06) 1px, transparent 0);
  background-size: 40px 40px;
  border-radius: 8px;
  overflow: auto;
}

.connection-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.route-line {
  fill: none;
}

.route-label {
  font-size: 11px;
  font-weight: 600;
  text-anchor: middle;
  dominant-baseline: central;
}

.draft-node {
  position: absolute;
  width: 180px;
  padding: 12px;
  border-radius: 10px;
  background-color: white;
  box-shadow: 0 8px 24px rgba(15, 22, 36, 0.12);
  border: 2px solid transparent;
  cursor: grab;
  user-select: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.draft-node.is-selected {
  border-color: #18a058;
  box-shadow: 0 8px 32px rgba(24, 160, 88, 0.35);
}

.node-type-tag {
  font-size: 12px;
  color: #18a058;
  font-weight: 600;
}

.node-name {
  font-size: 16px;
  font-weight: 600;
  margin: 6px 0;
}

.node-meta {
  font-size: 12px;
  color: #5c6370;
}
</style>
