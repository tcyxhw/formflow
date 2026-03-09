<template>
  <div class="auth-shell">
    <div class="auth-viewport">
      <aside class="auth-showcase" aria-hidden="true">
        <div class="showcase-content">
          <div class="showcase-visual" role="img" aria-label="动效展示">
            <div class="visual-core">
              <span>FF</span>
            </div>
            <div class="visual-ring ring-primary"></div>
            <div class="visual-ring ring-secondary"></div>
            <div class="visual-particle particle-one"></div>
            <div class="visual-particle particle-two"></div>
            <div class="visual-particle particle-three"></div>
          </div>
          <p class="eyebrow">Quantum Access Deck</p>
          <div class="dynamic-caption-wrapper">
            <transition name="spotlight-fade" mode="out-in">
              <p class="dynamic-caption" :key="activeSpotlightIndex">
                {{ spotlightMessages[activeSpotlightIndex] }}
              </p>
            </transition>
            <div class="caption-gradient" aria-hidden="true">
              <div class="gradient-fill" :key="activeSpotlightIndex"></div>
            </div>
          </div>
          <div class="dynamic-chips" role="list">
            <span
              class="chip"
              role="listitem"
              v-for="(item, index) in motionLabels"
              :key="`${item}-${index}`"
            >
              {{ item }}
            </span>
          </div>
          <div class="spotlight-controls" role="tablist">
            <button
              v-for="(item, index) in spotlightMessages"
              :key="item"
              class="spotlight-control"
              type="button"
              :class="{ active: activeSpotlightIndex === index }"
              :aria-label="`播放动态文案 ${index + 1}`"
              :aria-pressed="activeSpotlightIndex === index"
              role="tab"
              @click="handleSpotlightDotClick(index)"
            ></button>
          </div>
        </div>
      </aside>

      <section class="auth-panel" aria-live="polite">
        <div class="form-scroll" data-scroll>
          <div class="panel-inner">
            <div class="tenant-info">
              <div class="current-tenant">
                <span class="tenant-label">当前学校</span>
                <span class="tenant-name">{{ currentTenantName }}</span>
              </div>
              <button
                type="button"
                class="change-tenant-btn"
                @click="goToTenantSelect"
                aria-label="更换学校"
              >
                更换学校
              </button>
            </div>

            <header class="panel-head">
              <div class="panel-logo" aria-label="FormFlow Logo Icon"></div>
              <div>
                <p class="eyebrow">Access</p>
                <h2>{{ isLogin ? '欢迎回来' : '创建账户' }}</h2>
                <p class="panel-desc">{{ isLogin ? '登录以继续使用服务' : '注册新账户开始使用' }}</p>
              </div>
            </header>

            <div class="tabs" role="tablist" aria-label="登录或注册选项">
              <button
                type="button"
                class="tab"
                :class="{ active: isLogin }"
                @click="switchTab(true)"
                role="tab"
                :aria-selected="isLogin"
                :tabindex="isLogin ? 0 : -1"
              >
                登录
              </button>
              <button
                type="button"
                class="tab"
                :class="{ active: !isLogin }"
                @click="switchTab(false)"
                role="tab"
                :aria-selected="!isLogin"
                :tabindex="!isLogin ? 0 : -1"
              >
                注册
              </button>
            </div>

            <div class="forms-container">
              <Transition name="form-fade" mode="out-in">
                <form
                  v-if="isLogin"
                  @submit.prevent="handleLogin"
                  class="auth-form"
                  aria-label="登录表单"
                  key="login"
                  novalidate
                >
                  <div class="form-group">
                    <label for="login-phone" class="form-label">手机号</label>
                    <input
                      id="login-phone"
                      v-model="loginForm.phone"
                      type="tel"
                      class="form-input"
                      placeholder="请输入11位手机号"
                      pattern="[0-9]{11}"
                      autocomplete="tel"
                      :disabled="loading"
                      required
                    />
                  </div>

                  <div class="form-group">
                    <label for="login-password" class="form-label">密码</label>
                    <div class="password-input-wrapper">
                      <input
                        id="login-password"
                        v-model="loginForm.password"
                        :type="showPassword.login ? 'text' : 'password'"
                        class="form-input"
                        placeholder="请输入密码"
                        autocomplete="current-password"
                        :disabled="loading"
                        required
                      />
                      <button
                        type="button"
                        class="password-toggle"
                        @click="showPassword.login = !showPassword.login"
                        :aria-label="showPassword.login ? '隐藏密码' : '显示密码'"
                        tabindex="0"
                      >
                        <svg
                          v-if="showPassword.login"
                          class="icon"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          aria-hidden="true"
                        >
                          <path
                            d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"
                          />
                          <line x1="1" y1="1" x2="23" y2="23" />
                        </svg>
                        <svg
                          v-else
                          class="icon"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          aria-hidden="true"
                        >
                          <path
                            d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"
                          />
                          <circle cx="12" cy="12" r="3" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  <div class="form-group checkbox-group">
                    <label class="checkbox-wrapper">
                      <button
                        type="button"
                        class="checkbox"
                        :class="{ checked: loginForm.remember }"
                        @click="loginForm.remember = !loginForm.remember"
                        role="checkbox"
                        :aria-checked="loginForm.remember"
                        @keydown.space.prevent="loginForm.remember = !loginForm.remember"
                      >
                        <svg
                          v-if="loginForm.remember"
                          class="check-icon"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="3"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          aria-hidden="true"
                        >
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      </button>
                      <span class="checkbox-label">记住我的登录状态</span>
                    </label>
                  </div>

                  <button
                    type="submit"
                    class="btn btn-primary"
                    :disabled="loading"
                    :aria-busy="loading"
                  >
                    <span class="btn-text">{{ loading ? '登录中...' : '登录' }}</span>
                  </button>

                  <div class="form-footer">
                    <a href="#" class="link" @click.prevent="handleForgotPassword"
                      >忘记密码？
                    </a>
                  </div>
                </form>

                <form
                  v-else
                  @submit.prevent="handleRegister"
                  class="auth-form"
                  aria-label="注册表单"
                  key="register"
                  novalidate
                >
                  <div class="form-group">
                    <label for="reg-phone" class="form-label">手机号</label>
                    <input
                      id="reg-phone"
                      v-model="registerForm.phone"
                      type="tel"
                      class="form-input"
                      placeholder="请输入11位手机号"
                      pattern="[0-9]{11}"
                      autocomplete="tel"
                      :disabled="loading"
                      required
                    />
                  </div>

                  <div class="form-group">
                    <label for="reg-name" class="form-label">真实姓名</label>
                    <input
                      id="reg-name"
                      v-model="registerForm.name"
                      type="text"
                      class="form-input"
                      placeholder="请输入真实姓名"
                      autocomplete="name"
                      :disabled="loading"
                      required
                    />
                  </div>

                  <div class="form-group">
                    <label for="reg-password" class="form-label">设置密码</label>
                    <div class="password-input-wrapper">
                      <input
                        id="reg-password"
                        v-model="registerForm.password"
                        :type="showPassword.register ? 'text' : 'password'"
                        class="form-input"
                        placeholder="8-20位字符，包含字母和数字"
                        autocomplete="new-password"
                        :disabled="loading"
                        required
                      />
                      <button
                        type="button"
                        class="password-toggle"
                        @click="showPassword.register = !showPassword.register"
                        :aria-label="showPassword.register ? '隐藏密码' : '显示密码'"
                        tabindex="0"
                      >
                        <svg
                          v-if="showPassword.register"
                          class="icon"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          aria-hidden="true"
                        >
                          <path
                            d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"
                          />
                          <line x1="1" y1="1" x2="23" y2="23" />
                        </svg>
                        <svg
                          v-else
                          class="icon"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          aria-hidden="true"
                        >
                          <path
                            d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"
                          />
                          <circle cx="12" cy="12" r="3" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  <div class="form-group">
                    <label for="reg-confirm" class="form-label">确认密码</label>
                    <div class="password-input-wrapper">
                      <input
                        id="reg-confirm"
                        v-model="registerForm.confirmPassword"
                        :type="showPassword.confirm ? 'text' : 'password'"
                        class="form-input"
                        placeholder="请再次输入密码"
                        autocomplete="new-password"
                        :disabled="loading"
                        required
                      />
                      <button
                        type="button"
                        class="password-toggle"
                        @click="showPassword.confirm = !showPassword.confirm"
                        :aria-label="showPassword.confirm ? '隐藏密码' : '显示密码'"
                        tabindex="0"
                      >
                        <svg
                          v-if="showPassword.confirm"
                          class="icon"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          aria-hidden="true"
                        >
                          <path
                            d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"
                          />
                          <line x1="1" y1="1" x2="23" y2="23" />
                        </svg>
                        <svg
                          v-else
                          class="icon"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          aria-hidden="true"
                        >
                          <path
                            d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"
                          />
                          <circle cx="12" cy="12" r="3" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  <div class="form-group checkbox-group">
                    <label class="checkbox-wrapper">
                      <button
                        type="button"
                        class="checkbox"
                        :class="{ checked: registerForm.agree }"
                        @click="registerForm.agree = !registerForm.agree"
                        role="checkbox"
                        :aria-checked="registerForm.agree"
                        @keydown.space.prevent="registerForm.agree = !registerForm.agree"
                      >
                        <svg
                          v-if="registerForm.agree"
                          class="check-icon"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="3"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          aria-hidden="true"
                        >
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      </button>
                      <span class="checkbox-label">
                        我已阅读并同意
                        <a href="#" class="link" @click.stop>服务条款</a> 和
                        <a href="#" class="link" @click.stop>隐私政策</a>
                      </span>
                    </label>
                  </div>

                  <button
                    type="submit"
                    class="btn btn-primary"
                    :disabled="loading"
                    :aria-busy="loading"
                  >
                    <span class="btn-text">{{ loading ? '注册中...' : '注册' }}</span>
                  </button>
                </form>
              </Transition>
            </div>

            <div class="switch-tips">
              <span class="tips-text">{{ isLogin ? '还没有账号？' : '已有账号？' }}</span>
              <button
                type="button"
                class="link link-strong"
                @click="switchTab(!isLogin)"
              >
                {{ isLogin ? '立即注册' : '立即登录' }}
              </button>
            </div>
          </div>
        </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage, useDialog } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { useTenantStore } from '@/stores/tenant'

