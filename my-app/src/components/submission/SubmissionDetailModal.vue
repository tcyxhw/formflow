<template>
  <n-modal
    v-model:show="visible"
    preset="card"
    :title="`提交详情 - ${submission?.form_name || '加载中'}`"
    size="large"
    :segmented="false"
    :bordered="false"
    :closable="true"
    :close-on-esc="true"
    :mask-closable="false"
    style="width: 90%; max-width: 1200px"
    @update:show="handleClose"
  >
    <n-spin :show="loading">
      <n-alert
        v-if="!loading && !submission"
        type="warning"
        title="未找到对应的提交记录"
        class="mb-4"
      />

      <template v-else-if="submission">
        <!-- 基本信息 -->
        <n-card title="基本信息" :bordered="false" class="mb-4">
          <n-descriptions label-placement="left" :column="2" bordered size="small">
            <n-descriptions-item label="提交 ID">
              {{ submission.id }}
            </n-descriptions-item>
            <n-descriptions-item label="表单名称">
              {{ submission.form_name }}
            </n-descriptions-item>
            <n-descriptions-item label="提交人">
              {{ submission.submitter_name }}
            </n-descriptions-item>
            <n-descriptions-item label="状态">
              <n-space>
                <n-tag :type="statusTagType(submission.status)">
                  {{ statusLabel(submission.status) }}
                </n-tag>
                <n-tag :type="processStateTag(submission.process_state)">
                  {{ formatProcessState(submission.process_state) }}
                </n-tag>
              </n-space>
            </n-descriptions-item>
            <n-descriptions-item label="提交时间">
              {{ formatDate(submission.created_at) }}
            </n-descriptions-item>
            <n-descriptions-item label="耗时">
              {{ formatDuration(submission.duration) }}
            </n-descriptions-item>
          </n-descriptions>
        </n-card>

        <!-- 表单数据 -->
        <n-card title="表单数据" :bordered="false" class="mb-4">
          <template #header-extra>
            <n-button text type="primary" @click="toggleRawData">
              {{ showRawData ? '隐藏原始 JSON' : '查看原始 JSON' }}
            </n-button>
          </template>

          <n-descriptions label-placement="left" :column="1" bordered size="small">
            <n-descriptions-item
              v-for="item in displayFields"
              :key="item.key"
              :label="item.label"
            >
              <template v-if="item.attachments">
                <n-space vertical :size="4">
                  <n-a
                    v-for="file in item.attachments"
                    :key="file.id"
                    :href="file.download_url"
                    target="_blank"
                  >
                    {{ file.file_name }}
                  </n-a>
                </n-space>
              </template>
              <template v-else>
                {{ formatFieldValue(item.value) }}
              </template>
            </n-descriptions-item>
          </n-descriptions>

          <n-collapse v-if="showRawData" style="margin-top: 16px">
            <n-collapse-item title="原始数据 JSON" name="raw">
              <n-code :code="formattedRawData" language="json" show-line-numbers />
            </n-collapse-item>
          </n-collapse>
        </n-card>

        <!-- 附件列表 -->
        <n-card
          v-if="submission.attachments?.length"
          title="附件列表"
          :bordered="false"
          class="mb-4"
        >
          <n-data-table
            :columns="attachmentColumns"
            :data="submission.attachments"
            :bordered="true"
            size="small"
            :single-line="false"
          />
        </n-card>
      </template>
    </n-spin>

    <template #footer>
      <n-space justify="end">
        <n-button @click="handleClose">关闭</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch, h } from 'vue'
import { useMessage, NA, type DataTableColumns } from 'naive-ui'
import { getSubmissionDetail } from '@/api/submission'
import type { SubmissionDetail } from '@/types/submission'
import type { AttachmentInfo } from '@/types/attachment'
import { formatProcessState, processStateTag } from '@/utils/sla'

type TagType = 'default' | 'success' | 'error' | 'info' | 'warning'

interface Props {
  show: boolean
  submissionId?: number
}

