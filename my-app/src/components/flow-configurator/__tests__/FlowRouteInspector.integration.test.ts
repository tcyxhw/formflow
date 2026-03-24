/**
 * FlowRouteInspector 集成测试
 * 
 * 验证路由过滤、条件编辑、属性绑定等功能的集成工作
 * - 在不同节点编辑条件是否相互独立
 * - 路由属性是否正确关联到具体的路由
 * - 保存和加载流程是否正确
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowRouteInspector from '../FlowRouteInspector.vue'
import type { FlowNodeConfig, FlowRouteConfig, JsonLogicExpression } from '@/types/flow'

describe('FlowRouteInspector - 集成测试', () => {
  let nodes: FlowNodeConfig[]
  let routes: FlowRouteConfig[]

  beforeEach(() => {
    // 创建测试节点：开始 → 审批 → 结束
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
        priority: 1,
        is_default: true,
        condition: null,
      },
    ]
  })

  it('场景 1：多节点条件独立性 - 在不同节点添加不同的条件', async () => {
    const condition1: JsonLogicExpression = {
      '==': [{ var: 'amount' }, 1000],
    }

    const condition2: JsonLogicExpression = {
      '>': [{ var: 'days' }, 5],
    }

    const updateRouteSpy1 = vi.fn()
    const updateRouteSpy2 = vi.fn()

    // 编辑节点 2 的进入路由（开始→审批）
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

    const vm1 = wrapper1.vm as any

    // 添加条件 1
    vm1.handleConditionUpdate(condition1)
    await wrapper1.vm.$nextTick()

    // 验证条件 1 被保存
    expect(updateRouteSpy1).toHaveBeenCalledWith(
      expect.objectContaining({
        index: 0,
        patch: expect.objectContaining({ condition: condition1 })
      })
    )

    // 编辑节点 3 的进入路由（审批→结束）
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

    const vm2 = wrapper2.vm as any

    // 添加条件 2
    vm2.handleConditionUpdate(condition2)
    await wrapper2.vm.$nextTick()

    // 验证条件 2 被保存
    expect(updateRouteSpy2).toHaveBeenCalledWith(
      expect.objectContaining({
        index: 1,
        patch: expect.objectContaining({ condition: condition2 })
      })
    )

    // 验证两个条件不同
    expect(condition1).not.toEqual(condition2)
  })

  it('场景 2：路由属性独立性 - 修改不同路由的优先级', async () => {
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

    const vm1 = wrapper1.vm as any

    // 修改第一个路由的优先级
    vm1.emitPatch({ priority: 10 })
    await wrapper1.vm.$nextTick()

    // 验证第一个路由的优先级被更新
    expect(updateRouteSpy1).toHaveBeenCalledWith(
      expect.objectContaining({
        index: 0,
        patch: expect.objectContaining({ priority: 10 })
      })
    )

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

    const vm2 = wrapper2.vm as any

    // 修改第二个路由的优先级
    vm2.emitPatch({ priority: 20 })
    await wrapper2.vm.$nextTick()

    // 验证第二个路由的优先级被更新
    expect(updateRouteSpy2).toHaveBeenCalledWith(
      expect.objectContaining({
        index: 1,
        patch: expect.objectContaining({ priority: 20 })
      })
    )

    // 验证两个路由的优先级不同
    expect(vm1.priorityValue).not.toBe(vm2.priorityValue)
  })

  it('场景 3：路由过滤正确性 - 编辑节点时只显示进入该节点的路由', () => {
    // 编辑节点 2 时
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
    const relevantRoutes1 = vm1.relevantRoutes

    // 验证只有进入节点 2 的路由
    expect(relevantRoutes1).toHaveLength(1)
    expect(relevantRoutes1[0].from_node_key).toBe('1')
    expect(relevantRoutes1[0].to_node_key).toBe('2')

    // 编辑节点 3 时
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
    const relevantRoutes2 = vm2.relevantRoutes

    // 验证只有进入节点 3 的路由
    expect(relevantRoutes2).toHaveLength(1)
    expect(relevantRoutes2[0].from_node_key).toBe('2')
    expect(relevantRoutes2[0].to_node_key).toBe('3')
  })

  it('场景 4：条件和属性的组合修改', async () => {
    const condition: JsonLogicExpression = {
      '==': [{ var: 'amount' }, 1000],
    }

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

    // 同时修改条件和优先级
    vm.handleConditionUpdate(condition)
    await wrapper.vm.$nextTick()

    vm.emitPatch({ priority: 5 })
    await wrapper.vm.$nextTick()

    // 验证两个更新都被发送
    expect(updateRouteSpy).toHaveBeenCalledTimes(2)

    // 验证第一个更新是条件
    expect(updateRouteSpy.mock.calls[0][0]).toEqual(
      expect.objectContaining({
        index: 0,
        patch: expect.objectContaining({ condition })
      })
    )

    // 验证第二个更新是优先级
    expect(updateRouteSpy.mock.calls[1][0]).toEqual(
      expect.objectContaining({
        index: 0,
        patch: expect.objectContaining({ priority: 5 })
      })
    )
  })

  it('场景 5：路由信息显示正确性', () => {
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

    // 验证路由描述
    const description = vm.getRouteDescription(routes[0])
    expect(description).toBe('从 开始节点 到 审批节点')

    // 验证路由信息横幅显示
    const banner = wrapper.find('.route-info-banner')
    expect(banner.exists()).toBe(true)
    expect(banner.text()).toContain('从 开始节点 到 审批节点')
  })

  it('场景 6：多个进入同一节点的路由处理', () => {
    // 添加另一个进入节点 2 的路由
    const additionalRoute: FlowRouteConfig = {
      from_node_key: '3',
      to_node_key: '2',
      priority: 2,
      is_default: false,
      condition: null,
    }

    const allRoutes = [...routes, additionalRoute]

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: routes[0],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: allRoutes,
        currentNodeKey: '2',
      },
    })

    const vm = wrapper.vm as any
    const relevantRoutes = vm.relevantRoutes

    // 验证返回所有进入节点 2 的路由
    expect(relevantRoutes).toHaveLength(2)
    expect(relevantRoutes.some((r: FlowRouteConfig) => r.from_node_key === '1')).toBe(true)
    expect(relevantRoutes.some((r: FlowRouteConfig) => r.from_node_key === '3')).toBe(true)
  })

  it('场景 7：条件清除功能', async () => {
    const condition: JsonLogicExpression = {
      '==': [{ var: 'amount' }, 1000],
    }

    const updateRouteSpy = vi.fn()

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: {
          ...routes[0],
          condition: condition,
        },
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

    // 验证条件存在
    expect(vm.routeComputed.condition).toEqual(condition)

    // 清除条件
    vm.handleConditionUpdate(null)
    await wrapper.vm.$nextTick()

    // 验证条件被清除
    expect(updateRouteSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        index: 0,
        patch: expect.objectContaining({ condition: null })
      })
    )
  })

  it('场景 8：条件编辑弹窗中的路由信息显示', async () => {
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

    // 打开条件编辑弹窗
    vm.openConditionModal()
    await wrapper.vm.$nextTick()

    // 验证路由信息部分存在
    const routeInfoSection = wrapper.find('.route-info-section')
    expect(routeInfoSection.exists()).toBe(true)

    // 验证路由信息文本
    const routeInfoText = wrapper.find('.route-info-text')
    expect(routeInfoText.text()).toBe('从 开始节点 到 审批节点')
  })
})
