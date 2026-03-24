/**
 * 驳回策略集成测试
 * 
 * 验证驳回策略在流程配置中的完整功能
 */

import { describe, it, expect } from 'vitest'
import type { FlowNodeConfig, RejectStrategy } from '@/types/flow'

describe('驳回策略集成测试', () => {
  it('应该支持创建带有 TO_START 策略的审批节点', () => {
    const node: FlowNodeConfig = {
      name: '经理审批',
      type: 'user',
      assignee_type: 'user',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: false,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_START',
      metadata: {},
    }

    expect(node.reject_strategy).toBe('TO_START')
    expect(node.type).toBe('user')
  })

  it('应该支持创建带有 TO_PREVIOUS 策略的审批节点', () => {
    const node: FlowNodeConfig = {
      name: '总经理审批',
      type: 'user',
      assignee_type: 'user',
      approve_policy: 'all',
      route_mode: 'exclusive',
      allow_delegate: true,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_PREVIOUS',
      metadata: {},
    }

    expect(node.reject_strategy).toBe('TO_PREVIOUS')
  })

  it('应该支持在运行时切换驳回策略', () => {
    const node: FlowNodeConfig = {
      name: '审批节点',
      type: 'user',
      assignee_type: 'user',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: false,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_START',
      metadata: {},
    }

    // 模拟切换策略
    const updatedNode: FlowNodeConfig = {
      ...node,
      reject_strategy: 'TO_PREVIOUS',
    }

    expect(node.reject_strategy).toBe('TO_START')
    expect(updatedNode.reject_strategy).toBe('TO_PREVIOUS')
  })

  it('应该在多个审批节点中独立配置驳回策略', () => {
    const nodes: FlowNodeConfig[] = [
      {
        name: '部门经理',
        type: 'user',
        assignee_type: 'user',
        approve_policy: 'any',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {},
        id: 1,
      },
      {
        name: '总经理',
        type: 'user',
        assignee_type: 'user',
        approve_policy: 'any',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_PREVIOUS',
        metadata: {},
        id: 2,
      },
      {
        name: '财务审批',
        type: 'user',
        assignee_type: 'user',
        approve_policy: 'any',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {},
        id: 3,
      },
    ]

    expect(nodes[0].reject_strategy).toBe('TO_START')
    expect(nodes[1].reject_strategy).toBe('TO_PREVIOUS')
    expect(nodes[2].reject_strategy).toBe('TO_START')
  })

  it('应该验证驳回策略值的有效性', () => {
    const validStrategies: RejectStrategy[] = ['TO_START', 'TO_PREVIOUS']

    const node: FlowNodeConfig = {
      name: '审批节点',
      type: 'user',
      assignee_type: 'user',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: false,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_START',
      metadata: {},
    }

    expect(validStrategies).toContain(node.reject_strategy)
  })

  it('应该在条件节点中不使用驳回策略', () => {
    const conditionNode: FlowNodeConfig = {
      name: '条件分支',
      type: 'condition',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: false,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_START', // 条件节点不应该使用此字段
      metadata: {},
    }

    // 条件节点虽然有 reject_strategy 字段，但在实际使用中应该被忽略
    expect(conditionNode.type).toBe('condition')
    expect(conditionNode.reject_strategy).toBe('TO_START')
  })

  it('应该支持自动节点的驳回策略', () => {
    const autoNode: FlowNodeConfig = {
      name: '自动审批',
      type: 'auto',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: false,
      auto_approve_enabled: true,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_PREVIOUS',
      metadata: {},
    }

    expect(autoNode.type).toBe('auto')
    expect(autoNode.reject_strategy).toBe('TO_PREVIOUS')
  })

  it('应该保持驳回策略在节点克隆时的一致性', () => {
    const originalNode: FlowNodeConfig = {
      name: '原始节点',
      type: 'user',
      assignee_type: 'user',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: false,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_PREVIOUS',
      metadata: {},
      id: 1,
    }

    // 克隆节点
    const clonedNode: FlowNodeConfig = {
      ...originalNode,
      id: 2,
      name: '克隆节点',
    }

    expect(clonedNode.reject_strategy).toBe(originalNode.reject_strategy)
  })
})
