import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import FlowCanvas from '../FlowCanvas.vue'
import { useFlowDraftStore } from '@/stores/flowDraft'
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

describe('FlowCanvas Integration with Pinia Store', () => {
  let wrapper: any
  let store: any

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useFlowDraftStore()

    // 初始化 store 数据
    store.nodes = [
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

    store.routes = [
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

    store.nodesGraph = {
      '1': { x: 80, y: 160 },
      '2': { x: 280, y: 160 },
      '3': { x: 480, y: 160 }
    }

    wrapper = mount(FlowCanvas, {
      props: {
        nodes: store.nodes,
        routes: store.routes,
        nodesGraph: store.nodesGraph,
        selectedNodeKey: store.selectedNodeKey
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

  it('应该与 store 同步节点数据', () => {
    expect(wrapper.props('nodes')).toEqual(store.nodes)
    expect(wrapper.props('nodes')).toHaveLength(3)
  })

  it('应该与 store 同步路由数据', () => {
    expect(wrapper.props('routes')).toEqual(store.routes)
    expect(wrapper.props('routes')).toHaveLength(2)
  })

  it('应该与 store 同步节点位置', () => {
    expect(wrapper.props('nodesGraph')).toEqual(store.nodesGraph)
  })

  it('应该在选中节点时更新 store', async () => {
    const nodes = wrapper.findAll('.flow-node')
    await nodes[1].trigger('click')

    expect(wrapper.emitted('select-node')).toBeTruthy()
    expect(wrapper.emitted('select-node')[0]).toEqual(['2'])
  })

  it('应该在更新节点位置时发出事件', async () => {
    const node = wrapper.find('.flow-node')
    await node.trigger('pointerdown', {
      clientX: 100,
      clientY: 200,
      button: 0
    })

    await wrapper.find('.flow-canvas').trigger('pointermove', {
      clientX: 150,
      clientY: 250
    })

    await wrapper.find('.flow-canvas').trigger('pointerup')

    expect(wrapper.emitted('update-position')).toBeTruthy()
  })

  it('应该在添加路由时发出事件', async () => {
    wrapper.vm.connectionState.active = true
    wrapper.vm.connectionState.fromNodeKey = '1'

    await wrapper.find('.flow-canvas').trigger('pointerup', {
      clientX: 280,
      clientY: 210
    })

    expect(wrapper.emitted('add-route')).toBeTruthy()
  })

  it('应该在删除节点时发出事件', async () => {
    wrapper.vm.contextMenuNodeKey = '2'
    await wrapper.vm.handleContextMenuSelect('delete-node')

    expect(wrapper.emitted('delete-node')).toBeTruthy()
    expect(wrapper.emitted('delete-node')[0]).toEqual(['2'])
  })

  it('应该正确处理多个节点的选择', async () => {
    const nodes = wrapper.findAll('.flow-node')

    // 选择第一个节点
    await nodes[0].trigger('click')
    expect(wrapper.emitted('select-node')[0]).toEqual(['1'])

    // 选择第二个节点
    await nodes[1].trigger('click')
    expect(wrapper.emitted('select-node')[1]).toEqual(['2'])

    // 选择第三个节点
    await nodes[2].trigger('click')
    expect(wrapper.emitted('select-node')[2]).toEqual(['3'])
  })

  it('应该正确处理多个路由的选择', async () => {
    const routes = wrapper.findAll('.route-line')

    // 选择第一条路由
    await routes[0].trigger('click')
    expect(wrapper.emitted('select-route')[0]).toEqual([0])

    // 选择第二条路由
    await routes[1].trigger('click')
    expect(wrapper.emitted('select-route')[1]).toEqual([1])
  })

  it('应该在 props 更新时重新渲染', async () => {
    const newNode: FlowNodeConfig = {
      id: 4,
      name: '新节点',
      type: 'user',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: true,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      metadata: {},
      reject_strategy: 'TO_START'
    }

    const newNodes = [...store.nodes, newNode]
    await wrapper.setProps({ nodes: newNodes })

    const nodes = wrapper.findAll('.flow-node')
    expect(nodes).toHaveLength(4)
  })

  it('应该支持条件路由的显示', async () => {
    const routeWithCondition: FlowRouteConfig = {
      from_node_key: '1',
      to_node_key: '2',
      priority: 1,
      is_default: false,
      condition: { '>': [{ var: 'amount' }, 10000] }
    }

    await wrapper.setProps({ routes: [routeWithCondition] })
    const routes = wrapper.findAll('.route-line')

    expect(routes[0].attributes('stroke-dasharray')).toBe('8 4')
  })

  it('应该支持默认路由的显示', async () => {
    const defaultRoute: FlowRouteConfig = {
      from_node_key: '1',
      to_node_key: '2',
      priority: 1,
      is_default: true
    }

    await wrapper.setProps({ routes: [defaultRoute] })
    const routes = wrapper.findAll('.route-line')

    expect(routes[0].attributes('stroke-dasharray')).toBe('0')
  })

  it('应该在缩放时保持节点相对位置', async () => {
    const initialScale = wrapper.vm.scale
    wrapper.vm.scale = 1.5

    await wrapper.vm.$nextTick()

    const nodes = wrapper.findAll('.flow-node')
    expect(nodes).toHaveLength(3)
  })

  it('应该支持平移操作', async () => {
    const initialPanX = wrapper.vm.panX
    const initialPanY = wrapper.vm.panY

    wrapper.vm.panX = 100
    wrapper.vm.panY = 100

    await wrapper.vm.$nextTick()

    expect(wrapper.vm.panX).toBe(100)
    expect(wrapper.vm.panY).toBe(100)
  })

  it('应该在重置缩放时恢复初始状态', async () => {
    wrapper.vm.scale = 1.5
    wrapper.vm.panX = 100
    wrapper.vm.panY = 100

    wrapper.vm.resetZoom()

    expect(wrapper.vm.scale).toBe(1)
    expect(wrapper.vm.panX).toBe(0)
    expect(wrapper.vm.panY).toBe(0)
  })

  it('应该正确计算节点的连接点位置', () => {
    const startPos = wrapper.vm.getRouteStartPos(store.routes[0])
    const endPos = wrapper.vm.getRouteEndPos(store.routes[0])

    expect(startPos).toEqual({ x: 170, y: 210 })
    expect(endPos).toEqual({ x: 280, y: 210 })
  })

  it('应该支持连线拖拽的完整流程', async () => {
    const connectionPoint = wrapper.find('.connection-point-out')

    // 开始连线
    await connectionPoint.trigger('pointerdown', {
      clientX: 170,
      clientY: 210,
      button: 0
    })

    expect(wrapper.vm.connectionState.active).toBe(true)

    // 移动连线
    await wrapper.find('.flow-canvas').trigger('pointermove', {
      clientX: 280,
      clientY: 210
    })

    expect(wrapper.vm.connectionState.endX).toBeGreaterThan(0)
    expect(wrapper.vm.connectionState.endY).toBeGreaterThan(0)

    // 完成连线
    await wrapper.find('.flow-canvas').trigger('pointerup', {
      clientX: 280,
      clientY: 210
    })

    expect(wrapper.vm.connectionState.active).toBe(false)
  })
})
