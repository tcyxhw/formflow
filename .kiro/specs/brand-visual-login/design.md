# Design Document: Brand Visual Login Page

## Overview

This design document provides the technical implementation details for redesigning the login and registration pages with a professional brand visual experience. The new design replaces the existing anthropomorphic mascot with a sophisticated SaaS-style split-layout featuring a deep, tech-focused left panel and a clean, minimal right panel for authentication.

The implementation focuses on creating an immersive brand experience through carefully crafted visual layers, subtle animations, and professional styling. The design follows modern SaaS product patterns commonly used by leading enterprise and AI platforms.

## Architecture

### System Architecture

The login page redesign follows a component-based architecture with clear separation between visual presentation and form functionality. The left panel handles brand expression and atmosphere, while the right panel focuses on authentication conversion. This separation ensures that visual enhancements do not interfere with the core login functionality.

The architecture supports smooth transitions between login and registration states while maintaining consistent branding across both views. The design is fully responsive and adapts gracefully to different screen sizes while preserving the split-layout aesthetic on desktop and transforming to a stacked layout on mobile devices.

### Component Structure

```
LoginView.vue (Main Page Container)
├── LeftPanel (Brand Visual Area - 55%)
│   ├── BackgroundLayer
│   │   ├── GradientBackground
│   │   ├── LightSpots (Blue & Purple)
│   │   └── TextureOverlay (Grid, Circles, Lines)
│   ├── ProductMockup (Center Floating Card)
│   │   ├── MockupHeader (Navigation bar)
│   │   ├── MockupSidebar (Menu items)
│   │   ├── MockupContent (Data modules, Chart, Status)
│   │   └── MockupFooter
│   ├── FloatingCards (3 Glass Cards)
│   │   ├── SmartAnalysisCard
│   │   ├── RealTimeSyncCard
│   │   └── TeamCollaborationCard
│   └── BrandMessaging (Bottom area)
│       ├── MainTitle
│       ├── Subtitle
│       └── FeatureHighlights
│
└── RightPanel (Form Area - 45%)
    ├── FormContainer
    │   ├── Logo
    │   ├── FormHeader (Title & Subtitle)
    │   ├── LoginForm / RegisterForm
    │   │   ├── AccountInput
    │   │   ├── PasswordInput
    │   │   ├── RememberCheckbox
    │   │   ├── SubmitButton
    │   │   └── FormFooter (Links)
    │   └── TenantInfo
```

### Data Flow

```
User Interaction
       │
       ▼
┌──────────────────┐
│ LoginView.vue    │ ←─ Tab switching, form submission, input events
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ LeftPanel        │ ←─ Receives isLogin prop for text updates
│ (Static Display) │    Handles mouse movement for parallax
└────────┬─────────┘
         │ (Mouse events)
         ▼
┌──────────────────┐
│ Parallax Handler │ ←─ Calculates offset based on mouse position
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ CSS Transforms   │ ←─ Applies transforms to layers for depth effect
└──────────────────┘

Form Flow:
┌──────────────────┐
│ RightPanel       │ ←─ Handles all form interactions
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Auth Store       │ ←─ Processes login/register requests
└──────────────────┘
```

## Components and Interfaces

### LoginView.vue Interface

```typescript
// LoginView.vue
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

const props = defineProps<{
  // No external props needed, manages internal state
}>()

const emit = defineEmits<{
  (e: 'login-success'): void
  (e: 'register-success'): void
}>()

// State
const isLogin = ref(true)
const loading = ref(false)
const mouseX = ref(0)
const mouseY = ref(0)

// Form data
const loginForm = reactive<LoginForm>({
  phone: '',
  password: '',
  remember: false
})

const registerForm = reactive<RegisterForm>({
  phone: '',
  name: '',
  password: '',
  confirmPassword: '',
  agree: false
})

// Computed text based on login state
const mainTitle = computed(() => 
  isLogin.value ? '欢迎回来，继续你的高效工作流' : '开启你的高效协作体验'
)

const subtitle = computed(() => 
  isLogin.value 
    ? '统一管理数据、任务与协作流程，让每一步都更流畅。'
    : '从注册开始，快速连接团队、任务与业务数据'
)

// Parallax effect
const parallaxOffset = computed(() => {
  const maxOffset = 8
  const x = (mouseX.value / window.innerWidth - 0.5) * maxOffset
  const y = (mouseY.value / window.innerHeight - 0.5) * maxOffset
  return { x, y }
})

const handleMouseMove = (event: MouseEvent) => {
  mouseX.value = event.clientX
  mouseY.value = event.clientY
}

// Methods
const switchTab = (toLogin: boolean) => {
  isLogin.value = toLogin
  // Reset forms as needed
}

const handleLogin = async () => { /* ... */ }
const handleRegister = async () => { /* ... */ }

// Lifecycle
onMounted(() => {
  window.addEventListener('mousemove', handleMouseMove)
})

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', handleMouseMove)
})
</script>

<template>
  <div class="auth-shell">
    <div class="auth-viewport">
      <!-- Left Panel: Brand Visual -->
      <aside class="auth-showcase" :style="{
        transform: `translate(${parallaxOffset.x * 0.3}px, ${parallaxOffset.y * 0.3}px)`
      }">
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
      
      <!-- Right Panel: Form -->
      <section class="auth-panel">
        <!-- Form content (existing) -->
      </section>
    </div>
  </div>
</template>
```

