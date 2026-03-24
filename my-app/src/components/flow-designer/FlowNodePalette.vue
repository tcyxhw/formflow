<template>
  <div class="flow-node-palette">
    <!-- 头部 -->
    <div class="palette-header">
      <div class="title">节点调色板</div>
      <div class="subtitle">拖拽节点到画布</div>
    </div>

    <!-- 节点列表 -->
    <div class="palette-body">
      <div class="node-category">
        <div class="category-title">基础节点</div>
        <div class="node-list">
          <div
            v-for="nodeType in basicNodeTypes"
            :key="nodeType.type"
            class="palette-node"
            :draggable="true"
            @dragstart="handleDragStart($event, nodeType)"
            @dragend="handleDragEnd"
          >
            <div class="node-icon">
              <n-icon :size="24">
                <component :is="nodeType.icon" />
              </n-icon>
            </div>
            <div class="node-info">
              <div class="node-label">{{ nodeType.label }}</div>
              <div class="node-desc">{{ nodeType.description }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="node-category">
        <div class="category-title">高级节点</div>
        <div class="node-list">
          <div
            v-for="nodeType in advancedNodeTypes"
            :key="nodeType.type"
            class="palette-node"
            :draggable="true"
            @dragstart="handleDragStart($event, nodeType)"
            @dragend="handleDragEnd"
          >
            <div class="node-icon">
              <n-icon :size="24">
                <component :is="nodeType.icon" />
              </n-icon>
            </div>
            <div class="node-info">
              <div class="node-label">{{ nodeType.label }}</div>
              <div class="node-desc">{{ nodeType.description }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NIcon } from 'naive-ui'
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  BranchesOutlined,
  CopyOutlined,
  StopOutlined
} from '@vicons/antd'
import type { FlowNodeType } from '@/types/flow'

interface NodeTypeOption {
  type: FlowNodeType
  label: string
  description: string
  icon: any
  defaultName: string
}

const basicNodeTypes: NodeTypeOption[] = [
  {
    type: 'start',
    label: '开始',
    description: '流程起点',
    icon: PlayCircleOutlined,
    defaultName: '开始'
  },
  {
    type: 'end',
    label: '结束',
    description: '流程终点',
    icon: StopOutlined,
    defaultName: '结束'
  }
]

const advancedNodeTypes: NodeTypeOption[] = [
  {
    type: 'user',
    label: '审批',
    description: '人工审批节点',
    icon: CheckCircleOutlined,
    defaultName: '审批'
  },
  {
    type: 'condition',
    label: '条件',
    description: '条件分支节点',
    icon: BranchesOutlined,
    defaultName: '条件分支'
  },
  {
    type: 'auto',
    label: '抄送',
    description: '抄送通知节点',
    icon: CopyOutlined,
    defaultName: '抄送'
  }
]

const isDragging = ref(false)

const handleDragStart = (event: DragEvent, nodeType: NodeTypeOption) => {
  isDragging.value = true
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'copy'
    event.dataTransfer.setData(
      'application/json',
      JSON.stringify({
        type: 'node',
        nodeType: nodeType.type,
        defaultName: nodeType.defaultName
      })
    )
  }
}

const handleDragEnd = () => {
  isDragging.value = false
}
</script>

<style scoped>
.flow-node-palette {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(15, 22, 36, 0.12);
  overflow: hidden;
}

.palette-header {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
  background-color: #fafbfc;
}

.title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.subtitle {
  font-size: 12px;
  color: #6b7280;
}

.palette-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.node-category {
  margin-bottom: 16px;
}

.node-category:last-child {
  margin-bottom: 0;
}

.category-title {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
  padding: 0 8px;
}

.node-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.palette-node {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  cursor: grab;
  transition: all 0.2s ease;
  user-select: none;
}

.palette-node:hover {
  background-color: #f3f4f6;
  border-color: #d1d5db;
  box-shadow: 0 2px 8px rgba(15, 22, 36, 0.08);
}

.palette-node:active {
  cursor: grabbing;
}

.node-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 6px;
  background-color: white;
  border: 1px solid #e5e7eb;
  color: #18a058;
  flex-shrink: 0;
}

.palette-node:hover .node-icon {
  background-color: #ecfdf5;
  border-color: #18a058;
}

.node-info {
  flex: 1;
  min-width: 0;
}

.node-label {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2px;
}

.node-desc {
  font-size: 12px;
  color: #9ca3af;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 拖拽时的样式 */
.palette-node:active {
  opacity: 0.7;
}
</style>
