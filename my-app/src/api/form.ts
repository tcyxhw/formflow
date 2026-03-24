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
  FormTemplateSummary,
  FormFieldsResponse
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
export const publishForm = (formId: number, flowDefinitionId?: number): Promise<Response<FormResponse>> => {
  return request.post(`${FORM_BASE_PATH}/${formId}/publish`, { flow_definition_id: flowDefinitionId })
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
export const deleteForm = (formId: number, options?: { cascade?: boolean }): Promise<Response<any>> => {
  const params = new URLSearchParams()
  if (options?.cascade) {
    params.append('cascade', 'true')
  }
  
  const queryString = params.toString()
  const url = `${FORM_BASE_PATH}/${formId}${queryString ? '?' + queryString : ''}`
  
  return request.delete(url)
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

/**
 * 获取表单字段列表
 * 用于条件构造器等功能获取表单的所有字段定义
 */
export const getFormFields = (formId: number): Promise<Response<FormFieldsResponse>> => {
  return request.get(`${FORM_BASE_PATH}/${formId}/fields`)
}

/**
 * 获取或创建表单关联的流程定义
 */
export const getOrCreateFlowDefinition = (formId: number): Promise<Response<{ flow_definition_id: number }>> => {
  return request.post(`${FORM_BASE_PATH}/${formId}/flow-definition`)
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
  getFormFields,
  getOrCreateFlowDefinition,
}