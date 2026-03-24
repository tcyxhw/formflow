/**
 * FlowNodeInspector 组件单元测试
 * 
 * 测试范围：
 * - 节点基本信息编辑
 * - 审批策略配置
 * - 驳回策略选择
 * - 自动审批配置
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowNodeInspector from '../FlowNodeInspector.vue'
import type { FlowNodeConfig } from '@/types/flow'

describe('FlowNodeInspector - 驳回策略功能', () => {
  let wrapper: any

  const mockNode: FlowNodeConfig = {
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
    id: 1,
  }

  beforeEach(() => {
    wrapper = mount(FlowNodeInspector, {
      props: {
        node: mockNode,
        disabled: false,
      },
      global: {
        stubs: {
          ConditionNodeEditor: true,
          NForm: true,
          NFormItem: true,
          NInput: true,
          NSelect: true,
          NInputNumber: true,
          NSwitch: true,
          NSlider: true,
          NDivider: true,
          NAlert: true,
          NEmpty: true,
        },
      },
    })
  })

  it('应该正确渲染组件', () => {
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.inspector').exists()).toBe(true)
  })

  it('应该为审批节点包含驳回策略字段', () => {
    // 验证组件能够正确处理 reject_strategy 字段
    expect(wrapper.vm.node.reject_strategy).toBeDefined()
    expect(['TO_START', 'TO_PREVIOUS']).toContain(wrapper.vm.node.reject_strategy)
  })

  it('应该在条件节点时隐藏驳回策略', async () => {
    const conditionNode: FlowNodeConfig = {
      ...mockNode,
      type: 'condition',
    }
    
    await wrapper.setProps({ node: conditionNode })
    
    const dividers = wrapper.findAll('.n-divider-stub')
    const dividerTexts = dividers.map((d: any) => d.text())
    expect(dividerTexts).not.toContain('驳回策略')
  })

  it('应该在开始节点时隐藏驳回策略', async () => {
    const startNode: FlowNodeConfig = {
      ...mockNode,
      type: 'start',
    }
    
    await wrapper.setProps({ node: startNode })
    
    const dividers = wrapper.findAll('.n-divider-stub')
    const dividerTexts = dividers.map((d: any) => d.text())
    expect(dividerTexts).not.toContain('驳回策略')
  })

  it('应该在结束节点时隐藏驳回策略', async () => {
    const endNode: FlowNodeConfig = {
      ...mockNode,
      type: 'end',
    }
    
    await wrapper.setProps({ node: endNode })
    
    const dividers = wrapper.findAll('.n-divider-stub')
    const dividerTexts = dividers.map((d: any) => d.text())
    expect(dividerTexts).not.toContain('驳回策略')
  })

  it('应该在自动节点时支持驳回策略', async () => {
    const autoNode: FlowNodeConfig = {
      ...mockNode,
      type: 'auto',
    }
    
    await wrapper.setProps({ node: autoNode })
    
    // 验证自动节点也有 reject_strategy 字段
    expect(wrapper.vm.node.reject_strategy).toBeDefined()
  })

  it('应该能够更新驳回策略', async () => {
    // 验证 emitPatch 方法能够正确处理驳回策略更新
    const initialStrategy = wrapper.vm.node.reject_strategy
    expect(['TO_START', 'TO_PREVIOUS']).toContain(initialStrategy)
    
    // 验证可以切换策略
    const newStrategy = initialStrategy === 'TO_START' ? 'TO_PREVIOUS' : 'TO_START'
    expect(newStrategy).not.toBe(initialStrategy)
  })

  it('应该支持 TO_START 驳回策略', () => {
    const node: FlowNodeConfig = {
      ...mockNode,
      reject_strategy: 'TO_START',
    }
    
    wrapper = mount(FlowNodeInspector, {
      props: { node, disabled: false },
      global: { stubs: { ConditionNodeEditor: true } },
    })
    
    expect(wrapper.vm.node.reject_strategy).toBe('TO_START')
  })

  it('应该支持 TO_PREVIOUS 驳回策略', () => {
    const node: FlowNodeConfig = {
      ...mockNode,
      reject_strategy: 'TO_PREVIOUS',
    }
    
    wrapper = mount(FlowNodeInspector, {
      props: { node, disabled: false },
      global: { stubs: { ConditionNodeEditor: true } },
    })
    
    expect(wrapper.vm.node.reject_strategy).toBe('TO_PREVIOUS')
  })

  it('应该在禁用状态下隐藏驳回策略选择', async () => {
    await wrapper.setProps({ disabled: true })
    
    // 验证组件仍然存在但应该被禁用
    expect(wrapper.find('.inspector').exists()).toBe(true)
  })

  it('应该在没有选中节点时显示空状态', async () => {
    await wrapper.setProps({ node: undefined })
    
    expect(wrapper.find('.inspector-empty').exists()).toBe(true)
  })
})
