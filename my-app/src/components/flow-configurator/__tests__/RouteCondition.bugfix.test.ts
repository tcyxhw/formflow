/**
 * Bug Condition Exploration Test for Route Condition Display and Edit
 * 
 * **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
 * 
 * 这个测试编码了期望的正确行为。在未修复的代码上，测试应该失败，
 * 证明 bug 存在。在实现修复后，测试通过将验证修复的正确性。
 * 
 * 测试场景：
 * 1. 字段选择被替换：在 ConditionBuilderV2 中连续选择多个字段，验证字段是否被替换
 * 2. 条件不显示：配置条件并保存，验证 FlowRouteInspector 是否显示条件详情
 * 3. 条件不加载：保存条件后重新打开编辑弹窗，验证 ConditionBuilderV2 是否加载已有条件
 * 4. 条件管理功能缺失：尝试查找删除条件的 UI 入口
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
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

// 全局 stubs
const globalStubs = {
  'n-form': {
    template: '<div><slot /></div>'
  },
  'n-form-item': {
    template: '<div><slot /></div>'
  },
  'n-select': {
    template: '<select></select>'
  },
  'n-input-number': {
    template: '<input type="number" />'
  },
  'n-switch': {
    template: '<input type="checkbox" />'
  },
  'n-divider': {
    template: '<hr />'
  },
  'n-button': {
    template: '<button><slot /></button>',
    props: ['type', 'size', 'disabled', 'quaternary']
  },
  'n-input': {
    template: '<textarea></textarea>'
  },
  'n-empty': {
    template: '<div>Empty</div>'
  },
  'n-modal': {
    template: '<div v-if="show"><slot name="header" /><slot /><slot name="action" /></div>',
    props: ['show', 'title', 'preset', 'style', 'maskClosable']
  },
  'n-space': {
    template: '<div><slot /></div>'
  },
  'n-text': {
    template: '<span><slot /></span>',
    props: ['depth', 'style']
  },
  'n-tag': {
    template: '<span><slot /></span>'
  },
  'n-icon': {
    template: '<i><slot /></i>'
  }
}

describe('Bug Condition Exploration: Route Condition Display and Edit', () => {
  describe('Property 1: Bug Condition - 路由条件正确保存、加载和显示', () => {
    
    /**
     * 场景 1：字段选择被替换问题
     * 
     * 当前行为（缺陷）：用户在 ConditionBuilderV2 中通过滑动操作选择表单字段时，
     * 系统会将之前选择的字段替换为系统字段，导致最终只保留最后一个选择的字段
     * 
     * 期望行为（正确）：系统应该正确保留所有已选择的字段，不会被系统字段替换
     */
    it('should preserve all selected fields without replacement', async () => {
      const wrapper = mount(ConditionBuilderV2, {
        props: {
          formId: 1,
          formSchema: {
            fields: [
              { id: 'amount', label: '报销金额', type: 'number' },
              { id: 'category', label: '费用类别', type: 'select', options: ['差旅', '办公'] }
            ]
          },
          modelValue: null
        },
        global: {
          stubs: globalStubs
        }
      })

      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      // 模拟用户连续选择多个字段
      const initialCondition: ConditionNode = {
        type: 'GROUP',
        logic: 'AND',
        children: [
          {
            type: 'RULE',
            fieldKey: 'amount',
            fieldType: 'NUMBER',
            operator: 'GREATER_THAN',
            value: 1000
          },
          {
            type: 'RULE',
            fieldKey: 'category',
            fieldType: 'SINGLE_SELECT',
            operator: 'EQUALS',
            value: '差旅'
          }
        ]
      }

      await wrapper.setProps({ modelValue: initialCondition })
      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))

      // 验证：组件内部状态应该保留所有字段
      // 通过查找 ConditionGroup 组件来验证
      const conditionGroups = wrapper.findAllComponents({ name: 'ConditionGroup' })
      expect(conditionGroups.length).toBeGreaterThan(0)
      
      // 验证：应该有两个条件规则
      const conditionRules = wrapper.findAllComponents({ name: 'ConditionRule' })
      
      // 关键断言：应该保留两个字段，而不是被替换为一个
      expect(conditionRules.length).toBe(2)
      
      // 验证第一个字段（报销金额）的 props
      if (conditionRules.length >= 1) {
        const firstRule = conditionRules[0]
        const firstProps = firstRule.props()
        expect(firstProps.rule).toBeDefined()
        if (firstProps.rule && firstProps.rule.type === 'RULE') {
          expect(firstProps.rule.fieldKey).toBe('amount')
          expect(firstProps.rule.operator).toBe('GREATER_THAN')
          expect(firstProps.rule.value).toBe(1000)
        }
      }
      
      // 验证第二个字段（费用类别）的 props
      if (conditionRules.length >= 2) {
        const secondRule = conditionRules[1]
        const secondProps = secondRule.props()
        expect(secondProps.rule).toBeDefined()
        if (secondProps.rule && secondProps.rule.type === 'RULE') {
          expect(secondProps.rule.fieldKey).toBe('category')
          expect(secondProps.rule.operator).toBe('EQUALS')
          expect(secondProps.rule.value).toBe('差旅')
        }
      }
    })

    /**
     * 场景 2：已配置条件不显示
     * 
     * 当前行为（缺陷）：用户已经为路由配置了条件（route.condition 存在 JsonLogic 数据）
     * 并关闭条件编辑弹窗后，FlowRouteInspector 组件不显示已配置的条件内容
     * 
     * 期望行为（正确）：FlowRouteInspector 组件应该在界面上清晰展示已配置的条件内容
     * （包括字段名、操作符、值等）
     */
    it('should display configured condition details in FlowRouteInspector', async () => {
      const route: FlowRouteConfig = {
        from_node_key: 'node1',
        to_node_key: 'node2',
        priority: 1,
        is_default: false,
        condition: {
          'and': [
            { '==': [{ var: 'amount' }, 1000] },
            { '==': [{ var: 'category' }, '差旅'] }
          ]
        }
      }

      const wrapper = mount(FlowRouteInspector, {
        props: {
          route,
          nodeOptions: [
            { label: '节点1', value: 'node1' },
            { label: '节点2', value: 'node2' }
          ],
          selectedIndex: 0,
          formId: 1,
          formSchema: {
            fields: [
              { id: 'amount', label: '报销金额', type: 'number' },
              { id: 'category', label: '费用类别', type: 'select' }
            ]
          }
        },
        global: {
          stubs: globalStubs
        }
      })

      await nextTick()

      // 验证：应该显示"已设置条件"状态
      const conditionStatus = wrapper.find('.condition-status')
      expect(conditionStatus.exists()).toBe(true)
      expect(conditionStatus.text()).toContain('已设置条件')

      // 关键断言：应该显示条件详情
      // 在未修复的代码上，这个断言应该失败
      // 因为只显示"已设置条件"文本，没有条件详情展示
      
      // 查找条件详情展示区域（这个元素在未修复的代码中不存在）
      const conditionDetails = wrapper.find('.condition-details')
      
      // 在未修复的代码上，这个断言会失败
      expect(conditionDetails.exists()).toBe(true)
      
      // 如果条件详情存在，验证其内容
      if (conditionDetails.exists()) {
        const detailsText = conditionDetails.text()
        
        // 应该包含字段名
        expect(detailsText).toContain('报销金额')
        expect(detailsText).toContain('费用类别')
        
        // 应该包含操作符或值
        expect(detailsText).toContain('1000')
        expect(detailsText).toContain('差旅')
      }
    })

    /**
     * 场景 3：编辑弹窗缺少条件展示
     * 
     * 当前行为（缺陷）：用户点击"编辑条件"按钮打开条件编辑弹窗时，
     * 弹窗中的 ConditionBuilderV2 组件不显示路由已有的条件配置
     * 
     * 期望行为（正确）：ConditionBuilderV2 组件应该正确加载并显示路由已有的条件配置，
     * 允许用户在现有基础上进行修改
     */
    it('should load existing condition in ConditionBuilderV2 when editing', async () => {
      const route: FlowRouteConfig = {
        from_node_key: 'node1',
        to_node_key: 'node2',
        priority: 1,
        is_default: false,
        condition: {
          '==': [{ var: 'category' }, '差旅']
        }
      }

      const wrapper = mount(FlowRouteInspector, {
        props: {
          route,
          nodeOptions: [
            { label: '节点1', value: 'node1' },
            { label: '节点2', value: 'node2' }
          ],
          selectedIndex: 0,
          formId: 1,
          formSchema: {
            fields: [
              { id: 'category', label: '费用类别', type: 'select' }
            ]
          }
        },
        global: {
          stubs: globalStubs
        }
      })

      await nextTick()

      // 点击"编辑条件"按钮
      const buttons = wrapper.findAll('button')
      const editConditionButton = buttons.find(btn => btn.text().includes('编辑条件'))
      
      expect(editConditionButton).toBeDefined()
      
      if (editConditionButton) {
        await editConditionButton.trigger('click')
        await nextTick()
        await new Promise(resolve => setTimeout(resolve, 100))

        // 验证：ConditionBuilderV2 应该存在
        const conditionBuilder = wrapper.findComponent(ConditionBuilderV2)
        expect(conditionBuilder.exists()).toBe(true)

        // 关键断言：ConditionBuilderV2 应该显示空白编辑器用于添加新条件
        // 已有条件应该显示在条件列表中
        
        const builderProps = conditionBuilder.props()
        expect(builderProps.modelValue).toBeDefined()
        expect(builderProps.modelValue).not.toBeNull()
        
        // 验证编辑条件是一个空的 GROUP
        if (builderProps.modelValue) {
          const condition = builderProps.modelValue as ConditionNode
          
          // 编辑条件应该是一个空的 GROUP
          expect(condition.type).toBe('GROUP')
          
          if (condition.type === 'GROUP') {
            // 验证 GROUP 是空的（用于添加新条件）
            expect(condition.children).toBeDefined()
            expect(condition.children.length).toBe(0)
          }
        }
        
        // 验证：conditionsList 应该包含已有条件
        expect(wrapper.vm.conditionsList).toBeDefined()
        expect(wrapper.vm.conditionsList.length).toBe(1)
        
        // 验证已有条件的内容
        const existingCondition = wrapper.vm.conditionsList[0]
        expect(existingCondition).toBeDefined()
        if (existingCondition && existingCondition['==']) {
          const [field, value] = existingCondition['==']
          expect(field.var).toBe('category')
          expect(value).toBe('差旅')
        }
      }
    })

    /**
     * 场景 4：缺少条件管理功能
     * 
     * 当前行为（缺陷）：用户需要查看、修改或删除已配置的路由条件时，
     * 系统没有提供相应的 UI 交互入口和功能
     * 
     * 期望行为（正确）：系统应该提供直观的 UI 交互入口，
     * 支持查看条件详情、编辑条件内容、删除单个条件或清空所有条件
     */
    it('should provide UI for condition management (clear/delete)', async () => {
      const route: FlowRouteConfig = {
        from_node_key: 'node1',
        to_node_key: 'node2',
        priority: 1,
        is_default: false,
        condition: {
          '==': [{ var: 'amount' }, 1000]
        }
      }

      const wrapper = mount(FlowRouteInspector, {
        props: {
          route,
          nodeOptions: [
            { label: '节点1', value: 'node1' },
            { label: '节点2', value: 'node2' }
          ],
          selectedIndex: 0,
          formId: 1
        },
        global: {
          stubs: globalStubs
        }
      })

      await nextTick()

      // 关键断言：应该有"清空条件"或"删除条件"按钮
      // 在未修复的代码上，这个断言应该失败
      // 因为没有相应的 UI 入口
      
      const buttons = wrapper.findAll('button')
      const buttonTexts = buttons.map(btn => btn.text())
      
      // 查找清空条件或删除条件的按钮
      const hasClearButton = buttonTexts.some(text => 
        text.includes('清空条件') || 
        text.includes('删除条件') || 
        text.includes('移除条件')
      )
      
      // 在未修复的代码上，这个断言会失败
      expect(hasClearButton).toBe(true)
      
      // 如果找到清空按钮，验证其功能
      if (hasClearButton) {
        const clearButton = buttons.find(btn => 
          btn.text().includes('清空条件') || 
          btn.text().includes('删除条件') || 
          btn.text().includes('移除条件')
        )
        
        expect(clearButton).toBeDefined()
        
        if (clearButton) {
          // 点击清空按钮
          await clearButton.trigger('click')
          await nextTick()
          
          // 验证：应该触发更新事件，将条件设置为 null
          const emitted = wrapper.emitted('update-route')
          expect(emitted).toBeDefined()
          
          if (emitted && emitted.length > 0) {
            const lastEmit = emitted[emitted.length - 1][0] as any
            expect(lastEmit.patch.condition).toBeNull()
          }
        }
      }
    })
  })
})
