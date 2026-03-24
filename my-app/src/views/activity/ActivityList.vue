<template>
  <div class="activity-shell">
    <!-- Hero Section -->
    <section class="activity-hero section section--cut">
      <div class="hero-shapes" aria-hidden="true">
        <span class="hero-shard hero-shard--left"></span>
        <span class="hero-shard hero-shard--right"></span>
        <span class="hero-orb hero-orb--one"></span>
      </div>
      <div class="activity-hero__content">
        <div class="activity-hero__inner">
          <p class="eyebrow">Activity Management</p>
          <h1>活动管理中心</h1>
          <p class="activity-hero__subtitle">
            创建、管理和追踪校园活动全流程。从报名签到到评分评奖，一站式解决活动组织难题。
          </p>
          <div class="activity-hero__actions">
            <n-button type="primary" size="large" class="cta-primary" @click="handleCreate">
              <template #icon>
                <Icon icon="carbon:add" />
              </template>
              创建活动
            </n-button>
            <n-button size="large" quaternary class="cta-secondary" @click="handleRefresh">
              <template #icon>
                <Icon icon="carbon:renew" />
              </template>
              刷新列表
            </n-button>
          </div>
        </div>
        <div class="activity-hero__stats">
          <div class="stat-card">
            <span class="stat-label">进行中的活动</span>
            <strong class="stat-value">{{ stats.active }}</strong>
          </div>
          <div class="stat-card">
            <span class="stat-label">总报名人数</span>
            <strong class="stat-value">{{ stats.totalRegistrations }}</strong>
          </div>
          <div class="stat-card">
            <span class="stat-label">今日签到</span>
            <strong class="stat-value">{{ stats.todayCheckins }}</strong>
          </div>
        </div>
      </div>
    </section>

    <!-- Filter Section -->
    <section class="section">
      <div class="section-shell">
        <div class="filter-bar">
          <div class="filter-group">
            <n-input
              v-model:value="filters.keyword"
              placeholder="搜索活动名称..."
              clearable
              class="filter-search"
            >
              <template #prefix>
                <Icon icon="carbon:search" />
              </template>
            </n-input>
            <n-select
              v-model:value="filters.status"
              placeholder="活动状态"
              clearable
              :options="statusOptions"
              class="filter-select"
            />
            <n-select
              v-model:value="filters.type"
              placeholder="活动类型"
              clearable
              :options="typeOptions"
              class="filter-select"
            />
          </div>
          <n-button @click="handleFilter" type="primary" secondary>
            <template #icon>
              <Icon icon="carbon:filter" />
            </template>
            筛选
          </n-button>
        </div>
      </div>
    </section>

    <!-- Activity List -->
    <section class="section section--alt">
      <div class="section-shell">
        <div v-if="loading" class="loading-state">
          <n-spin size="large" />
          <p>加载中...</p>
        </div>

        <div v-else-if="activities.length === 0" class="empty-state">
          <Icon icon="carbon:events" class="empty-icon" />
          <h3>暂无活动</h3>
          <p>点击"创建活动"按钮开始组织您的第一个活动</p>
        </div>

        <div v-else class="activity-grid">
          <article
            v-for="activity in activities"
            :key="activity.id"
            class="activity-card"
            :class="`activity-card--${activity.status}`"
            @click="handleViewDetail(activity)"
          >
            <div class="activity-card__header">
              <span class="activity-type">{{ activity.type }}</span>
              <n-tag :type="getStatusType(activity.status)" size="small" round>
                {{ getStatusLabel(activity.status) }}
              </n-tag>
            </div>

            <h3 class="activity-card__title">{{ activity.name }}</h3>

            <div class="activity-card__meta">
              <div class="meta-item">
                <Icon icon="carbon:location" />
                <span>{{ activity.location || '地点待定' }}</span>
              </div>
              <div class="meta-item">
                <Icon icon="carbon:calendar" />
                <span>{{ formatDate(activity.start_date) }}</span>
              </div>
              <div class="meta-item">
                <Icon icon="carbon:user" />
                <span>{{ activity.registered_count }} / {{ activity.quota || '不限' }} 人</span>
              </div>
            </div>

            <div class="activity-card__progress">
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :style="{ width: getProgressWidth(activity) + '%' }"
                ></div>
              </div>
              <span class="progress-text">{{ getProgressText(activity) }}</span>
            </div>

            <div class="activity-card__actions">
              <n-button
                v-if="activity.status === 'draft'"
                size="small"
                type="primary"
                @click.stop="handlePublish(activity)"
              >
                发布
              </n-button>
              <n-button
                v-else-if="activity.status === 'published'"
                size="small"
                @click.stop="handleManage(activity)"
              >
                管理
              </n-button>
              <n-button size="small" quaternary @click.stop="handleEdit(activity)">
                编辑
              </n-button>
            </div>
          </article>
        </div>

        <!-- Pagination -->
        <div class="pagination-bar">
          <n-pagination
            v-model:page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :item-count="pagination.total"
            :page-sizes="[12, 24, 48]"
            show-size-picker
            @update:page="handlePageChange"
            @update:page-size="handlePageSizeChange"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { Icon } from '@iconify/vue'
