<!-- src/views/auth/TenantSelect.vue -->
<template>
  <div class="tenant-container">
    <div class="tenant-wrapper">
      <div class="tenant-card">
        <!-- Logo -->
        <div class="logo-wrapper">
          <div class="logo" role="img" aria-label="FormFlow Logo"></div>
        </div>
        
        <!-- Title -->
        <h1 class="tenant-title">选择您的学校</h1>
        <p class="tenant-subtitle">请从下方列表中选择您所在的学校或机构</p>
        
        <!-- Search -->
        <div class="search-box">
          <input 
            v-model="searchQuery"
            type="text"
            placeholder="搜索学校名称..."
            class="search-input"
            @input="handleSearch"
          />
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.35-4.35"/>
          </svg>
        </div>
        
        <!-- Tenant List -->
        <div class="tenant-list-wrapper">
          <div v-if="loading" class="loading-state">
            <div class="loading-spinner"></div>
            <p>加载中...</p>
          </div>
          
          <div v-else-if="filteredTenants.length === 0" class="empty-state">
            <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
            </svg>
            <p>{{ searchQuery ? '未找到匹配的学校' : '暂无可用学校' }}</p>
          </div>
          
          <div v-else class="tenant-list">
            <button
              v-for="tenant in filteredTenants"
              :key="tenant.id"
              class="tenant-item"
              @click="handleSelectTenant(tenant)"
              :aria-label="`选择 ${tenant.name}`"
            >
              <div class="tenant-item-content">
                <div class="tenant-icon">
                  {{ tenant.name.charAt(0) }}
                </div>
                <div class="tenant-info">
                  <div class="tenant-name">{{ tenant.name }}</div>
                </div>
              </div>
              <svg class="tenant-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- Footer -->
        <div class="tenant-footer">
          <p>找不到您的学校？请联系管理员</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useTenantStore } from '@/stores/tenant'
import type { Tenant } from '@/types/tenant'

const router = useRouter()
const tenantStore = useTenantStore()

// 状态
const searchQuery = ref('')
const loading = computed(() => tenantStore.loading)
const tenants = computed(() => tenantStore.tenantList)

// 搜索过滤
const filteredTenants = computed(() => {
  if (!searchQuery.value) {
    return tenants.value
  }
  
  const query = searchQuery.value.toLowerCase()
  return tenants.value.filter(tenant => 
    tenant.name.toLowerCase().includes(query)
  )
})

// 搜索处理（可以添加防抖）
const handleSearch = () => {
  // 搜索逻辑已通过computed实现
}

// 选择租户
const handleSelectTenant = (tenant: Tenant) => {
  tenantStore.selectTenant(tenant)
  ElMessage.success(`已选择：${tenant.name}`)
  
  // 跳转到登录页
  router.push('/login')
}

// 初始化
onMounted(async () => {
  // 如果已有租户信息，验证是否有效
  if (tenantStore.hasTenant) {
    const valid = await tenantStore.validateCurrentTenant()
    if (valid) {
      // 租户有效，直接跳转到登录页
      router.push('/login')
      return
    }
  }
  
  // 加载租户列表
  const success = await tenantStore.fetchTenantList()
  console.log("获取到的租户的信息：",success);
  
  if (!success) {
    ElMessage.error('获取学校列表失败，请刷新重试')
  }
})
</script>

<style scoped>
/* Design Tokens */
:root {
  /* Colors - Light Theme */
  --brand: hsl(211, 100%, 50%);
  --brand-hover: hsl(211, 100%, 45%);
  --brand-light: hsla(211, 100%, 50%, 0.1);
  --accent: hsl(340, 82%, 52%);
  --bg: hsl(0, 0%, 100%);
  --surface: hsl(0, 0%, 98%);
  --surface-hover: hsl(0, 0%, 96%);
  --muted: hsl(210, 20%, 96%);
  --text: hsl(222, 22%, 5%);
  --text-secondary: hsl(220, 13%, 45%);
  --border: hsla(0, 0%, 0%, 0.08);
  
  /* Radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px hsla(0, 0%, 0%, 0.06);
  --shadow-md: 0 6px 16px hsla(0, 0%, 0%, 0.08);
  --shadow-lg: 0 12px 32px hsla(0, 0%, 0%, 0.12);
  
  /* Animation */
  --ease-out: cubic-bezier(0.2, 0.8, 0.2, 1);
  --dur-fast: 180ms;
  --dur: 220ms;
  --dur-slow: 320ms;
  
  /* Spacing */
  --space-1: 8px;
  --space-2: 16px;
  --space-3: 24px;
  --space-4: 32px;
  --space-5: 40px;
  --space-6: 48px;
}

