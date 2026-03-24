<template>
  <div class="shortcut-hints">
    <n-button
      text
      type="primary"
      @click="showModal = true"
      class="shortcut-help-btn"
    >
      <template #icon>
        <n-icon><QuestionCircle /></n-icon>
      </template>
      快捷键
    </n-button>

    <n-modal
      v-model:show="showModal"
      title="快捷键帮助"
      preset="dialog"
      size="small"
      :show-icon="false"
      class="shortcut-modal"
    >
      <div class="shortcuts-list">
        <div
          v-for="shortcut in shortcuts"
          :key="shortcut.action"
          class="shortcut-item"
        >
          <div class="shortcut-keys">
            <span
              v-for="(key, idx) in shortcut.keys"
              :key="idx"
              class="key-badge"
            >
              {{ formatKey(key) }}
            </span>
          </div>
          <div class="shortcut-info">
            <div class="shortcut-name">{{ shortcut.name }}</div>
            <div class="shortcut-description">{{ shortcut.description }}</div>
          </div>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NButton, NIcon, NModal } from 'naive-ui'
import { QuestionCircle } from '@vicons/antd'
import { getAllShortcuts } from '@/constants/shortcuts'
import type { ShortcutConfig } from '@/constants/shortcuts'

const showModal = ref(false)
const shortcuts = getAllShortcuts()

const formatKey = (key: string): string => {
  const isMac = /Mac|iPhone|iPad|iPod/.test(navigator.platform)

  if (key === 'Ctrl') {
    return isMac ? '⌘' : 'Ctrl'
  }
  if (key === 'Shift') {
    return isMac ? '⇧' : 'Shift'
  }
  if (key === 'Alt') {
    return isMac ? '⌥' : 'Alt'
  }
  return key
}
</script>

<style scoped>
.shortcut-hints {
  display: flex;
  align-items: center;
}

.shortcut-help-btn {
  font-size: 12px;
}

.shortcuts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.shortcut-item {
  display: flex;
  gap: 12px;
  padding: 8px;
  border-radius: 6px;
  background-color: #f5f7fa;
  align-items: flex-start;
}

.shortcut-keys {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
  min-width: 80px;
}

.key-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;
  background-color: white;
  border: 1px solid #d3d8de;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  color: #333;
  min-width: 32px;
  text-align: center;
}

.shortcut-info {
  flex: 1;
  min-width: 0;
}

.shortcut-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 2px;
}

.shortcut-description {
  font-size: 12px;
  color: #666;
}

:deep(.shortcut-modal) {
  .n-modal-body {
    padding: 16px;
  }
}
</style>
