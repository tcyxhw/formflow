/**
 * 节点搜索工具 - 处理节点的搜索和过滤
 */

import type { FlowNodeConfig } from '@/types/flow'

/**
 * 搜索结果
 */
export interface SearchResult {
  /** 匹配的节点 */
  node: FlowNodeConfig
  /** 匹配的字段 */
  matchedFields: string[]
  /** 匹配的值 */
  matchedValues: string[]
  /** 相关性分数（0-1） */
  relevanceScore: number
}

/**
 * 搜索选项
 */
export interface SearchOptions {
  /** 是否区分大小写 */
  caseSensitive?: boolean
  /** 搜索字段 */
  fields?: (keyof FlowNodeConfig)[]
  /** 是否使用模糊匹配 */
  fuzzy?: boolean
  /** 最小相关性分数 */
  minRelevance?: number
}

/**
 * 默认搜索字段
 */
const DEFAULT_SEARCH_FIELDS: (keyof FlowNodeConfig)[] = [
  'name',
  'type',
  'assignee_type',
  'approve_policy',
  'reject_strategy'
]

/**
 * 搜索节点
 */
export function searchNodes(
  nodes: FlowNodeConfig[],
  query: string,
  options: SearchOptions = {}
): SearchResult[] {
  if (!query || query.trim().length === 0) {
    return []
  }

  const {
    caseSensitive = false,
    fields = DEFAULT_SEARCH_FIELDS,
    fuzzy = false,
    minRelevance = 0
  } = options

  const normalizedQuery = caseSensitive ? query : query.toLowerCase()
  const results: SearchResult[] = []

  nodes.forEach(node => {
    const matchedFields: string[] = []
    const matchedValues: string[] = []
    let totalScore = 0

    fields.forEach(field => {
      const value = node[field]
      if (value === null || value === undefined) {
        return
      }

      const stringValue = String(value)
      const normalizedValue = caseSensitive ? stringValue : stringValue.toLowerCase()

      let score = 0

      if (fuzzy) {
        score = calculateFuzzyScore(normalizedQuery, normalizedValue)
      } else {
        score = calculateExactScore(normalizedQuery, normalizedValue)
      }

      if (score > 0) {
        matchedFields.push(field)
        matchedValues.push(stringValue)
        totalScore += score
      }
    })

    if (matchedFields.length > 0) {
      const relevanceScore = totalScore / matchedFields.length

      if (relevanceScore >= minRelevance) {
        results.push({
          node,
          matchedFields,
          matchedValues,
          relevanceScore
        })
      }
    }
  })

  // 按相关性分数排序
  results.sort((a, b) => b.relevanceScore - a.relevanceScore)

  return results
}

/**
 * 计算精确匹配分数
 */
function calculateExactScore(query: string, value: string): number {
  if (value === query) {
    return 1 // 完全匹配
  }

  if (value.includes(query)) {
    return 0.8 // 包含匹配
  }

  if (value.startsWith(query)) {
    return 0.9 // 前缀匹配
  }

  return 0
}

/**
 * 计算模糊匹配分数
 */
function calculateFuzzyScore(query: string, value: string): number {
  if (value === query) {
    return 1
  }

  let score = 0
  let queryIndex = 0
  let valueIndex = 0
  let consecutiveMatches = 0

  while (queryIndex < query.length && valueIndex < value.length) {
    if (query[queryIndex] === value[valueIndex]) {
      queryIndex++
      consecutiveMatches++
      score += 0.1 * consecutiveMatches
    } else {
      consecutiveMatches = 0
    }
    valueIndex++
  }

  // 如果没有匹配所有查询字符，返回 0
  if (queryIndex < query.length) {
    return 0
  }

  // 归一化分数
  return Math.min(score / query.length, 1)
}

/**
 * 按节点类型过滤
 */
export function filterNodesByType(
  nodes: FlowNodeConfig[],
  types: string[]
): FlowNodeConfig[] {
  if (types.length === 0) {
    return nodes
  }

  const typeSet = new Set(types)
  return nodes.filter(node => typeSet.has(node.type))
}

/**
 * 按审批策略过滤
 */
export function filterNodesByApprovePolicy(
  nodes: FlowNodeConfig[],
  policies: string[]
): FlowNodeConfig[] {
  if (policies.length === 0) {
    return nodes
  }

  const policySet = new Set(policies)
  return nodes.filter(node => policySet.has(node.approve_policy))
}

/**
 * 按指派类型过滤
 */
export function filterNodesByAssigneeType(
  nodes: FlowNodeConfig[],
  types: string[]
): FlowNodeConfig[] {
  if (types.length === 0) {
    return nodes
  }

  const typeSet = new Set(types)
  return nodes.filter(node => node.assignee_type && typeSet.has(node.assignee_type))
}

/**
 * 按 SLA 时长过滤
 */
export function filterNodesBySlaHours(
  nodes: FlowNodeConfig[],
  minHours?: number,
  maxHours?: number
): FlowNodeConfig[] {
  return nodes.filter(node => {
    if (node.sla_hours === null || node.sla_hours === undefined) {
      return minHours === undefined && maxHours === undefined
    }

    if (minHours !== undefined && node.sla_hours < minHours) {
      return false
    }

    if (maxHours !== undefined && node.sla_hours > maxHours) {
      return false
    }

    return true
  })
}

/**
 * 按自动审批状态过滤
 */