interface Emits {
  (e: 'update:show', value: boolean): void
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
  submissionId: undefined,
})

const emit = defineEmits<Emits>()

const message = useMessage()
const loading = ref(false)
const submission = ref<SubmissionDetail | null>(null)
const showRawData = ref(false)

const visible = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value),
})

const attachmentMap = computed(() => {
  const map = new Map<number, AttachmentInfo>()
  const attachments = submission.value?.attachments ?? []
  attachments.forEach((item) => {
    map.set(item.id, item)
  })
  return map
})

interface DisplayField {
  key: string
  label: string
  value: unknown
  attachments?: AttachmentInfo[]
}

const displayFields = computed<DisplayField[]>(() => {
  if (!submission.value) return []
  const labels = submission.value.snapshot_json?.field_labels || {}
  const raw = submission.value.data_jsonb || {}
  return Object.entries(raw).map(([key, value]) => {
    const attachmentValue = resolveAttachmentValue(value)
    return {
      key,
      label: labels[key] || key,
      value,
      attachments: attachmentValue || undefined,
    }
  })
})

const formattedRawData = computed(() => {
  if (!submission.value) return ''
  return JSON.stringify(submission.value.data_jsonb || {}, null, 2)
})

const attachmentColumns: DataTableColumns<AttachmentInfo> = [
  {
    title: '文件名',
    key: 'file_name',
    minWidth: 160,
    ellipsis: {
      tooltip: true,
    },
    render(row) {
      return h(
        NA,
        {
          href: row.download_url,
          target: '_blank',
        },
        { default: () => row.file_name }
      )
    },
  },
  {
    title: '大小',
    key: 'size',
    width: 120,
    render(row) {
      return formatFileSize(row.size)
    },
  },
  {
    title: '类型',
    key: 'content_type',
    minWidth: 140,
  },
  {
    title: '上传时间',
    key: 'created_at',
    width: 180,
    render(row) {
      return formatDate(row.created_at)
    },
  },
]

const resolveAttachmentValue = (value: unknown): AttachmentInfo[] | null => {
  if (!Array.isArray(value)) return null
  const files = value
    .map((id) => (typeof id === 'number' ? attachmentMap.value.get(id) : null))
    .filter((item): item is AttachmentInfo => Boolean(item))
  return files.length ? files : null
}

const formatFieldValue = (value: unknown): string => {
  if (Array.isArray(value)) {
    return value.map((item) => String(item)).join('、')
  }
  if (value && typeof value === 'object') {
    return JSON.stringify(value)
  }
  return value != null ? String(value) : '-'
}

const statusLabel = (status: string) => {
  switch (status) {
    case 'approved':
      return '已通过'
    case 'rejected':
      return '已拒绝'
    case 'draft':
      return '草稿'
    default:
      return '已提交'
  }
}

const statusTagType = (status: string): 'success' | 'error' | 'info' | 'default' => {
  switch (status) {
    case 'approved':
      return 'success'
    case 'rejected':
      return 'error'
    case 'draft':
      return 'info'
    default:
      return 'default'
  }
}

const formatDuration = (seconds?: number) => {
  if (!seconds || seconds <= 0) return '-'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins <= 0) return `${secs} 秒`
  return `${mins} 分 ${secs} 秒`
}

const formatDate = (time?: string | null) => {
  if (!time) return '-'
  return new Date(time).toLocaleString()
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

const loadDetail = async () => {
  if (!props.submissionId) return

  loading.value = true
  try {
    const res = await getSubmissionDetail(props.submissionId)
    if (res.code === 200 && res.data) {
      submission.value = res.data
    } else {
      submission.value = null
      message.error('加载详情失败')
    }
  } catch (error) {
    console.error('Failed to load submission detail:', error)
    message.error('加载详情失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  visible.value = false
  submission.value = null
  showRawData.value = false
}

watch(
  () => props.show,
  (newVal) => {
    if (newVal && props.submissionId) {
      loadDetail()
    }
  }
)
</script>

<style scoped>
.mb-4 {
  margin-bottom: 16px;
}
</style>
