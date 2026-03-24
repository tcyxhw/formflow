<template>
  <div class="batch-import-container">
    <n-page-header title="批量用户导入" subtitle="通过Excel文件批量注册学生或老师">
      <template #extra>
        <n-space>
          <n-button @click="downloadTemplate" :loading="downloading">
            <template #icon>
              <n-icon><download-outline /></n-icon>
            </template>
            下载模板
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <n-card title="上传Excel文件" style="margin-top: 16px;">
      <n-upload
        v-model:file-list="fileList"
        :max="1"
        accept=".xlsx,.xls"
        :before-upload="beforeUpload"
        @change="handleFileChange"
      >
        <n-upload-dragger>
          <div style="margin-bottom: 12px">
            <n-icon size="48" :depth="3">
              <archive-outline />
            </n-icon>
          </div>
          <n-text style="font-size: 16px">
            点击或者拖动文件到该区域来上传
          </n-text>
          <n-p depth="3" style="margin: 8px 0 0 0">
            请上传 .xlsx 或 .xls 格式的Excel文件
          </n-p>
        </n-upload-dragger>
      </n-upload>

      <n-divider />

      <n-form label-placement="left" label-width="120">
        <n-form-item label="默认密码">
          <n-input
            v-model:value="defaultPassword"
            placeholder="请输入默认密码（至少6位）"
            type="password"
            show-password-on="click"
          />
        </n-form-item>
      </n-form>

      <n-space justify="end">
        <n-button
          type="primary"
          :loading="importing"
          :disabled="!selectedFile"
          @click="startImport"
        >
          开始导入
        </n-button>
      </n-space>
    </n-card>

    <n-card v-if="importResult" title="导入结果" style="margin-top: 16px;">
      <n-descriptions bordered :column="3">
        <n-descriptions-item label="总行数">
          {{ importResult.total_rows }}
        </n-descriptions-item>
        <n-descriptions-item label="成功数量">
          <n-tag type="success">{{ importResult.success_count }}</n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="失败数量">
          <n-tag type="error">{{ importResult.failed_count }}</n-tag>
        </n-descriptions-item>
      </n-descriptions>

      <n-divider />

      <n-data-table
        :columns="resultColumns"
        :data="importResult.results"
        :pagination="{ pageSize: 10 }"
        :row-class-name="getRowClassName"
      />
    </n-card>

    <n-card title="导入历史" style="margin-top: 16px;">
      <n-data-table
        :columns="historyColumns"
        :data="historyData"
        :loading="historyLoading"
        :pagination="historyPagination"
        @update:page="handleHistoryPageChange"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import {
  NPageHeader,
  NCard,
  NUpload,
  NUploadDragger,
  NButton,
  NIcon,
  NSpace,
  NText,
  NP,
  NDivider,
  NForm,
  NFormItem,
  NInput,
  NDescriptions,
  NDescriptionsItem,
  NTag,
  NDataTable,
  useMessage
} from 'naive-ui'
import { DownloadOutline, ArchiveOutline } from '@vicons/ionicons5'
import { downloadImportTemplate, batchImportUsers, getImportHistory } from '@/api/admin'
import type { UploadFileInfo } from 'naive-ui'

const message = useMessage()

const fileList = ref<UploadFileInfo[]>([])
const selectedFile = ref<File | null>(null)
const defaultPassword = ref('123456')
const importing = ref(false)
const downloading = ref(false)
const importResult = ref<any>(null)
const historyData = ref<any[]>([])
const historyLoading = ref(false)
const historyPagination = ref({
  page: 1,
  pageSize: 10,
  pageCount: 0,
  prefix({ itemCount }: { itemCount: number }) {
    return `共 ${itemCount} 条`
  }
} as any)

const resultColumns = [
  { title: '行号', key: 'row_number', width: 80 },
  { title: '账号', key: 'account', width: 120 },
  { title: '姓名', key: 'name', width: 100 },
  {
    title: '状态',
    key: 'success',
    width: 80,
    render: (row: any) => {
      return h(
        NTag,
        { type: row.success ? 'success' : 'error' },
        { default: () => (row.success ? '成功' : '失败') }
      )
    }
  },
  { title: '错误信息', key: 'error_message' }
]

const historyColumns = [
  { title: '文件名', key: 'filename' },
  { title: '总行数', key: 'total_rows', width: 100 },
  {
    title: '成功',
    key: 'success_count',
    width: 80,
    render: (row: any) => h(NTag, { type: 'success' }, { default: () => row.success_count })
  },
  {
    title: '失败',
    key: 'failed_count',
    width: 80,
    render: (row: any) => h(NTag, { type: 'error' }, { default: () => row.failed_count })
  },
  {
    title: '导入时间',
    key: 'created_at',
    width: 180,
    render: (row: any) => {
      if (!row.created_at) return '-'
      return new Date(row.created_at).toLocaleString()
    }
  }
]

const beforeUpload = (data: { file: UploadFileInfo }) => {
  const file = data.file.file
  if (!file) return false

  const isExcel =
    file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
    file.type === 'application/vnd.ms-excel' ||
    file.name.endsWith('.xlsx') ||
    file.name.endsWith('.xls')

  if (!isExcel) {
    message.error('只能上传Excel文件')
    return false
  }
  return true
}

const handleFileChange = (data: { file: UploadFileInfo }) => {
  if (data.file.file) {
    selectedFile.value = data.file.file
  }
}

const downloadTemplate = async () => {
  downloading.value = true
  try {
    const blob = await downloadImportTemplate()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '批量用户导入模板.xlsx'
    link.click()
    window.URL.revokeObjectURL(url)
    message.success('模板下载成功')
  } catch (error) {
    console.error('下载模板失败:', error)
    message.error('模板下载失败')
  } finally {
    downloading.value = false
  }
}

const startImport = async () => {
  if (!selectedFile.value) {
    message.error('请先选择Excel文件')
    return
  }

  if (defaultPassword.value.length < 6) {
    message.error('默认密码至少6位')
    return
  }

  importing.value = true
  try {
    const response = await batchImportUsers(selectedFile.value, defaultPassword.value)
    importResult.value = response.data

    if (response.data.failed_count === 0) {
      message.success(`导入完成，成功 ${response.data.success_count} 条`)
    } else {
      message.warning(`导入完成，成功 ${response.data.success_count} 条，失败 ${response.data.failed_count} 条`)
    }

    loadHistory()
  } catch (error) {
    console.error('批量导入失败:', error)
    message.error('批量导入失败')
  } finally {
    importing.value = false
  }
}

const getRowClassName = (row: any) => {
  return row.success ? 'success-row' : 'error-row'
}

const loadHistory = async () => {
  historyLoading.value = true
  try {
    const res = await getImportHistory({
      page: historyPagination.value.page,
      size: historyPagination.value.pageSize
    })
    historyData.value = res.data.items
    historyPagination.value.pageCount = Math.ceil(res.data.total / historyPagination.value.pageSize)
  } catch (error) {
    console.error('加载导入历史失败:', error)
  } finally {
    historyLoading.value = false
  }
}

const handleHistoryPageChange = (page: number) => {
  historyPagination.value.page = page
  loadHistory()
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.batch-import-container {
  padding: 16px;
}

:deep(.success-row) {
  background-color: #f6ffed;
}

:deep(.error-row) {
  background-color: #fff2f0;
}
</style>
