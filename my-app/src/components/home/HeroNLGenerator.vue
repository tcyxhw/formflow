<!-- src/components/home/HeroNLGenerator.vue -->
<template>
  <div class="nl-generator">
    <!-- 生成器卡片 -->
    <div class="generator-card">
      <div class="card-content">
        <div class="input-section">
          <n-input
            v-model:value="nlInput"
            type="textarea"
            :rows="3"
            placeholder="我想创建「会议室预约表」,包含主题、起止时间、人数、设备、备注"
            size="large"
            :maxlength="2000"
            show-count
            class="nl-input"
            :disabled="generating"
            @keyup.enter.ctrl="handleGenerate"
          />
        </div>
        
        <div class="action-row">
          <div class="hint-text">
            <n-icon :component="SparklesOutline" size="18" />
            <span>按 <kbd>Ctrl+Enter</kbd> 快速生成</span>
          </div>
          <n-space>
            <n-button
              v-if="generating"
              size="large"
              @click="handleCancel"
            >
              <template #icon>
                <n-icon :component="CloseOutline" />
              </template>
              取消
            </n-button>
            <n-button
              type="primary"
              size="large"
              :loading="generating"
              :disabled="!nlInput.trim() || nlInput.trim().length < 5"
              class="generate-btn"
              @click="handleGenerate"
            >
              <template #icon>
                <n-icon :component="SparklesOutline" />
              </template>
              {{ generating ? 'AI 生成中...' : '一键生成' }}
            </n-button>
          </n-space>
        </div>

        <!-- 进度提示 -->
        <transition name="fade">
          <div v-if="generating" class="progress-section">
            <n-progress
              type="line"
              :percentage="progress"
              status="success"
              :show-indicator="false"
            />
            <n-alert type="info" :bordered="false" style="margin-top: 12px">
              <template #icon>
                <n-icon :component="TimeOutline" />
              </template>
              {{ progressText }}
            </n-alert>
          </div>
        </transition>
      </div>
    </div>

    <!-- 生成的表单预览 -->
    <transition name="preview-slide">
      <div v-if="generatedConfig" class="preview-card">
        <div class="card-header">
          <div class="header-content">
            <h3 class="card-title">{{ generatedConfig.config.name }}</h3>
            <n-space :size="8">
              <n-tag type="success" size="small">
                <template #icon>
                  <n-icon :component="CheckmarkCircleOutline" />
                </template>
                AI 生成
              </n-tag>
              <n-tag v-if="generatedConfig.config.category" :bordered="false" size="small">
                {{ generatedConfig.config.category }}
              </n-tag>
            </n-space>
          </div>
        </div>
        
        <div class="card-content">
          <!-- 配置说明 -->
          <n-alert type="success" :bordered="false" style="margin-bottom: 16px">
            {{ generatedConfig.summary }}
          </n-alert>

          <!-- 统计信息 -->
          <div class="stats-row">
            <n-statistic label="字段数量" :value="generatedConfig.field_count">
              <template #suffix>个</template>
            </n-statistic>
            <n-statistic label="逻辑规则" :value="generatedConfig.rule_count">
              <template #suffix>条</template>
            </n-statistic>
            <n-statistic 
              label="访问模式" 
              :value="accessModeText"
            />
          </div>

          <n-divider />

          <!-- 字段列表预览 -->
          <div class="fields-section">
            <div class="section-title">字段列表</div>
            <div class="fields-container">
              <div
                v-for="field in generatedConfig.config.formSchema.fields"
                :key="field.id"
                class="field-item"
              >
                <n-tag 
                  :type="getFieldColor(field.type)" 
                  size="large"
                  class="field-tag"
                >
                  <template #icon>
                    <n-icon :component="getFieldIcon(field.type)" />
                  </template>
                  <span class="field-label">{{ field.label }}</span>
                  <span class="field-type">· {{ field.type }}</span>
                </n-tag>
                <n-badge 
                  v-if="field.required" 
                  value="必填" 
                  type="error"
                />
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="card-actions">
            <n-space :size="12" justify="end">
              <n-button size="medium" @click="handleRegenerate">
                <template #icon>
                  <n-icon :component="RefreshOutline" />
                </template>
                重新生成
              </n-button>
              <n-button type="primary" size="medium" @click="handleUseConfig">
                <template #icon>
                  <n-icon :component="CreateOutline" />
                </template>
                进入编辑器
              </n-button>
            </n-space>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Component } from 'vue'
import { isAxiosError } from 'axios'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { 
  SparklesOutline, 
  TextOutline, 
  CalendarOutline, 
  PeopleOutline, 
  AttachOutline,
  CheckmarkCircleOutline,
  RefreshOutline,
  CreateOutline,
  TimeOutline,
  CloseOutline,
  DocumentTextOutline
} from '@vicons/ionicons5'
import { quickGenerateForm } from '@/api/ai'
import type { AIFormGenerateResponse } from '@/types/ai'
import { ConfigTransfer } from '@/utils/configTransfer'

