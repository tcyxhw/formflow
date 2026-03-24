import { describe, it, expect, beforeEach } from 'vitest'
import {
  copyMultipleNodes,
  pasteNodes,
  canPaste,
  clearClipboard,
  cloneNodeConfigs,
  remapNodeIds,
  remapRouteNodeReferences
} from '../nodeClipboard'
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

describe('nodeClipboard 集成测试', () => {
  let nodes: FlowNodeConfig[]
  let routes: FlowRouteConfig[]

  beforeEach(() => {
    clearClipboard()

    // 创建一个简单的流程：开始 -> 审批 -> 结束
    nodes = [
      {
        id: 1,
        temp_id: 'start_node',
        name: '开始',
        type: 'start',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      },
      {
        id: 2,
        temp_id: 'approval_node',
        name: '审批',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      },
      {
        id: 3,
        temp_id: 'end_node',
        name: '结束',
        type: 'end',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }
    ]

    routes = [
      {
        id: 1,
        temp_id: 'route_1',
        from_node_key: 'start_node',
        to_node_key: 'approval_node',
        priority: 1,
        is_default: true
      },
      {
        id: 2,
        temp_id: 'route_2',
        from_node_key: 'approval_node',
        to_node_key: 'end_node',
        priority: 1,
        is_default: true
      }
    ]
  })

  describe('完整工作流', () => {
    it('应该支持完整的复制粘贴流程', () => {
      // 1. 复制审批节点
      const approvalNode = nodes.find(n => n.type === 'user')!
      copyMultipleNodes([approvalNode], [])

      // 2. 验证可以粘贴
      expect(canPaste()).toBe(true)

      // 3. 粘贴节点
      const result = pasteNodes()
      expect(result).not.toBeNull()
      expect(result?.nodes.length).toBe(1)

      // 4. 验证粘贴的节点配置正确
      expect(result?.nodes[0].name).toBe('审批')
      expect(result?.nodes[0].type).toBe('user')
      expect(result?.nodes[0].assignee_type).toBe('role')

      // 5. 验证生成了新的 ID
      expect(result?.nodes[0].temp_id).not.toBe('approval_node')
    })

    it('应该支持复制整个流程', () => {
      // 1. 复制所有节点和路由
      copyMultipleNodes(nodes, routes)

      // 2. 粘贴
      const result = pasteNodes()

      // 3. 验证节点数量
      expect(result?.nodes.length).toBe(3)

      // 4. 验证路由数量
      expect(result?.routes.length).toBe(2)

      // 5. 验证路由连接正确
      const startNode = result?.nodes.find(n => n.type === 'start')
      const approvalNode = result?.nodes.find(n => n.type === 'user')
      const endNode = result?.nodes.find(n => n.type === 'end')

      const firstRoute = result?.routes[0]
      expect(firstRoute?.from_node_key).toBe(startNode?.temp_id)
      expect(firstRoute?.to_node_key).toBe(approvalNode?.temp_id)
    })

    it('应该支持部分复制粘贴', () => {
      // 1. 只复制审批节点和相关路由
      const approvalNode = nodes.find(n => n.type === 'user')!
      const relatedRoutes = routes.filter(
        r => r.from_node_key === 'approval_node' || r.to_node_key === 'approval_node'
      )

      copyMultipleNodes([approvalNode], relatedRoutes)

      // 2. 粘贴
      const result = pasteNodes()

      // 3. 验证
      expect(result?.nodes.length).toBe(1)
      expect(result?.routes.length).toBe(2)
    })
  })

  describe('复杂场景', () => {
    it('应该支持多次复制粘贴', () => {
      // 第一次复制粘贴
      copyMultipleNodes(nodes, routes)
      const result1 = pasteNodes()

      // 第二次复制粘贴
      copyMultipleNodes(result1!.nodes, result1!.routes)
      const result2 = pasteNodes()

      // 验证每次粘贴都生成了新的 ID
      expect(result1?.nodes[0].temp_id).not.toBe(nodes[0].temp_id)
      expect(result2?.nodes[0].temp_id).not.toBe(result1?.nodes[0].temp_id)
    })

    it('应该支持复制粘贴后修改再复制', () => {
      // 1. 复制粘贴
      copyMultipleNodes(nodes, routes)
      const result1 = pasteNodes()

      // 2. 修改粘贴的节点
      result1!.nodes[0].name = '修改后的审批'

      // 3. 再次复制粘贴
      copyMultipleNodes(result1!.nodes, result1!.routes)
      const result2 = pasteNodes()

      // 4. 验证修改被保留
      expect(result2?.nodes[0].name).toBe('修改后的审批')
    })

    it('应该支持条件分支节点的复制', () => {
      // 创建条件分支节点
      const conditionNode: FlowNodeConfig = {
        id: 4,
        temp_id: 'condition_node',
        name: '条件分支',
        type: 'condition',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        condition_branches: {
          branches: [
            {
              priority: 1,
              label: '金额 > 1000',
              condition: { '>': [{ var: 'amount' }, 1000] },
              target_node_id: 2
            }
          ],
          default_target_node_id: 3
        },
        metadata: {}
      }

      // 复制条件分支节点
      copyMultipleNodes([conditionNode], [])
      const result = pasteNodes()

      // 验证条件分支配置被保留
      expect(result?.nodes[0].condition_branches).toBeDefined()
      expect(result?.nodes[0].condition_branches?.branches.length).toBe(1)
    })

    it('应该支持自动节点的复制', () => {
      // 创建自动节点
      const autoNode: FlowNodeConfig = {
        id: 5,
        temp_id: 'auto_node',
        name: '自动通知',
        type: 'auto',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {
          action: 'send_email',
          template: 'approval_notification'
        }
      }

      // 复制自动节点
      copyMultipleNodes([autoNode], [])
      const result = pasteNodes()

      // 验证元数据被保留
      expect(result?.nodes[0].metadata).toEqual(autoNode.metadata)
    })
  })

  describe('路由处理', () => {
    it('应该正确处理路由中的节点引用', () => {
      // 复制包含路由的节点
      const nodesToCopy = nodes.slice(0, 2) // 开始和审批
      const routesToCopy = routes.slice(0, 1) // 开始到审批的路由

      copyMultipleNodes(nodesToCopy, routesToCopy)
      const result = pasteNodes()

      // 验证路由中的节点引用被正确更新
      const startNode = result?.nodes.find(n => n.type === 'start')
      const approvalNode = result?.nodes.find(n => n.type === 'user')

      expect(result?.routes[0].from_node_key).toBe(startNode?.temp_id)
      expect(result?.routes[0].to_node_key).toBe(approvalNode?.temp_id)
    })

    it('应该保留路由的优先级和其他属性', () => {
      const routeWithPriority: FlowRouteConfig = {
        id: 3,
        temp_id: 'route_3',
        from_node_key: 'approval_node',
        to_node_key: 'end_node',
        priority: 5,
        is_default: false,
        condition: { '>': [{ var: 'amount' }, 1000] }
      }

      copyMultipleNodes(nodes, [routeWithPriority])
      const result = pasteNodes()

      expect(result?.routes[0].priority).toBe(5)
      expect(result?.routes[0].is_default).toBe(false)
      expect(result?.routes[0].condition).toEqual(routeWithPriority.condition)
    })
  })

  describe('克隆和重新映射', () => {
    it('应该能够克隆节点配置', () => {
      const cloned = cloneNodeConfigs(nodes)

      expect(cloned.length).toBe(3)
      cloned.forEach((config, index) => {
        expect(config.name).toBe(nodes[index].name)
        expect(config.type).toBe(nodes[index].type)
        expect(config.id).toBeUndefined()
        expect(config.temp_id).toBeUndefined()
      })
    })

    it('应该能够重新映射节点 ID', () => {
      const idMap = {
        'start_node': 'new_start',
        'approval_node': 'new_approval',
        'end_node': 'new_end'
      }

      const remapped = remapNodeIds(nodes, idMap)

      expect(remapped[0].temp_id).toBe('new_start')
      expect(remapped[1].temp_id).toBe('new_approval')
      expect(remapped[2].temp_id).toBe('new_end')
    })

    it('应该能够重新映射路由节点引用', () => {
      const idMap = {
        'start_node': 'new_start',
        'approval_node': 'new_approval',
        'end_node': 'new_end'
      }

      const remapped = remapRouteNodeReferences(routes, idMap)

      expect(remapped[0].from_node_key).toBe('new_start')
      expect(remapped[0].to_node_key).toBe('new_approval')
      expect(remapped[1].from_node_key).toBe('new_approval')
      expect(remapped[1].to_node_key).toBe('new_end')
    })
  })

  describe('性能测试', () => {
    it('应该能够快速复制大量节点', () => {
      // 创建 100 个节点
      const largeNodeList = Array.from({ length: 100 }, (_, i) => ({
        ...nodes[0],
        id: i,
        temp_id: `node_${i}`
      }))

      const startTime = performance.now()
      copyMultipleNodes(largeNodeList, [])
      const endTime = performance.now()

      // 应该在 100ms 内完成
      expect(endTime - startTime).toBeLessThan(100)
    })

    it('应该能够快速粘贴大量节点', () => {
      const largeNodeList = Array.from({ length: 100 }, (_, i) => ({
        ...nodes[0],
        id: i,
        temp_id: `node_${i}`
      }))

      copyMultipleNodes(largeNodeList, [])

      const startTime = performance.now()
      pasteNodes()
      const endTime = performance.now()

      // 应该在 100ms 内完成
      expect(endTime - startTime).toBeLessThan(100)
    })
  })

  describe('边界情况', () => {
    it('应该能够处理循环路由', () => {
      const circularRoutes: FlowRouteConfig[] = [
        {
          id: 1,
          temp_id: 'route_1',
          from_node_key: 'node_1',
          to_node_key: 'node_2',
          priority: 1,
          is_default: false
        },
        {
          id: 2,
          temp_id: 'route_2',
          from_node_key: 'node_2',
          to_node_key: 'node_1',
          priority: 1,
          is_default: false
        }
      ]

      const circularNodes = [
        { ...nodes[0], temp_id: 'node_1' },
        { ...nodes[1], temp_id: 'node_2' }
      ]

      copyMultipleNodes(circularNodes, circularRoutes)
      const result = pasteNodes()

      expect(result?.routes.length).toBe(2)
      // 验证循环关系被保留
      expect(result?.routes[0].to_node_key).toBe(result?.routes[1].from_node_key)
      expect(result?.routes[1].to_node_key).toBe(result?.routes[0].from_node_key)
    })

    it('应该能够处理孤立节点', () => {
      const isolatedNode = { ...nodes[0], temp_id: 'isolated' }
      copyMultipleNodes([isolatedNode], [])
      const result = pasteNodes()

      expect(result?.nodes.length).toBe(1)
      expect(result?.routes.length).toBe(0)
    })
  })
})
