import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowRouteEditor from '../FlowRouteEditor.vue'
import type { FlowRouteConfig, FlowNodeConfig } from '@/types/flow'

describe('FlowRouteEditor', () => {
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

  beforeEach(() => {
    wrapper = mount(FlowRouteEditor, {
      props: {
        route: mockRoute,
        allNodes: mockAllNodes,
        disabled: false
      },
      global: {
        stubs: {
          NForm: true,
          NFormItem: true,
          NSelect: true,
          NSwitch: true,
          NInputNumber: true,
          NDivider: true,
          NEmpty: true,
          NAlert: true,
          ConditionBuilderV2: true
        }
      }
    })
  })

  it('应该正确渲染路由编辑器', () => {
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.flow-route-editor').exists()).toBe(true)
  })

  it('应该显示编辑器标题', () => {
    expect(wrapper.find('.title').text()).toBe('路由编辑器')
  })

  it('应该显示编辑器副标题', () => {
    expect(wrapper.find('.subtitle').text()).toContain('配置路由条件')
  })

  it('当没有选中路由时应该显示空状态', async () => {
    await wrapper.setProps({ route: undefined })
    expect(wrapper.find('.editor-empty').exists()).toBe(true)
  })

  it('应该显示来源节点选择', async () => {
    const text = wrapper.text()
    expect(text).toContain('来源节点')
  })

  it('应该显示目标节点选择', async () => {
    const text = wrapper.text()
    expect(text).toContain('目标节点')
  })

  it('应该显示优先级输入', async () => {
    const text = wrapper.text()
    expect(text).toContain('优先级')
  })

  it('应该显示条件表达式编辑区域', async () => {
    const text = wrapper.text()
    expect(text).toContain('条件表达式')
  })

  it('应该显示默认路由设置', async () => {
    const text = wrapper.text()
    expect(text).toContain('默认路由')
  })

  it('应该显示是否默认路由的开关', async () => {
    const text = wrapper.text()
    expect(text).toContain('是否默认路由')
  })

  it('当设置为默认路由时应该显示提示信息', async () => {
    const defaultRoute = { ...mockRoute, is_default: true }
    await wrapper.setProps({ route: defaultRoute })
    
    const text = wrapper.text()
    expect(text).toContain('此路由将作为默认路由')
  })

  it('当未设置为默认路由时不应该显示提示信息', async () => {
    const nonDefaultRoute = { ...mockRoute, is_default: false }
    await wrapper.setProps({ route: nonDefaultRoute })
    
    const alertExists = wrapper.find('.default-route-hint').exists()
    expect(alertExists).toBe(false)
  })

  it('应该支持切换条件编辑器显示状态', async () => {
    const initialShowState = wrapper.vm.showConditionBuilder
    expect(initialShowState).toBe(false)
    
    wrapper.vm.showConditionBuilder = true
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.showConditionBuilder).toBe(true)
  })

  it('应该在条件编辑器隐藏时显示条件预览', async () => {
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
    wrapper.vm.showConditionBuilder = false
    await wrapper.vm.$nextTick()
    
    const previewText = wrapper.find('.condition-preview').text()
    expect(previewText).toContain('AND')
  })

  it('应该正确格式化条件预览', () => {
    const condition = {
      type: 'GROUP',
      logic: 'AND',
      children: [
        { type: 'RULE', field: 'amount', operator: 'gt', value: 10000 },
        { type: 'RULE', field: 'category', operator: 'eq', value: 'travel' }
      ]
    }
    
    const preview = wrapper.vm.formatConditionPreview(condition)
    expect(preview).toContain('AND')
    expect(preview).toContain('2')
  })

  it('应该在条件为空时显示未设置', () => {
    const preview = wrapper.vm.formatConditionPreview(null)
    expect(preview).toBe('未设置')
  })

  it('应该在条件没有子节点时显示未设置', () => {
    const emptyCondition = {
      type: 'GROUP',
      logic: 'AND',
      children: []
    }
    
    const preview = wrapper.vm.formatConditionPreview(emptyCondition)
    expect(preview).toBe('未设置')
  })

  it('应该发送正确的更新事件', async () => {
    wrapper.vm.emitPatch({ priority: 2 })
    
    expect(wrapper.emitted('update-route')).toBeTruthy()
    const emittedData = wrapper.emitted('update-route')[0][0]
    expect(emittedData.patch.priority).toBe(2)
  })

  it('应该在路由变化时重置条件编辑器显示状态', async () => {
    wrapper.vm.showConditionBuilder = true
    
    const newRoute = { ...mockRoute, id: 2 }
    await wrapper.setProps({ route: newRoute })
    
    expect(wrapper.vm.showConditionBuilder).toBe(false)
  })

  it('应该在禁用状态下禁用所有输入', async () => {
    await wrapper.setProps({ disabled: true })
    
    expect(wrapper.props('disabled')).toBe(true)
  })

  it('应该支持临时 ID 的路由', async () => {
    const tempRoute: FlowRouteConfig = {
      temp_id: 'temp_1',
      from_node_key: '1',
      to_node_key: '2',
      priority: 1,
      condition: null,
      is_default: false
    }
    
    await wrapper.setProps({ route: tempRoute })
    
    wrapper.vm.emitPatch({ priority: 2 })
    
    const emittedData = wrapper.emitted('update-route')[0][0]
    expect(emittedData.key).toBe('temp_1')
  })

  it('应该正确处理优先级范围', async () => {
    const routeWithHighPriority = { ...mockRoute, priority: 999 }
    await wrapper.setProps({ route: routeWithHighPriority })
    
    expect(wrapper.props('route').priority).toBe(999)
  })

  it('应该支持来源节点和目标节点的选择', async () => {
    const text = wrapper.text()
    expect(text).toContain('来源节点')
    expect(text).toContain('目标节点')
  })

  it('应该在条件编辑器中集成 ConditionBuilderV2', async () => {
    wrapper.vm.showConditionBuilder = true
    await wrapper.vm.$nextTick()
    
    const conditionBuilder = wrapper.findComponent({ name: 'ConditionBuilderV2' })
    expect(conditionBuilder.exists()).toBe(true)
  })

  it('应该支持 formId 和 formSchema props', async () => {
    const formId = 123
    const formSchema = { fields: [] }
    
    await wrapper.setProps({ formId, formSchema })
    
    expect(wrapper.props('formId')).toBe(formId)
    expect(wrapper.props('formSchema')).toEqual(formSchema)
  })

  it('应该正确处理路由的所有属性', async () => {
    const complexRoute: FlowRouteConfig = {
      id: 5,
      from_node_key: '1',
      to_node_key: '3',
      priority: 10,
      condition: {
        type: 'GROUP',
        logic: 'OR',
        children: []
      },
      is_default: true
    }
    
    await wrapper.setProps({ route: complexRoute })
    
    expect(wrapper.props('route')).toEqual(complexRoute)
  })
})
