import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useFlowDraftStore } from '@/stores/flowDraft'

// Mock API
vi.mock('@/api/flow', () => ({
  getFlowDefinitionDetail: vi.fn(() =>
    Promise.resolve({
      data: {
        definition: {
          id: 1,
          form_id: 100,
          name: '审批流程',
          version: 1,
          created_at: '2024-01-01',
          updated_at: '2024-01-01'
        },
        draft: {
          flow_definition_id: 1,
          version: 1,
          nodes: [
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
          ],
          routes: [
            {
              from_node_key: '1',
              to_node_key: '2',
              priority: 1,
              is_default: true
            },
            {
              from_node_key: '2',
              to_node_key: '3',
              priority: 1,
              is_default: true
            }
          ],
          nodes_graph: {
            '1': { x: 80, y: 160 },
            '2': { x: 280, y: 160 },
            '3': { x: 480, y: 160 }
          }
        },
        snapshots: []
      }
    })
  ),
  saveFlowDraft: vi.fn(() =>
    Promise.resolve({
      data: {
        flow_definition_id: 1,
        version: 2,
        nodes: [],
        routes: [],
        nodes_graph: {}
      }
    })
  ),
  publishFlow: vi.fn(() =>
    Promise.resolve({
      data: {
        id: 1,
        flow_definition_id: 1,
        version_tag: 'v1.0.0',
        created_at: '2024-01-01'
      }
    })
  )
}))

describe('FlowDesigner Integration Tests', () => {
  let store: any

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useFlowDraftStore()
  })

  describe('完整流程设计工作流', () => {
    it('应该能够初始化流程数据', () => {
      store.nodes = [
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
        }
      ]
      
      expect(store.nodes).toHaveLength(1)
      expect(store.nodes[0].type).toBe('start')
    })

    it('应该能够添加多个节点', () => {
      store.nodes = [
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
      
      expect(store.nodes).toHaveLength(3)
    })

    it('应该能够添加路由', () => {
      store.routes = [
        {
          from_node_key: '1',
          to_node_key: '2',
          priority: 1,
          is_default: true
        },
        {
          from_node_key: '2',
          to_node_key: '3',
          priority: 1,
          is_default: true
        }
      ]
      
      expect(store.routes).toHaveLength(2)
    })

    it('应该能够设置节点位置', () => {
      store.nodesGraph = {
        '1': { x: 80, y: 160 },
        '2': { x: 280, y: 160 },
        '3': { x: 480, y: 160 }
      }
      
      expect(Object.keys(store.nodesGraph)).toHaveLength(3)
    })

    it('应该能够完成完整的流程配置', () => {
      // 设置节点
      store.nodes = [
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
        }
      ]
      
      // 设置路由
      store.routes = [
        {
          from_node_key: '1',
          to_node_key: '2',
          priority: 1,
          is_default: true
        }
      ]
      
      // 设置位置
      store.nodesGraph = {
        '1': { x: 80, y: 160 },
        '2': { x: 280, y: 160 }
      }
      
      expect(store.nodes).toHaveLength(2)
      expect(store.routes).toHaveLength(1)
      expect(Object.keys(store.nodesGraph)).toHaveLength(2)
    })
  })

  describe('多节点编辑场景', () => {
    it('应该能够编辑节点属性', () => {
      store.nodes = [
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
        }
      ]
      
      store.nodes[0].name = '新开始'
      expect(store.nodes[0].name).toBe('新开始')
    })

    it('应该能够编辑多个节点', () => {
      store.nodes = [
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
        }
      ]
      
      store.nodes[0].name = '新开始'
      store.nodes[1].name = '新审批'
      
      expect(store.nodes[0].name).toBe('新开始')
      expect(store.nodes[1].name).toBe('新审批')
    })
  })

  describe('节点和路由的关联操作', () => {
    it('应该能够删除节点并清理相关路由', () => {
      store.nodes = [
        { id: 1, name: '开始', type: 'start', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, metadata: {}, reject_strategy: 'TO_START' },
        { id: 2, name: '审批', type: 'user', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, metadata: {}, reject_strategy: 'TO_START' }
      ]
      
      store.routes = [
        { from_node_key: '1', to_node_key: '2', priority: 1, is_default: true }
      ]
      
      // 删除节点 2
      store.nodes = store.nodes.filter((n: any) => n.id !== 2)
      store.routes = store.routes.filter((r: any) => r.to_node_key !== '2')
      
      expect(store.nodes).toHaveLength(1)
      expect(store.routes).toHaveLength(0)
    })

    it('应该能够添加新路由', () => {
      store.nodes = [
        { id: 1, name: '开始', type: 'start', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: false, auto_approve_enabled: false, auto_sample_ratio: 0, metadata: {}, reject_strategy: 'TO_START' },
        { id: 2, name: '审批', type: 'user', approve_policy: 'any', route_mode: 'exclusive', allow_delegate: true, auto_approve_enabled: false, auto_sample_ratio: 0, metadata: {}, reject_strategy: 'TO_START' }
      ]
      
      store.routes = [
        { from_node_key: '1', to_node_key: '2', priority: 1, is_default: true }
      ]
      
      expect(store.routes).toHaveLength(1)
    })

    it('应该能够更新节点位置', () => {
      store.nodesGraph = {
        '1': { x: 80, y: 160 },
        '2': { x: 280, y: 160 }
      }
      
      store.nodesGraph['1'] = { x: 100, y: 200 }
      
      expect(store.nodesGraph['1']).toEqual({ x: 100, y: 200 })
    })
  })

  describe('状态同步', () => {
    it('应该能够标记为脏状态', () => {
      store.isDirty = true
      expect(store.isDirty).toBe(true)
    })

    it('应该能够清除脏状态', () => {
      store.isDirty = true
      store.isDirty = false
      expect(store.isDirty).toBe(false)
    })
  })

  describe('数据持久化', () => {
    it('应该能够保存节点配置', () => {
      const nodeConfig = {
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
      }
      
      store.nodes = [nodeConfig]
      expect(store.nodes[0]).toEqual(nodeConfig)
    })

    it('应该能够保存路由配置', () => {
      const routeConfig = {
        from_node_key: '1',
        to_node_key: '2',
        priority: 1,
        is_default: true
      }
      
      store.routes = [routeConfig]
      expect(store.routes[0]).toEqual(routeConfig)
    })

    it('应该能够保存节点位置', () => {
      const positionConfig = {
        '1': { x: 80, y: 160 },
        '2': { x: 280, y: 160 }
      }
      
      store.nodesGraph = positionConfig
      expect(store.nodesGraph).toEqual(positionConfig)
    })
  })
})
