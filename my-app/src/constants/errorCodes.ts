// src/constants/errorCodes.ts
/**
 * 错误码常量定义
 * 与后端 app/core/exceptions.py 中的 ERROR_CODES 保持完全一致
 */
export const ERROR_CODES = {
  // 成功
  SUCCESS: 200,
  
  // 4xxx 客户端错误
  VALIDATION_FAILED: 4001,        // "验证失败"
  
  // 认证错误 401x
  AUTH_FAILED: 4011,              // "未登录或登录已过期"
  TOKEN_INVALID: 4012,            // "Token无效"
  TOKEN_EXPIRED: 4013,            // "Token已过期"
  
  // 授权错误 403x
  PERMISSION_DENIED: 4031,        // "权限不足"
  ROLE_INSUFFICIENT: 4032,        // "角色权限不足"
  DATA_PERMISSION: 4033,          // "数据权限不足"
  
  // 资源错误 404x
  RESOURCE_NOT_FOUND: 4041,       // "资源不存在"
  USER_NOT_FOUND: 4042,           // "用户不存在"
  FORM_NOT_FOUND: 4043,           // "表单不存在"
  
  // 频率限制 429x
  RATE_LIMIT: 4291,               // "请求过于频繁"
  
  // 5xxx 服务端错误
  BUSINESS_ERROR: 5001,           // "业务处理失败"
  DATABASE_ERROR: 5002,           // "数据库操作失败"
  EXTERNAL_SERVICE: 5003,         // "外部服务调用失败"
  FILE_ERROR: 5004,               // "文件处理失败"
  CACHE_ERROR: 5005,              // "缓存操作失败"
  
  // 全局异常处理器中使用的错误码
  SYSTEM_ERROR: 5000,             // "系统内部错误" (general_exception_handler)
  VALIDATION_PARAMS: 4220,        // "请求参数验证失败" (validation_exception_handler)
} as const

/**
 * 错误码分组 - 根据后端异常类型分组
 */

// 🔧 修复：认证相关错误（AuthenticationError - 需要重新登录）
export const AUTH_ERROR_CODES: number[] = [
  ERROR_CODES.AUTH_FAILED,        // 4011
  ERROR_CODES.TOKEN_INVALID,      // 4012
  ERROR_CODES.TOKEN_EXPIRED       // 4013
]

// 🔧 修复：权限相关错误（AuthorizationError - 显示权限提示）
export const PERMISSION_ERROR_CODES: number[] = [
  ERROR_CODES.PERMISSION_DENIED,  // 4031
  ERROR_CODES.ROLE_INSUFFICIENT,  // 4032
  ERROR_CODES.DATA_PERMISSION     // 4033
]

// 🔧 修复：验证相关错误（ValidationError + RequestValidationError）
export const VALIDATION_ERROR_CODES: number[] = [
  ERROR_CODES.VALIDATION_FAILED,  // 4001 - ValidationError
  ERROR_CODES.VALIDATION_PARAMS   // 4220 - RequestValidationError
]

// 🔧 修复：资源不存在错误（NotFoundError）
export const NOT_FOUND_ERROR_CODES: number[] = [
  ERROR_CODES.RESOURCE_NOT_FOUND, // 4041
  ERROR_CODES.USER_NOT_FOUND,     // 4042
  ERROR_CODES.FORM_NOT_FOUND      // 4043
]

// 🔧 修复：业务错误（BusinessError）
export const BUSINESS_ERROR_CODES: number[] = [
  ERROR_CODES.BUSINESS_ERROR      // 5001
]

// 🔧 修复：频率限制错误（RateLimitError）
export const RATE_LIMIT_ERROR_CODES: number[] = [
  ERROR_CODES.RATE_LIMIT          // 4291
]

// 🔧 修复：数据库错误（DatabaseError + SQLAlchemyError）
export const DATABASE_ERROR_CODES: number[] = [
  ERROR_CODES.DATABASE_ERROR      // 5002
]

// 🔧 修复：外部服务错误（ExternalServiceError）
export const EXTERNAL_SERVICE_ERROR_CODES: number[] = [
  ERROR_CODES.EXTERNAL_SERVICE    // 5003
]

// 🔧 修复：系统错误（需要联系管理员）
export const SYSTEM_ERROR_CODES: number[] = [
  ERROR_CODES.FILE_ERROR,         // 5004
  ERROR_CODES.CACHE_ERROR,        // 5005
  ERROR_CODES.SYSTEM_ERROR        // 5000 - 兜底错误
]

/**
 * 错误码描述映射 - 与后端保持一致
 */
export const ERROR_MESSAGES: { [key: number]: string } = {
  // 4xxx 客户端错误
  [ERROR_CODES.VALIDATION_FAILED]: "验证失败",
  [ERROR_CODES.AUTH_FAILED]: "未登录或登录已过期",
  [ERROR_CODES.TOKEN_INVALID]: "Token无效",
  [ERROR_CODES.TOKEN_EXPIRED]: "Token已过期",
  [ERROR_CODES.PERMISSION_DENIED]: "权限不足",
  [ERROR_CODES.ROLE_INSUFFICIENT]: "角色权限不足",
  [ERROR_CODES.DATA_PERMISSION]: "数据权限不足",
  [ERROR_CODES.RESOURCE_NOT_FOUND]: "资源不存在",
  [ERROR_CODES.USER_NOT_FOUND]: "用户不存在",
  [ERROR_CODES.FORM_NOT_FOUND]: "表单不存在",
  [ERROR_CODES.RATE_LIMIT]: "请求过于频繁",
  
  // 5xxx 服务端错误
  [ERROR_CODES.BUSINESS_ERROR]: "业务处理失败",
  [ERROR_CODES.DATABASE_ERROR]: "数据库操作失败",
  [ERROR_CODES.EXTERNAL_SERVICE]: "外部服务调用失败",
  [ERROR_CODES.FILE_ERROR]: "文件处理失败",
  [ERROR_CODES.CACHE_ERROR]: "缓存操作失败",
  
  // 异常处理器错误码
  [ERROR_CODES.SYSTEM_ERROR]: "系统内部错误",
  [ERROR_CODES.VALIDATION_PARAMS]: "请求参数验证失败"
}

/**
 * 根据错误码获取默认错误信息
 */
export function getErrorMessage(code: number): string {
  return ERROR_MESSAGES[code] || `未知错误 (${code})`
}

/**
 * 判断是否为认证错误
 */
export function isAuthError(code: number): boolean {
  return AUTH_ERROR_CODES.includes(code)
}

/**
 * 判断是否为权限错误
 */
export function isPermissionError(code: number): boolean {
  return PERMISSION_ERROR_CODES.includes(code)
}

/**
 * 判断是否为系统错误
 */
export function isSystemError(code: number): boolean {
  return SYSTEM_ERROR_CODES.includes(code)
}

/**
 * 判断是否为验证错误
 */
export function isValidationError(code: number): boolean {
  return VALIDATION_ERROR_CODES.includes(code)
}