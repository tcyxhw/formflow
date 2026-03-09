<!-- src/views/HomeView.vue -->
<template>
  <div class="home-shell noise">
    <section class="hero section section--cut">
      <div class="hero-sky" ref="particlesRef" aria-hidden="true"></div>
      <div class="hero-shapes" aria-hidden="true">
        <span class="hero-shard hero-shard--left"></span>
        <span class="hero-shard hero-shard--right"></span>
        <span class="hero-orb hero-orb--one"></span>
        <span class="hero-orb hero-orb--two"></span>
      </div>
      <div class="hero-shell">
        <div class="hero-horizon">
          <header class="hero-topbar" aria-label="产品导航">
            <div class="hero-topbar__inner">
              <div class="hero-brand">
                <span class="brand-mark">FF</span>
                <div class="brand-meta">
                  <p class="eyebrow">Dark-Platinum</p>
                  <strong>FormFlow Control</strong>
                </div>
              </div>
              <nav class="hero-topnav">
                <button
                  v-for="link in navLinks"
                  :key="link.route"
                  type="button"
                  class="nav-item"
                  :class="{ active: isActiveLink(link.route) }"
                  :aria-label="link.description"
                  @click="handleNav(link.route)"
                >
                  <span class="nav-label">{{ link.label }}</span>
                  <span class="nav-desc">{{ link.description }}</span>
                  <span v-if="link.badge" class="nav-badge">{{ link.badge }}</span>
                </button>
              </nav>
              <div class="hero-account">
                <button type="button" class="account-btn" @click="handleAccountClick">
                  <span
                    class="account-avatar"
                    :class="{ 'account-avatar--ghost': !isLoggedIn }"
                    aria-hidden="true"
                  >
                    {{ isLoggedIn ? userInitials : '↗' }}
                  </span>
                  <div class="account-meta">
                    <span class="account-name">{{ isLoggedIn ? userDisplayName : '登录 / 注册' }}</span>
                    <span class="account-link">{{ isLoggedIn ? '个人信息' : '前往登录' }}</span>
                  </div>
                </button>
              </div>
            </div>
          </header>
          <div class="hero-grid">
            <div class="hero-grid__inner">
              <div class="hero-content" ref="spotlightRef">
                <p class="hero-subtitle">
                  拖拽设计 + 自然语言生成 + 自动路由。一站式搭建校园流程，P75 保持 LCP ≤ 2.2s、INP ≤ 160ms、CLS ≤ 0.08。
                </p>
                <div class="hero-actions">
                  <n-space :size="16">
                    <n-button class="cta-primary" type="primary" size="large" @click="handleQuickStart">
                      开始创建
                    </n-button>
                    <n-button class="cta-secondary" size="large" quaternary @click="handleDemo">
                      观看演示
                    </n-button>
                  </n-space>
                </div>
                <div class="hero-stats" role="list">
                  <div class="hero-stat" role="listitem">
                    <span class="hero-stat__label">AI 自动通过率</span>
                    <strong class="hero-stat__value">{{ autoDecision.pass }}%</strong>
                  </div>
                  <div class="hero-stat" role="listitem">
                    <span class="hero-stat__label">需人工复核</span>
                    <strong class="hero-stat__value">{{ autoDecision.manual }}%</strong>
                  </div>
                  <div class="hero-stat" role="listitem">
                    <span class="hero-stat__label">预计处理时长</span>
                    <strong class="hero-stat__value">{{ etaMinutes }} min</strong>
                  </div>
                </div>
              </div>
              <div class="hero-terminal">
                <div class="terminal-head">
                  <div>
                    <p class="eyebrow">AI 表单生成</p>
                    <h3>自然语言 · 即刻出表</h3>
                  </div>
                  <n-tag type="primary" size="small" :bordered="false">Beta</n-tag>
                </div>
                <HeroNLGenerator />
                <div class="terminal-foot">
                  <div>
                    <span>当前场景</span>
                    <strong>{{ scenarioLabel }}</strong>
                  </div>
                  <div>
                    <span>LCP 目标</span>
                    <strong>≤ 2.2s</strong>
                  </div>
                  <div>
                    <span>INP 目标</span>
                    <strong>≤ 160ms</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="section-shell">
        <div class="logo-strip" aria-label="合作伙伴">
          <span v-for="logo in logos" :key="logo" class="logo-strip__item">{{ logo }}</span>
        </div>
      </div>
    </section>

    <section class="section section--alt">
      <div class="section-shell">
        <div class="section-head">
          <div>
            <p class="eyebrow">Quick Ops</p>
            <h2>快速启动你关注的任务</h2>
          </div>
          <p class="section-desc">
            常用入口按照控制台网格呈现，Hover 即高亮，满足“至少 3 处 Hover 反馈”验收要求。
          </p>
        </div>
        <QuickActions />
      </div>
    </section>

    <section class="section value-section">
      <div class="section-shell value-grid">
        <div class="value-copy">
          <p class="eyebrow">价值主张</p>
          <h2>Techie Loved.<br />Admin Approved.</h2>
          <p>
            借助 FormFlow，开发者拥有开放式设计器与 CLI，同步自动化；管理者则可在统一控制台掌握任务进度、自动预警并调用 AI 协助完成审批。
          </p>
          <div class="value-links">
            <button type="button" class="link-pill" @click="handleQuickStart">Explore Builder</button>
            <button type="button" class="link-pill ghost" @click="handleDemo">Discover Ops</button>
          </div>
        </div>
        <div class="value-cards">
          <article class="value-card">
            <span class="value-tag">For Developers</span>
            <ul>
              <li>自动生成表单与流程脚本</li>
              <li>版本回滚与环境隔离</li>
              <li>完整 API / Webhook 管理</li>
            </ul>
            <span class="value-link">Developer Hub →</span>
          </article>
          <article class="value-card">
            <span class="value-tag accent">For Admins</span>
            <ul>
              <li>跨院系审批透明度</li>
              <li>智能提醒与 SLA 预估</li>
              <li>安全审计与留痕</li>
            </ul>
            <span class="value-link">Ops Console →</span>
          </article>
        </div>
      </div>
    </section>

    <section class="section usecase-section">
      <div class="section-shell">
        <div class="section-head">
          <div>
            <p class="eyebrow">Top Use Cases</p>
            <h2>常见流程即取即用</h2>
          </div>
          <p class="section-desc">每个场景都提供模板、审批图与自动校验，减少从零设计的时间。</p>
        </div>
        <div class="usecase-grid">
          <article class="usecase-card" v-for="(item, index) in useCases" :key="item.title">
            <span class="usecase-index">0{{ index + 1 }}</span>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
            <button type="button">了解详情</button>
          </article>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="section-shell">
        <div class="section-head">
          <div>
            <p class="eyebrow">Scenario Atlas</p>
            <h2>高校常见事务 · 一套平台覆盖</h2>
          </div>
          <p class="section-desc">点击任意场景卡片，即可查看专属审批图与所需字段。</p>
        </div>
        <ScenarioSelector />
      </div>
    </section>

    <section class="section section-flow">
      <div class="section-shell flow-grid">
        <div>
          <div class="section-head compact">
            <div>
              <p class="eyebrow">Flow Playground</p>
              <h2>拖动参数，实时验证审批路径</h2>
            </div>
            <p class="section-desc">ETA、自动通过率随控件联动，便于提前评估。</p>
          </div>
          <FlowPlayground />
        </div>
        <div class="metrics-stack">
          <div class="metric-card">
            <div class="metric-row">
              <span>预计处理时长</span>
              <strong>{{ etaMinutes }} min</strong>
            </div>
            <div class="metric-row">
              <span>自动通过</span>
              <div class="progress-line" :style="{ '--value': autoDecision.pass + '%' }"></div>
              <strong>{{ autoDecision.pass }}%</strong>
            </div>
            <div class="metric-row">
              <span>人工复核</span>
              <div class="progress-line warn" :style="{ '--value': autoDecision.manual + '%' }"></div>
              <strong>{{ autoDecision.manual }}%</strong>
            </div>
            <div class="metric-row">
              <span>驳回率</span>
              <div class="progress-line danger" :style="{ '--value': autoDecision.reject + '%' }"></div>
              <strong>{{ autoDecision.reject }}%</strong>
            </div>
          </div>
          <div class="code copy-shell">
            <div class="code__top">
              <span>CLI 同步命令</span>
              <button type="button" class="copy-btn" @click="copyCommand">复制</button>
            </div>
            <pre><code>{{ commandSnippet }}</code></pre>
          </div>
        </div>
      </div>
    </section>

    <section class="section section--alt">
      <div class="section-shell">
        <div class="section-head">
          <div>
            <p class="eyebrow">Data Watch</p>
            <h2>秒级洞察，自动推荐可视化</h2>
          </div>
          <p class="section-desc">构建多场景看板，跨表单指标统一对齐，支持拖拽排序。</p>
        </div>
        <DataDashboard />
      </div>
    </section>

    <section class="section cta-section">
      <div class="section-shell cta-shell">
        <div class="cta-panel">
          <p class="eyebrow">Ready to Launch</p>
          <h2>把审批升级为“实时控制台”</h2>
          <p class="cta-desc">
            一键创建、AI 审核助手、全链路可观测性。FormFlow 让校务协同进入更明亮、清晰的数字体验。
          </p>
          <div class="cta-actions">
            <n-button type="primary" size="large" class="cta-btn-dark" @click="handleQuickStart">开启团队</n-button>
            <n-button size="large" tertiary class="cta-btn-ghost" @click="handleDemo">预约演示</n-button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useMessage } from 'naive-ui'
