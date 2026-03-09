<template>
  <div class="activity-detail-shell">
    <section class="section">
      <div class="section-shell">
        <div class="page-header">
          <n-button quaternary @click="router.back()">
            <template #icon>
              <Icon icon="carbon:arrow-left" />
            </template>
            返回
          </n-button>
          <h1>{{ activity?.name || '活动详情' }}</h1>
          <n-tag :type="getStatusType(activity?.status)">
            {{ getStatusLabel(activity?.status) }}
          </n-tag>
        </div>

        <n-spin :show="loading">
          <div v-if="activity" class="detail-content">
            <n-card class="detail-card">
              <n-descriptions :column="2" bordered>
                <n-descriptions-item label="活动类型">{{ activity.type }}</n-descriptions-item>
                <n-descriptions-item label="活动地点">{{ activity.location || '待定' }}</n-descriptions-item>
                <n-descriptions-item label="开始时间">{{ formatDate(activity.start_date) }}</n-descriptions-item>
                <n-descriptions-item label="结束时间">{{ formatDate(activity.end_date) }}</n-descriptions-item>
                <n-descriptions-item label="报名时间">{{ formatDate(activity.register_start) }} ~ {{ formatDate(activity.register_end) }}</n-descriptions-item>
                <n-descriptions-item label="名额">{{ activity.registered_count }} / {{ activity.quota || '不限' }}</n-descriptions-item>
              </n-descriptions>
              
              <div class="description-section">
                <h3>活动说明</h3>
                <p>{{ activity.description || '暂无说明' }}</p>
              </div>
            </n-card>

            <div class="detail-actions">
              <n-button type="primary" @click="handleRegister" v-if="activity.status === 'published'">
                立即报名
              </n-button>
              <n-button @click="router.push(`/activity/${activityId}/manage`)" v-if="isManager">
                管理活动
              </n-button>
            </div>
          </div>
        </n-spin>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { Icon } from '@iconify/vue'
import { getActivityDetail, registerActivity } from '@/api/activity'
import type { Activity } from '@/api/activity'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const activityId = Number(route.params.id)
const loading = ref(false)
const activity = ref<Activity | null>(null)
const isManager = ref(false)

const loadActivity = async () => {
  loading.value = true
  try {
    const { data } = await getActivityDetail(activityId)
    activity.value = data as any
  } catch (error) {
    message.error('加载活动详情失败')
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  try {
    await registerActivity(activityId)
    message.success('报名成功')
    loadActivity()
  } catch (error: any) {
    message.error(error.message || '报名失败')
  }
}

const getStatusType = (status?: string) => {
  const map: Record<string, string> = {
    draft: 'default',
    published: 'success',
    ended: 'info',
    cancelled: 'error',
  }
  return map[status || ''] || 'default'
}

const getStatusLabel = (status?: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    published: '已发布',
    ended: '已结束',
    cancelled: '已取消',
  }
  return map[status || ''] || status
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '待定'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadActivity()
})
</script>

<style scoped>
.activity-detail-shell {
  min-height: 100vh;
  background: var(--bg);
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.page-header h1 {
  margin: 0;
  flex: 1;
  font-size: 28px;
  color: #0b0d12;
}

.detail-card {
  border-radius: 18px;
  margin-bottom: 24px;
}

.description-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e7e9ef;
}

.description-section h3 {
  font-size: 16px;
  color: #0b0d12;
  margin-bottom: 12px;
}

.description-section p {
  color: #5a6172;
  line-height: 1.6;
}

.detail-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}
</style>
