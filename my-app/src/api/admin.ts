/**
 * 管理员相关 API（角色、部门、岗位、群组）
 */
import request from '@/utils/request'
import type { Response } from '@/types/api'

const ADMIN_BASE_PATH = '/api/v1/admin'

/**
 * 角色列表项
 */
export interface RoleListItem {
  id: number
  name: string
  description?: string
}

/**
 * 部门列表项
 */
export interface DepartmentListItem {
  id: number
  name: string
  type: string
  parent_id?: number
}

/**
 * 岗位列表项
 */
export interface PositionListItem {
  id: number
  name: string
}

/**
 * 审批群组列表项
 */
export interface GroupListItem {
  id: number
  name: string
  department_id?: number
}

/**
 * 列表响应（通用）
 */
export interface ListResponse<T> {
  items: T[]
  total: number
}

/**
 * 列表查询参数（通用）
 */
export interface ListParams {
  keyword?: string
  page?: number
  size?: number
}

/**
 * 获取角色列表（简化版，用于选择器）
 * GET /api/v1/admin/roles/list
 * 
 * @param params 查询参数
 * @returns 角色列表
 */
export const listRoles = (params?: ListParams): Promise<Response<ListResponse<RoleListItem>>> => {
  return request.get(`${ADMIN_BASE_PATH}/roles/list`, { params })
}

/**
 * 获取部门列表（简化版，用于选择器）
 * GET /api/v1/admin/departments/list
 * 
 * @param params 查询参数
 * @returns 部门列表
 */
export const listDepartments = (params?: ListParams): Promise<Response<ListResponse<DepartmentListItem>>> => {
  return request.get(`${ADMIN_BASE_PATH}/departments/list`, { params })
}

/**
 * 获取岗位列表（简化版，用于选择器）
 * GET /api/v1/admin/positions/list
 * 
 * @param params 查询参数
 * @returns 岗位列表
 */
export const listPositions = (params?: ListParams): Promise<Response<ListResponse<PositionListItem>>> => {
  return request.get(`${ADMIN_BASE_PATH}/positions/list`, { params })
}

/**
 * 获取审批群组列表（简化版，用于选择器）
 * GET /api/v1/admin/groups/list
 *
 * @param params 查询参数
 * @returns 群组列表
 */
export const listGroups = (params?: ListParams): Promise<Response<ListResponse<GroupListItem>>> => {
  return request.get(`${ADMIN_BASE_PATH}/groups/list`, { params })
}

// ==================== 批量导入相关 ====================

/**
 * 批量导入单行结果
 */
export interface BatchImportRowResult {
  row_number: number
  success: boolean
  account?: string
  name?: string
  error_message?: string
  user_id?: number
}

/**
 * 批量导入响应
 */
export interface BatchImportResponse {
  total_rows: number
  success_count: number
  failed_count: number
  results: BatchImportRowResult[]
  default_password: string
}

/**
 * 导入历史记录项
 */
export interface ImportHistoryItem {
  id: number
  filename: string
  total_rows: number
  success_count: number
  failed_count: number
  created_at: string
  created_by: number
}

/**
 * 批量导入用户
 * POST /api/v1/admin/batch-import
 *
 * @param file Excel文件
 * @param defaultPassword 默认密码
 * @returns 导入结果
 */
export const batchImportUsers = async (
  file: File,
  defaultPassword: string
): Promise<Response<BatchImportResponse>> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('default_password', defaultPassword)

  return request.post(`${ADMIN_BASE_PATH}/batch-import`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 下载批量导入模板
 * GET /api/v1/admin/batch-import/template
 *
 * @returns Excel文件Blob
 */
export const downloadImportTemplate = (): Promise<Blob> => {
  return request.get(`${ADMIN_BASE_PATH}/batch-import/template`, {
    responseType: 'blob'
  }) as unknown as Promise<Blob>
}

/**
 * 获取导入历史记录
 * GET /api/v1/admin/batch-import/history
 *
 * @param params 查询参数
 * @returns 导入历史列表
 */
export const getImportHistory = async (
  params: ListParams
): Promise<Response<ListResponse<ImportHistoryItem>>> => {
  return request.get(`${ADMIN_BASE_PATH}/batch-import/history`, { params })
}

/**
 * 获取导入历史详情
 * GET /api/v1/admin/batch-import/history/:id
 *
 * @param id 记录ID
 * @returns 导入详情
 */
export const getImportHistoryDetail = async (
  id: number
): Promise<Response<any>> => {
  return request.get(`${ADMIN_BASE_PATH}/batch-import/history/${id}`)
}

// 导出所有管理员相关的API函数
export default {
  listRoles,
  listDepartments,
  listPositions,
  listGroups,
  batchImportUsers,
  downloadImportTemplate,
  getImportHistory,
  getImportHistoryDetail
}
