// src/types/api.ts
/**
 * API响应类型定义 - 根据后端Schema生成
 */

// 基础响应接口
export interface Response<T = unknown> {
  code: number
  message: string
  data: T
  timestamp?: number
}

// 分页响应接口
export interface PageResponse<T = unknown> {
  code: number
  message: string
  data: {
    items: T[]
    total: number
    page: number
    size: number
    pages: number
  }
  timestamp?: number
}

// 分页请求参数
export interface PageParams {
  page?: number
  size?: number
  sort?: string
  order?: 'asc' | 'desc'
}

// 批量操作结果
export interface BatchOperationResult {
  success_count: number
  failed_count: number
  failed_items: Array<Record<string, unknown>>
  message: string
}

// 上传响应
export interface UploadResponse {
  url: string
  filename: string
  size: number
  type: string
}

export interface ApiMessageBridge {
  success: (content: string) => void
  error: (content: string) => void
  warning: (content: string) => void
  info: (content: string) => void
}

export interface ApiDialogOptions {
  title: string
  content: string
  positiveText?: string
  negativeText?: string
  onPositiveClick?: () => void | Promise<void>
  onNegativeClick?: () => void | Promise<void>
  onClose?: () => void
}

export interface ApiDialogBridge {
  warning: (options: ApiDialogOptions) => void
  error: (options: ApiDialogOptions) => void
  info: (options: ApiDialogOptions) => void
  success: (options: ApiDialogOptions) => void
}