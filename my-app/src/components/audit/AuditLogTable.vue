<template>
  <div class="audit-log-table">
    <!-- 筛选栏 -->
    <AuditLogFilter
      v-model="filters"
      :is-admin="isAdmin"
      @search="handleSearch"
    />

    <!-- 操作栏 -->
    <n-space justify="space-between" align="center" style="margin: 16px 0">
      <n-text depth="3">共 {{ pagination.total }} 条记录</n-text>
      <n-button size="small" @click="handleExport" :loading="exporting">
        <template #icon>
          <Icon icon="carbon:download" />
        </template>
        导出CSV
      </n-button>
    </n-space>

    <!-- 表格 -->
    <n-data-table
      :columns="columns"
      :data="logs"
      :loading="loading"
      :pagination="pagination"
      @update:page="handlePageChange"
      :row-key="(row: AuditLog) => row.id"
    />

    <!-- 详情抽屉 -->
    <n-drawer v-model:show="detailVisible" :width="520">
      <n-drawer-content :title="detailTitle" closable>
        <AuditLogDetail
          v-if="selectedLog"
          :log="selectedLog"
          :changes="selectedChanges"
        />
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import { useMessage } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { Icon } from '@iconify/vue'
import AuditLogFilter from './AuditLogFilter.vue'
import AuditLogDetail from './AuditLogDetail.vue'
import {
  listAuditLogs,
  exportAuditLogs,
  type AuditLog,
  type AuditLogQuery,
  type ChangeComparisonItem,
} from '@/api/audit'
import { getAuditLogDetail } from '@/api/audit'

interface Props {
  resourceType?: string
  resourceId?: number
  onlyMine?: boolean
  isAdmin?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  onlyMine: false,
  isAdmin: false,
})

const message = useMessage()

// 状态
const loading = ref(false)
const exporting = ref(false)
const logs = ref<AuditLog[]>([])
const filters = ref<AuditLogQuery>({
  page: 1,
  page_size: 20,
  resource_type: props.resourceType,
  resource_id: props.resourceId,
  only_mine: props.onlyMine,
})

const pagination = computed(() => ({
  page: filters.value.page || 1,
  pageSize: filters.value.page_size || 20,
  total: total.value,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
}))

const total = ref(0)

// 详情
const detailVisible = ref(false)
const selectedLog = ref<AuditLog | null>(null)
const selectedChanges = ref<ChangeComparisonItem[]>([])

const detailTitle = computed(() =>
  selectedLog.value ? `审计详情 #${selectedLog.value.id}` : '审计详情'
)

// 表格列定义
const columns: DataTableColumns<AuditLog> = [
  {
    title: '时间',
    key: 'created_at',
    width: 160,
    render(row) {
      return new Date(row.created_at).toLocaleString()
    },
  },
  {
    title: '操作人',
    key: 'actor_name',
    width: 120,
    render(row) {
      return row.actor_name || `用户#${row.actor_user_id}` || '系统'
    },
  },
  {
    title: '动作',
    key: 'action',
    width: 120,
  },
  {
    title: '资源类型',
    key: 'resource_type',
    width: 100,
  },
  {
    title: '资源ID',
    key: 'resource_id',
    width: 80,
    render(row) {
      return row.resource_id || '-'
    },
  },
  {
    title: 'IP地址',
    key: 'ip',
    width: 130,
    render(row) {
      return row.ip || '-'
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render(row) {
      return h(
        'n-button',
        {
          size: 'small',
          text: true,
          type: 'primary',
          onClick: () => handleViewDetail(row),
        },
        { default: () => '查看详情' }
      )
    },
  },
]

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const { data } = await listAuditLogs(filters.value)
    logs.value = data?.items || []
    total.value = data?.total || 0
  } catch (error) {
    message.error('加载审计日志失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 查询
const handleSearch = () => {
  filters.value.page = 1
  loadData()
}

// 分页
const handlePageChange = (page: number) => {
  filters.value.page = page
  loadData()
}

// 查看详情
const handleViewDetail = async (row: AuditLog) => {
  try {
    const { data } = await getAuditLogDetail(row.id)
    selectedLog.value = data.log
    selectedChanges.value = data.changes
    detailVisible.value = true
  } catch (error) {
    message.error('加载详情失败')
  }
}

// 导出
const handleExport = async () => {
  exporting.value = true
  try {
    const blob = await exportAuditLogs({
      resource_type: props.resourceType,
      resource_id: props.resourceId,
      date_from: filters.value.date_from,
      date_to: filters.value.date_to,
      action: filters.value.action,
    })

    // 下载文件
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `audit_logs_${new Date().getTime()}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    message.success('导出成功')
  } catch (error) {
    message.error('导出失败')
  } finally {
    exporting.value = false
  }
}

// 初始化
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.audit-log-table {
  padding: 16px 0;
}
</style>