import { listActivities, publishActivity } from '@/api/activity'
import type { Activity } from '@/api/activity'

const router = useRouter()
const message = useMessage()

// State
const loading = ref(false)
const activities = ref<Activity[]>([])
const filters = reactive({
  keyword: '',
  status: null as string | null,
  type: null as string | null,
})
const pagination = reactive({
  page: 1,
  pageSize: 12,
  total: 0,
})
const stats = reactive({
  active: 0,
  totalRegistrations: 0,
  todayCheckins: 0,
})

// Options
const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '已发布', value: 'published' },
  { label: '已结束', value: 'ended' },
  { label: '已取消', value: 'cancelled' },
]

const typeOptions = [
  { label: '学术讲座', value: 'lecture' },
  { label: '文体活动', value: 'sports' },
  { label: '志愿服务', value: 'volunteer' },
  { label: '竞赛比赛', value: 'competition' },
  { label: '社团活动', value: 'club' },
]

// Methods
const loadActivities = async () => {
  loading.value = true
  try {
    const { data } = await listActivities({
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
      activity_type: filters.type || undefined,
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    activities.value = data?.items || []
    pagination.total = data?.total || 0
  } catch (error) {
    message.error('加载活动列表失败')
  } finally {
    loading.value = false
  }
}

const handleFilter = () => {
  pagination.page = 1
  loadActivities()
}

const handleRefresh = () => {
  loadActivities()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  loadActivities()
}

const handlePageSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.page = 1
  loadActivities()
}

const handleCreate = () => {
  router.push('/activity/create')
}

const handleViewDetail = (activity: Activity) => {
  router.push(`/activity/${activity.id}`)
}

const handleEdit = (activity: Activity) => {
  router.push(`/activity/${activity.id}/edit`)
}

const handleManage = (activity: Activity) => {
  router.push(`/activity/${activity.id}/manage`)
}

const handlePublish = async (activity: Activity) => {
  try {
    await publishActivity(activity.id)
    message.success('活动发布成功')
    loadActivities()
  } catch (error) {
    message.error('发布失败')
  }
}

// Helpers
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    draft: 'default',
    published: 'success',
    ended: 'info',
    cancelled: 'error',
  }
  return map[status] || 'default'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    published: '已发布',
    ended: '已结束',
    cancelled: '已取消',
  }
  return map[status] || status
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '日期待定'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
  })
}

const getProgressWidth = (activity: Activity) => {
  if (!activity.quota) return 0
  return Math.min((activity.registered_count / activity.quota) * 100, 100)
}

const getProgressText = (activity: Activity) => {
  if (!activity.quota) return '名额不限'
  const percent = Math.round((activity.registered_count / activity.quota) * 100)
  return `已报名 ${percent}%`
}

