<!-- src/views/submissions/SubmissionDetailView.vue -->
<template>
  <div class="submission-detail-page">
    <n-spin :show="loading">
      <n-page-header @back="goBack">
        <template #title>
          提交详情
        </template>
        <template #extra>
          <n-button @click="goHome">
            <template #icon>
              <n-icon>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
              </n-icon>
            </template>
            返回主页
          </n-button>
        </template>
      </n-page-header>

      <n-alert
        v-if="!loading && !submission"
        type="warning"
        title="未找到对应的提交记录"
        class="mt-2"
      />

      <template v-else-if="submission">
        <!-- 基本信息 -->
        <n-card title="基本信息" :bordered="false" style="margin-bottom: 16px;">
          <n-descriptions label-placement="left" :column="1" bordered size="small">
            <n-descriptions-item label="提交 ID">
              {{ submission.id }}
            </n-descriptions-item>
            <n-descriptions-item label="表单名称">
              {{ submission.form_name }}
            </n-descriptions-item>
            <n-descriptions-item label="提交时间">
              {{ formatDate(submission.created_at) }}
            </n-descriptions-item>
          </n-descriptions>
        </n-card>

        <!-- 表单数据 -->
        <n-card :bordered="false" class="data-card">
          <template #header>
            <div class="data-header">
              <h3>表单数据</h3>
              <n-button text type="primary" @click="toggleRawData">
                {{ showRawData ? '隐藏原始 JSON' : '查看原始 JSON' }}
              </n-button>
            </div>
          </template>

          <n-descriptions label-placement="left" :column="1" bordered size="small">
            <n-descriptions-item
              v-for="item in displayFields"
              :key="item.key"
              :label="item.label"
            >
              <!-- 附件/图片字段 -->
              <template v-if="item.fieldType === 'upload' || item.fieldType === 'image'">
                <template v-if="item.attachments && item.attachments.length > 0">
                  <n-space vertical :size="8">
                    <div
                      v-for="file in item.attachments"
                      :key="file.id"
                      class="attachment-item"
                    >
                      <!-- 图片预览 -->
                      <template v-if="isImage(file.content_type)">
                        <div class="image-preview-wrapper">
                          <AuthImage
                            :src="`/api/v1/attachments/${file.id}/download?inline=true`"
                            :alt="file.file_name"
                            :width="200"
                            :height="150"
                            object-fit="cover"
                            :preview-src="`/api/v1/attachments/${file.id}/download?inline=true`"
                            fallback-src="/image-placeholder.png"
                          />
                          <div class="image-actions">
                            <n-button
                              text
                              type="primary"
                              size="small"
                              @click="downloadFile(file)"
                            >
                              下载原图
                            </n-button>
                          </div>
                        </div>
                      </template>
                      <!-- 文件下载 -->
                      <template v-else>
                        <n-button
                          text
                          type="primary"
                          @click="downloadFile(file)"
                        >
                          <template #icon>
                            <n-icon>
                              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="7 10 12 15 17 10"/>
                                <line x1="12" y1="15" x2="12" y2="3"/>
                              </svg>
                            </n-icon>
                          </template>
                          {{ file.file_name }}
                        </n-button>
                        <span class="file-size">({{ formatFileSize(file.size) }})</span>
                      </template>
                    </div>
                  </n-space>
                </template>
                <template v-else>
                  <span class="empty-value">未上传</span>
                </template>
              </template>
              <!-- 日期范围字段 -->
              <template v-else-if="item.fieldType === 'date-range'">
                {{ formatDateRange(item.value) }}
              </template>
              <!-- 日期字段 -->
              <template v-else-if="item.fieldType === 'date'">
                {{ formatDateValue(item.value) }}
              </template>
              <!-- 其他字段 -->
              <template v-else>
                {{ formatFieldValue(item.value, item.options) }}
              </template>
            </n-descriptions-item>
          </n-descriptions>

          <n-collapse v-if="showRawData" style="margin-top: 16px;">
            <n-collapse-item title="原始数据 JSON" name="raw">
              <n-code :code="formattedRawData" language="json" show-line-numbers />
            </n-collapse-item>
          </n-collapse>
        </n-card>
      </template>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage, NImage, NIcon } from 'naive-ui'
import { getSubmissionDetail } from '@/api/submission'
import type { SubmissionDetail } from '@/types/submission'
import type { AttachmentInfo } from '@/types/attachment'
import AuthImage from '@/components/AuthImage.vue'

interface SelectOption {
  label: string
  value: string | number
}

interface DisplayField {
  key: string
  label: string
  value: unknown
  fieldType?: string
  options?: SelectOption[]
  attachments?: AttachmentInfo[]
}

const route = useRoute()
const router = useRouter()
const message = useMessage()

const loading = ref(false)
const submission = ref<SubmissionDetail | null>(null)
const showRawData = ref(false)

const attachmentMap = computed(() => {
  const map = new Map<number, AttachmentInfo>()
  const attachments = submission.value?.attachments ?? []
  attachments.forEach((item) => {
    map.set(item.id, item)
  })
  return map
})

