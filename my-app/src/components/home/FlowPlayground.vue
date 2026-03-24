<!-- src/components/home/FlowPlayground.vue - 全屏控制台模式 -->
<template>
  <div class="flow-playground command-center">
    <!-- 1. 顶部全局区：场景切换 -->
    <div class="header-global">
      <div class="scenario-tabs" role="tablist" aria-label="审批场景切换">
        <span class="tabs-label">场景</span>
        <div class="tabs-list">
          <button
            v-for="item in scenarioOptions"
            :key="item.value"
            type="button"
            class="scenario-pill"
            :class="{ active: activeScenario === item.value }"
            role="tab"
            :aria-selected="activeScenario === item.value"
            @click="handleScenarioSwitch(item.value)"
          >
            <span class="pill-label">{{ item.label }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 主工作区：左右两栏布局 -->
    <div class="playground-workspace">
      <!-- 2. 左侧控制栏 (固定宽度 400px) -->
      <aside class="left-panel">
        <!-- 卡片 A：条件控制 -->
        <div class="control-card">
          <div class="card-header">
            <h3 class="card-title">条件控制</h3>
          </div>
          <div class="card-content">
            <div class="controls-wrapper">
              <!-- 请假场景 -->
              <div v-if="store.scenario === 'leave'" class="scenario-controls">
                <div class="control-item">
                  <div class="control-header">
                    <span class="control-label">📅 请假天数</span>
                    <span class="control-value-badge">{{ controls.leave.days }} 天</span>
                  </div>
                  <n-slider
                    v-model:value="controls.leave.days"
                    :min="1"
                    :max="15"
                    :marks="{ 3: '需主管', 7: '需总监' }"
                    @update:value="(val) => handleControlChange('days', val)"
                  />
                </div>
                <n-checkbox
                  v-model:checked="controls.leave.medicalProof"
                  size="large"
                  class="control-checkbox"
                  @update:checked="(val) => handleControlChange('medicalProof', val)"
                >
                  <span class="checkbox-label">附病假证明（可加快审批）</span>
                </n-checkbox>
              </div>

              <!-- 报销场景 -->
              <div v-if="store.scenario === 'reimburse'" class="scenario-controls">
                <div class="control-item">
                  <div class="control-header">
                    <span class="control-label">💵 报销金额</span>
                    <span class="control-value-badge control-value-success">¥{{ controls.reimburse.amount }}</span>
                  </div>
                  <n-slider
                    v-model:value="controls.reimburse.amount"
                    :min="0"
                    :max="10000"
                    :step="100"
                    :marks="{ 500: '需财务', 5000: '需领导' }"
                    @update:value="(val) => handleControlChange('amount', val)"
                  />
                </div>
                <div class="checkbox-group">
                  <n-checkbox
                    v-model:checked="controls.reimburse.needInvoice"
                    size="large"
                    class="control-checkbox"
                    @update:checked="(val) => handleControlChange('needInvoice', val)"
                  >
                    <span class="checkbox-label">需要发票</span>
                  </n-checkbox>
                  <n-checkbox
                    v-model:checked="controls.reimburse.docsComplete"
                    size="large"
                    class="control-checkbox"
                    @update:checked="(val) => handleControlChange('docsComplete', val)"
                  >
                    <span class="checkbox-label">材料完整（影响自动审批）</span>
                  </n-checkbox>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 卡片 B：实时指标与 AI 预测（合并） -->
        <div class="metrics-card">
          <div class="metrics-header">
            <span class="metrics-label">实时指标与 AI 预测</span>
            <span class="metrics-badge">Live</span>
          </div>
          
          <!-- 预计处理时长 - 大字强调 -->
          <div class="eta-display">
            <span class="eta-label">预计处理时长</span>
            <div class="eta-value">
              <n-number-animation
                :from="0"
                :to="store.etaMinutes"
                :duration="300"
                :precision="0"
              />
              <span class="eta-unit">分钟</span>
            </div>
          </div>

          <!-- 进度条 -->
          <div class="metrics-progress">
            <div class="progress-item">
              <div class="progress-header">
                <span>自动通过</span>
                <strong>{{ store.autoDecision.pass }}%</strong>
              </div>
              <div class="progress-line pass" :style="{ '--value': store.autoDecision.pass + '%' }"></div>
            </div>
            <div class="progress-item">
              <div class="progress-header">
                <span>人工复核</span>
                <strong>{{ store.autoDecision.manual }}%</strong>
              </div>
              <div class="progress-line warn" :style="{ '--value': store.autoDecision.manual + '%' }"></div>
            </div>
            <div class="progress-item">
              <div class="progress-header">
                <span>驳回率</span>
                <strong>{{ store.autoDecision.reject }}%</strong>
              </div>
              <div class="progress-line danger" :style="{ '--value': store.autoDecision.reject + '%' }"></div>
            </div>
          </div>
        </div>
      </aside>

      <!-- 3. 右侧展示区 (flex: 1) -->
      <main class="right-panel">
        <!-- 流程图区域 - 居中，四周留白 -->
        <div class="flow-visual">
          <FlowCanvas :nodes="store.flowData.nodes" :edges="store.flowData.edges" />
        </div>

        <!-- 审批阶段节奏 - 放在流程图下方横向展开 -->
        <div class="stage-timeline">
          <div class="timeline-header">
            <h4>审批阶段节奏</h4>
            <n-tag size="small" :bordered="false" type="success">{{ stageTimeline.length }} 步</n-tag>
          </div>
          <ul class="stage-list">
            <li v-for="stage in stageTimeline" :key="stage.id" class="stage-item">
              <span class="stage-index">{{ stage.index }}</span>
              <div class="stage-body">
                <p class="stage-name">{{ stage.name }}</p>
                <span class="stage-desc">{{ stage.description }}</span>
              </div>
              <n-tag size="small" :bordered="false" :type="stage.tagType">{{ stage.typeLabel }}</n-tag>
            </li>
            <li v-if="!stageTimeline.length" class="stage-empty">暂无流程节点，调整控件以生成路线</li>
          </ul>
        </div>
      </main>
    </div>

    <!-- 4. 底部悬浮区：CLI 命令 -->
    <div class="cli-float">
      <div class="cli-shell">
        <div class="cli-header">
          <div class="cli-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="4 17 10 11 4 5"></polyline>
              <line x1="12" y1="19" x2="20" y2="19"></line>
            </svg>
            <span>CLI 同步命令</span>
          </div>
          <button type="button" class="cli-copy-btn" @click="copyCommand">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            <span>复制</span>
          </button>
        </div>
        <pre><code>{{ commandSnippet }}</code></pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMessage } from 'naive-ui'
