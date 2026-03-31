// src/utils/request.ts (完整版 - Naive UI 版本)
/**
 * Axios请求封装 - 配合后端双Token中间件自动刷新
 * 
 * 功能特性:
 * - 自动添加访问令牌和刷新令牌到请求头
 * - 处理后端中间件自动刷新的新令牌
 * - 请求去重和取消机制
 * - 统一错误处理和消息提示（Naive UI）
 * - 文件上传下载支持
 * - 加载动画集成
 */
import axios, { 
  AxiosInstance, 
  AxiosError, 
  AxiosRequestConfig, 
  AxiosResponse,
  InternalAxiosRequestConfig 
} from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useTenantStore } from '@/stores/tenant'
import router from '@/router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import type { Response, PageResponse, ApiMessageBridge, ApiDialogBridge, ApiDialogOptions } from '@/types/api'

import { 
  ERROR_CODES,
  AUTH_ERROR_CODES, 
  PERMISSION_ERROR_CODES,
  VALIDATION_ERROR_CODES,
  SYSTEM_ERROR_CODES
} from '@/constants/errorCodes'

type MessageType = 'success' | 'error' | 'warning' | 'info'
type BusinessErrorData = { errors?: string[]; detail?: string; [key: string]: unknown }
type ApiErrorBody = Response<BusinessErrorData> & { detail?: string }

// ✅ Naive UI 消息和对话框实例（单例模式）
let messageInstance: ApiMessageBridge | null = null
let dialogInstance: ApiDialogBridge | null = null

/**
 * ✅ 设置 Naive UI 实例（在 App.vue 中调用）
 */
export function setNaiveUIInstances(message: ApiMessageBridge, dialog: ApiDialogBridge) {
  messageInstance = message
  dialogInstance = dialog
}

/**
 * ✅ 显示消息的辅助函数
 */
function showMessage(type: MessageType, content: string) {
  if (messageInstance) {
    messageInstance[type](content)
  } else {
    console.warn(`[Message] ${type}: ${content}`)
  }
}

/**
 * ✅ 显示确认对话框的辅助函数
 */
function showConfirm(options: ApiDialogOptions & { type?: MessageType }): Promise<boolean> {
  return new Promise((resolve) => {
    if (dialogInstance) {
      dialogInstance[options.type || 'warning']({
        title: options.title,
        content: options.content,
        positiveText: options.positiveText || '确定',
        negativeText: options.negativeText || '取消',
        onPositiveClick: async () => {
          await options.onPositiveClick?.()
          resolve(true)
        },
        onNegativeClick: async () => {
          await options.onNegativeClick?.()
          resolve(false)
        },
        onClose: () => {
          options.onClose?.()
          resolve(false)
        }
      })
    } else {
      console.warn(`[Dialog] ${options.title}: ${options.content}`)
      resolve(false)
    }
  })
}

// 请求队列项类型
interface PendingRequest {
  url: string
  cancel: () => void
}

// 扩展的请求配置类型
interface CustomAxiosRequestConfig extends InternalAxiosRequestConfig {
  skipErrorHandler?: boolean  // 跳过统一错误处理
  skipLoading?: boolean       // 跳过加载动画
  retry?: number              // 重试次数
}

// 请求队列管理类
class RequestQueue {
  private pending = new Map<string, PendingRequest>()
  
  /**
   * 生成请求的唯一标识
   */
  private getKey(config: AxiosRequestConfig): string {
    const { method = 'get', url, params, data } = config
    return [method, url, JSON.stringify(params), JSON.stringify(data)].join('&')
  }
  
  /**
   * 添加请求到队列
   */
  add(config: CustomAxiosRequestConfig): void {
    const key = this.getKey(config)
    this.remove(key)
    
    const source = axios.CancelToken.source()
    config.cancelToken = source.token
    
    this.pending.set(key, {
      url: config.url || '',
      cancel: source.cancel
    })
  }
  
