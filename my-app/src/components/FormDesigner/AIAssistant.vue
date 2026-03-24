<!-- src/components/formDesigner/AIAssistant.vue -->
<template>
    <!-- 悬浮按钮 -->
    <div class="ai-assistant-fab" @click="showDrawer = true">
      <n-tooltip placement="left">
        <template #trigger>
          <n-button circle type="primary" size="large" class="fab-button">
            <template #icon>
              <n-icon size="24">
                <Icon icon="carbon:watson-health-ai-results" />
              </n-icon>
            </template>
          </n-button>
        </template>
        AI 助手
      </n-tooltip>
    </div>
  
    <!-- AI 对话抽屉 -->
    <n-drawer
      v-model:show="showDrawer"
      :width="480"
      placement="right"
      :trap-focus="false"
      :block-scroll="false"
    >
      <n-drawer-content title="AI 表单生成助手" closable>
        <div class="ai-assistant-content">
          <!-- 快速模板 -->
          <div class="quick-templates">
            <div class="section-title">快速模板</div>
            <n-space :size="8">
              <n-tag
                v-for="template in quickTemplates"
                :key="template"
                :bordered="false"
                class="template-tag"
                @click="nlInput = template"
              >
                {{ template }}
              </n-tag>
            </n-space>
          </div>
  
          <n-divider />
  
          <!-- 输入区域 -->
          <div class="input-section">
            <div class="section-title">描述你的表单需求</div>
            <n-input
              v-model:value="nlInput"
              type="textarea"
              :rows="6"
              placeholder="例如：创建一个学生请假申请表，需要姓名、学号、请假类型（事假/病假/公假）、请假时间（日期范围）、自动计算请假天数、请假事由、联系电话，病假需要上传病假证明"
              :maxlength="2000"
              show-count
            />
          </div>
  
          <!-- 高级选项 -->
          <n-collapse class="advanced-options">
            <n-collapse-item title="高级选项" name="advanced">
              <n-form :model="advancedOptions" label-placement="left" label-width="100">
                <n-form-item label="思考模式">
                  <n-radio-group v-model:value="advancedOptions.thinkingType">
                    <n-space>
                      <n-radio value="enabled">深度思考（复杂表单）</n-radio>
                      <n-radio value="disabled">快速生成（简单表单）</n-radio>
                    </n-space>
                  </n-radio-group>
                </n-form-item>
              </n-form>
            </n-collapse-item>
          </n-collapse>
  
          <!-- 生成按钮 -->
          <div class="action-buttons">
            <n-button
              type="primary"
              block
              size="large"
              :loading="generating"
              :disabled="!nlInput.trim() || nlInput.trim().length < 5"
              @click="handleGenerate"
            >
              <template #icon>
                <n-icon>
                  <Icon icon="carbon:magic-wand" />
                </n-icon>
              </template>
              AI 生成表单
            </n-button>
          </div>
  
          <!-- 生成结果预览 -->
          <transition name="fade">
            <div v-if="generatedResult" class="result-preview">
              <n-alert type="success" :bordered="false">
                <template #icon>
                  <n-icon>
                    <Icon icon="carbon:checkmark-filled" />
                  </n-icon>
                </template>
                {{ generatedResult.summary }}
              </n-alert>
  
              <div class="result-stats">
                <n-statistic label="字段数量" :value="generatedResult.field_count" />
                <n-statistic label="逻辑规则" :value="generatedResult.rule_count" />
              </div>
  
              <n-space :size="12" justify="end">
                <n-button @click="generatedResult = null">取消</n-button>
                <n-button type="primary" @click="handleApplyConfig">
                  <template #icon>
                    <n-icon>
                      <Icon icon="carbon:checkmark" />
                    </n-icon>
                  </template>
                  应用到画布
                </n-button>
              </n-space>
            </div>
          </transition>
        </div>
      </n-drawer-content>
    </n-drawer>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue'
  import { useMessage, useDialog } from 'naive-ui'
  import { Icon } from '@iconify/vue'
  import { advancedGenerateForm } from '@/api/ai'
  import { ThinkingType } from '@/types/ai'
  import type { AIFormGenerateResponse } from '@/types/ai'
  
  // 事件约束：确保 AI 产物与设计器类型对齐
  const emit = defineEmits<{
    (e: 'apply-config', config: AIFormGenerateResponse['config']): void
  }>()
  
  const message = useMessage()
  const dialog = useDialog()
  
  const showDrawer = ref(false)
  const nlInput = ref('')
  const generating = ref(false)
  const generatedResult = ref<AIFormGenerateResponse | null>(null)
  
  const advancedOptions = ref({
    thinkingType: ThinkingType.ENABLED
  })
  
  const quickTemplates = [
    '创建一个活动报名表',
    '创建一个员工入职登记表',
    '创建一个客户信息收集表',
    '创建一个问卷调查表'
  ]
  
  // 错误解析：统一转换未知异常，符合后端规范中的防御性编程原则
  const resolveErrorMessage = (error: unknown, fallback: string) =>
    error instanceof Error ? error.message : fallback
  
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
    generatedResult.value = null
  
    try {
      const response = await advancedGenerateForm(
        trimmedInput,
        advancedOptions.value.thinkingType
      )
  
      if (response.code === 2000 && response.data) {
        generatedResult.value = response.data
        message.success('生成成功！')
      } else {
        message.error(response.message || '生成失败，请重试')
      }
    } catch (error) {
      console.error('AI 生成失败:', error)
      message.error(resolveErrorMessage(error, '生成失败，请稍后重试'))
    } finally {
      generating.value = false
    }
  }
  
  /**
   * 应用配置到画布
   */
  const handleApplyConfig = () => {
    if (!generatedResult.value) return
  
    dialog.warning({
      title: '确认替换',
      content: '应用 AI 生成的配置将替换当前画布中的所有内容，是否继续？',
      positiveText: '确认',
      negativeText: '取消',
      onPositiveClick: () => {
        emit('apply-config', generatedResult.value!.config)
        showDrawer.value = false
        generatedResult.value = null
        nlInput.value = ''
        message.success('已应用 AI 配置')
      }
    })
  }
  </script>
  
  <style scoped lang="scss">
  .ai-assistant-fab {
    position: fixed;
    right: 32px;
    bottom: 32px;
    z-index: 1000;
  
    .fab-button {
      width: 56px;
      height: 56px;
      box-shadow: 0 4px 12px rgba(24, 160, 88, 0.3);
      transition: all 0.3s ease;
  
      &:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 16px rgba(24, 160, 88, 0.4);
      }
    }
  }
  
  .ai-assistant-content {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .section-title {
    font-size: 14px;
    font-weight: 500;
    color: #333;
    margin-bottom: 12px;
  }
  
  .quick-templates {
    .template-tag {
      cursor: pointer;
      transition: all 0.2s;
  
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }
    }
  }
  
  .advanced-options {
    :deep(.n-collapse-item__header) {
      font-size: 14px;
    }
  }
  
  .action-buttons {
    margin-top: 8px;
  }
  
  .result-preview {
    margin-top: 20px;
    padding: 16px;
    background: #f9fafb;
    border-radius: 8px;
  
    .result-stats {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      margin: 16px 0;
    }
  }
  
  .fade-enter-active,
  .fade-leave-active {
    transition: opacity 0.3s ease;
  }
  
  .fade-enter-from,
  .fade-leave-to {
    opacity: 0;
  }
  </style>