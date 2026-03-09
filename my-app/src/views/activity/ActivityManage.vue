<template>
  <div class="activity-manage-shell">
    <!-- Header -->
    <section class="manage-header section">
      <div class="section-shell">
        <div class="header-content">
          <n-button quaternary @click="router.back()">
            <template #icon><Icon icon="carbon:arrow-left" /></template>
            返回
          </n-button>
          <div class="header-title">
            <h1>{{ activity?.name }}</h1>
            <n-tag :type="getStatusType(activity?.status)" size="small">
              {{ getStatusLabel(activity?.status) }}
            </n-tag>
          </div>
          <div class="header-actions">
            <n-button type="primary" @click="showCheckinModal = true">
              <template #icon><Icon icon="carbon:qr-code" /></template>
              签到码
            </n-button>
            <n-button @click="router.push(`/activity/${activityId}/awards`)">
              <template #icon><Icon icon="carbon:trophy" /></template>
              评分评奖
            </n-button>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Cards -->
    <section class="section">
      <div class="section-shell">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon"><Icon icon="carbon:user" /></div>
            <div class="stat-info">
              <span class="stat-value">{{ stats.total }}</span>
              <span class="stat-label">总报名</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon approved"><Icon icon="carbon:checkmark" /></div>
            <div class="stat-info">
              <span class="stat-value">{{ stats.approved }}</span>
              <span class="stat-label">已通过</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon pending"><Icon icon="carbon:time" /></div>
            <div class="stat-info">
              <span class="stat-value">{{ stats.pending }}</span>
              <span class="stat-label">待审核</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon checked"><Icon icon="carbon:location" /></div>
            <div class="stat-info">
              <span class="stat-value">{{ stats.checkedIn }}</span>
              <span class="stat-label">已签到</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Registration Management -->
    <section class="section section--alt">
      <div class="section-shell">
        <div class="section-header">
          <h2>报名管理</h2>
          <n-input
            v-model:value="searchQuery"
            placeholder="搜索学生姓名..."
            clearable
            style="width: 240px"
          >
            <template #prefix><Icon icon="carbon:search" /></template>
          </n-input>
        </div>

        <n-data-table
          :columns="columns"
          :data="filteredRegistrations"
          :loading="loading"
          :pagination="pagination"
          @update:page="handlePageChange"
        />
      </div>
    </section>

    <!-- Check-in Modal -->
    <n-modal v-model:show="showCheckinModal" title="签到管理" style="width: 600px">
      <n-card>
        <div class="checkin-section">
          <h3>生成签到码</h3>
          <n-space>
            <n-select v-model:value="checkinForm.type" :options="codeTypeOptions" style="width: 150px" />
            <n-input-number v-model:value="checkinForm.validHours" :min="1" :max="72" style="width: 120px">
              <template #suffix>小时</template>
            </n-input-number>
            <n-button type="primary" @click="generateCheckinCode" :loading="generatingCode">
              生成
            </n-button>
          </n-space>
        </div>

        <div class="checkin-list" v-if="checkinCodes.length > 0">
          <h3>签到码列表</h3>
          <n-list>
            <n-list-item v-for="code in checkinCodes" :key="code.id">
              <div class="code-item">
                <div class="code-info">
                  <span class="code-value">{{ code.code }}</span>
                  <n-tag size="small" :type="code.status === 'active' ? 'success' : 'default'">
                    {{ code.status === 'active' ? '有效' : '已过期' }}
                  </n-tag>
                </div>
                <div class="code-meta">
                  <span>已使用: {{ code.used_count }} / {{ code.max_use || '∞' }}</span>
                  <span>过期: {{ formatDate(code.valid_to) }}</span>
                </div>
              </div>
            </n-list-item>
          </n-list>
        </div>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage, NButton, NSpace, NTag } from 'naive-ui'
import { Icon } from '@iconify/vue'
import { getActivityDetail, generateCheckinCode as apiGenerateCheckinCode } from '@/api/activity'
import type { Activity, ActivityRegistration } from '@/api/activity'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const activityId = Number(route.params.id)
const loading = ref(false)
const activity = ref<Activity | null>(null)
const registrations = ref<ActivityRegistration[]>([])
const searchQuery = ref('')
const showCheckinModal = ref(false)
const generatingCode = ref(false)
const checkinCodes = ref<any[]>([])

const checkinForm = reactive({
  type: 'qrcode',
  validHours: 24,
})

const codeTypeOptions = [
  { label: '二维码', value: 'qrcode' },
  { label: '数字码', value: 'number' },
]

