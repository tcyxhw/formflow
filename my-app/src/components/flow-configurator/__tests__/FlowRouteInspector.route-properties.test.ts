/**
 * FlowRouteInspector 路由属性绑定测试
 * 
 * 验证路由属性（优先级、默认状态）是否正确绑定到具体的路由
 * - 修改优先级时只影响当前路由
 * - 修改默认状态时只影响当前路由
 * - 不同路由的属性保持独立
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowRouteInspector from '../FlowRouteInspector.vue'
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

describe('FlowRouteInspector - 路由属性绑定测试', () => {
  let nodes: FlowNodeConfig[]
  let routes: FlowRouteConfig[]

  beforeEach(() => {
    // 创建测试节点
    nodes = [
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
        assignee_value: null,
        auto_approve_cond: null,
        auto_reject_cond: null,
        reject_strategy: 'TO_START',
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
        assignee_value: null,
        auto_approve_cond: null,
        auto_reject_cond: null,
        reject_strategy: 'TO_START',
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
        assignee_value: null,
        auto_approve_cond: null,
        auto_reject_cond: null,
        reject_strategy: 'TO_START',
      },
    ]

    // 创建测试路由
    routes = [
      {
        from_node_key: '1',
        to_node_key: '2',
        priority: 1,
        is_default: true,
        condition: null,
      },
      {
        from_node_key: '2',
        to_node_key: '3',
        priority: 2,
        is_default: false,
        condition: null,
      },
    ]
  })

  it('应该正确显示路由的优先级', () => {
    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: routes[0],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '2',
      },
    })

    const vm = wrapper.vm as any
    expect(vm.priorityValue).toBe(1)
  })

  it('应该正确显示路由的默认状态', () => {
    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: routes[0],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '2',
      },
    })

    const vm = wrapper.vm as any
    expect(vm.isDefaultValue).toBe(true)
  })

  it('修改优先级时应该只影响当前路由', async () => {
    const updateRouteSpy = vi.fn()

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: routes[0],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '2',
        onUpdateRoute: updateRouteSpy,
      },
    })

    const vm = wrapper.vm as any

    // 修改优先级
    vm.emitPatch({ priority: 5 })
    await wrapper.vm.$nextTick()

    // 验证 emitPatch 是否被调用
    expect(updateRouteSpy).toHaveBeenCalled()
    const callArgs = updateRouteSpy.mock.calls[0][0]
    expect(callArgs.index).toBe(0)
    expect(callArgs.patch.priority).toBe(5)
  })

  it('修改默认状态时应该只影响当前路由', async () => {
    const updateRouteSpy = vi.fn()

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: routes[0],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '2',
        onUpdateRoute: updateRouteSpy,
      },
    })

    const vm = wrapper.vm as any

    // 修改默认状态
    vm.emitPatch({ is_default: false })
    await wrapper.vm.$nextTick()

    // 验证 emitPatch 是否被调用
    expect(updateRouteSpy).toHaveBeenCalled()
    const callArgs = updateRouteSpy.mock.calls[0][0]
    expect(callArgs.index).toBe(0)
    expect(callArgs.patch.is_default).toBe(false)
  })

  it('不同路由的优先级应该保持独立', () => {
    // 编辑第一个路由
    const wrapper1 = mount(FlowRouteInspector, {
      props: {
        route: routes[0],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '2',
      },
    })

    const vm1 = wrapper1.vm as any
    expect(vm1.priorityValue).toBe(1)

    // 编辑第二个路由
    const wrapper2 = mount(FlowRouteInspector, {
      props: {
        route: routes[1],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 1,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '3',
      },
    })

    const vm2 = wrapper2.vm as any
    expect(vm2.priorityValue).toBe(2)

    // 验证两个路由的优先级不同
    expect(vm1.priorityValue).not.toBe(vm2.priorityValue)
  })

  it('不同路由的默认状态应该保持独立', () => {
    // 编辑第一个路由
    const wrapper1 = mount(FlowRouteInspector, {
      props: {
        route: routes[0],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '2',
      },
    })

    const vm1 = wrapper1.vm as any
    expect(vm1.isDefaultValue).toBe(true)

    // 编辑第二个路由
    const wrapper2 = mount(FlowRouteInspector, {
      props: {
        route: routes[1],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 1,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '3',
      },
    })

    const vm2 = wrapper2.vm as any
    expect(vm2.isDefaultValue).toBe(false)

    // 验证两个路由的默认状态不同
    expect(vm1.isDefaultValue).not.toBe(vm2.isDefaultValue)
  })

  it('应该在优先级为 null 时显示默认值 1', () => {
    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: {
          ...routes[0],
          priority: undefined,
        },
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '2',
      },
    })

    const vm = wrapper.vm as any
    expect(vm.priorityValue).toBe(1)
  })

  it('应该在默认状态为 false 时正确显示', () => {
    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: routes[1],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 1,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '3',
      },
    })

    const vm = wrapper.vm as any
    expect(vm.isDefaultValue).toBe(false)
  })

  it('应该支持优先级范围 1-999', async () => {
    const updateRouteSpy = vi.fn()

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: routes[0],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '2',
        onUpdateRoute: updateRouteSpy,
      },
    })

    const vm = wrapper.vm as any

    // 测试最小值
    vm.emitPatch({ priority: 1 })
    expect(updateRouteSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        patch: expect.objectContaining({ priority: 1 })
      })
    )

    // 测试最大值
    vm.emitPatch({ priority: 999 })
    expect(updateRouteSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        patch: expect.objectContaining({ priority: 999 })
      })
    )
  })

  it('修改一个路由的属性不应该影响其他路由', async () => {
    const updateRouteSpy1 = vi.fn()
    const updateRouteSpy2 = vi.fn()

    // 编辑第一个路由
    const wrapper1 = mount(FlowRouteInspector, {
      props: {
        route: routes[0],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '2',
        onUpdateRoute: updateRouteSpy1,
      },
    })

    // 编辑第二个路由
    const wrapper2 = mount(FlowRouteInspector, {
      props: {
        route: routes[1],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 1,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '3',
        onUpdateRoute: updateRouteSpy2,
      },
    })

    const vm1 = wrapper1.vm as any
    const vm2 = wrapper2.vm as any

    // 修改第一个路由的优先级
    vm1.emitPatch({ priority: 10 })
    await wrapper1.vm.$nextTick()

    // 验证只有第一个路由的更新被发送
    expect(updateRouteSpy1).toHaveBeenCalledWith(
      expect.objectContaining({
        index: 0,
        patch: expect.objectContaining({ priority: 10 })
      })
    )

    // 验证第二个路由没有被更新
    expect(updateRouteSpy2).not.toHaveBeenCalled()

    // 验证第二个路由的优先级仍然是 2
    expect(vm2.priorityValue).toBe(2)
  })
})
