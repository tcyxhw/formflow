<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'

interface Props {
  /**
   * Enable bonus interactions (typing hand movement, password toggle reaction)
   */
  enableBonusInteractions?: boolean
  /**
   * Custom eye socket boundary radius in pixels
   */
  eyeSocketRadius?: number
  /**
   * Custom pupil tracking speed multiplier (0.1 - 2.0)
   */
  trackingSpeed?: number
}

const props = withDefaults(defineProps<Props>(), {
  enableBonusInteractions: false,
  eyeSocketRadius: 8,
  trackingSpeed: 1.0
})

// Emits for parent component communication
const emit = defineEmits<{
  (e: 'state-change', state: 'idle' | 'account-focus' | 'password-focus'): void
}>()

// Refs for DOM element access
const characterContainer = ref<HTMLElement | null>(null)
const leftPupil = ref<HTMLElement | null>(null)
const rightPupil = ref<HTMLElement | null>(null)
const leftHand = ref<HTMLElement | null>(null)
const rightHand = ref<HTMLElement | null>(null)

// State management
const currentState = ref<'idle' | 'account-focus' | 'password-focus'>('idle')
const isTyping = ref(false)
const isPasswordVisible = ref(false)

// Character state classes
const characterClasses = computed(() => ({
  'is-hiding': currentState.value === 'password-focus',
  'has-focus': currentState.value !== 'idle',
  'bonus-enabled': props.enableBonusInteractions,
  'is-typing': isTyping.value,
  'password-visible': isPasswordVisible.value
}))

// State transitions
const transitionTo = (newState: 'idle' | 'account-focus' | 'password-focus') => {
  const validTransitions: Record<string, string[]> = {
    'idle': ['account-focus', 'password-focus'],
    'account-focus': ['idle', 'password-focus'],
    'password-focus': ['idle', 'account-focus']
  }

  if (validTransitions[currentState.value]?.includes(newState)) {
    currentState.value = newState
    emit('state-change', newState)
  }
}

// Mouse tracking
const handleMouseMove = (event: MouseEvent) => {
  if (currentState.value === 'password-focus') return

  if (leftPupil.value && rightPupil.value) {
    const leftSocket = leftPupil.value.parentElement?.getBoundingClientRect()
    const rightSocket = rightPupil.value.parentElement?.getBoundingClientRect()

    if (leftSocket && rightSocket) {
      const leftPosition = calculatePupilPosition(
        event.clientX, event.clientY,
        leftSocket.left + leftSocket.width / 2,
        leftSocket.top + leftSocket.height / 2
      )
      const rightPosition = calculatePupilPosition(
        event.clientX, event.clientY,
        rightSocket.left + rightSocket.width / 2,
        rightSocket.top + rightSocket.height / 2
      )

      updatePupilPosition(leftPupil.value, leftPosition)
      updatePupilPosition(rightPupil.value, rightPosition)
    }
  }
}

const calculatePupilPosition = (
  mouseX: number,
  mouseY: number,
  socketCenterX: number,
  socketCenterY: number
): { x: number; y: number } => {
  let offsetX = (mouseX - socketCenterX) * 0.1 * props.trackingSpeed
  let offsetY = (mouseY - socketCenterY) * 0.1 * props.trackingSpeed

  // Apply gaze bias toward input form during account focus
  if (currentState.value === 'account-focus') {
    offsetX = offsetX * 0.3 + 10 // Bias 10px right
  }

  // Constrain to eye socket radius
  const distance = Math.sqrt(offsetX * offsetX + offsetY * offsetY)
  if (distance > props.eyeSocketRadius) {
    const ratio = props.eyeSocketRadius / distance
    offsetX *= ratio
    offsetY *= ratio
  }

  return { x: offsetX, y: offsetY }
}

const updatePupilPosition = (
  pupil: HTMLElement,
  position: { x: number; y: number }
) => {
  pupil.style.transform = `translate(calc(-50% + ${position.x}px), calc(-50% + ${position.y}px))`
}

// Event handlers for form inputs
const handleAccountFocus = () => {
  transitionTo('account-focus')
}

const handlePasswordFocus = () => {
  transitionTo('password-focus')
}

const handlePasswordBlur = () => {
  transitionTo('idle')
}

const handleInput = () => {
  if (props.enableBonusInteractions) {
    isTyping.value = true
    setTimeout(() => {
      isTyping.value = false
    }, 300)
  }
}

