/**
 * 批量节点编辑工具 - 处理多个节点的批量修改
 */

import type { FlowNodeConfig } from '@/types/flow'

/**
 * 批量编辑配置
 */
export interface BatchEditConfig {
  /** 选中的节点 ID 列表 */
  selectedNodeIds: string[]
  /** 要更新的字段 */
  updates: Partial<FlowNodeConfig>
}

/**
 * 批量编辑结果
 */
export interface BatchEditResult {
  /** 成功编辑的节点数 */
  successCount: number
  /** 失败编辑的节点数 */
  failureCount: number
  /** 编辑后的节点列表 */
  updatedNodes: FlowNodeConfig[]
  /** 失败的节点 ID 列表 */
  failedNodeIds: string[]
}

/**
 * 获取节点的唯一标识
 */
function getNodeKey(node: FlowNodeConfig): string {
  return node.temp_id ?? node.id?.toString() ?? ''
}

/**
 * 批量更新节点
 */
export function batchUpdateNodes(
  nodes: FlowNodeConfig[],
  selectedNodeIds: string[],
  updates: Partial<FlowNodeConfig>
): BatchEditResult {
  const selectedSet = new Set(selectedNodeIds)
  const updatedNodes: FlowNodeConfig[] = []
  const failedNodeIds: string[] = []
  let successCount = 0
  let failureCount = 0

  nodes.forEach(node => {
    const nodeKey = getNodeKey(node)

    if (selectedSet.has(nodeKey)) {
      try {
        // 验证更新的字段
        const validatedUpdates = validateNodeUpdates(node, updates)

        // 应用更新
        const updatedNode = {
          ...node,
          ...validatedUpdates
        }

        updatedNodes.push(updatedNode)
        successCount++
      } catch (error) {
        failedNodeIds.push(nodeKey)
        failureCount++
        updatedNodes.push(node) // 保留原始节点
      }
    } else {
      updatedNodes.push(node)
    }
  })

  return {
    successCount,
    failureCount,
    updatedNodes,
    failedNodeIds
  }
}

/**
 * 验证节点更新
 */
function validateNodeUpdates(
  node: FlowNodeConfig,
  updates: Partial<FlowNodeConfig>
): Partial<FlowNodeConfig> {
  const validated: Partial<FlowNodeConfig> = {}

  // 不允许修改的字段
  const readOnlyFields = ['id', 'temp_id', 'type']

  Object.entries(updates).forEach(([key, value]) => {
    if (readOnlyFields.includes(key)) {
      return // 跳过只读字段
    }

    // 验证特定字段
    switch (key) {
      case 'name':
        if (typeof value === 'string' && value.trim().length > 0) {
          validated[key as keyof FlowNodeConfig] = value
        }
        break

      case 'approve_policy':
        if (['any', 'all', 'percent'].includes(value as string)) {
          validated[key as keyof FlowNodeConfig] = value
        }
        break

      case 'approve_threshold':
        if (typeof value === 'number' && value >= 1 && value <= 100) {
          validated[key as keyof FlowNodeConfig] = value
        }
        break

      case 'route_mode':
        if (['exclusive', 'parallel'].includes(value as string)) {
          validated[key as keyof FlowNodeConfig] = value
        }
        break

      case 'sla_hours':
        if (value === null || (typeof value === 'number' && value > 0)) {
          validated[key as keyof FlowNodeConfig] = value
        }
        break

      case 'allow_delegate':
      case 'auto_approve_enabled':
        if (typeof value === 'boolean') {
          validated[key as keyof FlowNodeConfig] = value
        }
        break

      case 'auto_sample_ratio':
        if (typeof value === 'number' && value >= 0 && value <= 1) {
          validated[key as keyof FlowNodeConfig] = value
        }
        break

      case 'reject_strategy':
        if (['TO_START', 'TO_PREVIOUS'].includes(value as string)) {
          validated[key as keyof FlowNodeConfig] = value
        }
        break

      case 'assignee_type':
        if (['user', 'group', 'role', 'department', 'position', 'expr'].includes(value as string)) {
          validated[key as keyof FlowNodeConfig] = value
        }
        break

      default:
        // 其他字段直接复制
        validated[key as keyof FlowNodeConfig] = value
    }
  })

  return validated
}

/**
 * 批量修改节点名称
 */
export function batchRenameNodes(
  nodes: FlowNodeConfig[],
  selectedNodeIds: string[],
  namePrefix: string
): BatchEditResult {
  const selectedSet = new Set(selectedNodeIds)
  const updatedNodes: FlowNodeConfig[] = []
  let successCount = 0
  let failureCount = 0
  const failedNodeIds: string[] = []

  let counter = 1
  nodes.forEach(node => {
    const nodeKey = getNodeKey(node)

    if (selectedSet.has(nodeKey)) {
      try {
        const newName = `${namePrefix}${counter}`
        const updatedNode = {
          ...node,
          name: newName
        }
        updatedNodes.push(updatedNode)
        successCount++
        counter++
      } catch (error) {
        failedNodeIds.push(nodeKey)
        failureCount++
        updatedNodes.push(node)
      }
    } else {
      updatedNodes.push(node)
    }
  })

  return {
    successCount,
    failureCount,
    updatedNodes,
    failedNodeIds
  }
}

/**
 * 批量修改审批策略
 */
export function batchUpdateApprovePolicy(
  nodes: FlowNodeConfig[],
  selectedNodeIds: string[],
  policy: 'any' | 'all' | 'percent',
  threshold?: number
): BatchEditResult {
  const updates: Partial<FlowNodeConfig> = {
    approve_policy: policy
  }

  if (policy === 'percent' && threshold !== undefined) {
    updates.approve_threshold = threshold
  }

  return batchUpdateNodes(nodes, selectedNodeIds, updates)
}

