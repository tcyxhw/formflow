/**
 * auth Store Preservation 属性测试
 * 
 * **Validates: Requirements 3.1, 3.2**
 * 
 * Preservation Requirements:
 * - 当用户的 accessToken 和 refreshToken 都已过期或无效时，系统应正确清除登录状态并跳转到登录页
 * - 用户已登录且 userInfo 已存在时，系统应继续正常展示用户信息
 * 
 * 这些测试在未修复的代码上应该PASS（确认基线行为正确）
 * 修复后，这些测试应该继续PASS（确保没有回归）
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'
import * as fc from 'fast-check'

// Mock authAPI
vi.mock('@/api/auth', () => ({
  getCurrentUser: vi.fn(),
  refreshTokenByString: vi.fn()
}))

import * as authAPI from '@/api/auth'

describe('auth Store - Preservation 属性测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('Property 2: Preservation - Token确实过期时正确清除登录状态', () => {
    it('当refreshToken过期时，checkAuth()应该返回false并清除登录状态', async () => {
      // **Validates: Requirements 3.2**
      const store = useAuthStore()
      
      // 模拟用户有过期的token
      store.accessToken = 'expired_access_token'
      store.refreshToken = 'expired_refresh_token'
      store.tokenExpiry = Date.now() - 1000 // 已过期
      store.userInfo = null
      
      localStorage.setItem('access_token', 'expired_access_token')
      localStorage.setItem('refresh_token', 'expired_refresh_token')
      localStorage.setItem('token_expiry', store.tokenExpiry.toString())
      
      // Mock getCurrentUser返回401
      const mockGetCurrentUser = vi.mocked(authAPI.getCurrentUser)
      mockGetCurrentUser.mockRejectedValue({
        response: { status: 401 },
        message: 'Unauthorized'
      })
      
      // Mock refreshToken失败（token确实过期）
      const mockRefreshToken = vi.mocked(authAPI.refreshTokenByString)
      mockRefreshToken.mockRejectedValue({
        response: { status: 401 },
        message: 'Refresh token expired'
      })
      
      // 调用checkAuth
      const result = await store.checkAuth()
      
      // 验证：checkAuth应该返回false
      expect(result).toBe(false)
      
      // 验证：登录状态应该被清除
      expect(store.isLoggedIn).toBe(false)
      expect(store.accessToken).toBe('')
      expect(store.refreshToken).toBe('')
      expect(store.userInfo).toBe(null)
    })

    it('当refreshToken无效时，refreshAccessToken()应该清除登录状态', async () => {
      // **Validates: Requirements 3.2**
      const store = useAuthStore()
      
      // 模拟用户有无效的refreshToken
      store.refreshToken = 'invalid_refresh_token'
      localStorage.setItem('refresh_token', 'invalid_refresh_token')
      
      // Mock refreshToken失败
      const mockRefreshToken = vi.mocked(authAPI.refreshTokenByString)
      mockRefreshToken.mockRejectedValue({
        response: { status: 401 },
        message: 'Invalid refresh token'
      })
      
      // 调用refreshAccessToken
      const result = await store.refreshAccessToken()
      
      // 验证：刷新失败
      expect(result).toBe(false)
      
      // 验证：登录状态应该被清除
      expect(store.isLoggedIn).toBe(false)
      expect(store.accessToken).toBe('')
      expect(store.refreshToken).toBe('')
    })

    it('Property 2 (PBT): 对于所有过期的token，系统应该正确清除登录状态', async () => {
      // **Validates: Requirements 3.2**
      
      // 定义过期token生成器
      const expiredTokenArbitrary = fc.record({
        accessToken: fc.string({ minLength: 10, maxLength: 50 }),
        refreshToken: fc.string({ minLength: 10, maxLength: 50 }),
        // 生成过去的时间戳（已过期）
        tokenExpiry: fc.integer({ min: Date.now() - 86400000, max: Date.now() - 1000 })
      })

      await fc.assert(
        fc.asyncProperty(expiredTokenArbitrary, async (tokenData) => {
          // 每次测试前重置
          setActivePinia(createPinia())
          localStorage.clear()
          vi.clearAllMocks()
          
          const store = useAuthStore()
          
          // 设置过期的token
          store.accessToken = tokenData.accessToken
          store.refreshToken = tokenData.refreshToken
          store.tokenExpiry = tokenData.tokenExpiry
          store.userInfo = null
          
          localStorage.setItem('access_token', tokenData.accessToken)
          localStorage.setItem('refresh_token', tokenData.refreshToken)
          localStorage.setItem('token_expiry', tokenData.tokenExpiry.toString())
          
          // Mock API调用失败
          const mockGetCurrentUser = vi.mocked(authAPI.getCurrentUser)
          mockGetCurrentUser.mockRejectedValue({
            response: { status: 401 },
            message: 'Unauthorized'
          })
          
          const mockRefreshToken = vi.mocked(authAPI.refreshTokenByString)
          mockRefreshToken.mockRejectedValue({
            response: { status: 401 },
            message: 'Token expired'
          })
          
          // 调用checkAuth
          const result = await store.checkAuth()
          
          // 验证：对于所有过期token，checkAuth应该返回false
          expect(result).toBe(false)
          
          // 验证：登录状态应该被清除
          expect(store.isLoggedIn).toBe(false)
        }),
        { numRuns: 20 } // 运行20次测试
      )
    })
  })

  describe('Property 2: Preservation - userInfo已存在时保持不变', () => {
    it('当userInfo已存在时，checkAuth()不应该重新获取用户信息', async () => {
      // **Validates: Requirements 3.1**
      const store = useAuthStore()
      
      // 模拟用户已登录且userInfo已存在
      store.accessToken = 'valid_access_token'
      store.refreshToken = 'valid_refresh_token'
      store.tokenExpiry = Date.now() + 30 * 60 * 1000 // 30分钟后过期
      store.userInfo = {
        id: 1,
        account: 'testuser',
        name: 'Test User',
        tenant_id: 1,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        roles: ['user'],
        positions: ['student'],
        permissions: ['read']
      }
      
      localStorage.setItem('access_token', 'valid_access_token')
      localStorage.setItem('refresh_token', 'valid_refresh_token')
      localStorage.setItem('token_expiry', store.tokenExpiry.toString())
      
      // Mock getCurrentUser（不应该被调用）
      const mockGetCurrentUser = vi.mocked(authAPI.getCurrentUser)
      mockGetCurrentUser.mockResolvedValue({
        code: 200,
        data: {
          id: 1,
          account: 'testuser',
          name: 'Test User',
          tenant_id: 1,
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          roles: ['user'],
          positions: ['student'],
          permissions: ['read']
        },
        message: 'success'
      })
      
      // 调用checkAuth
      const result = await store.checkAuth()
      
      // 验证：checkAuth应该返回true
      expect(result).toBe(true)
      
      // 验证：userInfo应该保持不变
      expect(store.userInfo).toEqual({
        id: 1,
        account: 'testuser',
        name: 'Test User',
        tenant_id: 1,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        roles: ['user'],
        positions: ['student'],
        permissions: ['read']
      })
      
      // 验证：getCurrentUser不应该被调用（因为userInfo已存在）
      expect(mockGetCurrentUser).not.toHaveBeenCalled()
    })

    it('Property 2 (PBT): 对于所有已存在的userInfo，系统应该保持不变', async () => {
      // **Validates: Requirements 3.1**
      
      // 定义userInfo生成器
      const userInfoArbitrary = fc.record({
        id: fc.integer({ min: 1, max: 10000 }),
        account: fc.string({ minLength: 3, maxLength: 20 }),
        name: fc.string({ minLength: 2, maxLength: 50 }),
        tenant_id: fc.integer({ min: 1, max: 100 }),
        is_active: fc.boolean(),
        created_at: fc.constant('2024-01-01T00:00:00Z'),
        roles: fc.array(fc.constantFrom('admin', 'user', 'teacher', 'student'), { maxLength: 3 }),
        positions: fc.array(fc.constantFrom('admin', 'teacher', 'student'), { maxLength: 3 }),
        permissions: fc.array(fc.constantFrom('read', 'write', 'delete', 'approve'), { maxLength: 4 })
      })

      await fc.assert(
        fc.asyncProperty(userInfoArbitrary, async (userInfo) => {
          // 每次测试前重置
          setActivePinia(createPinia())
          localStorage.clear()
          vi.clearAllMocks()
          
          const store = useAuthStore()
          
          // 设置有效的token和userInfo
          store.accessToken = 'valid_access_token'
          store.refreshToken = 'valid_refresh_token'
          store.tokenExpiry = Date.now() + 30 * 60 * 1000
          store.userInfo = userInfo
          
          localStorage.setItem('access_token', 'valid_access_token')
          localStorage.setItem('refresh_token', 'valid_refresh_token')
          localStorage.setItem('token_expiry', store.tokenExpiry.toString())
          
          // Mock getCurrentUser（不应该被调用）
          const mockGetCurrentUser = vi.mocked(authAPI.getCurrentUser)
          mockGetCurrentUser.mockResolvedValue({
            code: 200,
            data: userInfo,
            message: 'success'
          })
          
          // 调用checkAuth
          const result = await store.checkAuth()
          
          // 验证：checkAuth应该返回true
          expect(result).toBe(true)
          
          // 验证：userInfo应该保持不变
          expect(store.userInfo).toEqual(userInfo)
          
          // 验证：getCurrentUser不应该被调用
          expect(mockGetCurrentUser).not.toHaveBeenCalled()
        }),
        { numRuns: 20 } // 运行20次测试
      )
    })

    it('边缘情况：userInfo存在但token即将过期时，不应该清除userInfo', async () => {
      // **Validates: Requirements 3.1**
      const store = useAuthStore()
      
      // 模拟token即将过期（但还有效）
      store.accessToken = 'valid_access_token'
      store.refreshToken = 'valid_refresh_token'
      store.tokenExpiry = Date.now() + 1000 // 1秒后过期
      store.userInfo = {
        id: 1,
        account: 'testuser',
        name: 'Test User',
        tenant_id: 1,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        roles: ['user'],
        positions: ['student'],
        permissions: ['read']
      }
      
      localStorage.setItem('access_token', 'valid_access_token')
      localStorage.setItem('refresh_token', 'valid_refresh_token')
      localStorage.setItem('token_expiry', store.tokenExpiry.toString())
      
      // 调用checkAuth
      const result = await store.checkAuth()
      
      // 验证：checkAuth应该返回true
      expect(result).toBe(true)
      
      // 验证：userInfo应该保持不变
      expect(store.userInfo).not.toBe(null)
      expect(store.userInfo?.id).toBe(1)
    })
  })

  describe('边缘情况测试', () => {
    it('当localStorage中没有token时，checkAuth()应该返回false', async () => {
      // **Validates: Requirements 3.2**
      const store = useAuthStore()
      
      // 确保localStorage为空
      localStorage.clear()
      
      // 调用checkAuth
      const result = await store.checkAuth()
      
      // 验证：应该返回false
      expect(result).toBe(false)
    })
  })
})
