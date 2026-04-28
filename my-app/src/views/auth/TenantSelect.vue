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
          <span class="search-icon-wrapper">
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35"/>
            </svg>
          </span>
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
:root {
  --brand: #2563eb;
  --brand-light: #3b82f6;
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-hover: #f1f5f9;
  --text: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --border: #e2e8f0;
  --border-light: #f1f5f9;
  --radius: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --ease: cubic-bezier(0.4, 0, 0.2, 1);
  --duration: 200ms;
}

@media (prefers-color-scheme: dark) {
  :root {
    --brand: #3b82f6;
    --brand-light: #60a5fa;
    --bg: #0f172a;
    --surface: #1e293b;
    --surface-hover: #334155;
    --text: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --border: #334155;
    --border-light: #1e293b;
  }
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.tenant-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--bg);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  font-size: 15px;
  line-height: 1.5;
  color: var(--text);
}

.tenant-wrapper {
  width: 100%;
  max-width: 420px;
}

.tenant-card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 40px 32px;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border);
}

.logo-wrapper {
  text-align: center;
  margin-bottom: 28px;
}

.logo {
  width: 56px;
  height: 56px;
  margin: 0 auto;
  background: var(--brand);
  border-radius: var(--radius);
}

.tenant-title {
  font-size: 22px;
  font-weight: 600;
  text-align: center;
  margin-bottom: 8px;
  color: var(--text);
}

.tenant-subtitle {
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: 28px;
  font-size: 14px;
}

.search-box {
  position: relative;
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
  padding: 12px 16px;
  padding-left: 40px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 14px;
  color: var(--text);
  transition: all var(--duration) var(--ease);
}

.search-input::placeholder {
  color: var(--text-muted);
}

.search-input:focus {
  outline: none;
  border-color: var(--brand);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.search-icon-wrapper {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
}

.search-icon {
  width: 18px;
  height: 18px;
  color: var(--text-muted);
}

.tenant-list-wrapper {
  max-height: 320px;
  overflow-y: auto;
  margin: 0 -4px;
  padding: 0 4px;
}

.tenant-list-wrapper::-webkit-scrollbar {
  width: 4px;
}

.tenant-list-wrapper::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 2px;
}

.tenant-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tenant-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 14px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--duration) var(--ease);
}

.tenant-item:hover {
  background: var(--surface-hover);
  border-color: var(--brand);
}

.tenant-item:active {
  transform: scale(0.99);
}

.tenant-item-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tenant-icon {
  width: 36px;
  height: 36px;
  background: var(--brand);
  color: white;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.tenant-name {
  font-weight: 500;
  color: var(--text);
  font-size: 14px;
}

.tenant-arrow {
  width: 16px;
  height: 16px;
  color: var(--text-muted);
  flex-shrink: 0;
}

.tenant-item:hover .tenant-arrow {
  color: var(--brand);
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 240px;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 2px solid var(--border);
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  width: 40px;
  height: 40px;
  margin-bottom: 12px;
  color: var(--text-muted);
}

.tenant-footer {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  font-size: 13px;
  color: var(--text-muted);
}

@media (max-width: 480px) {
  .tenant-card {
    padding: 28px 20px;
  }
}
</style>