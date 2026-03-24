/**
 * 节点剪贴板工具 - 处理节点复制和粘贴
 */

import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

/**
 * 节点剪贴板数据
 */
export interface NodeClipboardData {
  /** 复制的节点 */
  nodes: FlowNodeConfig[]
  /** 复制的路由 */
  routes: FlowRouteConfig[]
  /** 复制时间戳 */
  timestamp: number
  /** 源节点 ID 映射（用于粘贴时重新映射） */
  nodeIdMap: Record<string, string>
}

/**
 * 节点剪贴板管理器
 */
class NodeClipboardManager {
  private clipboard: NodeClipboardData | null = null

  /**
   * 复制节点
   */
  copyNodes(nodes: FlowNodeConfig[], routes: FlowRouteConfig[]): void {
    // 创建节点 ID 映射
    const nodeIdMap: Record<string, string> = {}
    nodes.forEach(node => {
      const key = node.id?.toString() ?? node.temp_id ?? ''
      if (key) {
        nodeIdMap[key] = key
      }
    })

    this.clipboard = {
      nodes: JSON.parse(JSON.stringify(nodes)),
      routes: JSON.parse(JSON.stringify(routes)),
      timestamp: Date.now(),
      nodeIdMap
    }
  }

  /**
   * 粘贴节点 - 返回新的节点和路由，带有新的 ID
   */
  pasteNodes(): { nodes: FlowNodeConfig[]; routes: FlowRouteConfig[] } | null {
    if (!this.clipboard) {
      return null
    }

    // 创建新的节点 ID 映射
    const oldToNewIdMap: Record<string, string> = {}
    const newNodes = this.clipboard.nodes.map(node => {
      const oldKey = node.temp_id ?? node.id?.toString() ?? ''
      const newTempId = `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

      if (oldKey) {
        oldToNewIdMap[oldKey] = newTempId
      }

      return {
        ...JSON.parse(JSON.stringify(node)),
        id: undefined,
        temp_id: newTempId
      }
    })

    // 更新路由中的节点引用
    const newRoutes = this.clipboard.routes.map(route => {
      const newRoute = JSON.parse(JSON.stringify(route))

      // 更新源节点引用
      const fromKey = route.from_node_key
      if (oldToNewIdMap[fromKey]) {
        newRoute.from_node_key = oldToNewIdMap[fromKey]
      }

      // 更新目标节点引用
      const toKey = route.to_node_key
      if (oldToNewIdMap[toKey]) {
        newRoute.to_node_key = oldToNewIdMap[toKey]
      }

      // 清除路由 ID
      newRoute.id = undefined
      newRoute.temp_id = `route_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

      return newRoute
    })

    return {
      nodes: newNodes,
      routes: newRoutes
    }
  }

  /**
   * 检查剪贴板是否有数据
   */
  hasData(): boolean {
    return this.clipboard !== null
  }

  /**
   * 清空剪贴板
   */
  clear(): void {
    this.clipboard = null
  }

  /**
   * 获取剪贴板数据（用于调试）
   */
  getData(): NodeClipboardData | null {
    return this.clipboard
  }
}

// 全局剪贴板实例
export const nodeClipboard = new NodeClipboardManager()

/**
 * 复制单个节点
 */
export function copySingleNode(node: FlowNodeConfig): void {
  nodeClipboard.copyNodes([node], [])
}

/**
 * 复制多个节点及其路由
 */
export function copyMultipleNodes(
  nodes: FlowNodeConfig[],
  routes: FlowRouteConfig[]
): void {
  nodeClipboard.copyNodes(nodes, routes)
}

/**
 * 粘贴节点
 */
export function pasteNodes(): { nodes: FlowNodeConfig[]; routes: FlowRouteConfig[] } | null {
  return nodeClipboard.pasteNodes()
}

/**
 * 检查是否可以粘贴
 */
export function canPaste(): boolean {
  return nodeClipboard.hasData()
}

/**
 * 清空剪贴板
 */
export function clearClipboard(): void {
  nodeClipboard.clear()
}

/**
 * 复制节点配置（不包括 ID）
 */
export function cloneNodeConfig(node: FlowNodeConfig): Partial<FlowNodeConfig> {
  const cloned = JSON.parse(JSON.stringify(node))
  delete cloned.id
  delete cloned.temp_id
  return cloned
}

/**
 * 复制路由配置（不包括 ID）
 */
export function cloneRouteConfig(route: FlowRouteConfig): Partial<FlowRouteConfig> {
  const cloned = JSON.parse(JSON.stringify(route))
  delete cloned.id
  delete cloned.temp_id
  return cloned
}

/**
 * 批量复制节点配置
 */
export function cloneNodeConfigs(nodes: FlowNodeConfig[]): Partial<FlowNodeConfig>[] {
  return nodes.map(node => cloneNodeConfig(node))
}

/**
 * 批量复制路由配置
 */
export function cloneRouteConfigs(routes: FlowRouteConfig[]): Partial<FlowRouteConfig>[] {
  return routes.map(route => cloneRouteConfig(route))
}

/**
 * 生成新的节点 ID
 */
export function generateNodeTempId(): string {
  return `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 生成新的路由 ID
 */
export function generateRouteTempId(): string {
  return `route_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 重新映射节点 ID
 */
export function remapNodeIds(
  nodes: FlowNodeConfig[],
  idMap: Record<string, string>
): FlowNodeConfig[] {
  return nodes.map(node => {
    // 优先使用 temp_id 作为查找键
    const oldKey = node.temp_id ?? node.id?.toString() ?? ''
    if (oldKey && idMap[oldKey]) {
      return {
        ...node,
        temp_id: idMap[oldKey]
      }
    }
    return node
  })
}

/**
 * 重新映射路由节点引用
 */
export function remapRouteNodeReferences(
  routes: FlowRouteConfig[],
  idMap: Record<string, string>
): FlowRouteConfig[] {
  return routes.map(route => {
    const newRoute = { ...route }

    if (idMap[route.from_node_key]) {
      newRoute.from_node_key = idMap[route.from_node_key]
    }

    if (idMap[route.to_node_key]) {
      newRoute.to_node_key = idMap[route.to_node_key]
    }

    return newRoute
  })
}