interface LoginForm {
  phone: string
  password: string
  remember: boolean
}

interface RegisterForm {
  phone: string
  name: string
  password: string
  confirmPassword: string
  agree: boolean
}

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const tenantStore = useTenantStore()
const message = useMessage()
const dialog = useDialog()

const showPassword = reactive({
  login: false,
  register: false,
  confirm: false
})

const isLogin = ref(true)
const loading = ref(false)

const loginForm = reactive<LoginForm>({
  phone: '15018816993',
  password: '11223344',
  remember: true
})

const registerForm = reactive<RegisterForm>({
  phone: '',
  name: '',
  password: '',
  confirmPassword: '',
  agree: false
})

const spotlightMessages = [
  '粒子环绕的护盾，将审批路径实时映射在光晕之上',
  '氛围亮度自适应，让每一次输入都保持清晰与质感',
  '悬浮态能量框架，动态提示步骤与完成度的跃迁'
]

const motionLabels = [
  'AURORA LOOP',
  'LIVE ROUTING',
  'AI SURGE',
  'NEBULA INPUT',
  'QUANTUM SYNC',
  'MAGNETIC FLOW'
]

const activeSpotlightIndex = ref(0)
let spotlightTimer: number | null = null

const currentTenantName = computed(() => tenantStore.currentTenant?.name || '未选择')