## Data Models

### Color Palette

```typescript
const colors = {
  left: {
    background: {
      start: '#0B1020',
      middle: '#111A35',
      end: '#1A2450'
    },
    accent: {
      blue: '#3B82F6',
      purple: '#8B5CF6'
    },
    text: {
      primary: '#F8FAFC',
      secondary: 'rgba(248, 250, 252, 0.72)'
    }
  },
  right: {
    background: '#FFFFFF',
    divider: '#E5E7EB',
    inputBorder: '#D1D5DB',
    text: '#111827'
  }
}
```

### Animation Config

```typescript
const animationConfig = {
  lightSpotDrift: {
    duration: '10s',
    easing: 'ease-in-out'
  },
  mockupFloat: {
    displacement: 8,
    duration: '6s',
    easing: 'ease-in-out'
  },
  cardFloat: {
    displacement: { min: 6, max: 10 },
    duration: { min: '4s', max: '7s' }
  },
  parallax: {
    maxOffset: 8,
    damping: 0.3
  }
}
```

## Correctness Properties

### Property 1: Layout Ratio Consistency

*For any* viewport width greater than 1024px, the left panel SHALL occupy 55% of the viewport width and the right panel SHALL occupy 45%.

**Validates: Requirement 1.1**

### Property 2: Color Scheme Application

*For any* rendered page, all left-side elements SHALL use colors from the left palette and all right-side elements SHALL use colors from the right palette.

**Validates: Requirements 2.1, 2.2, 8.1, 8.2**

### Property 3: Animation Continuity

*For any* animation cycle, the element SHALL return to its original position and the animation SHALL repeat smoothly without jumps or discontinuities.

**Validates: Requirements 6.1, 6.2, 6.3**

### Property 4: Text Content Switching

*For any* tab switch between login and registration, the main title and subtitle SHALL update to the corresponding values within 100 milliseconds.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 9.2**

### Property 5: Form Functionality Preservation

*For any* visual redesign, the login and registration forms SHALL continue to function correctly, including validation, submission, and error handling.

**Validates: Requirement 10.5**

## Error Handling

### Fallback States

If CSS animations are disabled or not supported by the browser, the design SHALL gracefully degrade to a static layout without breaking the user experience. The parallax effect SHALL be disabled on touch devices to prevent unwanted scrolling behavior.

### Responsive Behavior

On screens narrower than 1024px, the split layout SHALL transform into a stacked layout with the left panel appearing at the top and the right panel below. The animations MAY be simplified on mobile devices to improve performance and reduce battery consumption.

## Implementation Details

### HTML Structure

```html
<!-- Main Container -->
<div class="auth-shell">
  <div class="auth-viewport">
    
    <!-- Left Panel -->
    <aside class="auth-showcase">
      <div class="showcase-content">
        
        <!-- Background Layer -->
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
        <div class="floating-card card-smart-analysis">...</div>
        <div class="floating-card card-sync">...</div>
        <div class="floating-card card-team">...</div>
        
        <!-- Brand Messaging -->
        <div class="brand-messaging">
          <h1 class="main-title">...</h1>
          <p class="subtitle">...</p>
          <ul class="feature-list">...</ul>
        </div>
        
      </div>
    </aside>
    
    <!-- Right Panel -->
    <section class="auth-panel">...</section>
    
  </div>
</div>
```

### CSS Styling

