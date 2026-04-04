/**
 * 认证相关 API - 与后端Schema完全对应
 */
import request from '@/utils/request'
import type { Response } from '@/types/api'
import type {
  LoginRequest,
  LoginResponse,
  TokenResponse,
  RefreshTokenRequest,
  RegisterRequest,
  RegisterResponse,
  TenantInfo,
  ValidateTenantRequest,
  ValidateTenantResponse
} from '@/types/auth'
import type { UserInfo } from '@/types/user'

const AUTH_BASE_PATH = '/api/v1/auth'

/**
 * 用户登录
 * POST /api/v1/auth/login
 * 
 * @param data 登录参数
 * @returns 包含令牌和用户信息的响应
 */
export const login = (data: LoginRequest): Promise<Response<LoginResponse>> => {
  return request.post(`${AUTH_BASE_PATH}/login`, data)
}

/**
 * 刷新Token
 * POST /api/v1/auth/refresh
 * 
 * @param data 刷新令牌参数
 * @returns 新的令牌信息
 */
export const refreshToken = (data: RefreshTokenRequest): Promise<Response<TokenResponse>> => {
  return request.post(`${AUTH_BASE_PATH}/refresh`, data)
}

/**
 * 刷新Token (便捷方法 - 兼容旧版本)
 * @param refresh_token 刷新令牌字符串
 * @returns 新的令牌信息
 */
export const refreshTokenByString = (refresh_token: string): Promise<Response<TokenResponse>> => {
  return refreshToken({ refresh_token })
}

/**
 * 用户注册
 * POST /api/v1/auth/register
 * 
 * @param data 注册参数
 * @returns 创建的用户信息
 */
export const register = (data: RegisterRequest): Promise<Response<RegisterResponse>> => {
  return request.post(`${AUTH_BASE_PATH}/register`, data)
}

/**
 * 用户登出
 * POST /api/v1/auth/logout
 * 
 * @returns 登出操作结果
 */
export const logout = (): Promise<Response<{ success: boolean }>> => {
  return request.post(`${AUTH_BASE_PATH}/logout`)
}

/**
 * 获取当前用户信息
 * GET /api/v1/auth/me
 * 
 * @returns 当前用户的完整信息
 */
export const getCurrentUser = (): Promise<Response<UserInfo>> => {
  return request.get(`${AUTH_BASE_PATH}/me`)
}

/**
 * 获取当前用户统计信息
 * GET /api/v1/users/me/stats
 * 
 * @returns 用户统计信息
 */
export const getCurrentUserStats = (): Promise<Response<{
  forms_created: number
  forms_submitted: number
  tasks_pending: number
  tasks_completed: number
}>> => {
  return request.get('/api/v1/users/me/stats')
}

/**
 * 更新用户信息
 * PUT /api/v1/users/{user_id}
 * 
 * @param userId 用户ID
 * @param data 更新数据
 * @returns 更新后的用户信息
 */
export const updateUser = (userId: number, data: {
  name?: string
  email?: string
  phone?: string
  avatar_url?: string
}): Promise<Response<any>> => {
  return request.put(`/api/v1/users/${userId}`, data)
}

/**
 * 修改密码
 * POST /api/v1/users/{user_id}/change-password
 * 
 * @param userId 用户ID
 * @param data 密码修改数据
 * @returns 修改结果
 */
export const changePassword = (userId: number, data: {
  old_password: string
  new_password: string
}): Promise<Response<any>> => {
  return request.post(`/api/v1/users/${userId}/change-password`, data)
}

/**
 * 更新用户扩展信息
 * PUT /api/v1/users/{user_id}/profile
 * 
 * @param userId 用户ID
 * @param data 扩展信息
 * @returns 更新后的用户扩展信息
 */
export const updateUserProfile = (userId: number, data: {
  identity_type?: 'student' | 'teacher' | 'admin'
  identity_no?: string
  entry_year?: number
  grade?: string
  major?: string
  title?: string
  research_area?: string
  office?: string
}): Promise<Response<any>> => {
  return request.put(`/api/v1/users/${userId}/profile`, data)
}

/**
 * 获取租户列表
 * GET /api/v1/auth/tenants
 * 
 * @returns 所有可用租户列表
 */
export const getTenants = (): Promise<Response<TenantInfo[]>> => {
  return request.get(`${AUTH_BASE_PATH}/tenants`)
}

/**
 * 验证租户有效性
 * POST /api/v1/auth/validate-tenant
 * 
 * @param data 包含租户ID的验证参数
 * @returns 租户验证结果
 */
export const validateTenant = (data: ValidateTenantRequest): Promise<Response<ValidateTenantResponse>> => {
  return request.post(`${AUTH_BASE_PATH}/validate-tenant`, data)
}

/**
 * 验证租户有效性 (便捷方法)
 * @param tenant_id 租户ID
 * @returns 租户验证结果
 */
export const validateTenantById = (tenant_id: number): Promise<Response<ValidateTenantResponse>> => {
  return validateTenant({ tenant_id })
}

// 导出所有认证相关的API函数
export default {
  login,
  refreshToken,
  refreshTokenByString, // 兼容方法
  register,
  logout,
  getCurrentUser,
  getCurrentUserStats,
  getTenants,
  validateTenant,
  validateTenantById, // 便捷方法
}