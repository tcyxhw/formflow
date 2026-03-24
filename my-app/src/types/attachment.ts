// src/types/attachment.ts
/**
 * 附件（Attachment）相关类型定义
 */

export interface AttachmentInfo {
  id: number
  file_name: string
  content_type: string
  size: number
  storage_path: string
  download_url: string
  created_at: string
  [key: string]: string | number | boolean | null | undefined
}