const stats = computed(() => {
  const total = registrations.value.length
  const approved = registrations.value.filter(r => r.status === 'approved').length
  const pending = registrations.value.filter(r => r.status === 'pending').length
  const checkedIn = registrations.value.filter(r => r.checked_in_at).length
  return { total, approved, pending, checkedIn }
})

const filteredRegistrations = computed(() => {
  if (!searchQuery.value) return registrations.value
  return registrations.value.filter(r => 
    r.user_name?.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
})

const columns = [
  { title: '学生姓名', key: 'user_name', width: 120 },
  { title: '学号', key: 'student_no', width: 150 },
  { title: '报名时间', key: 'registered_at', width: 180 },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row: any) {
      const statusMap: Record<string, string> = {
        pending: 'warning',
        approved: 'success',
        rejected: 'error',
        cancelled: 'default',
      }
      const labelMap: Record<string, string> = {
        pending: '待审核',
        approved: '已通过',
        rejected: '已拒绝',
        cancelled: '已取消',
      }
      return h(NTag, { type: statusMap[row.status] as any, size: 'small' }, { default: () => labelMap[row.status] })
    },
  },
  {
    title: '签到',
    key: 'checked_in',
    width: 100,
    render(row: any) {
      return row.checked_in_at 
        ? h(NTag, { type: 'success', size: 'small' }, { default: () => '已签到' })
        : h(NTag, { size: 'small' }, { default: () => '未签到' })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render(row: any) {
      return h(NSpace, {}, {
        default: () => [
          row.status === 'pending' && h(NButton, { size: 'small', type: 'primary', onClick: () => handleApprove(row) }, { default: () => '通过' }),
          row.status === 'pending' && h(NButton, { size: 'small', onClick: () => handleReject(row) }, { default: () => '拒绝' }),
          !row.checked_in_at && h(NButton, { size: 'small', onClick: () => handleManualCheckin(row) }, { default: () => '手动签到' }),
        ],
      })
    },
  },
]

const loadActivity = async () => {
  loading.value = true
  try {
    const { data } = await getActivityDetail(activityId)
    activity.value = data?.activity
    // TODO: 加载报名列表
    registrations.value = []
  } catch (error) {
    message.error('加载失败')
  } finally {
    loading.value = false
  }
}

const generateCheckinCode = async () => {
  generatingCode.value = true
  try {
    const { data } = await apiGenerateCheckinCode(activityId, checkinForm.type, checkinForm.validHours)
    message.success('签到码生成成功')
    checkinCodes.value.unshift(data)
  } catch (error) {
    message.error('生成失败')
  } finally {
    generatingCode.value = false
  }
}

const handleApprove = (row: any) => {
  message.success(`已通过: ${row.user_name}`)
}

const handleReject = (row: any) => {
  message.warning(`已拒绝: ${row.user_name}`)
}

const handleManualCheckin = (row: any) => {
  message.success(`手动签到: ${row.user_name}`)
}

const handlePageChange = (page: number) => {
  pagination.page = page
}

const getStatusType = (status?: string) => {
  const map: Record<string, string> = { draft: 'default', published: 'success', ended: 'info', cancelled: 'error' }
  return map[status || ''] || 'default'
}

const getStatusLabel = (status?: string) => {
  const map: Record<string, string> = { draft: '草稿', published: '已发布', ended: '已结束', cancelled: '已取消' }
  return map[status || ''] || status
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadActivity()
})
</script>

<style scoped>
.activity-manage-shell {
  min-height: 100vh;
  background: var(--bg);
}

.manage-header {
  background: linear-gradient(180deg, #fbfbfc 0%, #f4f5f9 100%);
  padding: 40px 0;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-title {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title h1 {
  margin: 0;
  font-size: 28px;
  color: #0b0d12;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.stat-card {
  background: white;
  border-radius: 20px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid rgba(11, 13, 18, 0.08);
  box-shadow: 0 16px 40px rgba(8, 10, 18, 0.08);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: #f4f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #6b7282;
}

.stat-icon.approved { background: #dcfce7; color: #16a34a; }
.stat-icon.pending { background: #fef3c7; color: #d97706; }
.stat-icon.checked { background: #dbeafe; color: #2563eb; }

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #0b0d12;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #6b7282;
  margin-top: 4px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.section-header h2 {
  margin: 0;
  font-size: 20px;
  color: #0b0d12;
}

.checkin-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e7e9ef;
}

.checkin-section h3 {
  margin-bottom: 16px;
  font-size: 16px;
  color: #0b0d12;
}

.code-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.code-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.code-value {
  font-size: 20px;
  font-weight: 700;
  font-family: monospace;
  color: #0b0d12;
  letter-spacing: 2px;
}

.code-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #6b7282;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
  }
}
</style>
