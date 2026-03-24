/**
 * FlowRouteInspector 条件编辑和清除测试
 * 
 * 验证条件编辑和清除逻辑是否正确工作
 * - 条件编辑后是否保存到正确的路由
 * - 条件清除是否只清除当前路由的条件
 * - 条件编辑弹窗中是否显示路由信息
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowRouteInspector from '../FlowRouteInspector.vue'
import type { FlowNodeConfig, FlowRouteConfig, JsonLogicExpression } from '@/types/flow'

describe('FlowRouteInspector - 条件编辑和清除测试', () => {
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

  it('应该在条件编辑弹窗中显示路由信息', async () => {
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

    // 点击编辑条件按钮
    const editButton = wrapper.find('button:contains("编辑条件")')
    if (editButton.exists()) {
      await editButton.trigger('click')
      await wrapper.vm.$nextTick()

      // 验证路由信息部分是否存在
      const routeInfoSection = wrapper.find('.route-info-section')
      expect(routeInfoSection.exists()).toBe(true)

      // 验证路由信息文本
      const routeInfoText = wrapper.find('.route-info-text')
      expect(routeInfoText.text()).toBe('从 开始节点 到 审批节点')
    }
  })

  it('应该正确保存条件到当前路由', async () => {
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

    // 模拟条件编辑
    const testCondition: JsonLogicExpression = {
      '==': [{ var: 'amount' }, 1000],
    }

    // 调用 handleConditionUpdate
    vm.handleConditionUpdate(testCondition)
    await wrapper.vm.$nextTick()

    // 验证 emitPatch 是否被调用
    expect(updateRouteSpy).toHaveBeenCalled()
    const callArgs = updateRouteSpy.mock.calls[0][0]
    expect(callArgs.patch.condition).toEqual(testCondition)
  })

  it('应该正确清除条件', async () => {
    const updateRouteSpy = vi.fn()

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: {
          ...routes[0],
          condition: { '==': [{ var: 'amount' }, 1000] },
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

    // 调用 handleConditionUpdate 清除条件
    vm.handleConditionUpdate(null)
    await wrapper.vm.$nextTick()

    // 验证 emitPatch 是否被调用，且条件为 null
    expect(updateRouteSpy).toHaveBeenCalled()
    const callArgs = updateRouteSpy.mock.calls[0][0]
    expect(callArgs.patch.condition).toBeNull()
  })

  it('应该在 JSON 编辑器中显示条件', async () => {
    const testCondition: JsonLogicExpression = {
      '==': [{ var: 'amount' }, 1000],
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: {
          ...routes[0],
          condition: testCondition,
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

    // 验证 conditionDraft 是否包含条件 JSON
    expect(vm.conditionDraft).toContain('"=="')
    expect(vm.conditionDraft).toContain('"var"')
    expect(vm.conditionDraft).toContain('"amount"')
  })

  it('应该在条件为 null 时显示"未设置条件"', async () => {
    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: {
          ...routes[0],
          condition: null,
        },
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '2',
      },
    })

    // 验证条件状态显示
    const conditionStatus = wrapper.find('.condition-status')
    expect(conditionStatus.text()).toBe('未设置条件')
  })

  it('应该在条件存在时显示"已设置条件"', async () => {
    const testCondition: JsonLogicExpression = {
      '==': [{ var: 'amount' }, 1000],
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: {
          ...routes[0],
          condition: testCondition,
        },
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: routes,
        currentNodeKey: '2',
      },
    })

    // 验证条件状态显示
    const conditionStatus = wrapper.find('.condition-status')
    expect(conditionStatus.text()).toBe('已设置条件')
  })

  it('应该在条件编辑弹窗中显示已有条件', async () => {
    const testCondition: JsonLogicExpression = {
      '==': [{ var: 'amount' }, 1000],
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: {
          ...routes[0],
          condition: testCondition,
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

    // 打开条件编辑弹窗
    vm.openConditionModal()
    await wrapper.vm.$nextTick()

    // 验证条件列表是否包含已有条件
    expect(vm.conditionsList).toHaveLength(1)
    expect(vm.conditionsList[0]).toEqual(testCondition)
  })

  it('应该支持多个条件的编辑', async () => {
    const multipleConditions: JsonLogicExpression = {
      and: [
        { '==': [{ var: 'amount' }, 1000] },
        { '>': [{ var: 'days' }, 5] },
      ],
    }

    const wrapper = mount(FlowRouteInspector, {
      props: {
        route: {
          ...routes[0],
          condition: multipleConditions,
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

    // 打开条件编辑弹窗
    vm.openConditionModal()
    await wrapper.vm.$nextTick()

    // 验证条件列表是否包含所有条件
    expect(vm.conditionsList).toHaveLength(2)
  })

  it('应该在不同路由之间保持条件独立', async () => {
    const condition1: JsonLogicExpression = {
      '==': [{ var: 'amount' }, 1000],
    }

    const condition2: JsonLogicExpression = {
      '>': [{ var: 'days' }, 5],
    }

    const routesWithConditions: FlowRouteConfig[] = [
      {
        ...routes[0],
        condition: condition1,
      },
      {
        ...routes[1],
        condition: condition2,
      },
    ]

    // 编辑第一个路由
    const wrapper1 = mount(FlowRouteInspector, {
      props: {
        route: routesWithConditions[0],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 0,
        disabled: false,
        nodes: nodes,
        routes: routesWithConditions,
        currentNodeKey: '2',
      },
    })

    const vm1 = wrapper1.vm as any
    expect(vm1.routeComputed.condition).toEqual(condition1)

    // 编辑第二个路由
    const wrapper2 = mount(FlowRouteInspector, {
      props: {
        route: routesWithConditions[1],
        nodeOptions: nodes.map(n => ({ label: n.name, value: String(n.id) })),
        selectedIndex: 1,
        disabled: false,
        nodes: nodes,
        routes: routesWithConditions,
        currentNodeKey: '3',
      },
    })

    const vm2 = wrapper2.vm as any
    expect(vm2.routeComputed.condition).toEqual(condition2)

    // 验证两个路由的条件不同
    expect(vm1.routeComputed.condition).not.toEqual(vm2.routeComputed.condition)
  })
})
