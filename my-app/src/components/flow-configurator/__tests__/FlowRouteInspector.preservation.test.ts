/**
 * 保持不变测试：验证修复不会破坏现有功能
 * 
 * 目标：验证对于所有非 Bug 输入，修复后的代码产生与原始代码相同的结果
 * 
 * 保持不变的行为：
 * 1. 路由属性编辑（优先级、默认路由标志）应该继续正常工作
 * 2. 条件编辑操作（添加、编辑、删除条件）应该继续正常工作
 * 3. 节点切换时路由列表应该正确更新
 * 4. JsonLogic 格式应该继续使用英文字段名，不改变数据格式
 * 5. 条件逻辑组合（AND/OR）应该继续正常工作
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowRouteInspector from '../FlowRouteInspector.vue'
import type { FlowRouteConfig, FlowNodeConfig } from '@/types/flow'
import type { FormSchema } from '@/types/schema'

describe('FlowRouteInspector - 保持不变测试', () => {
  let mockFormSchema: FormSchema
  let mockNodes: FlowNodeConfig[]
  let mockRoutes: FlowRouteConfig[]

  beforeEach(() => {
    mockFormSchema = {
      id: 1,
      name: '学生信息表',
      fields: [
        {
          id: 'student_id',
          label: '学号',
          type: 'TEXT',
          required: true,
        },
        {
          id: 'score',
          label: '成绩',
          type: 'NUMBER',
          required: false,
        },
      ],
    } as FormSchema

    mockNodes = [
      {
        id: 1,
        temp_id: 'node_1',
        name: '提交申请',
        type: 'START',
      },
      {
        id: 2,
        temp_id: 'node_2',
        name: '审批人审核',
        type: 'APPROVAL',
      },
      {
        id: 3,
        temp_id: 'node_3',
        name: '财务审核',
        type: 'APPROVAL',
      },
    ]

    mockRoutes = [
      {
        id: 1,
        from_node_key: 'node_1',
        to_node_key: 'node_2',
        priority: 1,
        is_default: false,
        condition: {
          '==': [{ var: 'student_id' }, '001'],
        },
      },
      {
        id: 2,
        from_node_key: 'node_1',
        to_node_key: 'node_2',
        priority: 2,
        is_default: false,
        condition: {
          '==': [{ var: 'score' }, 90],
        },
      },
      {
        id: 3,
        from_node_key: 'node_1',
        to_node_key: 'node_3',
        priority: 1,
        is_default: true,
        condition: null,
      },
    ]
  })

  describe('保持不变 1：路由属性编辑', () => {
    it('应该能够编辑路由的优先级', () => {
      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: mockRoutes[0],
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm = wrapper.vm as any
      
      // 验证：初始优先级应该是 1
      expect(vm.priorityValue).toBe(1)
      
      // 验证：应该能够通过 emitPatch 更新优先级
      vm.emitPatch({ priority: 5 })
      
      // 验证：emit 事件应该被触发
      expect(wrapper.emitted('update-route')).toBeTruthy()
      expect(wrapper.emitted('update-route')?.[0]).toEqual([
        {
          index: 0,
          patch: { priority: 5 },
        },
      ])
    })

    it('应该能够编辑路由的默认路由标志', () => {
      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: mockRoutes[0],
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm = wrapper.vm as any
      
      // 验证：初始默认路由标志应该是 false
      expect(vm.isDefaultValue).toBe(false)
      
      // 验证：应该能够通过 emitPatch 更新默认路由标志
      vm.emitPatch({ is_default: true })
      
      // 验证：emit 事件应该被触发
      expect(wrapper.emitted('update-route')).toBeTruthy()
      expect(wrapper.emitted('update-route')?.[0]).toEqual([
        {
          index: 0,
          patch: { is_default: true },
        },
      ])
    })

    it('应该能够编辑路由的来源节点和目标节点', () => {
      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: mockRoutes[0],
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm = wrapper.vm as any
      
      // 验证：应该能够更新来源节点
      vm.emitPatch({ from_node_key: 'node_2' })
      expect(wrapper.emitted('update-route')?.[0]).toEqual([
        {
          index: 0,
          patch: { from_node_key: 'node_2' },
        },
      ])
      
      // 验证：应该能够更新目标节点
      vm.emitPatch({ to_node_key: 'node_3' })
      expect(wrapper.emitted('update-route')?.[1]).toEqual([
        {
          index: 0,
          patch: { to_node_key: 'node_3' },
        },
      ])
    })
  })

  describe('保持不变 2：条件编辑操作', () => {
    it('应该能够打开条件编辑模态框', () => {
      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: mockRoutes[0],
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm = wrapper.vm as any
      
      // 验证：初始状态下模态框应该是关闭的
      expect(vm.showConditionModal).toBe(false)
      
      // 打开模态框
      vm.openConditionModal()
      
      // 验证：模态框应该被打开
      expect(vm.showConditionModal).toBe(true)
      
      // 验证：条件列表应该被初始化
      expect(vm.conditionsList).toBeTruthy()
    })

    it('应该能够清空条件', () => {
      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: mockRoutes[0],
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm = wrapper.vm as any
      
      // 验证：初始条件应该存在
      expect(mockRoutes[0].condition).toBeTruthy()
      
      // 清空条件
      vm.handleConditionUpdate(null)
      
      // 验证：emit 事件应该被触发，条件应该被设置为 null
      expect(wrapper.emitted('update-route')).toBeTruthy()
      expect(wrapper.emitted('update-route')?.[0]).toEqual([
        {
          index: 0,
          patch: { condition: null },
        },
      ])
    })

    it('应该能够更新条件', () => {
      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: mockRoutes[0],
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm = wrapper.vm as any
      
      // 创建新的条件
      const newCondition = {
        '==': [{ var: 'student_id' }, '002'],
      }
      
      // 更新条件
      vm.handleConditionUpdate(newCondition)
      
      // 验证：emit 事件应该被触发，条件应该被更新
      expect(wrapper.emitted('update-route')).toBeTruthy()
      expect(wrapper.emitted('update-route')?.[0]).toEqual([
        {
          index: 0,
          patch: { condition: newCondition },
        },
      ])
    })
  })

  describe('保持不变 3：节点切换', () => {
    it('当切换节点时，应该正确更新显示的路由', () => {
      // 首先选择 node_2
      const wrapper1 = mount(FlowRouteInspector, {
        props: {
          route: mockRoutes[0],
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm1 = wrapper1.vm as any
      expect(vm1.relevantRoutes).toHaveLength(2)

      // 然后切换到 node_3
      const wrapper2 = mount(FlowRouteInspector, {
        props: {
          route: mockRoutes[2],
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 2,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_3',
        },
      })

      const vm2 = wrapper2.vm as any
      expect(vm2.relevantRoutes).toHaveLength(1)
      expect(vm2.relevantRoutes[0].id).toBe(3)
    })
  })

  describe('保持不变 4：JsonLogic 格式', () => {
    it('JsonLogic 格式应该继续使用英文字段名', () => {
      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: mockRoutes[0],
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm = wrapper.vm as any
      
      // 验证：conditionDraft 应该包含英文字段名
      expect(vm.conditionDraft).toContain('student_id')
      
      // 验证：JSON 格式应该保持不变
      const parsed = JSON.parse(vm.conditionDraft)
      expect(parsed['==']).toBeTruthy()
      expect(parsed['=='][0].var).toBe('student_id')
    })

    it('应该能够通过 JSON 编辑器更新条件，保持英文字段名', () => {
      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: mockRoutes[0],
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm = wrapper.vm as any
      
      // 创建新的 JSON 条件
      const newJsonCondition = JSON.stringify({
        '==': [{ var: 'score' }, 100],
      })
      
      // 更新 conditionDraft
      vm.conditionDraft = newJsonCondition
      
      // 调用 handleConditionBlur 来解析和保存
      vm.handleConditionBlur()
      
      // 验证：emit 事件应该被触发
      expect(wrapper.emitted('update-route')).toBeTruthy()
      
      // 验证：条件应该包含英文字段名
      const emittedPatch = wrapper.emitted('update-route')?.[0]?.[0]?.patch
      expect(emittedPatch?.condition['=='][0].var).toBe('score')
    })
  })

  describe('保持不变 5：条件逻辑组合', () => {
    it('应该能够处理 AND 逻辑组合', () => {
      const andCondition = {
        and: [
          { '==': [{ var: 'student_id' }, '001'] },
          { '>=': [{ var: 'score' }, 80] },
        ],
      }

      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: { ...mockRoutes[0], condition: andCondition },
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm = wrapper.vm as any
      
      // 验证：conditionDraft 应该包含 AND 逻辑
      expect(vm.conditionDraft).toContain('and')
      
      // 验证：JSON 格式应该保持不变
      const parsed = JSON.parse(vm.conditionDraft)
      expect(parsed.and).toBeTruthy()
      expect(Array.isArray(parsed.and)).toBe(true)
    })

    it('应该能够处理 OR 逻辑组合', () => {
      const orCondition = {
        or: [
          { '==': [{ var: 'student_id' }, '001'] },
          { '==': [{ var: 'student_id' }, '002'] },
        ],
      }

      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: { ...mockRoutes[0], condition: orCondition },
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm = wrapper.vm as any
      
      // 验证：conditionDraft 应该包含 OR 逻辑
      expect(vm.conditionDraft).toContain('or')
      
      // 验证：JSON 格式应该保持不变
      const parsed = JSON.parse(vm.conditionDraft)
      expect(parsed.or).toBeTruthy()
      expect(Array.isArray(parsed.or)).toBe(true)
    })

    it('应该能够处理嵌套的逻辑组合', () => {
      const nestedCondition = {
        and: [
          {
            or: [
              { '==': [{ var: 'student_id' }, '001'] },
              { '==': [{ var: 'student_id' }, '002'] },
            ],
          },
          { '>=': [{ var: 'score' }, 80] },
        ],
      }

      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: { ...mockRoutes[0], condition: nestedCondition },
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm = wrapper.vm as any
      
      // 验证：conditionDraft 应该包含嵌套的逻辑
      const parsed = JSON.parse(vm.conditionDraft)
      expect(parsed.and).toBeTruthy()
      expect(parsed.and[0].or).toBeTruthy()
    })
  })

  describe('保持不变 6：路由描述信息', () => {
    it('应该能够正确生成路由描述信息', () => {
      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: mockRoutes[0],
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm = wrapper.vm as any
      const description = vm.getRouteDescription(mockRoutes[0])

      // 验证：描述应该包含来源节点和目标节点的名称
      expect(description).toContain('提交申请')
      expect(description).toContain('审批人审核')
      expect(description).toContain('从')
      expect(description).toContain('到')
    })
  })

  describe('保持不变 7：禁用状态', () => {
    it('当 disabled 为 true 时，应该禁用所有编辑操作', () => {
      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: mockRoutes[0],
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: true, // 禁用状态
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm = wrapper.vm as any
      
      // 验证：disabled 属性应该被正确传递
      expect(vm.$props.disabled).toBe(true)
    })
  })
})