const router = useRouter()
const message = useMessage()

// ========== 状态管理 ==========
const nlInput = ref('')
const generating = ref(false)
const generatedConfig = ref<AIFormGenerateResponse | null>(null)
const progress = ref(0)
const progressTimer = ref<number | null>(null)

// ========== 计算属性 ==========
const accessModeText = computed(() => {
  if (!generatedConfig.value) return ''
  return generatedConfig.value.config.accessMode === 'authenticated' 
    ? '需登录' 
    : '公开访问'
})

const progressText = computed(() => {
  if (progress.value < 30) {
    return 'AI 正在分析需求...'
  } else if (progress.value < 60) {
    return '正在生成字段配置...'
  } else if (progress.value < 90) {
    return '正在优化布局和规则...'
  } else {
    return '即将完成...'
  }
})

// ========== 核心方法 ==========

/**
 * 处理 AI 生成
 */
 const handleGenerate = async () => {
  const trimmedInput = nlInput.value.trim()
  
  if (!trimmedInput) {
    message.warning('请输入表单需求描述')
    return
  }
  
  if (trimmedInput.length < 5) {
    message.warning('需求描述至少需要 5 个字符')
    return
  }

  generating.value = true
  generatedConfig.value = null
  progress.value = 0

  startProgressSimulation()

  try {
    const response = await quickGenerateForm(trimmedInput)

    stopProgressSimulation()
    progress.value = 100

    // ✅ 修复：兼容 200 和 2000 两种响应码
    if ((response.code === 200 || response.code === 2000) && response.data) {
      generatedConfig.value = response.data
      message.success(response.data.summary || '表单生成成功！')
    } else {
      message.error(response.message || '生成失败，请重试')
    }
  } catch (error: unknown) {
    stopProgressSimulation()
    
    console.error('AI 生成失败:', error)

    if (isAxiosError(error)) {
      const status = error.response?.status
      const messageFromServer = error.response?.data?.message as string | undefined
      const errorMessage = messageFromServer || error.message || '生成失败，请稍后重试'

      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        message.error('生成超时，请尝试简化需求描述或稍后重试')
      } else if (status === 400) {
        message.error(messageFromServer || '请求参数错误，请检查输入内容')
      } else if (status === 500) {
        message.error('服务器错误，请稍后重试')
      } else {
        message.error(errorMessage)
      }
    } else {
      message.error(resolveErrorMessage(error, '生成失败，请稍后重试'))
    }
  } finally {
    generating.value = false
    progress.value = 0
  }
}

/**
 * 启动进度模拟（视觉反馈）
 */
 const startProgressSimulation = () => {
  progressTimer.value = setInterval(() => {
    if (progress.value < 90) {
      if (progress.value < 30) {
        progress.value += 2
      } else if (progress.value < 60) {
        progress.value += 1.5
      } else {
        progress.value += 0.5
      }
    }
  }, 1000) as unknown as number  // ✅ 类型断言
}

/**
 * 停止进度模拟
 */
const stopProgressSimulation = () => {
  if (progressTimer.value) {
    clearInterval(progressTimer.value)
    progressTimer.value = null
  }
}

/**
 * 取消生成
 */
const handleCancel = () => {
  stopProgressSimulation()
  generating.value = false
  progress.value = 0
  message.warning('已取消生成')
}

/**
 * 重新生成
 */
const handleRegenerate = () => {
  generatedConfig.value = null
  handleGenerate()
}

/**
 * 使用配置进入编辑器
 */
 const handleUseConfig = () => {
  if (!generatedConfig.value) {
    message.warning('没有可用的配置')
    return
  }

  console.log('[生成器] 准备跳转，配置:', generatedConfig.value.config)
  console.log('[生成器] 字段数量:', generatedConfig.value.config.formSchema.fields.length)

  // ✅ 使用 sessionStorage 传递配置
  ConfigTransfer.saveConfig(generatedConfig.value.config)

  // 跳转到设计器
  router.push({
    name: 'FormDesigner',
    query: {
      from: 'ai'  // ✅ 添加标记，表示来自 AI 生成
    }
  }).then(() => {
    console.log('[生成器] 跳转成功')
  }).catch((error) => {
    console.error('[生成器] 跳转失败:', error)
    message.error('跳转失败')
  })
}

// ========== 工具方法 ==========

/**
 * 获取字段颜色
 */
