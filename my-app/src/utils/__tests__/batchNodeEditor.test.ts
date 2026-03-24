import { describe, it, expect, beforeEach } from 'vitest'
import {
  batchUpdateNodes,
  batchRenameNodes,
  batchUpdateApprovePolicy,
  batchUpdateRejectStrategy,
  batchToggleDelegate,
  batchToggleAutoApprove,
  batchSetSlaHours,
  batchUpdateRouteMode,
  getCommonNodeProperties,
  canBatchEdit,
  getBatchEditImpact,
  validateBatchEditOperation,
  generateBatchEditSummary
} from '../batchNodeEditor'
import type { FlowNodeConfig } from '@/types/flow'

describe('batchNodeEditor', () => {
  let nodes: FlowNodeConfig[]

  beforeEach(() => {
    nodes = [
      {
        id: 1,
        temp_id: 'node_1',
        name: '节点 1',
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
        name: '节点 2',
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
        name: '条件分支',
        type: 'condition',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }
    ]
  })

  describe('批量更新节点', () => {
    it('应该能够批量更新节点', () => {
      const result = batchUpdateNodes(nodes, ['node_1', 'node_2'], {
        approve_policy: 'any'
      })

      expect(result.successCount).toBe(2)
      expect(result.failureCount).toBe(0)
      expect(result.updatedNodes[0].approve_policy).toBe('any')
      expect(result.updatedNodes[1].approve_policy).toBe('any')
      expect(result.updatedNodes[2].approve_policy).toBe('all')
    })

    it('应该能够批量修改多个字段', () => {
      const result = batchUpdateNodes(nodes, ['node_1'], {
        name: '新名称',
        approve_policy: 'percent',
        approve_threshold: 75
      })

      expect(result.successCount).toBe(1)
      expect(result.updatedNodes[0].name).toBe('新名称')
      expect(result.updatedNodes[0].approve_policy).toBe('percent')
      expect(result.updatedNodes[0].approve_threshold).toBe(75)
    })

    it('应该能够处理无效的字段值', () => {
      const result = batchUpdateNodes(nodes, ['node_1'], {
        approve_policy: 'invalid' as any
      })

      expect(result.successCount).toBe(1)
      expect(result.updatedNodes[0].approve_policy).toBe('all')
    })

    it('应该不允许修改只读字段', () => {
      const result = batchUpdateNodes(nodes, ['node_1'], {
        id: 999,
        temp_id: 'new_id',
        type: 'condition' as any
      })

      expect(result.updatedNodes[0].id).toBe(1)
      expect(result.updatedNodes[0].temp_id).toBe('node_1')
      expect(result.updatedNodes[0].type).toBe('user')
    })

    it('应该能够处理不存在的节点 ID', () => {
      const result = batchUpdateNodes(nodes, ['nonexistent'], {
        approve_policy: 'any'
      })

      expect(result.successCount).toBe(0)
      expect(result.failureCount).toBe(0)
      expect(result.updatedNodes.length).toBe(3)
    })
  })

  describe('批量重命名节点', () => {
    it('应该能够批量重命名节点', () => {
      const result = batchRenameNodes(nodes, ['node_1', 'node_2'], '审批')

      expect(result.successCount).toBe(2)
      expect(result.updatedNodes[0].name).toBe('审批1')
      expect(result.updatedNodes[1].name).toBe('审批2')
      expect(result.updatedNodes[2].name).toBe('条件分支')
    })

    it('应该能够使用不同的前缀', () => {
      const result = batchRenameNodes(nodes, ['node_1'], '步骤')

      expect(result.updatedNodes[0].name).toBe('步骤1')
    })
  })

  describe('批量修改审批策略', () => {
    it('应该能够批量修改为任意一人', () => {
      const result = batchUpdateApprovePolicy(nodes, ['node_1', 'node_2'], 'any')

      expect(result.successCount).toBe(2)
      expect(result.updatedNodes[0].approve_policy).toBe('any')
      expect(result.updatedNodes[1].approve_policy).toBe('any')
    })

    it('应该能够批量修改为全部同意', () => {
      const result = batchUpdateApprovePolicy(nodes, ['node_1'], 'all')

      expect(result.updatedNodes[0].approve_policy).toBe('all')
    })

    it('应该能够批量修改为百分比策略', () => {
      const result = batchUpdateApprovePolicy(nodes, ['node_1', 'node_2'], 'percent', 66)

      expect(result.updatedNodes[0].approve_policy).toBe('percent')
      expect(result.updatedNodes[0].approve_threshold).toBe(66)
      expect(result.updatedNodes[1].approve_policy).toBe('percent')
      expect(result.updatedNodes[1].approve_threshold).toBe(66)
    })
  })

  describe('批量修改驳回策略', () => {
    it('应该能够批量修改为驳回到发起人', () => {
      const result = batchUpdateRejectStrategy(nodes, ['node_1', 'node_2'], 'TO_START')

      expect(result.updatedNodes[0].reject_strategy).toBe('TO_START')
      expect(result.updatedNodes[1].reject_strategy).toBe('TO_START')
    })

    it('应该能够批量修改为驳回到上一个节点', () => {
      const result = batchUpdateRejectStrategy(nodes, ['node_1'], 'TO_PREVIOUS')

      expect(result.updatedNodes[0].reject_strategy).toBe('TO_PREVIOUS')
    })
  })

  describe('批量启用/禁用代理', () => {
    it('应该能够批量启用代理', () => {
      nodes[0].allow_delegate = false
      const result = batchToggleDelegate(nodes, ['node_1'], true)

      expect(result.updatedNodes[0].allow_delegate).toBe(true)
    })

    it('应该能够批量禁用代理', () => {
      const result = batchToggleDelegate(nodes, ['node_1', 'node_2'], false)

      expect(result.updatedNodes[0].allow_delegate).toBe(false)
      expect(result.updatedNodes[1].allow_delegate).toBe(false)
    })
  })

  describe('批量启用/禁用自动审批', () => {
    it('应该能够批量启用自动审批', () => {
      const result = batchToggleAutoApprove(nodes, ['node_1', 'node_2'], true, 0.1)

      expect(result.updatedNodes[0].auto_approve_enabled).toBe(true)
      expect(result.updatedNodes[0].auto_sample_ratio).toBe(0.1)
      expect(result.updatedNodes[1].auto_approve_enabled).toBe(true)
      expect(result.updatedNodes[1].auto_sample_ratio).toBe(0.1)
    })

    it('应该能够批量禁用自动审批', () => {
      nodes[0].auto_approve_enabled = true
      const result = batchToggleAutoApprove(nodes, ['node_1'], false)

      expect(result.updatedNodes[0].auto_approve_enabled).toBe(false)
    })
  })

  describe('批量设置 SLA 时长', () => {
    it('应该能够批量设置 SLA 时长', () => {
      const result = batchSetSlaHours(nodes, ['node_1', 'node_2'], 24)

      expect(result.updatedNodes[0].sla_hours).toBe(24)
      expect(result.updatedNodes[1].sla_hours).toBe(24)
    })

    it('应该能够批量清除 SLA 时长', () => {
      nodes[0].sla_hours = 24
      const result = batchSetSlaHours(nodes, ['node_1'], null)

      expect(result.updatedNodes[0].sla_hours).toBeNull()
    })
  })

  describe('批量修改路由模式', () => {
    it('应该能够批量修改为互斥模式', () => {
      nodes[0].route_mode = 'parallel'
      const result = batchUpdateRouteMode(nodes, ['node_1'], 'exclusive')

      expect(result.updatedNodes[0].route_mode).toBe('exclusive')
    })

    it('应该能够批量修改为并行模式', () => {
      const result = batchUpdateRouteMode(nodes, ['node_1', 'node_2'], 'parallel')

      expect(result.updatedNodes[0].route_mode).toBe('parallel')
      expect(result.updatedNodes[1].route_mode).toBe('parallel')
    })
  })

  describe('获取共同属性', () => {
    it('应该能够获取选中节点的共同属性', () => {
      const common = getCommonNodeProperties(nodes, ['node_1', 'node_2'])

      expect(common?.approve_policy).toBe('all')
      expect(common?.route_mode).toBe('exclusive')
      expect(common?.allow_delegate).toBe(true)
    })

    it('应该能够识别不同的属性', () => {
      const common = getCommonNodeProperties(nodes, ['node_1', 'node_3'])

      expect(common?.name).toBeUndefined()
      expect(common?.type).toBeUndefined()
    })

    it('应该能够处理空选择', () => {
      const common = getCommonNodeProperties(nodes, [])

      expect(common).toBeNull()
    })

    it('应该能够处理单个节点', () => {
      const common = getCommonNodeProperties(nodes, ['node_1'])

      expect(common?.name).toBe('节点 1')
      expect(common?.type).toBe('user')
    })
  })

  describe('批量编辑检查', () => {
    it('应该能够检查是否可以批量编辑', () => {
      expect(canBatchEdit(['node_1'])).toBe(true)
      expect(canBatchEdit(['node_1', 'node_2'])).toBe(true)
      expect(canBatchEdit([])).toBe(false)
    })

    it('应该能够获取批量编辑的影响范围', () => {
      const impact = getBatchEditImpact(nodes, ['node_1', 'node_2', 'node_3'])

      expect(impact.nodeCount).toBe(3)
      expect(impact.nodeTypes.has('user')).toBe(true)
      expect(impact.nodeTypes.has('condition')).toBe(true)
      expect(impact.hasApprovalNodes).toBe(true)
      expect(impact.hasConditionNodes).toBe(true)
    })

    it('应该能够验证批量编辑操作', () => {
      const validation = validateBatchEditOperation(nodes, ['node_1'], {
        approve_policy: 'any'
      })

      expect(validation.valid).toBe(true)
      expect(validation.errors.length).toBe(0)
    })

    it('应该能够检测无效的操作', () => {
      const validation = validateBatchEditOperation(nodes, [], {
        approve_policy: 'any'
      })

      expect(validation.valid).toBe(false)
      expect(validation.errors.length).toBeGreaterThan(0)
    })

    it('应该能够生成警告', () => {
      const validation = validateBatchEditOperation(nodes, ['node_3'], {
        approve_policy: 'any'
      })

      expect(validation.warnings.length).toBeGreaterThan(0)
    })
  })

  describe('生成摘要', () => {
    it('应该能够生成批量编辑摘要', () => {
      const result = {
        successCount: 2,
        failureCount: 0,
        updatedNodes: nodes,
        failedNodeIds: []
      }

      const summary = generateBatchEditSummary(result, { approve_policy: 'any' })

      expect(summary).toContain('成功编辑 2 个节点')
      expect(summary).toContain('approve_policy')
    })

    it('应该能够包含失败信息', () => {
      const result = {
        successCount: 1,
        failureCount: 1,
        updatedNodes: nodes,
        failedNodeIds: ['node_2']
      }

      const summary = generateBatchEditSummary(result, { approve_policy: 'any' })

      expect(summary).toContain('失败 1 个节点')
    })
  })

  describe('边界情况', () => {
    it('应该能够处理空节点列表', () => {
      const result = batchUpdateNodes([], ['node_1'], { approve_policy: 'any' })

      expect(result.successCount).toBe(0)
      expect(result.updatedNodes.length).toBe(0)
    })

    it('应该能够处理无效的阈值', () => {
      const result = batchUpdateNodes(nodes, ['node_1'], {
        approve_threshold: 150
      })

      expect(result.updatedNodes[0].approve_threshold).toBeUndefined()
    })

    it('应该能够处理无效的 SLA 时长', () => {
      const result = batchUpdateNodes(nodes, ['node_1'], {
        sla_hours: -1
      })

      expect(result.updatedNodes[0].sla_hours).toBeUndefined()
    })

    it('应该能够处理无效的采样比例', () => {
      const result = batchUpdateNodes(nodes, ['node_1'], {
        auto_sample_ratio: 1.5
      })

      expect(result.updatedNodes[0].auto_sample_ratio).toBe(0)
    })
  })

  describe('性能测试', () => {
    it('应该能够快速处理大量节点', () => {
      const largeNodeList = Array.from({ length: 1000 }, (_, i) => ({
        ...nodes[0],
        id: i,
        temp_id: `node_${i}`
      }))

      const selectedIds = Array.from({ length: 100 }, (_, i) => `node_${i}`)

      const startTime = performance.now()
      batchUpdateNodes(largeNodeList, selectedIds, { approve_policy: 'any' })
      const endTime = performance.now()

      expect(endTime - startTime).toBeLessThan(100)
    })
  })
})