/**
 * 批量修改驳回策略
 */
export function batchUpdateRejectStrategy(
  nodes: FlowNodeConfig[],
  selectedNodeIds: string[],
  strategy: 'TO_START' | 'TO_PREVIOUS'
): BatchEditResult {
  return batchUpdateNodes(nodes, selectedNodeIds, {
    reject_strategy: strategy
  })
}

/**
 * 批量启用/禁用代理
 */
export function batchToggleDelegate(
  nodes: FlowNodeConfig[],
  selectedNodeIds: string[],
  enabled: boolean
): BatchEditResult {
  return batchUpdateNodes(nodes, selectedNodeIds, {
    allow_delegate: enabled
  })
}

/**
 * 批量启用/禁用自动审批
 */
export function batchToggleAutoApprove(
  nodes: FlowNodeConfig[],
  selectedNodeIds: string[],
  enabled: boolean,
  sampleRatio?: number
): BatchEditResult {
  const updates: Partial<FlowNodeConfig> = {
    auto_approve_enabled: enabled
  }

  if (enabled && sampleRatio !== undefined) {
    updates.auto_sample_ratio = sampleRatio
  }

  return batchUpdateNodes(nodes, selectedNodeIds, updates)
}

/**
 * 批量设置 SLA 时长
 */
export function batchSetSlaHours(
  nodes: FlowNodeConfig[],
  selectedNodeIds: string[],
  hours: number | null
): BatchEditResult {
  return batchUpdateNodes(nodes, selectedNodeIds, {
    sla_hours: hours
  })
}

/**
 * 批量修改路由模式
 */
export function batchUpdateRouteMode(
  nodes: FlowNodeConfig[],
  selectedNodeIds: string[],
  mode: 'exclusive' | 'parallel'
): BatchEditResult {
  return batchUpdateNodes(nodes, selectedNodeIds, {
    route_mode: mode
  })
}

/**
 * 获取选中节点的共同属性
 */
export function getCommonNodeProperties(
  nodes: FlowNodeConfig[],
  selectedNodeIds: string[]
): Partial<FlowNodeConfig> | null {
  if (selectedNodeIds.length === 0) {
    return null
  }

  const selectedSet = new Set(selectedNodeIds)
  const selectedNodes = nodes.filter(n => selectedSet.has(getNodeKey(n)))

  if (selectedNodes.length === 0) {
    return null
  }

  const firstNode = selectedNodes[0]
  const commonProps: Partial<FlowNodeConfig> = {}

  // 检查每个属性是否在所有选中节点中都相同
  const keys = Object.keys(firstNode) as (keyof FlowNodeConfig)[]

  keys.forEach(key => {
    const firstValue = firstNode[key]
    const allSame = selectedNodes.every(node => node[key] === firstValue)

    if (allSame) {
      commonProps[key] = firstValue
    }
  })

  return commonProps
}

/**
 * 检查是否可以批量编辑
 */
export function canBatchEdit(selectedNodeIds: string[]): boolean {
  return selectedNodeIds.length > 0
}

/**
 * 获取批量编辑的影响范围
 */
export function getBatchEditImpact(
  nodes: FlowNodeConfig[],
  selectedNodeIds: string[]
): {
  nodeCount: number
  nodeTypes: Set<string>
  hasApprovalNodes: boolean
  hasConditionNodes: boolean
  hasAutoNodes: boolean
} {
  const selectedSet = new Set(selectedNodeIds)
  const selectedNodes = nodes.filter(n => selectedSet.has(getNodeKey(n)))
  const nodeTypes = new Set(selectedNodes.map(n => n.type))

  return {
    nodeCount: selectedNodes.length,
    nodeTypes,
    hasApprovalNodes: nodeTypes.has('user'),
    hasConditionNodes: nodeTypes.has('condition'),
    hasAutoNodes: nodeTypes.has('auto')
  }
}

/**
 * 验证批量编辑操作
 */
export function validateBatchEditOperation(
  nodes: FlowNodeConfig[],
  selectedNodeIds: string[],
  updates: Partial<FlowNodeConfig>
): {
  valid: boolean
  warnings: string[]
  errors: string[]
} {
  const warnings: string[] = []
  const errors: string[] = []

  if (selectedNodeIds.length === 0) {
    errors.push('没有选中任何节点')
    return { valid: false, warnings, errors }
  }

  const impact = getBatchEditImpact(nodes, selectedNodeIds)

  // 检查是否尝试修改条件节点的审批策略
  if (impact.hasConditionNodes && updates.approve_policy) {
    warnings.push('条件节点不支持审批策略，这些节点将被跳过')
  }

  // 检查是否尝试修改自动节点的审批策略
  if (impact.hasAutoNodes && updates.approve_policy) {
    warnings.push('自动节点不支持审批策略，这些节点将被跳过')
  }

  // 检查百分比阈值
  if (updates.approve_policy === 'percent' && !updates.approve_threshold) {
    errors.push('百分比策略需要指定阈值')
  }

  return {
    valid: errors.length === 0,
    warnings,
    errors
  }
}

/**
 * 生成批量编辑摘要
 */
export function generateBatchEditSummary(
  result: BatchEditResult,
  updates: Partial<FlowNodeConfig>
): string {
  const parts: string[] = []

  parts.push(`成功编辑 ${result.successCount} 个节点`)

  if (result.failureCount > 0) {
    parts.push(`失败 ${result.failureCount} 个节点`)
  }

  const updateFields = Object.keys(updates).filter(k => !['id', 'temp_id', 'type'].includes(k))
  if (updateFields.length > 0) {
    parts.push(`修改字段: ${updateFields.join(', ')}`)
  }

  return parts.join(' | ')
}
