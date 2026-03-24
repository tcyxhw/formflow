/**
 * 手动测试：FlowRouteInspector 条件展示功能
 * 
 * 这个测试文件用于手动验证条件展示的视觉效果和格式化输出
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowRouteInspector from '../FlowRouteInspector.vue'
import { FlowRouteConfig } from '@/types/flow'

describe('FlowRouteInspector - Condition Display Manual Test', () => {
  it('should format simple equality condition', async () => {
    const route: FlowRouteConfig = {
      from_node_key: 'node1',
      to_node_key: 'node2',
      priority: 1,
      is_default: false,
      condition: {
        '==': [{ var: 'amount' }, 1000]
      }
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: [
          { label: '节点1', value: 'node1' },
          { label: '节点2', value: 'node2' }
        ],
        selectedIndex: 0,
        formId: 1,
        formSchema: {
          fields: [
            { id: 'amount', label: '报销金额', type: 'TEXT' }
          ]
        }
      }
    })

    const conditionDetails = wrapper.find('.condition-details')
    expect(conditionDetails.exists()).toBe(true)
    
    const text = conditionDetails.text()
    console.log('简单条件格式化输出:', text)
    expect(text).toContain('报销金额')
    expect(text).toContain('等于')
    expect(text).toContain('1000')
  })

  it('should format AND logic group', async () => {
    const route: FlowRouteConfig = {
      from_node_key: 'node1',
      to_node_key: 'node2',
      priority: 1,
      is_default: false,
      condition: {
        'and': [
          { '==': [{ var: 'amount' }, 1000] },
          { '==': [{ var: 'category' }, '差旅'] }
        ]
      }
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: [
          { label: '节点1', value: 'node1' },
          { label: '节点2', value: 'node2' }
        ],
        selectedIndex: 0,
        formId: 1,
        formSchema: {
          fields: [
            { id: 'amount', label: '报销金额', type: 'TEXT' },
            { id: 'category', label: '费用类别', type: 'TEXT' }
          ]
        }
      }
    })

    const conditionDetails = wrapper.find('.condition-details')
    expect(conditionDetails.exists()).toBe(true)
    
    const text = conditionDetails.text()
    console.log('AND 逻辑组格式化输出:', text)
    expect(text).toContain('报销金额')
    expect(text).toContain('费用类别')
    expect(text).toContain('且')
  })

  it('should format OR logic group', async () => {
    const route: FlowRouteConfig = {
      from_node_key: 'node1',
      to_node_key: 'node2',
      priority: 1,
      is_default: false,
      condition: {
        'or': [
          { '>': [{ var: 'amount' }, 5000] },
          { '==': [{ var: 'category' }, '差旅'] }
        ]
      }
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: [
          { label: '节点1', value: 'node1' },
          { label: '节点2', value: 'node2' }
        ],
        selectedIndex: 0,
        formId: 1,
        formSchema: {
          fields: [
            { id: 'amount', label: '报销金额', type: 'TEXT' },
            { id: 'category', label: '费用类别', type: 'TEXT' }
          ]
        }
      }
    })

    const conditionDetails = wrapper.find('.condition-details')
    expect(conditionDetails.exists()).toBe(true)
    
    const text = conditionDetails.text()
    console.log('OR 逻辑组格式化输出:', text)
    expect(text).toContain('报销金额')
    expect(text).toContain('大于')
    expect(text).toContain('或')
  })

  it('should format nested logic groups', async () => {
    const route: FlowRouteConfig = {
      from_node_key: 'node1',
      to_node_key: 'node2',
      priority: 1,
      is_default: false,
      condition: {
        'and': [
          { '>': [{ var: 'amount' }, 1000] },
          {
            'or': [
              { '==': [{ var: 'category' }, '差旅'] },
              { '==': [{ var: 'category' }, '办公'] }
            ]
          }
        ]
      }
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: [
          { label: '节点1', value: 'node1' },
          { label: '节点2', value: 'node2' }
        ],
        selectedIndex: 0,
        formId: 1,
        formSchema: {
          fields: [
            { id: 'amount', label: '报销金额', type: 'TEXT' },
            { id: 'category', label: '费用类别', type: 'TEXT' }
          ]
        }
      }
    })

    const conditionDetails = wrapper.find('.condition-details')
    expect(conditionDetails.exists()).toBe(true)
    
    const text = conditionDetails.text()
    console.log('嵌套逻辑组格式化输出:', text)
    expect(text).toContain('报销金额')
    expect(text).toContain('大于')
    expect(text).toContain('且')
    expect(text).toContain('或')
    expect(text).toContain('(') // 嵌套应该有括号
  })

  it('should show placeholder when no condition', async () => {
    const route: FlowRouteConfig = {
      from_node_key: 'node1',
      to_node_key: 'node2',
      priority: 1,
      is_default: false,
      condition: null
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route,
        nodeOptions: [
          { label: '节点1', value: 'node1' },
          { label: '节点2', value: 'node2' }
        ],
        selectedIndex: 0,
        formId: 1
      }
    })

    const conditionPlaceholder = wrapper.find('.condition-placeholder')
    expect(conditionPlaceholder.exists()).toBe(true)
    expect(conditionPlaceholder.text()).toContain('未设置条件')
  })
})