import { useHomeInteractive } from '@/stores/homeInteractive'
import type { Scenario } from '@/stores/homeInteractive'
import FlowCanvas from './FlowCanvas.vue'

const store = useHomeInteractive()
const controls = computed(() => store.controls)
const activeScenario = computed(() => store.scenario)
const message = useMessage()

const commandSnippet = 'npx formflow sync --tenant campus'

const handleControlChange = (key: string, value: unknown) => {
  store.updateControl(key, value)
}

const scenarioOptions: Array<{ label: string; value: Scenario; description: string }> = [
  { label: '请假审批', value: 'leave', description: '≤3 天自动通过' },
  { label: '经费报销', value: 'reimburse', description: '金额驱动路由' },
  { label: '教室预约', value: 'room', description: '智能冲突检测' },
  { label: '活动评奖', value: 'award', description: '多评委合议' },
  { label: '证明开具', value: 'certificate', description: '电子签章' }
]

const handleScenarioSwitch = (value: Scenario) => {
  if (value === store.scenario) return
  store.changeScenario(value)
}

const scenarioName = computed(() => {
  return scenarioOptions.find((item) => item.value === store.scenario)?.label || '未知场景'
})

const stageTimeline = computed(() => {
  if (!store.flowData.nodes?.length) return []

  const typeMeta: Record<string, { label: string; desc: string; tagType: 'success' | 'info' | 'warning' | 'error' }> = {
    start: { label: '开始', desc: '发起节点', tagType: 'success' },
    user: { label: '人工节点', desc: '人工审核/处理', tagType: 'warning' },
    auto: { label: '自动节点', desc: '系统自动处理', tagType: 'info' },
    end: { label: '结束', desc: '归档或完成', tagType: 'success' }
  }

  return store.flowData.nodes.map((node, index) => {
    const meta = typeMeta[node.type] || { label: '节点', desc: '流程节点', tagType: 'info' }
    return {
      id: node.id,
      index: index + 1,
      name: node.name,
      typeLabel: meta.label,
      description: meta.desc,
      tagType: meta.tagType
    }
  })
})

const copyCommand = async () => {
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(commandSnippet)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = commandSnippet
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.focus()
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    message.success('命令已复制')
  } catch (error) {
    console.warn('Copy failed', error)
    message.error('复制失败，请手动复制')
  }
}
</script>

