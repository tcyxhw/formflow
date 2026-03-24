/**
 * 流程配置相关 API
 */
import request from '@/utils/request'
import type { Response } from '@/types/api'
import type {
  FlowDefinitionDetailResponse,
  FlowDraftResponse,
  FlowDraftSaveRequest,
  FlowPublishRequest,
  FlowSnapshotResponse
} from '@/types/flow'

const FLOW_BASE_PATH = '/api/v1/flows'

/**
 * 获取流程定义详情（含草稿与快照）
 */
export const getFlowDefinitionDetail = (
  flowDefinitionId: number
): Promise<Response<FlowDefinitionDetailResponse>> => {
  return request.get(`${FLOW_BASE_PATH}/${flowDefinitionId}`)
}

/**
 * 获取流程草稿
 */
export const getFlowDraft = (
  flowDefinitionId: number
): Promise<Response<FlowDraftResponse | null>> => {
  return request.get(`${FLOW_BASE_PATH}/${flowDefinitionId}/draft`)
}

/**
 * 保存流程草稿
 */
export const saveFlowDraft = (
  flowDefinitionId: number,
  payload: FlowDraftSaveRequest
): Promise<Response<FlowDraftResponse>> => {
  return request.put(`${FLOW_BASE_PATH}/${flowDefinitionId}/draft`, payload)
}

/**
 * 发布流程
 */
export const publishFlow = (
  flowDefinitionId: number,
  payload: FlowPublishRequest
): Promise<Response<FlowSnapshotResponse>> => {
  return request.post(`${FLOW_BASE_PATH}/${flowDefinitionId}/publish`, payload)
}

/**
 * 获取快照列表
 */
export const listFlowSnapshots = (
  flowDefinitionId: number
): Promise<Response<FlowSnapshotResponse[]>> => {
  return request.get(`${FLOW_BASE_PATH}/${flowDefinitionId}/snapshots`)
}
