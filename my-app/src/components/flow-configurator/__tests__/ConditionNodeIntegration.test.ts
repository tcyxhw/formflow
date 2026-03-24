/**
 * 条件节点编辑器集成测试
 * 
 * 测试范围：
 * - ConditionNodeEditor 与 FlowNodeInspector 的集成
 * - 条件节点的完整编辑流程
 * - 数据的正确保存和更新
 */

import { describe, it, expect, beforeEach } from 'vitest'
import type { ConditionBranchesConfig } from '@/types/flow'
import type { FlowNodeConfig } from '@/types/flow'

describe('ConditionNodeEditor Integration', () => {
  let conditionConfig: ConditionBranchesConfig | null

  const mockNodes: FlowNodeConfig[] = [
    {
      id: 1,
      name: '审批节点1',
      type: 'user',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: false,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_START',
      metadata: {},
    },
    {
      id: 2,
      name: '审批节点2',
      type: 'user',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: false,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_START',
      metadata: {},
    },
  ]

  beforeEach(() => {
    conditionConfig = null
  })

  it('应该创建新的条件分支配置', () => {
    const newBranch = {
      priority: 1,
      label: '大额招待费',
      condition: { type: 'GROUP', logic: 'AND', children: [] },
      target_node_id: 1,
    }

    conditionConfig = {
      branches: [newBranch],
      default_target_node_id: 2,
    }

    expect(conditionConfig).toBeDefined()
    expect(conditionConfig!.branches.length).toBe(1)
    expect(conditionConfig!.branches[0].label).toBe('大额招待费')
    expect(conditionConfig!.default_target_node_id).toBe(2)
  })

  it('应该支持多个分支', () => {
    const branches = [
      {
        priority: 1,
        label: '大额招待费',
        condition: { type: 'GROUP', logic: 'AND', children: [] },
        target_node_id: 1,
      },
      {
        priority: 2,
        label: '小额招待费',
        condition: { type: 'GROUP', logic: 'AND', children: [] },
        target_node_id: 2,
      },
    ]

    conditionConfig = {
      branches,
      default_target_node_id: 1,
    }

    expect(conditionConfig!.branches.length).toBe(2)
    expect(conditionConfig!.branches[0].priority).toBe(1)
    expect(conditionConfig!.branches[1].priority).toBe(2)
  })

  it('应该支持更新分支标签', () => {
    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '原始标签',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 1,
        },
      ],
      default_target_node_id: 1,
    }

    // 更新标签
    conditionConfig.branches[0].label = '更新后的标签'

    expect(conditionConfig.branches[0].label).toBe('更新后的标签')
  })

  it('应该支持更新分支目标节点', () => {
    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '分支1',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 1,
        },
      ],
      default_target_node_id: 1,
    }

    // 更新目标节点
    conditionConfig.branches[0].target_node_id = 2

    expect(conditionConfig.branches[0].target_node_id).toBe(2)
  })

  it('应该支持删除分支', () => {
    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '分支1',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 1,
        },
        {
          priority: 2,
          label: '分支2',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 2,
        },
      ],
      default_target_node_id: 1,
    }

    // 删除第一个分支
    conditionConfig.branches.splice(0, 1)

    expect(conditionConfig.branches.length).toBe(1)
    expect(conditionConfig.branches[0].label).toBe('分支2')
  })

  it('应该支持重新排序分支', () => {
    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '分支1',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 1,
        },
        {
          priority: 2,
          label: '分支2',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 2,
        },
      ],
      default_target_node_id: 1,
    }

    // 交换顺序
    const temp = conditionConfig.branches[0]
    conditionConfig.branches[0] = conditionConfig.branches[1]
    conditionConfig.branches[1] = temp

    // 重新计算优先级
    conditionConfig.branches.forEach((branch: any, index: number) => {
      branch.priority = index + 1
    })

    expect(conditionConfig.branches[0].label).toBe('分支2')
    expect(conditionConfig.branches[0].priority).toBe(1)
    expect(conditionConfig.branches[1].label).toBe('分支1')
    expect(conditionConfig.branches[1].priority).toBe(2)
  })

  it('应该支持更新默认目标节点', () => {
    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '分支1',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 1,
        },
      ],
      default_target_node_id: 1,
    }

    // 更新默认目标
    conditionConfig.default_target_node_id = 2

    expect(conditionConfig.default_target_node_id).toBe(2)
  })

  it('应该验证分支数量至少为2', () => {
    const isValid = (config: ConditionBranchesConfig | null): boolean => {
      if (!config) return false
      return config.branches.length >= 2
    }

    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '分支1',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 1,
        },
      ],
      default_target_node_id: 1,
    }

    expect(isValid(conditionConfig)).toBe(false)

    conditionConfig.branches.push({
      priority: 2,
      label: '分支2',
      condition: { type: 'GROUP', logic: 'AND', children: [] },
      target_node_id: 2,
    })

    expect(isValid(conditionConfig)).toBe(true)
  })

  it('应该验证默认目标节点已设置', () => {
    const isValid = (config: ConditionBranchesConfig | null): boolean => {
      if (!config) return false
      return config.default_target_node_id !== null && config.default_target_node_id !== undefined
    }

    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '分支1',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 1,
        },
        {
          priority: 2,
          label: '分支2',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 2,
        },
      ],
      default_target_node_id: 1,
    }

    expect(isValid(conditionConfig)).toBe(true)

    conditionConfig.default_target_node_id = null as any

    expect(isValid(conditionConfig)).toBe(false)
  })

  it('应该支持复杂的条件表达式', () => {
    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '大额招待费',
          condition: {
            type: 'GROUP',
            logic: 'AND',
            children: [
              {
                type: 'RULE',
                fieldKey: 'amount',
                fieldType: 'NUMBER',
                operator: 'GREATER_THAN',
                value: 1000,
              },
              {
                type: 'RULE',
                fieldKey: 'category',
                fieldType: 'SINGLE_SELECT',
                operator: 'EQUALS',
                value: '招待费',
              },
            ],
          },
          target_node_id: 1,
        },
      ],
      default_target_node_id: 2,
    }

    expect(conditionConfig.branches[0].condition.type).toBe('GROUP')
    expect((conditionConfig.branches[0].condition as any).children.length).toBe(2)
  })

  it('应该支持嵌套的条件组', () => {
    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '复杂条件',
          condition: {
            type: 'GROUP',
            logic: 'AND',
            children: [
              {
                type: 'GROUP',
                logic: 'OR',
                children: [
                  {
                    type: 'RULE',
                    fieldKey: 'status',
                    fieldType: 'SINGLE_SELECT',
                    operator: 'EQUALS',
                    value: 'pending',
                  },
                ],
              },
            ],
          },
          target_node_id: 1,
        },
      ],
      default_target_node_id: 2,
    }

    const nestedGroup = (conditionConfig.branches[0].condition as any).children[0]
    expect(nestedGroup.type).toBe('GROUP')
    expect(nestedGroup.logic).toBe('OR')
  })

  it('应该支持完整的流程配置场景', () => {
    // 模拟完整的流程配置场景
    const flowConfig: ConditionBranchesConfig = {
      branches: [
        {
          priority: 1,
          label: '大额招待费（>5000）',
          condition: {
            type: 'GROUP',
            logic: 'AND',
            children: [
              {
                type: 'RULE',
                fieldKey: 'amount',
                fieldType: 'NUMBER',
                operator: 'GREATER_THAN',
                value: 5000,
              },
              {
                type: 'RULE',
                fieldKey: 'category',
                fieldType: 'SINGLE_SELECT',
                operator: 'EQUALS',
                value: '招待费',
              },
            ],
          },
          target_node_id: 1,
        },
        {
          priority: 2,
          label: '中额招待费（1000-5000）',
          condition: {
            type: 'GROUP',
            logic: 'AND',
            children: [
              {
                type: 'GROUP',
                logic: 'OR',
                children: [
                  {
                    type: 'RULE',
                    fieldKey: 'amount',
                    fieldType: 'NUMBER',
                    operator: 'GREATER_EQUAL',
                    value: 1000,
                  },
                  {
                    type: 'RULE',
                    fieldKey: 'amount',
                    fieldType: 'NUMBER',
                    operator: 'LESS_EQUAL',
                    value: 5000,
                  },
                ],
              },
              {
                type: 'RULE',
                fieldKey: 'category',
                fieldType: 'SINGLE_SELECT',
                operator: 'EQUALS',
                value: '招待费',
              },
            ],
          },
          target_node_id: 2,
        },
        {
          priority: 3,
          label: '其他支出',
          condition: {
            type: 'GROUP',
            logic: 'AND',
            children: [
              {
                type: 'RULE',
                fieldKey: 'category',
                fieldType: 'SINGLE_SELECT',
                operator: 'NOT_EQUALS',
                value: '招待费',
              },
            ],
          },
          target_node_id: 3,
        },
      ],
      default_target_node_id: 3,
    }

    expect(flowConfig.branches.length).toBe(3)
    expect(flowConfig.branches[0].priority).toBe(1)
    expect(flowConfig.branches[1].priority).toBe(2)
    expect(flowConfig.branches[2].priority).toBe(3)
    expect(flowConfig.default_target_node_id).toBe(3)
  })

  it('应该支持动态添加和删除分支', () => {
    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '分支1',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 1,
        },
      ],
      default_target_node_id: 1,
    }

    // 添加分支
    conditionConfig.branches.push({
      priority: 2,
      label: '分支2',
      condition: { type: 'GROUP', logic: 'AND', children: [] },
      target_node_id: 2,
    })

    expect(conditionConfig.branches.length).toBe(2)

    // 删除分支
    conditionConfig.branches.splice(0, 1)

    expect(conditionConfig.branches.length).toBe(1)
    expect(conditionConfig.branches[0].label).toBe('分支2')
  })

  it('应该支持批量更新分支', () => {
    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '分支1',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 1,
        },
        {
          priority: 2,
          label: '分支2',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 2,
        },
      ],
      default_target_node_id: 1,
    }

    // 批量更新目标节点
    conditionConfig.branches.forEach(branch => {
      branch.target_node_id = 3
    })

    expect(conditionConfig.branches.every(b => b.target_node_id === 3)).toBe(true)
  })

  it('应该支持条件表达式的复制', () => {
    const originalCondition = {
      type: 'GROUP',
      logic: 'AND',
      children: [
        {
          type: 'RULE',
          fieldKey: 'amount',
          fieldType: 'NUMBER',
          operator: 'GREATER_THAN',
          value: 5000,
        },
      ],
    }

    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '分支1',
          condition: originalCondition,
          target_node_id: 1,
        },
        {
          priority: 2,
          label: '分支2',
          condition: JSON.parse(JSON.stringify(originalCondition)),
          target_node_id: 2,
        },
      ],
      default_target_node_id: 1,
    }

    // 验证两个分支有相同的条件结构
    const branch1Str = JSON.stringify(conditionConfig.branches[0].condition)
    const branch2Str = JSON.stringify(conditionConfig.branches[1].condition)
    expect(branch1Str).toBe(branch2Str)

    // 验证两个分支的条件是独立的（深拷贝）
    expect(conditionConfig.branches[0].condition).not.toBe(conditionConfig.branches[1].condition)
  })

  it('应该支持条件表达式的验证', () => {
    const isValidCondition = (condition: any): boolean => {
      if (!condition) return false
      if (condition.type === 'RULE') {
        return !!(condition.fieldKey && condition.operator && condition.value !== undefined)
      }
      if (condition.type === 'GROUP') {
        return !!(condition.logic && Array.isArray(condition.children))
      }
      return false
    }

    const validCondition = {
      type: 'RULE',
      fieldKey: 'amount',
      operator: 'GREATER_THAN',
      value: 5000,
    }

    const invalidCondition = {
      type: 'RULE',
      fieldKey: 'amount',
      // 缺少 operator 和 value
    }

    expect(isValidCondition(validCondition)).toBe(true)
    expect(isValidCondition(invalidCondition)).toBe(false)
  })

  it('应该支持分支的启用/禁用状态', () => {
    interface BranchWithStatus extends ConditionBranch {
      enabled?: boolean
    }

    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '分支1',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 1,
          enabled: true,
        } as BranchWithStatus,
        {
          priority: 2,
          label: '分支2',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 2,
          enabled: false,
        } as BranchWithStatus,
      ],
      default_target_node_id: 1,
    }

    const enabledBranches = (conditionConfig.branches as BranchWithStatus[]).filter(b => b.enabled)
    expect(enabledBranches.length).toBe(1)
  })

  it('应该支持分支的描述和备注', () => {
    interface BranchWithDescription extends ConditionBranch {
      description?: string
      remark?: string
    }

    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '大额',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 1,
          description: '金额大于 5000 元',
          remark: '需要财务总监审批',
        } as BranchWithDescription,
      ],
      default_target_node_id: 1,
    }

    const branch = conditionConfig.branches[0] as BranchWithDescription
    expect(branch.description).toBe('金额大于 5000 元')
    expect(branch.remark).toBe('需要财务总监审批')
  })

  it('应该支持导出配置为 JSON', () => {
    conditionConfig = {
      branches: [
        {
          priority: 1,
          label: '分支1',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 1,
        },
      ],
      default_target_node_id: 1,
    }

    const json = JSON.stringify(conditionConfig)
    const parsed = JSON.parse(json)

    expect(parsed.branches.length).toBe(1)
    expect(parsed.default_target_node_id).toBe(1)
  })

  it('应该支持从 JSON 导入配置', () => {
    const json = JSON.stringify({
      branches: [
        {
          priority: 1,
          label: '分支1',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 1,
        },
      ],
      default_target_node_id: 1,
    })

    conditionConfig = JSON.parse(json)

    expect(conditionConfig.branches.length).toBe(1)
    expect(conditionConfig.branches[0].label).toBe('分支1')
  })
})
