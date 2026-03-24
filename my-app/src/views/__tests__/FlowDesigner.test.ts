import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import { NMessageProvider } from 'naive-ui'
import FlowDesigner from '../FlowDesigner.vue'
import { useFlowDraftStore } from '@/stores/flowDraft'

// Mock API
vi.mock('@/api/flow', () => ({
  getFlowDefinitionDetail: vi.fn(() =>
    Promise.resolve({
      data: {
        definition: {
          id: 1,
          form_id: 100,
          name: '测试流程',
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
            }
          ],
          routes: [],
          nodes_graph: { '1': { x: 80, y: 160 } }
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

describe('FlowDesigner.vue', () => {
  let store: any
  let router: any

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useFlowDraftStore()

    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: '/flow/:flowDefinitionId',
          component: FlowDesigner
        }
      ]
    })
  })

  describe('组件初始化', () => {
    it('应该能够挂载组件', () => {
      const wrapper = mount(
        {
          components: { NMessageProvider, FlowDesigner },
          template: '<n-message-provider><FlowDesigner :flowDefinitionId="1" /></n-message-provider>'
        },
        {
          global: {
            plugins: [router],
            stubs: {
              NButton: true,
              NButtonGroup: true,
              NIcon: true,
              NModal: true,
              NForm: true,
              NFormItem: true,
              NInput: true,
              NAlert: true,
              FlowCanvas: true,
              FlowNodePalette: true,
              FlowNodeEditor: true,
              FlowRouteEditor: true
            }
          }
        }
      )
      
      expect(wrapper.exists()).toBe(true)
    })
  })

  describe('状态管理', () => {
    it('应该能够访问 store', () => {
      expect(store).toBeDefined()
      expect(store.nodes).toBeDefined()
      expect(store.routes).toBeDefined()
    })

    it('应该能够更新节点', () => {
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
      expect(store.nodes[0].name).toBe('开始')
    })

    it('应该能够更新路由', () => {
      store.routes = [
        {
          from_node_key: '1',
          to_node_key: '2',
          priority: 1,
          is_default: true
        }
      ]
      
      expect(store.routes).toHaveLength(1)
      expect(store.routes[0].from_node_key).toBe('1')
    })
  })

  describe('节点操作', () => {
    it('应该能够添加节点', () => {
      const newNode = {
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
      
      store.nodes = [newNode]
      expect(store.nodes).toHaveLength(1)
      expect(store.nodes[0].type).toBe('user')
    })

    it('应该能够删除节点', () => {
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
      
      store.nodes = store.nodes.filter((n: any) => n.id !== 2)
      expect(store.nodes).toHaveLength(1)
    })
  })

  describe('路由操作', () => {
    it('应该能够添加路由', () => {
      const newRoute = {
        from_node_key: '1',
        to_node_key: '2',
        priority: 1,
        is_default: true
      }
      
      store.routes = [newRoute]
      expect(store.routes).toHaveLength(1)
    })

    it('应该能够删除路由', () => {
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
      
      store.routes = store.routes.filter((r: any) => r.from_node_key !== '1')
      expect(store.routes).toHaveLength(1)
    })
  })

  describe('位置管理', () => {
    it('应该能够更新节点位置', () => {
      store.nodesGraph = {
        '1': { x: 100, y: 200 }
      }
      
      expect(store.nodesGraph['1']).toEqual({ x: 100, y: 200 })
    })

    it('应该能够添加多个节点位置', () => {
      store.nodesGraph = {
        '1': { x: 80, y: 160 },
        '2': { x: 280, y: 160 },
        '3': { x: 480, y: 160 }
      }
      
      expect(Object.keys(store.nodesGraph)).toHaveLength(3)
    })
  })
})
