<template>
  <g class="custom-edge">
    <!-- 发光效果路径 -->
    <path
      :d="path"
      class="edge-glow"
      :style="{
        stroke: data?.isDefault ? '#fbbf24' : '#818cf8',
        strokeWidth: '8px',
        opacity: '0.2'
      }"
    />
    <!-- 主路径 -->
    <path
      :d="path"
      class="edge-path"
      :style="{
        stroke: data?.isDefault ? '#f59e0b' : '#6366f1',
        strokeWidth: data?.isDefault ? '2px' : '3px',
        strokeDasharray: data?.isDefault ? '6,4' : 'none'
      }"
      :class="{ 'animated': !data?.isDefault }"
    />
    <!-- 条件标签背景 -->
    <foreignObject
      v-if="label"
      :x="labelX - labelWidth / 2"
      :y="labelY - 14"
      :width="labelWidth"
      height="28"
      class="edge-label-fo"
    >
      <div
        class="edge-label"
        :class="{ 'is-default': data?.isDefault }"
        :style="{
          backgroundColor: data?.isDefault ? '#fffbeb' : '#eef2ff',
          borderColor: data?.isDefault ? '#f59e0b' : '#6366f1',
          color: data?.isDefault ? '#d97706' : '#4f46e5'
        }"
      >
        {{ label }}
      </div>
    </foreignObject>
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getBezierPath, type EdgeProps } from '@vue-flow/core'

const props = defineProps<EdgeProps>()

const path = computed(() => {
  const [pathData] = getBezierPath({
    sourceX: props.sourceX,
    sourceY: props.sourceY,
    targetX: props.targetX,
    targetY: props.targetY,
    sourcePosition: props.sourcePosition,
    targetPosition: props.targetPosition,
    curvature: 0.3
  })
  return pathData
})

const labelX = computed(() => (props.sourceX + props.targetX) / 2)
const labelY = computed(() => (props.sourceY + props.targetY) / 2)
const labelWidth = computed(() => {
  if (!props.label) return 60
  return Math.max(String(props.label).length * 13 + 20, 60)
})
</script>

<style scoped lang="scss">
.custom-edge {
  pointer-events: none;
}

.edge-glow {
  fill: none;
  filter: blur(4px);
}

.edge-path {
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: all 0.3s ease;

  &.animated {
    animation: dash 30s linear infinite;
  }
}

@keyframes dash {
  to {
    stroke-dashoffset: -1000;
  }
}

.edge-label-fo {
  overflow: visible;
}

.edge-label {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 4px 12px;
  border-radius: 14px;
  font-size: 12px;
  font-weight: 500;
  border: 1.5px solid;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(4px);
  animation: labelFadeIn 0.3s ease;

  &.is-default {
    font-style: italic;
  }
}

@keyframes labelFadeIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
