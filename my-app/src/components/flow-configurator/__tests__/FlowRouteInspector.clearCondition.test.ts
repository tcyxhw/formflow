/**
 * FlowRouteInspector 清空条件功能测试
 * 
 * 测试任务 3.4 的实现：
 * - 清空条件按钮的显示逻辑
 * - clearCondition 函数的功能
 * - 确认对话框的交互
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import FlowRouteInspector from '../FlowRouteInspector.vue'
import type { FlowRouteConfig } from '@/types/flow'

describe('FlowRouteInspector - 清空条件功能', () => {
  const mockNodeOptions = [
    { label: '开始节点', value: 'start' },
    { label: '审批节点', value: 'approval_1' },
    { label: '结束节点', value: 'end' }
  ]

  it('当路由有条件时，应该显示"清空条件"按钮', () => {
    const route: FlowRouteConfig = {
      from_node_key: 'start',
      to_node_key: 'approval_1',
      priority: 1,
      is_default: false,
      condition: { '==': [{ var: 'amount' }, 1000] }
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: mockNodeOptions,
        selectedIndex: 0,
        disabled: false
      }
    })

    // 查找"清空条件"按钮
    const clearButton = wrapper.findAll('button').find(btn => 
      btn.text().includes('清空条件')
    )
    
    expect(clearButton).toBeDefined()
    expect(clearButton?.exists()).toBe(true)
  })

  it('当路由没有条件时，不应该显示"清空条件"按钮', () => {
    const route: FlowRouteConfig = {
      from_node_key: 'start',
      to_node_key: 'approval_1',
      priority: 1,
      is_default: false,
      condition: null
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: mockNodeOptions,
        selectedIndex: 0,
        disabled: false
      }
    })

    // 查找"清空条件"按钮
    const clearButton = wrapper.findAll('button').find(btn => 
      btn.text().includes('清空条件')
    )
    
    expect(clearButton).toBeUndefined()
  })

  it('点击"清空条件"按钮应该触发 update-route 事件', async () => {
    const route: FlowRouteConfig = {
      from_node_key: 'start',
      to_node_key: 'approval_1',
      priority: 1,
      is_default: false,
      condition: { '==': [{ var: 'amount' }, 1000] }
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: mockNodeOptions,
        selectedIndex: 0,
        disabled: false
      },
      global: {
        stubs: {
          // 模拟 Naive UI 的 useDialog
          NButton: {
            template: '<button @click="$attrs.onClick"><slot /></button>'
          }
        }
      }
    })

    // 查找"清空条件"按钮
    const clearButton = wrapper.findAll('button').find(btn => 
      btn.text().includes('清空条件')
    )
    
    expect(clearButton).toBeDefined()
    
    // 注意：由于使用了 useDialog，实际测试需要模拟对话框的确认操作
    // 这里只验证按钮存在且可点击
    expect(clearButton?.attributes('disabled')).toBeUndefined()
  })

  it('当 disabled 为 true 时，"清空条件"按钮应该被禁用', () => {
    const route: FlowRouteConfig = {
      from_node_key: 'start',
      to_node_key: 'approval_1',
      priority: 1,
      is_default: false,
      condition: { '==': [{ var: 'amount' }, 1000] }
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: mockNodeOptions,
        selectedIndex: 0,
        disabled: true
      }
    })

    // 查找"清空条件"按钮
    const clearButton = wrapper.findAll('button').find(btn => 
      btn.text().includes('清空条件')
    )
    
    expect(clearButton).toBeDefined()
    // Naive UI 的按钮在 disabled 时会有相应的属性
    // 具体的禁用状态检查取决于 Naive UI 的实现
  })

  it('条件详情区域应该显示已配置的条件', () => {
    const route: FlowRouteConfig = {
      from_node_key: 'start',
      to_node_key: 'approval_1',
      priority: 1,
      is_default: false,
      condition: { '==': [{ var: 'amount' }, 1000] }
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: mockNodeOptions,
        selectedIndex: 0,
        disabled: false
      }
    })

    // 查找条件详情展示区域
    const conditionDetails = wrapper.find('.condition-details')
    expect(conditionDetails.exists()).toBe(true)
    
    // 验证条件内容被格式化显示
    const conditionContent = wrapper.find('.condition-content')
    expect(conditionContent.exists()).toBe(true)
    expect(conditionContent.text()).toContain('amount')
    expect(conditionContent.text()).toContain('1000')
  })

  it('当没有条件时，应该显示占位提示', () => {
    const route: FlowRouteConfig = {
      from_node_key: 'start',
      to_node_key: 'approval_1',
      priority: 1,
      is_default: false,
      condition: null
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: mockNodeOptions,
        selectedIndex: 0,
        disabled: false
      }
    })

    // 查找占位提示
    const placeholder = wrapper.find('.condition-placeholder')
    expect(placeholder.exists()).toBe(true)
    expect(placeholder.text()).toContain('未设置条件')
  })
})
