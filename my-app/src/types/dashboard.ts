// src/types/dashboard.ts
/**
 * 首页统计数据类型定义
 */

export interface DashboardStats {
  pending_tasks: number
  weekly_processed: number
  avg_processing_time_minutes: number
  approval_rate: number
}

export interface DailySubmissionCount {
  date: string
  count: number
}

export interface DashboardTrend {
  data: DailySubmissionCount[]
}

export interface StatusDistributionItem {
  name: string
  value: number
}

export interface DashboardDistribution {
  data: StatusDistributionItem[]
}
