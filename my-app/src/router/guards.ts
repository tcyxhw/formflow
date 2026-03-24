// src/router/guards.ts
/**
 * 路由守卫
 * 处理权限验证、租户验证等
 */
import type { Router } from 'vue-router'
import type { ApiMessageBridge } from '@/types/api'

import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 配置NProgress
NProgress.configure({ showSpinner: false })

type MessageType = 'success' | 'error' | 'warning' | 'info'

// ✅ Naive UI 消息实例（单例模式，与 request.ts 共享机制）
let messageInstance: ApiMessageBridge | null = null

/**
 * ✅ 设置消息实例（在 App.vue 中调用）
 */
export function setGuardMessageInstance(instance: ApiMessageBridge) {
  messageInstance = instance
}

/**
 * ✅ 显示消息的辅助函数
 */
function showMessage(type: MessageType, content: string) {

  if (messageInstance) {
    messageInstance[type](content)
  } else {
    // 降级方案：使用控制台输出
    console.warn(`[Guard Message] ${type}: ${content}`)
  }
}

export function setupRouterGuards(router: Router) {
  router.beforeEach(async (to, from, next) => {
    // 开始进度条
    NProgress.start()
    
    // 在路由守卫内部导入并使用 store
    // 这样可以确保 pinia 已经初始化
    const { useAuthStore } = await import('@/stores/auth')
    const { useTenantStore } = await import('@/stores/tenant')
    
    const authStore = useAuthStore()
    const tenantStore = useTenantStore()
    
    // 设置页面标题
    document.title = `${to.meta.title || '页面'} - FormFlow`
    
    // 1. 租户选择页面特殊处理
    if (to.path === '/tenant-select') {
      // 如果已登录，需要先退出
      if (authStore.isLoggedIn) {
        showMessage('warning', '请先退出登录后再切换学校')
        NProgress.done()
        next(false)
        return
      }
      next()
      NProgress.done()
      return
    }
    
    // 2. 检查是否有租户信息
    if (!tenantStore.hasTenant) {
      // 尝试从localStorage恢复
      if (!tenantStore.initTenant()) {
        // 没有租户信息，跳转到租户选择
        NProgress.done()
        next('/tenant-select')
        return
      }
      
      // 验证租户是否有效
      const valid = await tenantStore.validateCurrentTenant()
      if (!valid) {
        showMessage('error', '学校信息已失效，请重新选择')
        NProgress.done()
        next('/tenant-select')
        return
      }
    }
    
    // 3. 登录页面处理
    if (to.path === '/login') {
      if (authStore.isLoggedIn) {
        // 已登录，跳转到首页
        NProgress.done()
        next('/')
        return
      }
      next()
      NProgress.done()
      return
    }
    
    // 4. 注册页面处理
    if (to.path === '/register') {
      if (authStore.isLoggedIn) {
        // 已登录，跳转到首页
        NProgress.done()
        next('/')
        return
      }
      next()
      NProgress.done()
      return
    }
    
    // 5. 404页面
    if (to.path === '/404' || to.path === '/403') {
      next()
      NProgress.done()
      return
    }
    
    // 6. 其他页面需要登录
    if (!authStore.isLoggedIn) {
      // 尝试恢复登录状态
      const restored = await authStore.checkAuth()
      if (!restored) {
        showMessage('warning', '请先登录')
        NProgress.done()
        next(`/login?redirect=${to.path}`)
        return
      }
    }
    
    // 7. 权限检查
    if (to.meta.roles) {
      const hasRole = authStore.hasRole(to.meta.roles as string[])
      if (!hasRole) {
        showMessage('error', '没有权限访问该页面')
        NProgress.done()
        next('/403')
        return
      }
    }
    
    if (to.meta.permissions) {
      const hasPermission = authStore.hasPermission(to.meta.permissions as string[])
      if (!hasPermission) {
        showMessage('error', '没有权限访问该页面')
        NProgress.done()
        next('/403')
        return
      }
    }
    
    next()
  })
  
  router.afterEach(() => {
    // 结束进度条
    NProgress.done()
  })
  
  // 路由错误处理
  router.onError((error) => {
    console.error('路由错误:', error)
    NProgress.done()
  })
}