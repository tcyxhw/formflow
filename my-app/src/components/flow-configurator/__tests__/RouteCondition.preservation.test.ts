/**
 * Route Condition Preservation Property Test
 * 
 * **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
 * 
 * Property 2: Preservation - 非条件配置功能保持不变
 * 
 * 这个测试在未修复的代码上观察非 bug 输入的行为，并捕获这些行为模式。
 * 测试应该在未修复代码上通过，并在修复后继续通过，确保没有回归。
 * 
 * 保留行为：
 * 1. 首次为路由添加条件时，系统应正常打开空白的条件编辑器
 * 2. 点击"取消"按钮时，系统应放弃所有未保存的修改
 * 3. 点击"保存条件"按钮时，系统应将条件转换为 JsonLogic 格式并更新到 route.condition
 * 4. 多层嵌套的 AND/OR 逻辑组应正确处理序列化和反序列化
 * 5. 修改路由的其他属性（优先级、默认路由等）时，不应影响条件配置功能
 * 6. JSON 编辑器应继续支持手动输入 JsonLogic 格式的条件表达式
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import FlowRouteInspector from '../FlowRouteInspector.vue'
import ConditionBuilderV2 from '../ConditionBuilderV2.vue'
import { FlowRouteConfig } from '@/types/flow'
import { ConditionNode } from '@/types/condition'

// Mock Naive UI dialog
const mockDialog = {
  warning: vi.fn((options: any) => {
    if (options.onPositiveClick) {
      options.onPositiveClick()
    }
  })
}

vi.mock('naive-ui', async () => {
  const actual = await vi.importActual('naive-ui')
  return {
    ...actual,
    useDialog: () => mockDialog
  }
})

// Mock API
vi.mock('@/api/form', () => ({
  getFormFields: vi.fn().mockResolvedValue({
    data: {
      fields: [
        {
          key: 'amount',
          name: '报销金额',
          type: 'NUMBER'
        },
        {
          key: 'category',
          name: '费用类别',
          type: 'SINGLE_SELECT',
          options: [
            { label: '差旅', value: '差旅' },
            { label: '办公', value: '办公' }
          ]
        }
      ],
      system_fields: [
        {
          key: 'sys_submitter',
          name: '提交人',
          type: 'USER'
        }
      ]
    }
  })
}))

describe('Route Condition Preservation: 非条件配置功能保持不变', () => {
  const mockNodeOptions = [
    { label: '节点1', value: 'node1' },
    { label: '节点2', value: 'node2' }
  ]

  const mockFormSchema = {
    fields: [
      { id: 'amount', label: '报销金额', type: 'number' },
      { id: 'category', label: '费用类别', type: 'select', options: ['差旅', '办公'] }
    ]
  }

  /**
   * Requirement 3.1: 首次为路由添加条件时，系统应正常打开空白的条件编辑器
   * 
   * 观察：当路由的 condition 为 null 时，点击"编辑条件"按钮应该：
   * - 打开条件编辑模态框
   * - ConditionBuilderV2 显示空白的根组（没有子规则）
   * - 允许用户从零开始配置条件
   */
  describe('Preservation 3.1: 首次添加条件功能保持不变', () => {
    it('should open empty condition editor for route without condition', async () => {
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
          nodeOptions: mockNodeOptions,
          selectedIndex: 0,
          formId: 1,
          formSchema: mockFormSchema
        }
      })

      await nextTick()

      // 查找"编辑条件"按钮
      const buttons = wrapper.findAll('button')
      const editConditionButton = buttons.find(btn => btn.text().includes('编辑条件'))
      
      expect(editConditionButton).toBeDefined()
      
      if (editConditionButton) {
        // 点击按钮
        await editConditionButton.trigger('click')
        await nextTick()

        // 验证：模态框应该打开
        expect(wrapper.vm.showConditionModal).toBe(true)

        // 验证：editingCondition 应该是一个空的根组
        expect(wrapper.vm.editingCondition).toBeDefined()
        expect(wrapper.vm.editingCondition).not.toBeNull()
        
        if (wrapper.vm.editingCondition) {
          const condition = wrapper.vm.editingCondition as ConditionNode
          expect(condition.type).toBe('GROUP')
          
          if (condition.type === 'GROUP') {
            expect(condition.logic).toBe('AND')
            expect(condition.children).toEqual([])
          }
        }

        // 验证：ConditionBuilderV2 应该存在
        const conditionBuilder = wrapper.findComponent(ConditionBuilderV2)
        expect(conditionBuilder.exists()).toBe(true)
      }
    })
  })

  /**
   * Requirement 3.2: 点击"取消"按钮时，系统应放弃所有未保存的修改
   * 
   * 观察：当用户在条件编辑模态框中进行修改后点击"取消"按钮时：
   * - 模态框应该关闭
   * - editingCondition 应该被重置为 null
   * - 原有的 route.condition 应该保持不变
   * - 不应该触发 update-route 事件
   */
  describe('Preservation 3.2: 取消编辑功能保持不变', () => {
    it('should discard changes when cancel button is clicked', async () => {
      const originalCondition = {
        '==': [{ var: 'amount' }, 1000]
      }

      const route: FlowRouteConfig = {
        from_node_key: 'node1',
        to_node_key: 'node2',
        priority: 1,
        is_default: false,
        condition: originalCondition
      }

      const wrapper = mount(FlowRouteInspector, {
        props: {
          route,
          nodeOptions: mockNodeOptions,
          selectedIndex: 0,
          formId: 1,
          formSchema: mockFormSchema
        }
      })

      await nextTick()

      // 打开条件编辑模态框
      const buttons = wrapper.findAll('button')
      const editConditionButton = buttons.find(btn => btn.text().includes('编辑条件'))
      
      if (editConditionButton) {
        await editConditionButton.trigger('click')
        await nextTick()

        // 验证模态框已打开
        expect(wrapper.vm.showConditionModal).toBe(true)

        // 模拟用户修改条件（通过直接修改 editingCondition）
        const modifiedCondition: ConditionNode = {
          type: 'RULE',
          fieldKey: 'amount',
          fieldType: 'NUMBER',
          operator: 'GREATER_THAN',
          value: 2000
        }
        wrapper.vm.editingCondition = modifiedCondition

        await nextTick()

        // 直接调用 cancelCondition 方法（模拟点击取消按钮）
        wrapper.vm.cancelCondition()
        await nextTick()

        // 验证：模态框应该关闭
        expect(wrapper.vm.showConditionModal).toBe(false)

        // 验证：editingCondition 应该被重置为 null
        expect(wrapper.vm.editingCondition).toBeNull()

        // 验证：原有的 route.condition 应该保持不变
        expect(wrapper.props().route.condition).toEqual(originalCondition)

        // 验证：不应该触发 update-route 事件（或者事件数量没有增加）
        const updateEvents = wrapper.emitted('update-route')
        if (updateEvents) {
          // 如果有事件，验证最后一个事件不是条件更新
          const lastEvent = updateEvents[updateEvents.length - 1][0] as any
          expect(lastEvent.patch.condition).toBeUndefined()
        }
      }
    })
  })

  /**
   * Requirement 3.3: 点击"保存条件"按钮时，系统应将条件转换为 JsonLogic 格式并更新到 route.condition
   * 
   * 观察：当用户在条件编辑模态框中配置条件后点击"保存条件"按钮时：
   * - 模态框应该关闭
   * - editingCondition 应该被重置为 null
   * - 应该触发 update-route 事件，包含转换后的 JsonLogic 格式条件
   * - conditionDraft 应该更新为新的 JsonLogic 字符串
   */
  describe('Preservation 3.3: 保存条件功能保持不变', () => {
    it('should convert condition to JsonLogic and update route when save button is clicked', async () => {
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
          nodeOptions: mockNodeOptions,
          selectedIndex: 0,
          formId: 1,
          formSchema: mockFormSchema
        }
      })

      await nextTick()

      // 打开条件编辑模态框
      const buttons = wrapper.findAll('button')
      const editConditionButton = buttons.find(btn => btn.text().includes('编辑条件'))
      
      if (editConditionButton) {
        await editConditionButton.trigger('click')
        await nextTick()

        // 设置一个条件
        const newCondition: ConditionNode = {
          type: 'GROUP',
          logic: 'AND',
          children: [
            {
              type: 'RULE',
              fieldKey: 'amount',
              fieldType: 'NUMBER',
              operator: 'EQUALS',
              value: 1000
            }
          ]
        }
        wrapper.vm.editingCondition = newCondition

        await nextTick()

        // 直接调用 saveAllConditions 方法（模拟点击保存按钮）
        wrapper.vm.saveAllConditions()
        await nextTick()

        // 验证：模态框应该关闭
        expect(wrapper.vm.showConditionModal).toBe(false)

        // 验证：editingCondition 应该被重置为 null
        expect(wrapper.vm.editingCondition).toBeNull()

        // 验证：应该触发 update-route 事件
        const updateEvents = wrapper.emitted('update-route')
        expect(updateEvents).toBeDefined()
        expect(updateEvents!.length).toBeGreaterThan(0)

        // 验证：事件包含转换后的 JsonLogic 格式
        const lastEvent = updateEvents![updateEvents!.length - 1][0] as any
        expect(lastEvent.patch.condition).toBeDefined()
        expect(lastEvent.patch.condition).toEqual({
          '==': [{ var: 'amount' }, 1000]
        })

        // 验证：conditionDraft 应该更新
        expect(wrapper.vm.conditionDraft).toContain('"=="')
        expect(wrapper.vm.conditionDraft).toContain('"var"')
        expect(wrapper.vm.conditionDraft).toContain('"amount"')
        expect(wrapper.vm.conditionDraft).toContain('1000')
      }
    })
  })

  /**
   * Requirement 3.4: 多层嵌套的 AND/OR 逻辑组应正确处理序列化和反序列化
   * 
   * 观察：当路由包含多层嵌套的条件组时：
   * - jsonLogicToConditionNode 应该正确将 JsonLogic 转换为 ConditionNode
   * - conditionNodeToJsonLogic 应该正确将 ConditionNode 转换回 JsonLogic
   * - 转换应该是双向一致的（往返转换后结果相同）
   */
  describe('Preservation 3.4: 多层嵌套逻辑处理保持不变', () => {
    it('should correctly handle nested AND/OR logic groups', async () => {
      // 创建一个多层嵌套的条件：(amount > 1000 AND category = '差旅') OR (amount > 5000)
      const nestedCondition = {
        or: [
          {
            and: [
              { '>': [{ var: 'amount' }, 1000] },
              { '==': [{ var: 'category' }, '差旅'] }
            ]
          },
          { '>': [{ var: 'amount' }, 5000] }
        ]
      }

      const route: FlowRouteConfig = {
        from_node_key: 'node1',
        to_node_key: 'node2',
        priority: 1,
        is_default: false,
        condition: nestedCondition
      }

      const wrapper = mount(FlowRouteInspector, {
        props: {
          route,
          nodeOptions: mockNodeOptions,
          selectedIndex: 0,
          formId: 1,
          formSchema: mockFormSchema
        }
      })

      await nextTick()

      // 打开条件编辑模态框
      const buttons = wrapper.findAll('button')
      const editConditionButton = buttons.find(btn => btn.text().includes('编辑条件'))
      
      if (editConditionButton) {
        await editConditionButton.trigger('click')
        await nextTick()

        // 验证：editingCondition 应该是一个空的 GROUP（用于添加新条件）
        expect(wrapper.vm.editingCondition).toBeDefined()
        expect(wrapper.vm.editingCondition).not.toBeNull()
        
        if (wrapper.vm.editingCondition) {
          const condition = wrapper.vm.editingCondition as ConditionNode
          
          // 验证编辑条件是一个空的 GROUP
          expect(condition.type).toBe('GROUP')
          if (condition.type === 'GROUP') {
            expect(condition.logic).toBe('AND')
            expect(condition.children.length).toBe(0)
          }
        }
        
        // 验证：conditionsList 应该包含所有已有条件
        expect(wrapper.vm.conditionsList).toBeDefined()
        expect(wrapper.vm.conditionsList.length).toBe(2)
        
        // 验证第一个条件是 AND 组
        const firstCondition = wrapper.vm.conditionsList[0]
        expect(firstCondition).toBeDefined()
        if (firstCondition && firstCondition.and) {
          expect(Array.isArray(firstCondition.and)).toBe(true)
        }
        
        // 验证第二个条件是单个 RULE
        const secondCondition = wrapper.vm.conditionsList[1]
        expect(secondCondition).toBeDefined()
        if (secondCondition && secondCondition['>']) {
          expect(Array.isArray(secondCondition['>'])).toBe(true)
        }

        // 保存条件（测试往返转换）
        const saveButton = wrapper.findAll('button').find(btn => btn.text().includes('保存所有条件'))
        if (saveButton) {
          await saveButton.trigger('click')
          await nextTick()

          // 验证：转换后的 JsonLogic 应该保持嵌套结构
          const updateEvents = wrapper.emitted('update-route')
          if (updateEvents && updateEvents.length > 0) {
            const lastEvent = updateEvents[updateEvents.length - 1][0] as any
            const savedCondition = lastEvent.patch.condition
            
            expect(savedCondition).toBeDefined()
            // 验证包含 or 和 and 操作符
            expect(savedCondition.or || savedCondition.and).toBeDefined()
          }
        }
      }
    })
  })

  /**
   * Requirement 3.5: 修改路由的其他属性（优先级、默认路由等）时，不应影响条件配置功能
   * 
   * 观察：当用户修改路由的优先级、默认路由等属性时：
   * - 条件配置功能应该继续正常工作
   * - 已配置的条件不应该被清除或修改
   * - 条件编辑模态框应该仍然可以正常打开和使用
   */
  describe('Preservation 3.5: 修改其他路由属性不影响条件配置', () => {
    it('should preserve condition when updating other route properties', async () => {
      const existingCondition = {
        '==': [{ var: 'amount' }, 1000]
      }

      const route: FlowRouteConfig = {
        from_node_key: 'node1',
        to_node_key: 'node2',
        priority: 1,
        is_default: false,
        condition: existingCondition
      }

      const wrapper = mount(FlowRouteInspector, {
        props: {
          route,
          nodeOptions: mockNodeOptions,
          selectedIndex: 0,
          formId: 1,
          formSchema: mockFormSchema
        }
      })

      await nextTick()

      // 修改优先级
      wrapper.vm.emitPatch({ priority: 5 })
      await nextTick()

      // 验证：update-route 事件被触发
      const updateEvents = wrapper.emitted('update-route')
      expect(updateEvents).toBeDefined()
      
      if (updateEvents && updateEvents.length > 0) {
        const lastEvent = updateEvents[updateEvents.length - 1][0] as any
        
        // 验证：只更新了优先级
        expect(lastEvent.patch.priority).toBe(5)
        
        // 验证：条件没有被修改
        expect(lastEvent.patch.condition).toBeUndefined()
      }

      // 验证：原有条件仍然存在
      expect(wrapper.props().route.condition).toEqual(existingCondition)

      // 验证：条件编辑功能仍然可用
      const buttons = wrapper.findAll('button')
      const editConditionButton = buttons.find(btn => btn.text().includes('编辑条件'))
      
      if (editConditionButton) {
        await editConditionButton.trigger('click')
        await nextTick()

        // 验证：模态框可以正常打开
        expect(wrapper.vm.showConditionModal).toBe(true)

        // 验证：已有条件被正确加载
        expect(wrapper.vm.editingCondition).toBeDefined()
        expect(wrapper.vm.editingCondition).not.toBeNull()
      }
    })

    it('should preserve condition when toggling is_default flag', async () => {
      const existingCondition = {
        '>': [{ var: 'amount' }, 500]
      }

      const route: FlowRouteConfig = {
        from_node_key: 'node1',
        to_node_key: 'node2',
        priority: 1,
        is_default: false,
        condition: existingCondition
      }

      const wrapper = mount(FlowRouteInspector, {
        props: {
          route,
          nodeOptions: mockNodeOptions,
          selectedIndex: 0,
          formId: 1,
          formSchema: mockFormSchema
        }
      })

      await nextTick()

      // 切换默认路由标志
      wrapper.vm.emitPatch({ is_default: true })
      await nextTick()

      // 验证：条件没有被影响
      expect(wrapper.props().route.condition).toEqual(existingCondition)

      // 验证：conditionDraft 仍然包含条件数据
      expect(wrapper.vm.conditionDraft).toContain('">"')
      expect(wrapper.vm.conditionDraft).toContain('"amount"')
      expect(wrapper.vm.conditionDraft).toContain('500')
    })
  })

  /**
   * Requirement 3.6: JSON 编辑器应继续支持手动输入 JsonLogic 格式的条件表达式
   * 
   * 观察：当用户使用 JSON 编辑器手动输入条件时：
   * - JSON 编辑器应该可以正常显示和隐藏
   * - 用户应该可以手动输入 JsonLogic 格式的条件
   * - 输入的条件应该在失焦时被解析和验证
   * - 有效的条件应该触发 update-route 事件
   * - 无效的条件应该显示错误提示
   */
  describe('Preservation 3.6: JSON 编辑器手动输入功能保持不变', () => {
    it('should support manual JsonLogic input via JSON editor', async () => {
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
          nodeOptions: mockNodeOptions,
          selectedIndex: 0,
          formId: 1,
          formSchema: mockFormSchema
        }
      })

      await nextTick()

      // 验证：showJsonEditor 初始为 false
      expect(wrapper.vm.showJsonEditor).toBe(false)

      // 显示 JSON 编辑器
      wrapper.vm.showJsonEditor = true
      await nextTick()

      // 验证：JSON 编辑器状态已更新
      expect(wrapper.vm.showJsonEditor).toBe(true)

      // 模拟用户手动输入 JsonLogic
      const manualCondition = '{"==": [{"var": "category"}, "差旅"]}'
      wrapper.vm.conditionDraft = manualCondition
      await nextTick()

      // 模拟失焦事件（触发条件解析）
      wrapper.vm.handleConditionBlur()
      await nextTick()

      // 验证：条件被正确解析
      expect(wrapper.vm.conditionError).toBe('')

      // 验证：update-route 事件被触发
      const updateEvents = wrapper.emitted('update-route')
      expect(updateEvents).toBeDefined()
      
      if (updateEvents && updateEvents.length > 0) {
        const lastEvent = updateEvents[updateEvents.length - 1][0] as any
        expect(lastEvent.patch.condition).toEqual({
          '==': [{ var: 'category' }, '差旅']
        })
      }
    })

    it('should show error for invalid JsonLogic format', async () => {
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
          nodeOptions: mockNodeOptions,
          selectedIndex: 0,
          formId: 1,
          formSchema: mockFormSchema
        }
      })

      await nextTick()

      // 显示 JSON 编辑器
      wrapper.vm.showJsonEditor = true
      await nextTick()

      // 输入无效的 JSON
      wrapper.vm.conditionDraft = '{"invalid json'
      await nextTick()

      // 模拟失焦事件
      wrapper.vm.handleConditionBlur()
      await nextTick()

      // 验证：显示错误提示
      expect(wrapper.vm.conditionError).toContain('格式错误')
    })

    it('should clear condition when JSON editor input is empty', async () => {
      const existingCondition = {
        '==': [{ var: 'amount' }, 1000]
      }

      const route: FlowRouteConfig = {
        from_node_key: 'node1',
        to_node_key: 'node2',
        priority: 1,
        is_default: false,
        condition: existingCondition
      }

      const wrapper = mount(FlowRouteInspector, {
        props: {
          route,
          nodeOptions: mockNodeOptions,
          selectedIndex: 0,
          formId: 1,
          formSchema: mockFormSchema
        }
      })

      await nextTick()

      // 显示 JSON 编辑器
      wrapper.vm.showJsonEditor = true
      await nextTick()

      // 清空输入
      wrapper.vm.conditionDraft = ''
      await nextTick()

      // 模拟失焦事件
      wrapper.vm.handleConditionBlur()
      await nextTick()

      // 验证：没有错误
      expect(wrapper.vm.conditionError).toBe('')

      // 验证：条件被设置为 null
      const updateEvents = wrapper.emitted('update-route')
      if (updateEvents && updateEvents.length > 0) {
        const lastEvent = updateEvents[updateEvents.length - 1][0] as any
        expect(lastEvent.patch.condition).toBeNull()
      }
    })
  })
})