// Lifecycle
onMounted(() => {
  loadActivities()
})
</script>

<style scoped>
.activity-shell {
  min-height: 100vh;
  background: var(--bg);
}

.activity-hero {
  position: relative;
  padding: 60px 0 80px;
  background: linear-gradient(180deg, #fbfbfc 0%, #f4f5f9 65%, #ffffff 100%);
  overflow: hidden;
}

.activity-hero__content {
  position: relative;
  z-index: 1;
  max-width: 1360px;
  margin: 0 auto;
  padding: 0 clamp(24px, 6vw, 80px);
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 48px;
  align-items: center;
}

.activity-hero__inner {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.activity-hero__inner h1 {
  font-size: clamp(36px, 5vw, 52px);
  line-height: 1.1;
  color: #0b0d12;
  margin: 0;
}

.activity-hero__subtitle {
  font-size: 17px;
  color: #4d5464;
  line-height: 1.6;
  max-width: 480px;
}

.activity-hero__actions {
  display: flex;
  gap: 16px;
  margin-top: 8px;
}

.activity-hero__stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card {
  background: white;
  border-radius: 24px;
  padding: 24px;
  border: 1px solid rgba(11, 13, 18, 0.08);
  box-shadow: 0 16px 40px rgba(8, 10, 18, 0.08);
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 13px;
  color: #6b7282;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  color: #0b0d12;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-search {
  width: 280px;
}

.filter-select {
  width: 160px;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  font-size: 64px;
  color: #c1c7d0;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 20px;
  color: #0b0d12;
  margin-bottom: 8px;
}

.empty-state p {
  color: #6b7282;
}

.activity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}

.activity-card {
  background: white;
  border-radius: 28px;
  padding: 28px;
  border: 1px solid rgba(11, 13, 18, 0.08);
  box-shadow: 0 16px 40px rgba(8, 10, 18, 0.08);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.activity-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 24px 60px rgba(8, 10, 18, 0.12);
}

.activity-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.activity-type {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #ff7a18;
  font-weight: 600;
}

.activity-card__title {
  font-size: 20px;
  color: #0b0d12;
  margin: 0 0 16px 0;
  line-height: 1.4;
}

.activity-card__meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #5a6172;
}

.activity-card__progress {
  margin-bottom: 20px;
}

.progress-bar {
  height: 6px;
  background: #e7e9ef;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #111217, #ff7a18);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: #6b7282;
}

.activity-card__actions {
  display: flex;
  gap: 8px;
}

.pagination-bar {
  display: flex;
  justify-content: center;
  margin-top: 48px;
  padding-top: 32px;
  border-top: 1px solid rgba(11, 13, 18, 0.08);
}

/* Decorative shapes */
.hero-shapes {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.hero-shard {
  position: absolute;
  width: 40%;
  height: 80%;
  background: linear-gradient(140deg, rgba(255, 255, 255, 0.7), rgba(251, 236, 224, 0.2));
  clip-path: polygon(0 0, 100% 0, 82% 100%, 0% 100%);
  opacity: 0.6;
}

.hero-shard--left {
  left: -10%;
  top: -8%;
}

.hero-shard--right {
  right: -15%;
  top: 10%;
  transform: scaleX(-1);
}

.hero-orb {
  position: absolute;
  width: 260px;
  height: 260px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 122, 24, 0.22), transparent 65%);
  filter: blur(2px);
}

.hero-orb--one {
  top: -40px;
  right: 20%;
}

@media (max-width: 1024px) {
  .activity-hero__content {
    grid-template-columns: 1fr;
  }
  
  .activity-hero__stats {
    order: -1;
  }
}

@media (max-width: 640px) {
  .filter-group {
    width: 100%;
  }
  
  .filter-search,
  .filter-select {
    width: 100%;
  }
  
  .activity-grid {
    grid-template-columns: 1fr;
  }
}
</style>