const handlePasswordToggle = () => {
  if (props.enableBonusInteractions) {
    isPasswordVisible.value = !isPasswordVisible.value
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)

  // Attach listeners to form inputs
  const accountInput = document.querySelector<HTMLInputElement>('#account, #username, #email')
  const passwordInput = document.querySelector<HTMLInputElement>('#password')
  const passwordToggle = document.querySelector<HTMLButtonElement>('.password-toggle')

  accountInput?.addEventListener('focus', handleAccountFocus)
  passwordInput?.addEventListener('focus', handlePasswordFocus)
  passwordInput?.addEventListener('blur', handlePasswordBlur)
  accountInput?.addEventListener('input', handleInput)
  passwordToggle?.addEventListener('click', handlePasswordToggle)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)

  const accountInput = document.querySelector<HTMLInputElement>('#account, #username, #email')
  const passwordInput = document.querySelector<HTMLInputElement>('#password')
  const passwordToggle = document.querySelector<HTMLButtonElement>('.password-toggle')

  accountInput?.removeEventListener('focus', handleAccountFocus)
  passwordInput?.removeEventListener('focus', handlePasswordFocus)
  passwordInput?.removeEventListener('blur', handlePasswordBlur)
  accountInput?.removeEventListener('input', handleInput)
  passwordToggle?.removeEventListener('click', handlePasswordToggle)
})
</script>

<template>
  <div
    ref="characterContainer"
    class="miku-character"
    :class="characterClasses"
  >
    <!-- Layer 1: Body (Z-index: 1) -->
    <div class="miku-layer layer-body">
      <img
        src="/login/body-open.png"
        class="body-image body-open"
        alt="Miku with open eyes"
      />
      <img
        src="/login/body-closed.png"
        class="body-image body-closed"
        alt="Miku with closed eyes"
      />
    </div>

    <!-- Layer 2: Pupils (Z-index: 2) -->
    <div class="miku-layer layer-pupils">
      <div class="eye-socket left">
        <img
          ref="leftPupil"
          src="/login/pupil.png"
          class="pupil-image"
          alt="Left pupil"
        />
      </div>
      <div class="eye-socket right">
        <img
          ref="rightPupil"
          src="/login/pupil.png"
          class="pupil-image"
          alt="Right pupil"
        />
      </div>
    </div>

    <!-- Layer 3: Hands (Z-index: 3) -->
    <div class="miku-layer layer-hands">
      <img
        ref="leftHand"
        src="/login/hand.png"
        class="hand-image hand-left"
        alt="Left hand"
      />
      <img
        ref="rightHand"
        src="/login/hand.png"
        class="hand-image hand-right"
        alt="Right hand"
      />
    </div>
  </div>
</template>

<style scoped>
/* Character Container */
.miku-character {
  position: relative;
  width: 300px;
  height: 400px;
  /* Breathing animation */
  animation: breathe 3s ease-in-out infinite;
}

@keyframes breathe {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

/* Layer Base Styles */
.miku-layer {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

/* Layer 1: Body */
.layer-body {
  z-index: 1;
}

.body-image {
  position: absolute;
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: opacity 0.2s ease-in-out;
}

.body-open {
  opacity: 1;
}

.body-closed {
  opacity: 0;
}

/* Password focus state */
.miku-character.is-hiding .body-open {
  opacity: 0;
}

.miku-character.is-hiding .body-closed {
  opacity: 1;
}

/* Layer 2: Pupils */
.layer-pupils {
  z-index: 2;
}

.eye-socket {
  position: absolute;
  /* Position eye sockets based on character design */
  top: 85px;
  width: 50px;
  height: 50px;
  overflow: hidden;
}

.eye-socket.left {
  left: 85px;
}

.eye-socket.right {
  right: 85px;
}

.pupil-image {
  position: absolute;
  width: 28px;
  height: 28px;
  /* Center pupil in socket */
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  transition: transform 0.1s ease-out, opacity 0.1s ease-out;
}

/* Hide pupils in password focus */
.miku-character.is-hiding .pupil-image {
  opacity: 0;
}

/* Layer 3: Hands */
.layer-hands {
  z-index: 3;
}

.hand-image {
  position: absolute;
  width: 80px;
  height: 80px;
  bottom: 50px;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.hand-left {
  left: 30px;
  transform: translateY(50px); /* Hidden by default */
}

.hand-right {
  right: 30px;
  transform: translateY(50px) scaleX(-1); /* Hidden + mirrored */
}

/* Password focus: hands rise */
.miku-character.is-hiding .hand-left {
  transform: translateY(0);
}

.miku-character.is-hiding .hand-right {
  transform: translateY(0) scaleX(-1);
}

/* Bonus: Typing animation */
.miku-character.bonus-enabled.is-typing .hand-left {
  animation: typingHand 0.3s ease-in-out;
}

@keyframes typingHand {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

/* Bonus: Password visible partial state */
.miku-character.bonus-enabled.password-visible .hand-left {
  transform: translateY(25px);
}

.miku-character.bonus-enabled.password-visible .hand-right {
  transform: translateY(25px) scaleX(-1);
}
</style>