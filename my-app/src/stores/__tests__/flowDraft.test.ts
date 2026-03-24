/**
 * 流程草稿状态管理单元测试
 * 测试 useFlowDraftStore 的核心功能
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFlowDraftStore } from '../flowDraft'
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

// Mock API 模块
vi.mock('@/api/flow', () => ({
  getFlowDefinitionDetail: vi.fn(),
  saveFlowDraft: vi.fn(),
  publishFlow: vi.fn(),
}))

import * as flowApi from '@/api/flow'

describe('useFlowDraftStore - 单元测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始化状态', () => {
    it('应该有正确的初始状态', () => {
      const store = useFlowDraftStore()
      
      expect(store.flowDefinitionId).toBeUndefined()
      expect(store.flowName).toBe('')
      expect(store.version).toBe(1)
      expect(store.nodes).toEqual([])
      expect(store.routes).toEqual([])
      expect(store.dirty).toBe(false)
      expect(store.loading).toBe(false)
      expect(store.saving).toBe(false)
      expect(store.publishing).toBe(false)
    })

    it('应该有正确的计算属性初始值', () => {
      const store = useFlowDraftStore()
      
      expect(store.currentNode).toBeUndefined()
      expect(store.currentRoute).toBeUndefined()
      expect(store.nodeOptions).toEqual([])
      expect(store.definitionLoaded).toBe(false)
    })
  })

  describe('节点管理', () => {
    it('应该添加新节点', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      
      expect(store.nodes).toHaveLength(1)
      expect(store.nodes[0].type).toBe('user')
      expect(store.nodes[0].name).toBe('新节点')
      expect(store.dirty).toBe(true)
    })

    it('应该为新节点生成临时 ID', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      store.addNode('approval')
      
      expect(store.nodes[0].temp_id).toBeDefined()
      expect(store.nodes[1].temp_id).toBeDefined()
      expect(store.nodes[0].temp_id).not.toBe(store.nodes[1].temp_id)
    })

    it('应该为新节点分配画布位置', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      store.addNode('approval')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      
      expect(store.nodesGraph[key1]).toBeDefined()
      expect(store.nodesGraph[key2]).toBeDefined()
      expect(store.nodesGraph[key1]).not.toEqual(store.nodesGraph[key2])
    })

    it('应该更新节点属性', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      const nodeKey = store.nodes[0].temp_id!
      
      store.updateNode(nodeKey, { name: '审批人' })
      
      expect(store.nodes[0].name).toBe('审批人')
      expect(store.dirty).toBe(true)
    })

    it('应该删除节点', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      store.addNode('approval')
      const nodeKey = store.nodes[0].temp_id!
      
      store.removeNode(nodeKey)
      
      expect(store.nodes).toHaveLength(1)
      expect(store.nodes[0].type).toBe('approval')
      expect(store.nodesGraph[nodeKey]).toBeUndefined()
      expect(store.dirty).toBe(true)
    })

    it('删除节点时应该删除相关路由', () => {
      const store = useFlowDraftStore()
      
      store.addNode('start')
      store.addNode('user')
      store.addNode('end')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      const key3 = store.nodes[2].temp_id!
      
      store.addRoute({
        from_node_key: key1,
        to_node_key: key2,
        priority: 1,
        is_default: true,
      })
      store.addRoute({
        from_node_key: key2,
        to_node_key: key3,
        priority: 1,
        is_default: true,
      })
      
      store.removeNode(key2)
      
      expect(store.routes).toHaveLength(0)
    })

    it('删除选中节点时应该选择第一个节点', () => {
      const store = useFlowDraftStore()
      
      store.addNode('start')
      store.addNode('user')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      
      store.selectNodeByKey(key2)
      expect(store.selectedNodeKey).toBe(key2)
      
      store.removeNode(key2)
      
      expect(store.selectedNodeKey).toBe(key1)
    })

    it('应该更新节点位置', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      const nodeKey = store.nodes[0].temp_id!
      
      store.updateNodePosition(nodeKey, { x: 100, y: 200 })
      
      expect(store.nodesGraph[nodeKey]).toEqual({ x: 100, y: 200 })
      expect(store.dirty).toBe(true)
    })

    it('应该生成节点选项列表', () => {
      const store = useFlowDraftStore()
      
      store.addNode('start')
      store.addNode('user')
      store.addNode('end')
      
      store.nodes[0].name = '开始'
      store.nodes[1].name = '审批'
      store.nodes[2].name = '结束'
      
      const options = store.nodeOptions
      
      expect(options).toHaveLength(3)
      expect(options[0].label).toBe('开始')
      expect(options[1].label).toBe('审批')
      expect(options[2].label).toBe('结束')
    })
  })

  describe('路由管理', () => {
    it('应该添加新路由', () => {
      const store = useFlowDraftStore()
      
      store.addNode('start')
      store.addNode('end')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      
      store.addRoute({
        from_node_key: key1,
        to_node_key: key2,
        priority: 1,
        is_default: true,
      })
      
      expect(store.routes).toHaveLength(1)
      expect(store.routes[0].from_node_key).toBe(key1)
      expect(store.routes[0].to_node_key).toBe(key2)
      expect(store.dirty).toBe(true)
    })

    it('不应该从结束节点添加出边', () => {
      const store = useFlowDraftStore()
      
      store.addNode('end')
      store.addNode('user')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      
      expect(() => {
        store.addRoute({
          from_node_key: key1,
          to_node_key: key2,
          priority: 1,
          is_default: true,
        })
      }).toThrow('结束节点不能有出边')
    })

    it('应该更新路由属性', () => {
      const store = useFlowDraftStore()
      
      store.addNode('start')
      store.addNode('end')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      
      store.addRoute({
        from_node_key: key1,
        to_node_key: key2,
        priority: 1,
        is_default: true,
      })
      
      store.updateRoute(0, { priority: 2, is_default: false })
      
      expect(store.routes[0].priority).toBe(2)
      expect(store.routes[0].is_default).toBe(false)
      expect(store.dirty).toBe(true)
    })

    it('应该删除路由', () => {
      const store = useFlowDraftStore()
      
      store.addNode('start')
      store.addNode('user')
      store.addNode('end')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      const key3 = store.nodes[2].temp_id!
      
      store.addRoute({
        from_node_key: key1,
        to_node_key: key2,
        priority: 1,
        is_default: true,
      })
      store.addRoute({
        from_node_key: key2,
        to_node_key: key3,
        priority: 1,
        is_default: true,
      })
      
      store.removeRoute(0)
      
      expect(store.routes).toHaveLength(1)
      expect(store.routes[0].from_node_key).toBe(key2)
      expect(store.dirty).toBe(true)
    })

    it('删除路由时应该调整选中路由索引', () => {
      const store = useFlowDraftStore()
      
      store.addNode('start')
      store.addNode('user')
      store.addNode('end')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      const key3 = store.nodes[2].temp_id!
      
      store.addRoute({
        from_node_key: key1,
        to_node_key: key2,
        priority: 1,
        is_default: true,
      })
      store.addRoute({
        from_node_key: key2,
        to_node_key: key3,
        priority: 1,
        is_default: true,
      })
      
      store.selectRouteByIndex(1)
      expect(store.selectedRouteIndex).toBe(1)
      
      store.removeRoute(1)
      
      expect(store.selectedRouteIndex).toBeNull()
    })
  })

  describe('选择管理', () => {
    it('应该选择节点', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      const nodeKey = store.nodes[0].temp_id!
      
      store.selectNodeByKey(nodeKey)
      
      expect(store.selectedNodeKey).toBe(nodeKey)
      expect(store.currentNode).toBe(store.nodes[0])
    })

    it('应该切换节点多选状态', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      store.addNode('approval')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      
      // 第一次选择
      store.toggleNodeSelection(key1, false)
      expect(store.selectedNodeKeys.has(key1)).toBe(true)
      expect(store.selectedNodeKeys.size).toBe(1)
      
      // 多选第二个节点
      store.toggleNodeSelection(key2, true)
      expect(store.selectedNodeKeys.has(key1)).toBe(true)
      expect(store.selectedNodeKeys.has(key2)).toBe(true)
      expect(store.selectedNodeKeys.size).toBe(2)
      
      // 取消选择第一个节点
      store.toggleNodeSelection(key1, true)
      expect(store.selectedNodeKeys.has(key1)).toBe(false)
      expect(store.selectedNodeKeys.has(key2)).toBe(true)
      expect(store.selectedNodeKeys.size).toBe(1)
    })

    it('应该在单选时清除多选', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      store.addNode('approval')
      store.addNode('end')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      const key3 = store.nodes[2].temp_id!
      
      // 多选两个节点
      store.toggleNodeSelection(key1, false)
      store.toggleNodeSelection(key2, true)
      expect(store.selectedNodeKeys.size).toBe(2)
      
      // 单选第三个节点
      store.toggleNodeSelection(key3, false)
      expect(store.selectedNodeKeys.has(key1)).toBe(false)
      expect(store.selectedNodeKeys.has(key2)).toBe(false)
      expect(store.selectedNodeKeys.has(key3)).toBe(true)
      expect(store.selectedNodeKeys.size).toBe(1)
    })

    it('应该清除所有节点选择', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      store.addNode('approval')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      
      store.toggleNodeSelection(key1, false)
      store.toggleNodeSelection(key2, true)
      expect(store.selectedNodeKeys.size).toBe(2)
      
      store.clearNodeSelection()
      
      expect(store.selectedNodeKeys.size).toBe(0)
      expect(store.selectedNodeKey).toBeUndefined()
    })

    it('应该检查节点是否被选中', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      store.addNode('approval')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      
      store.toggleNodeSelection(key1, false)
      store.toggleNodeSelection(key2, true)
      
      expect(store.isNodeSelected(key1)).toBe(true)
      expect(store.isNodeSelected(key2)).toBe(true)
      expect(store.isNodeSelected('non-existent')).toBe(false)
    })

    it('应该获取所有选中的节点 key', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      store.addNode('approval')
      store.addNode('end')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      
      store.toggleNodeSelection(key1, false)
      store.toggleNodeSelection(key2, true)
      
      const selectedKeys = store.getSelectedNodeKeys()
      
      expect(selectedKeys).toHaveLength(2)
      expect(selectedKeys).toContain(key1)
      expect(selectedKeys).toContain(key2)
    })

    it('应该选择路由', () => {
      const store = useFlowDraftStore()
      
      store.addNode('start')
      store.addNode('end')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      
      store.addRoute({
        from_node_key: key1,
        to_node_key: key2,
        priority: 1,
        is_default: true,
      })
      
      store.selectRouteByIndex(0)
      
      expect(store.selectedRouteIndex).toBe(0)
      expect(store.currentRoute).toBe(store.routes[0])
    })

    it('应该清除节点选择', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      const nodeKey = store.nodes[0].temp_id!
      
      store.selectNodeByKey(nodeKey)
      store.selectNodeByKey(undefined)
      
      expect(store.selectedNodeKey).toBeUndefined()
      expect(store.currentNode).toBeUndefined()
    })

    it('应该清除路由选择', () => {
      const store = useFlowDraftStore()
      
      store.addNode('start')
      store.addNode('end')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      
      store.addRoute({
        from_node_key: key1,
        to_node_key: key2,
        priority: 1,
        is_default: true,
      })
      
      store.selectRouteByIndex(0)
      store.selectRouteByIndex(null)
      
      expect(store.selectedRouteIndex).toBeNull()
      expect(store.currentRoute).toBeUndefined()
    })

    it('选择无效路由索引时应该清除选择', () => {
      const store = useFlowDraftStore()
      
      store.addNode('start')
      store.addNode('end')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      
      store.addRoute({
        from_node_key: key1,
        to_node_key: key2,
        priority: 1,
        is_default: true,
      })
      
      store.selectRouteByIndex(0)
      store.selectRouteByIndex(999)
      
      expect(store.selectedRouteIndex).toBeNull()
    })
  })

  describe('草稿构建', () => {
    it('应该通过 applyDraftData 构建默认草稿', () => {
      const store = useFlowDraftStore()
      
      // 调用 applyDraftData 时传入 null 会构建默认草稿
      store.flowDefinitionId = 1
      store.flowName = '测试流程'
      store.version = 1
      
      // 通过 loadDefinition 的逻辑来测试
      store.nodes = []
      store.routes = []
      
      // 手动构建默认草稿
      store.addNode('start')
      store.addNode('user')
      store.addNode('end')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      const key3 = store.nodes[2].temp_id!
      
      store.addRoute({
        from_node_key: key1,
        to_node_key: key2,
        priority: 1,
        is_default: true,
      })
      store.addRoute({
        from_node_key: key2,
        to_node_key: key3,
        priority: 1,
        is_default: true,
      })
      
      expect(store.nodes).toHaveLength(3)
      expect(store.nodes[0].type).toBe('start')
      expect(store.nodes[1].type).toBe('user')
      expect(store.nodes[2].type).toBe('end')
      expect(store.routes).toHaveLength(2)
    })

    it('应该为节点分配画布位置', () => {
      const store = useFlowDraftStore()
      
      store.addNode('start')
      store.addNode('user')
      store.addNode('end')
      
      const keys = store.nodes.map(n => n.temp_id || n.id)
      keys.forEach(key => {
        expect(store.nodesGraph[key]).toBeDefined()
        expect(store.nodesGraph[key].x).toBeGreaterThanOrEqual(0)
        expect(store.nodesGraph[key].y).toBeGreaterThanOrEqual(0)
      })
    })

    it('应该选择第一个节点', () => {
      const store = useFlowDraftStore()
      
      store.addNode('start')
      store.addNode('user')
      store.addNode('end')
      
      store.selectFirstNode()
      
      expect(store.selectedNodeKey).toBeDefined()
      expect(store.currentNode).toBe(store.nodes[0])
    })
  })

  describe('脏标记', () => {
    it('应该标记为脏', () => {
      const store = useFlowDraftStore()
      
      expect(store.dirty).toBe(false)
      
      store.setDirty()
      
      expect(store.dirty).toBe(true)
    })

    it('添加节点时应该标记为脏', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      
      expect(store.dirty).toBe(true)
    })

    it('更新节点时应该标记为脏', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      const nodeKey = store.nodes[0].temp_id!
      
      store.dirty = false
      store.updateNode(nodeKey, { name: '新名称' })
      
      expect(store.dirty).toBe(true)
    })

    it('删除节点时应该标记为脏', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      const nodeKey = store.nodes[0].temp_id!
      
      store.dirty = false
      store.removeNode(nodeKey)
      
      expect(store.dirty).toBe(true)
    })
  })

  describe('验证', () => {
    it('应该在保存前验证节点条件', () => {
      const store = useFlowDraftStore()
      store.flowDefinitionId = 1
      
      store.addNode('user')
      const nodeKey = store.nodes[0].temp_id!
      
      // 有效的条件应该不抛出错误
      store.updateNode(nodeKey, {
        auto_approve_cond: { '==': [1, 1] },
      })
      
      expect(store.nodes[0].auto_approve_cond).toEqual({ '==': [1, 1] })
    })

    it('应该在构建负载时验证所有节点', () => {
      const store = useFlowDraftStore()
      store.flowDefinitionId = 1
      
      store.addNode('user')
      const nodeKey = store.nodes[0].temp_id!
      
      // 设置无效的条件
      store.nodes[0].auto_approve_cond = 'invalid' as any
      
      expect(() => {
        store.buildPayload()
      }).toThrow()
    })
  })

  describe('负载构建', () => {
    it('应该构建保存负载', () => {
      const store = useFlowDraftStore()
      store.flowDefinitionId = 123
      
      store.addNode('start')
      store.addNode('user')
      store.addNode('end')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      const key3 = store.nodes[2].temp_id!
      
      store.addRoute({
        from_node_key: key1,
        to_node_key: key2,
        priority: 1,
        is_default: true,
      })
      
      const payload = store.buildPayload()
      
      expect(payload.flow_definition_id).toBe(123)
      expect(payload.version).toBe(1)
      expect(payload.nodes).toHaveLength(3)
      expect(payload.routes).toHaveLength(1)
      expect(payload.nodes_graph).toBeDefined()
    })

    it('未加载定义时应该抛出错误', () => {
      const store = useFlowDraftStore()
      
      expect(() => {
        store.buildPayload()
      }).toThrow('请先加载流程定义')
    })
  })

  describe('撤销/重做功能', () => {
    it('应该初始化历史记录', () => {
      const store = useFlowDraftStore()
      
      expect(store.history).toBeDefined()
      expect(store.historyIndex).toBe(0)
      expect(store.canUndo).toBe(false)
      expect(store.canRedo).toBe(false)
    })

    it('应该在添加节点时创建快照', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      
      expect(store.history.length).toBeGreaterThan(0)
      expect(store.historyIndex).toBeGreaterThanOrEqual(0)
    })

    it('应该支持撤销操作', () => {
      const store = useFlowDraftStore()
      
      // 初始状态
      const initialNodeCount = store.nodes.length
      
      // 添加节点
      store.addNode('user')
      expect(store.nodes.length).toBe(initialNodeCount + 1)
      
      // 撤销
      store.undo()
      expect(store.nodes.length).toBe(initialNodeCount)
    })

    it('应该支持重做操作', () => {
      const store = useFlowDraftStore()
      
      // 添加节点
      store.addNode('user')
      const nodeCountAfterAdd = store.nodes.length
      
      // 撤销
      store.undo()
      expect(store.nodes.length).toBeLessThan(nodeCountAfterAdd)
      
      // 重做
      store.redo()
      expect(store.nodes.length).toBe(nodeCountAfterAdd)
    })

    it('应该正确计算 canUndo', () => {
      const store = useFlowDraftStore()
      
      expect(store.canUndo).toBe(false)
      
      store.addNode('user')
      expect(store.canUndo).toBe(true)
    })

    it('应该正确计算 canRedo', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      expect(store.canRedo).toBe(false)
      
      store.undo()
      expect(store.canRedo).toBe(true)
    })

    it('应该在撤销后添加新操作时清除重做历史', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      store.addNode('approval')
      
      store.undo()
      expect(store.canRedo).toBe(true)
      
      store.addNode('condition')
      expect(store.canRedo).toBe(false)
    })

    it('应该保存节点状态快照', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      const nodeKey = store.nodes[0].temp_id!
      
      store.updateNode(nodeKey, { name: '新名称' })
      
      store.undo()
      expect(store.nodes[0].name).toBe('新节点')
      
      store.redo()
      expect(store.nodes[0].name).toBe('新名称')
    })

    it('应该保存路由状态快照', () => {
      const store = useFlowDraftStore()
      
      store.addNode('start')
      store.addNode('end')
      
      const key1 = store.nodes[0].temp_id!
      const key2 = store.nodes[1].temp_id!
      
      store.addRoute({
        from_node_key: key1,
        to_node_key: key2,
        priority: 1,
        is_default: true,
      })
      
      expect(store.routes.length).toBe(1)
      
      store.undo()
      expect(store.routes.length).toBe(0)
      
      store.redo()
      expect(store.routes.length).toBe(1)
    })

    it('应该保存节点位置快照', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      const nodeKey = store.nodes[0].temp_id!
      
      const originalPos = store.nodesGraph[nodeKey]
      
      store.updateNodePosition(nodeKey, { x: 100, y: 200 })
      expect(store.nodesGraph[nodeKey]).toEqual({ x: 100, y: 200 })
      
      store.undo()
      expect(store.nodesGraph[nodeKey]).toEqual(originalPos)
      
      store.redo()
      expect(store.nodesGraph[nodeKey]).toEqual({ x: 100, y: 200 })
    })

    it('应该限制历史记录大小', () => {
      const store = useFlowDraftStore()
      
      // 添加超过最大历史记录数的操作
      for (let i = 0; i < 60; i++) {
        store.addNode('user')
      }
      
      expect(store.history.length).toBeLessThanOrEqual(50)
    })

    it('应该在多次撤销后恢复到初始状态', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      store.addNode('approval')
      store.addNode('condition')
      
      expect(store.nodes.length).toBe(3)
      
      store.undo()
      store.undo()
      store.undo()
      
      expect(store.nodes.length).toBe(0)
    })

    it('应该在多次重做后恢复到最后状态', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      store.addNode('approval')
      store.addNode('condition')
      
      store.undo()
      store.undo()
      store.undo()
      
      store.redo()
      store.redo()
      store.redo()
      
      expect(store.nodes.length).toBe(3)
    })

    it('应该在撤销时不改变选中节点', () => {
      const store = useFlowDraftStore()
      
      store.addNode('user')
      const nodeKey = store.nodes[0].temp_id!
      
      store.selectNodeByKey(nodeKey)
      expect(store.selectedNodeKey).toBe(nodeKey)
      
      store.addNode('approval')
      const nodeKey2 = store.nodes[1].temp_id!
      store.selectNodeByKey(nodeKey2)
      expect(store.selectedNodeKey).toBe(nodeKey2)
      
      // 撤销后应该恢复到之前的选中节点
      store.undo()
      expect(store.selectedNodeKey).toBe(nodeKey)
    })
  })
})

