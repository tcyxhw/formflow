<template>
  <n-card title="节点库" size="small" class="palette-card">
    <div class="palette-grid">
      <n-button
        v-for="item in nodeTypes"
        :key="item.type"
        strong
        secondary
        :disabled="disabled"
        @click="() => emitAddNode(item.type)"
      >
        <template #icon>
          <n-icon size="16">
            <Icon :icon="item.icon" />
          </n-icon>
        </template>
        {{ item.label }}
      </n-button>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import { useThemeVars } from 'naive-ui'
import type { FlowNodeType } from '@/types/flow'

interface Props {
  disabled?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{ (e: 'add-node', nodeType: FlowNodeType): void }>()

const themeVars = useThemeVars()

const nodeTypes = computed(() => [
  { type: 'start' as FlowNodeType, label: '开始节点', icon: 'carbon:play-outline' },
  { type: 'user' as FlowNodeType, label: '人工审批', icon: 'carbon:user-identification' },
  { type: 'auto' as FlowNodeType, label: '自动节点', icon: 'carbon:ai-status' },
  { type: 'end' as FlowNodeType, label: '结束节点', icon: 'carbon:flag-finish' }
])

const emitAddNode = (type: FlowNodeType) => {
  if (props.disabled) return
  emit('add-node', type)
}
</script>

<style scoped>
.palette-card {
  height: 100%;
}

.palette-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.palette-grid :deep(.n-button) {
  justify-content: flex-start;
}
</style>
