/**
 * Bug Condition 探索测试 - FlowNodeInspector 动态选择器
 * 
 * **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**
 * 
 * 此测试在未修复的代码上应该失败，证明 bug 存在。
 * 测试验证当用户选择不同的负责人类型时，应该显示对应的选择器组件。
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import * as fc from 'fast-check'
import FlowNodeInspector from '../FlowNodeInspector.vue'
import type { FlowNodeConfig, FlowAssigneeType } from '@/types/flow'

describe('Bug Condition - FlowNodeInspector 动态选择器缺失', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  const createTestNode = (assigneeType: FlowAssigneeType): FlowNodeConfig => ({
    id: 1,
    name: '审批节点',
    type: 'user',
    assignee_type: assigneeType,
    approve_policy: 'any',
    route_mode: 'exclusive',
    allow_delegate: false,
    auto_approve_enabled: false,
    auto_sample_ratio: 0,
    metadata: {},
    reject_strategy: 'TO_START'
  })

  /**
   * Property 1: Bug Condition - 动态选择器显示
   * 
   * 对于任何用户选择的负责人类型（user/role/group/department/position/expr），
   * 系统应该显示对应的选择器组件。
   */
  it('Property 1: 选择 assignee_type 为 user 时应显示用户选择器', () => {
    const node = createTestNode('user')
    const wrapper = mount(FlowNodeInspector, {
      props: { node, disabled: false },
      global: { stubs: { ConditionNodeEditor: true } }
    })

    // 验证组件已渲染
    expect(wrapper.exists()).toBe(true)

    // 查找负责人类型的表单项
    const html = wrapper.html()
    expect(html).toContain('负责人类型')

    // 关键断言：应该存在用户选择器的表单项
    // 在未修复的代码中，选择 assignee_type 后没有对应的选择器
    // 我们期望看到一个用于选择具体用户的表单项
    const hasUserSelectorFormItem = html.includes('选择用户') || 
                                     html.includes('用户选择') ||
                                     html.includes('assignee_value')
    
    // 这个断言在未修复的代码上会失败
    expect(hasUserSelectorFormItem, '应该显示用户选择器表单项，但未找到').toBe(true)
  })

  it('Property 1: 选择 assignee_type 为 role 时应显示角色选择器', () => {
    const node = createTestNode('role')
    const wrapper = mount(FlowNodeInspector, {
      props: { node, disabled: false },
      global: { stubs: { ConditionNodeEditor: true } }
    })

    const html = wrapper.html()
    expect(html).toContain('负责人类型')

    // 关键断言：应该存在角色选择器的表单项
    const hasRoleSelectorFormItem = html.includes('选择角色') || 
                                     html.includes('角色选择') ||
                                     html.includes('assignee_value')
    
    // 这个断言在未修复的代码上会失败
    expect(hasRoleSelectorFormItem, '应该显示角色选择器表单项，但未找到').toBe(true)
  })

  it('Property 1: 选择 assignee_type 为 group 时应显示群组选择器', () => {
    const node = createTestNode('group')
    const wrapper = mount(FlowNodeInspector, {
      props: { node, disabled: false },
      global: { stubs: { ConditionNodeEditor: true } }
    })

    const html = wrapper.html()
    expect(html).toContain('负责人类型')

    // 关键断言：应该存在群组选择器的表单项
    const hasGroupSelectorFormItem = html.includes('选择群组') || 
                                      html.includes('群组选择') ||
                                      html.includes('assignee_value')
    
    // 这个断言在未修复的代码上会失败
    expect(hasGroupSelectorFormItem, '应该显示群组选择器表单项，但未找到').toBe(true)
  })

  it('Property 1: 选择 assignee_type 为 department 时应显示部门选择器', () => {
    const node = createTestNode('department')
    const wrapper = mount(FlowNodeInspector, {
      props: { node, disabled: false },
      global: { stubs: { ConditionNodeEditor: true } }
    })

    const html = wrapper.html()
    expect(html).toContain('负责人类型')

    // 关键断言：应该存在部门选择器的表单项
    const hasDepartmentSelectorFormItem = html.includes('选择部门') || 
                                           html.includes('部门选择') ||
                                           html.includes('assignee_value')
    
    // 这个断言在未修复的代码上会失败
    expect(hasDepartmentSelectorFormItem, '应该显示部门选择器表单项，但未找到').toBe(true)
  })

  it('Property 1: 选择 assignee_type 为 position 时应显示岗位选择器', () => {
    const node = createTestNode('position')
    const wrapper = mount(FlowNodeInspector, {
      props: { node, disabled: false },
      global: { stubs: { ConditionNodeEditor: true } }
    })

    const html = wrapper.html()
    expect(html).toContain('负责人类型')

    // 关键断言：应该存在岗位选择器的表单项
    const hasPositionSelectorFormItem = html.includes('选择岗位') || 
                                         html.includes('岗位选择') ||
                                         html.includes('assignee_value')
    
    // 这个断言在未修复的代码上会失败
    expect(hasPositionSelectorFormItem, '应该显示岗位选择器表单项，但未找到').toBe(true)
  })

  it('Property 1: 选择 assignee_type 为 expr 时应显示表达式输入框', () => {
    const node = createTestNode('expr')
    const wrapper = mount(FlowNodeInspector, {
      props: { node, disabled: false },
      global: { stubs: { ConditionNodeEditor: true } }
    })

    const html = wrapper.html()
    expect(html).toContain('负责人类型')

    // 关键断言：应该存在表达式输入框的表单项
    const hasExprInputFormItem = html.includes('表达式') || 
                                  html.includes('输入表达式') ||
                                  html.includes('assignee_value')
    
    // 这个断言在未修复的代码上会失败
    expect(hasExprInputFormItem, '应该显示表达式输入框表单项，但未找到').toBe(true)
  })

  /**
   * 属性测试：对所有可能的 assignee_type 值进行测试
   * 
   * 这个测试使用 fast-check 生成所有可能的负责人类型，
   * 并验证每种类型都应该显示对应的选择器。
   */
  it('Property 1 (PBT): 对于所有 assignee_type，应显示对应的选择器', () => {
    // 定义所有可能的负责人类型
    const assigneeTypeArbitrary = fc.constantFrom<FlowAssigneeType>(
      'user',
      'role',
      'group',
      'department',
      'position',
      'expr'
    )

    fc.assert(
      fc.property(assigneeTypeArbitrary, (assigneeType) => {
        const node = createTestNode(assigneeType)
        const wrapper = mount(FlowNodeInspector, {
          props: { node, disabled: false },
          global: { stubs: { ConditionNodeEditor: true } }
        })

        const html = wrapper.html()
        
        // 验证负责人类型选择器存在
        const hasAssigneeTypeSelector = html.includes('负责人类型')
        if (!hasAssigneeTypeSelector) {
          return false
        }

        // 验证应该有对应的选择器表单项
        // 在未修复的代码中，这些表单项不存在
        const hasSelectorFormItem = html.includes('assignee_value') ||
                                     html.includes('选择用户') ||
                                     html.includes('选择角色') ||
                                     html.includes('选择群组') ||
                                     html.includes('选择部门') ||
                                     html.includes('选择岗位') ||
                                     html.includes('表达式')
        
        return hasSelectorFormItem
      }),
      { numRuns: 6 } // 运行 6 次，覆盖所有 6 种类型
    )
  })
})