import { useHomeInteractive } from '@/stores/homeInteractive'
import { useAuthStore } from '@/stores/auth'
import ScenarioSelector from '@/components/home/ScenarioSelector.vue'
import FlowPlayground from '@/components/home/FlowPlayground.vue'
import DataDashboard from '@/components/home/DataDashboard.vue'
import QuickActions from '@/components/home/QuickActions.vue'
import HeroNLGenerator from '@/components/home/HeroNLGenerator.vue'

interface NavLink {
  label: string
  description: string
  route: string
  badge?: string | number
}

const router = useRouter()
const route = useRoute()
const homeStore = useHomeInteractive()
const authStore = useAuthStore()
const { autoDecision, etaMinutes, scenarioConfig } = storeToRefs(homeStore)
const message = useMessage()

const particlesRef = ref<HTMLDivElement>()
const spotlightRef = ref<HTMLElement | null>(null)
const cleanupFns: Array<() => void> = []
const commandSnippet = 'npx formflow sync --tenant campus'
let animationId: number | null = null

const scenarioLabel = computed(() => scenarioConfig.value?.name ?? '智能审批')

const logos = ['Rakuten', 'Admiral', 'tokopedia', 'fiserv.', 'Trustt', 'Airwallex', 'Plume', 'VinAudit']

