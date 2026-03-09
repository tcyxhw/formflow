// src/api/submission.ts
/**
 * 表单提交相关 API
 */
import request from '@/utils/request'
import type { Response } from '@/types/api'
import type {
  CreateSubmissionRequest,
  UpdateSubmissionRequest,
  SubmissionDetail,
  SubmissionListResponse,
  SubmissionQueryParams,
  SubmissionStatistics,
  SubmissionDraft,
  MessageResponse,
  SubmissionExportRequest,
  SubmissionExportAsyncResponse,
  SubmissionExportSyncResponse,
  SubmissionExportTask,
} from '@/types/submission'

const BASE_PATH = '/api/v1/submissions'
const DRAFT_PATH = `${BASE_PATH}/drafts`
const EXPORT_PATH = `${BASE_PATH}/export`

/**
 * 创建提交
 * POST /submissions
 */
export const createSubmission = (
  data: CreateSubmissionRequest
): Promise<Response<SubmissionDetail>> => {
  return request.post(`${BASE_PATH}`, data)
}

/**
 * 更新提交
 * PUT /submissions/{submission_id}
 */
export const updateSubmission = (
  submissionId: number,
  data: UpdateSubmissionRequest['data']
): Promise<Response<SubmissionDetail>> => {
  return request.put(`${BASE_PATH}/${submissionId}`, { data })
}

/**
 * 删除提交
 * DELETE /submissions/{submission_id}
 */
export const deleteSubmission = (
  submissionId: number
): Promise<Response<MessageResponse>> => {
  return request.delete(`${BASE_PATH}/${submissionId}`)
}

/**
 * 获取提交详情
 * GET /submissions/{submission_id}
 */
export const getSubmissionDetail = (
  submissionId: number
): Promise<Response<SubmissionDetail>> => {
  return request.get(`${BASE_PATH}/${submissionId}`)
}

/**
 * 查询提交列表
 * GET /submissions
 */
export const getSubmissionList = (
  params?: SubmissionQueryParams
): Promise<Response<SubmissionListResponse>> => {
  return request.get(`${BASE_PATH}`, params)
}

/**
 * 提交统计
 * GET /submissions/statistics/{form_id}
 */
export const getSubmissionStatistics = (
  formId: number
): Promise<Response<SubmissionStatistics>> => {
  return request.get(`${BASE_PATH}/statistics/${formId}`)
}

/**
 * 保存草稿
 * POST /submissions/drafts
 */
export const saveDraft = (
  data: { form_id: number; data: SubmissionDraft['draft_data'] }
): Promise<Response<SubmissionDraft>> => {
  return request.post(`${DRAFT_PATH}`, data)
}

/**
 * 获取草稿
 * GET /submissions/drafts/{form_id}
 */
export const getDraft = (
  formId: number
): Promise<Response<SubmissionDraft | null>> => {
  return request.get(`${DRAFT_PATH}/${formId}`)
}

/**
 * 删除草稿
 * DELETE /submissions/drafts/{draft_id}
 */
export const deleteDraft = (
  draftId: number
): Promise<Response<MessageResponse>> => {
  return request.delete(`${DRAFT_PATH}/${draftId}`)
}

/**
 * 导出提交数据
 * POST /submissions/export
 * 返回同步或异步响应
 */
export const exportSubmissions = (
  data: SubmissionExportRequest
): Promise<Response<SubmissionExportSyncResponse | SubmissionExportAsyncResponse>> => {
  return request.post(`${EXPORT_PATH}`, data)
}

/**
 * 查询导出任务状态
 * GET /submissions/export/{task_id}
 */
export const getExportTask = (
  taskId: string
): Promise<Response<SubmissionExportTask>> => {
  return request.get(`${EXPORT_PATH}/${taskId}`)
}

export default {
  createSubmission,
  updateSubmission,
  deleteSubmission,
  getSubmissionDetail,
  getSubmissionList,
  getSubmissionStatistics,
  saveDraft,
  getDraft,
  deleteDraft,
  exportSubmissions,
  getExportTask,
}
