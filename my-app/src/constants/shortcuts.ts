/**
 * 快捷键配置常量
 * 定义所有支持的快捷键映射
 */

export interface ShortcutConfig {
  /** 快捷键名称 */
  name: string
  /** 快捷键描述 */
  description: string
  /** 快捷键组合（用于显示） */
  keys: string[]
  /** 快捷键操作类型 */
  action: ShortcutAction
  /** 是否在输入框中禁用 */
  disableInInput?: boolean
}

export type ShortcutAction =
  | 'undo'
  | 'redo'
  | 'selectAll'
  | 'delete'
  | 'copy'
  | 'paste'
  | 'duplicate'
  | 'save'

/**
 * 快捷键映射表
 */
export const SHORTCUTS: Record<ShortcutAction, ShortcutConfig> = {
  undo: {
    name: '撤销',
    description: '撤销上一步操作',
    keys: ['Ctrl', 'Z'],
    action: 'undo',
    disableInInput: false
  },
  redo: {
    name: '重做',
    description: '重做下一步操作',
    keys: ['Ctrl', 'Y'],
    action: 'redo',
    disableInInput: false
  },
  selectAll: {
    name: '全选',
    description: '选中所有节点',
    keys: ['Ctrl', 'A'],
    action: 'selectAll',
    disableInInput: true
  },
  delete: {
    name: '删除',
    description: '删除选中节点',
    keys: ['Delete'],
    action: 'delete',
    disableInInput: true
  },
  copy: {
    name: '复制',
    description: '复制选中节点',
    keys: ['Ctrl', 'C'],
    action: 'copy',
    disableInInput: false
  },
  paste: {
    name: '粘贴',
    description: '粘贴复制的节点',
    keys: ['Ctrl', 'V'],
    action: 'paste',
    disableInInput: false
  },
  duplicate: {
    name: '复制（重复）',
    description: '复制并粘贴选中节点',
    keys: ['Ctrl', 'D'],
    action: 'duplicate',
    disableInInput: false
  },
  save: {
    name: '保存',
    description: '保存流程',
    keys: ['Ctrl', 'S'],
    action: 'save',
    disableInInput: false
  }
}

/**
 * 获取所有快捷键配置
 */
export function getAllShortcuts(): ShortcutConfig[] {
  return Object.values(SHORTCUTS)
}

/**
 * 根据快捷键组合获取操作类型
 */
export function getShortcutAction(
  event: KeyboardEvent
): ShortcutAction | null {
  // 检查是否按下了 Ctrl 或 Cmd
  const isCtrlOrCmd = event.ctrlKey || event.metaKey

  // Ctrl+Z / Cmd+Z 撤销
  if (isCtrlOrCmd && event.key === 'z' && !event.shiftKey) {
    return 'undo'
  }

  // Ctrl+Y / Cmd+Y 重做
  if (isCtrlOrCmd && event.key === 'y') {
    return 'redo'
  }

  // Ctrl+Shift+Z / Cmd+Shift+Z 重做
  if (isCtrlOrCmd && event.key === 'z' && event.shiftKey) {
    return 'redo'
  }

  // Ctrl+A / Cmd+A 全选
  if (isCtrlOrCmd && event.key === 'a') {
    return 'selectAll'
  }

  // Delete 删除
  if (event.key === 'Delete') {
    return 'delete'
  }

  // Ctrl+C / Cmd+C 复制
  if (isCtrlOrCmd && event.key === 'c') {
    return 'copy'
  }

  // Ctrl+V / Cmd+V 粘贴
  if (isCtrlOrCmd && event.key === 'v') {
    return 'paste'
  }

  // Ctrl+D / Cmd+D 复制（重复）
  if (isCtrlOrCmd && event.key === 'd') {
    return 'duplicate'
  }

  // Ctrl+S / Cmd+S 保存
  if (isCtrlOrCmd && event.key === 's') {
    return 'save'
  }

  return null
}

/**
 * 获取快捷键的显示文本
 */
export function getShortcutDisplayText(action: ShortcutAction): string {
  const isMac = /Mac|iPhone|iPad|iPod/.test(navigator.platform)
  const config = SHORTCUTS[action]

  if (!config) return ''

  return config.keys
    .map(key => {
      if (key === 'Ctrl') {
        return isMac ? '⌘' : 'Ctrl'
      }
      if (key === 'Shift') {
        return isMac ? '⇧' : 'Shift'
      }
      if (key === 'Alt') {
        return isMac ? '⌥' : 'Alt'
      }
      return key
    })
    .join(isMac ? '' : '+')
}
