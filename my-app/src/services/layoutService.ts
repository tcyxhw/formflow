/**
 * 流程图自动布局服务
 * 使用分层布局算法（Hierarchical Layout）自动排列节点
 */

import type { FlowNodeConfig, FlowNodePosition, FlowRouteConfig } from '@/types/flow'

interface LayoutNode {
  key: string
  node: FlowNodeConfig
  level: number
  position: FlowNodePosition
}

interface LayoutGraph {
  nodes: LayoutNode[]
  edges: Array<{ from: string; to: string }>
}

const LEVEL_HEIGHT = 150 // 层级之间的垂直距离
const NODE_WIDTH = 180
const NODE_HEIGHT = 100
const HORIZONTAL_SPACING = 40 // 同层节点之间的水平距离

/**
 * 构建图的邻接表
 */
function buildAdjacencyList(
  nodes: FlowNodeConfig[],
  routes: FlowRouteConfig[]
): Map<string, string[]> {
  const adjacencyList = new Map<string, string[]>()

  // 初始化所有节点
  nodes.forEach((node) => {
    const key = node.id?.toString() ?? node.temp_id ?? ''
    if (!adjacencyList.has(key)) {
      adjacencyList.set(key, [])
    }
  })

  // 添加边
  routes.forEach((route) => {
    const fromKey = route.from_node_key
    const toKey = route.to_node_key
    if (adjacencyList.has(fromKey)) {
      const neighbors = adjacencyList.get(fromKey)!
      if (!neighbors.includes(toKey)) {
        neighbors.push(toKey)
      }
    }
  })

  return adjacencyList
}

/**
 * 使用 BFS 计算每个节点的层级
 */
function calculateLevels(
  nodes: FlowNodeConfig[],
  adjacencyList: Map<string, string[]>
): Map<string, number> {
  const levels = new Map<string, number>()
  const visited = new Set<string>()
  const queue: Array<{ key: string; level: number }> = []

  // 找到起始节点（入度为 0 的节点）
  const inDegree = new Map<string, number>()
  nodes.forEach((node) => {
    const key = node.id?.toString() ?? node.temp_id ?? ''
    inDegree.set(key, 0)
  })

  adjacencyList.forEach((neighbors) => {
    neighbors.forEach((neighbor) => {
      inDegree.set(neighbor, (inDegree.get(neighbor) ?? 0) + 1)
    })
  })

  // 从入度为 0 的节点开始
  inDegree.forEach((degree, key) => {
    if (degree === 0) {
      queue.push({ key, level: 0 })
      levels.set(key, 0)
    }
  })

  // BFS 遍历
  while (queue.length > 0) {
    const { key, level } = queue.shift()!
    if (visited.has(key)) continue
    visited.add(key)

    const neighbors = adjacencyList.get(key) ?? []
    neighbors.forEach((neighbor) => {
      const neighborLevel = Math.max(level + 1, levels.get(neighbor) ?? 0)
      levels.set(neighbor, neighborLevel)
      if (!visited.has(neighbor)) {
        queue.push({ key: neighbor, level: neighborLevel })
      }
    })
  }

  // 为未访问的节点分配层级
  nodes.forEach((node) => {
    const key = node.id?.toString() ?? node.temp_id ?? ''
    if (!levels.has(key)) {
      levels.set(key, 0)
    }
  })

  return levels
}

/**
 * 计算每层的节点宽度
 */
function calculateLayerWidths(
  nodes: LayoutNode[]
): Map<number, number> {
  const layerWidths = new Map<number, number>()

  nodes.forEach((node) => {
    const width = layerWidths.get(node.level) ?? 0
    layerWidths.set(node.level, width + NODE_WIDTH + HORIZONTAL_SPACING)
  })

  return layerWidths
}

/**
 * 计算节点在每层中的位置
 */
function calculatePositions(
  nodes: LayoutNode[],
  layerWidths: Map<number, number>
): Map<string, FlowNodePosition> {
  const positions = new Map<string, FlowNodePosition>()
  const layerNodeCounts = new Map<number, number>()
  const layerNodeIndices = new Map<string, number>()

  // 按层级分组节点
  const nodesByLevel = new Map<number, LayoutNode[]>()
  nodes.forEach((node) => {
    if (!nodesByLevel.has(node.level)) {
      nodesByLevel.set(node.level, [])
    }
    nodesByLevel.get(node.level)!.push(node)
  })

  // 计算每个节点的位置
  nodesByLevel.forEach((levelNodes, level) => {
    const layerWidth = layerWidths.get(level) ?? 0
    const totalWidth = levelNodes.length * (NODE_WIDTH + HORIZONTAL_SPACING)
    const startX = Math.max(80, (layerWidth - totalWidth) / 2)

    levelNodes.forEach((node, index) => {
      const x = startX + index * (NODE_WIDTH + HORIZONTAL_SPACING)
      const y = 80 + level * LEVEL_HEIGHT
      positions.set(node.key, { x, y })
    })
  })

  return positions
}

/**
 * 自动布局主函数
 * @param nodes 节点列表
 * @param routes 路由列表
 * @returns 节点位置映射
 */
export function autoLayout(
  nodes: FlowNodeConfig[],
  routes: FlowRouteConfig[]
): Record<string, FlowNodePosition> {
  if (nodes.length === 0) {
    return {}
  }

  // 构建邻接表
  const adjacencyList = buildAdjacencyList(nodes, routes)

  // 计算层级
  const levels = calculateLevels(nodes, adjacencyList)

  // 创建布局节点
  const layoutNodes: LayoutNode[] = nodes.map((node) => {
    const key = node.id?.toString() ?? node.temp_id ?? ''
    return {
      key,
      node,
      level: levels.get(key) ?? 0,
      position: { x: 0, y: 0 }
    }
  })

  // 计算层宽度
  const layerWidths = calculateLayerWidths(layoutNodes)

  // 计算位置
  const positions = calculatePositions(layoutNodes, layerWidths)

  // 转换为结果格式
  const result: Record<string, FlowNodePosition> = {}
  positions.forEach((position, key) => {
    result[key] = position
  })

  return result
}

/**
 * 获取推荐的布局方向
 */
export function getRecommendedDirection(
  nodes: FlowNodeConfig[],
  routes: FlowRouteConfig[]
): 'horizontal' | 'vertical' {
  if (nodes.length === 0) return 'horizontal'

  // 简单启发式：如果节点数多，使用水平布局
  return nodes.length > 5 ? 'horizontal' : 'vertical'
}

/**
 * 计算布局的边界框
 */
export function calculateBoundingBox(
  positions: Record<string, FlowNodePosition>
): { minX: number; minY: number; maxX: number; maxY: number; width: number; height: number } {
  const positionArray = Object.values(positions)

  if (positionArray.length === 0) {
    return { minX: 0, minY: 0, maxX: 0, maxY: 0, width: 0, height: 0 }
  }

  const minX = Math.min(...positionArray.map((p) => p.x))
  const minY = Math.min(...positionArray.map((p) => p.y))
  const maxX = Math.max(...positionArray.map((p) => p.x + NODE_WIDTH))
  const maxY = Math.max(...positionArray.map((p) => p.y + NODE_HEIGHT))

  return {
    minX,
    minY,
    maxX,
    maxY,
    width: maxX - minX,
    height: maxY - minY
  }
}