const useCases = [
  {
    title: 'Database Modernization',
    description: '用模板化流程替代纸质审批，快速统一字段与权限。'
  },
  {
    title: 'Cloud Native Applications',
    description: '跨部门协作上线表单，实现自助化发布与灰度。'
  },
  {
    title: 'Edge & Streaming Ops',
    description: '实时采集校务场景数据，按需触发审批与提醒。'
  }
]

const navLinks: NavLink[] = [
  {
    label: '审批控制台',
    description: '待办优先级 + 风险雷达',
    route: '/approvals',
    badge: '5+'
  },
  {
    label: '表单搭建',
    description: '拖拽 + AI Builder',
    route: '/form/designer'
  },
  {
    label: '表单管理',
    description: '模板 / 版本 / 协作',
    route: '/form/list'
  },
  {
    label: '填写工作台',
    description: '历史记录一键回填',
    route: '/form/fill-center'
  },
  {
    label: '提交记录',
    description: '草稿 / 导出 / 编辑',
    route: '/submissions'
  },
  {
    label: '个人信息',
    description: '资料 / 偏好 / 安全',
    route: '/user/profile'
  },
  {
    label: '登录 / 注册',
    description: '接入团队 / 切换身份',
    route: '/login'
  }
]

const isLoggedIn = computed(() => authStore.isLoggedIn)
const userDisplayName = computed(() => authStore.userInfo?.name || authStore.userInfo?.account || 'FormFlow 用户')
const userInitials = computed(() => {
  if (!isLoggedIn.value) return ''
  const base = userDisplayName.value.trim()
  const clean = base.replace(/\s+/g, '')
  return (clean || 'FF').slice(0, 2).toUpperCase()
})