const resolveErrorMessage = (error: unknown, fallback: string) =>
  error instanceof Error ? error.message : fallback

const goToTenantSelect = () => {
  dialog.warning({
    title: '提示',
    content: '切换学校将需要重新登录，确定要继续吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: () => {
      tenantStore.clearTenant()
      router.push('/tenant-select')
    }
  })
}

const startSpotlightRotation = () => {
  if (spotlightTimer !== null || spotlightMessages.length <= 1) return
  spotlightTimer = window.setInterval(() => {
    activeSpotlightIndex.value = (activeSpotlightIndex.value + 1) % spotlightMessages.length
  }, 4200)
}

const stopSpotlightRotation = () => {
  if (spotlightTimer === null) return
  window.clearInterval(spotlightTimer)
  spotlightTimer = null
}

const handleSpotlightDotClick = (index: number) => {
  activeSpotlightIndex.value = index
  stopSpotlightRotation()
  startSpotlightRotation()
}

const showMessage = (type: 'success' | 'error' | 'warning' | 'info', content: string) => {
  message[type](content)
}

const validatePhone = (phone: string): boolean => {
  const reg = /^1[3-9]\d{9}$/
  if (!reg.test(phone)) {
    showMessage('error', '请输入正确的手机号')
    return false
  }
  return true
}

