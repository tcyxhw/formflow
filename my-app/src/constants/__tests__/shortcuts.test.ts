import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  SHORTCUTS,
  getAllShortcuts,
  getShortcutAction,
  getShortcutDisplayText
} from '../shortcuts'
import type { ShortcutAction } from '../shortcuts'

describe('快捷键常量', () => {
  describe('SHORTCUTS 对象', () => {
    it('应该包含所有必需的快捷键', () => {
      const requiredActions: ShortcutAction[] = [
        'undo',
        'redo',
        'selectAll',
        'delete',
        'copy',
        'paste',
        'duplicate',
        'save'
      ]

      requiredActions.forEach(action => {
        expect(SHORTCUTS[action]).toBeDefined()
        expect(SHORTCUTS[action].action).toBe(action)
      })
    })

    it('每个快捷键应该有正确的属性', () => {
      Object.values(SHORTCUTS).forEach(shortcut => {
        expect(shortcut.name).toBeDefined()
        expect(shortcut.description).toBeDefined()
        expect(shortcut.keys).toBeDefined()
        expect(Array.isArray(shortcut.keys)).toBe(true)
        expect(shortcut.action).toBeDefined()
      })
    })

    it('撤销快捷键应该是 Ctrl+Z', () => {
      expect(SHORTCUTS.undo.keys).toContain('Ctrl')
      expect(SHORTCUTS.undo.keys).toContain('Z')
    })

    it('重做快捷键应该是 Ctrl+Y', () => {
      expect(SHORTCUTS.redo.keys).toContain('Ctrl')
      expect(SHORTCUTS.redo.keys).toContain('Y')
    })

    it('全选快捷键应该是 Ctrl+A', () => {
      expect(SHORTCUTS.selectAll.keys).toContain('Ctrl')
      expect(SHORTCUTS.selectAll.keys).toContain('A')
    })

    it('删除快捷键应该是 Delete', () => {
      expect(SHORTCUTS.delete.keys).toContain('Delete')
    })

    it('复制快捷键应该是 Ctrl+C', () => {
      expect(SHORTCUTS.copy.keys).toContain('Ctrl')
      expect(SHORTCUTS.copy.keys).toContain('C')
    })

    it('粘贴快捷键应该是 Ctrl+V', () => {
      expect(SHORTCUTS.paste.keys).toContain('Ctrl')
      expect(SHORTCUTS.paste.keys).toContain('V')
    })

    it('复制（重复）快捷键应该是 Ctrl+D', () => {
      expect(SHORTCUTS.duplicate.keys).toContain('Ctrl')
      expect(SHORTCUTS.duplicate.keys).toContain('D')
    })

    it('保存快捷键应该是 Ctrl+S', () => {
      expect(SHORTCUTS.save.keys).toContain('Ctrl')
      expect(SHORTCUTS.save.keys).toContain('S')
    })
  })

  describe('getAllShortcuts 函数', () => {
    it('应该返回所有快捷键配置', () => {
      const shortcuts = getAllShortcuts()
      expect(Array.isArray(shortcuts)).toBe(true)
      expect(shortcuts.length).toBeGreaterThan(0)
    })

    it('返回的数组应该包含所有快捷键', () => {
      const shortcuts = getAllShortcuts()
      const actions = shortcuts.map(s => s.action)
      
      expect(actions).toContain('undo')
      expect(actions).toContain('redo')
      expect(actions).toContain('selectAll')
      expect(actions).toContain('delete')
      expect(actions).toContain('copy')
      expect(actions).toContain('paste')
      expect(actions).toContain('duplicate')
      expect(actions).toContain('save')
    })
  })

  describe('getShortcutAction 函数', () => {
    let mockEvent: Partial<KeyboardEvent>

    beforeEach(() => {
      mockEvent = {
        key: '',
        ctrlKey: false,
        metaKey: false,
        shiftKey: false
      }
    })

    it('应该识别 Ctrl+Z 为撤销', () => {
      mockEvent.key = 'z'
      mockEvent.ctrlKey = true
      mockEvent.shiftKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('undo')
    })

    it('应该识别 Cmd+Z 为撤销（Mac）', () => {
      mockEvent.key = 'z'
      mockEvent.metaKey = true
      mockEvent.shiftKey = false
      mockEvent.ctrlKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('undo')
    })

    it('应该识别 Ctrl+Y 为重做', () => {
      mockEvent.key = 'y'
      mockEvent.ctrlKey = true
      mockEvent.metaKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('redo')
    })

    it('应该识别 Cmd+Y 为重做（Mac）', () => {
      mockEvent.key = 'y'
      mockEvent.metaKey = true
      mockEvent.ctrlKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('redo')
    })

    it('应该识别 Ctrl+Y 为重做', () => {
      mockEvent.key = 'y'
      mockEvent.ctrlKey = true
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('redo')
    })

    it('应该识别 Ctrl+Shift+Z 为重做', () => {
      mockEvent.key = 'z'
      mockEvent.ctrlKey = true
      mockEvent.shiftKey = true
      mockEvent.metaKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('redo')
    })

    it('应该识别 Cmd+Shift+Z 为重做（Mac）', () => {
      mockEvent.key = 'z'
      mockEvent.metaKey = true
      mockEvent.shiftKey = true
      mockEvent.ctrlKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('redo')
    })

    it('应该识别 Ctrl+A 为全选', () => {
      mockEvent.key = 'a'
      mockEvent.ctrlKey = true
      mockEvent.metaKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('selectAll')
    })

    it('应该识别 Cmd+A 为全选（Mac）', () => {
      mockEvent.key = 'a'
      mockEvent.metaKey = true
      mockEvent.ctrlKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('selectAll')
    })

    it('应该识别 Delete 为删除', () => {
      mockEvent.key = 'Delete'
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('delete')
    })

    it('应该识别 Ctrl+C 为复制', () => {
      mockEvent.key = 'c'
      mockEvent.ctrlKey = true
      mockEvent.metaKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('copy')
    })

    it('应该识别 Cmd+C 为复制（Mac）', () => {
      mockEvent.key = 'c'
      mockEvent.metaKey = true
      mockEvent.ctrlKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('copy')
    })

    it('应该识别 Ctrl+V 为粘贴', () => {
      mockEvent.key = 'v'
      mockEvent.ctrlKey = true
      mockEvent.metaKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('paste')
    })

    it('应该识别 Cmd+V 为粘贴（Mac）', () => {
      mockEvent.key = 'v'
      mockEvent.metaKey = true
      mockEvent.ctrlKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('paste')
    })

    it('应该识别 Ctrl+D 为复制（重复）', () => {
      mockEvent.key = 'd'
      mockEvent.ctrlKey = true
      mockEvent.metaKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('duplicate')
    })

    it('应该识别 Cmd+D 为复制（重复）（Mac）', () => {
      mockEvent.key = 'd'
      mockEvent.metaKey = true
      mockEvent.ctrlKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('duplicate')
    })

    it('应该识别 Ctrl+S 为保存', () => {
      mockEvent.key = 's'
      mockEvent.ctrlKey = true
      mockEvent.metaKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('save')
    })

    it('应该识别 Cmd+S 为保存（Mac）', () => {
      mockEvent.key = 's'
      mockEvent.metaKey = true
      mockEvent.ctrlKey = false
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBe('save')
    })

    it('应该返回 null 对于未知的快捷键', () => {
      mockEvent.key = 'x'
      mockEvent.ctrlKey = true
      
      const action = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action).toBeNull()
    })

    it('应该区分 Ctrl+Z 和 Ctrl+Shift+Z', () => {
      mockEvent.key = 'z'
      mockEvent.ctrlKey = true
      mockEvent.shiftKey = false
      
      const action1 = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action1).toBe('undo')

      mockEvent.shiftKey = true
      const action2 = getShortcutAction(mockEvent as KeyboardEvent)
      expect(action2).toBe('redo')
    })
  })

  describe('getShortcutDisplayText 函数', () => {
    it('应该返回撤销快捷键的显示文本', () => {
      const text = getShortcutDisplayText('undo')
      expect(text).toBeTruthy()
      expect(text.length).toBeGreaterThan(0)
    })

    it('应该返回重做快捷键的显示文本', () => {
      const text = getShortcutDisplayText('redo')
      expect(text).toBeTruthy()
      expect(text.length).toBeGreaterThan(0)
    })

    it('应该返回全选快捷键的显示文本', () => {
      const text = getShortcutDisplayText('selectAll')
      expect(text).toBeTruthy()
      expect(text.length).toBeGreaterThan(0)
    })

    it('应该返回删除快捷键的显示文本', () => {
      const text = getShortcutDisplayText('delete')
      expect(text).toBe('Delete')
    })

    it('应该返回复制快捷键的显示文本', () => {
      const text = getShortcutDisplayText('copy')
      expect(text).toBeTruthy()
      expect(text.length).toBeGreaterThan(0)
    })

    it('应该返回粘贴快捷键的显示文本', () => {
      const text = getShortcutDisplayText('paste')
      expect(text).toBeTruthy()
      expect(text.length).toBeGreaterThan(0)
    })

    it('应该返回复制（重复）快捷键的显示文本', () => {
      const text = getShortcutDisplayText('duplicate')
      expect(text).toBeTruthy()
      expect(text.length).toBeGreaterThan(0)
    })

    it('应该返回保存快捷键的显示文本', () => {
      const text = getShortcutDisplayText('save')
      expect(text).toBeTruthy()
      expect(text.length).toBeGreaterThan(0)
    })

    it('应该返回空字符串对于未知的操作', () => {
      const text = getShortcutDisplayText('unknown' as ShortcutAction)
      expect(text).toBe('')
    })

    it('在 Mac 上应该使用 ⌘ 符号', () => {
      // 模拟 Mac 环境
      const originalPlatform = Object.getOwnPropertyDescriptor(navigator, 'platform')
      Object.defineProperty(navigator, 'platform', {
        value: 'MacIntel',
        configurable: true
      })

      const text = getShortcutDisplayText('undo')
      expect(text).toContain('⌘')

      // 恢复原始值
      if (originalPlatform) {
        Object.defineProperty(navigator, 'platform', originalPlatform)
      }
    })

    it('在非 Mac 上应该使用 Ctrl 文本', () => {
      // 模拟非 Mac 环境
      const originalPlatform = Object.getOwnPropertyDescriptor(navigator, 'platform')
      Object.defineProperty(navigator, 'platform', {
        value: 'Linux',
        configurable: true
      })

      const text = getShortcutDisplayText('undo')
      expect(text).toContain('Ctrl')

      // 恢复原始值
      if (originalPlatform) {
        Object.defineProperty(navigator, 'platform', originalPlatform)
      }
    })
  })
})
