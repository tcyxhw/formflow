// src/types/submission.ts
/**
 * 提交（Submission）相关类型定义
 */

import type { AttachmentInfo } from '@/types/attachment'

type SubmissionPrimitive = string | number | boolean | null | undefined
export type SubmissionValue =
  | SubmissionPrimitive
  | SubmissionPrimitive[]
  | Record<string, SubmissionPrimitive | SubmissionPrimitive[]>

// 提交表单的字段数据
export interface SubmissionData {
  name?: string
  email?: string
  amount?: number
  department?: string
  tags?: string[]
  date_range?: {
    start: string
    end: string
  }
  time_range?: {
    start: string
    end: string
  }
  attachments?: number[]
  agree?: boolean
  total_amount?: number
  [key: string]: SubmissionValue
}

// 提交基础信息
export interface SubmissionBase {
  id: number
  form_id: number
  form_version_id: number
  submitter_user_id: number
  status: string
  duration: number
  source: string
  created_at: string
  updated_at: string
}

// 草稿数据结构（前端展示）
export interface SubmissionDraftData extends SubmissionData {}

// 草稿返回数据
export interface SubmissionDraft {
  id: number
  form_id: number
  draft_data: SubmissionDraftData | null
  auto_saved_at: string
  expires_at: string
}

// 创建提交请求
export interface CreateSubmissionRequest {
  form_id: number
  data: SubmissionData
  duration?: number
  source?: string
}

// 更新提交请求
export interface UpdateSubmissionRequest {
  submission_id: number
  data: SubmissionData
}

// 删除响应
export interface MessageResponse {
  message: string
}

// 提交概要信息（列表项）
export interface SubmissionListItem {
  id: number
  form_id: number
  form_name: string
  submitter_name: string
  status: 'submitted' | 'draft' | 'approved' | 'rejected'
  created_at: string
}

// 提交详情
export interface SubmissionDetail extends SubmissionBase {
  ip_address?: string
  created_at: string
  updated_at: string
  form_name: string
  submitter_name: string
  version_num: number
  data_jsonb: SubmissionData
  snapshot_json: SnapshotData
  device_info?: Record<string, SubmissionPrimitive>
  attachments?: AttachmentInfo[]
  process_instance_id?: number | null
  process_state?: string | null
}

// 快照数据结构
export interface SnapshotData {
  form_version_id: number
  version: number
  published_at?: string
  field_labels: Record<string, string>
  field_options: Record<string, Array<{ label: string; value: SubmissionPrimitive }>>
  calculated_formulas?: Record<string, string>
}

// 列表查询参数
export interface SubmissionQueryParams {
  page?: number
  page_size?: number
  form_id?: number
  status?: string
  submitter_user_id?: number
  keyword?: string
  date_from?: string
  date_to?: string
}

// 分页数据
export interface SubmissionListResponse {
  items: SubmissionListItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 统计数据
export interface SubmissionStatistics {
  total: number
  by_status: Record<string, number>
  by_date: Array<{ date: string; count: number }>
  avg_duration: number
}

// 导出任务请求
export interface SubmissionExportRequest {
  form_id: number
  format?: 'excel' | 'csv'
  field_ids?: string[] | null
  submission_ids?: number[] | null
  desensitize?: boolean
}

// 导出同步响应
export interface SubmissionExportSyncResponse {
  download_url: string
  total_rows: number
}

// 导出异步响应
export interface SubmissionExportAsyncResponse {
  task_id: string
  total_rows: number
}

// 导出任务详情
export interface SubmissionExportTask {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  download_url?: string
  created_at: string
  expires_at?: string
  error_message?: string | null
}
