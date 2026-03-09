// src/types/auth.ts
/**
 * 认证相关类型定义 - 对应后端 app/schemas/auth.py
 */

// 登录请求
export interface LoginRequest {
  account: string          // 账号/邮箱/手机号
  password: string         // 密码
  tenant_id?: number       // 租户ID（可选）
}

// 登录响应中的用户信息
export interface LoginUserInfo {
  id: number
  account: string
  name: string
  email?: string
  tenant_id: number
  identity_type: string
  positions: string[]
}

// 登录响应
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string       // "Bearer"
  expires_in: number       // 过期时间(秒)
  user: LoginUserInfo
}

// Token响应
export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string       // "Bearer"
  expires_in: number       // 访问令牌过期时间(秒)
}

// 刷新Token请求
export interface RefreshTokenRequest {
  refresh_token: string    // 刷新令牌
}

// 注册请求
export interface RegisterRequest {
  account: string          // 3-50字符
  password: string         // 最少6位
  name: string            // 2-50字符
  email?: string          // 可选邮箱
  phone?: string          // 可选手机号，格式：1[3-9]\d{9}
  tenant_id: number       // 租户ID
}

// 注册响应
export interface RegisterResponse {
  id: number
  account: string
  name: string
  email?: string
  phone?: string
  tenant_id: number
  identity_type: string
}

// 租户信息
export interface TenantInfo {
  id: number
  name: string
  created_at?: string
}

// 租户验证请求
export interface ValidateTenantRequest {
  tenant_id: number
}

// 租户验证响应
export interface ValidateTenantResponse {
  valid: boolean
  tenant?: TenantInfo
}