const isActiveLink = (target: string) => route.path.startsWith(target)
const handleNav = (target: string) => {
  if (route.path !== target) {
    router.push(target)
  }
}

const handleAccountClick = () => {
  router.push(isLoggedIn.value ? '/user/profile' : '/login')
}

const handleQuickStart = () => {
  router.push('/form/designer')
}

const handleDemo = () => {
  console.log('观看演示')
}

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

onMounted(() => {
  homeStore.computeFlow()
  homeStore.updateMetrics()
  initParticles()
  initSpotlight()
})

onBeforeUnmount(() => {
  if (animationId !== null) {
    cancelAnimationFrame(animationId)
    animationId = null
  }
  cleanupFns.forEach((fn) => fn())
  cleanupFns.length = 0
})

const initParticles = () => {
  if (!particlesRef.value) return

  const canvas = document.createElement('canvas')
  const rect = particlesRef.value.getBoundingClientRect()
  canvas.width = rect.width
  canvas.height = rect.height
  canvas.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;'
  particlesRef.value.appendChild(canvas)

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const particles: Array<{ x: number; y: number; vx: number; vy: number; size: number }> = []

  for (let i = 0; i < 50; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      size: Math.random() * 2 + 1
    })
  }

  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    particles.forEach((p) => {
      p.x += p.vx
      p.y += p.vy

      if (p.x < 0 || p.x > canvas.width) p.vx *= -1
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1

      ctx.beginPath()
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(255, 255, 255, 0.4)'
      ctx.fill()
    })

    particles.forEach((p1, i) => {
      particles.slice(i + 1).forEach((p2) => {
        const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y)
        if (dist < 120) {
          ctx.beginPath()
          ctx.moveTo(p1.x, p1.y)
          ctx.lineTo(p2.x, p2.y)
          ctx.strokeStyle = `rgba(255, 255, 255, ${(1 - dist / 120) * 0.15})`
          ctx.lineWidth = 0.5
          ctx.stroke()
        }
      })
    })

    animationId = requestAnimationFrame(animate)
  }

  animate()
}

const hasHover = () => {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false
  return window.matchMedia('(hover:hover)').matches
}

const initSpotlight = () => {
  if (!hasHover() || !spotlightRef.value) return

  const el = spotlightRef.value
  let raf = 0

  const move = (event: PointerEvent) => {
    if (raf) return
    raf = requestAnimationFrame(() => {
      const rect = el.getBoundingClientRect()
      const x = ((event.clientX - rect.left) / rect.width) * 100
      const y = ((event.clientY - rect.top) / rect.height) * 100
      el.style.setProperty('--mx', `${x}%`)
      el.style.setProperty('--my', `${y}%`)
      raf = 0
    })
  }

  const reset = () => {
    el.style.setProperty('--mx', '50%')
    el.style.setProperty('--my', '15%')
  }

  el.addEventListener('pointermove', move)
  el.addEventListener('pointerleave', reset)
  cleanupFns.push(() => {
    el.removeEventListener('pointermove', move)
    el.removeEventListener('pointerleave', reset)
  })
}

</script>

<style scoped>
.home-shell {
  position: relative;
  min-height: 100vh;
  padding-bottom: 120px;
  background: var(--bg);
  color: #111217;
}

