/**
 * 表单分类类型定义
 */

export interface Category {
  id: number
  name: string
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface CategoryCreateRequest {
  name: string
}

export interface CategoryUpdateRequest {
  name: string
}

export interface CategoryResponse {
  id: number
  name: string
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface CategoryListResponse {
  items: CategoryResponse[]
  total: number
  page: number
  page_size: number
}
