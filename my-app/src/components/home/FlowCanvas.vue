<!-- src/components/home/FlowCanvas.vue -->
<template>
  <div class="flow-canvas" role="img" aria-label="审批流程图，展示节点与连线关系">
    <svg 
      class="flow-svg"
      :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
      xmlns="http://www.w3.org/2000/svg"
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <!-- 激活状态的发光滤镜 -->
        <filter id="active-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>

        <!-- 箭头标记 -->
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="10"
          refX="9"
          refY="3"
          orient="auto"
        >
          <polygon points="0 0, 10 3, 0 6" fill="#18a058" />
        </marker>
        
        <marker
          id="arrowhead-inactive"
          markerWidth="10"
          markerHeight="10"
          refX="9"
          refY="3"
          orient="auto"
        >
          <polygon points="0 0, 10 3, 0 6" fill="#d0d0d0" />
        </marker>
      </defs>

      <!-- 边（连线）层 -->
      <g class="edges-layer">
        <g v-for="(edge, index) in edges" :key="`edge-${index}`">
          <line
            :x1="getNodePosition(edge.from).x"
            :y1="getNodePosition(edge.from).y"
            :x2="getNodePosition(edge.to).x"
            :y2="getNodePosition(edge.to).y"
            :stroke="edge.active ? '#18a058' : '#d0d0d0'"
            :stroke-width="edge.active ? 3 : 2"
            :stroke-dasharray="edge.active ? '0' : '5,5'"
            class="flow-edge"
            :marker-end="edge.active ? 'url(#arrowhead)' : 'url(#arrowhead-inactive)'"
          />
          
          <!-- 条件标签 -->
          <text
            v-if="edge.condition"
            :x="(getNodePosition(edge.from).x + getNodePosition(edge.to).x) / 2"
            :y="(getNodePosition(edge.from).y + getNodePosition(edge.to).y) / 2 - 12"
            :fill="edge.active ? '#18a058' : '#999'"
            font-size="12"
            font-weight="500"
            text-anchor="middle"
            class="edge-label"
          >
            {{ edge.condition }}
          </text>
        </g>
      </g>

      <!-- 节点层 -->
      <g class="nodes-layer">
        <g 
          v-for="node in nodes" 
          :key="node.id"
          class="flow-node-group"
          :class="{ 'node-active': isActiveNode(node.id) }"
          tabindex="0"
          role="button"
          :aria-label="`${node.name}节点，类型：${getNodeTypeLabel(node.type)}`"
          @keydown.enter="handleNodeClick(node.id)"
          @keydown.space.prevent="handleNodeClick(node.id)"
        >
          <!-- 扩大的触控区域（不可见） -->
          <circle
            :cx="node.position.x"
            :cy="node.position.y"
            :r="touchRadius"
            fill="transparent"
            class="node-touch-area"
          />
          
          <!-- 可见节点 -->
          <circle
            :cx="node.position.x"
            :cy="node.position.y"
            :r="nodeRadius"
            :fill="getNodeColor(node.type)"
            :stroke="isActiveNode(node.id) ? '#18a058' : '#fff'"
            :stroke-width="isActiveNode(node.id) ? 4 : 2"
            :filter="isActiveNode(node.id) ? 'url(#active-glow)' : ''"
            class="flow-node"
          />
          
          <!-- 节点文字 -->
          <text
            :x="node.position.x"
            :y="node.position.y + 5"
            fill="white"
            font-size="14"
            font-weight="600"
            text-anchor="middle"
            class="node-text"
            pointer-events="none"
          >
            {{ node.name }}
          </text>
        </g>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import type { FlowNode, FlowEdge } from '@/stores/homeInteractive'

const props = defineProps<{
  nodes: FlowNode[]
  edges: FlowEdge[]
}>()

const svgWidth = 800
const svgHeight = 400
const nodeRadius = 40
const touchRadius = 44

const getNodePosition = (nodeId: string) => {
  const node = props.nodes.find(n => n.id === nodeId)
  return node?.position || { x: 0, y: 0 }
}

const getNodeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    start: '#18a058',
    user: '#2080f0',
    auto: '#f0a020',
    end: '#d03050'
  }
  return colorMap[type] || '#999'
}

const isActiveNode = (nodeId: string) => {
  return props.edges.some(edge => (edge.from === nodeId || edge.to === nodeId) && edge.active)
}

const getNodeTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    start: '开始',
    user: '用户操作',
    auto: '自动处理',
    end: '结束'
  }
  return labels[type] || '未知'
}

const handleNodeClick = (nodeId: string) => {
  console.log('Node clicked:', nodeId)
}
</script>

<style scoped>
.flow-canvas {
  width: 100%;
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.flow-svg {
  width: 100%;
  height: auto;
  max-width: 800px;
  display: block;
}

/* 边 */
.flow-edge {
  fill: none;
  transition: all 220ms ease-out;
}

.edge-label {
  transition: fill 220ms ease-out;
}

/* 节点组 */
.flow-node-group {
  cursor: pointer;
  outline: none;
  transition: transform 220ms ease-out;
}

.flow-node-group:hover {
  transform: scale(1.05);
}

.flow-node-group:active {
  transform: scale(0.98);
}

.node-touch-area {
  cursor: pointer;
}

.flow-node {
  transition: all 220ms ease-out;
}

/* 激活节点脉冲动画 */
.node-active .flow-node {
  animation: nodePulse 1.6s ease-in-out infinite;
}

@keyframes nodePulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.08);
    opacity: 0.9;
  }
}

.node-text {
  user-select: none;
}

/* 焦点样式 */
.flow-node-group:focus-visible {
  outline: 2px solid #18a058;
  outline-offset: 4px;
}

/* 响应式 */
@media (max-width: 768px) {
  .flow-canvas {
    min-height: 280px;
    padding: 8px;
  }
  
  .node-text {
    font-size: 12px;
  }
  
  .edge-label {
    font-size: 11px;
  }
}

/* 运动减弱支持 */
@media (prefers-reduced-motion: reduce) {
  .flow-edge,
  .edge-label,
  .flow-node-group,
  .flow-node {
    transition: none;
    animation: none;
  }
  
  .node-active .flow-node {
    animation: none;
  }
}
</style>