.hero {
  position: relative;
  padding: 80px 0 120px;
  min-height: 100vh;
  isolation: isolate;
  overflow: hidden;
  background: linear-gradient(180deg, #fbfbfc 0%, #f4f5f9 65%, #ffffff 100%);
}

.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, rgba(255, 255, 255, 0.9), transparent 55%);
  opacity: 0.6;
  pointer-events: none;
}

.hero-shell {
  position: relative;
  z-index: 1;
  width: 100vw;
  margin-left: calc(50% - 50vw);
}

.hero-horizon {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.hero-topbar {
  width: 100vw;
  margin-left: calc(50% - 50vw);
  background: rgba(255, 255, 255, 0.85);
  border-top: 1px solid rgba(11, 13, 18, 0.06);
  border-bottom: 1px solid rgba(11, 13, 18, 0.06);
  box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.4), 0 20px 40px rgba(8, 12, 32, 0.12);
  backdrop-filter: blur(18px);
  padding: clamp(16px, 3vw, 28px) 0;
}

.hero-topbar__inner {
  max-width: 1360px;
  margin: 0 auto;
  width: 100%;
  padding: 0 clamp(24px, 6vw, 80px);
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: clamp(16px, 3vw, 32px);
}

.hero-brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-mark {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: #0b0d12;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.brand-meta strong {
  display: block;
  font-size: 18px;
  color: #0b0d12;
}

.hero-topnav {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 14px;
}

.nav-item {
  position: relative;
  padding: 12px 14px;
  border: 1px solid rgba(11, 13, 18, 0.1);
  border-radius: 18px;
  background: #fff;
  font-size: 13px;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.nav-item:hover,
.nav-item:focus-visible {
  border-color: #0b0d12;
  transform: translateY(-2px);
}

.nav-item.active {
  border-color: #ff7a18;
  box-shadow: 0 12px 26px rgba(11, 13, 18, 0.12);
}

.nav-label {
  display: block;
  font-weight: 600;
  color: #0b0d12;
}

.nav-desc {
  display: block;
  color: #6b7282;
  font-size: 12px;
}

.nav-badge {
  position: absolute;
  top: 10px;
  right: 12px;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #ff7a18;
}

.hero-account {
  display: flex;
  justify-content: flex-end;
}

.account-btn {
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 6px 0;
}

.account-avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: #0b0d12;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.account-avatar--ghost {
  background: rgba(11, 13, 18, 0.08);
  color: #0b0d12;
}

.account-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.account-name {
  font-weight: 600;
}

.account-link {
  font-size: 12px;
  color: #6b7282;
}

.hero-grid {
  width: 100%;
}

.hero-grid__inner {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
  gap: 48px;
  padding: 36px clamp(24px, 5vw, 72px) 60px;
  background: #fff;
  border-radius: 48px;
  border: 1px solid rgba(15, 18, 23, 0.08);
  box-shadow: 0 50px 140px rgba(12, 16, 32, 0.18);
  max-width: 1360px;
  margin: 0 auto;
  width: calc(100% - clamp(48px, 8vw, 160px));
}

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
  animation: shard-float 16s ease-in-out infinite;
}

.hero-shard--left {
  left: -10%;
  top: -8%;
}

.hero-shard--right {
  right: -15%;
  top: 10%;
  transform: scaleX(-1);
  animation-delay: 6s;
}

.hero-orb {
  position: absolute;
  width: 260px;
  height: 260px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 122, 24, 0.22), transparent 65%);
  filter: blur(2px);
  animation: orb-float 20s linear infinite;
}

.hero-orb--one {
  top: -40px;
  left: 20%;
}

.hero-orb--two {
  bottom: -80px;
  right: 18%;
  animation-delay: 10s;
}

@keyframes shard-float {
  0% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(0, -20px, 0);
  }
  100% {
    transform: translate3d(0, 0, 0);
  }
}

@keyframes orb-float {
  0% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(-20px, -30px, 0);
  }
  100% {
    transform: translate3d(0, 0, 0);
  }
}

.hero-sky {
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0.08;
}

.hero-stripe {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(120deg, rgba(255, 255, 255, 0.9) 25%, transparent 25%)
      , linear-gradient(120deg, transparent 45%, rgba(12, 13, 18, 0.95) 45%);
  clip-path: polygon(0 0, 70% 0, 55% 100%, 0% 100%);
  opacity: 0.45;
  pointer-events: none;
}

