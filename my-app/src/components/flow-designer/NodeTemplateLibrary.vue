<template>
  <div class="node-template-library">
    <!-- 头部 -->
    <div class="library-header">
      <div class="title">节点模板库</div>
      <div class="subtitle">选择预定义模板快速创建节点</div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="library-toolbar">
      <n-input
        v-model:value="searchQuery"
        type="text"
        placeholder="搜索模板..."
        clearable
        :style="{ flex: 1 }"
      >
        <template #prefix>
          <n-icon>
            <SearchOutlined />
          </n-icon>
        </template>
      </n-input>

      <n-select
        v-model:value="selectedCategory"
        :options="categoryOptions"
        placeholder="选择分类"
        clearable
        :style="{ width: '150px', marginLeft: '12px' }"
      />
    </div>

    <!-- 模板列表 -->
    <div class="library-content">
      <div v-if="filteredTemplates.length === 0" class="empty-state">
        <n-empty description="没有找到匹配的模板" />
      </div>

      <div v-else class="templates-grid">
        <div
          v-for="template in filteredTemplates"
          :key="template.id"
          class="template-card"
          @click="selectTemplate(template)"
        >
          <div class="template-header">
            <div class="template-name">{{ template.name }}</div>
            <n-tag
              v-if="template.usageCount && template.usageCount > 0"
              type="info"
              size="small"
            >
              已用 {{ template.usageCount }} 次
            </n-tag>
          </div>

          <div class="template-description">{{ template.description }}</div>

          <div class="template-meta">
            <span class="meta-item">
              <n-icon size="small">
                <TagsOutlined />
              </n-icon>
              {{ template.category }}
            </span>
            <span class="meta-item">
              <n-icon size="small">
                <FileOutlined />
              </n-icon>
              {{ template.type }}
            </span>
          </div>

          <div class="template-actions">
            <n-button
              type="primary"
              size="small"
              @click.stop="applyTemplate(template)"
            >
              应用
            </n-button>
            <n-button
              text
              type="default"
              size="small"
              @click.stop="previewTemplate(template)"
            >
              预览
            </n-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 预览对话框 -->
    <n-modal
      v-model:show="showPreview"
      title="模板预览"
      preset="dialog"
      size="large"
      :mask-closable="false"
    >
      <div v-if="previewTemplate" class="preview-content">
        <n-descriptions :columns="1" size="small">
          <n-descriptions-item label="模板名称">
            {{ previewTemplate.name }}
          </n-descriptions-item>
          <n-descriptions-item label="模板描述">
            {{ previewTemplate.description }}
          </n-descriptions-item>
          <n-descriptions-item label="节点类型">
            {{ previewTemplate.type }}
          </n-descriptions-item>
          <n-descriptions-item label="分类">
            {{ previewTemplate.category }}
          </n-descriptions-item>
          <n-descriptions-item label="配置信息">
            <n-code
              :code="JSON.stringify(previewTemplate.config, null, 2)"
              language="json"
              :show-line-numbers="false"
            />
          </n-descriptions-item>
        </n-descriptions>
      </div>

      <template #action>
        <n-button @click="showPreview = false">关闭</n-button>
        <n-button
          type="primary"
          @click="applyTemplate(previewTemplate!)"
        >
          应用此模板
        </n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  NInput,
  NSelect,
  NButton,
  NTag,
  NIcon,
  NEmpty,
  NModal,
  NDescriptions,
  NDescriptionsItem,
  NCode
} from 'naive-ui'
import { SearchOutlined, TagsOutlined, FileOutlined } from '@vicons/antd'
import type { NodeTemplate, NodeTemplateCategory } from '@/types/nodeTemplate'
import { BUILTIN_NODE_TEMPLATES, getAllCategories } from '@/constants/nodeTemplates'

interface Props {
  disabled?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'apply-template', template: NodeTemplate): void
}>()

// 状态
const searchQuery = ref('')
const selectedCategory = ref<string | null>(null)
const showPreview = ref(false)
const previewTemplateData = ref<NodeTemplate | null>(null)

// 计算属性
const categoryOptions = computed(() => {
  const categories = getAllCategories()
  return categories.map(cat => ({
    label: cat,
    value: cat
  }))
})

const filteredTemplates = computed(() => {
  let templates = BUILTIN_NODE_TEMPLATES

  // 按分类筛选
  if (selectedCategory.value) {
    templates = templates.filter(t => t.category === selectedCategory.value)
  }

  // 按搜索词筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    templates = templates.filter(
      t =>
        t.name.toLowerCase().includes(query) ||
        t.description.toLowerCase().includes(query) ||
        t.id.toLowerCase().includes(query)
    )
  }

  return templates
})

const previewTemplate = computed(() => previewTemplateData.value)

// 方法
const selectTemplate = (template: NodeTemplate) => {
  previewTemplateData.value = template
  showPreview.value = true
}

const previewTemplate_ = (template: NodeTemplate) => {
  previewTemplateData.value = template
  showPreview.value = true
}

const applyTemplate = (template: NodeTemplate) => {
  emit('apply-template', template)
  showPreview.value = false
}
</script>

<style scoped>
.node-template-library {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e0e5ec;
  overflow: hidden;
}

.library-header {
  padding: 20px 24px;
  background: linear-gradient(135deg, #f6fbf8 0%, #f0f6ff 100%);
  border-bottom: 1px solid #e0e5ec;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.subtitle {
  font-size: 12px;
  color: #6b7385;
  margin-top: 4px;
}

.library-toolbar {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  border-bottom: 1px solid #e0e5ec;
  background: #fafbfc;
}

.library-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.template-card {
  display: flex;
  flex-direction: column;
  padding: 16px;
  border: 1px solid #e0e5ec;
  border-radius: 8px;
  background: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
}

.template-card:hover {
  border-color: #0ea5e9;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15);
  transform: translateY(-2px);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 8px;
}

.template-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.template-description {
  font-size: 12px;
  color: #6b7385;
  margin-bottom: 12px;
  line-height: 1.5;
  flex: 1;
}

.template-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 12px;
  color: #6b7385;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.template-actions {
  display: flex;
  gap: 8px;
  margin-top: auto;
}

.preview-content {
  padding: 16px 0;
}

:deep(.n-code) {
  margin-top: 8px;
}
</style>