const validatePassword = (password: string): boolean => {
  if (password.length < 6) {
    showMessage('error', '密码长度至少6位')
    return false
  }
  if (password.length > 20) {
    showMessage('error', '密码长度不能超过20位')
    return false
  }
  return true
}

const validateName = (name: string): boolean => {
  if (name.length < 2) {
    showMessage('error', '姓名至少2个字符')
    return false
  }
  if (name.length > 50) {
    showMessage('error', '姓名不能超过50个字符')
    return false
  }
  return true
}

const handleLogin = async () => {
  if (!loginForm.phone || !loginForm.password) {
    showMessage('warning', '请输入手机号和密码')
    return
  }

  if (!validatePhone(loginForm.phone)) return

  if (!tenantStore.hasTenant) {
    showMessage('error', '请先选择学校')
    router.push('/tenant-select')
    return
  }

  loading.value = true
  try {
    const success = await authStore.login(loginForm.phone, loginForm.password)

    if (success) {
      showMessage('success', '登录成功')

      if (loginForm.remember) {
        localStorage.setItem('remember_login', 'true')
      }

      const redirect = (route.query.redirect as string) || '/'
      router.push(redirect)
    } else {
      showMessage('error', '登录失败，请检查手机号和密码')
    }
  } catch (error) {
    console.error('Login error:', error)
    showMessage('error', resolveErrorMessage(error, '登录失败，请稍后重试'))
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!registerForm.phone) {
    showMessage('warning', '请输入手机号')
    return
  }
  if (!validatePhone(registerForm.phone)) return

  if (!registerForm.name) {
    showMessage('warning', '请输入真实姓名')
    return
  }
  if (!validateName(registerForm.name)) return

  if (!registerForm.password) {
    showMessage('warning', '请输入密码')
    return
  }
  if (!validatePassword(registerForm.password)) return

  if (registerForm.password !== registerForm.confirmPassword) {
    showMessage('error', '两次输入的密码不一致')
    return
  }

  if (!registerForm.agree) {
    showMessage('warning', '请阅读并同意服务条款')
    return
  }

  if (!tenantStore.hasTenant) {
    showMessage('error', '请先选择学校')
    router.push('/tenant-select')
    return
  }

  loading.value = true
  try {
    const registerData = {
      account: registerForm.phone,
      password: registerForm.password,
      name: registerForm.name,
      phone: registerForm.phone
    }

    const success = await authStore.register(registerData)

    if (success) {
      showMessage('success', '注册成功，请登录')
      switchTab(true)
      loginForm.phone = registerForm.phone
    } else {
      showMessage('error', '注册失败，请稍后重试')
    }
  } catch (error) {
    console.error('Register error:', error)
    showMessage('error', resolveErrorMessage(error, '注册失败，请稍后重试'))
  } finally {
    loading.value = false
  }
}

const handleForgotPassword = () => {
  showMessage('info', '请联系管理员重置密码')
}

onMounted(() => {
  if (!tenantStore.hasTenant) {
    router.push('/tenant-select')
  }
  startSpotlightRotation()
})

onBeforeUnmount(() => {
  stopSpotlightRotation()
})

const resetLoginForm = () => {
  loginForm.phone = ''
  loginForm.password = ''
  loginForm.remember = false
  showPassword.login = false
}

