// src/api/approvals.ts
/**
 * 审批任务相关 API
 */
import request from '@/utils/request'
import type { Response } from '@/types/api'
import type {
  TaskListQuery,
  TaskListResponse,
  TaskActionRequest,
  TaskTransferRequest,
  TaskDelegateRequest,
  TaskAddSignRequest,
  ProcessTimelineResponse,
  TaskResponse,
  TaskSlaSummary
} from '@/types/approval'

const APPROVAL_BASE_PATH = '/api/v1/approvals'

/**
 * 查询审批任务
 */
export const listTasks = (params: TaskListQuery): Promise<Response<TaskListResponse>> => {
  return request.get(APPROVAL_BASE_PATH, params)
}

/**
 * 查询当前筛选条件下的 SLA 概览
 */
export const getTaskSlaSummary = (
  params: TaskListQuery
): Promise<Response<TaskSlaSummary>> => {
  return request.get(`${APPROVAL_BASE_PATH}/summary`, params)
}

/**
 * 认领任务
 */
export const claimTask = (taskId: number): Promise<Response<TaskResponse>> => {
  return request.post(`${APPROVAL_BASE_PATH}/${taskId}/claim`)
}

/**
 * 释放任务
 */
export const releaseTask = (taskId: number): Promise<Response<TaskResponse>> => {
  return request.post(`${APPROVAL_BASE_PATH}/${taskId}/release`)
}

/**
 * 执行审批动作
 */
export const performTaskAction = (
  taskId: number,
  payload: TaskActionRequest
): Promise<Response<TaskResponse>> => {
  return request.post(`${APPROVAL_BASE_PATH}/${taskId}/actions`, payload)
}

export const transferTask = (
  taskId: number,
  payload: TaskTransferRequest
): Promise<Response<TaskResponse>> => {
  return request.post(`${APPROVAL_BASE_PATH}/${taskId}/transfer`, payload)
}

export const delegateTask = (
  taskId: number,
  payload: TaskDelegateRequest
): Promise<Response<TaskResponse>> => {
  return request.post(`${APPROVAL_BASE_PATH}/${taskId}/delegate`, payload)
}

export const addSignTask = (
  taskId: number,
  payload: TaskAddSignRequest
): Promise<Response<TaskResponse[]>> => {
  return request.post(`${APPROVAL_BASE_PATH}/${taskId}/add-sign`, payload)
}

export const listGroupTasks = (
  params: Pick<TaskListQuery, 'page' | 'page_size'>
): Promise<Response<TaskListResponse>> => {
  return request.get(`${APPROVAL_BASE_PATH}/group`, params)
}

/**
 * 查询流程轨迹
 */
export const getProcessTimeline = (
  processInstanceId: number
): Promise<Response<ProcessTimelineResponse>> => {
  return request.get(`${APPROVAL_BASE_PATH}/processes/${processInstanceId}/timeline`)
}
