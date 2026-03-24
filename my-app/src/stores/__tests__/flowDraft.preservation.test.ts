/**
 * flowDraft Store 保留属性测试
 * 
 * **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
 * 
 * Property 2: Preservation - 非缺陷条件行为保留
 * 
 * 这个测试文件验证修复不会破坏现有功能。
 * 测试应该在未修复代码上通过，并在修复后继续通过。
 * 
 * 保留行为：
 * 1. 路由的创建和删除继续正常工作
 * 2. 节点的创建和删除继续正常工作
 * 3. 流程的保存和加载继续正常工作
 * 4. 历史记录（撤销/重做）继续正常工作
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFlowDraftStore } from '../flowDraft'
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

describe('flowDraft Store - 保留属性测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('路由管理功能保留', () => {
    it('addRoute 方法继续正常工作', () => {
      // **Validates: Requirements 3.3**
      const store = useFlowDraftStore()

      // 创建测试节点
      store.nodes = [
        {
          name: '开始节点',
          type: 'start',
          approve_policy: 'any',
          route_mode: 'exclusive',
          allow_delegate: false,
          auto_approve_enabled: false,
          auto_sample_ratio: 0,
          reject_strategy: 'TO_START',
          metadata: {},
          temp_id: 'start-1',
        },
        {
          name: '审批节点',
          type: 'user',
          approve_policy: 'any',
          route_mode: 'exclusive',
          allow_delegate: true,
          auto_approve_enabled: false,
          auto_sample_ratio: 0,
          reject_strategy: 'TO_START',
          metadata: {},
          temp_id: 'approve-1',
        },
      ]

      // 添加路由
      const route: FlowRouteConfig = {
        from_node_key: 'start-1',
        to_node_key: 'approve-1',
        is_default: true,
        priority: 1,
      }

      store.addRoute(route)

      // 验证路由被添加
      expect(store.routes.length).toBe(1)
      expect(store.routes[0].from_node_key).toBe('start-1')
      expect(store.routes[0].to_node_key).toBe('approve-1')
      expect(store.routes[0].is_default).toBe(true)
      expect(store.routes[0].priority).toBe(1)

      // 验证 selectedRouteIndex 被设置
      expect(store.selectedRouteIndex).toBe(0)

      // 验证 dirty 标志被设置
      expect(store.dirty).toBe(true)
    })

    it('updateRoute 方法继续正常工作', () => {
      // **Validates: Requirements 3.3**
      const store = useFlowDraftStore()

      // 创建测试节点和路由
      store.nodes = [
        { name: '开始', type: 'start', temp_id: 'start', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批', type: 'user', temp_id: 'approve', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
      ]

      store.addRoute({
        from_node_key: 'start',
        to_node_key: 'approve',
        is_default: true,
        priority: 1,
      })

      // 更新路由
      store.updateRoute(0, { priority: 5, is_default: false })

      // 验证路由被更新
      expect(store.routes[0].priority).toBe(5)
      expect(store.routes[0].is_default).toBe(false)
      expect(store.routes[0].from_node_key).toBe('start')
      expect(store.routes[0].to_node_key).toBe('approve')
    })

    it('removeRoute 方法继续正常工作', () => {
      // **Validates: Requirements 3.3**
      const store = useFlowDraftStore()

      // 创建测试节点和路由
      store.nodes = [
        { name: '开始', type: 'start', temp_id: 'start', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批1', type: 'user', temp_id: 'approve-1', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批2', type: 'user', temp_id: 'approve-2', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
      ]

      store.addRoute({ from_node_key: 'start', to_node_key: 'approve-1', is_default: true, priority: 1 })
      store.addRoute({ from_node_key: 'approve-1', to_node_key: 'approve-2', is_default: true, priority: 1 })

      expect(store.routes.length).toBe(2)

      // 删除第一条路由
      store.removeRoute(0)

      // 验证路由被删除
      expect(store.routes.length).toBe(1)
      expect(store.routes[0].from_node_key).toBe('approve-1')
      expect(store.routes[0].to_node_key).toBe('approve-2')
    })

    it('带条件的路由继续正常工作', () => {
      // **Validates: Requirements 3.1**
      const store = useFlowDraftStore()

      store.nodes = [
        { name: '开始', type: 'start', temp_id: 'start', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批', type: 'user', temp_id: 'approve', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
      ]

      const condition = { '==': [{ var: 'amount' }, 100] }

      store.addRoute({
        from_node_key: 'start',
        to_node_key: 'approve',
        is_default: false,
        priority: 1,
        condition,
      })

      // 验证条件被正确保存
      expect(store.routes[0].condition).toEqual(condition)

      // 更新条件
      const newCondition = { '>': [{ var: 'amount' }, 200] }
      store.updateRoute(0, { condition: newCondition })

      // 验证条件被正确更新
      expect(store.routes[0].condition).toEqual(newCondition)
    })

    it('结束节点不能有出边的验证继续正常工作', () => {
      // **Validates: Requirements 3.2**
      const store = useFlowDraftStore()

      store.nodes = [
        { name: '结束', type: 'end', temp_id: 'end', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批', type: 'user', temp_id: 'approve', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
      ]

      // 尝试从结束节点创建出边
      expect(() => {
        store.addRoute({
          from_node_key: 'end',
          to_node_key: 'approve',
          is_default: true,
          priority: 1,
        })
      }).toThrow('结束节点不能有出边')
    })
  })

  describe('节点管理功能保留', () => {
    it('addNode 方法继续正常工作', () => {
      // **Validates: Requirements 3.2**
      const store = useFlowDraftStore()

      const initialCount = store.nodes.length

      // 添加节点
      store.addNode('user')

      // 验证节点被添加
      expect(store.nodes.length).toBe(initialCount + 1)
      expect(store.nodes[store.nodes.length - 1].type).toBe('user')

      // 验证节点被选中
      expect(store.selectedNodeKey).toBeDefined()

      // 验证节点位置被初始化
      const nodeKey = store.selectedNodeKey!
      expect(store.nodesGraph[nodeKey]).toBeDefined()
      expect(store.nodesGraph[nodeKey].x).toBeGreaterThanOrEqual(0)
      expect(store.nodesGraph[nodeKey].y).toBeGreaterThanOrEqual(0)
    })

    it('updateNode 方法继续正常工作', () => {
      // **Validates: Requirements 3.1**
      const store = useFlowDraftStore()

      const node: FlowNodeConfig = {
        name: '审批节点',
        type: 'user',
        approve_policy: 'any',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {},
        temp_id: 'approve-1',
      }

      store.nodes = [node]

      // 更新节点
      store.updateNode('approve-1', {
        name: '更新后的审批节点',
        approve_policy: 'all',
      })

      // 验证节点被更新
      expect(store.nodes[0].name).toBe('更新后的审批节点')
      expect(store.nodes[0].approve_policy).toBe('all')
      expect(store.nodes[0].type).toBe('user')
    })

    it('removeNode 方法继续正常工作', () => {
      // **Validates: Requirements 3.2**
      const store = useFlowDraftStore()

      store.nodes = [
        { name: '开始', type: 'start', temp_id: 'start', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批', type: 'user', temp_id: 'approve', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '结束', type: 'end', temp_id: 'end', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
      ]

      store.addRoute({ from_node_key: 'start', to_node_key: 'approve', is_default: true, priority: 1 })
      store.addRoute({ from_node_key: 'approve', to_node_key: 'end', is_default: true, priority: 1 })

      // 删除中间节点
      store.removeNode('approve')

      // 验证节点被删除
      expect(store.nodes.length).toBe(2)
      expect(store.nodes.find(n => n.temp_id === 'approve')).toBeUndefined()

      // 验证相关路由被删除
      expect(store.routes.length).toBe(0)

      // 验证节点位置被删除
      expect(store.nodesGraph['approve']).toBeUndefined()
    })

    it('条件节点的配置继续正常工作', () => {
      // **Validates: Requirements 3.2**
      const store = useFlowDraftStore()

      const conditionNode: FlowNodeConfig = {
        name: '条件节点',
        type: 'condition',
        approve_policy: 'any',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {},
        temp_id: 'condition-1',
        condition_branches: [
          {
            name: '分支1',
            condition: { '==': [{ var: 'amount' }, 100] },
          },
          {
            name: '分支2',
            condition: { '>': [{ var: 'amount' }, 100] },
          },
        ],
      }

      store.nodes = [conditionNode]

      // 验证条件分支被正确保存
      expect(store.nodes[0].condition_branches).toHaveLength(2)
      expect(store.nodes[0].condition_branches![0].name).toBe('分支1')

      // 更新条件分支
      store.updateNode('condition-1', {
        condition_branches: [
          {
            name: '更新后的分支',
            condition: { '<': [{ var: 'amount' }, 50] },
          },
        ],
      })

      // 验证条件分支被正确更新
      expect(store.nodes[0].condition_branches).toHaveLength(1)
      expect(store.nodes[0].condition_branches![0].name).toBe('更新后的分支')
    })
  })

  describe('流程保存和加载功能保留', () => {
    it('buildPayload 方法继续正常工作', () => {
      // **Validates: Requirements 3.4**
      const store = useFlowDraftStore()

      // 设置流程定义 ID
      store.flowDefinitionId = 123
      store.version = 1

      // 创建测试数据
      store.nodes = [
        { name: '开始', type: 'start', temp_id: 'start', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批', type: 'user', temp_id: 'approve', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
      ]

      store.routes = [
        { from_node_key: 'start', to_node_key: 'approve', is_default: true, priority: 1 },
      ]

      store.nodesGraph = {
        start: { x: 100, y: 200 },
        approve: { x: 300, y: 200 },
      }

      // 构建 payload
      const payload = store.buildPayload()

      // 验证 payload 结构
      expect(payload.flow_definition_id).toBe(123)
      expect(payload.version).toBe(1)
      expect(payload.nodes).toHaveLength(2)
      expect(payload.routes).toHaveLength(1)
      expect(payload.nodes_graph).toEqual({
        start: { x: 100, y: 200 },
        approve: { x: 300, y: 200 },
      })
    })

    it('节点位置管理继续正常工作', () => {
      // **Validates: Requirements 3.4**
      const store = useFlowDraftStore()

      const node: FlowNodeConfig = {
        name: '审批节点',
        type: 'user',
        approve_policy: 'any',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {},
        temp_id: 'approve-1',
      }

      store.nodes = [node]

      // 更新节点位置
      store.updateNodePosition('approve-1', { x: 500, y: 300 })

      // 验证位置被更新
      expect(store.nodesGraph['approve-1']).toEqual({ x: 500, y: 300 })

      // 验证 dirty 标志被设置
      expect(store.dirty).toBe(true)
    })
  })

  describe('历史记录功能保留', () => {
    it('撤销功能继续正常工作', () => {
      // **Validates: Requirements 3.2**
      const store = useFlowDraftStore()

      // 记录初始节点数量
      const initialCount = store.nodes.length

      // 添加一个节点（会创建历史记录）
      store.addNode('user')
      
      // 验证节点被添加
      expect(store.nodes.length).toBe(initialCount + 1)

      // 验证可以撤销
      expect(store.canUndo).toBe(true)

      // 执行撤销
      store.undo()

      // 验证节点被撤销，恢复到初始状态
      expect(store.nodes.length).toBe(initialCount)
    })

    it('重做功能继续正常工作', () => {
      // **Validates: Requirements 3.2**
      const store = useFlowDraftStore()

      // 初始化数据
      store.nodes = [
        { name: '开始', type: 'start', temp_id: 'start', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
      ]

      // 添加一个节点
      store.addNode('user')
      const nodeCount = store.nodes.length

      // 撤销
      store.undo()

      // 验证可以重做
      expect(store.canRedo).toBe(true)

      // 执行重做
      store.redo()

      // 验证节点被恢复
      expect(store.nodes.length).toBe(nodeCount)
    })

    it('历史记录大小限制继续正常工作', () => {
      // **Validates: Requirements 3.2**
      const store = useFlowDraftStore()

      // 初始化数据
      store.nodes = []

      // 添加超过最大历史记录数量的操作
      for (let i = 0; i < 60; i++) {
        store.addNode('user')
      }

      // 验证历史记录被限制在最大大小
      expect(store.history.length).toBeLessThanOrEqual(50)
    })
  })

  describe('选择状态管理保留', () => {
    it('selectNodeByKey 方法继续正常工作', () => {
      // **Validates: Requirements 3.2**
      const store = useFlowDraftStore()

      store.nodes = [
        { name: '开始', type: 'start', temp_id: 'start', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批', type: 'user', temp_id: 'approve', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
      ]

      // 选择节点
      store.selectNodeByKey('approve')

      // 验证节点被选中
      expect(store.selectedNodeKey).toBe('approve')
      expect(store.currentNode?.temp_id).toBe('approve')
    })

    it('selectRouteByIndex 方法继续正常工作', () => {
      // **Validates: Requirements 3.3**
      const store = useFlowDraftStore()

      store.nodes = [
        { name: '开始', type: 'start', temp_id: 'start', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批', type: 'user', temp_id: 'approve', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
      ]

      store.addRoute({ from_node_key: 'start', to_node_key: 'approve', is_default: true, priority: 1 })

      // 选择路由
      store.selectRouteByIndex(0)

      // 验证路由被选中
      expect(store.selectedRouteIndex).toBe(0)
      expect(store.currentRoute?.from_node_key).toBe('start')
    })

    it('多选功能继续正常工作', () => {
      // **Validates: Requirements 3.2**
      const store = useFlowDraftStore()

      store.nodes = [
        { name: '开始', type: 'start', temp_id: 'start', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批1', type: 'user', temp_id: 'approve-1', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批2', type: 'user', temp_id: 'approve-2', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
      ]

      // 多选节点
      store.toggleNodeSelection('approve-1', true)
      store.toggleNodeSelection('approve-2', true)

      // 验证多个节点被选中
      expect(store.isNodeSelected('approve-1')).toBe(true)
      expect(store.isNodeSelected('approve-2')).toBe(true)
      expect(store.getSelectedNodeKeys()).toHaveLength(2)
    })
  })

  describe('计算属性保留', () => {
    it('nodeOptions 计算属性继续正常工作', () => {
      // **Validates: Requirements 3.2**
      const store = useFlowDraftStore()

      store.nodes = [
        { name: '开始节点', type: 'start', temp_id: 'start', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批节点', type: 'user', temp_id: 'approve', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
      ]

      // 验证 nodeOptions
      expect(store.nodeOptions).toHaveLength(2)
      expect(store.nodeOptions[0]).toEqual({ label: '开始节点', value: 'start' })
      expect(store.nodeOptions[1]).toEqual({ label: '审批节点', value: 'approve' })
    })

    it('definitionLoaded 计算属性继续正常工作', () => {
      // **Validates: Requirements 3.4**
      const store = useFlowDraftStore()

      // 初始状态：未加载
      expect(store.definitionLoaded).toBe(false)

      // 设置流程定义 ID
      store.flowDefinitionId = 123

      // 验证已加载
      expect(store.definitionLoaded).toBe(true)
    })
  })
})
