import { describe, it, expect } from 'vitest'
import { autoLayout, getRecommendedDirection, calculateBoundingBox } from '../layoutService'
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

describe('layoutService', () => {
  const mockNodes: FlowNodeConfig[] = [
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
      name: '审批1',
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
      name: '审批2',
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
      id: 4,
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

  const mockRoutes: FlowRouteConfig[] = [
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
    },
    {
      from_node_key: '3',
      to_node_key: '4',
      priority: 1,
      is_default: true
    }
  ]

  describe('autoLayout', () => {
    it('应该返回空对象当节点列表为空', () => {
      const result = autoLayout([], [])
      expect(result).toEqual({})
    })

    it('应该为所有节点返回位置', () => {
      const result = autoLayout(mockNodes, mockRoutes)
      expect(Object.keys(result)).toHaveLength(4)
      expect(result['1']).toBeDefined()
      expect(result['2']).toBeDefined()
      expect(result['3']).toBeDefined()
      expect(result['4']).toBeDefined()
    })

    it('应该返回有效的位置坐标', () => {
      const result = autoLayout(mockNodes, mockRoutes)
      Object.values(result).forEach((position) => {
        expect(position.x).toBeGreaterThanOrEqual(0)
        expect(position.y).toBeGreaterThanOrEqual(0)
        expect(typeof position.x).toBe('number')
        expect(typeof position.y).toBe('number')
      })
    })

    it('应该按层级排列节点', () => {
      const result = autoLayout(mockNodes, mockRoutes)
      // 开始节点应该在最上面
      expect(result['1'].y).toBeLessThan(result['2'].y)
      // 审批节点应该在中间
      expect(result['2'].y).toBeLessThan(result['4'].y)
      // 结束节点应该在最下面
      expect(result['3'].y).toBeLessThan(result['4'].y)
    })

    it('应该处理分支流程', () => {
      const branchRoutes: FlowRouteConfig[] = [
        {
          from_node_key: '1',
          to_node_key: '2',
          priority: 1,
          is_default: true
        },
        {
          from_node_key: '1',
          to_node_key: '3',
          priority: 2,
          is_default: false
        },
        {
          from_node_key: '2',
          to_node_key: '4',
          priority: 1,
          is_default: true
        },
        {
          from_node_key: '3',
          to_node_key: '4',
          priority: 1,
          is_default: true
        }
      ]

      const result = autoLayout(mockNodes, branchRoutes)
      expect(Object.keys(result)).toHaveLength(4)
      // 节点 2 和 3 应该在同一层
      expect(result['2'].y).toBe(result['3'].y)
    })

    it('应该处理循环流程', () => {
      const circularRoutes: FlowRouteConfig[] = [
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
        },
        {
          from_node_key: '3',
          to_node_key: '2',
          priority: 1,
          is_default: false
        },
        {
          from_node_key: '3',
          to_node_key: '4',
          priority: 2,
          is_default: true
        }
      ]

      const result = autoLayout(mockNodes, circularRoutes)
      expect(Object.keys(result)).toHaveLength(4)
    })

    it('应该处理孤立节点', () => {
      const isolatedNode: FlowNodeConfig = {
        id: 5,
        name: '孤立节点',
        type: 'user',
        approve_policy: 'any',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        metadata: {},
        reject_strategy: 'TO_START'
      }

      const result = autoLayout([...mockNodes, isolatedNode], mockRoutes)
      expect(result['5']).toBeDefined()
    })

    it('应该处理临时 ID 的节点', () => {
      const nodeWithTempId: FlowNodeConfig = {
        name: '临时节点',
        type: 'user',
        approve_policy: 'any',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        metadata: {},
        reject_strategy: 'TO_START',
        temp_id: 'tmp-123'
      }

      const result = autoLayout([nodeWithTempId], [])
      expect(result['tmp-123']).toBeDefined()
    })
  })

  describe('getRecommendedDirection', () => {
    it('应该为空节点列表返回 horizontal', () => {
      const direction = getRecommendedDirection([], [])
      expect(direction).toBe('horizontal')
    })

    it('应该为少量节点返回 vertical', () => {
      const direction = getRecommendedDirection(mockNodes.slice(0, 3), mockRoutes)
      expect(direction).toBe('vertical')
    })

    it('应该为大量节点返回 horizontal', () => {
      const manyNodes = Array.from({ length: 10 }, (_, i) => ({
        ...mockNodes[0],
        id: i + 1,
        name: `节点 ${i + 1}`
      }))
      const direction = getRecommendedDirection(manyNodes, [])
      expect(direction).toBe('horizontal')
    })
  })

  describe('calculateBoundingBox', () => {
    it('应该为空位置返回零边界框', () => {
      const bbox = calculateBoundingBox({})
      expect(bbox.minX).toBe(0)
      expect(bbox.minY).toBe(0)
      expect(bbox.maxX).toBe(0)
      expect(bbox.maxY).toBe(0)
      expect(bbox.width).toBe(0)
      expect(bbox.height).toBe(0)
    })

    it('应该计算正确的边界框', () => {
      const positions = {
        '1': { x: 100, y: 100 },
        '2': { x: 300, y: 200 }
      }
      const bbox = calculateBoundingBox(positions)
      expect(bbox.minX).toBe(100)
      expect(bbox.minY).toBe(100)
      expect(bbox.maxX).toBe(480) // 300 + 180 (NODE_WIDTH)
      expect(bbox.maxY).toBe(300) // 200 + 100 (NODE_HEIGHT)
      expect(bbox.width).toBe(380)
      expect(bbox.height).toBe(200)
    })

    it('应该处理单个节点', () => {
      const positions = {
        '1': { x: 50, y: 50 }
      }
      const bbox = calculateBoundingBox(positions)
      expect(bbox.minX).toBe(50)
      expect(bbox.minY).toBe(50)
      expect(bbox.maxX).toBe(230) // 50 + 180
      expect(bbox.maxY).toBe(150) // 50 + 100
    })

    it('应该处理负坐标', () => {
      const positions = {
        '1': { x: -100, y: -50 },
        '2': { x: 100, y: 100 }
      }
      const bbox = calculateBoundingBox(positions)
      expect(bbox.minX).toBe(-100)
      expect(bbox.minY).toBe(-50)
      expect(bbox.maxX).toBe(280) // 100 + 180
      expect(bbox.maxY).toBe(200) // 100 + 100
    })
  })

  describe('集成测试', () => {
    it('应该为复杂流程生成有效布局', () => {
      const complexNodes: FlowNodeConfig[] = [
        { ...mockNodes[0], id: 1 },
        { ...mockNodes[1], id: 2 },
        { ...mockNodes[1], id: 3 },
        { ...mockNodes[1], id: 4 },
        { ...mockNodes[3], id: 5 }
      ]

      const complexRoutes: FlowRouteConfig[] = [
        { from_node_key: '1', to_node_key: '2', priority: 1, is_default: true },
        { from_node_key: '1', to_node_key: '3', priority: 2, is_default: false },
        { from_node_key: '1', to_node_key: '4', priority: 3, is_default: false },
        { from_node_key: '2', to_node_key: '5', priority: 1, is_default: true },
        { from_node_key: '3', to_node_key: '5', priority: 1, is_default: true },
        { from_node_key: '4', to_node_key: '5', priority: 1, is_default: true }
      ]

      const result = autoLayout(complexNodes, complexRoutes)
      const bbox = calculateBoundingBox(result)

      expect(Object.keys(result)).toHaveLength(5)
      expect(bbox.width).toBeGreaterThan(0)
      expect(bbox.height).toBeGreaterThan(0)
    })

    it('应该保持节点之间的相对位置关系', () => {
      const result = autoLayout(mockNodes, mockRoutes)

      // 验证层级关系
      expect(result['1'].y).toBeLessThanOrEqual(result['2'].y)
      expect(result['2'].y).toBeLessThanOrEqual(result['3'].y)
      expect(result['3'].y).toBeLessThanOrEqual(result['4'].y)
    })
  })
})
