// src/types/tenant.ts
/**
 * 租户相关类型定义
 */

export interface Tenant {
  id: number
  name: string
  created_at?: string
}

export interface TenantListResponse {
  code: number
  message: string
  data: Tenant[]
}

export interface TenantValidateResponse {
  code: number
  message: string
  data: {
    valid: boolean
    tenant?: {
      id: number
      name: string
    }
  }
}