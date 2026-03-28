<!-- src/views/submissions/SubmissionListView.vue -->
<template>
  <div class="submission-list-page">
    <n-spin :show="loading">
      <n-page-header @back="goBack">
        <template #title>
          提交管理
        </template>
        <template #subtitle>
          提交记录
        </template>
        <template #extra>
          <n-space>
            <n-button @click="goHome">
              <template #icon>
                <n-icon :component="HomeOutline" />
              </template>
              返回主页
            </n-button>
          </n-space>
        </template>
      </n-page-header>

      <n-card class="filter-card" :bordered="false">
        <n-form inline :model="filters" label-placement="left">
          <n-form-item label="表单 ID">
            <n-input-number
              v-model:value="filters.form_id"
              :min="1"
              placeholder="请输入表单 ID"
              clearable
              style="width: 180px"
            />
          </n-form-item>
          <n-form-item label="状态">
            <n-select
              v-model:value="filters.status"
              :options="statusOptions"
              placeholder="全部"
              clearable
              style="width: 140px"
            />
          </n-form-item>
          <n-form-item label="关键词">
            <n-input
              v-model:value="filters.keyword"
              placeholder="搜索提交者/内容"
              clearable
              @keyup.enter="fetchList"
              style="width: 200px"
            />
          </n-form-item>
          <n-form-item>
            <n-space>
              <n-button type="primary" @click="fetchList">查询</n-button>
              <n-button @click="resetFilters">重置</n-button>
            </n-space>
          </n-form-item>
        </n-form>
      </n-card>

      <n-card :bordered="false">
        <template #header>
          <div class="table-header">
            <h3>提交列表</h3>
            <n-space>
              <n-button text @click="fetchList">
                <template #icon>
                  <n-icon :component="RefreshOutline" />
                </template>
                刷新
              </n-button>
            </n-space>
          </div>
        </template>

        <div class="table-actions" v-if="checkedRowKeys.length > 0">
          <n-space align="center">
            <span class="selection-info">已选中 {{ checkedRowKeys.length }} 条记录</span>
            <n-button type="primary" size="small" :loading="exporting" @click="handleExportSelected">
              <template #icon>
                <n-icon :component="DownloadOutline" />
              </template>
              导出选中
            </n-button>
            <n-button size="small" @click="clearSelection">取消选中</n-button>
          </n-space>
        </div>

        <n-data-table
          v-model:checked-row-keys="checkedRowKeys"
          :columns="columns"
          :data="submissions"
          :row-key="(row: SubmissionListItem) => row.id"
          :bordered="false"
          :single-line="false"
          striped
        />

        <div class="table-footer">
          <div class="export-section">
            <n-button type="primary" :loading="exporting" @click="handleExportAll">
              <template #icon>
                <n-icon :component="DownloadOutline" />
              </template>
              导出全部
            </n-button>
          </div>
          <n-pagination
            v-model:page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :page-count="Math.ceil(pagination.total / pagination.pageSize)"
            :page-sizes="[10, 20, 50]"
            show-size-picker
            show-quick-jumper
            :item-count="pagination.total"
            @update:page="handlePageChange"
            @update:page-size="handleSizeChange"
          >
            <template #prefix="{ itemCount }">
              共 {{ itemCount }} 条
            </template>
          </n-pagination>
        </div>
      </n-card>

      <n-modal
        v-model:show="exportDialog.visible"
        preset="dialog"
        title="导出任务创建成功"
        :style="{ width: '420px' }"
        @after-leave="resetExportDialog"
      >
        <p v-if="exportDialog.mode === 'sync'">
          导出生成完成，点击下方按钮下载。
        </p>
        <p v-else>
          已创建导出任务（ID: {{ exportDialog.taskId }}）。您可以稍后在导出记录中查看进度。
        </p>
        <template #action>
          <n-space>
            <n-button @click="exportDialog.visible = false">关闭</n-button>
            <n-button
              v-if="exportDialog.mode === 'sync'"
              type="primary"
              @click="downloadExport"
            >
              下载文件
            </n-button>
          </n-space>
        </template>
      </n-modal>

      <SubmissionDetailModal
        :show="detailModalVisible"
        :submission-id="selectedSubmissionId"
        @update:show="detailModalVisible = $event"
      />
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, useDialog, NButton, NTag, NSpace, NIcon, type DataTableColumns } from 'naive-ui'
import { RefreshOutline, HomeOutline, DownloadOutline } from '@vicons/ionicons5'
import {
  getSubmissionList,
  deleteSubmission,
  exportSubmissions,
  getExportTask,
} from '@/api/submission'
import type {
  SubmissionListItem,
  SubmissionExportRequest,
  SubmissionExportAsyncResponse,
  SubmissionExportSyncResponse,
} from '@/types/submission'
import SubmissionDetailModal from '@/components/submission/SubmissionDetailModal.vue'

