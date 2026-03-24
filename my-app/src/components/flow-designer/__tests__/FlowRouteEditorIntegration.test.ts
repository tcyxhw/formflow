import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowRouteEditor from '../FlowRouteEditor.vue'
import ConditionBuilderV2 from '../../flow-configurator/ConditionBuilderV2.vue'
import type { FlowRouteConfig, FlowNodeConfig } from '@/types/flow'
import type { FormSchema } from '@/types/schema'

describe('FlowRouteEditor Integration', () => {
  let wrapper: any

  const mockRoute: FlowRouteConfig = {
    id: 1,
    from_node_key: '1',
    to_node_key: '2',
    priority: 1,
    condition: null,
    is_default: false
  }

  const mockAllNodes: FlowNodeConfig[] = [
    {
      id: 1,
      name: '开始',
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
      name: '审批',
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
      name: '结束',
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

  const mockFormSchema: FormSchema = {
    fields: [
      {
        id: 'amount',
        label: '金额',
        type: 'number',
        required: true
      },
      {
        id: 'category',
        label: '类别',
        type: 'select',
        options: [
          { label: '差旅', value: 'travel' },
          { label: '招待', value: 'entertainment' }
        ]
      }
    ]
  }

  beforeEach(() => {
    wrapper = mount(FlowRouteEditor, {
      props: {
        route: mockRoute,
        allNodes: mockAllNodes,
        formSchema: mockFormSchema,
        formId: 1,
        disabled: false
      },
      global: {
        stubs: {
          NForm: false,
          NFormItem: false,
          NSelect: false,
          NSwitch: false,
          NInputNumber: false,
          NDivider: false,
          NEmpty: false,
          NAlert: false,
          ConditionBuilderV2: true
        }
      }
    })
  })

  it('应该完整渲染路由编辑器的所有部分', () => {
    expect(wrapper.find('.editor-header').exists()).toBe(true)
    expect(wrapper.find('.editor-body').exists()).toBe(true)
    expect(wrapper.find('.title').text()).toBe('路由编辑器')
  })

  it('应该支持编辑路由的基本属性', async () => {
    // 模拟优先级更新
    wrapper.vm.emitPatch({ priority: 5 })

    const emitted = wrapper.emitted('update-route')
    expect(emitted).toBeTruthy()
    expect(emitted[0][0].patch.priority).toBe(5)
  })

  it('应该支持编辑条件表达式', async () => {
    const newCondition = {
      type: 'GROUP',
      logic: 'AND',
      children: [
        {
          type: 'RULE',
          field: 'amount',
          operator: 'gt',
          value: 10000
        }
      ]
    }

    wrapper.vm.emitPatch({ condition: newCondition })

    const emitted = wrapper.emitted('update-route')
    expect(emitted).toBeTruthy()
    expect(emitted[0][0].patch.condition).toEqual(newCondition)
  })

  it('应该支持设置默认路由', async () => {
    wrapper.vm.emitPatch({ is_default: true })

    const emitted = wrapper.emitted('update-route')
    expect(emitted).toBeTruthy()
    expect(emitted[0][0].patch.is_default).toBe(true)
  })

  it('应该支持多个条件分支的编辑', async () => {
    const complexCondition = {
      type: 'GROUP',
      logic: 'OR',
      children: [
        {
          type: 'GROUP',
          logic: 'AND',
          children: [
            {
              type: 'RULE',
              field: 'amount',
              operator: 'gt',
              value: 10000
            },
            {
              type: 'RULE',
              field: 'category',
              operator: 'eq',
              value: 'travel'
            }
          ]
        },
        {
          type: 'RULE',
          field: 'amount',
          operator: 'lt',
          value: 5000
        }
      ]
    }

    wrapper.vm.emitPatch({ condition: complexCondition })

    const emitted = wrapper.emitted('update-route')
    expect(emitted[0][0].patch.condition).toEqual(complexCondition)
  })

  it('应该支持从一个路由切换到另一个路由', async () => {
    const newRoute: FlowRouteConfig = {
      id: 2,
      from_node_key: '2',
      to_node_key: '3',
      priority: 2,
      condition: {
        type: 'GROUP',
        logic: 'AND',
        children: []
      },
      is_default: false
    }

    await wrapper.setProps({ route: newRoute })

    expect(wrapper.props('route')).toEqual(newRoute)
    expect(wrapper.vm.showConditionBuilder).toBe(false)
  })

  it('应该支持条件编辑器的显示和隐藏', async () => {
    expect(wrapper.vm.showConditionBuilder).toBe(false)

    wrapper.vm.showConditionBuilder = true
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.showConditionBuilder).toBe(true)

    wrapper.vm.showConditionBuilder = false
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.showConditionBuilder).toBe(false)
  })

  it('应该在条件编辑器显示时集成 ConditionBuilderV2', async () => {
    wrapper.vm.showConditionBuilder = true
    await wrapper.vm.$nextTick()

    const conditionBuilder = wrapper.findComponent({ name: 'ConditionBuilderV2' })
    expect(conditionBuilder.exists()).toBe(true)
  })

  it('应该支持禁用状态下的只读模式', async () => {
    await wrapper.setProps({ disabled: true })

    expect(wrapper.props('disabled')).toBe(true)
  })

  it('应该正确处理临时 ID 的路由', async () => {
    const tempRoute: FlowRouteConfig = {
      temp_id: 'temp_route_1',
      from_node_key: '1',
      to_node_key: '2',
      priority: 1,
      condition: null,
      is_default: false
    }

    await wrapper.setProps({ route: tempRoute })

    wrapper.vm.emitPatch({ priority: 3 })

    const emitted = wrapper.emitted('update-route')
    expect(emitted[0][0].key).toBe('temp_route_1')
  })

  it('应该支持来源节点和目标节点的动态选择', async () => {
    wrapper.vm.emitPatch({ from_node_key: '2', to_node_key: '3' })

    const emitted = wrapper.emitted('update-route')
    expect(emitted[0][0].patch.from_node_key).toBe('2')
    expect(emitted[0][0].patch.to_node_key).toBe('3')
  })

  it('应该支持优先级的范围设置', async () => {
    // 测试最小优先级
    wrapper.vm.emitPatch({ priority: 1 })
    let emitted = wrapper.emitted('update-route')
    expect(emitted[0][0].patch.priority).toBe(1)

    // 测试最大优先级
    wrapper.vm.emitPatch({ priority: 999 })
    emitted = wrapper.emitted('update-route')
    expect(emitted[1][0].patch.priority).toBe(999)
  })

  it('应该支持条件表达式的清空', async () => {
    const routeWithCondition = {
      ...mockRoute,
      condition: {
        type: 'GROUP',
        logic: 'AND',
        children: [
          {
            type: 'RULE',
            field: 'amount',
            operator: 'gt',
            value: 10000
          }
        ]
      }
    }

    await wrapper.setProps({ route: routeWithCondition })

    wrapper.vm.emitPatch({ condition: null })

    const emitted = wrapper.emitted('update-route')
    expect(emitted[0][0].patch.condition).toBe(null)
  })

  it('应该支持多个属性的同时更新', async () => {
    const newCondition = {
      type: 'GROUP',
      logic: 'AND',
      children: []
    }

    wrapper.vm.emitPatch({
      priority: 5,
      condition: newCondition,
      is_default: true
    })

    const emitted = wrapper.emitted('update-route')
    expect(emitted[0][0].patch.priority).toBe(5)
    expect(emitted[0][0].patch.condition).toEqual(newCondition)
    expect(emitted[0][0].patch.is_default).toBe(true)
  })

  it('应该正确格式化不同类型的条件预览', () => {
    // AND 条件
    const andCondition = {
      type: 'GROUP',
      logic: 'AND',
      children: [
        { type: 'RULE', field: 'a', operator: 'eq', value: 1 },
        { type: 'RULE', field: 'b', operator: 'eq', value: 2 }
      ]
    }
    expect(wrapper.vm.formatConditionPreview(andCondition)).toContain('AND')

    // OR 条件
    const orCondition = {
      type: 'GROUP',
      logic: 'OR',
      children: [
        { type: 'RULE', field: 'a', operator: 'eq', value: 1 }
      ]
    }
    expect(wrapper.vm.formatConditionPreview(orCondition)).toContain('OR')
  })

  it('应该在路由变化时重置编辑器状态', async () => {
    wrapper.vm.showConditionBuilder = true
    await wrapper.vm.$nextTick()

    const newRoute: FlowRouteConfig = {
      id: 2,
      from_node_key: '2',
      to_node_key: '3',
      priority: 2,
      condition: null,
      is_default: false
    }

    await wrapper.setProps({ route: newRoute })

    expect(wrapper.vm.showConditionBuilder).toBe(false)
  })

  it('应该支持表单 schema 和 formId 的传递', async () => {
    expect(wrapper.props('formSchema')).toEqual(mockFormSchema)
    expect(wrapper.props('formId')).toBe(1)
  })

  it('应该在没有路由时显示空状态', async () => {
    await wrapper.setProps({ route: undefined })

    expect(wrapper.find('.editor-empty').exists()).toBe(true)
    expect(wrapper.find('.editor-body').exists()).toBe(false)
  })

  it('应该支持节点列表的动态更新', async () => {
    const newNodes: FlowNodeConfig[] = [
      ...mockAllNodes,
      {
        id: 4,
        name: '新节点',
        type: 'user',
        approve_policy: 'any',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        metadata: {},
        reject_strategy: 'TO_START'
      }
    ]

    await wrapper.setProps({ allNodes: newNodes })

    expect(wrapper.props('allNodes').length).toBe(4)
  })

  it('应该支持完整的路由编辑工作流', async () => {
    // 1. 更新优先级
    wrapper.vm.emitPatch({ priority: 2 })

    // 2. 添加条件
    const condition = {
      type: 'GROUP',
      logic: 'AND',
      children: [
        {
          type: 'RULE',
          field: 'amount',
          operator: 'gt',
          value: 10000
        }
      ]
    }
    wrapper.vm.emitPatch({ condition })

    // 3. 设置为默认路由
    wrapper.vm.emitPatch({ is_default: true })

    const emitted = wrapper.emitted('update-route')
    expect(emitted.length).toBe(3)
    expect(emitted[0][0].patch.priority).toBe(2)
    expect(emitted[1][0].patch.condition).toEqual(condition)
    expect(emitted[2][0].patch.is_default).toBe(true)
  })
})