@media (prefers-color-scheme: dark) {
  :root {
    --brand: hsl(211, 100%, 58%);
    --brand-hover: hsl(211, 100%, 63%);
    --brand-light: hsla(211, 100%, 58%, 0.15);
    --accent: hsl(340, 82%, 60%);
    --bg: hsl(222, 22%, 8%);
    --surface: hsl(222, 22%, 12%);
    --surface-hover: hsl(222, 22%, 16%);
    --muted: hsl(222, 20%, 18%);
    --text: hsl(210, 20%, 98%);
    --text-secondary: hsl(220, 10%, 65%);
    --border: hsla(0, 0%, 100%, 0.16);
  }
}

/* Base */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* Container */
.tenant-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-3);
  background: var(--bg);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  font-size: clamp(15px, 2vw, 18px);
  line-height: 1.6;
  color: var(--text);
  transition: background-color var(--dur) var(--ease-out);
}

.tenant-wrapper {
  width: clamp(320px, 90vw, 520px);
  animation: fadeInUp var(--dur-slow) var(--ease-out);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tenant-card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border);
}

/* Logo */
.logo-wrapper {
  text-align: center;
  margin-bottom: var(--space-4);
}

.logo {
  width: 64px;
  height: 64px;
  margin: 0 auto;
  background: linear-gradient(135deg, var(--brand), var(--accent));
  border-radius: var(--radius-md);
}

/* Typography */
.tenant-title {
  font-size: clamp(24px, 3.5vw, 32px);
  font-weight: 700;
  letter-spacing: -0.02em;
  text-align: center;
  margin-bottom: var(--space-1);
}

.tenant-subtitle {
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: var(--space-4);
  font-size: clamp(14px, 1.8vw, 16px);
}

/* Search Box */
.search-box {
  position: relative;
  margin-bottom: var(--space-3);
}

.search-input {
  width: 100%;
  padding: var(--space-2);
  padding-left: var(--space-6);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-size: clamp(15px, 2vw, 16px);
  color: var(--text);
  transition: all var(--dur-fast) var(--ease-out);
  min-height: 44px;
}

.search-input::placeholder {
  color: var(--text-secondary);
  opacity: 0.6;
}

.search-input:hover {
  border-color: var(--text-secondary);
}

.search-input:focus {
  outline: none;
  border-color: var(--brand);
  box-shadow: 0 0 0 3px var(--brand-light);
}

.search-icon {
  position: absolute;
  left: var(--space-2);
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: var(--text-secondary);
  pointer-events: none;
}

/* Tenant List */
.tenant-list-wrapper {
  min-height: 300px;
  max-height: 400px;
  overflow-y: auto;
  margin: 0 calc(-1 * var(--space-2));
  padding: 0 var(--space-2);
}

.tenant-list-wrapper::-webkit-scrollbar {
  width: 6px;
}

.tenant-list-wrapper::-webkit-scrollbar-track {
  background: transparent;
}

.tenant-list-wrapper::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 3px;
}

.tenant-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.tenant-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: var(--space-2);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease-out);
  min-height: 56px;
}

.tenant-item:hover {
  background: var(--surface-hover);
  border-color: var(--brand);
  transform: translateX(4px);
}

.tenant-item:focus-visible {
  outline: 2px solid var(--brand);
  outline-offset: 2px;
}

.tenant-item:active {
  transform: translateX(2px);
}

.tenant-item-content {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.tenant-icon {
  width: 40px;
  height: 40px;
  background: var(--brand-light);
  color: var(--brand);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 18px;
}

.tenant-name {
  font-weight: 500;
  color: var(--text);
}

.tenant-arrow {
  width: 20px;
  height: 20px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

/* States */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  width: 48px;
  height: 48px;
  margin-bottom: var(--space-2);
  opacity: 0.5;
}

/* Footer */
.tenant-footer {
  text-align: center;
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--border);
  font-size: clamp(13px, 1.6vw, 14px);
  color: var(--text-secondary);
}

/* Responsive */
@media (max-width: 480px) {
  .tenant-card {
    padding: var(--space-4);
  }
}

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
</style>