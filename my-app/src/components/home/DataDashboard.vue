<!-- src/components/home/DataDashboard.vue -->
<template>
  <div class="data-dashboard">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon pending">
          <n-icon size="24"><ClipboardOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.pending_tasks }}</div>
          <div class="stat-label">待办任务</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon processed">
          <n-icon size="24"><CheckmarkCircleOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.weekly_processed }}</div>
          <div class="stat-label">本周处理量</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon time">
          <n-icon size="24"><TimeOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ formatTime(stats.avg_processing_time_minutes) }}</div>
          <div class="stat-label">平均处理时长</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon rate">
          <n-icon size="24"><TrendingUpOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.approval_rate }}%</div>
          <div class="stat-label">审批通过率</div>
        </div>
      </div>
    </div>

    <div class="dashboard-grid">
      <!-- 提交量趋势图 -->
      <div class="chart-card">
        <div class="card-header">
          <h3 class="card-title">提交量趋势</h3>
          <n-tag size="small" type="info" :bordered="false">最近 7 天</n-tag>
        </div>
        <div class="card-content">
          <div class="chart-wrapper">
            <div v-if="!chartReady1" class="chart-placeholder">图表加载中...</div>
            <div 
              v-show="chartReady1"
              ref="chartRef1" 
              class="chart-container" 
              role="img" 
              aria-label="提交量趋势折线图"
            ></div>
          </div>
        </div>
      </div>

      <!-- 审批通过率图 -->
      <div class="chart-card">
        <div class="card-header">
          <h3 class="card-title">审批通过率</h3>
          <n-tag size="small" type="success" :bordered="false">实时数据</n-tag>
        </div>
        <div class="card-content">
          <div class="chart-wrapper">
            <div v-if="!chartReady2" class="chart-placeholder">图表加载中...</div>
            <div 
              v-show="chartReady2"
              ref="chartRef2" 
              class="chart-container"
              role="img" 
              aria-label="审批通过率饼图"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { NIcon, NTag } from 'naive-ui'
import { ClipboardOutline, CheckmarkCircleOutline, TimeOutline, TrendingUpOutline } from '@vicons/ionicons5'
import { useHomeInteractive } from '@/stores/homeInteractive'
import { getDashboardStats } from '@/api/dashboard'
import type { DashboardStats } from '@/types/dashboard'

const store = useHomeInteractive()
const chartRef1 = ref<HTMLDivElement>()
const chartRef2 = ref<HTMLDivElement>()
const chartReady1 = ref(false)
const chartReady2 = ref(false)

const stats = ref<DashboardStats>({
  pending_tasks: 0,
  weekly_processed: 0,
  avg_processing_time_minutes: 0,
  approval_rate: 0,
})

let chart1: echarts.ECharts | null = null
let chart2: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null

const formatTime = (minutes: number): string => {
  if (minutes < 60) {
    return `${Math.round(minutes)}分钟`
  }
  const hours = Math.floor(minutes / 60)
  const mins = Math.round(minutes % 60)
  return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
}

