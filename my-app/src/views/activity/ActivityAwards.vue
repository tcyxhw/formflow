<template>
  <div class="activity-awards-shell">
    <!-- Header -->
    <section class="awards-header section">
      <div class="section-shell">
        <div class="header-content">
          <n-button quaternary @click="router.back()">
            <template #icon><Icon icon="carbon:arrow-left" /></template>
            返回
          </n-button>
          <div class="header-title">
            <h1>评分评奖</h1>
            <span class="subtitle">{{ activity?.name }}</span>
          </div>
          <div class="header-actions">
            <n-button type="primary" @click="handleFinalize" :disabled="finalized">
              <template #icon><Icon icon="carbon:trophy" /></template>
              Finalize获奖名单
            </n-button>
          </div>
        </div>
      </div>
    </section>

    <!-- Award Stats -->
    <section class="section">
      <div class="section-shell">
        <div class="award-stats-grid">
          <div class="award-stat-card first">
            <Icon icon="carbon:trophy" class="award-icon" />
            <div class="award-info">
              <span class="award-value">{{ awardStats.first }}</span>
              <span class="award-label">一等奖</span>
            </div>
          </div>
          <div class="award-stat-card second">
            <Icon icon="carbon:medal" class="award-icon" />
            <div class="award-info">
              <span class="award-value">{{ awardStats.second }}</span>
              <span class="award-label">二等奖</span>
            </div>
          </div>
          <div class="award-stat-card third">
            <Icon icon="carbon:star" class="award-icon" />
            <div class="award-info">
              <span class="award-value">{{ awardStats.third }}</span>
              <span class="award-label">三等奖</span>
            </div>
          </div>
          <div class="award-stat-card participation">
            <Icon icon="carbon:user" class="award-icon" />
            <div class="award-info">
              <span class="award-value">{{ awardStats.participation }}</span>
              <span class="award-label">参与奖</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Scoring Section -->
    <section class="section section--alt">
      <div class="section-shell">
        <div class="section-header">
          <h2>学生评分</h2>
          <n-space>
            <n-select v-model:value="filterAward" :options="awardFilterOptions" clearable placeholder="筛选奖项" style="width: 140px" />
            <n-button @click="showScoreModal = true" type="primary">
              <template #icon><Icon icon="carbon:add" /></template>
              添加评分
            </n-button>
          </n-space>
        </div>

        <n-data-table
          :columns="columns"
          :data="filteredRecords"
          :loading="loading"
          :pagination="pagination"
        />
      </div>
    </section>

    <!-- Credit Section -->
    <section class="section" v-if="finalized">
      <div class="section-shell">
        <div class="credit-section">
          <h2>学分发放</h2>
          <p class="credit-desc">获奖名单已Finalize，可以发放学分</p>
          <n-button type="primary" size="large" @click="handleIssueCredits" :loading="issuingCredits">
            <template #icon><Icon icon="carbon:certificate" /></template>
            批量发放学分
          </n-button>
        </div>
      </div>
    </section>

    <!-- Score Modal -->
    <n-modal v-model:show="showScoreModal" title="提交评分" style="width: 500px">
      <n-card>
        <n-form :model="scoreForm" label-width="100px">
          <n-form-item label="学生">
            <n-select
              v-model:value="scoreForm.student_id"
              :options="studentOptions"
              placeholder="选择学生"
              filterable
            />
          </n-form-item>
          <n-form-item label="奖项等级">
            <n-select v-model:value="scoreForm.award_level" :options="awardLevelOptions" placeholder="选择奖项" />
          </n-form-item>
          <n-form-item label="创意得分">
            <n-slider v-model:value="scoreForm.creativity" :max="100" />
          </n-form-item>
          <n-form-item label="完成度">
            <n-slider v-model:value="scoreForm.completion" :max="100" />
          </n-form-item>
          <n-form-item label="表达力">
            <n-slider v-model:value="scoreForm.expression" :max="100" />
          </n-form-item>
          <n-form-item label="评语">
            <n-input v-model:value="scoreForm.comment" type="textarea" :rows="3" placeholder="输入评语..." />
          </n-form-item>
        </n-form>
        <template #footer>
          <n-space justify="end">
            <n-button @click="showScoreModal = false">取消</n-button>
            <n-button type="primary" @click="submitScore" :loading="submitting">提交</n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage, NButton, NTag, NSpace } from 'naive-ui'
import { Icon } from '@iconify/vue'
import { getActivityDetail, getAwardStats, submitAward, finalizeAwards, issueCredits } from '@/api/activity'
import type { Activity, AwardRecord } from '@/api/activity'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const activityId = Number(route.params.id)
const loading = ref(false)
const activity = ref<Activity | null>(null)
const awardRecords = ref<AwardRecord[]>([])
const finalized = ref(false)
const showScoreModal = ref(false)
const submitting = ref(false)
const issuingCredits = ref(false)
const filterAward = ref('')

const awardStats = reactive({
  first: 0,
  second: 0,
  third: 0,
  participation: 0,
})

const scoreForm = reactive({
  student_id: null as number | null,
  award_level: '',
  creativity: 80,
  completion: 80,
  expression: 80,
  comment: '',
})

const studentOptions = ref<{ label: string; value: number }[]>([])

const awardLevelOptions = [
  { label: '一等奖', value: '一等奖' },
  { label: '二等奖', value: '二等奖' },
  { label: '三等奖', value: '三等奖' },
  { label: '参与奖', value: '参与奖' },
]

const awardFilterOptions = [
  { label: '全部', value: '' },
  ...awardLevelOptions,
]

