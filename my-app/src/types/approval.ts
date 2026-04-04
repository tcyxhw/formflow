/**
 * 审批任务相关类型定义
 */
export type SlaLevel = 'unknown' | 'normal' | 'warning' | 'critical' | 'expired'

export interface TaskAssigneeInfo {
  /** 指派用户 ID */
  user_id: number | null
  /** 指派小组 ID */
  group_id: number | null
  /** 小组名称 */
  group_name: string | null
}

export type TaskStatus = 'open' | 'claimed' | 'completed' | 'canceled'

export interface TaskResponse {
  id: number
  process_instance_id: number
  process_state: string
  node_id: number
  node_name?: string | null
  flow_name?: string | null
  status: TaskStatus
  action?: string | null
  payload?: Record<string, unknown> | null
  assignee: TaskAssigneeInfo
  claimed_by?: number | null
  claimed_at?: string | null
  due_at?: string | null
  created_at: string
  updated_at: string
  sla_hours?: number | null
  is_overdue: boolean
  remaining_sla_minutes?: number | null
  sla_level?: SlaLevel | null
  submitter_user_id?: number | null
  submitter_name?: string | null
  form_data_snapshot?: Record<string, unknown> | null
  form_id?: number | null
}

export interface TaskListResponse {
  items: TaskResponse[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface TaskSlaSummary {
  total: number
  unknown: number
  normal: number
  warning: number
  critical: number
  expired: number
}

export interface TaskListQuery {
  page?: number
  page_size?: number
  status?: TaskStatus | null
  only_mine?: boolean
  keyword?: string | null
  sla_level?: SlaLevel | null
}

export interface TaskActionRequest {
  action: string
  comment?: string
  extra_data?: Record<string, unknown>
}

export interface TaskTransferRequest {
  target_user_id: number
  message?: string
}

export interface TaskDelegateRequest {
  delegate_user_id: number
  expire_hours?: number
  message?: string
}

export interface TaskAddSignRequest {
  user_ids: number[]
  message?: string
}

export interface TimelineEntry {
  task_id?: number | null
  node_id?: number | null
  node_name?: string | null
  assignee_name?: string | null
  status?: TaskStatus | null
  action?: string | null
  actor_user_id?: number | null
  actor_name?: string | null
  started_at?: string | null
  completed_at?: string | null
  due_at?: string | null
  remaining_sla_minutes?: number | null
  sla_level?: string | null
  comment?: string | null
  actions: TimelineAction[]
}

export interface TimelineAction {
  action: string
  actor_user_id?: number | null
  actor_name?: string | null
  comment?: string | null
  created_at?: string | null
  detail?: Record<string, unknown> | null
}

export interface ProcessTimelineResponse {
  process_instance_id: number
  state: string
  entries: TimelineEntry[]
}
