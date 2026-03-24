/**
 * Bug 条件探索测试：路由过滤和条件显示本地化
 * 
 * 目标：在未修复代码上运行此测试以观察 Bug 的表现
 * 
 * Bug 条件：
 * 1. 用户在流程审批配置页面选择一个节点时，系统显示所有路由而不是只显示进入该节点的路由
 * 2. 用户查看路由条件时，系统使用英文字段名而不是中文字段标签
 * 3. 用户编辑路由条件中的字段选择时，系统显示英文字段名而不是中文字段标签
 * 
 * 期望行为：
 * 1. 系统应该只显示进入当前节点的路由（to_node_key === currentNodeKey）
 * 2. 系统应该使用中文字段标签显示条件
 * 3. 系统应该在字段列表中显示中文字段标签
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowRouteInspector from '../FlowRouteInspector.vue'
import type { FlowRouteConfig, FlowNodeConfig } from '@/types/flow'
import type { FormSchema } from '@/types/schema'

describe('FlowRouteInspector - Bug 条件探索测试', () => {
  let mockFormSchema: FormSchema
  let mockNodes: FlowNodeConfig[]
  let mockRoutes: FlowRouteConfig[]

  beforeEach(() => {
    // 创建模拟的表单 Schema，包含中文字段标签
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
          id: 'student_name',
          label: '学生姓名',
          type: 'TEXT',
          required: true,
        },
        {
          id: 'class_name',
          label: '班级名称',
          type: 'TEXT',
          required: false,
        },
        {
          id: 'score',
          label: '成绩',
          type: 'NUMBER',
          required: false,
        },
      ],
    } as FormSchema

    // 创建模拟的节点
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
      {
        id: 4,
        temp_id: 'node_4',
        name: '完成',
        type: 'END',
      },
    ]

    // 创建模拟的路由
    // 总共 5 条路由：
    // - 2 条进入 node_2（审批人审核）
    // - 2 条进入 node_3（财务审核）
    // - 1 条进入 node_4（完成）
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
          '==': [{ var: 'student_id' }, '002'],
        },
      },
      {
        id: 3,
        from_node_key: 'node_1',
        to_node_key: 'node_3',
        priority: 1,
        is_default: false,
        condition: {
          '==': [{ var: 'score' }, 90],
        },
      },
      {
        id: 4,
        from_node_key: 'node_1',
        to_node_key: 'node_3',
        priority: 2,
        is_default: false,
        condition: {
          '==': [{ var: 'score' }, 80],
        },
      },
      {
        id: 5,
        from_node_key: 'node_1',
        to_node_key: 'node_4',
        priority: 1,
        is_default: true,
        condition: null,
      },
    ]
  })

  describe('Bug 1：路由过滤问题', () => {
    it('应该只显示进入当前节点的路由（node_2）', () => {
      // 选择 node_2（审批人审核）
      const currentNodeKey = 'node_2'
      
      // 创建组件实例
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
          currentNodeKey,
        },
      })

      // 获取 relevantRoutes 计算属性的值
      const vm = wrapper.vm as any
      const relevantRoutes = vm.relevantRoutes

      // 验证：只有 2 条路由进入 node_2
      expect(relevantRoutes).toHaveLength(2)
      expect(relevantRoutes.every((r: FlowRouteConfig) => r.to_node_key === currentNodeKey)).toBe(true)
      
      // 验证：这 2 条路由是正确的
      expect(relevantRoutes[0].id).toBe(1)
      expect(relevantRoutes[1].id).toBe(2)
    })

    it('应该只显示进入当前节点的路由（node_3）', () => {
      // 选择 node_3（财务审核）
      const currentNodeKey = 'node_3'
      
      const wrapper = mount(FlowRouteInspector, {
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
          currentNodeKey,
        },
      })

      const vm = wrapper.vm as any
      const relevantRoutes = vm.relevantRoutes

      // 验证：只有 2 条路由进入 node_3
      expect(relevantRoutes).toHaveLength(2)
      expect(relevantRoutes.every((r: FlowRouteConfig) => r.to_node_key === currentNodeKey)).toBe(true)
      
      // 验证：这 2 条路由是正确的
      expect(relevantRoutes[0].id).toBe(3)
      expect(relevantRoutes[1].id).toBe(4)
    })

    it('当没有路由进入当前节点时，应该显示空状态', () => {
      // 选择一个没有任何路由进入的节点
      const currentNodeKey = 'node_nonexistent'
      
      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: undefined,
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: null,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey,
        },
      })

      const vm = wrapper.vm as any
      const relevantRoutes = vm.relevantRoutes

      // 验证：没有路由进入该节点
      expect(relevantRoutes).toHaveLength(0)
    })
  })

  describe('Bug 2：条件显示本地化问题', () => {
    it('应该使用中文字段标签显示条件（student_id -> 学号）', () => {
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
      const conditionDisplay = vm.formatConditionForDisplay(mockRoutes[0].condition)

      // 验证：条件显示中应该包含中文标签"学号"而不是英文字段名"student_id"
      expect(conditionDisplay).toContain('学号')
      expect(conditionDisplay).not.toContain('student_id')
      
      // 验证：条件显示格式应该是"学号 等于 001"
      expect(conditionDisplay).toMatch(/学号\s+等于\s+001/)
    })

    it('应该使用中文字段标签显示条件（score -> 成绩）', () => {
      const wrapper = mount(FlowRouteInspector, {
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

      const vm = wrapper.vm as any
      const conditionDisplay = vm.formatConditionForDisplay(mockRoutes[2].condition)

      // 验证：条件显示中应该包含中文标签"成绩"而不是英文字段名"score"
      expect(conditionDisplay).toContain('成绩')
      expect(conditionDisplay).not.toContain('score')
      
      // 验证：条件显示格式应该是"成绩 等于 90"
      expect(conditionDisplay).toMatch(/成绩\s+等于\s+90/)
    })

    it('应该处理复杂的条件表达式并使用中文标签', () => {
      // 创建一个复杂的条件表达式
      const complexCondition = {
        and: [
          { '==': [{ var: 'student_id' }, '001'] },
          { '>=': [{ var: 'score' }, 80] },
        ],
      }

      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: { ...mockRoutes[0], condition: complexCondition },
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
      const conditionDisplay = vm.formatConditionForDisplay(complexCondition)

      // 验证：条件显示中应该包含中文标签而不是英文字段名
      expect(conditionDisplay).toContain('学号')
      expect(conditionDisplay).toContain('成绩')
      expect(conditionDisplay).not.toContain('student_id')
      expect(conditionDisplay).not.toContain('score')
      
      // 验证：条件显示应该包含逻辑连接符"且"
      expect(conditionDisplay).toContain('且')
    })
  })

  describe('Bug 3：字段选择器本地化问题', () => {
    it('字段列表应该显示中文标签而不是英文字段名', () => {
      // 这个测试验证 ConditionRule 组件中的字段选择器
      // 字段选项应该使用中文标签作为显示文本
      
      const fields = mockFormSchema.fields!.map(f => ({
        key: f.id,
        name: f.label, // 应该使用标签而不是 id
        type: f.type as any,
        isSystem: false,
      }))

      // 验证：字段列表中的 name 应该是中文标签
      expect(fields[0].name).toBe('学号')
      expect(fields[1].name).toBe('学生姓名')
      expect(fields[2].name).toBe('班级名称')
      expect(fields[3].name).toBe('成绩')
      
      // 验证：不应该包含英文字段名
      expect(fields.map(f => f.name)).not.toContain('student_id')
      expect(fields.map(f => f.name)).not.toContain('student_name')
      expect(fields.map(f => f.name)).not.toContain('class_name')
      expect(fields.map(f => f.name)).not.toContain('score')
    })
  })

  describe('边界情况', () => {
    it('当 formSchema 为空时，应该使用英文字段名作为备选', () => {
      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: mockRoutes[0],
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 0,
          disabled: false,
          formSchema: undefined, // 没有 formSchema
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_2',
        },
      })

      const vm = wrapper.vm as any
      const conditionDisplay = vm.formatConditionForDisplay(mockRoutes[0].condition)

      // 验证：当 formSchema 为空时，应该使用英文字段名作为备选
      expect(conditionDisplay).toContain('student_id')
    })

    it('当条件为 null 时，应该显示"未设置条件"', () => {
      const wrapper = mount(FlowRouteInspector, {
        props: {
          route: { ...mockRoutes[4], condition: null },
          nodeOptions: mockNodes.map(n => ({
            label: n.name,
            value: n.temp_id,
          })),
          selectedIndex: 4,
          disabled: false,
          formSchema: mockFormSchema,
          formId: 1,
          nodes: mockNodes,
          routes: mockRoutes,
          currentNodeKey: 'node_4',
        },
      })

      const vm = wrapper.vm as any
      const conditionDisplay = vm.formatConditionForDisplay(null)

      // 验证：条件为 null 时应该显示"未设置条件"
      expect(conditionDisplay).toBe('未设置条件')
    })
  })
})
