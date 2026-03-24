import { describe, it, expect, beforeEach } from 'vitest'
import {
  nodeClipboard,
  copySingleNode,
  copyMultipleNodes,
  pasteNodes,
  canPaste,
  clearClipboard,
  cloneNodeConfig,
  cloneRouteConfig,
  cloneNodeConfigs,
  cloneRouteConfigs,
  generateNodeTempId,
  generateRouteTempId,
  remapNodeIds,
  remapRouteNodeReferences
} from '../nodeClipboard'
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

describe('nodeClipboard', () => {
  let mockNode: FlowNodeConfig
  let mockRoute: FlowRouteConfig

  beforeEach(() => {
    clearClipboard()

    mockNode = {
      id: 1,
      temp_id: 'node_1',
      name: '测试节点',
      type: 'user',
      assignee_type: 'role',
      approve_policy: 'all',
      route_mode: 'exclusive',
      allow_delegate: true,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_START',
      metadata: {}
    }

    mockRoute = {
      id: 1,
      temp_id: 'route_1',
      from_node_key: 'node_1',
      to_node_key: 'node_2',
      priority: 1,
      is_default: false
    }
  })

  describe('复制功能', () => {
    it('应该能够复制单个节点', () => {
      copySingleNode(mockNode)
      expect(canPaste()).toBe(true)
    })

    it('应该能够复制多个节点', () => {
      const nodes = [mockNode, { ...mockNode, id: 2, temp_id: 'node_2' }]
      copyMultipleNodes(nodes, [])
      expect(canPaste()).toBe(true)
    })

    it('应该能够复制节点和路由', () => {
      copyMultipleNodes([mockNode], [mockRoute])
      expect(canPaste()).toBe(true)
    })

    it('复制应该创建深拷贝', () => {
      copySingleNode(mockNode)
      const data = nodeClipboard.getData()
      expect(data?.nodes[0]).not.toBe(mockNode)
      expect(data?.nodes[0]).toEqual(mockNode)
    })

    it('复制应该记录时间戳', () => {
      const beforeTime = Date.now()
      copySingleNode(mockNode)
      const afterTime = Date.now()

      const data = nodeClipboard.getData()
      expect(data?.timestamp).toBeGreaterThanOrEqual(beforeTime)
      expect(data?.timestamp).toBeLessThanOrEqual(afterTime)
    })
  })

  describe('粘贴功能', () => {
    it('应该能够粘贴节点', () => {
      copySingleNode(mockNode)
      const result = pasteNodes()

      expect(result).not.toBeNull()
      expect(result?.nodes.length).toBe(1)
    })

    it('粘贴应该生成新的 temp_id', () => {
      copySingleNode(mockNode)
      const result = pasteNodes()

      expect(result?.nodes[0].temp_id).not.toBe(mockNode.temp_id)
      expect(result?.nodes[0].temp_id).toMatch(/^node_\d+_/)
    })

    it('粘贴应该清除 id 字段', () => {
      copySingleNode(mockNode)
      const result = pasteNodes()

      expect(result?.nodes[0].id).toBeUndefined()
    })

    it('粘贴应该保留节点配置', () => {
      copySingleNode(mockNode)
      const result = pasteNodes()

      expect(result?.nodes[0].name).toBe(mockNode.name)
      expect(result?.nodes[0].type).toBe(mockNode.type)
      expect(result?.nodes[0].approve_policy).toBe(mockNode.approve_policy)
    })

    it('粘贴多个节点应该生成不同的 temp_id', () => {
      const nodes = [mockNode, { ...mockNode, id: 2, temp_id: 'node_2' }]
      copyMultipleNodes(nodes, [])
      const result = pasteNodes()

      expect(result?.nodes[0].temp_id).not.toBe(result?.nodes[1].temp_id)
    })

    it('粘贴应该更新路由中的节点引用', () => {
      const nodes = [
        { ...mockNode, temp_id: 'node_1' },
        { ...mockNode, id: 2, temp_id: 'node_2' }
      ]
      const routes = [
        { ...mockRoute, from_node_key: 'node_1', to_node_key: 'node_2' }
      ]

      copyMultipleNodes(nodes, routes)
      const result = pasteNodes()

      expect(result?.routes[0].from_node_key).not.toBe('node_1')
      expect(result?.routes[0].to_node_key).not.toBe('node_2')
      expect(result?.routes[0].from_node_key).toMatch(/^node_\d+_/)
      expect(result?.routes[0].to_node_key).toMatch(/^node_\d+_/)
    })

    it('粘贴空剪贴板应该返回 null', () => {
      clearClipboard()
      const result = pasteNodes()
      expect(result).toBeNull()
    })
  })

  describe('剪贴板管理', () => {
    it('应该能够检查剪贴板是否有数据', () => {
      expect(canPaste()).toBe(false)
      copySingleNode(mockNode)
      expect(canPaste()).toBe(true)
    })

    it('应该能够清空剪贴板', () => {
      copySingleNode(mockNode)
      expect(canPaste()).toBe(true)
      clearClipboard()
      expect(canPaste()).toBe(false)
    })

    it('应该能够获取剪贴板数据', () => {
      copySingleNode(mockNode)
      const data = nodeClipboard.getData()
      expect(data).not.toBeNull()
      expect(data?.nodes.length).toBe(1)
    })

    it('清空后获取数据应该返回 null', () => {
      copySingleNode(mockNode)
      clearClipboard()
      const data = nodeClipboard.getData()
      expect(data).toBeNull()
    })
  })

  describe('节点配置克隆', () => {
    it('应该能够克隆单个节点配置', () => {
      const cloned = cloneNodeConfig(mockNode)
      expect(cloned).not.toBe(mockNode)
      expect(cloned.name).toBe(mockNode.name)
      expect(cloned.id).toBeUndefined()
      expect(cloned.temp_id).toBeUndefined()
    })

    it('应该能够克隆多个节点配置', () => {
      const nodes = [mockNode, { ...mockNode, id: 2 }]
      const cloned = cloneNodeConfigs(nodes)

      expect(cloned.length).toBe(2)
      expect(cloned[0].id).toBeUndefined()
      expect(cloned[1].id).toBeUndefined()
    })

    it('克隆应该保留所有配置字段', () => {
      const cloned = cloneNodeConfig(mockNode)
      expect(cloned.name).toBe(mockNode.name)
      expect(cloned.type).toBe(mockNode.type)
      expect(cloned.assignee_type).toBe(mockNode.assignee_type)
      expect(cloned.approve_policy).toBe(mockNode.approve_policy)
    })
  })

  describe('路由配置克隆', () => {
    it('应该能够克隆单个路由配置', () => {
      const cloned = cloneRouteConfig(mockRoute)
      expect(cloned).not.toBe(mockRoute)
      expect(cloned.from_node_key).toBe(mockRoute.from_node_key)
      expect(cloned.id).toBeUndefined()
      expect(cloned.temp_id).toBeUndefined()
    })

    it('应该能够克隆多个路由配置', () => {
      const routes = [mockRoute, { ...mockRoute, id: 2 }]
      const cloned = cloneRouteConfigs(routes)

      expect(cloned.length).toBe(2)
      expect(cloned[0].id).toBeUndefined()
      expect(cloned[1].id).toBeUndefined()
    })
  })

  describe('ID 生成', () => {
    it('应该能够生成节点 temp_id', () => {
      const id = generateNodeTempId()
      expect(id).toMatch(/^node_\d+_/)
    })

    it('应该能够生成路由 temp_id', () => {
      const id = generateRouteTempId()
      expect(id).toMatch(/^route_\d+_/)
    })

    it('生成的 ID 应该是唯一的', () => {
      const id1 = generateNodeTempId()
      const id2 = generateNodeTempId()
      expect(id1).not.toBe(id2)
    })
  })

  describe('ID 重新映射', () => {
    it('应该能够重新映射节点 ID', () => {
      const nodes = [
        { ...mockNode, temp_id: 'node_1' },
        { ...mockNode, id: 2, temp_id: 'node_2' }
      ]
      const idMap = {
        'node_1': 'new_node_1',
        'node_2': 'new_node_2'
      }

      const remapped = remapNodeIds(nodes, idMap)
      expect(remapped[0].temp_id).toBe('new_node_1')
      expect(remapped[1].temp_id).toBe('new_node_2')
    })

    it('应该能够重新映射路由节点引用', () => {
      const routes = [
        { ...mockRoute, from_node_key: 'node_1', to_node_key: 'node_2' }
      ]
      const idMap = {
        'node_1': 'new_node_1',
        'node_2': 'new_node_2'
      }

      const remapped = remapRouteNodeReferences(routes, idMap)
      expect(remapped[0].from_node_key).toBe('new_node_1')
      expect(remapped[0].to_node_key).toBe('new_node_2')
    })

    it('未映射的 ID 应该保持不变', () => {
      const nodes = [{ ...mockNode, temp_id: 'node_1' }]
      const idMap = { 'node_2': 'new_node_2' }

      const remapped = remapNodeIds(nodes, idMap)
      expect(remapped[0].temp_id).toBe('node_1')
    })
  })

  describe('多次复制粘贴', () => {
    it('应该能够多次复制粘贴', () => {
      copySingleNode(mockNode)
      const result1 = pasteNodes()

      copySingleNode(result1!.nodes[0])
      const result2 = pasteNodes()

      expect(result2?.nodes[0].temp_id).not.toBe(result1?.nodes[0].temp_id)
    })

    it('应该能够复制粘贴后再复制', () => {
      copySingleNode(mockNode)
      const result1 = pasteNodes()

      copyMultipleNodes(result1!.nodes, [])
      const result2 = pasteNodes()

      expect(result2?.nodes[0].name).toBe(mockNode.name)
    })
  })

  describe('边界情况', () => {
    it('应该能够处理空节点列表', () => {
      copyMultipleNodes([], [])
      expect(canPaste()).toBe(true)
      const result = pasteNodes()
      expect(result?.nodes.length).toBe(0)
    })

    it('应该能够处理空路由列表', () => {
      copyMultipleNodes([mockNode], [])
      const result = pasteNodes()
      expect(result?.routes.length).toBe(0)
    })

    it('应该能够处理节点没有 ID 的情况', () => {
      const nodeWithoutId = { ...mockNode, id: undefined }
      copySingleNode(nodeWithoutId)
      const result = pasteNodes()
      expect(result?.nodes[0].id).toBeUndefined()
    })

    it('应该能够处理节点没有 temp_id 的情况', () => {
      const nodeWithoutTempId = { ...mockNode, temp_id: undefined }
      copySingleNode(nodeWithoutTempId)
      const result = pasteNodes()
      expect(result?.nodes[0].temp_id).toBeDefined()
    })
  })
})
