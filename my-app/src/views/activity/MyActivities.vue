<template>
  <div class="my-activities-shell">
    <!-- Header -->
    <section class="activities-hero section">
      <div class="section-shell">
        <div class="hero-content">
          <p class="eyebrow">My Activities</p>
          <h1>我的活动</h1>
          <p class="hero-subtitle">
            查看您报名的活动、签到记录和获奖情况
          </p>
        </div>
      </div>
    </section>

    <!-- Filter Tabs -->
    <section class="section">
      <div class="section-shell">
        <div class="filter-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="filter-tab"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            <Icon :icon="tab.icon" />
            <span>{{ tab.label }}</span>
            <span class="tab-badge" v-if="tab.count">{{ tab.count }}</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Activity List -->
    <section class="section section--alt">
      <div class="section-shell">
        <div v-if="loading" class="loading-state">
          <n-spin size="large" />
        </div>

        <div v-else-if="filteredActivities.length === 0" class="empty-state">
          <Icon icon="carbon:events" class="empty-icon" />
          <h3>暂无{{ getTabLabel(activeTab) }}</h3>
          <p>{{ getEmptyText(activeTab) }}</p>
          <n-button type="primary" @click="router.push('/activities')">
            去发现活动
          </n-button>
        </div>

        <div v-else class="activities-list">
          <div
            v-for="item in filteredActivities"
            :key="item.id"
            class="activity-item"
            @click="viewActivity(item.activity_id)"
          >
            <div class="activity-status-bar" :class="item.status"></div>
            
            <div class="activity-content">
              <div class="activity-header">
                <span class="activity-type">{{ item.activity_type }}</span>
                <n-tag :type="getStatusType(item.registration_status)" size="small">
                  {{ getStatusLabel(item.registration_status) }}
                </n-tag>
              </div>

              <h3 class="activity-title">{{ item.activity_name }}</h3>

              <div class="activity-meta">
                <div class="meta-item">
                  <Icon icon="carbon:calendar" />
                  <span>{{ formatDate(item.activity_start_date) }}</span>
                </div>
                <div class="meta-item">
                  <Icon icon="carbon:location" />
                  <span>{{ item.activity_location || '地点待定' }}</span>
                </div>
              </div>

              <div class="activity-footer">
                <div class="checkin-status" v-if="item.checked_in_at">
                  <Icon icon="carbon:checkmark-filled" class="checkin-icon" />
                  <span>已签到 {{ formatTime(item.checked_in_at) }}</span>
                </div>
                <div class="award-badge" v-if="item.award_level">
                  <Icon icon="carbon:trophy" />
                  <span>{{ item.award_level }}</span>
                </div>
              </div>
            </div>

            <div class="activity-actions">
              <n-button v-if="!item.checked_in_at && item.registration_status === 'approved'" 
                       type="primary" size="small" @click.stop="handleCheckin(item)">
                签到
              </n-button>
              <n-button v-if="item.award_level" size="small" @click.stop="viewCertificate(item)">
                查看证书
              </n-button>
              <n-button v-if="item.registration_status === 'pending'" size="small" @click.stop="cancelRegistration(item)">
                取消报名
              </n-button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Check-in Modal -->
    <n-modal v-model:show="showCheckinModal" title="活动签到" style="width: 400px">
      <n-card>
        <div class="checkin-modal-content">
          <div class="checkin-qr-placeholder">
            <Icon icon="carbon:qr-code" class="qr-icon" />
            <p>请扫描二维码或输入签到码</p>
          </div>
          <n-input v-model:value="checkinCode" placeholder="输入6位签到码" maxlength="8" />
          <n-button type="primary" block :loading="checkingIn" @click="submitCheckin">
            确认签到
          </n-button>
        </div>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { Icon } from '@iconify/vue'
import { checkin, cancelRegistration } from '@/api/activity'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const loading = ref(false)
const activeTab = ref('registered')
const showCheckinModal = ref(false)
const checkinCode = ref('')
const checkingIn = ref(false)
const selectedActivity = ref<any>(null)

const tabs = [
  { key: 'registered', label: '已报名', icon: 'carbon:user', count: 0 },
  { key: 'ongoing', label: '进行中', icon: 'carbon:play', count: 0 },
  { key: 'completed', label: '已结束', icon: 'carbon:checkmark', count: 0 },
  { key: 'awarded', label: '已获奖', icon: 'carbon:trophy', count: 0 },
]

const myActivities = ref<any[]>([])

const filteredActivities = computed(() => {
  // 根据activeTab筛选
  return myActivities.value.filter(item => {
    if (activeTab.value === 'registered') return item.registration_status === 'pending' || item.registration_status === 'approved'
    if (activeTab.value === 'ongoing') return item.activity_status === 'published' && !item.checked_in_at
    if (activeTab.value === 'completed') return item.checked_in_at
    if (activeTab.value === 'awarded') return item.award_level
    return true
  })
})