const displayFields = computed<DisplayField[]>(() => {
  if (!submission.value) return []
  const snapshot = submission.value.snapshot_json || {}
  const labels = snapshot.field_labels || {}
  const types = snapshot.field_types || {}
  const options = snapshot.field_options || {}
  const raw = submission.value.data_jsonb || {}
  const attachments = submission.value.attachments || []

  console.log('[displayFields] attachments:', attachments)
  console.log('[displayFields] field_types:', types)
  console.log('[displayFields] raw data:', raw)

  return Object.entries(raw).map(([key, value]) => {
    const fieldType = types[key]
    const fieldOptions = options[key]
    const attachmentValue = resolveAttachmentValue(value, fieldType)

    console.log(`[displayFields] key: ${key}, fieldType: ${fieldType}, value:`, value, 'attachments:', attachmentValue)

    return {
      key,
      label: labels[key] || key,
      value,
      fieldType,
      options: fieldOptions,
      attachments: attachmentValue || undefined,
    }
  })
})

const formattedRawData = computed(() => {
  if (!submission.value) return ''
  return JSON.stringify(submission.value.data_jsonb || {}, null, 2)
})

const loadDetail = async () => {
  const id = Number(route.params.id)
  if (!id) {
    message.error('无效的提交 ID')
    router.back()
    return
  }

  loading.value = true
  try {
    const res = await getSubmissionDetail(id)
    console.log('[loadDetail] API response:', res)
    if (res.code === 200 && res.data) {
      submission.value = res.data
      console.log('[loadDetail] submission data:', {
        id: res.data.id,
        attachments: res.data.attachments,
        data_jsonb: res.data.data_jsonb,
        snapshot_json: res.data.snapshot_json
      })
    } else {
      submission.value = null
    }
  } catch (error) {
    console.error('Failed to load submission detail:', error)
    message.error('加载详情失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const resolveAttachmentValue = (value: unknown, fieldType?: string): AttachmentInfo[] | null => {
  if (!fieldType || !['upload', 'image'].includes(fieldType)) {
    return null
  }
  
  if (!Array.isArray(value)) {
    return null
  }

  const files = value
    .map((id) => (typeof id === 'number' ? attachmentMap.value.get(id) : null))
    .filter((item): item is AttachmentInfo => Boolean(item))
  
  return files.length ? files : null
}

const isImage = (contentType?: string): boolean => {
  if (!contentType) return false
  return contentType.startsWith('image/')
}

const downloadFile = (file: AttachmentInfo) => {
  if (file.download_url) {
    window.open(file.download_url, '_blank')
  } else {
    message.error('下载链接不可用')
  }
}

const formatFieldValue = (value: unknown, options?: SelectOption[]): string => {
  if (value == null) return '-'

  if (options && options.length > 0) {
    if (Array.isArray(value)) {
      const labels = value.map(v => {
        const option = options.find(opt => opt.value === v)
        return option?.label || String(v)
      })
      return labels.join('、')
    } else {
      const option = options.find(opt => opt.value === value)
      return option?.label || String(value)
    }
  }

  if (Array.isArray(value)) {
    return value.map((item) => String(item)).join('、')
  }

  if (typeof value === 'object') {
    return JSON.stringify(value)
  }

  return String(value)
}

const formatDateRange = (value: unknown): string => {
  if (!value) return '-'

  if (Array.isArray(value) && value.length === 2) {
    const [start, end] = value
    const startDate = formatDateOnly(start)
    const endDate = formatDateOnly(end)
    return `${startDate} - ${endDate}`
  }

  if (typeof value === 'object' && value !== null) {
    const obj = value as Record<string, unknown>
    if ('start' in obj && 'end' in obj) {
      const startDate = formatDateOnly(obj.start)
      const endDate = formatDateOnly(obj.end)
      return `${startDate} - ${endDate}`
    }
  }

  return String(value)
}

const formatDateOnly = (value: unknown): string => {
  if (!value) return '-'

  let date: Date
  if (typeof value === 'number') {
    date = new Date(value)
  } else if (typeof value === 'string') {
    date = new Date(value)
  } else {
    return String(value)
  }

  if (isNaN(date.getTime())) {
    return String(value)
  }

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const formatDateValue = (value: unknown): string => {
  if (!value) return '-'

  if (typeof value === 'number') {
    const date = new Date(value)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (typeof value === 'string') {
    const date = new Date(value)
    if (!isNaN(date.getTime())) {
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    }
  }

  return String(value)
}

const formatDate = (time?: string | null) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const formatFileSize = (bytes?: number) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }
  return `${size.toFixed(size >= 10 || size === Math.floor(size) ? 0 : 1)} ${units[unitIndex]}`
}

const toggleRawData = () => {
  showRawData.value = !showRawData.value
}

const goBack = () => {
  router.back()
}

const goHome = () => {
  router.push('/')
}

onMounted(loadDetail)
</script>

<style scoped>
.submission-detail-page {
  padding: 20px;
}

.mt-2 {
  margin-top: 16px;
}

.data-card {
  margin-top: 16px;
}

.data-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.data-header h3 {
  margin: 0;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-size {
  color: #999;
  font-size: 12px;
}

.image-preview-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.image-actions {
  display: flex;
  gap: 8px;
}

.empty-value {
  color: #999;
  font-style: italic;
}
</style>