const resetRegisterForm = () => {
  registerForm.phone = ''
  registerForm.name = ''
  registerForm.password = ''
  registerForm.confirmPassword = ''
  showPassword.register = false
  registerForm.agree = false
}

const switchTab = (toLogin: boolean) => {
  isLogin.value = toLogin
  if (toLogin) {
    resetRegisterForm()
  } else {
    resetLoginForm()
  }
}

</script>

<style scoped>
.auth-shell {
  --bg: #f5f5f7;
  --panel-bg: #ffffff;
  --panel-border: rgba(15, 18, 23, 0.08);
  --input-bg: #ffffff;
  --input-border: rgba(15, 18, 23, 0.12);
  --input-text: #111217;
  --text-1: #0b0d12;
  --text-2: #4a5264;
  --text-3: #8a8f9f;
  --accent: #ff7a18;
  --accent-soft: rgba(255, 122, 24, 0.12);
  --ink: #0b0d12;
  min-height: 100vh;
  background: linear-gradient(180deg, #fbfbfc 0%, #f2f3f7 45%, #ffffff 100%);
  color: var(--text-1);
}

.auth-viewport {
  min-height: 100vh;
  display: flex;
}

.auth-showcase {
  flex: 0 0 42%;
  min-width: 300px;
  background: #0b0d12;
  color: #fff;
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.auth-showcase::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 30% 20%, rgba(255, 122, 24, 0.25), transparent 50%),
    radial-gradient(circle at 80% 60%, rgba(255, 255, 255, 0.12), transparent 60%);
  pointer-events: none;
}

.showcase-content {
  width: min(460px, 88%);
  display: flex;
  flex-direction: column;
  gap: 28px;
  position: relative;
  z-index: 1;
}

.showcase-visual {
  position: relative;
  width: 220px;
  height: 220px;
  margin: 0 auto;
  border-radius: 32px;
  background: #111217;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.visual-core {
  width: 110px;
  height: 110px;
  background: #ff7a18;
  border-radius: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 32px;
  color: #0b0d12;
  letter-spacing: 0.1em;
}

.visual-ring {
  position: absolute;
  border-radius: 32px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  animation: ring-spin 18s linear infinite;
}

.ring-primary {
  inset: 12px;
}

.ring-secondary {
  inset: -12px;
  animation-duration: 28s;
}

.visual-particle {
  position: absolute;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(255, 122, 24, 0.8));
  animation: particle-float 6s ease-in-out infinite;
}

.particle-one {
  top: 10%;
  left: 65%;
}

.particle-two {
  bottom: 12%;
  right: 18%;
  animation-delay: 1.8s;
}

.particle-three {
  top: 30%;
  left: 18%;
  animation-delay: 3.2s;
}

@keyframes ring-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes particle-float {
  0% {
    transform: translate3d(0, 0, 0);
    opacity: 0.4;
  }
  50% {
    transform: translate3d(6px, -12px, 0);
    opacity: 1;
  }
  100% {
    transform: translate3d(-8px, 10px, 0);
    opacity: 0.4;
  }
}

.eyebrow {
  letter-spacing: 0.25em;
  text-transform: uppercase;
  font-size: 12px;
  color: var(--text-3);
  margin: 0;
}

.dynamic-caption {
  margin: 0;
  font-size: 20px;
  line-height: 1.6;
  color: #fff;
}

.dynamic-caption-wrapper {
  position: relative;
  padding: 12px 16px;
  border-radius: 22px;
  overflow: hidden;
  background: rgba(11, 13, 18, 0.6);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 12px 30px rgba(0, 0, 0, 0.35);
}

.caption-gradient {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  opacity: 0.55;
}

.gradient-fill {
  width: 140%;
  height: 100%;
  background: linear-gradient(120deg, rgba(255, 255, 255, 0.2), rgba(255, 122, 24, 0.3), rgba(255, 255, 255, 0.2));
  transform: translateX(-110%);
  animation: caption-gradient-flow 1.1s ease forwards;
}

@keyframes caption-gradient-flow {
  0% {
    transform: translateX(-110%);
    opacity: 0;
  }
  40% {
    opacity: 0.8;
  }
  100% {
    transform: translateX(15%);
    opacity: 0;
  }
}

