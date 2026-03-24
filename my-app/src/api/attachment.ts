// src/api/attachment.ts
/**
 * 附件相关 API
 */
import request from '@/utils/request'
import type { Response } from '@/types/api'
import type { AttachmentInfo } from '@/types/attachment'

const BASE_PATH = '/api/v1/attachments'

/**
 * 上传附件
 * POST /attachments/upload
 */
export const uploadAttachment = (
  file: File
): Promise<Response<AttachmentInfo>> => {
  return request.upload(`${BASE_PATH}/upload`, file)
}

/**
 * 获取附件信息
 * GET /attachments/{attachment_id}
 */
export const getAttachment = (
  attachmentId: number
): Promise<Response<AttachmentInfo>> => {
  return request.get(`${BASE_PATH}/${attachmentId}`)
}

/**
 * 删除附件
 * DELETE /attachments/{attachment_id}
 */
export const deleteAttachment = (
  attachmentId: number
): Promise<Response<{ message: string }>> => {
  return request.delete(`${BASE_PATH}/${attachmentId}`)
}

/**
 * 下载附件
 * GET /attachments/{attachment_id}/download
 */
export const downloadAttachment = async (
  attachmentId: number,
  fileName?: string
): Promise<void> => {
  await request.download(`${BASE_PATH}/${attachmentId}/download`, undefined, fileName)
}

export default {
  uploadAttachment,
  getAttachment,
  deleteAttachment,
  downloadAttachment,
}