const router = useRouter()
const message = useMessage()
const dialog = useDialog()

const detailModalVisible = ref(false)
const selectedSubmissionId = ref<number | undefined>()

const loading = ref(false)
const exporting = ref(false)
const submissions = ref<SubmissionListItem[]>([])
const checkedRowKeys = ref<number[]>([])

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const filters = reactive({
  form_id: undefined as number | undefined,
  status: undefined as string | undefined,
  keyword: '',
})

const exportDialog = reactive({
  visible: false,
  mode: 'sync' as 'sync' | 'async',
  downloadUrl: '',
  taskId: '',
})

const statusOptions = [
  { label: '全部', value: '' },
  { label: '已提交', value: 'submitted' },
  { label: '草稿', value: 'draft' },
  { label: '已通过', value: 'approved' },
  { label: '已拒绝', value: 'rejected' },
]

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

const formatDate = (value?: string) => {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

const viewDetail = (id: number) => {
  selectedSubmissionId.value = id
  detailModalVisible.value = true
}

const confirmDelete = (id: number) => {
  dialog.warning({
    title: '提示',
    content: '确定要删除该提交记录吗？操作不可撤销。',
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      loading.value = true
      try {
        const res = await deleteSubmission(id)
        if (res.code === 200) {
          message.success('删除成功')
          fetchList()
        }
      } catch (error) {
        console.error('Failed to delete submission:', error)
        message.error('删除失败，请稍后重试')
      } finally {
        loading.value = false
      }
    }
  })
}

const clearSelection = () => {
  checkedRowKeys.value = []
}

