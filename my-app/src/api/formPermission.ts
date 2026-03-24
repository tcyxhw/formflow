// src/api/formPermission.ts
import request from '@/utils/request'
import type { Response } from '@/types/api'
import type {
  FormPermission,
  FormPermissionListResponse,
  FormPermissionOverview,
  FormPermissionPayload,
  FormPermissionUpdatePayload
} from '@/types/formPermission'

const FORM_BASE_PATH = '/api/v1/forms'

/**
 * 获取表单权限列表
 */
export const listFormPermissions = (
  formId: number
): Promise<Response<FormPermissionListResponse>> => {
  return request.get(`${FORM_BASE_PATH}/${formId}/permissions`)
}

/**
 * 新增表单权限
 */
export const createFormPermission = (
  formId: number,
  payload: FormPermissionPayload
): Promise<Response<FormPermission>> => {
  return request.post(`${FORM_BASE_PATH}/${formId}/permissions`, payload)
}

/**
 * 更新表单权限
 */
export const updateFormPermission = (
  formId: number,
  permissionId: number,
  payload: FormPermissionUpdatePayload
): Promise<Response<FormPermission>> => {
  return request.put(`${FORM_BASE_PATH}/${formId}/permissions/${permissionId}`, payload)
}

/**
 * 删除表单权限
 */
export const deleteFormPermission = (formId: number, permissionId: number): Promise<Response<void>> => {
  return request.delete(`${FORM_BASE_PATH}/${formId}/permissions/${permissionId}`)
}

/**
 * 查询当前用户在指定表单下的权限概览
 */
export const getMyFormPermissions = (
  formId: number
): Promise<Response<FormPermissionOverview>> => {
  return request.get(`${FORM_BASE_PATH}/${formId}/permissions/me`)
}
