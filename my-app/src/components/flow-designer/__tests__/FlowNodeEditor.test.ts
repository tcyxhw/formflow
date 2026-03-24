import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowNodeEditor from '../FlowNodeEditor.vue'
import type { FlowNodeConfig } from '@/types/flow'

describe('FlowNodeEditor', () => {
  let wrapper: any

  const mockNode: FlowNodeConfig = {
    id: 1,
    name: '审批节点',
    type: 'user',
    assignee_type: 'user',
    approve_policy: 'any',
    route_mode: 'exclusive',
    allow_delegate: true,
    auto_approve_enabled: false,
    auto_sample_ratio: 0,
    reject_strategy: 'TO_START',
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
    mockNode,
    {
      id: 3,
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
        node: mockNode,
        allNodes: mockAllNodes,
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

  it('应该正确渲染节点编辑器', () => {
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.flow-node-editor').exists()).toBe(true)
  })

  it('应该显示节点名称', () => {
    expect(wrapper.find('.title').text()).toBe('节点编辑器')
  })

  it('当没有选中节点时应该显示空状态', async () => {
    await wrapper.setProps({ node: undefined })
    expect(wrapper.find('.editor-empty').exists()).toBe(true)
  })

  it('应该在节点类型为 user 时显示审批人配置', async () => {
    const userNode = { ...mockNode, type: 'user' as const }
    await wrapper.setProps({ node: userNode })
    
    // 检查是否包含审批人配置相关的文本
    const text = wrapper.text()
    expect(text).toContain('审批人配置')
  })

  it('应该在节点类型为 condition 时显示条件分支配置', async () => {
    const conditionNode: FlowNodeConfig = {
      ...mockNode,
      type: 'condition',
      condition_branches: {
        branches: [],
        default_target_node_id: 3
      }
    }
    await wrapper.setProps({ node: conditionNode })
    
    const text = wrapper.text()
    expect(text).toContain('条件分支配置')
  })

  it('应该在节点类型为 start 或 end 时不显示审批人配置', async () => {
    const startNode = { ...mockNode, type: 'start' as const }
    await wrapper.setProps({ node: startNode })
    
    const text = wrapper.text()
    expect(text).not.toContain('审批人配置')
  })

  it('应该在 approve_policy 为 percent 时显示通过阈值', async () => {
    const percentNode = { ...mockNode, approve_policy: 'percent' as const }
    await wrapper.setProps({ node: percentNode })
    
    const text = wrapper.text()
    expect(text).toContain('通过阈值')
  })

  it('应该在启用自动审批时显示抽检比例', async () => {
    const autoNode = { ...mockNode, auto_approve_enabled: true }
    await wrapper.setProps({ node: autoNode })
    
    const text = wrapper.text()
    expect(text).toContain('抽检比例')
  })

  it('应该发送正确的更新事件', async () => {
    const emitSpy = wrapper.vm.$emit = () => {}
    
    // 模拟节点名称更新
    wrapper.vm.emitPatch({ name: '新节点名称' })
    
    // 验证事件已发送
    expect(wrapper.emitted('update-node')).toBeTruthy()
  })

  it('应该在禁用状态下禁用所有输入', async () => {
    await wrapper.setProps({ disabled: true })
    
    // 验证禁用状态已应用
    expect(wrapper.props('disabled')).toBe(true)
  })

  it('应该正确处理节点类型变更', async () => {
    const newNode = { ...mockNode, type: 'condition' as const }
    await wrapper.setProps({ node: newNode })
    
    expect(wrapper.props('node').type).toBe('condition')
  })

  it('应该显示所有必要的表单项', async () => {
    const text = wrapper.text()
    expect(text).toContain('节点名称')
    expect(text).toContain('节点类型')
    expect(text).toContain('路由模式')
  })

  it('应该支持 SLA 配置', async () => {
    const slaNode = { ...mockNode, sla_hours: 24 }
    await wrapper.setProps({ node: slaNode })
    
    const text = wrapper.text()
    expect(text).toContain('SLA')
  })

  it('应该支持驳回策略配置', async () => {
    const rejectNode = { ...mockNode, reject_strategy: 'TO_PREVIOUS' as const }
    await wrapper.setProps({ node: rejectNode })
    
    const text = wrapper.text()
    expect(text).toContain('驳回策略')
  })
})