<style scoped>
/* 全局容器 - 全屏控制台模式 */
.flow-playground {
  width: 100vw;
  margin-left: calc(50% - 50vw);
  display: flex;
  flex-direction: column;
  gap: 0;
  background: #F7F8FA;
  padding: 0;
}

/* 1. 顶部全局区：场景切换 */
.header-global {
  width: 100%;
  padding: 24px 40px;
  background: #fff;
  border-bottom: 1px solid rgba(12, 16, 32, 0.06);
}

.scenario-tabs {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 1600px;
  margin: 0 auto;
}

.tabs-label {
  font-size: 11px;
  font-weight: 600;
  color: #86909c;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}

.tabs-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.scenario-pill {
  position: relative;
  padding: 10px 24px;
  border-radius: 999px;
  background: #F2F3F5;
  color: #4E5969;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.scenario-pill:hover {
  background: #E5E6EB;
  transform: translateY(-2px);
}

.scenario-pill.active {
  background: linear-gradient(135deg, #4085F5 0%, #3A8FD5 100%);
  color: #fff;
  box-shadow: 0 4px 16px rgba(64, 133, 245, 0.35);
}

.scenario-pill.active:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(64, 133, 245, 0.45);
}

/* 主工作区：左右两栏布局 */
.playground-workspace {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 0;
  min-height: calc(100vh - 200px);
  max-width: 1800px;
  margin: 0 auto;
  width: 100%;
  padding: 32px 40px;
}

/* 2. 左侧控制栏 */
.left-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-right: 32px;
  border-right: 1px solid rgba(12, 16, 32, 0.06);
}

/* 条件控制卡片 */
.control-card {
  border-radius: 18px;
  border: 1px solid rgba(12, 16, 32, 0.06);
  background: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  padding: 28px;
  flex-shrink: 0;
  transition: box-shadow 0.3s ease;
}

