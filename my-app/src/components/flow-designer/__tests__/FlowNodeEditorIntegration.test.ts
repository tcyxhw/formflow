import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowNodeEditor from '../FlowNodeEditor.vue'
import type { FlowNodeConfig, ConditionBranchesConfig } from '@/types/flow'

describe('FlowNodeEditor 集成测试', () => {
  let wrapper: any

  const mockConditionNode: FlowNodeConfig = {
    id: 2,
    name: '条件分支',
    type: 'condition',
    approve_policy: 'any',
    route_mode: 'exclusive',
    allow_delegate: false,
    auto_approve_enabled: false,
    auto_sample_ratio: 0,
    reject_strategy: 'TO_START',
    condition_branches: {
      branches: [
        {
          priority: 1,
          label: '大额',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 3
        }
      ],
      default_target_node_id: 4
    },
    metadata: {}
  }

  const mockAllNodes: FlowNodeConfig[] = [
    {
      id: 1,
      name: '开始',
      type: 'start',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: false,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      metadata: {},
      reject_strategy: 'TO_START'
    },
    mockConditionNode,
    {
      id: 3,
      name: '审批1',
      type: 'user',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: true,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      metadata: {},
      reject_strategy: 'TO_START'
    },
    {
      id: 4,
      name: '审批2',
      type: 'user',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: true,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      metadata: {},
      reject_strategy: 'TO_START'
    },
    {
      id: 5,
      name: '结束',
      type: 'end',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: false,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      metadata: {},
      reject_strategy: 'TO_START'
    }
  ]

  beforeEach(() => {
    wrapper = mount(FlowNodeEditor, {
      props: {
        node: mockConditionNode,
        allNodes: mockAllNodes,
        formId: 1,
        disabled: false
      },
      global: {
        stubs: {
          NForm: true,
          NFormItem: true,
          NInput: true,
          NSelect: true,
          NSwitch: true,
          NInputNumber: true,
          NSlider: true,
          NDivider: true,
          NEmpty: true,
          ConditionNodeEditor: true
        }
      }
    })
  })

  it('应该支持条件节点的完整配置', () => {
    expect(wrapper.props('node').type).toBe('condition')
    expect(wrapper.props('node').condition_branches).toBeDefined()
    expect(wrapper.props('node').condition_branches?.branches.length).toBe(1)
  })

  it('应该在条件节点中显示条件编辑器', async () => {
    const text = wrapper.text()
    expect(text).toContain('条件分支配置')
  })

  it('应该支持多个节点的切换编辑', async () => {
    const userNode = mockAllNodes[2]
    await wrapper.setProps({ node: userNode })
    
    expect(wrapper.props('node').type).toBe('user')
    expect(wrapper.props('node').id).toBe(3)
  })

  it('应该在编辑审批节点时显示驳回策略选项', async () => {
    const userNode = mockAllNodes[2]
    await wrapper.setProps({ node: userNode })
    
    const text = wrapper.text()
    expect(text).toContain('驳回策略')
  })

  it('应该支持 TO_START 驳回策略', async () => {
    const userNode = { ...mockAllNodes[2], reject_strategy: 'TO_START' as const }
    await wrapper.setProps({ node: userNode })
    
    expect(wrapper.props('node').reject_strategy).toBe('TO_START')
  })

  it('应该支持 TO_PREVIOUS 驳回策略', async () => {
    const userNode = { ...mockAllNodes[2], reject_strategy: 'TO_PREVIOUS' as const }
    await wrapper.setProps({ node: userNode })
    
    expect(wrapper.props('node').reject_strategy).toBe('TO_PREVIOUS')
  })

  it('应该支持不同的审批人类型', async () => {
    const userNode = { ...mockAllNodes[2], assignee_type: 'user' as const }
    await wrapper.setProps({ node: userNode })
    expect(wrapper.props('node').assignee_type).toBe('user')

    const groupNode = { ...mockAllNodes[2], assignee_type: 'group' as const }
    await wrapper.setProps({ node: groupNode })
    expect(wrapper.props('node').assignee_type).toBe('group')

    const roleNode = { ...mockAllNodes[2], assignee_type: 'role' as const }
    await wrapper.setProps({ node: roleNode })
    expect(wrapper.props('node').assignee_type).toBe('role')
  })

  it('应该支持不同的会签策略', async () => {
    const anyNode = { ...mockAllNodes[2], approve_policy: 'any' as const }
    await wrapper.setProps({ node: anyNode })
    expect(wrapper.props('node').approve_policy).toBe('any')

    const allNode = { ...mockAllNodes[2], approve_policy: 'all' as const }
    await wrapper.setProps({ node: allNode })
    expect(wrapper.props('node').approve_policy).toBe('all')

    const percentNode = { ...mockAllNodes[2], approve_policy: 'percent' as const }
    await wrapper.setProps({ node: percentNode })
    expect(wrapper.props('node').approve_policy).toBe('percent')
  })

  it('应该支持 SLA 配置', async () => {
    const slaNode = { ...mockAllNodes[2], sla_hours: 24 }
    await wrapper.setProps({ node: slaNode })
    
    expect(wrapper.props('node').sla_hours).toBe(24)
  })

  it('应该支持自动审批配置', async () => {
    const autoNode = {
      ...mockAllNodes[2],
      auto_approve_enabled: true,
      auto_sample_ratio: 0.1
    }
    await wrapper.setProps({ node: autoNode })
    
    expect(wrapper.props('node').auto_approve_enabled).toBe(true)
    expect(wrapper.props('node').auto_sample_ratio).toBe(0.1)
  })

  it('应该支持路由模式配置', async () => {
    const exclusiveNode = { ...mockAllNodes[2], route_mode: 'exclusive' as const }
    await wrapper.setProps({ node: exclusiveNode })
    expect(wrapper.props('node').route_mode).toBe('exclusive')

    const parallelNode = { ...mockAllNodes[2], route_mode: 'parallel' as const }
    await wrapper.setProps({ node: parallelNode })
    expect(wrapper.props('node').route_mode).toBe('parallel')
  })

  it('应该在禁用状态下保持所有配置', async () => {
    await wrapper.setProps({ disabled: true })
    
    expect(wrapper.props('disabled')).toBe(true)
    expect(wrapper.props('node')).toBeDefined()
  })

  it('应该正确处理条件分支配置的更新', async () => {
    const newBranches: ConditionBranchesConfig = {
      branches: [
        {
          priority: 1,
          label: '分支1',
          condition: { type: 'GROUP', logic: 'AND', children: [] },
          target_node_id: 3
        },
        {
          priority: 2,
          label: '分支2',
          condition: { type: 'GROUP', logic: 'OR', children: [] },
          target_node_id: 4
        }
      ],
      default_target_node_id: 5
    }

    const updatedNode = { ...mockConditionNode, condition_branches: newBranches }
    await wrapper.setProps({ node: updatedNode })
    
    expect(wrapper.props('node').condition_branches?.branches.length).toBe(2)
    expect(wrapper.props('node').condition_branches?.default_target_node_id).toBe(5)
  })

  it('应该支持节点名称的编辑', async () => {
    const renamedNode = { ...mockAllNodes[2], name: '新的审批节点名称' }
    await wrapper.setProps({ node: renamedNode })
    
    expect(wrapper.props('node').name).toBe('新的审批节点名称')
  })

  it('应该在所有节点类型间正确切换', async () => {
    const nodeTypes = ['start', 'user', 'condition', 'auto', 'end']
    
    for (const type of nodeTypes) {
      const node = mockAllNodes.find(n => n.type === type)
      if (node) {
        await wrapper.setProps({ node })
        expect(wrapper.props('node').type).toBe(type)
      }
    }
  })

  it('应该支持通过阈值的配置', async () => {
    const percentNode = {
      ...mockAllNodes[2],
      approve_policy: 'percent' as const,
      approve_threshold: 75
    }
    await wrapper.setProps({ node: percentNode })
    
    expect(wrapper.props('node').approve_threshold).toBe(75)
  })

  it('应该支持代理权限配置', async () => {
    const delegateNode = { ...mockAllNodes[2], allow_delegate: true }
    await wrapper.setProps({ node: delegateNode })
    expect(wrapper.props('node').allow_delegate).toBe(true)

    const noDelegateNode = { ...mockAllNodes[2], allow_delegate: false }
    await wrapper.setProps({ node: noDelegateNode })
    expect(wrapper.props('node').allow_delegate).toBe(false)
  })
})
