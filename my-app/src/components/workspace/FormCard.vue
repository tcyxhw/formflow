<template>
  <div
    class="form-card"
    :class="[statusClass, { 'is-disabled': !form.can_fill, 'is-selected': isSelected }]"
    @click="handleCardClick"
    @mouseenter="showFullDescription = true"
    @mouseleave="showFullDescription = false"
  >
    <!-- 批量选择复选框 -->
    <div v-if="isBatchMode" class="batch-checkbox" @click.stop>
      <n-checkbox
        :checked="isSelected"
        @update:checked="() => emit('toggleSelection', form.id)"
      />
    </div>

    <!-- 状态标识 -->
    <div class="status-indicator" :class="statusClass"></div>

    <!-- 卡片内容 -->
    <div class="card-content">
      <!-- 标题和类别 -->
      <div class="card-header">
        <h3 class="form-title" v-html="highlightKeyword(form.name)"></h3>
        <n-tag v-if="form.category" size="small" :bordered="false">
          {{ form.category }}
        </n-tag>
      </div>

      <!-- 描述 -->
      <p v-if="form.description" class="form-description" v-html="highlightKeyword(form.description)">
      </p>

      <!-- 元信息 -->
      <div class="form-meta">
        <div class="meta-item">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="meta-icon"
          >
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          <span>{{ formatDate(form.created_at) }}</span>
        </div>

        <div v-if="form.submit_deadline" class="meta-item">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="meta-icon"
          >
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
          <span>截止: {{ formatDate(form.submit_deadline) }}</span>
        </div>

        <div class="meta-item">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="meta-icon"
          >
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
          <span>{{ form.owner_name }}</span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="card-actions" @click.stop>
        <n-button
          v-if="form.can_fill && !form.is_expired && !form.is_closed && !form.is_fill_limit_reached"
          type="primary"
          size="small"
          @click="handleFillClick"
        >
          填写
        </n-button>

        <n-button
          v-else-if="form.is_expired"
          size="small"
          disabled
        >
          已过期
        </n-button>

        <n-button
          v-else-if="form.is_closed"
          size="small"
          disabled
        >
          已关闭
        </n-button>

        <n-button
          v-else-if="form.is_fill_limit_reached"
          size="small"
          disabled
        >
          已达上限
        </n-button>

        <n-button
          v-else
          size="small"
          disabled
        >
          无权限
        </n-button>

        <n-button size="small" @click="handleDetailClick">
          查看详情
        </n-button>

        <n-button
          size="small"
          :type="isInQuickAccess ? 'default' : 'default'"
          @click="handleQuickAccessClick"
        >
          <template #icon>
            <svg
              v-if="isInQuickAccess"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              style="width: 16px; height: 16px"
            >
              <path d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
            </svg>
            <svg
              v-else
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              style="width: 16px; height: 16px"
            >
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
            </svg>
          </template>
          {{ isInQuickAccess ? '已收藏' : '收藏' }}
        </n-button>
      </div>
    </div>

    <!-- 悬停显示完整描述 -->
    <n-tooltip
      v-if="form.description && form.description.length > 100"
      :show="showFullDescription"
      placement="top"
      trigger="manual"
    >
      <template #trigger>
        <div></div>
      </template>
      {{ form.description }}
    </n-tooltip>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NTag, NTooltip, NCheckbox, useMessage } from 'naive-ui'
import type { FillableFormItem } from '@/types/workspace'
import { useQuickAccess } from '@/composables/useQuickAccess'

interface Props {
  form: FillableFormItem
  isBatchMode?: boolean
  isSelected?: boolean
  searchKeyword?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  toggleSelection: [formId: number]
}>()

const router = useRouter()
const message = useMessage()
const { isInQuickAccess: checkIsInQuickAccess, toggleQuickAccess } = useQuickAccess()

// 悬停状态
const showFullDescription = ref(false)