.hero-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero-content::after {
  content: '';
  display: block;
  width: 72px;
  height: 4px;
  background: linear-gradient(90deg, #0b0d12, #ff7a18);
  border-radius: 999px;
}

.hero-nav {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.hero-terminal {
  padding: 32px;
  background: #f8f9fb;
  border-radius: 28px;
  border: 1px solid rgba(15, 18, 23, 0.06);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hero-kicker,
.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.3em;
  font-size: 12px;
  color: var(--text-3);
  margin: 0;
}


.hero-title {
  margin: 8px 0;
  font-size: clamp(40px, 5vw, 68px);
  line-height: 1.05;
  color: #0b0d12;
}

.hero-title span {
  display: block;
  font-size: clamp(28px, 4vw, 40px);
  color: #ff7a18;
}

.hero-subtitle {
  margin: 0;
  color: #4d5464;
  font-size: 17px;
}

.hero-actions :deep(.n-button) {
  min-width: 160px;
  font-weight: 600;
}


.hero-actions :deep(.cta-primary) {
  position: relative;
  border: 0;
  color: #fff;
  background: #0b0d12;
  overflow: hidden;
}

.hero-actions :deep(.cta-primary)::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(255, 122, 24, 0.18);
  opacity: 0;
  transition: opacity 0.25s ease;
}

.hero-actions :deep(.cta-primary:hover)::after,
.hero-actions :deep(.cta-primary:focus-visible)::after {
  opacity: 1;
}

.hero-actions :deep(.cta-secondary) {
  border: 1.5px solid rgba(11, 13, 18, 0.2);
  color: #0b0d12;
  background: transparent;
}



.hero-stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding-top: 12px;
  border-top: 1px solid rgba(15, 18, 23, 0.08);
}


.hero-stat {
  flex: 1 1 120px;
  padding: 14px 16px;
  border: 1px solid rgba(15, 18, 23, 0.1);
  background: #f8f9fb;
  border-radius: 18px;
}

.hero-stat__label {
  display: block;
  font-size: 12px;
  letter-spacing: 0.08em;
  color: #6c7282;
  margin-bottom: 6px;
}

.hero-stat__value {
  font-size: 22px;
  color: #0b0d12;
}

.hero-terminal {
  gap: 16px;
}

.terminal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.terminal-head h3 {
  margin: 6px 0 0;
  font-size: 20px;
}

.terminal-foot {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}

.terminal-foot span {
  display: block;
  font-size: 12px;
  color: var(--text-3);
}

.terminal-foot strong {
  font-size: 16px;
  color: var(--text-1);
}

.section-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 32px;
  border-bottom: 1px solid var(--divider);
  padding-bottom: 18px;
}

.section-head.compact {
  margin-bottom: 18px;
}

.section-head h2 {
  margin: 6px 0 0;
  font-size: clamp(24px, 4vw, 36px);
  color: #0b0d12;
}

.section-desc {
  max-width: 420px;
  margin: 0;
  color: #5a6172;
}

.flow-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 32px;
}

@media (min-width: 1024px) {
  .flow-grid {
    grid-template-columns: 1.25fr 0.75fr;
  }
}

.section-flow .metrics-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.metric-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #fff;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-card);
  padding: 24px;
  border-radius: 24px;
}

.metric-row {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #5a6172;
}

.metric-row strong {
  font-size: 18px;
  color: #0b0d12;
}

.progress-line {
  grid-column: 1 / -1;
  height: 6px;
  border-radius: 0;
  background: #e7e9ef;
  position: relative;
  overflow: hidden;
}

