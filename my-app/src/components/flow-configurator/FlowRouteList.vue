<template>
  <div class="route-list">
    <div class="list-header">
      <div class="title">路由列表</div>
      <div class="subtitle">点击选择需要编辑的路由</div>
    </div>
    <n-empty v-if="routes.length === 0" description="暂无路由" size="small" class="empty-body" />
    <n-scrollbar v-else class="list-body">
      <div class="route-items">
        <div
          v-for="(route, index) in routes"
          :key="route.id ?? route.temp_id ?? `${route.from_node_key}-${route.to_node_key}`"
          class="route-item"
          :class="{ active: index === selectedIndex }"
          @click="handleSelect(index)"
        >
          <div class="upper">
            <span class="route-index">{{ index + 1 }}</span>
            <span class="name">{{ getNodeName(route.from_node_key) }} → {{ getNodeName(route.to_node_key) }}</span>
            <div class="upper-right">
              <n-button
                quaternary
                circle
                type="error"
                size="tiny"
                :disabled="disabled"
                @click.stop="handleDelete(index)"
                class="delete-btn"
              >
                <template #icon>
                  <n-icon>
                    <DeleteOutlined />
                  </n-icon>
                </template>
              </n-button>
            </div>
          </div>
          <div class="meta">
            <span class="owner">归属：{{ getNodeName(route.from_node_key) }}</span>
            <span>优先级 {{ route.priority }}</span>
            <span v-if="route.condition">已配置条件</span>
            <span v-else>无条件</span>
          </div>
        </div>
      </div>
    </n-scrollbar>
    <!-- 新建路由按钮 -->
    <div class="list-footer">
      <n-button
        type="primary"
        size="small"
        block
        :disabled="disabled || nodes.length < 2"
        @click="handleAddRoute"
      >
        新建路由
      </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'
import { NButton, NIcon } from 'naive-ui'
import { DeleteOutlined } from '@vicons/antd'

interface Props {
  routes: FlowRouteConfig[]
  nodes: FlowNodeConfig[]
  selectedIndex: number | null
  disabled?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'select', index: number): void
  (e: 'add-route'): void
  (e: 'delete', index: number): void
}>()

const getNodeName = (key: string) => {
  const found = props.nodes.find(node => node.id?.toString() === key || node.temp_id === key)
  return found?.name ?? key
}

const handleSelect = (index: number) => {
  if (props.disabled) return
  emit('select', index)
}

const handleAddRoute = () => {
  if (props.disabled) return
  emit('add-route')
}

const handleDelete = (index: number) => {
  if (props.disabled) return
  emit('delete', index)
}
</script>

<style scoped>
.route-list {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.list-header {
  flex-shrink: 0;
  margin-bottom: 8px;
}

.list-header .title {
  font-size: 14px;
  font-weight: 600;
}

.list-header .subtitle {
  font-size: 12px;
  color: #6b7385;
}

.empty-body {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.list-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  position: relative;
}

.list-body :deep(.n-scrollbar) {
  position: absolute;
  inset: 0;
}

.route-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.route-item {
  border: 1px solid transparent;
  border-radius: 10px;
  padding: 10px 12px;
  background: #f7f9fb;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.route-item.active {
  border-color: #18a058;
  background: #f0faf4;
}

.upper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.upper-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.route-index {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #18a058;
  color: white;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.name {
  font-weight: 600;
  flex: 1;
}

.delete-btn {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.route-item:hover .delete-btn {
  opacity: 1;
}

.meta {
  margin-top: 4px;
  font-size: 12px;
  color: #6b7385;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.meta .owner {
  color: #18a058;
  font-weight: 600;
}

.list-footer {
  flex-shrink: 0;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e0e5ec;
}
</style>