const getFieldColor = (type: string): 'info' | 'success' | 'warning' | 'error' | 'default' => {
  const colorMap: Record<string, 'info' | 'success' | 'warning' | 'error' | 'default'> = {
    text: 'info',
    textarea: 'info',
    number: 'success',
    phone: 'success',
    email: 'success',
    date: 'warning',
    'date-range': 'warning',
    time: 'warning',
    datetime: 'warning',
    select: 'default',
    radio: 'default',
    checkbox: 'default',
    switch: 'default',
    rate: 'error',
    upload: 'error',
    calculated: 'success',
    divider: 'default',
    description: 'default'
  }
  return colorMap[type] || 'default'
}

/**
 * 获取字段图标
 */
const getFieldIcon = (type: string): Component => {
  const iconMap: Record<string, Component> = {
    text: TextOutline,
    textarea: DocumentTextOutline,
    number: TextOutline,
    phone: TextOutline,
    email: TextOutline,
    date: CalendarOutline,
    'date-range': CalendarOutline,
    time: CalendarOutline,
    datetime: CalendarOutline,
    select: PeopleOutline,
    radio: PeopleOutline,
    checkbox: PeopleOutline,
    switch: PeopleOutline,
    rate: TextOutline,
    upload: AttachOutline,
    calculated: TextOutline,
    divider: TextOutline,
    description: DocumentTextOutline
  }
  return iconMap[type] || TextOutline
}

const resolveErrorMessage = (error: unknown, fallback: string) =>
  error instanceof Error ? error.message : fallback
</script>

<style scoped>
.nl-generator {
  width: 100%;
}

/* 生成器卡片 */
.generator-card {
  border-radius: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  transition: all 260ms cubic-bezier(0.4, 0, 0.2, 1);
}

.generator-card:hover {
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.1);
}

.card-content {
  padding: 24px;
}

/* 输入区域 */
.input-section {
  width: 100%;
  margin-bottom: 20px;
}

.nl-input {
  font-size: 15px;
}

:deep(.n-input__textarea-el) {
  font-size: 15px !important;
  line-height: 1.6 !important;
}

/* 操作行 */
.action-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.hint-text {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #666;
}

.hint-text kbd {
  display: inline-block;
  padding: 2px 6px;
  font-size: 12px;
  font-family: 'Courier New', monospace;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  margin: 0 2px;
}

/* 生成按钮 */
.generate-btn {
  min-width: 140px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(24, 160, 88, 0.2);
  transition: all 260ms cubic-bezier(0.4, 0, 0.2, 1);
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(24, 160, 88, 0.3);
}

.generate-btn:active:not(:disabled) {
  transform: translateY(0);
}

/* 进度区域 */
.progress-section {
  margin-top: 20px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

/* 预览卡片 */
.preview-card {
  margin-top: 24px;
  border-radius: 16px;
  background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
  box-shadow: 0 4px 20px rgba(24, 160, 88, 0.08);
  border-left: 4px solid #18a058;
  overflow: hidden;
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(24, 160, 88, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.card-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
}

/* 统计信息 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 24px;
  margin-bottom: 16px;
  padding: 0 24px;
}

/* 字段区域 */
.fields-section {
  padding: 0 24px 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: #666;
  margin-bottom: 12px;
}

.fields-container {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.field-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 14px;
  border-radius: 10px;
  transition: all 260ms cubic-bezier(0.4, 0, 0.2, 1);
  cursor: default;
}

.field-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.field-label {
  font-weight: 600;
}

.field-type {
  font-size: 12px;
  opacity: 0.7;
}

/* 卡片操作 */
.card-actions {
  padding: 16px 24px 20px;
  border-top: 1px solid rgba(24, 160, 88, 0.1);
}

/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 预览滑动动画 */
.preview-slide-enter-active {
  animation: previewSlideIn 320ms cubic-bezier(0.4, 0, 0.2, 1);
}

.preview-slide-leave-active {
  animation: previewSlideOut 240ms cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes previewSlideIn {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes previewSlideOut {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-12px);
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .generator-card,
  .preview-card {
    border-radius: 12px;
  }

  .card-content {
    padding: 20px;
  }

  .preview-card {
    margin-top: 16px;
  }

  .action-row {
    flex-direction: column;
    align-items: stretch;
  }

  .hint-text {
    font-size: 13px;
    justify-content: center;
  }

  .generate-btn {
    width: 100%;
  }

  .stats-row {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 0 20px;
  }

  .fields-section {
    padding: 0 20px 16px;
  }

  .fields-container {
    gap: 10px;
  }

  .card-header,
  .card-actions {
    padding-left: 20px;
    padding-right: 20px;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (prefers-reduced-motion: reduce) {
  .generator-card,
  .generate-btn,
  .field-tag,
  .preview-slide-enter-active,
  .preview-slide-leave-active {
    transition: none;
    animation: none;
  }

  .generate-btn:hover,
  .field-tag:hover {
    transform: none;
  }
}
</style>