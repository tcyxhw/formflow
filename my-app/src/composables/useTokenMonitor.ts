// src/composables/useTokenMonitor.ts
import { useAuthStore } from '@/stores/auth'
import { computed } from 'vue'

export function useTokenMonitor() {
  const authStore = useAuthStore()
  
  // 计算令牌剩余时间
  const tokenTimeRemaining = computed(() => {
    if (!authStore.tokenExpiry) return 0
    return Math.max(0, authStore.tokenExpiry - Date.now())
  })
  
  // 判断令牌是否即将过期（剩余时间少于10分钟）
  const isTokenExpiringSoon = computed(() => {
    return tokenTimeRemaining.value > 0 && tokenTimeRemaining.value < 10 * 60 * 1000
  })
  
  // 格式化剩余时间
  const formattedTimeRemaining = computed(() => {
    const remaining = tokenTimeRemaining.value
    if (remaining <= 0) return '已过期'
    
    const hours = Math.floor(remaining / (60 * 60 * 1000))
    const minutes = Math.floor((remaining % (60 * 60 * 1000)) / (60 * 1000))
    
    if (hours > 0) {
      return `${hours}小时${minutes}分钟`
    }
    return `${minutes}分钟`
  })
  
  return {
    tokenTimeRemaining,
    isTokenExpiringSoon,
    formattedTimeRemaining
  }
}