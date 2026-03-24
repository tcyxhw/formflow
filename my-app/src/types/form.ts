/**
 * 表单类型定义
 */
import type { FormSchema, UISchema } from './schema'
import type { LogicSchema } from './logic'
import type { AttachmentInfo } from './attachment'

export enum FormStatus {
  DRAFT = 'draft',
  PUBLISHED = 'published',
  ARCHIVED = 'archived',
}

export enum AccessMode {
  AUTHENTICATED = 'authenticated',
  PUBLIC = 'public',
}

export interface FormConfig {
  id?: number
  name: string
  category?: string
  accessMode: AccessMode
  status?: FormStatus
  submitDeadline?: string
  allowEdit: boolean
  maxEditCount: number
  formSchema: FormSchema
  uiSchema: UISchema
  logicSchema: LogicSchema
  attachments?: AttachmentInfo[]
}

export interface FormCreateRequest {
  name: string
  category?: string
  access_mode: AccessMode
  submit_deadline?: string
  allow_edit: boolean
  max_edit_count: number
  form_schema?: FormSchema
  ui_schema?: UISchema
  logic_schema?: LogicSchema
}

export type FormUpdateRequest = Partial<FormCreateRequest>

export interface FormResponse {
  id: number
  tenant_id: number
  name: string
  category?: string
  access_mode: string
  owner_user_id: number
  status: string
  submit_deadline?: string
  allow_edit: boolean
  max_edit_count: number
  current_version?: number
  total_submissions?: number
  flow_definition_id?: number
  created_at: string
  updated_at: string
  // 前端计算字段，用于控制操作按钮显示
  can_manage?: boolean
}

export interface FormDetailResponse extends FormResponse {
  schema_json: FormSchema
  ui_schema_json: UISchema
  logic_json: LogicSchema
}

export interface FormListQuery {
  page?: number
  page_size?: number
  keyword?: string
  category?: number
  status?: FormStatus
}

export interface FormListResponse {
  items: FormResponse[]
  total: number
  page?: number
  page_size?: number
}

export interface FormTemplateSummary {
  id: number
  name: string
  description?: string
  category?: string
}

export type FormSubmissionPayload = Record<string, unknown>

/**
 * 表单字段相关类型
 */
export interface FormFieldOption {
  label: string
  value: string | number
}

export interface FormField {
  key: string
  name: string
  type: string
  description?: string
  required: boolean
  options?: FormFieldOption[]
  props: Record<string, unknown>
  isSystem?: boolean
}

export interface FormFieldsResponse {
  form_id: number
  form_name: string
  fields: FormField[]
  system_fields: FormField[]
}