<template>
  <div class="route-list">
    <div class="list-header">
      <div class="title">路由列表</div>
      <div class="subtitle">点击选择需要编辑的路由</div>
    </div>
    <n-empty v-if="routes.length === 0" description="暂无路由" size="small" />
    <n-scrollbar v-else class="list-body">
      <div
        v-for="(route, index) in routes"
        :key="route.id ?? route.temp_id ?? `${route.from_node_key}-${route.to_node_key}`"
        class="route-item"
        :class="{ active: index === selectedIndex }"
        @click="handleSelect(index)"
      >
        <div class="upper">
          <span class="name">{{ getNodeName(route.from_node_key) }} → {{ getNodeName(route.to_node_key) }}</span>
          <n-tag size="small" :type="route.is_default ? 'success' : 'default'">
            {{ route.is_default ? '默认' : '条件' }}
          </n-tag>
        </div>
        <div class="meta">
          <span>优先级 {{ route.priority }}</span>
          <span v-if="route.condition">已配置条件</span>
          <span v-else>无条件</span>
        </div>
      </div>
    </n-scrollbar>
  </div>
</template>

<script setup lang="ts">
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

interface Props {
  routes: FlowRouteConfig[]
  nodes: FlowNodeConfig[]
  selectedIndex: number | null
  disabled?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'select', index: number): void
}>()

const getNodeName = (key: string) => {
  const found = props.nodes.find(node => node.id?.toString() === key || node.temp_id === key)
  return found?.name ?? key
}

const handleSelect = (index: number) => {
  if (props.disabled) return
  emit('select', index)
}
</script>

<style scoped>
.route-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.list-header .title {
  font-size: 14px;
  font-weight: 600;
}

.list-header .subtitle {
  font-size: 12px;
  color: #6b7385;
}

.list-body {
  max-height: 220px;
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
}

.name {
  font-weight: 600;
}

.meta {
  margin-top: 4px;
  font-size: 12px;
  color: #6b7385;
  display: flex;
  gap: 12px;
}
</style>
