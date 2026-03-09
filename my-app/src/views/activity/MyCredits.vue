<template>
  <div class="my-credits-shell">
    <!-- Header -->
    <section class="credits-hero section">
      <div class="section-shell">
        <div class="hero-content">
          <p class="eyebrow">My Credits</p>
          <h1>我的学分</h1>
          <p class="hero-subtitle">
            查看您的学分统计、历史记录和证书。所有学分数据实时同步，可追溯可验证。
          </p>
        </div>
      </div>
    </section>

    <!-- Summary Cards -->
    <section class="section">
      <div class="section-shell">
        <div class="credits-summary">
          <div class="summary-card total">
            <div class="summary-icon"><Icon icon="carbon:chart-pie" /></div>
            <div class="summary-info">
              <span class="summary-value">{{ creditSummary.total_score?.toFixed(1) || '0.0' }}</span>
              <span class="summary-label">总学分</span>
            </div>
          </div>
          <div class="summary-card activity">
            <div class="summary-icon"><Icon icon="carbon:events" /></div>
            <div class="summary-info">
              <span class="summary-value">{{ getTypeScore('activity') }}</span>
              <span class="summary-label">活动学分</span>
            </div>
          </div>
          <div class="summary-card competition">
            <div class="summary-icon"><Icon icon="carbon:trophy" /></div>
            <div class="summary-info">
              <span class="summary-value">{{ getTypeScore('competition') }}</span>
              <span class="summary-label">竞赛学分</span>
            </div>
          </div>
          <div class="summary-card volunteer">
            <div class="summary-icon"><Icon icon="carbon:friendship" /></div>
            <div class="summary-info">
              <span class="summary-value">{{ getTypeScore('volunteer') }}</span>
              <span class="summary-label">志愿学分</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Ledger & Certificates -->
    <section class="section section--alt">
      <div class="section-shell">
        <n-tabs type="line" animated>
          <n-tab-pane name="ledger" tab="学分明细">
            <div class="tab-content">
              <div class="tab-header">
                <n-select
                  v-model:value="selectedTerm"
                  :options="termOptions"
                  placeholder="选择学期"
                  clearable
                  style="width: 180px"
                  @update:value="loadLedger"
                />
              </div>
              
              <n-timeline class="ledger-timeline">
                <n-timeline-item
                  v-for="entry in ledgerEntries"
                  :key="entry.id"
                  :type="entry.delta_value > 0 ? 'success' : 'error'"
                >
                  <div class="ledger-item">
                    <div class="ledger-header">
                      <span class="ledger-term">{{ entry.term }}</span>
                      <span class="ledger-score" :class="entry.delta_value > 0 ? 'positive' : 'negative'">
                        {{ entry.delta_value > 0 ? '+' : '' }}{{ entry.delta_value }}
                      </span>
                    </div>
                    <div class="ledger-body">
                      <p class="ledger-source">{{ getSourceLabel(entry.source_type) }}</p>
                      <p class="ledger-time">{{ formatDate(entry.created_at) }}</p>
                    </div>
                  </div>
                </n-timeline-item>
              </n-timeline>

              <n-empty v-if="ledgerEntries.length === 0" description="暂无学分记录" />
            </div>
          </n-tab-pane>

          <n-tab-pane name="certificates" tab="我的证书">
            <div class="tab-content">
              <div class="certificates-grid">
                <div
                  v-for="cert in certificates"
                  :key="cert.id"
                  class="certificate-card"
                  @click="viewCertificate(cert)"
                >
                  <div class="cert-preview">
                    <Icon icon="carbon:certificate" class="cert-icon" />
                  </div>
                  <div class="cert-info">
                    <h4>{{ cert.certificate_type === 'award' ? '获奖证书' : '参与证明' }}</h4>
                    <p class="cert-no">No. {{ cert.certificate_no }}</p>
                    <p class="cert-date">{{ formatDate(cert.issued_at) }}</p>
                  </div>
                  <n-button size="small" quaternary class="cert-download">
                    <template #icon><Icon icon="carbon:download" /></template>
                  </n-button>
                </div>
              </div>

              <n-empty v-if="certificates.length === 0" description="暂无证书">
                <template #extra>
                  <n-button @click="router.push('/activities')">去参加活动</n-button>
                </template>
              </n-empty>
            </div>
          </n-tab-pane>

          <n-tab-pane name="stats" tab="统计分析">
            <div class="tab-content">
              <div class="stats-chart-placeholder">
                <Icon icon="carbon:chart-bar" class="chart-icon" />
                <p>学分趋势统计图表</p>
              </div>
            </div>
          </n-tab-pane>
        </n-tabs>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { Icon } from '@iconify/vue'
import { getStudentCreditSummary, getCreditLedger, getStudentCertificates } from '@/api/activity'
import type { CreditLedger, Certificate } from '@/api/activity'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const studentId = computed(() => authStore.userInfo?.id || 0)
const loading = ref(false)
const creditSummary = reactive({
  total_score: 0,
  entry_count: 0,
  type_breakdown: [] as any[],
})
const ledgerEntries = ref<CreditLedger[]>([])
const certificates = ref<Certificate[]>([])
const selectedTerm = ref('')

const termOptions = [
  { label: '2024-2025-1', value: '2024-2025-1' },
  { label: '2023-2024-2', value: '2023-2024-2' },
  { label: '2023-2024-1', value: '2023-2024-1' },
]

