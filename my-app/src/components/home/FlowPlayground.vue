<!-- src/components/home/FlowPlayground.vue - 仅显示修改的部分 -->
<template>
  <div class="flow-playground">
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
          <span class="pill-desc">{{ item.description }}</span>
        </button>
      </div>
    </div>

    <div class="playground-grid">
      <!-- 左侧控制区 -->
      <div class="control-card">
        <div class="card-header">
          <h3 class="card-title">条件控制</h3>
          <div class="help-tip">
            <n-popover trigger="hover" placement="bottom">
              <template #trigger>
                <span class="help-icon">?</span>
              </template>
              <div style="max-width: 200px;">
                拖动滑块或勾选选项，实时查看流程路径和审批预测的变化
              </div>
            </n-popover>
          </div>
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
                <div class="control-description">
                  拖动滑块调整天数，超过 3 天需要主管审批
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
                <span class="checkbox-label">📋 附病假证明（可加快审批）</span>
              </n-checkbox>
            </div>

            <!-- 报销场景 -->
            <div v-if="store.scenario === 'reimburse'" class="scenario-controls">
              <div class="control-item">
                <div class="control-header">
                  <span class="control-label">💵 报销金额</span>
                  <span class="control-value-badge control-value-success">¥{{ controls.reimburse.amount }}</span>
                </div>
                <div class="control-description">
                  拖动调整金额，超过 ¥500 需要财务审核
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
                  <span class="checkbox-label">🧾 需要发票</span>
                </n-checkbox>
                <n-checkbox 
                  v-model:checked="controls.reimburse.docsComplete" 
                  size="large"
                  class="control-checkbox"
                  @update:checked="(val) => handleControlChange('docsComplete', val)"
                >
                  <span class="checkbox-label">📎 材料完整（影响自动审批）</span>
                </n-checkbox>
              </div>
            </div>

            <!-- 分隔线 -->
            <div class="divider"></div>
            
            <!-- 预计处理时长 -->
            <div class="eta-display">
              <div class="eta-icon">⏱️</div>
              <n-statistic label="预计处理时长" tabular-nums>
                <n-number-animation 
                  :from="0" 
                  :to="store.etaMinutes" 
                  :duration="300"
                  :precision="0"
                />
                <template #suffix>
                  <span class="eta-suffix">分钟</span>
                </template>
              </n-statistic>
              <div class="eta-description">
                根据当前条件预测的平均处理时间
              </div>
            </div>

            <!-- 自动审批决策 -->
            <div class="auto-decision">
              <div class="decision-header">
                <h4 class="decision-title">🤖 AI 自动审批预测</h4>
                <n-popover trigger="hover" placement="top">
                  <template #trigger>
                    <span class="help-icon-small">?</span>
                  </template>
                  <div style="max-width: 250px;">
                    <p style="margin: 0 0 8px 0; font-weight: 600;">预测说明：</p>
                    <ul style="margin: 0; padding-left: 20px; font-size: 13px;">
                      <li>绿色：AI 判断可自动通过</li>
                      <li>黄色：需要人工审核</li>
                      <li>红色：不符合条件，自动驳回</li>
                    </ul>
                  </div>
                </n-popover>
              </div>
              
              <div class="decision-bar">
                <div 
                  class="bar-segment bar-pass" 
                  :style="{ width: store.autoDecision.pass + '%' }"
                  :title="`自动通过概率：${store.autoDecision.pass}%`"
                >
                  <span v-if="store.autoDecision.pass > 12" class="bar-label">
                    {{ store.autoDecision.pass }}%
                  </span>
                </div>
                <div 
                  class="bar-segment bar-manual" 
                  :style="{ width: store.autoDecision.manual + '%' }"
                  :title="`转人工概率：${store.autoDecision.manual}%`"
                >
                  <span v-if="store.autoDecision.manual > 12" class="bar-label">
                    {{ store.autoDecision.manual }}%
                  </span>
                </div>
                <div 
                  class="bar-segment bar-reject" 
                  :style="{ width: store.autoDecision.reject + '%' }"
                  :title="`自动驳回概率：${store.autoDecision.reject}%`"
                >
                  <span v-if="store.autoDecision.reject > 12" class="bar-label">
                    {{ store.autoDecision.reject }}%
                  </span>
                </div>
              </div>
              
              <div class="decision-legend">
                <div class="legend-item">
                  <n-tag type="success" size="small" :bordered="false">自动通过</n-tag>
                  <span class="legend-desc">符合条件</span>
                </div>
                <div class="legend-item">
                  <n-tag type="warning" size="small" :bordered="false">转人工</n-tag>
                  <span class="legend-desc">需审核</span>
                </div>
                <div class="legend-item">
                  <n-tag type="error" size="small" :bordered="false">自动驳回</n-tag>
                  <span class="legend-desc">不符合</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧视觉区域 -->
      <div class="visual-column">
        <div class="flow-card">
          <div class="card-header">
            <h3 class="card-title">流程路径（实时）</h3>
            <n-tag type="info" size="small" :bordered="false">
              {{ scenarioName }}
            </n-tag>
          </div>
          <div class="card-content flow-visual">
            <FlowCanvas :nodes="store.flowData.nodes" :edges="store.flowData.edges" />
          </div>
        </div>

        <div class="insight-card">
          <div class="insight-head">
            <div>
              <p class="insight-label">节点概览</p>
              <h4>审批阶段节奏</h4>
            </div>
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
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useHomeInteractive } from '@/stores/homeInteractive'
import type { Scenario } from '@/stores/homeInteractive'
import FlowCanvas from './FlowCanvas.vue'

const store = useHomeInteractive()
const controls = computed(() => store.controls)
const activeScenario = computed(() => store.scenario)

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
</script>

<style scoped>
.flow-playground {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: clamp(20px, 2vw, 28px);
  border-radius: 32px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(245, 247, 255, 0.8));
  border: 1px solid rgba(12, 16, 32, 0.08);
  box-shadow: 0 28px 70px rgba(8, 12, 32, 0.08);
}

.playground-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

@media (min-width: 1024px) {
  .playground-grid {
    grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
    align-items: stretch;
  }
}

.visual-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.flow-visual {
  min-height: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.insight-card {
  border-radius: 24px;
  border: 1px solid rgba(12, 16, 32, 0.08);
  background: #fff;
  box-shadow: 0 18px 45px rgba(8, 12, 32, 0.08);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.insight-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.insight-label {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #8a8f9f;
}

.insight-head h4 {
  margin: 6px 0 0;
  font-size: 18px;
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
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(12, 16, 32, 0.08);
}

.stage-item:last-child {
  border-bottom: none;
}

.stage-index {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(15, 18, 23, 0.05);
  font-weight: 600;
  color: #0b0d12;
  display: inline-flex;
  align-items: center;
  justify-content: center;
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
  color: #1d2130;
}

.stage-desc {
  font-size: 12px;
  color: #7a8194;
}

.stage-empty {
  text-align: center;
  color: #7a8194;
  font-size: 13px;
  padding: 24px 0;
}

@media (max-width: 768px) {
  .flow-playground {
    border-radius: 24px;
    padding: 20px;
  }

  .card-content {
    padding: 20px;
  }

  .decision-bar {
    height: 48px;
  }

  .decision-legend {
    flex-direction: column;
  }
}

@media (prefers-reduced-motion: reduce) {
  .scenario-pill,
  .control-card,
  .flow-card,
  .control-checkbox,
  .bar-segment {
    transition: none;
  }

  .control-card:hover,
  .flow-card:hover,
  .scenario-pill:hover,
  .bar-segment:hover {
    transform: none;
  }
}
</style>