```css
/* Main Layout */
.auth-shell {
  min-height: 100vh;
  background: #f5f5f7;
}

.auth-viewport {
  display: flex;
  min-height: 100vh;
}

/* Left Panel */
.auth-showcase {
  flex: 0 0 55%;
  position: relative;
  background: linear-gradient(180deg, #0B1020 0%, #111A35 50%, #1A2450 100%);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Background Gradient */
.bg-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, #0B1020 0%, #111A35 50%, #1A2450 100%);
}

/* Light Spots */
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
}

.purple-spot {
  width: 350px;
  height: 350px;
  background: #8B5CF6;
  bottom: -50px;
  left: 30%;
}

/* Background Texture */
.bg-texture {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px),
    radial-gradient(circle at 50% 50%, rgba(255,255,255,0.01) 0%, transparent 50%);
  background-size: 50px 50px, 50px 50px, 100% 100%;
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
  animation: float 6s ease-in-out infinite;
  z-index: 10;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
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

/* Card positions and animations */
.card-smart-analysis {
  top: -20px;
  left: -60px;
  animation: floatCard1 5s ease-in-out infinite;
}

.card-sync {
  top: 40%;
  right: -80px;
  animation: floatCard2 6s ease-in-out infinite 0.5s;
}

.card-team {
  bottom: -10px;
  left: -40px;
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
  bottom: 60px;
  left: 60px;
  right: 60px;
  color: #F8FAFC;
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

/* Right Panel */
.auth-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #FFFFFF;
  padding: 48px;
}

.form-scroll[data-scroll] {
  width: 100%;
  max-width: 420px;
}

/* Responsive */
@media (max-width: 1023px) {
  .auth-viewport {
    flex-direction: column;
  }
  
  .auth-showcase {
    flex: 0 0 320px;
  }
  
  .product-mockup {
    width: 360px;
    height: 240px;
    transform: scale(0.8);
  }
  
  .floating-card {
    transform: scale(0.85);
  }
  
  .brand-messaging {
    bottom: 20px;
    left: 40px;
    right: 40px;
  }
  
  .main-title {
    font-size: 22px;
  }
  
  .feature-list {
    flex-wrap: wrap;
    gap: 12px;
  }
}
```

### JavaScript Implementation

```typescript
// Parallax effect handler
const setupParallax = () => {
  const handleMouseMove = (event: MouseEvent) => {
    const x = (event.clientX / window.innerWidth - 0.5) * 2
    const y = (event.clientY / window.innerHeight - 0.5) * 2
    
    // Apply to showcase panel with damping
    const showcase = document.querySelector('.auth-showcase')
    if (showcase) {
      showcase.style.transform = `translate(${x * 5}px, ${y * 3}px)`
    }
    
    // Apply to floating cards with different intensities
    const cards = document.querySelectorAll('.floating-card')
    cards.forEach((card, index) => {
      const factor = (index + 1) * 2
      ;(card as HTMLElement).style.transform = 
        `translate(${x * factor}px, ${y * factor}px)`
    })
  }
  
  window.addEventListener('mousemove', handleMouseMove)
  
  return () => {
    window.removeEventListener('mousemove', handleMouseMove)
  }
}

// Light spot drift animation
const setupLightSpotAnimation = () => {
  const blueSpot = document.querySelector('.blue-spot')
  const purpleSpot = document.querySelector('.purple-spot')
  
  if (blueSpot) {
    blueSpot.animate([
      { transform: 'translate(0, 0)' },
      { transform: 'translate(20px, -20px)' },
      { transform: 'translate(-10px, 10px)' },
      { transform: 'translate(0, 0)' }
    ], {
      duration: 12000,
      iterations: Infinity,
      easing: 'ease-in-out'
    })
  }
  
  if (purpleSpot) {
    purpleSpot.animate([
      { transform: 'translate(0, 0)' },
      { transform: 'translate(-15px, 15px)' },
      { transform: 'translate(10px, -10px)' },
      { transform: 'translate(0, 0)' }
    ], {
      duration: 10000,
      iterations: Infinity,
      easing: 'ease-in-out'
    })
  }
}
```

## Performance Considerations

### GPU Acceleration

All animations use CSS transforms and opacity changes which are GPU-accelerated in modern browsers. The parallax effect uses transform translations rather than position changes to prevent layout thrashing. The backdrop-filter effects are applied sparingly to maintain performance.

### Animation Optimization

The light spot drift animation uses long durations (8-12 seconds) with subtle movements to minimize visual distraction while maintaining the atmospheric effect. The floating card animations use different durations and delays to create natural, non-repetitive movement patterns.

### Responsive Design

On mobile devices, the complex animations are simplified or disabled to reduce battery consumption and improve scrolling performance. The mockup and floating cards are scaled down to fit smaller screens while maintaining visual hierarchy.