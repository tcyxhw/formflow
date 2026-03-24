import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowCanvas from '../FlowCanvas.vue'
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

describe('FlowCanvas', () => {
  let wrapper: any

  const mockNodes: FlowNodeConfig[] = [
    {
      id: 1,
      name: '开始节点',
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
      name: '审批节点',
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
      name: '结束节点',
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
    }
  ]

  const mockNodesGraph = {
    '1': { x: 80, y: 160 },
    '2': { x: 280, y: 160 },
    '3': { x: 480, y: 160 }
  }

  beforeEach(() => {
    wrapper = mount(FlowCanvas, {
      props: {
        nodes: mockNodes,
        routes: mockRoutes,
        nodesGraph: mockNodesGraph,
        selectedNodeKey: '1'
      },
      global: {
        stubs: {
          NButton: true,
          NButtonGroup: true,
          NIcon: true,
          NDropdown: true
        }
      }
    })
  })

  it('应该正确渲染所有节点', () => {
    const nodes = wrapper.findAll('.flow-node')
    expect(nodes).toHaveLength(3)
  })

  it('应该正确渲染所有连线', () => {
    const routes = wrapper.findAll('.route-line')
    expect(routes).toHaveLength(2)
  })

  it('应该显示正确的节点类型标签', () => {
    const tags = wrapper.findAll('.node-type-tag')
    expect(tags[0].text()).toBe('开始')
    expect(tags[1].text()).toBe('审批')
    expect(tags[2].text()).toBe('结束')
  })

  it('应该显示正确的节点名称', () => {
    const names = wrapper.findAll('.node-name')
    expect(names[0].text()).toBe('开始节点')
    expect(names[1].text()).toBe('审批节点')
    expect(names[2].text()).toBe('结束节点')
  })

  it('应该在选中节点时添加 is-selected 类', async () => {
    await wrapper.setProps({ selectedNodeKey: '2' })
    const nodes = wrapper.findAll('.flow-node')
    expect(nodes[1].classes()).toContain('is-selected')
  })

  it('应该在点击节点时发出 select-node 事件', async () => {
    const nodes = wrapper.findAll('.flow-node')
    await nodes[1].trigger('click')
    expect(wrapper.emitted('select-node')).toBeTruthy()
    expect(wrapper.emitted('select-node')[0]).toEqual(['2', false])
  })

  it('应该在 Ctrl+Click 时发出多选事件', async () => {
    const nodes = wrapper.findAll('.flow-node')
    await nodes[1].trigger('click', { ctrlKey: true })
    expect(wrapper.emitted('select-node')).toBeTruthy()
    expect(wrapper.emitted('select-node')[0]).toEqual(['2', true])
  })

  it('应该在 Cmd+Click 时发出多选事件（Mac）', async () => {
    const nodes = wrapper.findAll('.flow-node')
    await nodes[1].trigger('click', { metaKey: true })
    expect(wrapper.emitted('select-node')).toBeTruthy()
    expect(wrapper.emitted('select-node')[0]).toEqual(['2', true])
  })

  it('应该在点击连线时发出 select-route 事件', async () => {
    const routes = wrapper.findAll('.route-line')
    await routes[0].trigger('click')
    expect(wrapper.emitted('select-route')).toBeTruthy()
    expect(wrapper.emitted('select-route')[0]).toEqual([0])
  })

  it('应该支持缩放功能', async () => {
    const zoomInBtn = wrapper.findAll('button')[0]
    await zoomInBtn.trigger('click')
    expect(wrapper.vm.scale).toBeGreaterThan(1)
  })

  it('应该支持重置缩放', async () => {
    wrapper.vm.scale = 1.5
    const resetBtn = wrapper.findAll('button')[2]
    await resetBtn.trigger('click')
    expect(wrapper.vm.scale).toBe(1)
  })

  it('应该显示缩放百分比', () => {
    const indicator = wrapper.find('.zoom-indicator')
    expect(indicator.text()).toContain('100%')
  })

  it('应该在拖拽节点时发出 update-position 事件', async () => {
    const node = wrapper.find('.flow-node')
    const canvas = wrapper.find('.flow-canvas')

    await node.trigger('pointerdown', {
      clientX: 100,
      clientY: 200,
      button: 0
    })

    await canvas.trigger('pointermove', {
      clientX: 150,
      clientY: 250
    })

    await canvas.trigger('pointerup')

    expect(wrapper.emitted('update-position')).toBeTruthy()
  })

  it('应该在右键点击节点时显示上下文菜单', async () => {
    const node = wrapper.find('.flow-node')
    await node.trigger('contextmenu', {
      clientX: 100,
      clientY: 200,
      preventDefault: () => {}
    })
    expect(wrapper.vm.showContextMenu).toBe(true)
  })

  it('应该支持删除节点', async () => {
    wrapper.vm.contextMenuNodeKey = '1'
    wrapper.vm.showContextMenu = true
    await wrapper.vm.handleContextMenuSelect('delete-node')
    expect(wrapper.emitted('delete-node')).toBeTruthy()
    expect(wrapper.emitted('delete-node')[0]).toEqual(['1'])
  })

  it('应该正确计算节点位置', () => {
    const pos = wrapper.vm.getNodePosition('1')
    expect(pos).toEqual({ x: 80, y: 160 })
  })

  it('应该正确计算连线起点', () => {
    const startPos = wrapper.vm.getRouteStartPos(mockRoutes[0])
    expect(startPos).toEqual({ x: 170, y: 210 })
  })

  it('应该正确计算连线终点', () => {
    const endPos = wrapper.vm.getRouteEndPos(mockRoutes[0])
    expect(endPos).toEqual({ x: 280, y: 210 })
  })

  it('应该支持连线拖拽', async () => {
    const connectionPoint = wrapper.find('.connection-point-out')
    await connectionPoint.trigger('pointerdown', {
      clientX: 100,
      clientY: 200,
      button: 0
    })
    expect(wrapper.vm.connectionState.active).toBe(true)
  })

  it('应该在连线完成时发出 add-route 事件', async () => {
    wrapper.vm.connectionState.active = true
    wrapper.vm.connectionState.fromNodeKey = '1'
    
    await wrapper.find('.flow-canvas').trigger('pointerup', {
      clientX: 280,
      clientY: 210
    })
    
    expect(wrapper.emitted('add-route')).toBeTruthy()
  })

  it('应该在滚轮事件时改变缩放', async () => {
    const canvas = wrapper.find('.flow-canvas')
    const initialScale = wrapper.vm.scale
    
    await canvas.trigger('wheel', {
      deltaY: 100,
      preventDefault: () => {}
    })
    
    expect(wrapper.vm.scale).toBeLessThan(initialScale)
  })

  it('应该显示默认路由的虚线', async () => {
    const routes = wrapper.findAll('.route-line')
    expect(routes[0].attributes('stroke-dasharray')).toBe('0')
  })

  it('应该显示条件路由的虚线', async () => {
    const routesWithCondition: FlowRouteConfig[] = [
      {
        from_node_key: '1',
        to_node_key: '2',
        priority: 1,
        is_default: false,
        condition: { '>': [{ var: 'amount' }, 10000] }
      }
    ]
    
    await wrapper.setProps({ routes: routesWithCondition })
    const routes = wrapper.findAll('.route-line')
    expect(routes[0].attributes('stroke-dasharray')).toBe('8 4')
  })

  it('应该在多选时显示 is-multi-selected 类', async () => {
    const selectedNodeKeys = new Set(['1', '2'])
    await wrapper.setProps({ selectedNodeKeys })
    const nodes = wrapper.findAll('.flow-node')
    expect(nodes[0].classes()).toContain('is-multi-selected')
    expect(nodes[1].classes()).toContain('is-multi-selected')
  })

  it('应该正确判断节点是否被多选', async () => {
    const selectedNodeKeys = new Set(['1', '2'])
    await wrapper.setProps({ selectedNodeKeys })
    expect(wrapper.vm.isNodeMultiSelected('1')).toBe(true)
    expect(wrapper.vm.isNodeMultiSelected('2')).toBe(true)
    expect(wrapper.vm.isNodeMultiSelected('3')).toBe(false)
  })

  describe('撤销/重做功能', () => {
    it('应该在按下 Ctrl+Z 时发出 undo 事件', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('undo')).toBeTruthy()
    })

    it('应该在按下 Cmd+Z 时发出 undo 事件（Mac）', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 'z',
        metaKey: true,
        shiftKey: false,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('undo')).toBeTruthy()
    })

    it('应该在按下 Ctrl+Y 时发出 redo 事件', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 'y',
        ctrlKey: true,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('redo')).toBeTruthy()
    })

    it('应该在按下 Ctrl+Shift+Z 时发出 redo 事件', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: true,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('redo')).toBeTruthy()
    })

    it('应该在按下 Cmd+Shift+Z 时发出 redo 事件（Mac）', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 'z',
        metaKey: true,
        shiftKey: true,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('redo')).toBeTruthy()
    })

    it('应该在 keydown 事件中调用 preventDefault', async () => {
      const preventDefaultSpy = vi.fn()
      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true
      })
      vi.spyOn(event, 'preventDefault').mockImplementation(preventDefaultSpy)
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(preventDefaultSpy).toHaveBeenCalled()
    })
  })

  describe('快捷键操作', () => {
    it('应该在按下 Ctrl+A 时发出 select-all 事件', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 'a',
        ctrlKey: true,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('select-all')).toBeTruthy()
    })

    it('应该在按下 Cmd+A 时发出 select-all 事件（Mac）', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 'a',
        metaKey: true,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('select-all')).toBeTruthy()
    })

    it('应该在按下 Delete 时发出 delete 事件', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 'Delete',
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('delete')).toBeTruthy()
    })

    it('应该在按下 Ctrl+C 时发出 copy 事件', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 'c',
        ctrlKey: true,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('copy')).toBeTruthy()
    })

    it('应该在按下 Cmd+C 时发出 copy 事件（Mac）', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 'c',
        metaKey: true,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('copy')).toBeTruthy()
    })

    it('应该在按下 Ctrl+V 时发出 paste 事件', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 'v',
        ctrlKey: true,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('paste')).toBeTruthy()
    })

    it('应该在按下 Cmd+V 时发出 paste 事件（Mac）', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 'v',
        metaKey: true,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('paste')).toBeTruthy()
    })

    it('应该在按下 Ctrl+D 时发出 duplicate 事件', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 'd',
        ctrlKey: true,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('duplicate')).toBeTruthy()
    })

    it('应该在按下 Cmd+D 时发出 duplicate 事件（Mac）', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 'd',
        metaKey: true,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('duplicate')).toBeTruthy()
    })

    it('应该在按下 Ctrl+S 时发出 save 事件', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 's',
        ctrlKey: true,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('save')).toBeTruthy()
    })

    it('应该在按下 Cmd+S 时发出 save 事件（Mac）', async () => {
      const event = new KeyboardEvent('keydown', {
        key: 's',
        metaKey: true,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      expect(wrapper.emitted('save')).toBeTruthy()
    })

    it('不应该处理未知的快捷键', async () => {
      const initialEmitCount = Object.keys(wrapper.emitted()).length
      
      const event = new KeyboardEvent('keydown', {
        key: 'x',
        ctrlKey: true,
        bubbles: true
      })
      window.dispatchEvent(event)
      await wrapper.vm.$nextTick()
      
      const finalEmitCount = Object.keys(wrapper.emitted()).length
      expect(finalEmitCount).toBe(initialEmitCount)
    })
  })

  describe('网格对齐功能', () => {
    it('应该有默认的网格大小', () => {
      expect(wrapper.vm.gridSize).toBe(20)
    })

    it('应该默认启用网格对齐', () => {
      expect(wrapper.vm.gridEnabled).toBe(true)
    })

    it('应该能够切换网格对齐', async () => {
      const initialState = wrapper.vm.gridEnabled
      wrapper.vm.toggleGrid()
      expect(wrapper.vm.gridEnabled).toBe(!initialState)
    })

    it('应该能够增加网格大小', async () => {
      const initialSize = wrapper.vm.gridSize
      wrapper.vm.increaseGridSize()
      expect(wrapper.vm.gridSize).toBe(initialSize + 10)
    })

    it('应该能够减小网格大小', async () => {
      wrapper.vm.gridSize = 30
      const initialSize = wrapper.vm.gridSize
      wrapper.vm.decreaseGridSize()
      expect(wrapper.vm.gridSize).toBe(initialSize - 10)
    })

    it('网格大小不应该超过最大值 40', async () => {
      wrapper.vm.gridSize = 40
      wrapper.vm.increaseGridSize()
      expect(wrapper.vm.gridSize).toBe(40)
    })

    it('网格大小不应该低于最小值 10', async () => {
      wrapper.vm.gridSize = 10
      wrapper.vm.decreaseGridSize()
      expect(wrapper.vm.gridSize).toBe(10)
    })

    it('应该正确对齐坐标到网格', () => {
      wrapper.vm.gridSize = 20
      wrapper.vm.gridEnabled = true
      
      expect(wrapper.vm.snapToGrid(0)).toBe(0)
      expect(wrapper.vm.snapToGrid(5)).toBe(0)
      expect(wrapper.vm.snapToGrid(15)).toBe(20)
      expect(wrapper.vm.snapToGrid(25)).toBe(20)
      expect(wrapper.vm.snapToGrid(35)).toBe(40)
    })

    it('当网格禁用时不应该对齐坐标', () => {
      wrapper.vm.gridSize = 20
      wrapper.vm.gridEnabled = false
      
      expect(wrapper.vm.snapToGrid(15)).toBe(15)
      expect(wrapper.vm.snapToGrid(25)).toBe(25)
    })

    it('应该在拖拽时应用网格对齐', async () => {
      wrapper.vm.gridSize = 20
      wrapper.vm.gridEnabled = true
      wrapper.vm.dragState.active = true
      wrapper.vm.dragState.nodeKey = '1'
      wrapper.vm.dragState.offsetX = 0
      wrapper.vm.dragState.offsetY = 0

      const canvas = wrapper.find('.flow-canvas')
      const canvasRect = {
        left: 0,
        top: 0,
        getBoundingClientRect: () => canvasRect
      }
      
      wrapper.vm.$el.getBoundingClientRect = () => canvasRect

      await canvas.trigger('pointermove', {
        clientX: 25,
        clientY: 35
      })

      const emitted = wrapper.emitted('update-position')
      if (emitted && emitted.length > 0) {
        const position = emitted[0][0].position
        expect(position.x % 20).toBe(0)
        expect(position.y % 20).toBe(0)
      }
    })

    it('应该在网格背景中使用正确的网格大小', async () => {
      wrapper.vm.gridSize = 30
      await wrapper.vm.$nextTick()
      
      const gridBg = wrapper.find('.grid-background')
      const style = gridBg.attributes('style')
      expect(style).toContain('30px')
    })

    it('应该显示网格切换按钮', () => {
      const buttons = wrapper.findAll('button')
      expect(buttons.length).toBeGreaterThan(3)
    })

    it('应该在启用网格时显示主要按钮样式', async () => {
      wrapper.vm.gridEnabled = true
      await wrapper.vm.$nextTick()
      
      const buttons = wrapper.findAll('button')
      expect(buttons.length).toBeGreaterThan(3)
    })

    it('应该在禁用网格时显示默认按钮样式', async () => {
      wrapper.vm.gridEnabled = false
      await wrapper.vm.$nextTick()
      
      const buttons = wrapper.findAll('button')
      const gridButton = buttons[3]
      expect(gridButton.classes()).not.toContain('n-button--primary')
    })
  })

  describe('自动布局功能', () => {
    it('应该有自动布局方法', () => {
      expect(wrapper.vm.autoLayoutNodes).toBeDefined()
      expect(typeof wrapper.vm.autoLayoutNodes).toBe('function')
    })

    it('应该在调用自动布局时发出 update-position 事件', async () => {
      wrapper.vm.autoLayoutNodes()
      await wrapper.vm.$nextTick()
      
      const emitted = wrapper.emitted('update-position')
      expect(emitted).toBeTruthy()
      expect(emitted!.length).toBeGreaterThan(0)
    })

    it('应该为所有节点发出 update-position 事件', async () => {
      wrapper.vm.autoLayoutNodes()
      await wrapper.vm.$nextTick()
      
      const emitted = wrapper.emitted('update-position')
      expect(emitted!.length).toBe(3) // 3 个节点
    })

    it('应该为每个节点发出正确的位置数据', async () => {
      wrapper.vm.autoLayoutNodes()
      await wrapper.vm.$nextTick()
      
      const emitted = wrapper.emitted('update-position')
      emitted!.forEach((event: any) => {
        expect(event[0]).toHaveProperty('key')
        expect(event[0]).toHaveProperty('position')
        expect(event[0].position).toHaveProperty('x')
        expect(event[0].position).toHaveProperty('y')
      })
    })

    it('应该显示自动布局按钮', () => {
      const buttons = wrapper.findAll('button')
      const autoLayoutButton = buttons.find((btn) => btn.text().includes('自动布局'))
      expect(autoLayoutButton).toBeDefined()
    })
  })
})