const getTypeScore = (type: string) => {
  const item = creditSummary.type_breakdown?.find((t: any) => t.score_type === type)
  return item ? item.total.toFixed(1) : '0.0'
}

const getSourceLabel = (sourceType: string) => {
  const map: Record<string, string> = {
    'activity_award': '活动获奖',
    'competition': '竞赛获奖',
    'volunteer': '志愿服务',
    'reverse:activity_award': '学分冲销',
  }
  return map[sourceType] || sourceType
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const loadSummary = async () => {
  try {
    const { data } = await getStudentCreditSummary(studentId.value)
    if (data) {
      creditSummary.total_score = data.total_score
      creditSummary.entry_count = data.entry_count
      creditSummary.type_breakdown = data.type_breakdown || []
    }
  } catch (error) {
    console.error('加载学分汇总失败', error)
  }
}

const loadLedger = async () => {
  try {
    const { data } = await getCreditLedger(studentId.value, {
      term: selectedTerm.value || undefined,
      page: 1,
      page_size: 50,
    })
    ledgerEntries.value = data?.items || []
  } catch (error) {
    console.error('加载学分明细失败', error)
  }
}

const loadCertificates = async () => {
  try {
    const { data } = await getStudentCertificates(studentId.value)
    certificates.value = data || []
  } catch (error) {
    console.error('加载证书失败', error)
  }
}

const viewCertificate = (cert: Certificate) => {
  message.info(`查看证书: ${cert.certificate_no}`)
  // TODO: 打开证书预览
}

onMounted(() => {
  loadSummary()
  loadLedger()
  loadCertificates()
})
</script>

<style scoped>
.my-credits-shell {
  min-height: 100vh;
  background: var(--bg);
}

.credits-hero {
  background: linear-gradient(180deg, #fbfbfc 0%, #f4f5f9 65%, #ffffff 100%);
  padding: 60px 0 80px;
}

.hero-content {
  max-width: 1360px;
  margin: 0 auto;
  padding: 0 clamp(24px, 6vw, 80px);
  text-align: center;
}

.eyebrow {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.3em;
  color: #6b7282;
  margin-bottom: 12px;
}

.hero-content h1 {
  font-size: clamp(36px, 5vw, 52px);
  color: #0b0d12;
  margin: 0 0 16px 0;
}

.hero-subtitle {
  font-size: 17px;
  color: #4d5464;
  max-width: 600px;
  margin: 0 auto;
}

.credits-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-top: -40px;
  position: relative;
  z-index: 10;
}

.summary-card {
  background: white;
  border-radius: 24px;
  padding: 28px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid rgba(11, 13, 18, 0.08);
  box-shadow: 0 20px 50px rgba(8, 10, 18, 0.12);
}

.summary-card.total { border-top: 4px solid #ff7a18; }
.summary-card.activity { border-top: 4px solid #3b82f6; }
.summary-card.competition { border-top: 4px solid #8b5cf6; }
.summary-card.volunteer { border-top: 4px solid #10b981; }

.summary-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.summary-card.total .summary-icon { background: #fff7ed; color: #ff7a18; }
.summary-card.activity .summary-icon { background: #eff6ff; color: #3b82f6; }
.summary-card.competition .summary-icon { background: #f5f3ff; color: #8b5cf6; }
.summary-card.volunteer .summary-icon { background: #ecfdf5; color: #10b981; }

.summary-info {
  display: flex;
  flex-direction: column;
}

.summary-value {
  font-size: 32px;
  font-weight: 700;
  color: #0b0d12;
  line-height: 1;
}

.summary-label {
  font-size: 14px;
  color: #6b7282;
  margin-top: 4px;
}

.tab-content {
  padding: 24px 0;
}

.tab-header {
  margin-bottom: 24px;
}

.ledger-timeline {
  max-width: 800px;
}

.ledger-item {
  padding: 8px 0;
}

.ledger-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.ledger-term {
  font-weight: 600;
  color: #0b0d12;
}

.ledger-score {
  font-size: 20px;
  font-weight: 700;
}

.ledger-score.positive { color: #16a34a; }
.ledger-score.negative { color: #dc2626; }

.ledger-body {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #6b7282;
}

.certificates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.certificate-card {
  background: white;
  border-radius: 20px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid rgba(11, 13, 18, 0.08);
  box-shadow: 0 16px 40px rgba(8, 10, 18, 0.08);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.certificate-card:hover {
  transform: translateY(-4px);
}

.cert-preview {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cert-icon {
  font-size: 32px;
  color: #ff7a18;
}

.cert-info {
  flex: 1;
}

.cert-info h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: #0b0d12;
}

.cert-no {
  font-size: 13px;
  color: #6b7282;
  margin: 0;
}

.cert-date {
  font-size: 12px;
  color: #9ca3af;
  margin: 4px 0 0 0;
}

.cert-download {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.certificate-card:hover .cert-download {
  opacity: 1;
}

.stats-chart-placeholder {
  height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f8f9fb;
  border-radius: 24px;
  border: 2px dashed #e7e9ef;
}

.chart-icon {
  font-size: 64px;
  color: #c1c7d0;
  margin-bottom: 16px;
}

@media (max-width: 1024px) {
  .credits-summary {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .credits-summary {
    grid-template-columns: 1fr;
    margin-top: -20px;
  }
}
</style>
