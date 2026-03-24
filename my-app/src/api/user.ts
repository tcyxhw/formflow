/**
 * 用户相关 API
 */
import request from '@/utils/request'
import type { Response } from '@/types/api'

const USER_BASE_PATH = '/api/v1/users'

/**
 * 用户列表项（简化版）
 */
export interface UserListItem {
  id: number
  name: string
  account: string
  email?: string
}

/**
 * 用户列表响应
 */
export interface UserListResponse {
  items: UserListItem[]
  total: number
}

/**
 * 用户列表查询参数
 */
export interface UserListParams {
  keyword?: string
  page?: number
  size?: number
}

/**
 * 获取用户列表（简化版，用于选择器）
 * GET /api/v1/users/list
 * 
 * @param params 查询参数
 * @returns 用户列表
 */
export const listUsers = (params?: UserListParams): Promise<Response<UserListResponse>> => {
  return request.get(`${USER_BASE_PATH}/list`, { params })
}

// 导出所有用户相关的API函数
export default {
  listUsers
}
