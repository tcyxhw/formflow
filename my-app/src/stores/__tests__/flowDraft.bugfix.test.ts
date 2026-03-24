/**
 * flowDraft Store 缺陷条件探索测试
 * 
 * **Validates: Requirements 1.4, 1.5**
 * 
 * 这个测试文件用于在未修复代码上表现缺陷存在。
 * 测试应该在未修复代码上失败，证实缺陷存在。
 * 
 * 缺陷 3：路由属性覆盖问题
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFlowDraftStore } from '../flowDraft'
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

describe('flowDraft Store - 缺陷条件探索测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('缺陷 3: 路由覆盖问题', () => {
    it('设置多条路由时，所有路由都应该被保留', () => {
      // **Validates: Requirements 1.4, 1.5**
      const store = useFlowDraftStore()

      // 创建测试节点
      const startNode: FlowNodeConfig = {
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
      }

      const approveNode: FlowNodeConfig = {
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

      const endNode: FlowNodeConfig = {
        name: '结束节点',
        type: 'end',
        approve_policy: 'any',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {},
        temp_id: 'end-1',
      }

      // 添加节点到 store
      store.nodes = [startNode, approveNode, endNode]

      // 创建第一条路由：开始节点 -> 审批节点
      const route1: FlowRouteConfig = {
        from_node_key: 'start-1',
        to_node_key: 'approve-1',
        is_default: true,
        priority: 1,
      }

      store.addRoute(route1)

      // 验证第一条路由被添加
      expect(store.routes.length).toBe(1)
      expect(store.routes[0].from_node_key).toBe('start-1')
      expect(store.routes[0].to_node_key).toBe('approve-1')

      // 创建第二条路由：审批节点 -> 结束节点
      const route2: FlowRouteConfig = {
        from_node_key: 'approve-1',
        to_node_key: 'end-1',
        is_default: true,
        priority: 1,
      }

      store.addRoute(route2)

      // 期望：两条路由都应该被保留
      // 在未修复代码上，这个测试可能会失败，因为第二条路由可能覆盖第一条
      expect(store.routes.length).toBe(2)
      expect(store.routes[0].from_node_key).toBe('start-1')
      expect(store.routes[0].to_node_key).toBe('approve-1')
      expect(store.routes[1].from_node_key).toBe('approve-1')
      expect(store.routes[1].to_node_key).toBe('end-1')
    })

    it('更新路由时，不应该影响其他路由', () => {
      // **Validates: Requirements 1.5**
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
          name: '审批节点1',
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
        {
          name: '审批节点2',
          type: 'user',
          approve_policy: 'any',
          route_mode: 'exclusive',
          allow_delegate: true,
          auto_approve_enabled: false,
          auto_sample_ratio: 0,
          reject_strategy: 'TO_START',
          metadata: {},
          temp_id: 'approve-2',
        },
        {
          name: '结束节点',
          type: 'end',
          approve_policy: 'any',
          route_mode: 'exclusive',
          allow_delegate: false,
          auto_approve_enabled: false,
          auto_sample_ratio: 0,
          reject_strategy: 'TO_START',
          metadata: {},
          temp_id: 'end-1',
        },
      ]

      // 添加三条路由
      store.addRoute({
        from_node_key: 'start-1',
        to_node_key: 'approve-1',
        is_default: true,
        priority: 1,
      })

      store.addRoute({
        from_node_key: 'approve-1',
        to_node_key: 'approve-2',
        is_default: true,
        priority: 1,
      })

      store.addRoute({
        from_node_key: 'approve-2',
        to_node_key: 'end-1',
        is_default: true,
        priority: 1,
      })

      // 验证所有路由都被添加
      expect(store.routes.length).toBe(3)

      // 更新第二条路由的优先级
      store.updateRoute(1, { priority: 2 })

      // 期望：所有路由都应该保留，只有第二条路由的优先级改变
      expect(store.routes.length).toBe(3)
      expect(store.routes[0].from_node_key).toBe('start-1')
      expect(store.routes[0].to_node_key).toBe('approve-1')
      expect(store.routes[0].priority).toBe(1)
      expect(store.routes[1].from_node_key).toBe('approve-1')
      expect(store.routes[1].to_node_key).toBe('approve-2')
      expect(store.routes[1].priority).toBe(2)
      expect(store.routes[2].from_node_key).toBe('approve-2')
      expect(store.routes[2].to_node_key).toBe('end-1')
      expect(store.routes[2].priority).toBe(1)
    })

    it('设置多个节点的路由属性时，应该独立管理每个节点的路由', () => {
      // **Validates: Requirements 1.5**
      const store = useFlowDraftStore()

      // 创建一个更复杂的流程：开始 -> 审批1 -> 审批2 -> 审批3 -> 结束
      store.nodes = [
        { name: '开始', type: 'start', temp_id: 'start', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批1', type: 'user', temp_id: 'approve-1', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批2', type: 'user', temp_id: 'approve-2', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '审批3', type: 'user', temp_id: 'approve-3', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
        { name: '结束', type: 'end', temp_id: 'end', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, reject_strategy: 'TO_START', metadata: {} },
      ]

      // 依次添加路由
      store.addRoute({ from_node_key: 'start', to_node_key: 'approve-1', is_default: true, priority: 1 })
      store.addRoute({ from_node_key: 'approve-1', to_node_key: 'approve-2', is_default: true, priority: 1 })
      store.addRoute({ from_node_key: 'approve-2', to_node_key: 'approve-3', is_default: true, priority: 1 })
      store.addRoute({ from_node_key: 'approve-3', to_node_key: 'end', is_default: true, priority: 1 })

      // 期望：所有 4 条路由都应该被保留
      expect(store.routes.length).toBe(4)
      expect(store.routes[0].from_node_key).toBe('start')
      expect(store.routes[1].from_node_key).toBe('approve-1')
      expect(store.routes[2].from_node_key).toBe('approve-2')
      expect(store.routes[3].from_node_key).toBe('approve-3')
    })
  })
})
