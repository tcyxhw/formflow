<template>
  <div class="auth-shell">
    <div class="auth-viewport">
      <!-- Left Panel: Brand Visual -->
      <aside class="auth-showcase" aria-hidden="true" :style="parallaxStyle">
        <div class="showcase-content">
          <!-- Background Layers -->
          <div class="bg-gradient"></div>
          <div class="bg-light-spot blue-spot"></div>
          <div class="bg-light-spot purple-spot"></div>
          <div class="bg-texture"></div>
          
          <!-- Product Mockup -->
          <div class="product-mockup">
            <div class="mockup-header">
              <div class="mockup-logo"></div>
              <div class="mockup-nav">
                <span class="nav-item active"></span>
                <span class="nav-item"></span>
                <span class="nav-item"></span>
              </div>
            </div>
            <div class="mockup-body">
              <div class="mockup-sidebar">
                <div class="menu-item"></div>
                <div class="menu-item"></div>
                <div class="menu-item"></div>
                <div class="menu-item"></div>
              </div>
              <div class="mockup-main">
                <div class="data-card"></div>
                <div class="chart-area"></div>
                <div class="status-panel"></div>
              </div>
            </div>
          </div>
          
          <!-- Floating Cards -->
          <div class="floating-card card-smart-analysis">
            <div class="card-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
              </svg>
            </div>
            <div class="card-content">
              <span class="card-title">智能分析</span>
              <span class="card-subtitle">自动提取关键数据</span>
            </div>
          </div>
          
          <div class="floating-card card-sync">
            <div class="card-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 4v6h-6M1 20v-6h6"/>
                <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
              </svg>
            </div>
            <div class="card-content">
              <span class="card-title">实时同步</span>
              <span class="card-subtitle">跨端数据即时更新</span>
            </div>
          </div>
          
          <div class="floating-card card-team">
            <div class="card-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
              </svg>
            </div>
            <div class="card-content">
              <span class="card-title">团队协作</span>
              <span class="card-subtitle">高效共享与管理</span>
            </div>
          </div>
          
          <!-- Brand Messaging -->
          <div class="brand-messaging">
            <h1 class="main-title">{{ mainTitle }}</h1>
            <p class="subtitle">{{ subtitle }}</p>
            <ul class="feature-list">
              <li>智能处理任务</li>
              <li>实时同步数据</li>
              <li>多端无缝协作</li>
            </ul>
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
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
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

// 当前租户名称
const currentTenantName = computed(() => tenantStore.currentTenant?.name || '未选择学校')

const showPassword = reactive({
  login: false,
  register: false,
  confirm: false
})

const isLogin = ref(true)
const loading = ref(false)
const passwordFocused = ref(false)

// Parallax effect for brand visual
let mouseX = 0
let mouseY = 0

function onMouseMove(event: MouseEvent) {
  mouseX = event.clientX
  mouseY = event.clientY
}

const parallaxStyle = computed(() => {
  const maxOffset = 8
  const x = ((mouseX / window.innerWidth) - 0.5) * maxOffset
  const y = ((mouseY / window.innerHeight) - 0.5) * maxOffset
  return {
    transform: `translate(${x * 0.3}px, ${y * 0.3}px)`
  }
})

// Dynamic text based on login state
const mainTitle = computed(() => 
  isLogin.value ? '欢迎回来，继续你的高效工作流' : '开启你的高效协作体验'
)

const subtitle = computed(() => 
  isLogin.value 
    ? '统一管理数据、任务与协作流程，让每一步都更流畅。'
    : '从注册开始，快速连接团队、任务与业务数据'
)

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
    captionIndex.value = (captionIndex.value + 1) % spotlightMessages.length
    captionText.value = spotlightMessages[captionIndex.value]
  }, 4200)
}

const stopSpotlightRotation = () => {
  if (spotlightTimer === null) return
  window.clearInterval(spotlightTimer)
  spotlightTimer = null
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

const switchTab = (toLogin: boolean) => {
  isLogin.value = toLogin
  if (toLogin) {
    resetRegisterForm()
  } else {
    resetLoginForm()
  }
}

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

</script>

<style>
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

/* Left Panel: Brand Visual Area */
.auth-showcase {
  flex: 0 0 55%;
  min-width: 400px;
  background: linear-gradient(180deg, #0B1020 0%, #111A35 50%, #1A2450 100%);
  color: #fff;
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.showcase-content {
  width: min(520px, 90%);
  display: flex;
  flex-direction: column;
  gap: 32px;
  position: relative;
  z-index: 1;
}

/* Background Layers */
.bg-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, #0B1020 0%, #111A35 50%, #1A2450 100%);
  z-index: 0;
}

.bg-light-spot {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.4;
  animation: drift 10s ease-in-out infinite;
}

.blue-spot {
  width: 400px;
  height: 400px;
  background: #3B82F6;
  top: -100px;
  left: -50px;
  animation-delay: 0s;
}

.purple-spot {
  width: 350px;
  height: 350px;
  background: #8B5CF6;
  bottom: -50px;
  left: 30%;
  animation-delay: -2s;
}

@keyframes drift {
  0%, 100% { transform: translate(0, 0); }
  33% { transform: translate(20px, -15px); }
  66% { transform: translate(-10px, 10px); }
}

.bg-texture {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px),
    radial-gradient(circle at 50% 50%, rgba(255,255,255,0.01) 0%, transparent 50%);
  background-size: 50px 50px, 50px 50px, 100% 100%;
  z-index: 1;
}

/* Product Mockup */
.product-mockup {
  position: relative;
  width: 480px;
  height: 320px;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.05);
  animation: floatMockup 6s ease-in-out infinite;
  z-index: 10;
  overflow: hidden;
}