const filteredRecords = computed(() => {
  if (!filterAward.value) return awardRecords.value
  return awardRecords.value.filter(r => r.award_level === filterAward.value)
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
})

const columns = [
  { title: '学生姓名', key: 'student_name', width: 120 },
  { title: '学号', key: 'student_no', width: 150 },
  {
    title: '奖项',
    key: 'award_level',
    width: 120,
    render(row: any) {
      const colorMap: Record<string, string> = {
        '一等奖': '#ff7a18',
        '二等奖': '#64748b',
        '三等奖': '#92400e',
        '参与奖': '#6b7282',
      }
      return h(NTag, { style: { color: colorMap[row.award_level], fontWeight: 'bold' }, bordered: false }, 
        { default: () => row.award_level }
      )
    },
  },
  {
    title: '综合得分',
    key: 'total_score',
    width: 120,
    render(row: any) {
      const avg = row.score_breakdown ? 
        Object.values(row.score_breakdown).reduce((a: any, b: any) => a + b, 0) / Object.values(row.score_breakdown).length 
        : 0
      return h('span', { style: { fontWeight: 'bold', fontSize: '16px' } }, Math.round(avg).toString())
    },
  },
  { title: '评委', key: 'judge_name', width: 120 },
  { title: '评语', key: 'comment', ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render(row: any) {
      return h(NButton, { size: 'small', onClick: () => viewDetail(row) }, { default: () => '详情' })
    },
  },
]

const loadActivity = async () => {
  loading.value = true
  try {
    const { data } = await getActivityDetail(activityId)
    activity.value = data?.activity
    await loadAwardStats()
  } catch (error) {
    message.error('加载失败')
  } finally {
    loading.value = false
  }
}

const loadAwardStats = async () => {
  try {
    const { data } = await getAwardStats(activityId)
    if (data?.rankings) {
      awardStats.first = data.rankings.filter((r: any) => r.final_award === '一等奖').length
      awardStats.second = data.rankings.filter((r: any) => r.final_award === '二等奖').length
      awardStats.third = data.rankings.filter((r: any) => r.final_award === '三等奖').length
      awardStats.participation = data.rankings.filter((r: any) => r.final_award === '参与奖').length
      awardRecords.value = data.rankings
    }
  } catch (error) {
    console.error('加载评奖统计失败', error)
  }
}

const submitScore = async () => {
  if (!scoreForm.student_id || !scoreForm.award_level) {
    message.warning('请填写完整信息')
    return
  }
  
  submitting.value = true
  try {
    await submitAward(activityId, {
      student_user_id: scoreForm.student_id,
      award_level: scoreForm.award_level,
      score_breakdown: {
        creativity: scoreForm.creativity,
        completion: scoreForm.completion,
        expression: scoreForm.expression,
      },
      comment: scoreForm.comment,
    })
    message.success('评分提交成功')
    showScoreModal.value = false
    loadAwardStats()
  } catch (error) {
    message.error('提交失败')
  } finally {
    submitting.value = false
  }
}

const handleFinalize = async () => {
  try {
    await finalizeAwards(activityId)
    message.success('获奖名单已Finalize')
    finalized.value = true
    loadAwardStats()
  } catch (error) {
    message.error('Finalize失败')
  }
}

const handleIssueCredits = async () => {
  issuingCredits.value = true
  try {
    const { data } = await issueCredits(activityId)
    message.success(`学分发放成功，共${data.issued_count}人`)
  } catch (error) {
    message.error('发放失败')
  } finally {
    issuingCredits.value = false
  }
}

const viewDetail = (row: any) => {
  message.info(`查看详情: ${row.student_name}`)
}

onMounted(() => {
  loadActivity()
})
</script>

<style scoped>
.activity-awards-shell {
  min-height: 100vh;
  background: var(--bg);
}

.awards-header {
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
  padding: 60px 0;
  color: white;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-title {
  flex: 1;
}

.header-title h1 {
  margin: 0;
  font-size: 32px;
  color: white;
}

.subtitle {
  font-size: 16px;
  opacity: 0.8;
  margin-top: 8px;
  display: block;
}

.award-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.award-stat-card {
  background: white;
  border-radius: 20px;
  padding: 28px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 2px solid transparent;
  box-shadow: 0 16px 40px rgba(8, 10, 18, 0.08);
}

.award-stat-card.first { border-color: #ff7a18; background: linear-gradient(135deg, #fff7ed 0%, #ffffff 100%); }
.award-stat-card.second { border-color: #64748b; background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); }
.award-stat-card.third { border-color: #92400e; background: linear-gradient(135deg, #fffbeb 0%, #ffffff 100%); }
.award-stat-card.participation { border-color: #e7e9ef; }

.award-icon {
  font-size: 40px;
}

.award-stat-card.first .award-icon { color: #ff7a18; }
.award-stat-card.second .award-icon { color: #64748b; }
.award-stat-card.third .award-icon { color: #92400e; }
.award-stat-card.participation .award-icon { color: #6b7282; }

.award-info {
  display: flex;
  flex-direction: column;
}

.award-value {
  font-size: 36px;
  font-weight: 700;
  color: #0b0d12;
  line-height: 1;
}

.award-label {
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

.credit-section {
  text-align: center;
  padding: 48px;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-radius: 24px;
  border: 2px dashed #16a34a;
}

.credit-section h2 {
  margin: 0 0 12px 0;
  font-size: 24px;
  color: #166534;
}

.credit-desc {
  color: #16a34a;
  margin-bottom: 24px;
}

@media (max-width: 1024px) {
  .award-stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .award-stats-grid {
    grid-template-columns: 1fr;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
