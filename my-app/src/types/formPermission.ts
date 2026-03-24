/**
 * 表单权限相关类型定义
 */
export type GrantType = 'user' | 'role' | 'department' | 'position'

export type PermissionType = 'view' | 'fill' | 'edit' | 'export' | 'manage'

export interface FormPermissionPayload {
  /** 授权类型 */
  grant_type: GrantType
  /** 授权对象ID */
  grantee_id: number
  /** 权限类型 */
  permission: PermissionType
  /** 生效时间 (ISO 字符串，可为空) */
  valid_from?: string | null
  /** 失效时间 (ISO 字符串，可为空) */
  valid_to?: string | null
}

export interface FormPermissionUpdatePayload {
  /** 生效时间 (ISO 字符串，可为空) */
  valid_from?: string | null
  /** 失效时间 (ISO 字符串，可为空) */
  valid_to?: string | null
}

export interface FormPermission extends FormPermissionPayload {
  id: number
  form_id: number
  tenant_id: number
  /** 授权对象名称 */
  grantee_name?: string
  created_at: string
  updated_at: string
}

export interface FormPermissionOverview {
  /** 已授予权限列表 */
  permissions: PermissionType[]
  /** 能否查看 */
  can_view: boolean
  /** 能否填写 */
  can_fill: boolean
  /** 能否编辑 */
  can_edit: boolean
  /** 能否导出 */
  can_export: boolean
  /** 能否管理 */
  can_manage: boolean
  /** 是否表单拥有者 */
  is_owner: boolean
}

export interface FormPermissionListResponse {
  /** 权限记录 */
  items: FormPermission[]
  /** 总数 */
  total: number
}
