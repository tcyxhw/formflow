/**
 * 活动管理相关 API
 */
import request from '@/utils/request'
import type { Response, PageResponse } from '@/types/api'

export interface Activity {
  id: number
  name: string
  type: string
  status: 'draft' | 'published' | 'ended' | 'cancelled'
  description?: string
  location?: string
  start_date?: string
  end_date?: string
  register_start?: string
  register_end?: string
  quota?: number
  registered_count: number
  form_id?: number
  award_form_id?: number
  organizer_dept_id?: number
  manager_user_id?: number
}

export interface ActivityCreateRequest {
  name: string
  activity_type: string
  form_id?: number
  award_form_id?: number
  start_date?: string
  end_date?: string
  register_start?: string
  register_end?: string
  quota?: number
  location?: string
  organizer_dept_id?: number
  description?: string
}

export interface ActivityRegistration {
  id: number
  activity_id: number
  user_id: number
  status: 'pending' | 'approved' | 'rejected' | 'cancelled'
  registered_at: string
  checked_in_at?: string
  check_in_method?: string
}

export interface AwardRecord {
  id: number
  activity_id: number
  student_user_id: number
  award_level: string
  score_breakdown: Record<string, number>
  comment?: string
  judge_user_id?: number
  judged_at?: string
  status: 'draft' | 'confirmed' | 'finalized'
}

export interface CreditLedger {
  id: number
  student_user_id: number
  term: string
  score_type: string
  delta_value: number
  source_type: string
  source_ref_id?: number
  activity_id?: number
  created_at: string
}

export interface Certificate {
  id: number
  certificate_no: string
  certificate_type: string
  student_user_id: number
  activity_id: number
  verification_code: string
  issued_at: string
  status: 'active' | 'revoked' | 'expired'
}

// 创建活动
export const createActivity = (data: ActivityCreateRequest): Promise<Response<{ id: number; status: string }>> => {
  return request.post('/api/v1/activities', data)
}

// 活动列表
export const listActivities = (params: {
  status?: string
  activity_type?: string
  keyword?: string
  page?: number
  page_size?: number
}): Promise<Response<PageResponse<Activity>>> => {
  return request.get('/api/v1/activities', params)
}

// 活动详情
export const getActivityDetail = (activityId: number): Promise<Response<Activity & { stats: any }>> => {
  return request.get(`/api/v1/activities/${activityId}`)
}

// 发布活动
export const publishActivity = (activityId: number): Promise<Response<any>> => {
  return request.post(`/api/v1/activities/${activityId}/publish`)
}

// 报名活动
export const registerActivity = (activityId: number): Promise<Response<{ registration_id: number; status: string }>> => {
  return request.post(`/api/v1/activities/${activityId}/register`)
}

// 取消报名
export const cancelRegistration = (activityId: number): Promise<Response<any>> => {
  return request.post(`/api/v1/activities/${activityId}/cancel-registration`)
}

// 活动签到
export const checkin = (code: string): Promise<Response<{ registration_id: number; checked_in_at: string }>> => {
  return request.post('/api/v1/activities/checkin', { code })
}

// 提交评分
export const submitAward = (
  activityId: number,
  data: {
    student_user_id: number
    award_level: string
    score_breakdown?: Record<string, number>
    comment?: string
  }
): Promise<Response<{ award_record_id: number }>> => {
  return request.post(`/api/v1/activities/${activityId}/awards`, data)
}

// 获取评奖统计
export const getAwardStats = (activityId: number): Promise<Response<any>> => {
  return request.get(`/api/v1/activities/${activityId}/award-stats`)
}

// Finalize获奖名单
export const finalizeAwards = (activityId: number): Promise<Response<{ finalized_count: number }>> => {
  return request.post(`/api/v1/activities/${activityId}/finalize`)
}

// 发放学分
export const issueCredits = (
  activityId: number,
  studentUserId?: number
): Promise<Response<{ issued_count: number; entries: any[] }>> => {
  return request.post(`/api/v1/activities/${activityId}/issue-credits`, { student_user_id: studentUserId })
}

// 批量生成证书
export const generateCertificates = (
  activityId: number,
  templateId: number
): Promise<Response<{ generated_count: number; certificates: any[] }>> => {
  return request.post(`/api/v1/activities/${activityId}/generate-certificates`, { template_id: templateId })
}

// 学生学分汇总
export const getStudentCreditSummary = (studentId: number, term?: string): Promise<Response<any>> => {
  return request.get(`/api/v1/credits/summary/${studentId}`, { term })
}

// 学分明细
export const getCreditLedger = (studentId: number, params: { term?: string; page?: number; page_size?: number }): Promise<Response<PageResponse<CreditLedger>>> => {
  return request.get(`/api/v1/credits/ledger/${studentId}`, params)
}

// 证书列表
export const getStudentCertificates = (studentId: number): Promise<Response<Certificate[]>> => {
  return request.get(`/api/v1/certificates/student/${studentId}`)
}

// 验证证书
export const verifyCertificate = (code: string): Promise<Response<any>> => {
  return request.get(`/api/v1/certificates/verify/${code}`)
}

// 生成签到码
export interface CheckinCode {
  id: number
  activity_id: number
  code: string
  type: 'qrcode' | 'number'
  status: 'active' | 'expired'
  valid_from: string
  valid_to: string
  used_count: number
  max_use?: number
}

export const generateCheckinCode = (
  activityId: number,
  type: 'qrcode' | 'number',
  validHours: number
): Promise<Response<CheckinCode>> => {
  return request.post(`/api/v1/activities/${activityId}/generate-checkin-code`, {
    type,
    valid_hours: validHours,
  })
}
