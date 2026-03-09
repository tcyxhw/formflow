// src/api/ai.ts
/**
 * AI 相关 API
 */
import request from '@/utils/request'
import type { Response } from '@/types/api'
import type { 
  AIFormGenerateRequest, 
  AIFormGenerateResponse
} from '@/types/ai'
import { ThinkingType } from '@/types/ai'

const AI_BASE_PATH = '/api/v1/ai'

/**
 * AI 生成表单配置
 * 
 * @param data - 生成请求参数
 * @param data.prompt - 表单需求描述（5-2000字符）
 * @param data.thinking_type - AI 思考模式（可选，默认 enabled）
 * @returns Promise<Response<AIFormGenerateResponse>>
 * 
 * @example
 * ```typescript
 * // 简单生成
 * const result = await generateFormByAI({
 *   prompt: '创建一个用户反馈表，需要姓名、邮箱、反馈内容'
 * })
 * 
 * // 复杂生成（启用深度思考）
 * const result = await generateFormByAI({
 *   prompt: '创建一个学生请假申请表，包含请假类型、时间、病假需要上传证明',
 *   thinking_type: ThinkingType.ENABLED
 * })
 * 
 * // 简单任务（禁用思考，更快速）
 * const result = await generateFormByAI({
 *   prompt: '创建一个简单的问卷调查表',
 *   thinking_type: ThinkingType.DISABLED
 * })
 * ```
 */
export const generateFormByAI = (
  data: AIFormGenerateRequest
): Promise<Response<AIFormGenerateResponse>> => {
  return request.post(`${AI_BASE_PATH}/generate-form`, data)
}

/**
 * AI 生成表单配置（简化版，使用默认思考模式）
 * 
 * @param prompt - 表单需求描述
 * @returns Promise<Response<AIFormGenerateResponse>>
 * 
 * @example
 * ```typescript
 * const result = await quickGenerateForm('创建一个活动报名表')
 * ```
 */
export const quickGenerateForm = (
  prompt: string
): Promise<Response<AIFormGenerateResponse>> => {
  return generateFormByAI({ prompt })
}

/**
 * AI 生成表单配置（高级版，自定义思考模式）
 * 
 * @param prompt - 表单需求描述
 * @param thinkingType - 思考模式
 * @returns Promise<Response<AIFormGenerateResponse>>
 * 
 * @example
 * ```typescript
 * import { ThinkingType } from '@/types/ai'
 * 
 * // 复杂任务
 * const result = await advancedGenerateForm(
 *   '创建一个包含复杂逻辑的员工绩效评估表',
 *   ThinkingType.ENABLED
 * )
 * 
 * // 简单任务
 * const result = await advancedGenerateForm(
 *   '创建一个问卷调查表',
 *   ThinkingType.DISABLED
 * )
 * ```
 */
export const advancedGenerateForm = (
  prompt: string,
  thinkingType: ThinkingType = ThinkingType.ENABLED
): Promise<Response<AIFormGenerateResponse>> => {
  return generateFormByAI({
    prompt,
    thinking_type: thinkingType
  })
}

/**
 * 查询任务状态
 */
export const getTaskStatus = (
    taskId: string
  ): Promise<Response<{
    task_id: string
    status: 'pending' | 'processing' | 'completed' | 'failed'
    result?: AIFormGenerateResponse
    error?: string
  }>> => {
    return request.get(`${AI_BASE_PATH}/task/${taskId}`)
  }