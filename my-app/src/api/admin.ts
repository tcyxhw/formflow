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
 * @param defaultDepartmentId 默认部门ID（可选）
 * @returns 导入结果
 */
export const batchImportUsers = async (
  file: File,
  defaultPassword: string,
  defaultDepartmentId?: number | null
): Promise<Response<BatchImportResponse>> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('default_password', defaultPassword)
  if (defaultDepartmentId) {
    formData.append('default_department_id', String(defaultDepartmentId))
  }

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
  // 对于 blob 响应，request.get 直接返回 Blob
  return request.get(`${ADMIN_BASE_PATH}/batch-import/template`, undefined, {
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

// ==================== 用户管理相关 ====================

/**
 * 用户列表项
 */
export interface UserListItem {
  id: number
  account: string
  name: string
  email: string | null
  phone: string | null
  is_active: boolean
  role?: string
  roles: string[]
  department_name: string | null
  department_id: number | null
  post_name?: string | null
  post_id?: number | null
  positions: string[]
  created_at?: string
}

/**
 * 用户列表查询参数
 */
export interface UserListQuery {
  page: number
  size: number
  department_id?: number | null
  post_id?: number | null
  keyword?: string
}

/**
 * 用户列表响应
 */
export interface UserListResponse {
  items: UserListItem[]
  total: number
  page: number
  size: number
}

/**
 * 可管理部门
 */
export interface ManageableDepartment {
  id: number
  name: string
  type?: string
  parent_id?: number
  posts: Array<{ id: number; name: string; level?: number }>
}

/**
 * 当前用户岗位信息
 */
export interface CurrentUserPosition {
  id: number
  name: string
  department_id: number
  department_name: string
}

/**
 * 可管理范围
 */
export interface ManageableScope {
  departments: ManageableDepartment[]
  positions: Array<{ id: number; name: string }>
  is_admin: boolean
  current_user_department?: ManageableDepartment
  current_user_positions: CurrentUserPosition[]
}

/**
 * 导入预览行
 */
export interface ImportPreviewRow {
  row_number: number
  account: string
  name: string
  department: string
  post: string
  role: string
  is_valid: boolean
  errors: string[]
}

/**
 * 导入预览响应
 */
export interface ImportPreviewResponse {
  preview_key: string
  rows: ImportPreviewRow[]
  valid_count: number
  invalid_count: number
}

/**
 * 确认导入请求
 */
export interface ImportConfirmRequest {
  preview_key: string
  user_ids: string[]
}

/**
 * 获取用户列表
 * GET /api/v1/admin/users
 */
export const getUsers = (params: UserListQuery): Promise<Response<UserListResponse>> => {
  return request.get(`${ADMIN_BASE_PATH}/users`, { params })
}

/**
 * 更新用户信息
 * PUT /api/v1/admin/users/{user_id}
 */
export const updateUser = (id: number, data: Partial<UserListItem>): Promise<Response<UserListItem>> => {
  return request.put(`${ADMIN_BASE_PATH}/users/${id}`, data)
}

/**
 * 删除用户
 * DELETE /api/v1/admin/users/{user_id}
 */
export const deleteUser = (id: number): Promise<Response<{ message: string }>> => {
  return request.delete(`${ADMIN_BASE_PATH}/users/${id}`)
}

/**
 * 获取可管理范围
 * GET /api/v1/admin/manageable-scope
 */
export const getManageableScope = (): Promise<Response<ManageableScope>> => {
  return request.get(`${ADMIN_BASE_PATH}/manageable-scope`)
}

/**
 * 预览导入用户
 * POST /api/v1/admin/users/preview-import
 */
export const previewImportUsers = (file: File): Promise<Response<ImportPreviewResponse>> => {
  const formData = new FormData()
  formData.append('file', file)

  return request.post(`${ADMIN_BASE_PATH}/users/preview-import`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 确认导入用户
 * POST /api/v1/admin/users/confirm-import
 */
export const confirmImportUsers = (data: ImportConfirmRequest): Promise<Response<{ message: string; imported_count: number }>> => {
  return request.post(`${ADMIN_BASE_PATH}/users/confirm-import`, data)
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
  getImportHistoryDetail,
  getUsers,
  updateUser,
  deleteUser,
  getManageableScope,
  previewImportUsers,
  confirmImportUsers
}
