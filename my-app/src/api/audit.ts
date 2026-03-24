/**
 * 审计日志相关 API
 */
import request from '@/utils/request'
import type { Response, PageResponse } from '@/types/api'

export interface AuditLogQuery {
  page?: number
  page_size?: number
  actor_user_id?: number
  resource_type?: string
  action?: string
  date_from?: string
  date_to?: string
  resource_id?: number
  only_mine?: boolean
}

export interface AuditLog {
  id: number
  tenant_id: number
  actor_user_id: number | null
  actor_name: string | null
  action: string
  resource_type: string
  resource_id: number | null
  before_json: Record<string, any> | null
  after_json: Record<string, any> | null
  ip: string | null
  ua: string | null
  created_at: string
}

export interface AuditLogListResponse {
  items: AuditLog[]
  total: number
}

export interface AuditLogDetailResponse {
  log: AuditLog
  changes: ChangeComparisonItem[]
}

export interface ChangeComparisonItem {
  field: string
  before: any
  after: any
  change_type: 'added' | 'modified' | 'removed'
}

export interface AuditLogExportParams {
  actor_user_id?: number
  resource_type?: string
  action?: string
  date_from?: string
  date_to?: string
  resource_ids?: number[]
}

/**
 * 查询审计日志列表
 */
export const listAuditLogs = (
  params: AuditLogQuery
): Promise<Response<AuditLogListResponse>> => {
  return request.get('/api/v1/admin/audit-logs', params)
}

/**
 * 获取审计日志详情
 */
export const getAuditLogDetail = (
  logId: number
): Promise<Response<AuditLogDetailResponse>> => {
  return request.get(`/api/v1/admin/audit-logs/${logId}`)
}

/**
 * 导出审计日志为CSV
 */
export const exportAuditLogs = (
  params: AuditLogExportParams
): Promise<Blob> => {
  return request.post('/api/v1/admin/audit-logs/export', params, {
    responseType: 'blob'
  })
}
