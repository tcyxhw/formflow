<template>
  <div class="auth-shell">
    <div class="auth-viewport">
      <aside class="auth-showcase" aria-hidden="true">
        <div class="showcase-content">
          <div class="showcase-visual" role="img" aria-label="AI助手形象">
            <!-- SVG Character - 可爱极简风格 -->
            <svg class="character-svg" viewBox="0 0 80 100" fill="none" stroke="currentColor" stroke-width="1.2">
              <!-- 头部 - 圆润轮廓 -->
              <ellipse cx="40" cy="26" rx="18" ry="20" class="head-shape" />
              <!-- 眼睛 - 大眼睛更可爱 -->
              <g class="character-eyes" :class="{ 'eyes-hidden': passwordFocused }">
                <circle 
                  class="eye-left" 
                  :cx="33 + eyeOffset.leftX" 
                  :cy="24 + eyeOffset.leftY" 
                  r="3.5" 
                  fill="#ff7a18" 
                />
                <circle 
                  class="eye-right" 
                  :cx="47 + eyeOffset.rightX" 
                  :cy="24 + eyeOffset.rightY" 
                  r="3.5" 
                  fill="#ff7a18" 
                />
                <!-- 眼睛高光 -->
                <circle class="eye-shine" cx="31" cy="22" r="1" fill="white" />
                <circle class="eye-shine" cx="45" cy="22" r="1" fill="white" />
              </g>
              <!-- 身体 - 圆润水滴形 -->
              <path d="M22 48 Q40 52 58 48 L56 75 Q40 82 24 75 Z" class="body-shape" />
              <!-- 手臂 - 举起的小手 -->
              <path d="M22 52 Q10 58 12 70" class="arm-left" />
              <path d="M58 52 Q70 58 68 70" class="arm-right" />
              <!-- 手部 - 圆润小球 -->
              <circle class="hand-left" cx="12" cy="70" r="4" fill="currentColor" />
              <circle class="hand-right" cx="68" cy="70" r="4" fill="currentColor" />
            </svg>

            <!-- 密码遮挡遮罩 -->
            <div class="eye-overlay" :class="{ 'overlay-hidden': !passwordFocused }"></div>
          </div>
          <p class="eyebrow">Quantum Access Deck</p>
          <div class="caption-wrapper">
            <p class="dynamic-caption">{{ captionText }}</p>
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
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
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
const passwordFocused = ref(false)

// 眼睛视差跟踪
const eyeOffset = reactive({ leftX: 0, leftY: 0, rightX: 0, rightY: 0 })
let mouseX = 0
let mouseY = 0
let rafId: number | null = null

const MAX_OFFSET = 1.5
const EYE_LEFT_BASE = { x: 34, y: 20 }
const EYE_RIGHT_BASE = { x: 46, y: 20 }

function updateEyeParallax() {
  const viewportCenter = { x: window.innerWidth / 2, y: window.innerHeight / 2 }
  const deltaX = (mouseX - viewportCenter.x) / viewportCenter.x
  const deltaY = (mouseY - viewportCenter.y) / viewportCenter.y
  
  eyeOffset.leftX = deltaX * MAX_OFFSET
  eyeOffset.leftY = deltaY * MAX_OFFSET * 0.5
  eyeOffset.rightX = deltaX * MAX_OFFSET
  eyeOffset.rightY = deltaY * MAX_OFFSET * 0.5
  
  rafId = requestAnimationFrame(updateEyeParallax)
}

function onMouseMove(event: MouseEvent) {
  mouseX = event.clientX
  mouseY = event.clientY
}

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

const captionIndex = ref(0)
let spotlightTimer: number | null = null

// Character caption text with fade effect
const captionText = ref(spotlightMessages[0])

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

// Watch for password field focus state
watch(() => showPassword.login, (newVal) => {
  // If password is shown, eye is blocked
  passwordFocused.value = !newVal
})

onMounted(() => {
  if (!tenantStore.hasTenant) {
    router.push('/tenant-select')
  }
  startSpotlightRotation()
  window.addEventListener('mousemove', onMouseMove)
  rafId = requestAnimationFrame(updateEyeParallax)
})

onBeforeUnmount(() => {
  stopSpotlightRotation()
  window.removeEventListener('mousemove', onMouseMove)
  if (rafId) cancelAnimationFrame(rafId)
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
  /* Diagonal cut background */
  clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%);
}

/* Background gradient for diagonal cut effect */
.auth-showcase::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    linear-gradient(160deg, #0b0d12 0%, #0b0d12 80%, #1a1d24 100%);
  pointer-events: none;
  z-index: 0;
}

.showcase-content {
  width: min(460px, 88%);
  display: flex;
  flex-direction: column;
  gap: 24px;
  position: relative;
  z-index: 1;
}

.showcase-visual {
  position: relative;
  width: 180px;
  height: 220px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* SVG Character Styles */
.character-svg {
  width: 100%;
  height: 100%;
  color: rgba(255, 255, 255, 0.9);
  stroke-linecap: round;
  stroke-linejoin: round;
  filter: drop-shadow(0 12px 24px rgba(0, 0, 0, 0.5));
}

.head-shape {
  stroke: rgba(255, 255, 255, 0.7);
  stroke-width: 1.5;
}

.body-shape {
  stroke: rgba(255, 255, 255, 0.6);
  stroke-width: 1.5;
}

.arm-left,
.arm-right {
  stroke: rgba(255, 255, 255, 0.5);
  stroke-width: 1.5;
  stroke-linecap: round;
}

.character-eyes {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.eyes-hidden {
  opacity: 0;
  transform: scale(0.8);
}

.eye-left,
.eye-right {
  fill: #ff7a18;
  filter: drop-shadow(0 0 8px rgba(255, 122, 24, 0.9));
}

.eye-shine {
  fill: white;
  opacity: 0.8;
}

.hand-left,
.hand-right {
  fill: rgba(255, 255, 255, 0.7);
  transform-origin: center;
}

/* Eye Overlay */
.eye-overlay {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 36px;
  height: 18px;
  background: rgba(11, 13, 18, 0.95);
  border-radius: 3px;
  transition: opacity 0.2s ease, transform 0.2s ease;
  z-index: 2;
}

.overlay-hidden {
  opacity: 0;
  transform: translateX(-50%) translateY(-8px);
}

/* Parallax Animation - 悬浮呼吸动画 - 大幅度 */
@keyframes float {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  20% { transform: translate(-4px, -12px) rotate(-2deg); }
  40% { transform: translate(4px, -18px) rotate(2deg); }
  60% { transform: translate(-4px, -12px) rotate(-2deg); }
  80% { transform: translate(4px, -6px) rotate(1deg); }
}

@keyframes breathe {
  0%, 100% { opacity: 0.9; }
  50% { opacity: 1; }
}

@keyframes blink {
  0%, 90%, 100% { transform: scaleY(1); }
  95% { transform: scaleY(0.1); }
}

.character-svg {
  animation: float 6s ease-in-out infinite, breathe 3s ease-in-out infinite;
}

.character-eyes {
  animation: blink 4s ease-in-out infinite;
  transform-origin: center 24px;
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

/* Caption Styles */
.caption-wrapper {
  padding-left: 4px;
}

.dynamic-caption {
  margin: 0;
  font-size: 18px;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 300;
  text-align: left;
  letter-spacing: 0.02em;
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
  border-radius: 4px;
  padding: clamp(28px, 4vw, 44px);
  box-shadow: 0 40px 90px rgba(12, 16, 32, 0.12);
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
</style>