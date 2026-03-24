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
                <n-dropdown
                  :options="accountMenuOptions"
                  @select="handleAccountMenuSelect"
                  trigger="click"
                >
                  <button type="button" class="account-btn">
                    <n-avatar
                      v-if="isLoggedIn && userAvatarUrl"
                      :src="userAvatarUrl"
                      :size="40"
                      round
                      class="account-avatar-img"
                    />
                    <span
                      v-else
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
                </n-dropdown>
              </div>
            </div>
          </header>
          <div class="hero-grid">
            <div class="hero-grid__inner">
              <div class="hero-content" ref="spotlightRef">
                <div class="hero-text-block">
                  <h2 class="hero-text__title">氛围亮度自适应</h2>
                  <p class="hero-text__subtitle">让每一次输入都保持清晰与质感</p>
                  <p class="hero-text__accent">QUANTUM ACCESS DECK</p>
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
                    <strong>智能审批</strong>
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
            常用入口按照控制台网格呈现，Hover 即高亮，满足"至少 3 处 Hover 反馈"验收要求。
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
          <article class="value-card" @click="handleDeveloperHub">
            <span class="value-tag">For Developers</span>
            <ul>
              <li>自动生成表单与流程脚本</li>
              <li>版本回滚与环境隔离</li>
              <li>完整 API / Webhook 管理</li>
            </ul>
            <span class="value-link">Developer Hub →</span>
          </article>
          <article class="value-card" @click="handleOpsConsole">
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

    <section class="section section-flow section--wide">
      <div class="section-shell section-shell--wide">
        <div class="flow-header">
          <div class="flow-header__content">
            <div class="flow-header__badge">
              <span class="badge-dot"></span>
              <span class="badge-text">我的审批</span>
            </div>
            <h2 class="flow-header__title">查看我发起的审批进度</h2>
            <p class="flow-header__desc">
              实时掌握您发起的审批流程进度，了解每个审批的当前状态和处理情况。
            </p>
          </div>
        </div>
        <div class="flow-grid flow-grid--wide">
          <MySubmittedApprovals />
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
          <h2>把审批升级为"实时控制台"</h2>
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

    <footer class="home-footer">
      <div class="footer-shell">
        <div class="footer-grid">
          <div class="footer-brand">
            <span class="brand-mark">FF</span>
            <p>FormFlow 高校多租户表单与审批中台，让校务协同更高效、更智能。</p>
          </div>
          <div class="footer-col">
            <h4>产品</h4>
            <ul>
              <li><a href="#" @click.prevent="handleQuickStart">表单设计器</a></li>
              <li><a href="#" @click.prevent="handleDemo">流程编排</a></li>
              <li><a href="#">AI 助手</a></li>
              <li><a href="#">数据看板</a></li>
            </ul>
          </div>
          <div class="footer-col">
            <h4>资源</h4>
            <ul>
              <li><a href="#">文档中心</a></li>
              <li><a href="#">API 参考</a></li>
              <li><a href="#">最佳实践</a></li>
              <li><a href="#">更新日志</a></li>
            </ul>
          </div>
          <div class="footer-col">
            <h4>公司</h4>
            <ul>
              <li><a href="#">关于我们</a></li>
              <li><a href="#">联系我们</a></li>
              <li><a href="#">隐私政策</a></li>
              <li><a href="#">服务条款</a></li>
            </ul>
          </div>
        </div>
        <div class="footer-bottom">
          <span class="footer-copyright">© 2024 FormFlow. All rights reserved.</span>
          <div class="footer-social">
            <a href="#" title="GitHub">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
              </svg>
            </a>
            <a href="#" title="Twitter">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
              </svg>
            </a>
            <a href="#" title="文档">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM6 20V4h7v5h5v11H6z"/>
              </svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>
<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useMessage, NAvatar } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import MySubmittedApprovals from '@/components/home/MySubmittedApprovals.vue'
import DataDashboard from '@/components/home/DataDashboard.vue'
import QuickActions from '@/components/home/QuickActions.vue'
import HeroNLGenerator from '@/components/home/HeroNLGenerator.vue'
import LogoutButton from '@/components/LogoutButton.vue'

interface NavLink {
  label: string
  description: string
  route: string
  badge?: string | number
}

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const message = useMessage()

const particlesRef = ref<HTMLDivElement>()
const spotlightRef = ref<HTMLElement | null>(null)
const cleanupFns: Array<() => void> = []
const commandSnippet = 'npx formflow sync --tenant campus'
let animationId: number | null = null

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
const userAvatarUrl = computed(() => {
  if (!isLoggedIn.value) return null
  const avatarUrl = authStore.userInfo?.avatar_url
  if (!avatarUrl) return null
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const token = authStore.accessToken || localStorage.getItem('access_token')
  return `${apiBase}/api/v1/users/me/avatar?token=${encodeURIComponent(token || '')}`
})
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

interface MenuOption {
  label: string
  key: string
}