export function filterNodesByAutoApprove(
  nodes: FlowNodeConfig[],
  enabled: boolean
): FlowNodeConfig[] {
  return nodes.filter(node => node.auto_approve_enabled === enabled)
}

/**
 * 按代理状态过滤
 */
export function filterNodesByDelegate(
  nodes: FlowNodeConfig[],
  enabled: boolean
): FlowNodeConfig[] {
  return nodes.filter(node => node.allow_delegate === enabled)
}

/**
 * 组合搜索和过滤
 */
export function searchAndFilter(
  nodes: FlowNodeConfig[],
  query: string,
  filters: {
    types?: string[]
    policies?: string[]
    assigneeTypes?: string[]
    minSlaHours?: number
    maxSlaHours?: number
    autoApproveEnabled?: boolean
    delegateEnabled?: boolean
  } = {},
  searchOptions: SearchOptions = {}
): SearchResult[] {
  let filtered = nodes

  // 应用过滤器
  if (filters.types && filters.types.length > 0) {
    filtered = filterNodesByType(filtered, filters.types)
  }

  if (filters.policies && filters.policies.length > 0) {
    filtered = filterNodesByApprovePolicy(filtered, filters.policies)
  }

  if (filters.assigneeTypes && filters.assigneeTypes.length > 0) {
    filtered = filterNodesByAssigneeType(filtered, filters.assigneeTypes)
  }

  if (filters.minSlaHours !== undefined || filters.maxSlaHours !== undefined) {
    filtered = filterNodesBySlaHours(filtered, filters.minSlaHours, filters.maxSlaHours)
  }

  if (filters.autoApproveEnabled !== undefined) {
    filtered = filterNodesByAutoApprove(filtered, filters.autoApproveEnabled)
  }

  if (filters.delegateEnabled !== undefined) {
    filtered = filterNodesByDelegate(filtered, filters.delegateEnabled)
  }

  // 执行搜索
  return searchNodes(filtered, query, searchOptions)
}

/**
 * 获取搜索建议
 */
export function getSearchSuggestions(
  nodes: FlowNodeConfig[],
  query: string,
  limit: number = 5
): string[] {
  if (!query || query.trim().length === 0) {
    return []
  }

  const suggestions = new Set<string>()
  const normalizedQuery = query.toLowerCase()

  nodes.forEach(node => {
    // 从节点名称获取建议
    if (node.name.toLowerCase().includes(normalizedQuery)) {
      suggestions.add(node.name)
    }

    // 从节点类型获取建议
    if (node.type.toLowerCase().includes(normalizedQuery)) {
      suggestions.add(node.type)
    }

    // 从审批策略获取建议
    if (node.approve_policy.toLowerCase().includes(normalizedQuery)) {
      suggestions.add(node.approve_policy)
    }

    // 从指派类型获取建议
    if (node.assignee_type && node.assignee_type.toLowerCase().includes(normalizedQuery)) {
      suggestions.add(node.assignee_type)
    }
  })

  return Array.from(suggestions).slice(0, limit)
}

/**
 * 高亮搜索结果
 */
export function highlightSearchResult(
  text: string,
  query: string,
  caseSensitive: boolean = false
): string {
  if (!query || query.trim().length === 0) {
    return text
  }

  const flags = caseSensitive ? 'g' : 'gi'
  const regex = new RegExp(`(${escapeRegex(query)})`, flags)

  return text.replace(regex, '<mark>$1</mark>')
}

/**
 * 转义正则表达式特殊字符
 */
function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * 获取搜索统计信息
 */
export function getSearchStatistics(
  nodes: FlowNodeConfig[],
  results: SearchResult[]
): {
  totalNodes: number
  matchedNodes: number
  matchRate: number
  averageRelevance: number
  topMatches: SearchResult[]
} {
  const matchedNodeIds = new Set(results.map(r => r.node.id || r.node.temp_id))
  const averageRelevance = results.length > 0
    ? results.reduce((sum, r) => sum + r.relevanceScore, 0) / results.length
    : 0

  return {
    totalNodes: nodes.length,
    matchedNodes: matchedNodeIds.size,
    matchRate: nodes.length > 0 ? matchedNodeIds.size / nodes.length : 0,
    averageRelevance,
    topMatches: results.slice(0, 3)
  }
}

/**
 * 保存搜索历史
 */
const searchHistory: string[] = []
const MAX_HISTORY_SIZE = 10

export function addToSearchHistory(query: string): void {
  if (!query || query.trim().length === 0) {
    return
  }

  // 移除重复项
  const index = searchHistory.indexOf(query)
  if (index > -1) {
    searchHistory.splice(index, 1)
  }

  // 添加到开头
  searchHistory.unshift(query)

  // 保持历史记录大小
  if (searchHistory.length > MAX_HISTORY_SIZE) {
    searchHistory.pop()
  }
}

export function getSearchHistory(): string[] {
  return [...searchHistory]
}

export function clearSearchHistory(): void {
  searchHistory.length = 0
}

/**
 * 搜索历史中的建议
 */
export function getHistorySuggestions(query: string, limit: number = 5): string[] {
  if (!query || query.trim().length === 0) {
    return getSearchHistory().slice(0, limit)
  }

  const normalizedQuery = query.toLowerCase()
  return searchHistory
    .filter(item => item.toLowerCase().includes(normalizedQuery))
    .slice(0, limit)
}
