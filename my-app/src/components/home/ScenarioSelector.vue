<!-- src/components/home/ScenarioSelector.vue -->
<template>
  <div class="scenario-selector">
    <div class="scenarios-grid">
      <div
        v-for="(config, key) in scenarios"
        :key="key"
        :class="['scenario-card', { 'scenario-active': store.scenario === key }]"
        @click="handleSelect(key as Scenario)"
      >
        <div class="card-content">
          <div class="scenario-icon-wrapper">
            <span class="scenario-icon" :style="{ color: config.color }">
              {{ config.icon }}
            </span>
          </div>
          <div class="scenario-info">
            <h3 class="scenario-title">{{ config.name }}</h3>
            <p class="scenario-desc">{{ config.description }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useHomeInteractive, type Scenario } from '@/stores/homeInteractive'

const store = useHomeInteractive()

// 修复：每个场景都有固定的配置，不再依赖 store.scenarioConfig
const scenarios = computed(() => ({
  leave: { 
    name: '请假审批', 
    icon: '🏖️', 
    color: '#18a058', 
    description: '智能审批流转' 
  },
  reimburse: { 
    name: '经费报销', 
    icon: '💰', 
    color: '#f0a020', 
    description: '按金额自动路由' 
  },
  room: { 
    name: '教室预约', 
    icon: '🏫', 
    color: '#2080f0', 
    description: '实时冲突检测' 
  },
  award: { 
    name: '活动评奖', 
    icon: '🏆', 
    color: '#d03050', 
    description: '在线评审汇总' 
  },
  certificate: { 
    name: '证明开具', 
    icon: '📜', 
    color: '#7c4dff', 
    description: '电子签章验真' 
  }
}))

const handleSelect = (key: Scenario) => {
  store.changeScenario(key)
}
</script>

<style scoped>
/* 样式保持不变 */
.scenario-selector {
  width: 100%;
}

.scenarios-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

@media (min-width: 640px) {
  .scenarios-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 768px) {
  .scenarios-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}

.scenario-card {
  position: relative;
  min-height: 160px;
  border-radius: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%);
  border: 2px solid transparent;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  transition: all 260ms cubic-bezier(0.4, 0, 0.2, 1);
}

.scenario-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
}

.scenario-active {
  border-color: #18a058;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  box-shadow: 0 8px 24px rgba(24, 160, 88, 0.2);
  transform: scale(1.02);
}

.scenario-active:hover {
  transform: translateY(-6px) scale(1.02);
}

.card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 24px 16px;
  text-align: center;
  min-height: 160px;
}

.scenario-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: all 260ms cubic-bezier(0.4, 0, 0.2, 1);
}

.scenario-card:hover .scenario-icon-wrapper {
  transform: scale(1.15) rotate(-5deg);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
}

.scenario-active .scenario-icon-wrapper {
  background: rgba(255, 255, 255, 1);
  box-shadow: 0 6px 20px rgba(24, 160, 88, 0.15);
}

.scenario-icon {
  font-size: 48px;
  line-height: 1;
  user-select: none;
  display: block;
}

.scenario-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.scenario-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
}

.scenario-desc {
  margin: 0;
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .scenarios-grid {
    gap: 12px;
  }

  .scenario-card {
    min-height: 140px;
    border-radius: 12px;
  }

  .card-content {
    padding: 20px 12px;
    gap: 12px;
    min-height: 140px;
  }

  .scenario-icon-wrapper {
    width: 64px;
    height: 64px;
    border-radius: 16px;
  }

  .scenario-icon {
    font-size: 40px;
  }

  .scenario-title {
    font-size: 16px;
  }

  .scenario-desc {
    font-size: 12px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .scenario-card,
  .scenario-icon-wrapper {
    transition: none;
  }

  .scenario-card:hover,
  .scenario-active {
    transform: none;
  }

  .scenario-card:hover .scenario-icon-wrapper {
    transform: none;
  }
}
</style>