const getTabLabel = (key: string) => {
  const tab = tabs.find(t => t.key === key)
  return tab?.label || key
}

const getEmptyText = (key: string) => {
  const map: Record<string, string> = {
    registered: '您还没有报名任何活动',
    ongoing: '暂无进行中的活动',
    completed: '还没有已完成的活动',
    awarded: '您还没有获得任何奖项',
  }
  return map[key] || ''
}

const loadMyActivities = async () => {
  loading.value = true
  try {
    // TODO: 调用API获取我的活动列表
    // const { data } = await getMyActivities(authStore.userInfo?.id)
    myActivities.value = [] // 临时空数据
  } catch (error) {
    message.error('加载失败')
  } finally {
    loading.value = false
  }
}

const viewActivity = (activityId: number) => {
  router.push(`/activity/${activityId}`)
}

const handleCheckin = (item: any) => {
  selectedActivity.value = item
  showCheckinModal.value = true
}

const submitCheckin = async () => {
  if (!checkinCode.value) {
    message.warning('请输入签到码')
    return
  }
  
  checkingIn.value = true
  try {
    await checkin(checkinCode.value)
    message.success('签到成功')
    showCheckinModal.value = false
    checkinCode.value = ''
    loadMyActivities()
  } catch (error: any) {
    message.error(error.message || '签到失败')
  } finally {
    checkingIn.value = false
  }
}

const viewCertificate = (item: any) => {
  message.info(`查看证书: ${item.activity_name}`)
  // TODO: 打开证书详情
}

const cancelRegistration = async (item: any) => {
  try {
    await cancelRegistration(item.activity_id)
    message.success('取消报名成功')
    loadMyActivities()
  } catch (error) {
    message.error('取消失败')
  }
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'error',
    cancelled: 'default',
  }
  return map[status] || 'default'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    cancelled: '已取消',
  }
  return map[status] || status
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '日期待定'
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatTime = (dateStr?: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  loadMyActivities()
})
</script>

<style scoped>
.my-activities-shell {
  min-height: 100vh;
  background: var(--bg);
}

.activities-hero {
  background: linear-gradient(180deg, #fbfbfc 0%, #f4f5f9 100%);
  padding: 60px 0;
}

.hero-content {
  text-align: center;
}

.eyebrow {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.3em;
  color: #6b7282;
}

.hero-content h1 {
  font-size: clamp(32px, 5vw, 48px);
  color: #0b0d12;
  margin: 12px 0;
}

.hero-subtitle {
  font-size: 16px;
  color: #4d5464;
}

.filter-tabs {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.filter-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 999px;
  border: 1px solid rgba(11, 13, 18, 0.1);
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  color: #4d5464;
}

.filter-tab:hover {
  border-color: #ff7a18;
  color: #ff7a18;
}

.filter-tab.active {
  background: #0b0d12;
  color: white;
  border-color: #0b0d12;
}

.tab-badge {
  background: #ff7a18;
  color: white;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 4px;
}

.loading-state {
  text-align: center;
  padding: 80px;
}

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
  margin-bottom: 24px;
}

.activities-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  display: flex;
  background: white;
  border-radius: 20px;
  overflow: hidden;
  border: 1px solid rgba(11, 13, 18, 0.08);
  box-shadow: 0 16px 40px rgba(8, 10, 18, 0.06);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.activity-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 50px rgba(8, 10, 18, 0.1);
}

.activity-status-bar {
  width: 4px;
  background: #e7e9ef;
}

.activity-status-bar.registered { background: #3b82f6; }
.activity-status-bar.approved { background: #10b981; }
.activity-status-bar.completed { background: #8b5cf6; }

.activity-content {
  flex: 1;
  padding: 24px;
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.activity-type {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #ff7a18;
  font-weight: 600;
}

.activity-title {
  font-size: 18px;
  color: #0b0d12;
  margin: 0 0 12px 0;
}

.activity-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6b7282;
}

.activity-footer {
  display: flex;
  gap: 12px;
}

.checkin-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #10b981;
}

.checkin-icon {
  font-size: 16px;
}

.award-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #ff7a18;
  font-weight: 600;
}

.activity-actions {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  border-left: 1px solid #f3f4f6;
}

.checkin-modal-content {
  text-align: center;
  padding: 20px;
}

.checkin-qr-placeholder {
  margin-bottom: 24px;
}

.qr-icon {
  font-size: 80px;
  color: #e7e9ef;
}

@media (max-width: 640px) {
  .activity-item {
    flex-direction: column;
  }
  
  .activity-actions {
    flex-direction: row;
    border-left: none;
    border-top: 1px solid #f3f4f6;
    padding: 16px 24px;
  }
}
</style>
