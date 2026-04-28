// src/stores/auth.ts - 适应最新API修改版
/**
 * 认证状态管理 - 配合后端双Token中间件
 */
import { defineStore } from 'pinia'
import router from '@/router'
import * as authAPI from '@/api/auth'
import type { UserInfo, UserBasicInfo } from '@/types/user'

interface AuthState {
  userInfo: UserInfo | null
  userBasicInfo: UserBasicInfo | null  // 保留原有字段
  accessToken: string
  refreshToken: string
  tokenExpiry: number
  refreshPromise: Promise<boolean> | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    userInfo: null,
    userBasicInfo: null,
    accessToken: '',
    refreshToken: '',
    tokenExpiry: 0,
    refreshPromise: null
  }),
  
  getters: {
    // ✅ 保持原有的 getters 不变
    isLoggedIn: (state): boolean => {
      return !!state.accessToken && state.tokenExpiry > Date.now()
    },
    
    userId: (state): number | undefined => {
      return state.userInfo?.id || state.userBasicInfo?.id
    },
    
    username: (state): string | undefined => {
      return state.userInfo?.account || state.userBasicInfo?.account
    },
    
    userRoles: (state): string[] => {
      return state.userInfo?.roles || []
    },
    
    userPermissions: (state): string[] => {
      return state.userInfo?.permissions || []
    }
  },
  
  actions: {
    // ✅ 保持原有函数名，只修改内部实现
    saveTokens(access: string, refresh: string, expiresIn: number) {
      this.accessToken = access
      this.refreshToken = refresh
      this.tokenExpiry = Date.now() + expiresIn * 1000

      // ✅ 存储两个 token
      localStorage.setItem('access_token', access)     // 添加这行
      localStorage.setItem('refresh_token', refresh)
      localStorage.setItem('token_expiry', this.tokenExpiry.toString())
    },
      
    // ✅ 保持原有函数名不变
    clearAuth() {
      this.accessToken = ''
      this.refreshToken = ''
      this.tokenExpiry = 0
      this.userInfo = null
      this.userBasicInfo = null
      
      localStorage.removeItem('access_token')   
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('token_expiry')
      localStorage.removeItem('user_basic_info')  // 清理旧数据
      localStorage.removeItem('user_info')         // 清理旧数据
    },
    
    // ✅ 保持原有函数名，改进内部逻辑
    initTokens() {
      const storedAccessToken = localStorage.getItem('access_token')    // 添加这行
      const storedRefreshToken = localStorage.getItem('refresh_token')
      const storedExpiry = localStorage.getItem('token_expiry')
      
      if (storedRefreshToken) {
        this.accessToken = storedAccessToken || ''      // 添加这行
        this.refreshToken = storedRefreshToken
        this.tokenExpiry = storedExpiry ? parseInt(storedExpiry) : 0
      }
    },
    
    // ✅ 保持原有函数签名不变
    async login(account: string, password: string): Promise<boolean> {
      const { useTenantStore } = await import('@/stores/tenant')
      const tenantStore = useTenantStore()
      
      if (!tenantStore.tenantId) {
        throw new Error('请先选择学校')
      }
      
      try {
        const response = await authAPI.login({ 
          account, 
          password,
          tenant_id: tenantStore.tenantId
        })
        
        if (response.code === 200 && response.data) {
          const { access_token, refresh_token, expires_in, user } = response.data
          
          this.saveTokens(access_token, refresh_token, expires_in)
          
          // 🔧 修正：处理登录返回的用户信息
          this.userBasicInfo = user
          
          // 获取详细用户信息
          this.getUserInfo().catch(console.error)
          
          return true
        }
        
        return false
      } catch (error) {
        console.error('Login failed:', error)
        this.clearAuth()
        throw error
      }
    },
    
    // ✅ 保持原有函数完全不变
    async register(data: {
      account: string
      password: string
      name: string
      phone?: string
      email?: string
    }): Promise<boolean> {
      const { useTenantStore } = await import('@/stores/tenant')
      const tenantStore = useTenantStore()
      
      if (!tenantStore.tenantId) {
        throw new Error('请先选择学校')
      }
      
      try {
        const response = await authAPI.register({
          ...data,
          tenant_id: tenantStore.tenantId
        })
        
        return response.code === 200
      } catch (error) {
        console.error('Register failed:', error)
        throw error
      }
    },
    
    // 🔧 关键修正：刷新令牌方法
    async refreshAccessToken(): Promise<boolean> {
      if (this.refreshPromise) return this.refreshPromise
      
      this.refreshPromise = (async () => {
        try {
          if (!this.refreshToken) {
            // 如果内存中没有，尝试从存储读取
            const storedRefreshToken = localStorage.getItem('refresh_token')
            if (!storedRefreshToken) return false
            this.refreshToken = storedRefreshToken
          }
          
          // 🔧 修正：使用正确的参数格式
          const response = await authAPI.refreshTokenByString(this.refreshToken)
          
          if (response.code === 200 && response.data) {
            const { access_token, refresh_token, expires_in } = response.data
            this.saveTokens(access_token, refresh_token, expires_in)
            
            // 🔧 修正：刷新接口不返回用户信息，移除这部分
            // 刷新Token接口只返回令牌，不返回用户信息
            
            return true
          }
          
          return false
        } catch (error) {
          console.error('Token refresh failed:', error)
          this.clearAuth()
          return false
        } finally {
          this.refreshPromise = null
        }
      })()
      
      return this.refreshPromise
    },
    
    // ✅ 保持原有函数，只改进存储逻辑
    async getUserInfo(): Promise<void> {
      try {
        const response = await authAPI.getCurrentUser()
        
        // 防御性检查：response 和 response.data 都可能为 null
        if (response && response.code === 200 && response.data) {
          this.userInfo = response.data
        }
      } catch (error: any) {
        if (error?.name === 'CanceledError' || error?.code === 'ERR_CANCELED') {
          return
        }
        console.error('Failed to get user info:', error)
        throw error
      }
    },
    
    // ✅ 保持原有函数完全不变
    async logout(): Promise<void> {
      try {
        if (this.accessToken) {
          await authAPI.logout()
        }
      } catch (error) {
        console.error('Logout API call failed:', error)
      } finally {
        this.clearAuth()
        router.push('/login')
      }
    },
    
    // ✅ 保持原有函数名，改进实现
    getAccessToken(): string {
      if (!this.accessToken) {
        this.initTokens()
        // 如果没有访问令牌但有刷新令牌，返回空（让拦截器处理刷新）
      }
      return this.accessToken
    },
    
    // 🔧 修正：简化checkAuth，依赖中间件自动处理刷新
    async checkAuth(): Promise<boolean> {
      try {
        this.initTokens()
        
        // 如果没有刷新令牌，直接返回 false
        if (!this.refreshToken && !localStorage.getItem('refresh_token')) {
          return false
        }
        
        // 确保刷新令牌在内存中
        if (!this.refreshToken) {
          const storedRefreshToken = localStorage.getItem('refresh_token')
          if (storedRefreshToken) {
            this.refreshToken = storedRefreshToken
          } else {
            return false
          }
        }
        
        // 🔧 关键修正：依赖中间件自动刷新，这里只需要检查用户信息
        if (!this.userInfo) {
          try {
            await this.getUserInfo()
          } catch (error: any) {
            console.log('User info fetch failed:', error.message || error)
            
            // 🔧 优化：只有在401错误时才尝试刷新token
            // 其他错误（如网络错误、超时）直接返回false
            if (error.response?.status === 401) {
              console.log('Got 401, trying to refresh token...')
              const refreshed = await this.refreshAccessToken()
              if (refreshed) {
                // 刷新成功后重新获取用户信息
                try {
                  await this.getUserInfo()
                  return true
                } catch {
                  return false
                }
              }
            }
            return false
          }
        }
        
        return true
      } catch (error) {
        console.error('Check auth failed:', error)
        return false
      }
    },
    
    // ✅ 保持原有函数完全不变
    hasRole(role: string | string[]): boolean {
      if (!this.userInfo) return false
      
      const roles = Array.isArray(role) ? role : [role]
      return roles.some(r => this.userRoles.includes(r))
    },
    
    hasPermission(permission: string | string[]): boolean {
      if (!this.userInfo) return false
      
      const permissions = Array.isArray(permission) ? permission : [permission]
      return permissions.some(p => this.userPermissions.includes(p))
    },
    
    // 获取用户统计信息
    async fetchUserStats(): Promise<{
      forms_created: number
      forms_submitted: number
      tasks_pending: number
      tasks_completed: number
    }> {
      try {
        const response = await authAPI.getCurrentUserStats()
        if (response.code === 200 && response.data) {
          return response.data
        }
        return {
          forms_created: 0,
          forms_submitted: 0,
          tasks_pending: 0,
          tasks_completed: 0
        }
      } catch (error) {
        console.error('获取统计信息失败:', error)
        return {
          forms_created: 0,
          forms_submitted: 0,
          tasks_pending: 0,
          tasks_completed: 0
        }
      }
    },
    
    // 🔧 新增：更新访问令牌
    updateAccessToken(newAccessToken: string) {
      this.accessToken = newAccessToken
      
      // 重新计算过期时间（30分钟）
      this.tokenExpiry = Date.now() + 30 * 60 * 1000
      
      // 更新localStorage（如果你选择存储的话）
      localStorage.setItem('access_token', newAccessToken)
      localStorage.setItem('token_expiry', this.tokenExpiry.toString())
      
      console.log('访问令牌已更新')
    },
    
    // 🔧 新增：更新刷新令牌
    updateRefreshToken(newRefreshToken: string) {
      // ✅ 必须同时更新内存和 localStorage
      this.refreshToken = newRefreshToken
      
      // 更新localStorage
      localStorage.setItem('refresh_token', newRefreshToken)
      
      // 刷新令牌轮转时，重置完整的有效期（7天）
      const newRefreshExpiry = Date.now() + (7 * 24 * 60 * 60 * 1000)
      // 这里不更新 tokenExpiry，因为它主要用于访问令牌
      
      console.log('刷新令牌已轮转')
    },
    
  }
})