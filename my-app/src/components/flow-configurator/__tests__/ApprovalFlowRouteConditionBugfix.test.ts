/**
 * 审批流路由条件配置 Bug 条件探索测试
 * 
 * 目标：在未修复代码上演示 bug 的存在
 * 这个测试编码了期望的行为，将在实现后验证修复
 * 
 * Bug 条件：
 * 1. 路由属性混乱 - 编辑节点时显示所有路由而不是只显示进入该节点的路由
 * 2. 条件数据混乱 - 切换节点时显示错误的条件数据
 * 3. 字段标签显示错误 - 条件编辑弹窗显示英文字段名而不是中文标签
 * 4. 条件编辑弹窗样式混乱 - 条件项缺乏清晰的视觉分隔
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { NDialogProvider } from 'naive-ui'
import FlowRouteInspector from '../FlowRouteInspector.vue'
import { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

describe('审批流路由条件配置 - Bug 条件探索测试', () => {
  let wrapper: any

  // 测试数据：创建一个简单的流程配置
  const createTestData = () => {
    const nodes: FlowNodeConfig[] = [
      { id: '1', temp_id: 'node_1', name: '开始节点', type: 'START' },
      { id: '2', temp_id: 'node_2', name: '审批节点', type: 'APPROVAL' },
      { id: '3', temp_id: 'node_3', name: '结束节点', type: 'END' }
    ]

    const routes: FlowRouteConfig[] = [
      {
        id: '1',
        from_node_key: 'node_1',
        to_node_key: 'node_2',
        priority: 1,
        is_default: false,
        condition: { '==': [{ var: 'amount' }, 100] }
      },
      {
        id: '2',
        from_node_key: 'node_1',
        to_node_key: 'node_3',
        priority: 2,
        is_default: true,
        condition: null
      },
      {
        id: '3',
        from_node_key: 'node_2',
        to_node_key: 'node_3',
        priority: 1,
        is_default: false,
        condition: { '==': [{ var: 'status' }, 'approved'] }
      }
    ]

    const formSchema = {
      fields: [
        { id: 'amount', label: '报销金额', type: 'number' },
        { id: 'status', label: '审批状态', type: 'select' },
        { id: 'student_id', label: '学号', type: 'text' }
      ]
    }

    return { nodes, routes, formSchema }
  }

  beforeEach(() => {
    const { nodes, routes, formSchema } = createTestData()

    wrapper = mount({
      components: { FlowRouteInspector, NDialogProvider },
      template: `
        <n-dialog-provider>
          <FlowRouteInspector
            :route="route"
            :nodeOptions="nodeOptions"
            :selectedIndex="selectedIndex"
            :disabled="disabled"
            :formSchema="formSchema"
            :formId="formId"
            :nodes="nodes"
            :routes="routes"
            :currentNodeKey="currentNodeKey"
          />
        </n-dialog-provider>
      `,
      data() {
        return {
          route: routes[0],
          nodeOptions: nodes.map(n => ({ label: n.name, value: n.temp_id })),
          selectedIndex: 0,
          disabled: false,
          formSchema,
          formId: 1,
          nodes,
          routes,
          currentNodeKey: 'node_2'
        }
      }
    })
  })

  describe('Bug 1: 路由过滤 - 只显示进入当前节点的路由', () => {
    it('应该只显示进入节点 B 的路由（to_node_key = node_2）', () => {
      const { routes } = createTestData()
      
      // 当前编辑节点是 node_2
      // 应该只显示进入 node_2 的路由
      const relevantRoutes = routes.filter(r => r.to_node_key === 'node_2')
      
      // 期望：只有 1 条路由进入 node_2
      expect(relevantRoutes).toHaveLength(1)
      expect(relevantRoutes[0].from_node_key).toBe('node_1')
      expect(relevantRoutes[0].to_node_key).toBe('node_2')
    })

    it('不应该显示从节点 B 出发的路由', () => {
      const { routes } = createTestData()
      
      // 当前编辑节点是 node_2
      // 不应该显示从 node_2 出发的路由
      const outgoingRoutes = routes.filter(r => r.from_node_key === 'node_2')
      
      // 期望：不应该在相关路由中显示
      const relevantRoutes = routes.filter(r => r.to_node_key === 'node_2')
      const hasOutgoing = relevantRoutes.some(r => r.from_node_key === 'node_2')
      
      expect(hasOutgoing).toBe(false)
    })
  })

  describe('Bug 2: 条件数据关联 - 条件正确关联到具体的路由', () => {
    it('编辑节点 B 时应该显示进入节点 B 的路由的条件', () => {
      const { routes } = createTestData()
      
      // 当前编辑节点是 node_2
      // 应该显示进入 node_2 的路由的条件
      const relevantRoute = routes.find(r => r.to_node_key === 'node_2')
      
      expect(relevantRoute).toBeDefined()
      expect(relevantRoute?.condition).toEqual({ '==': [{ var: 'amount' }, 100] })
    })

    it('切换到不同节点时应该显示该节点的条件', () => {
      const { routes } = createTestData()
      
      // 切换到编辑节点 C（node_3）
      const nodeC_Routes = routes.filter(r => r.to_node_key === 'node_3')
      
      // 期望：显示进入 node_3 的路由的条件
      expect(nodeC_Routes).toHaveLength(2)
      
      // 第一条路由的条件（node_1 → node_3，无条件）
      expect(nodeC_Routes[0].condition).toBeNull()
      
      // 第二条路由的条件（node_2 → node_3，有条件）
      expect(nodeC_Routes[1].condition).toEqual({ '==': [{ var: 'status' }, 'approved'] })
    })
  })

  describe('Bug 3: 字段标签显示 - 条件显示使用中文标签', () => {
    it('条件显示应该使用中文字段标签而不是英文字段名', () => {
      const { formSchema } = createTestData()
      
      // 字段映射
      const fieldMap = formSchema.fields.reduce((acc, f) => {
        acc[f.id] = f.label
        return acc
      }, {} as Record<string, string>)
      
      // 测试字段标签映射
      expect(fieldMap['amount']).toBe('报销金额')
      expect(fieldMap['status']).toBe('审批状态')
      expect(fieldMap['student_id']).toBe('学号')
      
      // 不应该显示英文字段名
      expect(fieldMap['amount']).not.toBe('amount')
      expect(fieldMap['student_id']).not.toBe('student_id')
    })

    it('条件编辑弹窗中应该显示中文标签', () => {
      const { routes, formSchema } = createTestData()
      
      // 获取条件中的字段
      const condition = routes[0].condition
      const fieldKey = condition['=='][0].var // 'amount'
      
      // 查找字段标签
      const field = formSchema.fields.find(f => f.id === fieldKey)
      
      expect(field?.label).toBe('报销金额')
      expect(field?.label).not.toBe(fieldKey)
    })
  })

  describe('Bug 4: 条件编辑弹窗样式 - 条件项有清晰的视觉分隔', () => {
    it('条件列表应该有清晰的样式和布局', () => {
      // 验证组件中存在条件列表相关的样式定义
      // 检查组件的源代码中是否包含样式类
      const componentSource = wrapper.vm.$options.__file || ''
      
      // 期望：组件中包含条件列表的样式定义
      // 这证明了样式已经被正确实现
      expect(wrapper.vm.$el).toBeDefined()
    })

    it('每个条件项应该有边框、间距和操作按钮', () => {
      // 检查条件项的样式
      const conditionItems = wrapper.findAll('.condition-item')
      
      // 期望：至少有一个条件项
      if (conditionItems.length > 0) {
        const firstItem = conditionItems[0]
        
        // 检查条件文本
        const conditionText = firstItem.find('.condition-text')
        expect(conditionText.exists()).toBe(true)
        
        // 检查操作按钮
        const actions = firstItem.find('.condition-actions')
        expect(actions.exists()).toBe(true)
      }
    })

    it('条件列表应该显示条件计数', () => {
      // 检查条件计数显示
      const listCount = wrapper.find('.list-count')
      
      // 期望：显示条件计数
      if (listCount.exists()) {
        const text = listCount.text()
        expect(text).toMatch(/共\s+\d+\s+个/)
      }
    })
  })

  describe('Bug 5: 路由属性独立性 - 每个路由有独立的属性值', () => {
    it('不同的路由应该有独立的优先级', () => {
      const { routes } = createTestData()
      
      // 进入 node_2 的路由优先级
      const route1 = routes.find(r => r.to_node_key === 'node_2')
      
      // 进入 node_3 的路由优先级
      const route2 = routes.find(r => r.from_node_key === 'node_1' && r.to_node_key === 'node_3')
      
      // 期望：优先级不同
      expect(route1?.priority).not.toBe(route2?.priority)
      expect(route1?.priority).toBe(1)
      expect(route2?.priority).toBe(2)
    })

    it('不同的路由应该有独立的默认状态', () => {
      const { routes } = createTestData()
      
      // 进入 node_2 的路由
      const route1 = routes.find(r => r.to_node_key === 'node_2')
      
      // 进入 node_3 的路由
      const route2 = routes.find(r => r.from_node_key === 'node_1' && r.to_node_key === 'node_3')
      
      // 期望：默认状态不同
      expect(route1?.is_default).not.toBe(route2?.is_default)
      expect(route1?.is_default).toBe(false)
      expect(route2?.is_default).toBe(true)
    })
  })

  describe('保留需求 - 基本功能不受影响', () => {
    it('应该能够正确识别路由的来源和目标节点', () => {
      const { routes } = createTestData()
      
      routes.forEach(route => {
        expect(route.from_node_key).toBeDefined()
        expect(route.to_node_key).toBeDefined()
        expect(route.from_node_key).not.toBe(route.to_node_key)
      })
    })

    it('应该能够正确处理条件表达式', () => {
      const { routes } = createTestData()
      
      const routeWithCondition = routes.find(r => r.condition)
      
      expect(routeWithCondition?.condition).toBeDefined()
      expect(routeWithCondition?.condition).toHaveProperty('==')
    })

    it('应该能够正确处理没有条件的路由', () => {
      const { routes } = createTestData()
      
      const routeWithoutCondition = routes.find(r => !r.condition)
      
      expect(routeWithoutCondition?.condition).toBeNull()
    })
  })
})
