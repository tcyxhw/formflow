import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowCanvas from '../FlowCanvas.vue'
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

describe('FlowCanvas - 多选功能', () => {
  let wrapper: any

  const mockNodes: FlowNodeConfig[] = [
    {
      id: 1,
      name: '开始节点',
      type: 'start',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: false,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      metadata: {},
      reject_strategy: 'TO_START'
    },
    {
      id: 2,
      name: '审批节点',
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
      id: 3,
      name: '结束节点',
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

  const mockRoutes: FlowRouteConfig[] = [
    {
      from_node_key: '1',
      to_node_key: '2',
      priority: 1,
      is_default: true
    },
    {
      from_node_key: '2',
      to_node_key: '3',
      priority: 1,
      is_default: true
    }
  ]

  const mockNodesGraph = {
    '1': { x: 80, y: 160 },
    '2': { x: 280, y: 160 },
    '3': { x: 480, y: 160 }
  }

  beforeEach(() => {
    wrapper = mount(FlowCanvas, {
      props: {
        nodes: mockNodes,
        routes: mockRoutes,
        nodesGraph: mockNodesGraph,
        selectedNodeKey: '1',
        selectedNodeKeys: new Set()
      },
      global: {
        stubs: {
          NButton: true,
          NButtonGroup: true,
          NIcon: true,
          NDropdown: true
        }
      }
    })
  })

  it('应该在普通点击时发出单选事件', async () => {
    const nodes = wrapper.findAll('.flow-node')
    await nodes[1].trigger('click', { ctrlKey: false, metaKey: false })
    
    expect(wrapper.emitted('select-node')).toBeTruthy()
    const emitted = wrapper.emitted('select-node')[0]
    expect(emitted[0]).toBe('2')
    expect(emitted[1]).toBe(false)
  })

  it('应该在 Ctrl+Click 时发出多选事件', async () => {
    const nodes = wrapper.findAll('.flow-node')
    await nodes[1].trigger('click', { ctrlKey: true, metaKey: false })
    
    expect(wrapper.emitted('select-node')).toBeTruthy()
    const emitted = wrapper.emitted('select-node')[0]
    expect(emitted[0]).toBe('2')
    expect(emitted[1]).toBe(true)
  })

  it('应该在 Cmd+Click 时发出多选事件（Mac）', async () => {
    const nodes = wrapper.findAll('.flow-node')
    await nodes[1].trigger('click', { ctrlKey: false, metaKey: true })
    
    expect(wrapper.emitted('select-node')).toBeTruthy()
    const emitted = wrapper.emitted('select-node')[0]
    expect(emitted[0]).toBe('2')
    expect(emitted[1]).toBe(true)
  })

  it('应该显示多选节点的样式', async () => {
    const selectedNodeKeys = new Set(['1', '2'])
    await wrapper.setProps({ selectedNodeKeys })
    
    const nodes = wrapper.findAll('.flow-node')
    expect(nodes[0].classes()).toContain('is-multi-selected')
    expect(nodes[1].classes()).toContain('is-multi-selected')
    expect(nodes[2].classes()).not.toContain('is-multi-selected')
  })

  it('应该正确判断节点是否被多选', async () => {
    const selectedNodeKeys = new Set(['1', '2'])
    await wrapper.setProps({ selectedNodeKeys })
    
    expect(wrapper.vm.isNodeMultiSelected('1')).toBe(true)
    expect(wrapper.vm.isNodeMultiSelected('2')).toBe(true)
    expect(wrapper.vm.isNodeMultiSelected('3')).toBe(false)
  })

  it('应该在多选和单选之间切换', async () => {
    const selectedNodeKeys = new Set(['1', '2'])
    await wrapper.setProps({ selectedNodeKeys })
    
    let nodes = wrapper.findAll('.flow-node')
    expect(nodes[0].classes()).toContain('is-multi-selected')
    expect(nodes[1].classes()).toContain('is-multi-selected')
    
    // 切换到单选
    await wrapper.setProps({ selectedNodeKeys: new Set(['1']) })
    
    nodes = wrapper.findAll('.flow-node')
    expect(nodes[0].classes()).toContain('is-multi-selected')
    expect(nodes[1].classes()).not.toContain('is-multi-selected')
  })

  it('应该在清除多选时移除样式', async () => {
    const selectedNodeKeys = new Set(['1', '2'])
    await wrapper.setProps({ selectedNodeKeys })
    
    let nodes = wrapper.findAll('.flow-node')
    expect(nodes[0].classes()).toContain('is-multi-selected')
    
    // 清除多选
    await wrapper.setProps({ selectedNodeKeys: new Set() })
    
    nodes = wrapper.findAll('.flow-node')
    expect(nodes[0].classes()).not.toContain('is-multi-selected')
    expect(nodes[1].classes()).not.toContain('is-multi-selected')
  })

  it('应该支持多个节点同时被多选', async () => {
    const selectedNodeKeys = new Set(['1', '2', '3'])
    await wrapper.setProps({ selectedNodeKeys })
    
    const nodes = wrapper.findAll('.flow-node')
    expect(nodes[0].classes()).toContain('is-multi-selected')
    expect(nodes[1].classes()).toContain('is-multi-selected')
    expect(nodes[2].classes()).toContain('is-multi-selected')
  })

  it('应该在单选时保持选中状态', async () => {
    const selectedNodeKeys = new Set(['2'])
    await wrapper.setProps({ 
      selectedNodeKey: '2',
      selectedNodeKeys 
    })
    
    const nodes = wrapper.findAll('.flow-node')
    expect(nodes[1].classes()).toContain('is-selected')
    expect(nodes[1].classes()).toContain('is-multi-selected')
  })
})
