/**
 * 流程草稿状态管理集成测试
 * 测试 useFlowDraftStore 与 API 的交互
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFlowDraftStore } from '../flowDraft'
import type { FlowDefinitionDetailResponse, FlowDraftResponse } from '@/types/flow'

// Mock API 模块
vi.mock('@/api/flow', () => ({
  getFlowDefinitionDetail: vi.fn(),
  saveFlowDraft: vi.fn(),
  publishFlow: vi.fn(),
}))

import * as flowApi from '@/api/flow'

describe('useFlowDraftStore - 集成测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('加载流程定义', () => {
    it('应该加载流程定义和草稿', async () => {
      const store = useFlowDraftStore()
      
      const mockDetail: FlowDefinitionDetailResponse = {
        definition: {
          id: 1,
          form_id: 100,
          name: '招待费申请',
          version: 1,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
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
              reject_strategy: 'TO_START',
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
              reject_strategy: 'TO_START',
            },
          ],
          routes: [
            {
              from_node_key: '1',
              to_node_key: '2',
              priority: 1,
              is_default: true,
            },
          ],
          nodes_graph: {
            '1': { x: 80, y: 160 },
            '2': { x: 280, y: 160 },
          },
        },
        snapshots: [],
      }
      
      vi.mocked(flowApi.getFlowDefinitionDetail).mockResolvedValue({
        data: mockDetail,
      } as any)
      
      const result = await store.loadDefinition(1)
      
      expect(store.flowDefinitionId).toBe(1)
      expect(store.flowName).toBe('招待费申请')
      expect(store.nodes).toHaveLength(2)
      expect(store.routes).toHaveLength(1)
      expect(store.dirty).toBe(false)
      expect(result.detail).toEqual(mockDetail)
    })

    it('应该在没有草稿时构建默认草稿', async () => {
      const store = useFlowDraftStore()
      
      const mockDetail: FlowDefinitionDetailResponse = {
        definition: {
          id: 1,
          form_id: 100,
          name: '新流程',
          version: 1,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
        draft: null,
        snapshots: [],
      }
      
      vi.mocked(flowApi.getFlowDefinitionDetail).mockResolvedValue({
        data: mockDetail,
      } as any)
      
      await store.loadDefinition(1)
      
      expect(store.nodes).toHaveLength(3)
      expect(store.nodes[0].type).toBe('start')
      expect(store.nodes[1].type).toBe('user')
      expect(store.nodes[2].type).toBe('end')
      expect(store.dirty).toBe(true)
    })

    it('应该设置加载状态', async () => {
      const store = useFlowDraftStore()
      
      const mockDetail: FlowDefinitionDetailResponse = {
        definition: {
          id: 1,
          form_id: 100,
          name: '流程',
          version: 1,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
        draft: null,
        snapshots: [],
      }
      
      vi.mocked(flowApi.getFlowDefinitionDetail).mockResolvedValue({
        data: mockDetail,
      } as any)
      
      const promise = store.loadDefinition(1)
      expect(store.loading).toBe(true)
      
      await promise
      expect(store.loading).toBe(false)
    })
  })

  describe('保存草稿', () => {
    it('应该保存草稿到远程', async () => {
      const store = useFlowDraftStore()
      store.flowDefinitionId = 1
      
      store.addNode('start')
      store.addNode('user')
      store.addNode('end')
      
      const mockResponse: FlowDraftResponse = {
        flow_definition_id: 1,
        version: 2,
        nodes: store.nodes,
        routes: store.routes,
        nodes_graph: store.nodesGraph,
      }
      
      vi.mocked(flowApi.saveFlowDraft).mockResolvedValue({
        data: mockResponse,
      } as any)
      
      const result = await store.saveDraftRemote()
      
      expect(store.saving).toBe(false)
      expect(store.version).toBe(2)
      expect(store.dirty).toBe(false)
      expect(store.lastSavedAt).toBeDefined()
      expect(result).toEqual(mockResponse)
    })

    it('应该设置保存状态', async () => {
      const store = useFlowDraftStore()
      store.flowDefinitionId = 1
      
      store.addNode('start')
      
      const mockResponse: FlowDraftResponse = {
        flow_definition_id: 1,
        version: 2,
        nodes: store.nodes,
        routes: store.routes,
        nodes_graph: store.nodesGraph,
      }
      
      vi.mocked(flowApi.saveFlowDraft).mockResolvedValue({
        data: mockResponse,
      } as any)
      
      const promise = store.saveDraftRemote()
      expect(store.saving).toBe(true)
      
      await promise
      expect(store.saving).toBe(false)
    })

    it('未加载定义时不应该保存', async () => {
      const store = useFlowDraftStore()
      
      await expect(store.saveDraftRemote()).rejects.toThrow('请先加载流程定义')
    })
  })

  describe('发布流程', () => {
    it('应该发布当前草稿', async () => {
      const store = useFlowDraftStore()
      store.flowDefinitionId = 1
      
      store.addNode('start')
      store.addNode('user')
      store.addNode('end')
      
      const mockSnapshot = {
        data: {
          id: 1,
          flow_definition_id: 1,
          version_tag: 'v1.0',
          rules_payload: {},
          created_at: '2024-01-01',
        },
      }
      
      vi.mocked(flowApi.publishFlow).mockResolvedValue(mockSnapshot as any)
      
      const result = await store.publishCurrentDraft({
        changelog: '初始版本',
        versionTag: 'v1.0',
      })
      
      expect(store.publishing).toBe(false)
      expect(store.dirty).toBe(false)
      expect(store.lastPublishedAt).toBeDefined()
      expect(result).toEqual(mockSnapshot.data)
    })

    it('应该设置发布状态', async () => {
      const store = useFlowDraftStore()
      store.flowDefinitionId = 1
      
      store.addNode('start')
      
      const mockSnapshot = {
        data: {
          id: 1,
          flow_definition_id: 1,
          version_tag: 'v1.0',
          rules_payload: {},
          created_at: '2024-01-01',
        },
      }
      
      vi.mocked(flowApi.publishFlow).mockResolvedValue(mockSnapshot as any)
      
      const promise = store.publishCurrentDraft()
      expect(store.publishing).toBe(true)
      
      await promise
      expect(store.publishing).toBe(false)
    })
  })

  describe('完整工作流', () => {
    it('应该完成加载-编辑-保存流程', async () => {
      const store = useFlowDraftStore()
      
      // 1. 加载定义
      const mockDetail: FlowDefinitionDetailResponse = {
        definition: {
          id: 1,
          form_id: 100,
          name: '招待费申请',
          version: 1,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
        draft: null,
        snapshots: [],
      }
      
      vi.mocked(flowApi.getFlowDefinitionDetail).mockResolvedValue({
        data: mockDetail,
      } as any)
      
      await store.loadDefinition(1)
      expect(store.definitionLoaded).toBe(true)
      expect(store.dirty).toBe(true)
      
      // 2. 编辑流程
      const startNodeKey = store.nodes[0].temp_id!
      store.updateNode(startNodeKey, { name: '开始审批' })
      expect(store.dirty).toBe(true)
      
      // 3. 保存草稿
      const mockSaveResponse: FlowDraftResponse = {
        flow_definition_id: 1,
        version: 2,
        nodes: store.nodes,
        routes: store.routes,
        nodes_graph: store.nodesGraph,
      }
      
      vi.mocked(flowApi.saveFlowDraft).mockResolvedValue({
        data: mockSaveResponse,
      } as any)
      
      await store.saveDraftRemote()
      expect(store.dirty).toBe(false)
      expect(store.version).toBe(2)
    })

    it('应该完成加载-编辑-发布流程', async () => {
      const store = useFlowDraftStore()
      
      // 1. 加载定义
      const mockDetail: FlowDefinitionDetailResponse = {
        definition: {
          id: 1,
          form_id: 100,
          name: '招待费申请',
          version: 1,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
        draft: null,
        snapshots: [],
      }
      
      vi.mocked(flowApi.getFlowDefinitionDetail).mockResolvedValue({
        data: mockDetail,
      } as any)
      
      await store.loadDefinition(1)
      
      // 2. 编辑流程
      const approvalNodeKey = store.nodes[1].temp_id!
      store.updateNode(approvalNodeKey, { name: '部门经理审批' })
      
      // 3. 发布流程
      const mockSnapshot = {
        data: {
          id: 1,
          flow_definition_id: 1,
          version_tag: 'v1.0',
          rules_payload: {},
          created_at: '2024-01-01',
        },
      }
      
      vi.mocked(flowApi.publishFlow).mockResolvedValue(mockSnapshot as any)
      
      await store.publishCurrentDraft({
        changelog: '初始版本',
        versionTag: 'v1.0',
      })
      
      expect(store.dirty).toBe(false)
      expect(store.lastPublishedAt).toBeDefined()
    })
  })

  describe('多节点编辑场景', () => {
    it('应该支持复杂的节点和路由编辑', async () => {
      const store = useFlowDraftStore()
      
      // 构建复杂流程
      store.addNode('start')
      store.addNode('user')
      store.addNode('condition')
      store.addNode('user')
      store.addNode('end')
      
      const keys = store.nodes.map(n => n.temp_id!)
      
      // 添加路由
      store.addRoute({
        from_node_key: keys[0],
        to_node_key: keys[1],
        priority: 1,
        is_default: true,
      })
      store.addRoute({
        from_node_key: keys[1],
        to_node_key: keys[2],
        priority: 1,
        is_default: true,
      })
      store.addRoute({
        from_node_key: keys[2],
        to_node_key: keys[3],
        priority: 1,
        is_default: false,
        condition: { '==': [{ var: 'amount' }, 1000] },
      })
      store.addRoute({
        from_node_key: keys[2],
        to_node_key: keys[4],
        priority: 2,
        is_default: true,
      })
      
      expect(store.nodes).toHaveLength(5)
      expect(store.routes).toHaveLength(4)
      
      // 编辑节点
      store.updateNode(keys[1], { name: '部门经理' })
      store.updateNode(keys[3], { name: '财务审批' })
      
      expect(store.nodes[1].name).toBe('部门经理')
      expect(store.nodes[3].name).toBe('财务审批')
      
      // 删除中间节点
      store.removeNode(keys[2])
      
      expect(store.nodes).toHaveLength(4)
      expect(store.routes).toHaveLength(1)
    })

    it('应该支持节点位置调整', async () => {
      const store = useFlowDraftStore()
      
      store.addNode('start')
      store.addNode('user')
      store.addNode('end')
      
      const keys = store.nodes.map(n => n.temp_id!)
      
      // 调整位置
      store.updateNodePosition(keys[0], { x: 100, y: 100 })
      store.updateNodePosition(keys[1], { x: 300, y: 100 })
      store.updateNodePosition(keys[2], { x: 500, y: 100 })
      
      expect(store.nodesGraph[keys[0]]).toEqual({ x: 100, y: 100 })
      expect(store.nodesGraph[keys[1]]).toEqual({ x: 300, y: 100 })
      expect(store.nodesGraph[keys[2]]).toEqual({ x: 500, y: 100 })
    })
  })
})