  /**
   * 从队列中移除请求
   */
  remove(keyOrConfig: string | AxiosRequestConfig): void {
    const key = typeof keyOrConfig === 'string' ? keyOrConfig : this.getKey(keyOrConfig)
    const request = this.pending.get(key)
    if (request) {
      request.cancel()
      this.pending.delete(key)
    }
  }
  
  /**
   * 清空所有待处理请求
   */
  clear(): void {
    this.pending.forEach(request => request.cancel())
    this.pending.clear()
  }
  
  /**
   * 获取待处理请求数量
   */
  size(): number {
    return this.pending.size
  }
}

// 创建请求队列实例
const requestQueue = new RequestQueue()

// 创建axios实例
const service: AxiosInstance = axios.create({
  baseURL: '',  // 使用空字符串，让Vite代理处理/api路径
  timeout: 10000,  // 10秒超时，快速反馈网络问题
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
service.interceptors.request.use(
  (config: CustomAxiosRequestConfig) => {
    // 显示加载动画
    if (!config.skipLoading) {
      NProgress.start()
    }
    
    // 添加到请求队列（防重复请求）
    // 跳过附件下载请求，因为多个图片可能同时加载
    const isAttachmentDownload = config.url?.includes('/attachments/') && config.url?.includes('/download')
    if (!isAttachmentDownload) {
      requestQueue.add(config)
    }
    
    // 获取认证store
    const authStore = useAuthStore()
    
    // 设置访问令牌
    const accessToken = authStore.getAccessToken()
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }
    
    // 设置刷新令牌（配合后端中间件自动刷新）
    const refreshToken = authStore.refreshToken || localStorage.getItem('refresh_token')
    if (refreshToken) {
      config.headers['X-Refresh-Token'] = refreshToken
    }
    
    // 设置租户ID
    const tenantStore = useTenantStore()
    if (tenantStore.tenantId) {
      config.headers['X-Tenant-ID'] = String(tenantStore.tenantId)
    }
    
    // 设置请求时间戳（用于调试）
    config.headers['X-Request-Time'] = Date.now().toString()
    
    return config
  },
  (error: AxiosError) => {
    NProgress.done()
    console.error('Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  async (response: AxiosResponse<Response>) => {
    NProgress.done()
    
    
    const config = response.config as CustomAxiosRequestConfig
    
    // 从请求队列中移除已完成的请求
    requestQueue.remove(config)
    
    // 处理令牌轮转
    const authStore = useAuthStore()
    handleTokenRotation(response, authStore)
    
    // 文件下载请求直接返回原始响应
    if (config.responseType === 'blob') {
      return response as AxiosResponse<Response<unknown>>
    }
    
    const res = response.data as ApiErrorBody
    
    // 处理业务层面的错误（使用四位数错误码）
    if (res.code !== ERROR_CODES.SUCCESS) {
      // 根据错误类型进行不同处理（不要await，避免阻塞）
      handleBusinessError(res, config, authStore)
      
      return Promise.reject(new Error(res.message || '操作失败'))
    }
    
    return response
  },
  
  async (error: AxiosError<ApiErrorBody>) => {
    NProgress.done()
    
    const config = error.config as CustomAxiosRequestConfig
    
    // 从请求队列中移除失败的请求
    if (config) {
      requestQueue.remove(config)
    }
    
    // 取消的请求静默处理，返回空响应
    if (axios.isCancel(error)) {
      return Promise.resolve({ 
        data: { code: 0, data: null, message: 'canceled' }, 
        status: 0, 
        statusText: 'canceled', 
        headers: {}, 
        config: error.config || {} 
      })
    }
    
    // 重试机制
    if (config?.retry && config.retry > 0) {
      config.retry--
      console.log(`Retrying request, ${config.retry} attempts left`)
      return service(config)
    }
    
    // 处理网络错误和其他异常（不要await，避免阻塞）
    handleNetworkError(error, config)
    
    return Promise.reject(error)
  }
)

/**
 * 处理业务错误
 */
async function handleBusinessError(
  res: ApiErrorBody,
  config: CustomAxiosRequestConfig,
  authStore: ReturnType<typeof useAuthStore>
) {
  const { code, message, data } = res
  
  // 显示错误消息（除非明确跳过）
  if (!config.skipErrorHandler) {
    // 特殊处理参数验证错误，显示详细信息
    if (VALIDATION_ERROR_CODES.includes(code) && data?.errors) {
      const errorDetails = Array.isArray(data.errors) ? data.errors.join('; ') : message
      showMessage('error', `参数验证失败: ${errorDetails}`)
    } else {
      showMessage('error', message || '操作失败')
    }
  }
  
  // 根据错误码进行特殊处理
  if (AUTH_ERROR_CODES.includes(code)) {
    // 认证错误：清除状态并跳转登录页（不要await，避免阻塞）
    handleAuthError(config, authStore, message)
    
  } else if (PERMISSION_ERROR_CODES.includes(code)) {
    // 权限错误：只显示消息，不跳转
    console.log(`权限错误 [${code}]: ${message}`)
    
  } else if (code === ERROR_CODES.RATE_LIMIT) {
    // 频率限制：显示特殊提示
    if (!config.skipErrorHandler) {
      showMessage('warning', '操作过于频繁，请稍后再试')
    }
    
  } else if (SYSTEM_ERROR_CODES.includes(code)) {
    // 系统错误：显示技术支持提示
    if (!config.skipErrorHandler) {
      showMessage('error', `${message || '系统错误'}，如问题持续请联系技术支持`)
    }
  }
}

/**
 * 处理认证错误
 */
function handleAuthError(
  config: CustomAxiosRequestConfig,
  authStore: ReturnType<typeof useAuthStore>,
  message: string
) {
  // 如果是登录接口的认证错误，不需要跳转
  if (config.url?.includes('/login')) {
    console.log('登录接口认证失败，已显示错误消息')
    return
  }
  
  // 其他接口的认证错误，需要跳转到登录页
  // 不要await，避免阻塞响应处理
  showConfirm({
    title: '认证过期',
    content: message || '登录状态已过期，请重新登录',
    positiveText: '重新登录',
    negativeText: '取消',
    type: 'warning'
  }).then(() => {
    // 无论用户是否确认，都清除认证状态并跳转
    authStore.clearAuth()
    router.push('/login')
  })
}

// src/utils/request.ts

/**
 * 处理网络错误
 */
function handleNetworkError(
  error: AxiosError<ApiErrorBody>,
  config: CustomAxiosRequestConfig
) {
  if (config?.skipErrorHandler) {
    return
  }

  let errorMessage = '网络错误'

  // ✅ 优先检查响应数据（正常的 HTTP 错误）
  if (error.response?.data) {
    // 后端返回了错误信息
    const res = error.response.data

    // ✅ 特殊处理 422 验证错误
    if (error.response.status === 422) {
      const data = res.data as BusinessErrorData | undefined
      if (data?.errors && Array.isArray(data.errors)) {
        const errorDetails = data.errors.join('; ')
        showMessage('error', `参数验证失败: ${errorDetails}`)
      } else {
        showMessage('error', res.message || '请求参数验证失败')
      }
      return
    }

    errorMessage = res.message || res.detail || '请求失败'

    // ✅ 特殊处理 401 错误
    if (error.response.status === 401) {
      const authStore = useAuthStore()

      // 检查是否是登录接口
      if (!config.url?.includes('/login')) {
        // 非登录接口的 401 错误，清除认证状态并跳转
        showMessage('warning', errorMessage || '登录已过期，请重新登录')
        authStore.clearAuth()
        router.push('/login')
        return
      }
    }

  } else if (error.code) {
    // ✅ 网络层错误或 CORS 错误
    switch (error.code) {
      case 'NETWORK_ERROR':
      case 'ERR_NETWORK':
        // 网络连接失败，不要自动清除认证状态
        // 因为这可能只是临时的网络问题，而不是认证过期
        errorMessage = '网络连接失败，请检查网络设置或稍后重试'
        break
      
      case 'TIMEOUT':
      case 'ECONNABORTED':
        errorMessage = '请求超时，请稍后重试'
        break
      
      case 'ERR_CANCELED':
        return // 请求被取消，不显示错误
      
      default:
        errorMessage = `网络错误: ${error.code}`
    }
  } else if (error.message) {
    errorMessage = error.message
  }
  
  showMessage('error', errorMessage)
}

/**
 * 处理令牌轮转逻辑
 */
function handleTokenRotation(response: AxiosResponse, authStore: ReturnType<typeof useAuthStore>) {
  const headers = response.headers
  
  // 检查是否有新的访问令牌
  const newAccessToken = headers['x-new-access-token']
  const tokenRefreshed = headers['x-token-refreshed']
  
  if (newAccessToken && tokenRefreshed === 'true') {
    // 更新内存中的访问令牌
    authStore.updateAccessToken(newAccessToken)
    console.log('刷新令牌')
    console.log('🔄 Access token auto-refreshed by backend middleware')
  }
  
  // 检查是否有新的刷新令牌（轮转）
  const newRefreshToken = headers['x-new-refresh-token'] 
  const tokenRotated = headers['x-token-rotated']
  
  if (newRefreshToken && tokenRotated === 'true') {
    authStore.updateRefreshToken(newRefreshToken)
    console.log('🔄 Refresh token rotated by backend')
  }
}

// HTTP请求类 - 提供各种请求方法
class HttpRequest {
  /**
   * GET请求
   */
  get<TResponse = unknown, TParams extends object | undefined = undefined>(
    url: string, 
    params?: TParams, 
    config?: AxiosRequestConfig
  ): Promise<Response<TResponse>> {
    return service
      .get<Response<TResponse>>(url, { params, ...config })
      .then(({ data }) => data)
  }
  
  /**
   * POST请求
   */
  post<TResponse = unknown, TBody extends object | FormData | undefined = undefined>(
    url: string, 
    data?: TBody, 
    config?: AxiosRequestConfig
  ): Promise<Response<TResponse>> {
    return service
      .post<Response<TResponse>>(url, data, config)
      .then(({ data: responseData }) => responseData)
  }
  
  /**
   * PUT请求
   */
  put<TResponse = unknown, TBody extends object | FormData | undefined = undefined>(
    url: string, 
    data?: TBody, 
    config?: AxiosRequestConfig
  ): Promise<Response<TResponse>> {
    return service
      .put<Response<TResponse>>(url, data, config)
      .then(({ data: responseData }) => responseData)
  }
  
  /**
   * PATCH请求
   */
  patch<TResponse = unknown, TBody extends object | FormData | undefined = undefined>(
    url: string, 
    data?: TBody, 
    config?: AxiosRequestConfig
  ): Promise<Response<TResponse>> {
    return service
      .patch<Response<TResponse>>(url, data, config)
      .then(({ data: responseData }) => responseData)
  }
  
  /**
   * DELETE请求
   */
  delete<TResponse = unknown, TParams extends object | undefined = undefined>(
    url: string, 
    params?: TParams, 
    config?: AxiosRequestConfig
  ): Promise<Response<TResponse>> {
    return service
      .delete<Response<TResponse>>(url, { params, ...config })
      .then(({ data }) => data)
  }
  
  /**
   * 分页请求
   */
  page<TResponse = unknown, TParams extends object | undefined = undefined>(
    url: string,
    params?: TParams,
    config?: AxiosRequestConfig
  ): Promise<PageResponse<TResponse>> {
    return service
      .get<PageResponse<TResponse>>(url, { params, ...config })
      .then(({ data }) => data)
  }
  
  /**
   * 文件上传
   */
  async upload<TResponse = unknown>(
    url: string,
    file: File,
    data?: Record<string, string | number | boolean>,
    onProgress?: (percent: number) => void
  ): Promise<Response<TResponse>> {
    const formData = new FormData()
    formData.append('file', file)
    
    // 添加额外的表单数据
    if (data) {
      Object.entries(data).forEach(([key, value]) => {
        formData.append(key, String(value))
      })
    }
    
    return service.post<Response<TResponse>>(url, formData, {
      headers: { 
        'Content-Type': 'multipart/form-data' 
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent)
        }
      },
    }).then(({ data: responseData }) => responseData)
  }
  
  /**
   * 多文件上传
   */
  async uploadMultiple<TResponse = unknown>(
    url: string,
    files: File[],
    data?: Record<string, string | number | boolean>,
    onProgress?: (percent: number) => void
  ): Promise<Response<TResponse>> {
    const formData = new FormData()
    
    // 添加文件
    files.forEach((file, index) => {
      formData.append(`files[${index}]`, file)
    })
    
    // 添加额外数据
    if (data) {
      Object.entries(data).forEach(([key, value]) => {
        formData.append(key, String(value))
      })
    }
    
    return service.post<Response<TResponse>>(url, formData, {
      headers: { 
        'Content-Type': 'multipart/form-data' 
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent)
        }
      },
    }).then(({ data: responseData }) => responseData)
  }
  
  /**
   * 文件下载
   */
  async download(
    url: string,
    params?: Record<string, unknown>,
    fileName?: string
  ): Promise<void> {
    try {
      const response = await service.get(url, {
        params,
        responseType: 'blob',
      })
      
      // 创建下载链接
      const blob = new Blob([response.data])
      const downloadUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      
      // 尝试从响应头获取文件名
      const contentDisposition = response.headers['content-disposition']
      let finalFileName = fileName
      
      if (contentDisposition && !finalFileName) {
        const fileNameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
        if (fileNameMatch && fileNameMatch[1]) {
          finalFileName = fileNameMatch[1].replace(/['"]/g, '')
        }
      }
      
      link.download = finalFileName || 'download'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(downloadUrl)
      
      showMessage('success', '文件下载成功')
    } catch (error) {
      console.error('Download failed:', error)
      showMessage('error', '文件下载失败')
      throw error
    }
  }
  
  /**
   * 请求重试
   */
  async retry<T>(
    requestFn: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> {
    let lastError: Error
    
    for (let i = 0; i <= maxRetries; i++) {
      try {
        return await requestFn()
      } catch (error) {
        lastError = error as Error
        
        if (i < maxRetries) {
          console.log(`Request failed, retrying in ${delay}ms... (${i + 1}/${maxRetries})`)
          await new Promise(resolve => setTimeout(resolve, delay))
          delay *= 2 // 指数退避
        }
      }
    }
    
    throw lastError!
  }
  
  /**
   * 并发请求控制
   */
  async concurrent<T>(
    requests: Array<() => Promise<T>>,
    concurrency: number = 3
  ): Promise<T[]> {
    const results: T[] = []
    const executing: Promise<void>[] = []
    
    for (const request of requests) {
      const promise = request().then(result => {
        results.push(result)
      })
      
      executing.push(promise)
      
      if (executing.length >= concurrency) {
        await Promise.race(executing)
        executing.splice(executing.findIndex(p => p === promise), 1)
      }
    }
    
    await Promise.all(executing)
    return results
  }
  
  /**
   * 取消所有待处理请求
   */
  cancelAll(): void {
    requestQueue.clear()
  }
  
  /**
   * 获取待处理请求数量
   */
  getPendingCount(): number {
    return requestQueue.size()
  }
}

// 创建HTTP请求实例
const request = new HttpRequest()

// 导出
export default request

// 导出其他实例和类型
export { 
  service, 
  requestQueue, 
  HttpRequest,
  type CustomAxiosRequestConfig,
  type PendingRequest
}

// 导出API响应类型
export type { Response, PageResponse } from '@/types/api'

// 导出便捷方法
export const http = {
  get: request.get.bind(request),
  post: request.post.bind(request),
  put: request.put.bind(request),
  patch: request.patch.bind(request),
  delete: request.delete.bind(request),
  page: request.page.bind(request),
  upload: request.upload.bind(request),
  download: request.download.bind(request),
}