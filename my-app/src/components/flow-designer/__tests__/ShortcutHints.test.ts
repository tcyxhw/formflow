import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ShortcutHints from '../ShortcutHints.vue'

describe('ShortcutHints 组件', () => {
  let wrapper: any

  beforeEach(() => {
    wrapper = mount(ShortcutHints, {
      global: {
        stubs: {
          NButton: true,
          NIcon: true,
          NModal: true
        }
      }
    })
  })

  it('应该正确渲染快捷键帮助按钮', () => {
    const button = wrapper.find('.shortcut-help-btn')
    expect(button.exists()).toBe(true)
    expect(button.text()).toContain('快捷键')
  })

  it('应该在点击按钮时打开模态框', async () => {
    const button = wrapper.find('.shortcut-help-btn')
    await button.trigger('click')
    expect(wrapper.vm.showModal).toBe(true)
  })

  it('应该显示所有快捷键', () => {
    const shortcuts = wrapper.vm.shortcuts
    expect(shortcuts.length).toBeGreaterThan(0)
    
    const actions = shortcuts.map((s: any) => s.action)
    expect(actions).toContain('undo')
    expect(actions).toContain('redo')
    expect(actions).toContain('selectAll')
    expect(actions).toContain('delete')
    expect(actions).toContain('copy')
    expect(actions).toContain('paste')
    expect(actions).toContain('duplicate')
    expect(actions).toContain('save')
  })

  it('应该正确格式化快捷键', () => {
    const formattedCtrl = wrapper.vm.formatKey('Ctrl')
    expect(formattedCtrl).toBeTruthy()
    
    const formattedDelete = wrapper.vm.formatKey('Delete')
    expect(formattedDelete).toBe('Delete')
  })

  it('应该在 Mac 上显示 ⌘ 符号', () => {
    // 模拟 Mac 环境
    const originalPlatform = Object.getOwnPropertyDescriptor(navigator, 'platform')
    Object.defineProperty(navigator, 'platform', {
      value: 'MacIntel',
      configurable: true
    })

    const formattedCtrl = wrapper.vm.formatKey('Ctrl')
    expect(formattedCtrl).toBe('⌘')

    // 恢复原始值
    if (originalPlatform) {
      Object.defineProperty(navigator, 'platform', originalPlatform)
    }
  })

  it('应该在非 Mac 上显示 Ctrl 文本', () => {
    // 模拟非 Mac 环境
    const originalPlatform = Object.getOwnPropertyDescriptor(navigator, 'platform')
    Object.defineProperty(navigator, 'platform', {
      value: 'Linux',
      configurable: true
    })

    const formattedCtrl = wrapper.vm.formatKey('Ctrl')
    expect(formattedCtrl).toBe('Ctrl')

    // 恢复原始值
    if (originalPlatform) {
      Object.defineProperty(navigator, 'platform', originalPlatform)
    }
  })

  it('应该正确格式化 Shift 键', () => {
    const originalPlatform = Object.getOwnPropertyDescriptor(navigator, 'platform')
    Object.defineProperty(navigator, 'platform', {
      value: 'MacIntel',
      configurable: true
    })

    const formattedShift = wrapper.vm.formatKey('Shift')
    expect(formattedShift).toBe('⇧')

    Object.defineProperty(navigator, 'platform', {
      value: 'Linux',
      configurable: true
    })

    const formattedShiftLinux = wrapper.vm.formatKey('Shift')
    expect(formattedShiftLinux).toBe('Shift')

    // 恢复原始值
    if (originalPlatform) {
      Object.defineProperty(navigator, 'platform', originalPlatform)
    }
  })

  it('应该正确格式化 Alt 键', () => {
    const originalPlatform = Object.getOwnPropertyDescriptor(navigator, 'platform')
    Object.defineProperty(navigator, 'platform', {
      value: 'MacIntel',
      configurable: true
    })

    const formattedAlt = wrapper.vm.formatKey('Alt')
    expect(formattedAlt).toBe('⌥')

    Object.defineProperty(navigator, 'platform', {
      value: 'Linux',
      configurable: true
    })

    const formattedAltLinux = wrapper.vm.formatKey('Alt')
    expect(formattedAltLinux).toBe('Alt')

    // 恢复原始值
    if (originalPlatform) {
      Object.defineProperty(navigator, 'platform', originalPlatform)
    }
  })

  it('应该为每个快捷键显示名称和描述', () => {
    const shortcuts = wrapper.vm.shortcuts
    
    shortcuts.forEach((shortcut: any) => {
      expect(shortcut.name).toBeTruthy()
      expect(shortcut.description).toBeTruthy()
    })
  })

  it('应该为每个快捷键显示快捷键组合', () => {
    const shortcuts = wrapper.vm.shortcuts
    
    shortcuts.forEach((shortcut: any) => {
      expect(shortcut.keys).toBeDefined()
      expect(Array.isArray(shortcut.keys)).toBe(true)
      expect(shortcut.keys.length).toBeGreaterThan(0)
    })
  })
})
