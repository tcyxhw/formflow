// src/types/workspace.ts
/**
 * 表单填写工作区类型定义 - 根据后端Schema生成
 */

/**
 * 可填写表单项
 */
export interface FillableFormItem {
  id: number
  name: string
  category: string | null
  status: string
  owner_name: string
  created_at: string
  updated_at: string
  submit_deadline: string | null
  is_expired: boolean
  is_closed: boolean
  is_fill_limit_reached: boolean
  can_fill: boolean
  description: string | null
}

/**
 * 可填写表单列表响应
 */
export interface FillableFormsResponse {
  items: FillableFormItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * 可填写表单查询参数
 */
export interface FillableFormsQuery {
  page?: number
  page_size?: number
  keyword?: string
  status?: string
  category?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  search_type?: 'name' | 'owner'
}

/**
 * 筛选状态
 */
export interface FilterState {
  keyword: string
  status: string | null
  category: string | null
  sortBy: string
  sortOrder: 'asc' | 'desc'
  dateRange?: { start: string; end: string } | null
  searchType?: 'name' | 'owner'
}

/**
 * 分页状态
 */
export interface PaginationState {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

/**
 * 快捷入口响应
 */
export interface QuickAccessResponse {
  items: FillableFormItem[]
}