const fetchStats = async () => {
  try {
    const res = await getDashboardStats()
    if (res.data) {
      stats.value = res.data
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

onMounted(async () => {
  await nextTick()
  fetchStats()
  initCharts()
  setupResizeObserver()
})

onBeforeUnmount(() => {
  if (chart1) {
    chart1.dispose()
    chart1 = null
  }
  if (chart2) {
    chart2.dispose()
    chart2 = null
  }
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})

watch(() => store.scenario, () => {
  updateCharts()
})

const initCharts = () => {
  if (chartRef1.value) {
    chart1 = echarts.init(chartRef1.value)
    chart1.setOption({
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
        axisLine: { lineStyle: { color: '#e0e0e6' } },
        axisLabel: { color: '#666', fontSize: 13 }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } },
        axisLabel: { color: '#666', fontSize: 13 }
      },
      series: [{
        data: [120, 200, 150, 80, 70, 110, 130],
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(24, 160, 88, 0.3)' },
            { offset: 1, color: 'rgba(24, 160, 88, 0.05)' }
          ])
        },
        lineStyle: { color: '#18a058', width: 3 },
        itemStyle: { color: '#18a058' }
      }],
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e0e0e6',
        borderWidth: 1,
        textStyle: { color: '#333', fontSize: 14 },
        padding: [10, 14],
        extraCssText: 'border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.12);'
      }
    })
    chartReady1.value = true
  }

  if (chartRef2.value) {
    chart2 = echarts.init(chartRef2.value)
    chart2.setOption({
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e0e0e6',
        borderWidth: 1,
        textStyle: { color: '#333', fontSize: 14 },
        padding: [10, 14],
        extraCssText: 'border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.12);',
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        bottom: '5%',
        left: 'center',
        itemGap: 20,
        textStyle: { color: '#666', fontSize: 14 }
      },
      series: [{
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 3
        },
        label: {
          show: true,
          formatter: '{b}\n{d}%',
          fontSize: 14,
          color: '#666',
          fontWeight: 500
        },
        emphasis: {
          label: { show: true, fontSize: 16, fontWeight: 'bold' },
          itemStyle: { 
            shadowBlur: 12, 
            shadowOffsetX: 0, 
            shadowColor: 'rgba(0, 0, 0, 0.3)' 
          }
        },
        data: [
          { value: store.autoDecision.pass, name: '自动通过', itemStyle: { color: '#18a058' } },
          { value: store.autoDecision.manual, name: '转人工', itemStyle: { color: '#f0a020' } },
          { value: store.autoDecision.reject, name: '自动驳回', itemStyle: { color: '#d03050' } }
        ]
      }]
    })
    chartReady2.value = true
  }
}

const updateCharts = () => {
  if (chart2) {
    chart2.setOption({
      series: [{
        data: [
          { value: store.autoDecision.pass, name: '自动通过', itemStyle: { color: '#18a058' } },
          { value: store.autoDecision.manual, name: '转人工', itemStyle: { color: '#f0a020' } },
          { value: store.autoDecision.reject, name: '自动驳回', itemStyle: { color: '#d03050' } }
        ]
      }]
    })
  }
}

const setupResizeObserver = () => {
  if (!chartRef1.value && !chartRef2.value) return

  resizeObserver = new ResizeObserver(() => {
    chart1?.resize()
    chart2?.resize()
  })

  if (chartRef1.value) resizeObserver.observe(chartRef1.value)
  if (chartRef2.value) resizeObserver.observe(chartRef2.value)
}
</script>

<style scoped>
.data-dashboard {
  width: 100%;
}

/* 统计卡片 Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

/* 统计卡片 */
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  transition: all 260ms cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover {
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.12);
  transform: translateY(-4px);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  flex-shrink: 0;
}

.stat-icon.pending {
  background: linear-gradient(135deg, #e8f4ff 0%, #d6e9ff 100%);
  color: #2080f0;
}

.stat-icon.processed {
  background: linear-gradient(135deg, #e8faf0 0%, #d0f0e0 100%);
  color: #18a058;
}

.stat-icon.time {
  background: linear-gradient(135deg, #fff7e6 0%, #ffefd5 100%);
  color: #f0a020;
}

.stat-icon.rate {
  background: linear-gradient(135deg, #f0e6ff 0%, #e0d0ff 100%);
  color: #7c4dff;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

/* Grid 布局 */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

@media (min-width: 768px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 图表卡片 */
.chart-card {
  border-radius: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  transition: all 260ms cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.chart-card:hover {
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.12);
  transform: translateY(-4px);
}

/* 卡片头部 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.card-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
}

/* 卡片内容 */
.card-content {
  padding: 16px 24px 24px;
}

/* 图表容器 */
.chart-wrapper {
  position: relative;
  width: 100%;
  height: 340px;
  min-height: 340px;
}

.chart-container {
  width: 100%;
  height: 100%;
}

.chart-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #999;
  font-size: 14px;
}

/* 响应式 */
@media (max-width: 768px) {
  .stats-grid {
    gap: 12px;
  }

  .stat-card {
    padding: 16px 20px;
  }

  .stat-value {
    font-size: 24px;
  }

  .dashboard-grid {
    gap: 16px;
  }

  .chart-card {
    border-radius: 12px;
  }

  .card-header {
    padding: 16px 20px;
  }

  .card-title {
    font-size: 16px;
  }

  .card-content {
    padding: 12px 20px 20px;
  }

  .chart-wrapper {
    height: 300px;
    min-height: 300px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .stat-card,
  .chart-card {
    transition: none;
  }
  .stat-card:hover,
  .chart-card:hover {
    transform: none;
  }
}
</style>
