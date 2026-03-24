/**
 * 表单分类API客户端
 */
import { http } from '@/utils/http'
import type {
  Category,
  CategoryCreateRequest,
  CategoryUpdateRequest,
  CategoryListResponse,
  CategoryResponse
} from '@/types/category'

/**
 * 获取分类列表
 */
export const listCategories = (page: number = 1, pageSize: number = 20) => {
  return http.get<{ data: CategoryListResponse }>('/categories', {
    params: {
      page,
      page_size: pageSize
    }
  })
}

/**
 * 创建分类
 */
export const createCategory = (data: CategoryCreateRequest) => {
  return http.post<{ data: CategoryResponse }>('/categories', data)
}

/**
 * 更新分类
 */
export const updateCategory = (categoryId: number, data: CategoryUpdateRequest) => {
  return http.put<{ data: CategoryResponse }>(`/categories/${categoryId}`, data)
}

/**
 * 删除分类
 */
export const deleteCategory = (categoryId: number) => {
  return http.delete(`/categories/${categoryId}`)
}