const accountMenuOptions = computed<MenuOption[]>(() => {
  if (isLoggedIn.value) {
    return [
      { label: '个人信息', key: 'profile' },
      { label: '退出登录', key: 'logout' }
    ]
  }
  return [
    { label: '登录 / 注册', key: 'login' }
  ]
})

const handleAccountMenuSelect = (key: string) => {
  if (key === 'profile') {
    router.push('/user/profile')
  } else if (key === 'logout') {
    authStore.logout()
  } else if (key === 'login') {
    router.push('/login')
  }
}

const handleQuickStart = () => {
  router.push('/form/designer')
}

const handleDemo = () => {
  console.log('观看演示')
}

const handleDeveloperHub = () => {
  router.push('/form/designer')
}

const handleOpsConsole = () => {
  router.push('/approvals')
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
  padding-bottom: 0;
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
  border-radius: 4px;
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

.account-avatar-img {
  flex-shrink: 0;
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
  border-radius: 8px;
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
  0% { transform: translate3d(0, 0, 0); }
  50% { transform: translate3d(0, -20px, 0); }
  100% { transform: translate3d(0, 0, 0); }
}

@keyframes orb-float {
  0% { transform: translate3d(0, 0, 0); }
  50% { transform: translate3d(-20px, -30px, 0); }
  100% { transform: translate3d(0, 0, 0); }
}

.hero-sky {
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0.08;
}

.hero-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  position: relative;
  background: linear-gradient(135deg, var(--bg-dark) 0%, var(--bg-dark) 70%, var(--bg-darker) 70%, var(--bg-darker) 100%);
  padding: 40px;
  border-radius: 0;
}

.hero-text-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hero-text__title {
  font-size: clamp(24px, 3vw, 28px);
  color: var(--color-white);
  font-weight: 700;
  line-height: 1.2;
  margin: 0;
  text-align: left;
}

.hero-text__subtitle {
  font-size: 14px;
  color: var(--color-gray-400);
  font-weight: 400;
  line-height: 1.5;
  margin: 0;
  text-align: left;
}

.hero-text__accent {
  font-size: 11px;
  color: var(--color-gray-300);
  letter-spacing: 0.3em;
  margin: 16px 0 0;
  text-align: left;
}

.hero-terminal {
  padding: 32px;
  background: #f8f9fb;
  border-radius: 8px;
  border: 1px solid rgba(15, 18, 23, 0.06);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.3em;
  font-size: 12px;
  color: var(--text-3);
  margin: 0;
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

.section-flow {
  background: linear-gradient(180deg, #f8f9fb 0%, #ffffff 100%);
  padding: 80px 0;
  position: relative;
  overflow: hidden;
}

.section-flow::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(11, 13, 18, 0.1), transparent);
}

.flow-header {
  max-width: 720px;
  margin: 0 auto 56px;
  text-align: center;
}

.flow-header__content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  align-items: center;
}

.flow-header__badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: rgba(255, 122, 24, 0.08);
  border: 1px solid rgba(255, 122, 24, 0.2);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #ff7a18;
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ff7a18;
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.2);
  }
}

.flow-header__title {
  font-size: clamp(32px, 5vw, 48px);
  font-weight: 700;
  color: #0b0d12;
  margin: 0;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.flow-header__desc {
  font-size: 16px;
  color: #5a6172;
  line-height: 1.7;
  margin: 0;
  max-width: 580px;
}

.flow-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 32px;
  align-items: start;
}

@media (min-width: 1024px) {
  .flow-grid {
    grid-template-columns: 1.4fr 0.6fr;
    gap: 48px;
  }
}

/* 宽屏布局 - 我的审批区域 */
.section--wide {
  padding: 60px 24px;
}

.section-shell--wide {
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
}

.flow-grid--wide {
  display: block;
  width: 100%;
}

.flow-playground-wrapper {
  background: #fff;
  border-radius: 16px;
  border: 1px solid rgba(11, 13, 18, 0.08);
  box-shadow: 
    0 4px 24px rgba(0, 0, 0, 0.04),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
  padding: 32px;
  transition: box-shadow 0.3s ease;
}

.flow-playground-wrapper:hover {
  box-shadow: 
    0 8px 40px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
}

.section-flow .metrics-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: sticky;
  top: 100px;
}

.metric-card {
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 249, 251, 0.95) 100%);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  padding: 28px;
  border-radius: 16px;
  backdrop-filter: blur(20px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.metric-card:hover {
  transform: translateY(-4px);
  box-shadow:
    0 16px 48px rgba(0, 0, 0, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 1);
  border-color: rgba(255, 122, 24, 0.2);
}

.metric-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(11, 13, 18, 0.06);
}

.metric-card__header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  letter-spacing: -0.01em;
}

.metric-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #22c55e;
}

.metric-badge::before {
  content: '';
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #22c55e;
  animation: pulse-dot 2s ease-in-out infinite;
}

.metric-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  font-size: 14px;
  color: #5a6172;
}

.metric-row-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.metric-row span {
  font-weight: 500;
}

