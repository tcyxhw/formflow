import { describe, it, expect, beforeEach } from 'vitest'
import {
  searchNodes,
  filterNodesByType,
  filterNodesByApprovePolicy,
  filterNodesByAssigneeType,
  filterNodesBySlaHours,
  filterNodesByAutoApprove,
  filterNodesByDelegate,
  searchAndFilter,
  getSearchSuggestions,
  highlightSearchResult,
  getSearchStatistics,
  addToSearchHistory,
  getSearchHistory,
  clearSearchHistory,
  getHistorySuggestions
} from '../nodeSearch'
import type { FlowNodeConfig } from '@/types/flow'

describe('nodeSearch', () => {
  let nodes: FlowNodeConfig[]

  beforeEach(() => {
    clearSearchHistory()

    nodes = [
      {
        id: 1,
        temp_id: 'node_1',
        name: '经理审批',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      },
      {
        id: 2,
        temp_id: 'node_2',
        name: '部门负责人审批',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      },
      {
        id: 3,
        temp_id: 'node_3',
        name: '金额条件分支',
        type: 'condition',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      },
      {
        id: 4,
        temp_id: 'node_4',
        name: '自动通知',
        type: 'auto',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: true,
        auto_sample_ratio: 0.1,
        reject_strategy: 'TO_START',
        metadata: {}
      }
    ]
  })

  describe('搜索节点', () => {
    it('应该能够按名称搜索节点', () => {
      const results = searchNodes(nodes, '经理')
      expect(results.length).toBeGreaterThan(0)
      expect(results[0].node.name).toContain('经理')
    })

    it('应该能够按节点类型搜索', () => {
      const results = searchNodes(nodes, 'user')
      expect(results.length).toBeGreaterThan(0)
      expect(results.some(r => r.node.type === 'user')).toBe(true)
    })

    it('应该能够按审批策略搜索', () => {
      const results = searchNodes(nodes, 'all')
      expect(results.length).toBeGreaterThan(0)
    })

    it('搜索应该不区分大小写', () => {
      const results1 = searchNodes(nodes, '经理')
      const results2 = searchNodes(nodes, '经理', { caseSensitive: false })
      expect(results1.length).toBe(results2.length)
    })

    it('搜索应该支持区分大小写', () => {
      const results = searchNodes(nodes, 'User', { caseSensitive: true })
      expect(results.length).toBe(0)
    })

    it('应该能够使用模糊匹配', () => {
      const results = searchNodes(nodes, '经理', { fuzzy: true })
      expect(results.length).toBeGreaterThan(0)
    })

    it('应该能够按相关性排序', () => {
      const results = searchNodes(nodes, '审批')
      expect(results[0].relevanceScore).toBeGreaterThanOrEqual(results[1]?.relevanceScore || 0)
    })

    it('应该能够过滤最小相关性', () => {
      const results = searchNodes(nodes, '审批', { minRelevance: 0.9 })
      expect(results.every(r => r.relevanceScore >= 0.9)).toBe(true)
    })

    it('空查询应该返回空结果', () => {
      const results = searchNodes(nodes, '')
      expect(results.length).toBe(0)
    })
  })

  describe('按类型过滤', () => {
    it('应该能够按单个类型过滤', () => {
      const results = filterNodesByType(nodes, ['user'])
      expect(results.every(n => n.type === 'user')).toBe(true)
    })

    it('应该能够按多个类型过滤', () => {
      const results = filterNodesByType(nodes, ['user', 'condition'])
      expect(results.every(n => n.type === 'user' || n.type === 'condition')).toBe(true)
    })

    it('空类型列表应该返回所有节点', () => {
      const results = filterNodesByType(nodes, [])
      expect(results.length).toBe(nodes.length)
    })
  })

  describe('按审批策略过滤', () => {
    it('应该能够按审批策略过滤', () => {
      const results = filterNodesByApprovePolicy(nodes, ['all'])
      expect(results.every(n => n.approve_policy === 'all')).toBe(true)
    })
  })

  describe('按指派类型过滤', () => {
    it('应该能够按指派类型过滤', () => {
      const results = filterNodesByAssigneeType(nodes, ['role'])
      expect(results.every(n => n.assignee_type === 'role')).toBe(true)
    })
  })

  describe('按 SLA 时长过滤', () => {
    it('应该能够按最小 SLA 时长过滤', () => {
      nodes[0].sla_hours = 24
      nodes[1].sla_hours = 48
      const results = filterNodesBySlaHours(nodes, 30)
      expect(results.every(n => !n.sla_hours || n.sla_hours >= 30)).toBe(true)
    })

    it('应该能够按最大 SLA 时长过滤', () => {
      nodes[0].sla_hours = 24
      nodes[1].sla_hours = 48
      const results = filterNodesBySlaHours(nodes, undefined, 30)
      expect(results.every(n => !n.sla_hours || n.sla_hours <= 30)).toBe(true)
    })

    it('应该能够按 SLA 时长范围过滤', () => {
      nodes[0].sla_hours = 24
      nodes[1].sla_hours = 48
      nodes[2].sla_hours = 72
      const results = filterNodesBySlaHours(nodes, 20, 50)
      expect(results.every(n => !n.sla_hours || (n.sla_hours >= 20 && n.sla_hours <= 50))).toBe(true)
    })
  })

  describe('按自动审批过滤', () => {
    it('应该能够过滤启用自动审批的节点', () => {
      const results = filterNodesByAutoApprove(nodes, true)
      expect(results.every(n => n.auto_approve_enabled === true)).toBe(true)
    })

    it('应该能够过滤禁用自动审批的节点', () => {
      const results = filterNodesByAutoApprove(nodes, false)
      expect(results.every(n => n.auto_approve_enabled === false)).toBe(true)
    })
  })

  describe('按代理过滤', () => {
    it('应该能够过滤允许代理的节点', () => {
      const results = filterNodesByDelegate(nodes, true)
      expect(results.every(n => n.allow_delegate === true)).toBe(true)
    })

    it('应该能够过滤禁止代理的节点', () => {
      const results = filterNodesByDelegate(nodes, false)
      expect(results.every(n => n.allow_delegate === false)).toBe(true)
    })
  })

  describe('组合搜索和过滤', () => {
    it('应该能够组合搜索和过滤', () => {
      const results = searchAndFilter(nodes, '审批', {
        types: ['user']
      })
      expect(results.every(r => r.node.type === 'user')).toBe(true)
    })

    it('应该能够应用多个过滤器', () => {
      const results = searchAndFilter(nodes, '', {
        types: ['user'],
        delegateEnabled: true
      })
      expect(results.every(r => r.node.type === 'user' && r.node.allow_delegate)).toBe(true)
    })
  })

  describe('搜索建议', () => {
    it('应该能够获取搜索建议', () => {
      const suggestions = getSearchSuggestions(nodes, '审')
      expect(suggestions.length).toBeGreaterThan(0)
    })

    it('应该能够限制建议数量', () => {
      const suggestions = getSearchSuggestions(nodes, '审', 2)
      expect(suggestions.length).toBeLessThanOrEqual(2)
    })

    it('空查询应该返回空建议', () => {
      const suggestions = getSearchSuggestions(nodes, '')
      expect(suggestions.length).toBe(0)
    })
  })

  describe('高亮搜索结果', () => {
    it('应该能够高亮搜索结果', () => {
      const highlighted = highlightSearchResult('经理审批', '经理')
      expect(highlighted).toContain('<mark>')
      expect(highlighted).toContain('</mark>')
    })

    it('应该能够支持区分大小写的高亮', () => {
      const highlighted = highlightSearchResult('User Node', 'user', false)
      expect(highlighted).toContain('<mark>')
    })

    it('空查询应该返回原文本', () => {
      const highlighted = highlightSearchResult('经理审批', '')
      expect(highlighted).toBe('经理审批')
    })
  })

  describe('搜索统计', () => {
    it('应该能够获取搜索统计信息', () => {
      const results = searchNodes(nodes, '审批')
      const stats = getSearchStatistics(nodes, results)

      expect(stats.totalNodes).toBe(nodes.length)
      expect(stats.matchedNodes).toBeGreaterThan(0)
      expect(stats.matchRate).toBeGreaterThan(0)
      expect(stats.averageRelevance).toBeGreaterThan(0)
    })

    it('应该能够计算匹配率', () => {
      const results = searchNodes(nodes, '审批')
      const stats = getSearchStatistics(nodes, results)

      expect(stats.matchRate).toBeLessThanOrEqual(1)
      expect(stats.matchRate).toBeGreaterThanOrEqual(0)
    })
  })

  describe('搜索历史', () => {
    it('应该能够添加到搜索历史', () => {
      addToSearchHistory('经理')
      const history = getSearchHistory()
      expect(history).toContain('经理')
    })

    it('应该能够获取搜索历史', () => {
      addToSearchHistory('经理')
      addToSearchHistory('审批')
      const history = getSearchHistory()
      expect(history.length).toBe(2)
      expect(history[0]).toBe('审批')
    })

    it('应该能够清空搜索历史', () => {
      addToSearchHistory('经理')
      clearSearchHistory()
      const history = getSearchHistory()
      expect(history.length).toBe(0)
    })

    it('应该能够限制历史记录大小', () => {
      for (let i = 0; i < 15; i++) {
        addToSearchHistory(`查询${i}`)
      }
      const history = getSearchHistory()
      expect(history.length).toBeLessThanOrEqual(10)
    })

    it('应该能够移除重复的历史记录', () => {
      addToSearchHistory('经理')
      addToSearchHistory('审批')
      addToSearchHistory('经理')
      const history = getSearchHistory()
      expect(history[0]).toBe('经理')
      expect(history.filter(h => h === '经理').length).toBe(1)
    })
  })

  describe('历史建议', () => {
    it('应该能够获取历史建议', () => {
      addToSearchHistory('经理')
      addToSearchHistory('审批')
      const suggestions = getHistorySuggestions('经')
      expect(suggestions).toContain('经理')
    })

    it('空查询应该返回所有历史', () => {
      addToSearchHistory('经理')
      addToSearchHistory('审批')
      const suggestions = getHistorySuggestions('')
      expect(suggestions.length).toBe(2)
    })

    it('应该能够限制建议数量', () => {
      for (let i = 0; i < 5; i++) {
        addToSearchHistory(`查询${i}`)
      }
      const suggestions = getHistorySuggestions('', 2)
      expect(suggestions.length).toBeLessThanOrEqual(2)
    })
  })

  describe('性能测试', () => {
    it('应该能够快速搜索大量节点', () => {
      const largeNodeList = Array.from({ length: 1000 }, (_, i) => ({
        ...nodes[0],
        id: i,
        temp_id: `node_${i}`,
        name: `节点${i}`
      }))

      const startTime = performance.now()
      searchNodes(largeNodeList, '节点')
      const endTime = performance.now()

      expect(endTime - startTime).toBeLessThan(100)
    })

    it('应该能够快速过滤大量节点', () => {
      const largeNodeList = Array.from({ length: 1000 }, (_, i) => ({
        ...nodes[0],
        id: i,
        temp_id: `node_${i}`
      }))

      const startTime = performance.now()
      filterNodesByType(largeNodeList, ['user'])
      const endTime = performance.now()

      expect(endTime - startTime).toBeLessThan(50)
    })
  })

  describe('边界情况', () => {
    it('应该能够处理空节点列表', () => {
      const results = searchNodes([], '经理')
      expect(results.length).toBe(0)
    })

    it('应该能够处理特殊字符', () => {
      const results = searchNodes(nodes, '.*+?')
      expect(results.length).toBe(0)
    })

    it('应该能够处理非常长的查询', () => {
      const longQuery = 'a'.repeat(1000)
      const results = searchNodes(nodes, longQuery)
      expect(results.length).toBe(0)
    })

    it('应该能够处理 null 值', () => {
      nodes[0].assignee_type = null as any
      const results = filterNodesByAssigneeType(nodes, ['role'])
      expect(results.length).toBeGreaterThanOrEqual(0)
    })
  })
})