.control-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.card-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  letter-spacing: -0.01em;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.controls-wrapper {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 控制项样式 */
.scenario-controls {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  border-radius: 12px;
  background: rgba(15, 18, 23, 0.02);
  transition: all 0.2s ease;
}

.control-item:hover {
  background: rgba(15, 18, 23, 0.04);
}

.control-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.control-label {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
}

.control-value-badge {
  font-size: 14px;
  font-weight: 700;
  color: #4085F5;
  padding: 4px 12px;
  border-radius: 8px;
  background: rgba(64, 133, 245, 0.1);
  transition: all 0.2s ease;
}

.control-value-badge:hover {
  background: rgba(64, 133, 245, 0.15);
}

.control-value-badge.control-value-success {
  color: #18A058;
  background: rgba(24, 160, 88, 0.1);
}

.control-value-badge.control-value-success:hover {
  background: rgba(24, 160, 88, 0.15);
}

.control-checkbox {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 14px;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.control-checkbox:hover {
  background: rgba(15, 18, 23, 0.02);
}

.checkbox-label {
  font-size: 13px;
  color: #1d2129;
  font-weight: 500;
  line-height: 1.5;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 实时指标卡片 */
.metrics-card {
  border-radius: 18px;
  border: 1px solid rgba(12, 16, 32, 0.06);
  background: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  padding: 28px;
  flex-shrink: 0;
  transition: box-shadow 0.3s ease;
}

.metrics-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

.metrics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.metrics-label {
  font-size: 11px;
  font-weight: 500;
  color: #86909c;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}

.metrics-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #22c55e;
}

.metrics-badge::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22c55e;
  animation: pulse-dot 2s ease-in-out infinite;
}

/* 预计处理时长 - 大字强调 */
.eta-display {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 24px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(64, 133, 245, 0.08) 0%, rgba(64, 133, 245, 0.03) 100%);
  margin-bottom: 24px;
}

.eta-label {
  font-size: 13px;
  font-weight: 500;
  color: #86909c;
}

.eta-value {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.eta-value :deep(.n-number-animation) {
  font-size: 48px;
  font-weight: 700;
  color: #4085F5;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}

.eta-unit {
  font-size: 18px;
  font-weight: 500;
  color: #86909c;
}

/* 进度条 */
.metrics-progress {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.progress-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-header span {
  font-size: 14px;
  font-weight: 500;
  color: #4E5969;
}

.progress-header strong {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  font-variant-numeric: tabular-nums;
}

.progress-line {
  height: 10px;
  border-radius: 999px;
  background: rgba(11, 13, 18, 0.06);
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.1);
}

.progress-line::after {
  content: '';
  position: absolute;
  inset: 0;
  width: var(--value, 0%);
  border-radius: 999px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-line.pass::after {
  background: linear-gradient(90deg, #18A058 0%, #3AC885 100%);
  box-shadow: 0 2px 8px rgba(24, 160, 88, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.progress-line.warn::after {
  background: linear-gradient(90deg, #F0B90B 0%, #F5C358 100%);
  box-shadow: 0 2px 8px rgba(240, 185, 11, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.progress-line.danger::after {
  background: linear-gradient(90deg, #F53F3F 0%, #F7786E 100%);
  box-shadow: 0 2px 8px rgba(245, 63, 63, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

/* 3. 右侧展示区 */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-left: 32px;
}

/* 流程图区域 - 居中，四周留白 */
.flow-visual {
  flex: 1;
  min-height: 500px;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(12, 16, 32, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px;
  position: relative;
}

/* 审批阶段节奏 - 横向展开 */
.stage-timeline {
  border-radius: 14px;
  border: 1px solid rgba(12, 16, 32, 0.06);
  background: #fff;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  padding: 24px;
  flex-shrink: 0;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.timeline-header h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
  letter-spacing: -0.01em;
}

.stage-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stage-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(12, 16, 32, 0.06);
  transition: all 0.2s ease;
}

.stage-item:hover {
  padding-left: 8px;
}

.stage-item:last-child {
  border-bottom: none;
}

.stage-index {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: rgba(15, 18, 23, 0.06);
  font-size: 13px;
  font-weight: 600;
  color: #1d2129;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stage-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stage-name {
  margin: 0;
  font-weight: 600;
  color: #1d2129;
  font-size: 14px;
}

.stage-desc {
  font-size: 12px;
  color: #86909c;
}

.stage-empty {
  text-align: center;
  color: #86909c;
  font-size: 13px;
  padding: 24px 0;
  font-weight: 400;
}

/* 4. 底部悬浮区：CLI 命令 */
.cli-float {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 100;
}

.cli-shell {
  background: #1E1E1E;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  backdrop-filter: blur(12px);
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
  transition: all 0.3s ease;
  max-width: 420px;
}

.cli-shell:hover {
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.45);
  transform: translateY(-2px);
}

.cli-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.cli-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
}

.cli-label svg {
  opacity: 0.6;
}

.cli-copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  padding: 6px 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 12px;
  font-weight: 500;
}

.cli-copy-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  color: #fff;
}

.cli-copy-btn:hover svg {
  opacity: 0.9;
}

.cli-shell pre {
  font-size: 14px;
  padding: 18px;
  margin: 0;
  background: transparent;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.9);
}

/* 动画 */
@keyframes pulse-dot {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.3);
  }
}

/* 响应式适配 */
@media (max-width: 1400px) {
  .playground-workspace {
    max-width: 100%;
    padding: 24px 32px;
  }
}

@media (max-width: 1200px) {
  .playground-workspace {
    grid-template-columns: 360px 1fr;
  }
}

@media (max-width: 1024px) {
  .playground-workspace {
    grid-template-columns: 1fr;
    padding: 20px 24px;
  }

  .left-panel {
    padding-right: 0;
    border-right: none;
    border-bottom: 1px solid rgba(12, 16, 32, 0.06);
    padding-bottom: 24px;
  }

  .right-panel {
    padding-left: 0;
    padding-top: 24px;
  }

  .header-global {
    padding: 16px 24px;
  }
}

@media (max-width: 768px) {
  .flow-playground {
    width: 100%;
    margin-left: 0;
  }

  .header-global {
    padding: 12px 16px;
  }

  .playground-workspace {
    padding: 16px;
  }

  .scenario-tabs {
    padding: 12px;
  }

  .control-card,
  .metrics-card {
    padding: 20px;
  }

  .eta-value :deep(.n-number-animation) {
    font-size: 36px;
  }

  .flow-visual {
    min-height: 350px;
    padding: 40px;
  }

  .cli-float {
    bottom: 16px;
    right: 16px;
  }

  .cli-shell {
    max-width: 340px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .scenario-pill,
  .control-card,
  .metrics-card,
  .eta-display,
  .cli-shell {
    transition: none;
  }

  .scenario-pill:hover,
  .control-card:hover,
  .metrics-card:hover,
  .eta-display:hover,
  .cli-shell:hover {
    transform: none;
  }
}
</style>