.spotlight-fade-enter-active,
.spotlight-fade-leave-active {
  transition: opacity 0.55s ease, transform 0.55s ease;
}

.spotlight-fade-enter-from,
.spotlight-fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.dynamic-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.chip {
  padding: 8px 18px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
  font-size: 12px;
  letter-spacing: 0.14em;
  color: rgba(255, 255, 255, 0.8);
}

.spotlight-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.spotlight-control {
  width: 36px;
  height: 6px;
  border-radius: 999px;
  background: rgba(118, 138, 163, 0.2);
  border: none;
  cursor: pointer;
  transition: background 0.25s ease, transform 0.25s ease;
}

.spotlight-control.active {
  background: linear-gradient(90deg, var(--accent), var(--accent));
  transform: scaleX(1.08);
}

.showcase-content h1 {
  font-size: clamp(32px, 3.5vw, 48px);
  margin: 0;
}

.auth-panel {
  flex: 1;
  position: relative;
  border-left: 1px solid rgba(15, 18, 23, 0.06);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(250, 250, 252, 0.9));
}

.form-scroll[data-scroll] {
  height: 100vh;
  overflow-y: auto;
  padding: 48px clamp(32px, 4vw, 72px);
}

.panel-inner {
  max-width: 520px;
  margin: 0 auto;
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: 28px;
  padding: clamp(28px, 4vw, 44px);
  box-shadow: 0 40px 90px rgba(12, 16, 32, 0.12);
}

.tenant-info {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 18px;
  border-bottom: 1px solid rgba(135, 147, 168, 0.2);
  margin-bottom: 32px;
}

.current-tenant {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tenant-label {
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 11px;
  color: var(--text-3);
}

.tenant-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-1);
}

.change-tenant-btn {
  padding: 10px 18px;
  border-radius: 999px;
  border: 1px solid rgba(15, 18, 23, 0.12);
  background: #fff;
  color: var(--text-2);
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease, background 0.2s ease;
}

.change-tenant-btn:hover {
  border-color: var(--accent);
  background: rgba(255, 122, 24, 0.08);
  transform: translateY(-1px);
}

.panel-head {
  display: flex;
  gap: 18px;
  align-items: center;
  justify-content: center;
}

.logo-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-hover) 100%);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-light);
  transition: transform var(--duration-base) var(--ease-out);
}

.logo:hover .logo-icon {
  transform: scale(1.05);
}

.auth-header {
  text-align: center;
  margin-bottom: var(--spacing-lg);
}

.auth-title {
  font-size: clamp(24px, 5vw, 28px);
  line-height: 1.3;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-xs) 0;
}

.auth-subtitle {
  font-size: clamp(14px, 3.5vw, 16px);
  line-height: 1.6;
  color: var(--color-text-secondary);
  margin: 0;
}

.tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 6px;
  background: rgba(245, 246, 250, 0.9);
  border-radius: 18px;
  margin-bottom: 28px;
  border: 1px solid rgba(15, 18, 23, 0.06);
}

.tab {
  position: relative;
  height: 46px;
  padding: 0 18px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-3);
  background-color: transparent;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab:hover {
  color: var(--color-text-primary);
  background-color: var(--color-bg-active);
}

.tab:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
  z-index: var(--z-base);
}

.tab.active {
  color: #fff;
  background: #0b0d12;
  box-shadow: 0 8px 20px rgba(11, 13, 18, 0.2);
}

.forms-container {
  position: relative;
  margin-bottom: var(--spacing-md);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.form-label {
  font-size: 13px;
  line-height: 1.45;
  font-weight: 600;
  color: var(--text-2);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.form-input {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  font-size: 15px;
  line-height: 1.5;
  color: var(--input-text);
  background-color: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: 14px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  outline: none;
}

.form-input::placeholder {
  color: rgba(15, 23, 42, 0.5);
}

.password-input-wrapper .form-input {
  padding-right: 44px;
}

.password-toggle {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 44px;
  height: 44px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: rgba(15, 23, 42, 0.55);
  cursor: pointer;
  border-radius: 12px;
  transition: color 0.2s ease, background 0.2s ease;
}

.password-toggle:hover {
  color: var(--accent);
  background-color: var(--accent-soft);
}

.password-toggle:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.checkbox-group {
  margin-top: calc(var(--spacing-xs) * -1);
}

.checkbox-wrapper {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-xs);
  cursor: pointer;
  user-select: none;
}

.checkbox {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.9);
  border: 1.5px solid rgba(120, 137, 172, 0.8);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0;
  margin-top: 2px;
  box-shadow: inset 0 1px 4px rgba(45, 64, 99, 0.15);
}

