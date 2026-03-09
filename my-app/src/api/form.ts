// src\api\form.ts
/**
 * 表单相关API
 */
import request from '@/utils/request'
import type { Response } from '@/types/api'
import type {
  FormCreateRequest,
  FormUpdateRequest,
  FormResponse,
  FormDetailResponse,
  FormListQuery,
  FormListResponse,
  FormTemplateSummary
} from '@/types/form'

const FORM_BASE_PATH = '/api/v1/forms'

/**
 * 创建表单
 */
export const createForm = (data: FormCreateRequest): Promise<Response<FormResponse>> => {
  return request.post(FORM_BASE_PATH, data)
}

/**
 * 更新表单
 */
export const updateForm = (formId: number, data: FormUpdateRequest): Promise<Response<FormResponse>> => {
  return request.put(`${FORM_BASE_PATH}/${formId}`, data)
}

/**
 * 发布表单
 */
export const publishForm = (formId: number): Promise<Response<FormResponse>> => {
  return request.post(`${FORM_BASE_PATH}/${formId}/publish`)
}

/**
 * 获取表单详情
 */
export const getFormDetail = (formId: number): Promise<Response<FormDetailResponse>> => {
  return request.get(`${FORM_BASE_PATH}/${formId}`)
}

/**
 * 获取表单列表
 */
export const listForms = (
  params?: FormListQuery
): Promise<Response<FormListResponse>> => {
  return request.get(FORM_BASE_PATH, { params })
}

/**
 * 删除表单
 */
export const deleteForm = (formId: number): Promise<Response<void>> => {
  return request.delete(`${FORM_BASE_PATH}/${formId}`)
}

/**
 * 克隆表单
 */
export const cloneForm = (formId: number, newName: string): Promise<Response<FormResponse>> => {
  return request.post(`${FORM_BASE_PATH}/${formId}/clone`, { new_name: newName })
}

/**
 * 获取模板列表
 */
export const listTemplates = (): Promise<Response<FormTemplateSummary[]>> => {
  return request.get(`${FORM_BASE_PATH}/templates`)
}

/**
 * 从模板创建表单
 */
export const createFromTemplate = (
  templateId: number,
  name: string
): Promise<Response<FormResponse>> => {
  return request.post(`${FORM_BASE_PATH}/from-template/${templateId}`, { name })
}

export default {
  createForm,
  updateForm,
  publishForm,
  getFormDetail,
  listForms,
  deleteForm,
  cloneForm,
  listTemplates,
  createFromTemplate,
}