// 计算状态类名
const statusClass = computed(() => {
  if (props.form.is_expired) {
    return 'status-expired'
  }
  if (props.form.is_closed) {
    return 'status-closed'
  }
  
  // 检查是否即将截止（3天内）
  if (props.form.submit_deadline) {
    const deadline = new Date(props.form.submit_deadline)
    const now = new Date()
    const daysUntilDeadline = (deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
    
    if (daysUntilDeadline <= 3 && daysUntilDeadline > 0) {
      return 'status-warning'
    }
  }
  
  return 'status-active'
})

// 检查是否在快捷入口中
const isInQuickAccess = computed(() => {
  return checkIsInQuickAccess(props.form.id)
})

/**
 * 高亮搜索关键词
 * @param text 原始文本
 * @returns 高亮后的HTML字符串
 */
const highlightKeyword = (text: string | null | undefined): string => {
  if (!text || !props.searchKeyword) {
    return text || ''
  }
  
  const keyword = props.searchKeyword.trim()
  if (!keyword) {
    return text
  }
  
  // 使用正则表达式进行不区分大小写的匹配
  const regex = new RegExp(`(${keyword})`, 'gi')
  return text.replace(regex, '<mark class="highlight">$1</mark>')
}

// 格式化日期
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffTime = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return '今天'
  } else if (diffDays === 1) {
    return '昨天'
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  }
}

// 点击卡片
const handleCardClick = () => {
  // 如果是批量模式，点击卡片切换选择状态
  if (props.isBatchMode) {
    emit('toggleSelection', props.form.id)
    return
  }
  
  if (!props.form.can_fill) {
    message.warning('您没有权限填写此表单')
    return
  }
  
  if (props.form.is_expired) {
    message.warning('此表单已过期')
    return
  }
  
  if (props.form.is_closed) {
    message.warning('此表单已关闭')
    return
  }
  
  if (props.form.is_fill_limit_reached) {
    message.warning('此表单已达到填写上限')
    return
  }
  
  // 导航到表单填写页面
  router.push(`/forms/${props.form.id}/fill`)
}

// 点击填写按钮
const handleFillClick = () => {
  router.push(`/forms/${props.form.id}/fill`)
}

// 点击查看详情按钮
const handleDetailClick = () => {
  router.push(`/forms/${props.form.id}/detail`)
}

// 点击快捷入口按钮
const handleQuickAccessClick = async () => {
  const success = await toggleQuickAccess(props.form.id, props.form)
  
  if (success) {
    if (isInQuickAccess.value) {
      message.success('已从快捷入口移除')
    } else {
      message.success('已添加到快捷入口')
    }
  } else {
    message.error('操作失败，请重试')
  }
}
</script>

<style scoped>
.form-card {
  position: relative;
  padding: 20px;
  background-color: var(--n-color);
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
}

.form-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.form-card.is-disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.form-card.is-disabled:hover {
  transform: none;
  box-shadow: none;
}

.form-card.is-selected {
  border-color: var(--n-color-target);
  background-color: rgba(24, 160, 88, 0.05);
}

/* 批量选择复选框 */
.batch-checkbox {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 10;
}

/* 状态指示器 */
.status-indicator {
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  transition: background-color 0.3s ease;
}

.status-active .status-indicator {
  background-color: #18a058; /* 绿色 - 进行中 */
}

.status-warning .status-indicator {
  background-color: #f0a020; /* 黄色 - 即将截止 */
}

.status-expired .status-indicator,
.status-closed .status-indicator {
  background-color: #d0d0d0; /* 灰色 - 已过期/已关闭 */
}

/* 卡片内容 */
.card-content {
  padding-left: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.form-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--n-text-color);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.form-description {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--n-text-color-2);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* 元信息 */
.form-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 13px;
  color: var(--n-text-color-3);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

/* 操作按钮 */
.card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>

/* 搜索关键词高亮 */
.form-card :deep(mark.highlight) {
  background-color: #fff59d;
  color: #000;
  padding: 2px 4px;
  border-radius: 2px;
  font-weight: 500;
}
