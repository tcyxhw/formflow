<template>
  <div class="quick-access">
    <!-- 标题栏 -->
    <div class="quick-access-header">
      <h2 class="quick-access-title">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          class="title-icon"
        >
          <path d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
        </svg>
        快捷入口
      </h2>
      <n-button
        v-if="!loading && quickAccessForms.length > 0"
        text
        size="small"
        @click="handleRefresh"
      >
        <template #icon>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            style="width: 16px; height: 16px"
          >
            <polyline points="23 4 23 10 17 10"></polyline>
            <polyline points="1 20 1 14 7 14"></polyline>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
        </template>
        刷新
      </n-button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="quick-access-loading">
      <n-spin size="small" />
      <span>加载中...</span>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="quick-access-error">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="error-icon"
      >
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <span>{{ error }}</span>
      <n-button size="small" @click="handleRefresh">重试</n-button>
    </div>

    <!-- 空状态 -->
    <div v-else-if="quickAccessForms.length === 0" class="quick-access-empty">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="empty-icon"
      >
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
      </svg>
      <span>暂无快捷入口</span>
      <p class="empty-hint">在表单卡片上点击"收藏"按钮添加快捷入口</p>
    </div>

    <!-- 快捷入口列表 -->
    <div v-else class="quick-access-list-wrapper">
      <div class="quick-access-list" ref="listRef">
        <div
          v-for="form in quickAccessForms"
          :key="form.id"
          class="quick-access-item"
          :class="getStatusClass(form)"
          @click="handleNavigate(form)"
        >
          <!-- 状态指示器 -->
          <div class="item-indicator" :class="getStatusClass(form)"></div>

          <!-- 表单信息 -->
          <div class="item-content">
            <h3 class="item-title">{{ form.name }}</h3>
            <div class="item-meta">
              <n-tag v-if="form.category" size="tiny" :bordered="false">
                {{ form.category }}
              </n-tag>
              <span v-if="form.submit_deadline" class="deadline">
                截止: {{ formatDeadline(form.submit_deadline) }}
              </span>
            </div>
          </div>

          <!-- 移除按钮 -->
          <n-button
            text
            size="small"
            class="remove-btn"
            @click.stop="handleRemove(form.id)"
          >
            <template #icon>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                style="width: 16px; height: 16px"
              >
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </template>
          </n-button>
        </div>
      </div>

      <!-- 滚动控制按钮 -->
      <div v-if="showScrollButtons" class="scroll-controls">
        <n-button
          circle
          size="small"
          :disabled="!canScrollLeft"
          @click="scrollLeft"
        >
          <template #icon>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              style="width: 16px; height: 16px"
            >
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </template>
        </n-button>
        <n-button
          circle
          size="small"
          :disabled="!canScrollRight"
          @click="scrollRight"
        >
          <template #icon>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              style="width: 16px; height: 16px"
            >
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </template>
        </n-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NTag, NSpin, useMessage } from 'naive-ui'
import { useQuickAccess } from '@/composables/useQuickAccess'
import type { FillableFormItem } from '@/types/workspace'

const router = useRouter()
const message = useMessage()
const {
  quickAccessForms,
  loading,
  error,
  loadQuickAccess,
  removeFromQuickAccess
} = useQuickAccess()

// 列表容器引用
const listRef = ref<HTMLElement | null>(null)

// 滚动状态
const canScrollLeft = ref(false)
const canScrollRight = ref(false)
const showScrollButtons = ref(false)

// 初始化加载
onMounted(() => {
  loadQuickAccess()
  
  // 监听窗口大小变化
  window.addEventListener('resize', updateScrollState)
  
  // 延迟检查滚动状态（等待DOM渲染）
  setTimeout(updateScrollState, 100)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateScrollState)
})

// 更新滚动状态
const updateScrollState = () => {
  if (!listRef.value) return
  
  const { scrollLeft, scrollWidth, clientWidth } = listRef.value
  
  showScrollButtons.value = scrollWidth > clientWidth
  canScrollLeft.value = scrollLeft > 0
  canScrollRight.value = scrollLeft < scrollWidth - clientWidth - 1
}

// 向左滚动
const scrollLeft = () => {
  if (!listRef.value) return
  
  listRef.value.scrollBy({
    left: -300,
    behavior: 'smooth'
  })
  
  setTimeout(updateScrollState, 300)
}

// 向右滚动
const scrollRight = () => {
  if (!listRef.value) return
  
  listRef.value.scrollBy({
    left: 300,
    behavior: 'smooth'
  })
  
  setTimeout(updateScrollState, 300)
}