// 表格列定义
const columns: DataTableColumns<SubmissionListItem> = [
  {
    title: 'ID',
    key: 'id',
    width: 80,
    sorter: 'default'
  },
  {
    title: '表单',
    key: 'form_name',
    minWidth: 160,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '提交人',
    key: 'submitter_name',
    minWidth: 140
  },
  {
    title: '状态',
    key: 'status',
    width: 120,
    render(row) {
      return h(
        NTag,
        { type: statusTagType(row.status) },
        { default: () => statusLabel(row.status) }
      )
    }
  },
  {
    title: '提交时间',
    key: 'created_at',
    width: 180,
    render(row) {
      return formatDate(row.created_at)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 140,
    render(row) {
      return h(
        NSpace,
        {},
        {
          default: () => [
            h(
              NButton,
              {
                text: true,
                type: 'primary',
                onClick: () => viewDetail(row.id)
              },
              { default: () => '详情' }
            ),
            h(
              NButton,
              {
                text: true,
                type: 'error',
                onClick: () => confirmDelete(row.id)
              },
              { default: () => '删除' }
            )
          ]
        }
      )
    }
  }
]

const fetchList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
      form_id: filters.form_id,
    }
    const res = await getSubmissionList(params)
    if (res.code === 200 && res.data) {
      submissions.value = res.data.items
      pagination.total = res.data.total
      pagination.page = res.data.page
      pagination.pageSize = res.data.page_size
    }
  } catch (error) {
    console.error('Failed to fetch submissions:', error)
    message.error('加载提交列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  pagination.page = page
  fetchList()
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  fetchList()
}

const resetFilters = () => {
  filters.form_id = undefined
  filters.status = undefined
  filters.keyword = ''
  pagination.page = 1
  fetchList()
}

// 处理导出响应
const handleExportResponse = async (res: { code: number; data?: SubmissionExportSyncResponse | SubmissionExportAsyncResponse }) => {
  if (res.code === 200 && res.data) {
    if ((res.data as SubmissionExportSyncResponse).download_url) {
      const syncData = res.data as SubmissionExportSyncResponse
      exportDialog.mode = 'sync'
      exportDialog.downloadUrl = syncData.download_url
      exportDialog.visible = true
    } else {
      const asyncData = res.data as SubmissionExportAsyncResponse
      exportDialog.mode = 'async'
      exportDialog.taskId = asyncData.task_id
      exportDialog.visible = true
      pollExportTask(asyncData.task_id)
    }
  }
}

// 导出选中的记录
const handleExportSelected = async () => {
  if (checkedRowKeys.value.length === 0) {
    message.warning('请先选择要导出的记录')
    return
  }

  exporting.value = true
  try {
    // 获取选中记录的 form_id
    const selectedSubmissions = submissions.value.filter(s => checkedRowKeys.value.includes(s.id))
    const formIds = [...new Set(selectedSubmissions.map(s => s.form_id))]

    if (formIds.length === 1) {
      // 单表单导出
      const payload: SubmissionExportRequest = {
        form_id: formIds[0],
        format: 'excel',
        submission_ids: checkedRowKeys.value,
      }
      const res = await exportSubmissions(payload)
      await handleExportResponse(res)
    } else {
      // 多表单导出（每个表单一个 Sheet）
      const payload: SubmissionExportRequest = {
        form_id: undefined,
        format: 'excel',
        submission_ids: checkedRowKeys.value,
      }
      const res = await exportSubmissions(payload)
      await handleExportResponse(res)
    }
  } catch (error) {
    console.error('Failed to export selected submissions:', error)
    message.error('导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

// 导出全部（按当前筛选条件）
const handleExportAll = async () => {
  if (!filters.form_id) {
    message.warning('请先指定表单 ID 再导出数据')
    return
  }

  exporting.value = true
  try {
    const payload: SubmissionExportRequest = {
      form_id: filters.form_id,
      format: 'excel',
      submission_ids: submissions.value.map((item) => item.id),
    }
    const res = await exportSubmissions(payload)
    await handleExportResponse(res)
  } catch (error) {
    console.error('Failed to export submissions:', error)
    message.error('导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

const pollExportTask = async (taskId: string) => {
  try {
    const res = await getExportTask(taskId)
    if (res.code === 200 && res.data && res.data.status === 'completed' && res.data.download_url) {
      exportDialog.mode = 'sync'
      exportDialog.downloadUrl = res.data.download_url
    }
  } catch (error) {
    console.error('Failed to poll export task:', error)
  }
}

const downloadExport = () => {
  if (!exportDialog.downloadUrl) return
  window.open(exportDialog.downloadUrl, '_blank')
}

const resetExportDialog = () => {
  exportDialog.downloadUrl = ''
  exportDialog.taskId = ''
  exportDialog.mode = 'sync'
}

const goBack = () => {
  router.back()
}

const goHome = () => {
  router.push('/')
}

onMounted(fetchList)
</script>

<style scoped>
.submission-list-page {
  padding: 20px;
}

.filter-card {
  margin: 16px 0;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-header h3 {
  margin: 0;
}

.table-actions {
  margin-bottom: 12px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.selection-info {
  color: #666;
  font-size: 14px;
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
}

.export-section {
  display: flex;
  align-items: center;
}
</style>
