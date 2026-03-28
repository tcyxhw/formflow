// src/api/dashboard.ts
/**
 * 首页统计相关 API
 */
import request from '@/utils/request'
import type { Response } from '@/types/api'
import type { DashboardStats, DashboardTrend, DashboardDistribution } from '@/types/dashboard'

const BASE_PATH = '/api/v1/dashboard'

/**
 * 获取首页统计数据
 * GET /dashboard/stats
 */
export const getDashboardStats = (): Promise<Response<DashboardStats>> => {
  return request.get(`${BASE_PATH}/stats`)
}

/**
 * 获取提交量趋势
 * GET /dashboard/trend
 */
export const getDashboardTrend = (): Promise<Response<DashboardTrend>> => {
  return request.get(`${BASE_PATH}/trend`)
}

/**
 * 获取审批状态分布
 * GET /dashboard/distribution
 */
export const getDashboardDistribution = (): Promise<Response<DashboardDistribution>> => {
  return request.get(`${BASE_PATH}/distribution`)
}

export default {
  getDashboardStats,
  getDashboardTrend,
  getDashboardDistribution,
}