.checkbox:hover {
  border-color: var(--color-primary);
  background-color: var(--color-primary-light);
}

.checkbox:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.checkbox.checked {
  background: linear-gradient(120deg, #00b7ff, #7c4dff);
  border-color: transparent;
}

.check-icon {
  width: 14px;
  height: 14px;
  color: #0b1630;
  animation: checkmark 0.18s ease;
}

@keyframes checkmark {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.checkbox-label {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-2);
  flex: 1;
}

.btn {
  width: 100%;
  height: 50px;
  padding: 0 22px;
  font-size: 16px;
  line-height: 1.5;
  font-weight: 600;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-primary {
  color: #fff;
  background: #0b0d12;
  box-shadow: 0 12px 30px rgba(11, 13, 18, 0.25);
}

.btn-primary:hover:not(:disabled) {
  background-color: #1a1d24;
  box-shadow: 0 6px 18px rgba(11, 13, 18, 0.3);
  transform: translateY(-1px);
}

.btn-primary:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.btn-primary:active:not(:disabled) {
  background-color: #000;
  transform: translateY(0);
  box-shadow: 0 1px 4px rgba(11, 13, 18, 0.2);
}

.btn:disabled {
  background-color: var(--color-bg-active);
  color: var(--color-text-tertiary);
  cursor: not-allowed;
  box-shadow: none;
  opacity: 0.6;
}

.btn-text {
  display: inline-block;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: calc(var(--spacing-md) * -0.5);
}

.link {
  font-size: 14px;
  line-height: 1.5;
  color: var(--accent);
  text-decoration: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-weight: 500;
  transition: all var(--duration-fast) var(--ease-out);
  border-radius: 2px;
}

.link:hover {
  color: #0b0d12;
  text-decoration: underline;
}

.link:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.link-strong {
  font-weight: 600;
  font-size: 15px;
}

.switch-tips {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border-light);
}

.tips-text {
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-2);
}

.form-fade-enter-active,
.form-fade-leave-active {
  transition: all var(--duration-slow) var(--ease-out);
}

.form-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.form-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ===== 响应式适配 ===== */

/* 移动端 (<768px) */
@media (max-width: 767px) {
  .auth-container {
    padding: var(--spacing-sm);
  }
  
  .auth-card {
    padding: clamp(20px, 5vw, 24px);
  }
  
  .tenant-info {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }
  
  .change-tenant-btn {
    width: 100%;
  }
  
  .logo-icon {
    width: 56px;
    height: 56px;
  }
}

/* 平板 (768-1024px) */
@media (min-width: 768px) {
  .auth-container {
    padding: var(--spacing-md);
  }
  
  .auth-card {
    padding: 32px;
  }
}

/* 桌面 (>1024px) */
@media (min-width: 1024px) {
  .auth-container {
    padding: var(--spacing-lg);
  }
  
  .auth-card {
    padding: 40px;
  }
  
  .auth-card:hover {
    box-shadow: var(--shadow-strong);
  }
}

/* ===== 高对比度模式支持 ===== */
@media (prefers-contrast: high) {
  .auth-container {
    --color-border-base: #000000;
    --color-border-strong: #000000;
  }
  
  .form-input:focus {
    outline: 3px solid var(--color-primary);
    outline-offset: 2px;
  }
  
  .btn-primary {
    border: 2px solid var(--color-primary-active);
  }
}

/* ===== 打印样式 ===== */
@media print {
  .auth-container {
    background: white;
  }
  
  .auth-card {
    box-shadow: none;
    border: 1px solid #000;
  }
  
  .change-tenant-btn,
  .password-toggle {
    display: none;
  }
}
</style>