@keyframes floatMockup {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.mockup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.mockup-logo {
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #3B82F6, #8B5CF6);
  border-radius: 6px;
}

.mockup-nav {
  display: flex;
  gap: 8px;
}

.mockup-nav .nav-item {
  width: 60px;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.mockup-nav .nav-item.active {
  background: rgba(59, 130, 246, 0.5);
  width: 40px;
}

.mockup-body {
  display: flex;
  height: calc(100% - 48px);
}

.mockup-sidebar {
  width: 60px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-right: 1px solid rgba(255, 255, 255, 0.05);
}

.mockup-sidebar .menu-item {
  height: 32px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
}

.mockup-main {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.data-card {
  height: 60px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 10px;
}

.chart-area {
  flex: 1;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  background-image: linear-gradient(
    to top,
    rgba(59, 130, 246, 0.1) 0%,
    transparent 100%
  );
}

.status-panel {
  height: 40px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
}

/* Floating Cards */
.floating-card {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: #F8FAFC;
  z-index: 20;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.card-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  color: #3B82F6;
  flex-shrink: 0;
}

.card-icon svg {
  width: 18px;
  height: 18px;
}

.card-content {
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.3;
}

.card-subtitle {
  font-size: 11px;
  color: rgba(248, 250, 252, 0.6);
  line-height: 1.3;
}

.card-smart-analysis {
  top: -20px;
  left: -80px;
  animation: floatCard1 5s ease-in-out infinite;
}

.card-sync {
  top: 35%;
  right: -100px;
  animation: floatCard2 6s ease-in-out infinite 0.5s;
}

.card-team {
  bottom: -10px;
  left: -60px;
  animation: floatCard3 7s ease-in-out infinite 1s;
}

@keyframes floatCard1 {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

@keyframes floatCard2 {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes floatCard3 {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

/* Brand Messaging */
.brand-messaging {
  position: absolute;
  bottom: 40px;
  left: 0;
  right: 0;
  color: #F8FAFC;
  text-align: left;
}

.main-title {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.3;
  margin: 0 0 12px 0;
  letter-spacing: -0.02em;
}

.subtitle {
  font-size: 15px;
  line-height: 1.6;
  color: rgba(248, 250, 252, 0.72);
  margin: 0 0 20px 0;
}

.feature-list {
  display: flex;
  gap: 24px;
  list-style: none;
  padding: 0;
  margin: 0;
}

.feature-list li {
  font-size: 13px;
  color: rgba(248, 250, 252, 0.8);
  display: flex;
  align-items: center;
  gap: 6px;
}

.feature-list li::before {
  content: '';
  width: 6px;
  height: 6px;
  background: #3B82F6;
  border-radius: 50%;
}

/* Eyebrow */
.eyebrow {
  letter-spacing: 0.25em;
  text-transform: uppercase;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
  text-align: left;
}

.auth-panel {
  flex: 1;
  position: relative;
  background: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-scroll[data-scroll] {
  width: 100%;
  max-width: 420px;
  padding: 48px 32px;
}

.panel-inner {
  width: 100%;
}

.tenant-info {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 16px;
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
  padding: 8px 16px;
  border-radius: 4px;
  border: 1px solid rgba(15, 18, 23, 0.12);
  background: transparent;
  color: var(--text-2);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
}

.change-tenant-btn:hover {
  border-color: var(--text-2);
  background: rgba(15, 18, 23, 0.04);
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
  gap: 0;
  margin-bottom: 28px;
  background: rgba(245, 246, 250, 0.9);
  border-radius: 2px;
  border: 1px solid rgba(15, 18, 23, 0.06);
  padding: 1px;
}

.tab {
  position: relative;
  height: 44px;
  padding: 0 18px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-3);
  background-color: transparent;
  border: none;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab:hover {
  color: var(--text-1);
  background-color: rgba(15, 18, 23, 0.04);
}

.tab:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
  z-index: var(--z-base);
}

.tab.active {
  color: #fff;
  background: #0b0d12;
  box-shadow: none;
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
  gap: 6px;
}

.form-label {
  font-size: 12px;
  line-height: 1.4;
  font-weight: 500;
  color: var(--text-3);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.form-input {
  width: 100%;
  height: 44px;
  padding: 0 14px;
  font-size: 15px;
  line-height: 1.5;
  color: var(--input-text);
  background-color: var(--input-bg);
  border: none;
  border-bottom: 1px solid var(--input-border);
  border-radius: 2px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  outline: none;
}

.form-input::placeholder {
  color: rgba(15, 23, 42, 0.4);
}

.form-input:focus {
  border-bottom-color: var(--accent);
  box-shadow: 0 2px 0 -1px var(--accent-soft);
}

.password-input-wrapper {
  position: relative;
}

.password-input-wrapper .form-input {
  padding-right: 44px;
}

.password-toggle {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--text-3);
  cursor: pointer;
  border-radius: 2px;
  transition: color 0.2s ease, background 0.2s ease;
}

.password-toggle:hover {
  color: var(--accent);
  background-color: var(--accent-soft);
}

.password-toggle:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.checkbox-group {
  margin-top: calc(var(--spacing-xs) * -1);
}

.checkbox-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}

.checkbox {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  border: 1px solid var(--text-3);
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0;
  margin-top: 2px;
}

.checkbox:hover {
  border-color: var(--accent);
}

.checkbox:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.checkbox.checked {
  background: var(--accent);
  border-color: var(--accent);
}

.check-icon {
  width: 12px;
  height: 12px;
  color: #fff;
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
  height: 46px;
  padding: 0 22px;
  font-size: 15px;
  line-height: 1.5;
  font-weight: 600;
  border: none;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-primary {
  color: #fff;
  background: #0b0d12;
  box-shadow: 0 8px 24px rgba(11, 13, 18, 0.25);
}

.btn-primary:hover:not(:disabled) {
  background-color: #1a1d24;
  box-shadow: 0 4px 16px rgba(11, 13, 18, 0.3);
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
  background-color: rgba(15, 18, 23, 0.06);
  color: var(--text-3);
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
  color: var(--text-3);
  text-decoration: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-weight: 500;
  transition: all 0.2s ease;
  border-radius: 2px;
}

.link:hover {
  color: var(--accent);
  background-color: var(--accent-soft);
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
  border-top: 1px solid rgba(135, 147, 168, 0.2);
}

.tips-text {
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-3);
}

.form-fade-enter-active,
.form-fade-leave-active {
  transition: all 0.3s ease;
}

.form-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.form-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ===== 响应式适配 ===== */

/* 移动端 (<768px) */
@media (max-width: 767px) {
  .auth-shell {
    flex-direction: column;
  }

  .auth-showcase {
    flex: 0 0 auto;
    height: 220px;
  }

  .form-scroll[data-scroll] {
    padding: 32px 24px;
  }

  .panel-inner {
    padding: clamp(24px, 5vw, 32px);
  }
}

/* 平板 (768-1024px) */
@media (min-width: 768px) {
  .panel-inner {
    padding: 36px;
  }
}

/* 桌面 (>1024px) */
@media (min-width: 1024px) {
  .panel-inner {
    padding: 44px;
  }
}

/* ===== 高对比度模式支持 ===== */
@media (prefers-contrast: high) {
  .form-input:focus {
    outline: 2px solid var(--accent);
    outline-offset: 1px;
  }

  .btn-primary {
    border: 2px solid var(--accent);
  }
}

/* ===== 打印样式 ===== */
@media print {
  .auth-shell {
    background: white;
  }

  .panel-inner {
    box-shadow: none;
    border: 1px solid #000;
  }

  .change-tenant-btn,
  .password-toggle,
  .character-svg {
    display: none;
  }
}

/* ===== Responsive Design ===== */
@media (max-width: 1023px) {
  .auth-viewport {
    flex-direction: column;
  }
  
  .auth-showcase {
    flex: 0 0 280px;
    min-width: 100%;
  }
  
  .product-mockup {
    width: 360px;
    height: 240px;
    transform: scale(0.85);
  }
  
  .floating-card {
    transform: scale(0.85);
  }
  
  .card-smart-analysis {
    left: -40px;
  }
  
  .card-sync {
    right: -60px;
  }
  
  .card-team {
    left: -30px;
  }
  
  .brand-messaging {
    bottom: 16px;
  }
  
  .main-title {
    font-size: 22px;
  }
  
  .subtitle {
    font-size: 13px;
    margin-bottom: 16px;
  }
  
  .feature-list {
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .auth-panel {
    padding: 32px 24px;
  }
}
</style>