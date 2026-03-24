<!-- src/components/home/QuickActions.vue -->
<template>
  <div class="quick-actions">
    <div class="actions-grid">
      <button
        v-for="item in actions"
        :key="item.title"
        type="button"
        class="action-card"
        @click="router.push(item.route)"
      >
        <n-badge
          v-if="item.badge"
          class="card-badge"
          :value="item.badge.value"
          :max="item.badge.max"
          :type="item.badge.type"
        />
        <div class="action-content">
          <div class="icon-wrapper" :style="{ '--icon-color': item.color || '#ff7a18' }">
            <component :is="item.icon" class="icon" aria-hidden="true" />
          </div>
          <div class="action-text">
            <div class="action-meta">
              <span class="kicker">{{ item.kicker }}</span>
              <span class="route">{{ item.routeLabel }}</span>
            </div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { AddCircleOutline, AlbumsOutline, FileTrayFullOutline, ShieldCheckmarkOutline } from '@vicons/ionicons5'

const router = useRouter()

const actions = computed(() => [
  {
    title: '创建表单',
    description: '3 分钟上线，高校字段模板随取随用',
    kicker: 'Builder',
    routeLabel: '/form/designer',
    route: '/form/designer',
    color: '#8b5cff',
    icon: AddCircleOutline
  },
  {
    title: '我的表单',
    description: '版本快照、发布审批、协作编辑',
    kicker: 'Library',
    routeLabel: '/form/list',
    route: '/form/list',
    color: '#31d6ff',
    icon: AlbumsOutline
  },
  {
    title: '提交记录',
    description: '实时筛选 + 导出，草稿可追溯',
    kicker: 'Submissions',
    routeLabel: '/submissions',
    route: '/submissions',
    color: '#ffd166',
    icon: FileTrayFullOutline
  },
  {
    title: '待审批',
    description: 'AI 预判风险，优先提醒关键节点',
    kicker: 'Approvals',
    routeLabel: '/approvals',
    route: '/approvals',
    color: '#52e5b6',
    icon: ShieldCheckmarkOutline,
    badge: { value: 5, max: 99, type: 'error' as const }
  }
])
</script>

<style scoped>
.quick-actions {
  width: 100%;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
}

.action-card {
  position: relative;
  min-height: 220px;
  padding: 0;
  border: none;
  background: #fff;
  border-radius: 20px;
  cursor: pointer;
  color: inherit;
  text-align: left;
  box-shadow: 0 20px 50px rgba(15, 15, 18, 0.08);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.action-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 30px 70px rgba(15, 15, 18, 0.12);
}

.card-badge {
  position: absolute;
  top: 16px;
  right: 18px;
  z-index: 2;
}

.action-content {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 28px;
  height: 100%;
}

.icon-wrapper {
  width: 62px;
  height: 62px;
  border-radius: 999px;
  background: var(--brand-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--icon-color, var(--accent));
  transition: transform 0.2s ease;
}

.action-card:hover .icon-wrapper {
  transform: translateY(-4px);
}

.icon {
  width: 30px;
  height: 30px;
  color: var(--icon-color, #0b0d12);
}

.action-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--text-3);
}

.kicker {
  text-transform: uppercase;
  letter-spacing: 0.18em;
}

.route {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  color: var(--accent);
}

.action-text h3 {
  margin: 6px 0 4px;
  font-size: 20px;
  color: #0f0f12;
}

.action-text p {
  margin: 0;
  color: #4d5568;
  font-size: 14px;
  line-height: 1.5;
}

@media (max-width: 640px) {
  .action-card {
    min-height: 180px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .action-card,
  .icon-wrapper {
    transition: none;
  }

  .action-card:hover {
    transform: none;
  }
}
</style>