.progress-line::after {
  content: '';
  position: absolute;
  inset: 0;
  width: var(--value, 0%);
  background: linear-gradient(90deg, #111217, #ff7a18);
}


.progress-line.warn::after {
  background: linear-gradient(90deg, #ffa938, #ff7a18);
}

.progress-line.danger::after {
  background: linear-gradient(90deg, #111217, #c1121f);
}

.copy-shell {
  background: #0b0d12;
  border: none;
  color: #fff;
  border-radius: 24px;
}

.copy-shell pre {
  font-size: 14px;
}

.copy-btn {
  background: transparent;
  border: 1.5px solid #fff;
  color: #fff;
  border-radius: 0;
  padding: 4px 12px;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;
  font-size: 13px;
}

.copy-btn:hover {
  background: #fff;
  color: #111217;
}

.cta-section {
  margin-top: 80px;
}

.cta-shell {
  padding: 0 24px;
}

.cta-panel {
  text-align: center;
  padding: 56px;
  background: #161722;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 28px 70px rgba(0, 0, 0, 0.4);
  border-radius: 32px;
  color: #fff;
}

.section--dark .cta-panel {
  background: #ff7a18;
  color: #111217;
}

.cta-panel h2 {
  margin: 12px 0;
  font-size: clamp(28px, 4vw, 40px);
}

.cta-desc {
  color: rgba(255, 255, 255, 0.74);
  margin: 0 auto 32px;
  max-width: 520px;
}

.section--dark .cta-panel .cta-desc {
  color: rgba(17, 18, 23, 0.76);
}

.cta-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
}

.cta-actions :deep(.n-button) {
  min-width: 160px;
}

@media (max-width: 1024px) {
  .home-shell {
    padding: 0 16px 80px;
  }
}

@media (max-width: 768px) {
  .hero-panel {
    padding: 24px;
  }

  .terminal-foot {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .section-head {
    flex-direction: column;
  }
}

@media (max-width: 540px) {
  .terminal-foot {
    grid-template-columns: 1fr;
  }

  .hero-stats {
    flex-direction: column;
  }

  .cta-actions {
    flex-direction: column;
  }
}

.value-section {
  background: var(--breath);
}

.value-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 32px;
  align-items: center;
}

@media (min-width: 1024px) {
  .value-grid {
    grid-template-columns: 1fr 1fr;
    gap: 64px;
  }
}

.value-copy h2 {
  margin: 18px 0;
  font-size: clamp(36px, 5vw, 52px);
}

.value-copy p {
  margin: 0 0 24px;
  color: #4b5164;
  line-height: 1.7;
}

.value-links {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.link-pill {
  border: none;
  border-radius: 999px;
  padding: 12px 28px;
  font-weight: 600;
  cursor: pointer;
  background: #0b0d12;
  color: #fff;
}

.link-pill.ghost {
  background: transparent;
  border: 1px solid #0b0d12;
  color: #0b0d12;
}

.value-cards {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.value-card {
  background: #fff;
  border-radius: 24px;
  padding: 32px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-card);
}

.value-card ul {
  margin: 16px 0 20px;
  padding-left: 18px;
  color: #4a5163;
  line-height: 1.6;
}

.value-tag {
  font-size: 13px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #7c8194;
}

.value-tag.accent {
  color: #ff7a18;
}

.value-link {
  font-weight: 600;
  color: #0b0d12;
}

.usecase-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
}

.usecase-card {
  background: #fff;
  padding: 28px;
  border-radius: 20px;
  border: 1px solid var(--border);
  box-shadow: 0 16px 40px rgba(8, 10, 18, 0.08);
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 260px;
}

.usecase-index {
  font-size: 14px;
  letter-spacing: 0.2em;
  color: #ff7a18;
}

.usecase-card h3 {
  margin: 0;
  font-size: 20px;
}

.usecase-card p {
  margin: 0;
  color: #4d5568;
  flex-grow: 1;
}

.usecase-card button {
  align-self: flex-start;
  border: none;
  background: transparent;
  color: #0b0d12;
  font-weight: 600;
  cursor: pointer;
}

@media (prefers-reduced-motion: reduce) {
  .hero,
  .hero-panel,
  .card,
  .energy-frame,
  .cta-panel,
  .metrics-stack,
  .hero-actions :deep(.n-button) {
    transition: none !important;
  }
}
</style>