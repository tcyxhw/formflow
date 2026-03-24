/**
 * FlowRouteInspector 路由过滤测试
 * 
 * 验证路由过滤逻辑是否正确工作
 * - 只显示进入当前节点的路由（to_node_key = 当前节点）
 * - 路由描述信息是否正确显示
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowRouteInspector from '../FlowRouteInspector.vue'
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

describe('FlowRouteInspector - 路由过滤测试', () => {
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
        priority: 1,
        is_default: true,
        condition: null,
      },
    ]
  })

  it('应该正确过滤进入当前节点的路由', () => {
    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: routes[0],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '2', // 当前编辑节点 2
      },
    })

    // 获取 relevantRoutes 计算属性
    const vm = wrapper.vm as any
    const relevantRoutes = vm.relevantRoutes

    // 验证只有进入节点 2 的路由被返回
    expect(relevantRoutes).toHaveLength(1)
    expect(relevantRoutes[0].from_node_key).toBe('1')
    expect(relevantRoutes[0].to_node_key).toBe('2')
  })

  it('当编辑节点 3 时，应该只显示进入节点 3 的路由', () => {
    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: routes[1],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 1,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '3', // 当前编辑节点 3
      },
    })

    const vm = wrapper.vm as any
    const relevantRoutes = vm.relevantRoutes

    // 验证只有进入节点 3 的路由被返回
    expect(relevantRoutes).toHaveLength(1)
    expect(relevantRoutes[0].from_node_key).toBe('2')
    expect(relevantRoutes[0].to_node_key).toBe('3')
  })

  it('当没有进入当前节点的路由时，应该返回空数组', () => {
    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: undefined,
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: null,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '1', // 节点 1 是开始节点，没有进入的路由
      },
    })

    const vm = wrapper.vm as any
    const relevantRoutes = vm.relevantRoutes

    // 验证返回空数组
    expect(relevantRoutes).toHaveLength(0)
  })

  it('应该正确生成路由描述信息', () => {
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
    const description = vm.getRouteDescription(routes[0])

    // 验证描述信息格式
    expect(description).toBe('从 开始节点 到 审批节点')
  })

  it('当节点不存在时，应该显示"未知节点"', () => {
    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: {
          from_node_key: 'unknown-1',
          to_node_key: 'unknown-2',
          priority: 1,
          is_default: true,
          condition: null,
        },
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: 'unknown-2',
      },
    })

    const vm = wrapper.vm as any
    const description = vm.getRouteDescription({
      from_node_key: 'unknown-1',
      to_node_key: 'unknown-2',
      priority: 1,
      is_default: true,
      condition: null,
    })

    // 验证未知节点的处理
    expect(description).toBe('从 未知节点 到 未知节点')
  })

  it('应该在模板中显示路由信息横幅', () => {
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

    // 验证路由信息横幅是否存在
    const banner = wrapper.find('.route-info-banner')
    expect(banner.exists()).toBe(true)

    // 验证横幅中的描述信息
    const description = wrapper.find('.route-info-description')
    expect(description.text()).toBe('从 开始节点 到 审批节点')
  })

  it('当没有选择路由时，应该显示空状态', () => {
    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: undefined,
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: null,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '2',
      },
    })

    // 验证空状态提示
    const empty = wrapper.find('.inspector-empty')
    expect(empty.exists()).toBe(true)
  })

  it('应该支持多个进入同一节点的路由', () => {
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
})
