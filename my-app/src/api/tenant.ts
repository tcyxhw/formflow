// src/api/tenant.ts
/**
 * 租户相关API
 */
import request from '@/utils/request'
import type { Response } from '@/types/api'
import type { Tenant } from '@/types/tenant'

/**
 * 获取租户列表
 * 无需认证
 */
export const getTenantList = (): Promise<Response<Tenant[]>> => {
  return request.get('/api/v1/auth/tenants')
}

/**
 * 验证租户有效性
 * 无需认证
 */
export const validateTenant = (tenantId: number): Promise<Response<{
  valid: boolean
  tenant?: {
    id: number
    name: string
  }
}>> => {
  return request.post('/api/v1/auth/validate-tenant', { tenant_id: tenantId })
}