.metric-row strong {
  font-size: 18px;
  color: #0b0d12;
  font-weight: 700;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.progress-line {
  height: 6px;
  border-radius: 999px;
  background: rgba(242, 243, 245, 0.8);
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.08);
}

.progress-line::after {
  content: '';
  position: absolute;
  inset: 0;
  width: var(--value, 0%);
  background: linear-gradient(90deg, #F59E0B 0%, #FBBF24 100%);
  border-radius: 999px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow:
    0 2px 8px rgba(245, 158, 11, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.progress-line.warn::after {
  background: linear-gradient(90deg, #F59E0B 0%, #FBBF24 100%);
  box-shadow:
    0 2px 8px rgba(245, 158, 11, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.progress-line.danger::after {
  background: linear-gradient(90deg, #EF4444 0%, #F87171 100%);
  box-shadow:
    0 2px 8px rgba(239, 68, 68, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.copy-shell {
  background: #1E1E1E;
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #fff;
  border-radius: 12px;
  backdrop-filter: blur(12px);
  overflow: hidden;
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
}

.copy-shell:hover {
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 122, 24, 0.3);
}

.code__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.code__label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
}

.code__label svg {
  opacity: 0.6;
}

.copy-shell pre {
  font-size: 14px;
  padding: 20px 24px;
  margin: 0;
  background: transparent;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.9);
}

.copy-btn {
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

.copy-btn svg {
  opacity: 0.6;
}

.copy-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  color: #fff;
}

.copy-btn:hover svg {
  opacity: 0.8;
}

.copy-btn:active {
  transform: translateY(0);
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
  border-radius: 8px;
  color: #fff;
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
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.link-pill:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.link-pill.ghost {
  background: transparent;
  border: 1px solid #0b0d12;
  color: #0b0d12;
}

.link-pill.ghost:hover {
  background: #0b0d12;
  color: #fff;
}

.value-cards {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.value-card {
  background: #fff;
  border-radius: 8px;
  padding: 32px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-card);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  cursor: pointer;
}

.value-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-floating);
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
  cursor: pointer;
  transition: color 0.2s ease;
}

.value-link:hover {
  color: #ff7a18;
}

.usecase-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.usecase-card {
  background: #fff;
  padding: 28px;
  border-radius: 8px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 260px;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.usecase-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-floating);
}

.usecase-index {
  font-size: 14px;
  letter-spacing: 0.2em;
  color: #ff7a18;
  font-weight: 600;
}

.usecase-card h3 {
  margin: 0;
  font-size: 20px;
  color: #0b0d12;
}

.usecase-card p {
  margin: 0;
  color: #4d5464;
  flex-grow: 1;
  line-height: 1.6;
}

.usecase-card button {
  align-self: flex-start;
  border: none;
  background: transparent;
  color: #0b0d12;
  font-weight: 600;
  cursor: pointer;
  padding: 8px 0;
  position: relative;
  transition: color 0.2s ease;
}

.usecase-card button::after {
  content: '';
  position: absolute;
  bottom: 4px;
  left: 0;
  width: 100%;
  height: 2px;
  background: #ff7a18;
  transform: scaleX(0);
  transform-origin: right;
  transition: transform 0.2s ease;
}

.usecase-card button:hover {
  color: #ff7a18;
}

.usecase-card button:hover::after {
  transform: scaleX(1);
  transform-origin: left;
}

/* Footer Styles */
.home-footer {
  background: #0b0d12;
  color: #fff;
  padding: 64px 0 32px;
  margin-top: 80px;
}

.footer-shell {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.footer-grid {
  display: grid;
  grid-template-columns: 2fr repeat(3, 1fr);
  gap: 48px;
  padding-bottom: 48px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.footer-brand .brand-mark {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: #fff;
  color: #0b0d12;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
}

.footer-brand p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
}

.footer-col h4 {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.4);
  margin: 0 0 20px;
}

.footer-col ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.footer-col a {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  text-decoration: none;
  transition: color 0.2s ease;
}

.footer-col a:hover {
  color: #ff7a18;
}

.footer-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 32px;
  flex-wrap: wrap;
  gap: 16px;
}

.footer-copyright {
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
}

.footer-social {
  display: flex;
  gap: 16px;
}

.footer-social a {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  text-decoration: none;
  transition: background 0.2s ease, transform 0.2s ease;
}

.footer-social a:hover {
  background: #ff7a18;
  transform: translateY(-2px);
}

@media (max-width: 900px) {
  .footer-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .footer-grid {
    grid-template-columns: 1fr;
    gap: 32px;
  }

  .footer-bottom {
    flex-direction: column;
    text-align: center;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero,
  .hero-panel,
  .card,
  .energy-frame,
  .cta-panel,
  .metrics-stack,
  .hero-actions :deep(.n-button),
  .usecase-card,
  .usecase-card button,
  .value-link,
  .footer-social a,
  .link-pill,
  .value-card {
    transition: none !important;
  }
}
</style>