// 刷新列表
const handleRefresh = async () => {
  await loadQuickAccess(false)
  message.success('已刷新')
}

// 导航到表单
const handleNavigate = (form: FillableFormItem) => {
  if (!form.can_fill) {
    message.warning('您没有权限填写此表单')
    return
  }
  
  if (form.is_expired) {
    message.warning('此表单已过期')
    return
  }
  
  if (form.is_closed) {
    message.warning('此表单已关闭')
    return
  }
  
  router.push(`/forms/${form.id}/fill`)
}

// 移除快捷入口
const handleRemove = async (formId: number) => {
  const success = await removeFromQuickAccess(formId)
  
  if (success) {
    message.success('已从快捷入口移除')
    // 更新滚动状态
    setTimeout(updateScrollState, 100)
  } else {
    message.error('移除失败，请重试')
  }
}

// 获取状态类名
const getStatusClass = (form: FillableFormItem): string => {
  if (form.is_expired) {
    return 'status-expired'
  }
  if (form.is_closed) {
    return 'status-closed'
  }
  
  // 检查是否即将截止（3天内）
  if (form.submit_deadline) {
    const deadline = new Date(form.submit_deadline)
    const now = new Date()
    const daysUntilDeadline = (deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
    
    if (daysUntilDeadline <= 3 && daysUntilDeadline > 0) {
      return 'status-warning'
    }
  }
  
  return 'status-active'
}

// 格式化截止时间
const formatDeadline = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffTime = date.getTime() - now.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays < 0) {
    return '已截止'
  } else if (diffDays === 0) {
    return '今天'
  } else if (diffDays === 1) {
    return '明天'
  } else if (diffDays <= 7) {
    return `${diffDays}天后`
  } else {
    return date.toLocaleDateString('zh-CN', {
      month: '2-digit',
      day: '2-digit'
    })
  }
}
</script>

<style scoped>
.quick-access {
  margin-bottom: 24px;
  padding: 20px;
  background-color: var(--n-color);
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
}

/* 标题栏 */
.quick-access-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.quick-access-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--n-text-color);
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  width: 20px;
  height: 20px;
  color: var(--n-primary-color);
}

/* 加载状态 */
.quick-access-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 0;
  color: var(--n-text-color-3);
}

/* 错误状态 */
.quick-access-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 0;
  color: var(--n-text-color-3);
}

.error-icon {
  width: 32px;
  height: 32px;
  color: var(--n-error-color);
}

/* 空状态 */
.quick-access-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 0;
  color: var(--n-text-color-3);
}

.empty-icon {
  width: 32px;
  height: 32px;
  opacity: 0.5;
}

.empty-hint {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: var(--n-text-color-3);
}

/* 列表容器 */
.quick-access-list-wrapper {
  position: relative;
}

.quick-access-list {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  scroll-behavior: smooth;
  padding-bottom: 8px;
  
  /* 隐藏滚动条 */
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.quick-access-list::-webkit-scrollbar {
  display: none;
}

/* 快捷入口项 */
.quick-access-item {
  position: relative;
  flex-shrink: 0;
  width: 280px;
  padding: 16px;
  background-color: var(--n-color);
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
}

.quick-access-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.quick-access-item:hover .remove-btn {
  opacity: 1;
}

/* 状态指示器 */
.item-indicator {
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  transition: background-color 0.3s ease;
}

.status-active .item-indicator {
  background-color: #18a058;
}

.status-warning .item-indicator {
  background-color: #f0a020;
}

.status-expired .item-indicator,
.status-closed .item-indicator {
  background-color: #d0d0d0;
}

/* 项内容 */
.item-content {
  padding-left: 8px;
  padding-right: 32px;
}

.item-title {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--n-text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--n-text-color-3);
}

.deadline {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 移除按钮 */
.remove-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

/* 滚动控制按钮 */
.scroll-controls {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  transform: translateY(-50%);
  display: flex;
  justify-content: space-between;
  pointer-events: none;
  padding: 0 -8px;
}

.scroll-controls .n-button {
  pointer-events: auto;
  background-color: var(--n-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* 禁用状态样式 */
.quick-access-item.status-expired,
.quick-access-item.status-closed {
  opacity: 0.6;
  cursor: not-allowed;
}

.quick-access-item.status-expired:hover,
.quick-access-item.status-closed:hover {
  transform: none;
  box-shadow: none;
}
</style>
