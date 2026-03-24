/**
 * 节点模板相关类型定义
 */

import type { FlowNodeConfig, FlowNodeType, FlowAssigneeType, FlowApprovePolicy, RejectStrategy } from './flow'

/**
 * 节点模板 - 预定义的节点配置模板
 */
export interface NodeTemplate {
  /** 模板 ID */
  id: string
  /** 模板名称 */
  name: string
  /** 模板描述 */
  description: string
  /** 节点类型 */
  type: FlowNodeType
  /** 模板分类 */
  category: 'approval' | 'condition' | 'auto' | 'other'
  /** 模板配置（部分节点配置） */
  config: Partial<FlowNodeConfig>
  /** 图标 */
  icon?: string
  /** 是否为系统内置模板 */
  isBuiltin: boolean
  /** 使用次数 */
  usageCount?: number
  /** 创建时间 */
  createdAt?: string
  /** 最后使用时间 */
  lastUsedAt?: string
}

/**
 * 节点模板分类
 */
export type NodeTemplateCategory = 'approval' | 'condition' | 'auto' | 'other'

/**
 * 节点模板库响应
 */
export interface NodeTemplateLibraryResponse {
  /** 模板列表 */
  templates: NodeTemplate[]
  /** 总数 */
  total: number
}

/**
 * 创建节点模板请求
 */
export interface CreateNodeTemplateRequest {
  /** 模板名称 */
  name: string
  /** 模板描述 */
  description: string
  /** 模板分类 */
  category: NodeTemplateCategory
  /** 模板配置 */
  config: Partial<FlowNodeConfig>
}

/**
 * 更新节点模板请求
 */
export interface UpdateNodeTemplateRequest {
  /** 模板名称 */
  name?: string
  /** 模板描述 */
  description?: string
  /** 模板分类 */
  category?: NodeTemplateCategory
  /** 模板配置 */
  config?: Partial<FlowNodeConfig>
}
