import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ConditionNodeEditor from '../ConditionNodeEditor.vue'
import type { ConditionBranchesConfig } from '@/types/flow'
import type { FlowNodeConfig } from '@/types/flow'

describe('ConditionNodeEditor - 单元测试', () => {
  let wrapper: any

  const mockNodes: FlowNodeConfig[] = [
    {
      id: 1,
      name: '财务审批',
      type: 'user',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: false,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_START',
      metadata: {},
    },
    {
      id: 2,
      name: '总经理审批',
      type: 'user',
      approve_policy: 'any',
      route_mode: 'exclusive',
      allow_delegate: false,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_START',
      metadata: {},
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
      reject_strategy: 'TO_START',
      metadata: {},
    },
  ]

  const mockConfig: ConditionBranchesConfig = {
    branches: [
      {
        priority: 1,
        label: '大额招待费',
        condition: { type: 'GROUP', logic: 'AND', children: [] },
        target_node_id: 1,
      },
      {
        priority: 2,
        label: '小额招待费',
        condition: { type: 'GROUP', logic: 'AND', children: [] },
        target_node_id: 2,
      },
    ],
    default_target_node_id: 3,
  }

  const createWrapper = (props = {}) => {
    return mount(ConditionNodeEditor, {
      props: {
        modelValue: mockConfig,
        allNodes: mockNodes,
        disabled: false,
        ...props,
      },
      global: {
        stubs: {
          ConditionBuilderV2: true,
          draggable: {
            template: '<div><slot /></div>',
            props: ['modelValue', 'disabled'],
            emits: ['change'],
          },
          NButton: true,
          NInput: true,
          NSelect: true,
          NEmpty: true,
          NIcon: true,
          NPopconfirm: true,
          NModal: true,
        },
      },
    })
  }

  beforeEach(() => {
    wrapper = createWrapper()
  })

  describe('分支列表编辑功能', () => {
    it('应该正确初始化分支数据', () => {
      expect(wrapper.vm.branches.length).toBe(2)
      expect(wrapper.vm.branches[0].label).toBe('大额招待费')
    })

    it('应该支持编辑分支标签', async () => {
      wrapper.vm.updateBranch(0, { label: '超大额招待费' })
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches[0].label).toBe('超大额招待费')
    })

    it('应该支持添加新分支', async () => {
      const initialCount = wrapper.vm.branches.length
      wrapper.vm.addBranch()
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches.length).toBe(initialCount + 1)
    })

    it('应该支持删除分支', async () => {
      const initialCount = wrapper.vm.branches.length
      wrapper.vm.deleteBranch(0)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches.length).toBe(initialCount - 1)
    })

    it('应该在删除分支后发出更新事件', async () => {
      wrapper.vm.deleteBranch(0)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    })

    it('应该支持编辑分支目标节点', async () => {
      wrapper.vm.updateBranch(0, { target_node_id: 2 })
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches[0].target_node_id).toBe(2)
    })

    it('应该在编辑分支后发出更新事件', async () => {
      wrapper.vm.updateBranch(0, { label: '新标签' })
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    })

    it('应该在添加分支时自动分配优先级', async () => {
      wrapper.vm.addBranch()
      await wrapper.vm.$nextTick()
      const newBranch = wrapper.vm.branches[wrapper.vm.branches.length - 1]
      expect(newBranch.priority).toBeGreaterThan(0)
    })

    it('应该在添加分支时初始化空条件', async () => {
      wrapper.vm.addBranch()
      await wrapper.vm.$nextTick()
      const newBranch = wrapper.vm.branches[wrapper.vm.branches.length - 1]
      expect(newBranch.condition.type).toBe('GROUP')
      expect(newBranch.condition.logic).toBe('AND')
    })
  })

  describe('条件表达式编辑功能', () => {
    it('应该支持打开条件编辑对话框', async () => {
      wrapper.vm.editBranch(0)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.showConditionModal).toBe(true)
      expect(wrapper.vm.editingBranchIndex).toBe(0)
    })

    it('应该在编辑对话框中显示当前条件', async () => {
      wrapper.vm.editBranch(0)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.editingCondition).toEqual(wrapper.vm.branches[0].condition)
    })

    it('应该支持保存条件表达式', async () => {
      const newCondition = {
        type: 'GROUP',
        logic: 'OR',
        children: [
          {
            type: 'RULE',
            fieldKey: 'amount',
            fieldType: 'NUMBER',
            operator: 'GREATER_THAN',
            value: 5000,
          },
        ],
      }
      wrapper.vm.editBranch(0)
      wrapper.vm.editingCondition = newCondition
      wrapper.vm.saveCondition()
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches[0].condition).toEqual(newCondition)
      expect(wrapper.vm.showConditionModal).toBe(false)
    })

    it('应该支持取消条件编辑', async () => {
      wrapper.vm.editBranch(0)
      const originalCondition = JSON.parse(JSON.stringify(wrapper.vm.branches[0].condition))
      wrapper.vm.editingCondition = { type: 'GROUP', logic: 'OR', children: [] }
      wrapper.vm.cancelCondition()
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches[0].condition).toEqual(originalCondition)
      expect(wrapper.vm.showConditionModal).toBe(false)
    })

    it('应该格式化条件预览文本', () => {
      const condition = {
        type: 'GROUP',
        logic: 'AND',
        children: [
          { type: 'RULE', fieldKey: 'amount', operator: 'GREATER_THAN', value: 5000 },
        ],
      }
      const preview = wrapper.vm.formatConditionPreview(condition)
      expect(preview).toContain('AND')
    })

    it('应该处理空条件的预览', () => {
      const emptyCondition = { type: 'GROUP', logic: 'AND', children: [] }
      const preview = wrapper.vm.formatConditionPreview(emptyCondition)
      expect(preview).toBe('未设置')
    })

    it('应该处理无效条件的预览', () => {
      const preview = wrapper.vm.formatConditionPreview(null)
      expect(preview).toBe('未设置')
    })

    it('应该支持复杂的嵌套条件表达式', async () => {
      const complexCondition = {
        type: 'GROUP',
        logic: 'AND',
        children: [
          {
            type: 'GROUP',
            logic: 'OR',
            children: [
              {
                type: 'RULE',
                fieldKey: 'status',
                fieldType: 'SINGLE_SELECT',
                operator: 'EQUALS',
                value: 'pending',
              },
            ],
          },
        ],
      }
      wrapper.vm.editBranch(0)
      wrapper.vm.editingCondition = complexCondition
      wrapper.vm.saveCondition()
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches[0].condition).toEqual(complexCondition)
    })

    it('应该在保存条件后发出更新事件', async () => {
      wrapper.vm.editBranch(0)
      wrapper.vm.editingCondition = { type: 'GROUP', logic: 'OR', children: [] }
      wrapper.vm.saveCondition()
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    })
  })

  describe('优先级排序功能', () => {
    it('应该正确管理优先级', () => {
      expect(wrapper.vm.branches[0].priority).toBe(1)
      expect(wrapper.vm.branches[1].priority).toBe(2)
    })

    it('应该支持重新排序分支', async () => {
      const temp = wrapper.vm.branches[0]
      wrapper.vm.branches[0] = wrapper.vm.branches[1]
      wrapper.vm.branches[1] = temp
      wrapper.vm.onBranchesReorder()
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches[0].priority).toBe(1)
      expect(wrapper.vm.branches[1].priority).toBe(2)
    })

    it('应该在重新排序后更新优先级', async () => {
      wrapper.vm.branches.reverse()
      wrapper.vm.onBranchesReorder()
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches[0].priority).toBe(1)
      expect(wrapper.vm.branches[1].priority).toBe(2)
    })

    it('应该在重新排序后发出更新事件', async () => {
      wrapper.vm.onBranchesReorder()
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    })

    it('应该支持多个分支的优先级管理', async () => {
      wrapper.vm.addBranch()
      wrapper.vm.addBranch()
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches.length).toBe(4)
      wrapper.vm.branches.forEach((branch: any, index: number) => {
        expect(branch.priority).toBeGreaterThan(0)
      })
    })

    it('应该在删除分支后重新计算优先级', async () => {
      wrapper.vm.addBranch()
      await wrapper.vm.$nextTick()
      wrapper.vm.deleteBranch(1)
      wrapper.vm.onBranchesReorder()
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches[0].priority).toBe(1)
      expect(wrapper.vm.branches[1].priority).toBe(2)
    })
  })

  describe('默认路由设置功能', () => {
    it('应该显示默认路由选择器', () => {
      const defaultRouteSection = wrapper.find('.default-route-section')
      expect(defaultRouteSection.exists()).toBe(true)
    })

    it('应该支持更新默认目标节点', async () => {
      wrapper.vm.updateDefaultTarget(2)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.defaultTargetNodeId).toBe(2)
    })

    it('应该在更新默认目标后发出更新事件', async () => {
      wrapper.vm.updateDefaultTarget(2)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    })

    it('应该支持设置默认目标为 null', async () => {
      wrapper.vm.updateDefaultTarget(null)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.defaultTargetNodeId).toBeNull()
    })

    it('应该在默认目标为 null 时不发出有效配置', async () => {
      wrapper.vm.updateDefaultTarget(null)
      await wrapper.vm.$nextTick()
      const emitted = wrapper.emitted('update:modelValue')
      const lastEmit = emitted[emitted.length - 1]
      expect(lastEmit[0]).toBeNull()
    })

    it('应该正确初始化默认目标节点', () => {
      expect(wrapper.vm.defaultTargetNodeId).toBe(3)
    })

    it('应该支持更改默认目标节点多次', async () => {
      wrapper.vm.updateDefaultTarget(1)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.defaultTargetNodeId).toBe(1)
      wrapper.vm.updateDefaultTarget(2)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.defaultTargetNodeId).toBe(2)
    })
  })

  describe('节点选项过滤', () => {
    it('应该生成正确的节点选项', () => {
      const nodeOptions = wrapper.vm.nodeOptions
      expect(Array.isArray(nodeOptions)).toBe(true)
      expect(nodeOptions.length).toBe(3)
    })

    it('应该过滤掉开始节点', () => {
      const nodesWithStart: FlowNodeConfig[] = [
        {
          id: 0,
          name: '开始',
          type: 'start',
          approve_policy: 'any',
          route_mode: 'exclusive',
          allow_delegate: false,
          auto_approve_enabled: false,
          auto_sample_ratio: 0,
          reject_strategy: 'TO_START',
          metadata: {},
        },
        ...mockNodes,
      ]
      wrapper = createWrapper({ allNodes: nodesWithStart })
      const nodeOptions = wrapper.vm.nodeOptions
      expect(nodeOptions.every((opt: any) => opt.value !== 0)).toBe(true)
    })

    it('应该过滤掉条件节点', () => {
      const nodesWithCondition: FlowNodeConfig[] = [
        ...mockNodes,
        {
          id: 99,
          name: '条件节点',
          type: 'condition',
          approve_policy: 'any',
          route_mode: 'exclusive',
          allow_delegate: false,
          auto_approve_enabled: false,
          auto_sample_ratio: 0,
          reject_strategy: 'TO_START',
          metadata: {},
        },
      ]
      wrapper = createWrapper({ allNodes: nodesWithCondition })
      const nodeOptions = wrapper.vm.nodeOptions
      expect(nodeOptions.every((opt: any) => opt.value !== 99)).toBe(true)
    })

    it('应该包含正确的节点标签和值', () => {
      const nodeOptions = wrapper.vm.nodeOptions
      expect(nodeOptions[0].label).toBe('财务审批')
      expect(nodeOptions[0].value).toBe(1)
    })
  })

  describe('禁用状态', () => {
    it('应该在禁用状态下隐藏添加按钮', async () => {
      wrapper = createWrapper({ disabled: true })
      const addButton = wrapper.find('.section-header button')
      expect(addButton.attributes('disabled')).toBeDefined()
    })

    it('应该在启用状态下允许操作', async () => {
      wrapper = createWrapper({ disabled: false })
      const addButton = wrapper.find('.section-header button')
      expect(addButton.attributes('disabled')).toBeUndefined()
    })
  })

  describe('数据同步', () => {
    it('应该在 modelValue 变化时更新本地状态', async () => {
      const newConfig: ConditionBranchesConfig = {
        branches: [
          {
            priority: 1,
            label: '新分支',
            condition: { type: 'GROUP', logic: 'AND', children: [] },
            target_node_id: 1,
          },
        ],
        default_target_node_id: 2,
      }
      await wrapper.setProps({ modelValue: newConfig })
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches.length).toBe(1)
      expect(wrapper.vm.branches[0].label).toBe('新分支')
    })

    it('应该在 modelValue 为 null 时清空本地状态', async () => {
      await wrapper.setProps({ modelValue: null })
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches.length).toBe(0)
      expect(wrapper.vm.defaultTargetNodeId).toBeNull()
    })

    it('应该保持分支排序', async () => {
      const config: ConditionBranchesConfig = {
        branches: [
          {
            priority: 2,
            label: '分支2',
            condition: { type: 'GROUP', logic: 'AND', children: [] },
            target_node_id: 2,
          },
          {
            priority: 1,
            label: '分支1',
            condition: { type: 'GROUP', logic: 'AND', children: [] },
            target_node_id: 1,
          },
        ],
        default_target_node_id: 3,
      }
      await wrapper.setProps({ modelValue: config })
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches[0].priority).toBe(1)
      expect(wrapper.vm.branches[1].priority).toBe(2)
    })
  })

  describe('完整流程场景', () => {
    it('应该支持完整的分支配置流程', async () => {
      wrapper.vm.addBranch()
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches.length).toBe(3)

      wrapper.vm.updateBranch(2, { label: '中额招待费' })
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches[2].label).toBe('中额招待费')

      wrapper.vm.editBranch(2)
      wrapper.vm.editingCondition = {
        type: 'GROUP',
        logic: 'AND',
        children: [
          {
            type: 'RULE',
            fieldKey: 'amount',
            fieldType: 'NUMBER',
            operator: 'BETWEEN',
            value: [1000, 5000],
          },
        ],
      }
      wrapper.vm.saveCondition()
      await wrapper.vm.$nextTick()

      wrapper.vm.updateBranch(2, { target_node_id: 2 })
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.branches[2].label).toBe('中额招待费')
      expect(wrapper.vm.branches[2].target_node_id).toBe(2)
    })

    it('应该支持删除和重新排序', async () => {
      wrapper.vm.addBranch()
      wrapper.vm.addBranch()
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches.length).toBe(4)

      wrapper.vm.deleteBranch(1)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches.length).toBe(3)

      wrapper.vm.branches.reverse()
      wrapper.vm.onBranchesReorder()
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.branches[0].priority).toBe(1)
      expect(wrapper.vm.branches[1].priority).toBe(2)
      expect(wrapper.vm.branches[2].priority).toBe(3)
    })

    it('应该在所有操作后发出正确的更新事件', async () => {
      wrapper.vm.addBranch()
      wrapper.vm.updateBranch(0, { label: '新标签' })
      wrapper.vm.updateDefaultTarget(2)
      await wrapper.vm.$nextTick()

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted.length).toBeGreaterThan(0)

      const lastEmit = emitted[emitted.length - 1]
      expect(lastEmit[0]).toBeTruthy()
      expect(lastEmit[0].branches).toBeDefined()
      expect(lastEmit[0].default_target_node_id).toBeDefined()
    })
  })

  describe('边界情况', () => {
    it('应该处理空节点列表', () => {
      wrapper = createWrapper({ allNodes: [] })
      const nodeOptions = wrapper.vm.nodeOptions
      expect(nodeOptions.length).toBe(0)
    })

    it('应该处理只有一个分支的情况', async () => {
      const singleBranchConfig: ConditionBranchesConfig = {
        branches: [
          {
            priority: 1,
            label: '唯一分支',
            condition: { type: 'GROUP', logic: 'AND', children: [] },
            target_node_id: 1,
          },
        ],
        default_target_node_id: 2,
      }
      wrapper = createWrapper({ modelValue: singleBranchConfig })
      expect(wrapper.vm.branches.length).toBe(1)
      wrapper.vm.deleteBranch(0)
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches.length).toBe(0)
    })

    it('应该处理特殊字符的分支标签', async () => {
      wrapper.vm.updateBranch(0, { label: '分支 <>&"\'@#$%' })
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches[0].label).toBe('分支 <>&"\'@#$%')
    })

    it('应该处理非常长的分支标签', async () => {
      const longLabel = 'A'.repeat(500)
      wrapper.vm.updateBranch(0, { label: longLabel })
      await wrapper.vm.$nextTick()
      expect(wrapper.vm.branches[0].label).toBe(longLabel)
    })
  })
})
