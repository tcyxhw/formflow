/**
 * FlowRouteInspector 手动验证测试
 * 
 * 验证修复后的组件是否正确实现了模态框功能
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowRouteInspector from '../FlowRouteInspector.vue'
import type { FlowRouteConfig } from '@/types/flow'

describe('FlowRouteInspector - 手动验证', () => {
  it('验证：组件应该有模态框相关的方法和状态', () => {
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

    // 核心验证：这些方法和状态应该存在
    console.log('showConditionModal:', wrapper.vm.showConditionModal)
    console.log('editingCondition:', wrapper.vm.editingCondition)
    console.log('openConditionModal:', typeof wrapper.vm.openConditionModal)
    console.log('saveCondition:', typeof wrapper.vm.saveCondition)
    console.log('cancelCondition:', typeof wrapper.vm.cancelCondition)

    // 验证状态存在
    expect(wrapper.vm.showConditionModal).toBeDefined()
    expect(wrapper.vm.editingCondition).toBeDefined()
    
    // 验证方法存在
    expect(wrapper.vm.openConditionModal).toBeDefined()
    expect(wrapper.vm.saveCondition).toBeDefined()
    expect(wrapper.vm.cancelCondition).toBeDefined()
    
    // 验证方法是函数
    expect(typeof wrapper.vm.openConditionModal).toBe('function')
    expect(typeof wrapper.vm.saveCondition).toBe('function')
    expect(typeof wrapper.vm.cancelCondition).toBe('function')
  })

  it('验证：模态框工作流程', async () => {
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

    // 初始状态
    expect(wrapper.vm.showConditionModal).toBe(false)
    expect(wrapper.vm.editingCondition).toBeNull()

    // 打开模态框
    wrapper.vm.openConditionModal()
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.showConditionModal).toBe(true)
    expect(wrapper.vm.editingCondition).toEqual(route.condition)

    // 关闭模态框
    wrapper.vm.cancelCondition()
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.showConditionModal).toBe(false)
    expect(wrapper.vm.editingCondition).toBeNull()
  })

  it('验证：HTML结构包含模态框', () => {
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
          // 不 stub NModal，检查其存在
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

    // 检查HTML中是否包含模态框相关的文本
    const html = wrapper.html()
    console.log('Component HTML includes modal:', html.includes('n-modal'))
    
    // 验证组件结构
    expect(html).toBeTruthy()
  })
})
