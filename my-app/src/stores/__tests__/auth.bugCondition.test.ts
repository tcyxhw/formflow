/**
 * auth Store Bug Condition 探索测试
 * 
 * **Validates: Requirements 2.1, 2.2**
 * 
 * Bug Condition: 用户已登录（有token）但 userInfo 为空时，
 * getUserInfo() API返回401错误时直接调用 clearAuth() 清除登录状态
 * 
 * 这个测试在未修复代码上应该FAIL，证明bug存在
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'

// Mock authAPI
vi.mock('@/api/auth', () => ({
  getCurrentUser: vi.fn(),
  refreshTokenByString: vi.fn().mockResolvedValue({
    code: 200,
    data: {
      access_token: 'new_access_token',
      refresh_token: 'new_refresh_token',
      expires_in: 1800
    }
  })
}))

import * as authAPI from '@/api/auth'

describe('auth Store - Bug Condition 探索测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('Bug Condition: getUserInfo() 401时不应直接清除登录状态', () => {
    it('当getUserInfo()返回401时，不应该直接调用clearAuth()', async () => {
      // **Validates: Requirements 2.1, 2.2**
      const store = useAuthStore()
      
      // 模拟用户已登录（有token但userInfo为空）
      store.accessToken = 'valid_access_token'
      store.refreshToken = 'valid_refresh_token'
      store.tokenExpiry = Date.now() + 30 * 60 * 1000 // 30分钟后过期
      store.userInfo = null // userInfo为空
      
      // 存储到localStorage
      localStorage.setItem('access_token', 'valid_access_token')
      localStorage.setItem('refresh_token', 'valid_refresh_token')
      localStorage.setItem('token_expiry', store.tokenExpiry.toString())
      
      // Mock getCurrentUser返回401
      const mockGetCurrentUser = vi.mocked(authAPI.getCurrentUser)
      mockGetCurrentUser.mockRejectedValue({
        response: { status: 401 },
        message: 'Unauthorized'
      })
      
      // 记录clearAuth是否被调用
      const clearAuthSpy = vi.spyOn(store, 'clearAuth')
      
      // 调用getUserInfo - 在未修复代码上，这会直接调用clearAuth()
      try {
        await store.getUserInfo()
      } catch (error) {
        // 预期会抛出错误
      }
      
      // 验证：在未修复代码上，clearAuth会被错误调用（测试会FAIL）
      // 修复后，clearAuth不应该被直接调用，而是让调用者处理刷新逻辑
      expect(clearAuthSpy).not.toHaveBeenCalled()
    })

    it('当getUserInfo()返回401时，应该抛出错误而不是清除登录状态', async () => {
      // **Validates: Requirements 2.1, 2.2**
      const store = useAuthStore()
      
      // 模拟用户已登录（有token但userInfo为空）
      store.accessToken = 'valid_access_token'
      store.refreshToken = 'valid_refresh_token'
      store.tokenExpiry = Date.now() + 30 * 60 * 1000
      store.userInfo = null
      
      localStorage.setItem('access_token', 'valid_access_token')
      localStorage.setItem('refresh_token', 'valid_refresh_token')
      localStorage.setItem('token_expiry', store.tokenExpiry.toString())
      
      // Mock getCurrentUser返回401
      const mockGetCurrentUser = vi.mocked(authAPI.getCurrentUser)
      mockGetCurrentUser.mockRejectedValue({
        response: { status: 401 },
        message: 'Unauthorized'
      })
      
      // 验证登录状态在调用getUserInfo之前是true
      expect(store.isLoggedIn).toBe(true)
      
      // 调用getUserInfo
      let errorThrown = false
      try {
        await store.getUserInfo()
      } catch (error) {
        errorThrown = true
      }
      
      // 应该抛出错误
      expect(errorThrown).toBe(true)
      
      // 在未修复代码上，登录状态会被错误清除
      // 修复后，登录状态应该保持不变
      expect(store.isLoggedIn).toBe(true)
      expect(store.accessToken).toBe('valid_access_token')
      expect(store.refreshToken).toBe('valid_refresh_token')
    })

    it('checkAuth()在getUserInfo()失败时应该尝试刷新token而不是直接清除登录状态', async () => {
      // **Validates: Requirements 2.1, 2.2**
      const store = useAuthStore()
      
      // 模拟用户已登录（有token但userInfo为空）
      store.accessToken = 'valid_access_token'
      store.refreshToken = 'valid_refresh_token'
      store.tokenExpiry = Date.now() + 30 * 60 * 1000
      store.userInfo = null
      
      localStorage.setItem('access_token', 'valid_access_token')
      localStorage.setItem('refresh_token', 'valid_refresh_token')
      localStorage.setItem('token_expiry', store.tokenExpiry.toString())
      
      // Mock getCurrentUser返回401（第一次）
      const mockGetCurrentUser = vi.mocked(authAPI.getCurrentUser)
      mockGetCurrentUser
        .mockRejectedValueOnce({
          response: { status: 401 },
          message: 'Unauthorized'
        })
        .mockResolvedValueOnce({
          code: 200,
          data: {
            id: 1,
            account: 'testuser',
            name: 'Test User',
            roles: [],
            permissions: []
          }
        })
      
      // Mock refreshToken成功
      const mockRefreshToken = vi.mocked(authAPI.refreshTokenByString)
      mockRefreshToken.mockResolvedValue({
        code: 200,
        data: {
          access_token: 'new_access_token',
          refresh_token: 'new_refresh_token',
          expires_in: 1800
        }
      })
      
      // 记录clearAuth是否被调用
      const clearAuthSpy = vi.spyOn(store, 'clearAuth')
      
      // 调用checkAuth - 在未修复代码上，getUserInfo会直接调用clearAuth
      const result = await store.checkAuth()
      
      // 在未修复代码上，clearAuth会被错误调用（测试会FAIL）
      // 修复后，checkAuth应该先尝试刷新token，刷新成功后再获取用户信息
      expect(clearAuthSpy).not.toHaveBeenCalled()
    })
  })
})