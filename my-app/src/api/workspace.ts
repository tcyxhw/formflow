// src/api/workspace.ts
/**
 * 表单填写工作区相关API
 */
import request from '@/utils/request'
import type { Response } from '@/types/api'
import type {
  FillableFormsQuery,
  FillableFormsResponse,
  QuickAccessResponse
} from '@/types/workspace'

const WORKSPACE_BASE_PATH = '/api/v1/forms'

/**
 * 获取可填写表单列表
 * GET /api/v1/forms/fillable
 * 
 * @param params 查询参数（分页、搜索、筛选、排序）
 * @returns 可填写表单列表响应
 */
export const getFillableForms = (
  params?: FillableFormsQuery
): Promise<Response<FillableFormsResponse>> => {
  return request.get(`${WORKSPACE_BASE_PATH}/fillable`, { params })
}

/**
 * 添加表单到快捷入口
 * POST /api/v1/forms/{form_id}/quick-access
 * 
 * @param formId 表单ID
 * @returns 操作结果
 */
export const addQuickAccess = (formId: number): Promise<Response<{ form_id: number }>> => {
  return request.post(`${WORKSPACE_BASE_PATH}/${formId}/quick-access`)
}

/**
 * 从快捷入口移除表单
 * DELETE /api/v1/forms/{form_id}/quick-access
 * 
 * @param formId 表单ID
 * @returns 操作结果
 */
export const removeQuickAccess = (formId: number): Promise<Response<void>> => {
  return request.delete(`${WORKSPACE_BASE_PATH}/${formId}/quick-access`)
}

/**
 * 获取快捷入口表单列表
 * GET /api/v1/forms/quick-access
 * 
 * @returns 快捷入口表单列表
 */
export const getQuickAccessForms = (): Promise<Response<QuickAccessResponse>> => {
  return request.get(`${WORKSPACE_BASE_PATH}/quick-access`)
}

// 导出所有工作区相关的API函数
export default {
  getFillableForms,
  addQuickAccess,
  removeQuickAccess,
  getQuickAccessForms
}
