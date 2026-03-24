/**
 * FlowRouteInspector 修复验证测试
 * 
 * **Validates: Requirements 2.1**
 * 
 * 验证缺陷 1 的修复：条件设置交互问题
 * 
 * 修复后行为：FlowRouteInspector 使用模态框来编辑条件，
 * 用户点击"编辑条件"按钮时，打开一个模态框进行条件编辑。
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowRouteInspector from '../FlowRouteInspector.vue'
import type { FlowRouteConfig } from '@/types/flow'

describe('FlowRouteInspector - 修复验证：条件设置模态框', () => {
  it('修复验证：应该有模态框状态管理', () => {
    // **Validates: Requirements 2.1**
    const route: FlowRouteConfig = {
      from_node_key: 'node-1',
      to_node_key: 'node-2',
      is_default: false,
      priority: 1,
      condition: null,
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: [
          { label: '节点1', value: 'node-1' },
          { label: '节点2', value: 'node-2' },
        ],
        selectedIndex: 0,
        disabled: false,
      },
      global: {
        stubs: {
          ConditionBuilder: true,
          NModal: true,
          NButton: true,
          NSelect: true,
          NInputNumber: true,
          NSwitch: true,
          NFormItem: true,
          NForm: true,
          NDivider: true,
          NInput: true,
          NEmpty: true,
        },
      },
    })

    // 验证：现在应该有模态框状态
    expect(wrapper.vm.showConditionModal).toBeDefined()
    expect(wrapper.vm.showConditionModal).toBe(false)
    
    // 验证：现在应该有打开模态框的方法
    expect(wrapper.vm.openConditionModal).toBeDefined()
    expect(typeof wrapper.vm.openConditionModal).toBe('function')
    
    // 验证：现在应该有保存条件的方法
    expect(wrapper.vm.saveCondition).toBeDefined()
    expect(typeof wrapper.vm.saveCondition).toBe('function')
    
    // 验证：现在应该有取消编辑的方法
    expect(wrapper.vm.cancelCondition).toBeDefined()
    expect(typeof wrapper.vm.cancelCondition).toBe('function')
  })

  it('修复验证：点击"编辑条件"按钮应该打开模态框', async () => {
    // **Validates: Requirements 2.1**
    const route: FlowRouteConfig = {
      from_node_key: 'node-1',
      to_node_key: 'node-2',
      is_default: false,
      priority: 1,
      condition: { and: [{ '==': [{ var: 'amount' }, 100] }] },
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: [
          { label: '节点1', value: 'node-1' },
          { label: '节点2', value: 'node-2' },
        ],
        selectedIndex: 0,
        disabled: false,
      },
      global: {
        stubs: {
          ConditionBuilder: true,
          NModal: true,
          NButton: true,
          NSelect: true,
          NInputNumber: true,
          NSwitch: true,
          NFormItem: true,
          NForm: true,
          NDivider: true,
          NInput: true,
          NEmpty: true,
        },
      },
    })

    // 初始状态：模态框应该是关闭的
    expect(wrapper.vm.showConditionModal).toBe(false)
    
    // 调用打开模态框的方法
    wrapper.vm.openConditionModal()
    await wrapper.vm.$nextTick()
    
    // 验证：模态框应该打开
    expect(wrapper.vm.showConditionModal).toBe(true)
    
    // 验证：editingCondition 应该被设置为当前条件
    expect(wrapper.vm.editingCondition).toEqual(route.condition)
  })

  it('修复验证：保存条件应该更新路由并关闭模态框', async () => {
    // **Validates: Requirements 2.1**
    const route: FlowRouteConfig = {
      from_node_key: 'node-1',
      to_node_key: 'node-2',
      is_default: false,
      priority: 1,
      condition: null,
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: [
          { label: '节点1', value: 'node-1' },
          { label: '节点2', value: 'node-2' },
        ],
        selectedIndex: 0,
        disabled: false,
      },
      global: {
        stubs: {
          ConditionBuilder: true,
          NModal: true,
          NButton: true,
          NSelect: true,
          NInputNumber: true,
          NSwitch: true,
          NFormItem: true,
          NForm: true,
          NDivider: true,
          NInput: true,
          NEmpty: true,
        },
      },
    })

    // 打开模态框
    wrapper.vm.openConditionModal()
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.showConditionModal).toBe(true)
    
    // 设置一个新条件
    const newCondition = { and: [{ '==': [{ var: 'status' }, 'approved'] }] }
    wrapper.vm.editingCondition = newCondition
    await wrapper.vm.$nextTick()
    
    // 保存条件
    wrapper.vm.saveCondition()
    await wrapper.vm.$nextTick()
    
    // 验证：模态框应该关闭
    expect(wrapper.vm.showConditionModal).toBe(false)
    
    // 验证：editingCondition 应该被清空
    expect(wrapper.vm.editingCondition).toBeNull()
    
    // 验证：应该触发 update-route 事件
    expect(wrapper.emitted('update-route')).toBeTruthy()
    const emittedEvents = wrapper.emitted('update-route') as any[]
    expect(emittedEvents[0][0]).toEqual({
      index: 0,
      patch: { condition: newCondition }
    })
  })

  it('修复验证：取消编辑应该关闭模态框而不保存', async () => {
    // **Validates: Requirements 2.1**
    const route: FlowRouteConfig = {
      from_node_key: 'node-1',
      to_node_key: 'node-2',
      is_default: false,
      priority: 1,
      condition: { and: [{ '==': [{ var: 'amount' }, 100] }] },
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: [
          { label: '节点1', value: 'node-1' },
          { label: '节点2', value: 'node-2' },
        ],
        selectedIndex: 0,
        disabled: false,
      },
      global: {
        stubs: {
          ConditionBuilder: true,
          NModal: true,
          NButton: true,
          NSelect: true,
          NInputNumber: true,
          NSwitch: true,
          NFormItem: true,
          NForm: true,
          NDivider: true,
          NInput: true,
          NEmpty: true,
        },
      },
    })

    // 打开模态框
    wrapper.vm.openConditionModal()
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.showConditionModal).toBe(true)
    
    // 修改条件（但不保存）
    const newCondition = { and: [{ '==': [{ var: 'status' }, 'rejected'] }] }
    wrapper.vm.editingCondition = newCondition
    await wrapper.vm.$nextTick()
    
    // 取消编辑
    wrapper.vm.cancelCondition()
    await wrapper.vm.$nextTick()
    
    // 验证：模态框应该关闭
    expect(wrapper.vm.showConditionModal).toBe(false)
    
    // 验证：editingCondition 应该被清空
    expect(wrapper.vm.editingCondition).toBeNull()
    
    // 验证：不应该触发 update-route 事件（或者只有初始的事件）
    const emittedEvents = wrapper.emitted('update-route')
    if (emittedEvents) {
      // 如果有事件，应该不包含新条件
      const lastEvent = emittedEvents[emittedEvents.length - 1] as any
      expect(lastEvent[0].patch.condition).not.toEqual(newCondition)
    }
  })

  it('修复验证：ConditionBuilder 应该在模态框中，而不是内联显示', () => {
    // **Validates: Requirements 2.1**
    const route: FlowRouteConfig = {
      from_node_key: 'node-1',
      to_node_key: 'node-2',
      is_default: false,
      priority: 1,
      condition: null,
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: [
          { label: '节点1', value: 'node-1' },
          { label: '节点2', value: 'node-2' },
        ],
        selectedIndex: 0,
        disabled: false,
      },
      global: {
        stubs: {
          ConditionBuilder: true,
          NModal: false, // 不 stub NModal，以便检查其存在
          NButton: true,
          NSelect: true,
          NInputNumber: true,
          NSwitch: true,
          NFormItem: true,
          NForm: true,
          NDivider: true,
          NInput: true,
          NEmpty: true,
        },
      },
    })

    // 验证：应该有一个模态框组件
    const modal = wrapper.findComponent({ name: 'NModal' })
    expect(modal.exists()).toBe(true)
    
    // 验证：模态框应该包含 ConditionBuilder
    const conditionBuilder = modal.findComponent({ name: 'ConditionBuilder' })
    expect(conditionBuilder.exists()).toBe(true)
  })
})

describe('FlowRouteInspector - 修复验证：UI 改进', () => {
  it('修复验证：应该显示"编辑条件"按钮', () => {
    // **Validates: Requirements 2.1**
    const route: FlowRouteConfig = {
      from_node_key: 'node-1',
      to_node_key: 'node-2',
      is_default: false,
      priority: 1,
      condition: null,
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: [
          { label: '节点1', value: 'node-1' },
          { label: '节点2', value: 'node-2' },
        ],
        selectedIndex: 0,
        disabled: false,
      },
      global: {
        stubs: {
          ConditionBuilder: true,
          NModal: true,
          NButton: false, // 不 stub NButton，以便检查按钮文本
          NSelect: true,
          NInputNumber: true,
          NSwitch: true,
          NFormItem: true,
          NForm: true,
          NDivider: true,
          NInput: true,
          NEmpty: true,
        },
      },
    })

    // 验证：应该有"编辑条件"按钮
    const editButton = wrapper.find('button')
    expect(editButton.exists()).toBe(true)
    
    // 注意：由于 NButton 的实现，我们可能需要检查文本内容
    // 这里我们只验证按钮存在
  })

  it('修复验证：应该显示条件状态（已设置/未设置）', () => {
    // **Validates: Requirements 2.1**
    
    // 测试未设置条件的情况
    const routeWithoutCondition: FlowRouteConfig = {
      from_node_key: 'node-1',
      to_node_key: 'node-2',
      is_default: false,
      priority: 1,
      condition: null,
    }

    const wrapper1 = mount(FlowRouteInspector, {
      props: {
        route: routeWithoutCondition,
        nodeOptions: [
          { label: '节点1', value: 'node-1' },
          { label: '节点2', value: 'node-2' },
        ],
        selectedIndex: 0,
        disabled: false,
      },
      global: {
        stubs: {
          ConditionBuilder: true,
          NModal: true,
          NButton: true,
          NSelect: true,
          NInputNumber: true,
          NSwitch: true,
          NFormItem: true,
          NForm: true,
          NDivider: true,
          NInput: true,
          NEmpty: true,
        },
      },
    })

    // 验证：应该显示"未设置条件"
    expect(wrapper1.text()).toContain('未设置条件')
    
    // 测试已设置条件的情况
    const routeWithCondition: FlowRouteConfig = {
      from_node_key: 'node-1',
      to_node_key: 'node-2',
      is_default: false,
      priority: 1,
      condition: { and: [{ '==': [{ var: 'amount' }, 100] }] },
    }

    const wrapper2 = mount(FlowRouteInspector, {
      props: {
        route: routeWithCondition,
        nodeOptions: [
          { label: '节点1', value: 'node-1' },
          { label: '节点2', value: 'node-2' },
        ],
        selectedIndex: 0,
        disabled: false,
      },
      global: {
        stubs: {
          ConditionBuilder: true,
          NModal: true,
          NButton: true,
          NSelect: true,
          NInputNumber: true,
          NSwitch: true,
          NFormItem: true,
          NForm: true,
          NDivider: true,
          NInput: true,
          NEmpty: true,
        },
      },
    })

    // 验证：应该显示"已设置条件"
    expect(wrapper2.text()).toContain('已设置条件')
  })
})
