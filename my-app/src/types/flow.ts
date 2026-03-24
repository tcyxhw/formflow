/**
 * 流程配置相关类型
 */

// ==================== 枚举定义 ====================

export type WorkflowStatus = 'draft' | 'published' | 'disabled'
export type InstanceStatus = 'running' | 'approved' | 'rejected' | 'canceled'
export type OperationType = 'submit' | 'approve' | 'reject' | 'cancel' | 'cc'

export type FlowNodeType = 'start' | 'user' | 'auto' | 'condition' | 'cc' | 'end'
export type FlowAssigneeType = 'user' | 'group' | 'role' | 'department' | 'position' | 'expr' | 'form_field' | 'department_post'
export type FlowApprovePolicy = 'any' | 'all' | 'percent'
export type FlowRouteMode = 'exclusive' | 'parallel'
export type RejectStrategy = 'TO_START' | 'TO_PREVIOUS'
export type JsonLogicExpression = Record<string, unknown>

// 条件表达式类型（来自 condition.ts）
export type Condition = JsonLogicExpression

/**
 * 条件分支 - 表示单个条件分支
 */
export interface ConditionBranch {
  /** 优先级（数字越小优先级越高） */
  priority: number
  /** 分支标签 */
  label: string
  /** 条件表达式 */
  condition: Condition
  /** 目标节点 ID */
  target_node_id: number
}

/**
 * 条件分支配置 - 表示条件节点的完整配置
 */
export interface ConditionBranchesConfig {
  /** 条件分支列表 */
  branches: ConditionBranch[]
  /** 默认目标节点 ID（当所有条件都不匹配时使用） */
  default_target_node_id: number
}

export interface FlowNodeConfig {
  /** 节点数据库 ID（草稿节点可能为空） */
  id?: number
  /** 前端临时 ID，确保可在保存前引用 */
  temp_id?: string
  /** 节点名称 */
  name: string
  /** 节点类型 */
  type: FlowNodeType
  /** 指派类型 */
  assignee_type?: FlowAssigneeType
  /** 指派参数 */
  assignee_value?: Record<string, unknown> | null
  /** 会签策略 */
  approve_policy: FlowApprovePolicy
  /** 百分比策略阈值 */
  approve_threshold?: number | null
  /** 路由模式 */
  route_mode: FlowRouteMode
  /** SLA 时长（小时） */
  sla_hours?: number | null
  /** 是否允许代理 */
  allow_delegate: boolean
  /** 自动审批开关 */
  auto_approve_enabled: boolean
  /** 自动通过条件 */
  auto_approve_cond?: JsonLogicExpression | null
  /** 自动驳回条件 */
  auto_reject_cond?: JsonLogicExpression | null
  /** 抽检比例 */
  auto_sample_ratio: number
  /** 驳回策略 */
  reject_strategy: RejectStrategy
  /** 条件分支配置（CONDITION 节点使用） */
  condition_branches?: ConditionBranchesConfig | null
  /** 扩展元数据 */
  metadata: Record<string, unknown>
}

export interface FlowRouteConfig {
  /** 路由 ID（草稿阶段可能不存在） */
  id?: number
  /** 前端临时 ID */
  temp_id?: string
  /** 来源节点 key（ID 或 temp_id） */
  from_node_key: string
  /** 目标节点 key（ID 或 temp_id） */
  to_node_key: string
  /** 优先级 */
  priority: number
  /** 条件表达式（JsonLogic） */
  condition?: JsonLogicExpression | null
  /** 是否默认路由 */
  is_default: boolean
}

export interface FlowDraftPayload {
  /** 草稿版本号（乐观锁） */
  version: number
  /** 节点配置 */
  nodes: FlowNodeConfig[]
  /** 路由配置 */
  routes: FlowRouteConfig[]
  /** 画布节点坐标等扩展信息 */
  nodes_graph: Record<string, FlowNodePosition>
}

export interface FlowNodePosition {
  /** X 轴位置（px） */
  x: number
  /** Y 轴位置（px） */
  y: number
}

export interface FlowDraftResponse extends FlowDraftPayload {
  /** 流程定义 ID */
  flow_definition_id: number
  /** 最后编辑人 */
  updated_by?: number | null
  /** 最后更新时间 */
  updated_at?: string | null
  /** 最近同步快照 ID */
  last_snapshot_id?: number | null
}

export interface FlowDraftSaveRequest extends FlowDraftPayload {
  /** 流程定义 ID */
  flow_definition_id: number
}

export interface FlowPublishRequest {
  /** 流程定义 ID */
  flow_definition_id: number
  /** 草稿版本号 */
  version: number
  /** 发布版本标签 */
  version_tag?: string
  /** 变更说明 */
  changelog?: string
}

export interface FlowSnapshotResponse {
  /** 快照 ID */
  id: number
  /** 流程定义 ID */
  flow_definition_id: number
  /** 版本标签 */
  version_tag: string
  /** 规则载荷 */
  rules_payload: Record<string, unknown>
  /** 元信息 */
  metadata_json?: Record<string, unknown> | null
  /** 创建时间 */
  created_at: string
  /** 创建人 */
  created_by?: number | null
}

export interface FlowDefinitionResponse {
  /** 流程定义 ID */
  id: number
  /** 对应表单 ID */
  form_id: number
  /** 流程名称 */
  name: string
  /** 流程版本号 */
  version: number
  /** 当前快照 ID */
  active_snapshot_id?: number | null
  /** 当前快照标签 */
  active_snapshot_tag?: string | null
  /** 创建时间 */
  created_at: string
  /** 更新时间 */
  updated_at: string
}

export interface FlowDefinitionDetailResponse {
  /** 流程定义概要 */
  definition: FlowDefinitionResponse
  /** 草稿数据 */
  draft?: FlowDraftResponse | null
  /** 当前生效快照 */
  active_snapshot?: FlowSnapshotResponse | null
  /** 历史快照 */
  snapshots: FlowSnapshotResponse[]
}
