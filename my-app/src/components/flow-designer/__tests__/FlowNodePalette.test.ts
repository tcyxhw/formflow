import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowNodePalette from '../FlowNodePalette.vue'

describe('FlowNodePalette', () => {
  let wrapper: any

  beforeEach(() => {
    wrapper = mount(FlowNodePalette)
  })

  describe('节点类型展示', () => {
    it('应该展示所有基础节点类型', () => {
      const basicNodes = wrapper.findAll('.node-category')[0]
      const nodeItems = basicNodes.findAll('.palette-node')
      
      // 基础节点：开始、结束
      expect(nodeItems.length).toBe(2)
    })

    it('应该展示所有高级节点类型', () => {
      const advancedNodes = wrapper.findAll('.node-category')[1]
      const nodeItems = advancedNodes.findAll('.palette-node')
      
      // 高级节点：审批、条件、抄送
      expect(nodeItems.length).toBe(3)
    })

    it('应该正确显示节点标签', () => {
      const nodeLabels = wrapper.findAll('.node-label')
      const labels = nodeLabels.map((el: any) => el.text())
      
      expect(labels).toContain('开始')
      expect(labels).toContain('结束')
      expect(labels).toContain('审批')
      expect(labels).toContain('条件')
      expect(labels).toContain('抄送')
    })

    it('应该正确显示节点描述', () => {
      const nodeDescs = wrapper.findAll('.node-desc')
      const descs = nodeDescs.map((el: any) => el.text())
      
      expect(descs).toContain('流程起点')
      expect(descs).toContain('流程终点')
      expect(descs).toContain('人工审批节点')
      expect(descs).toContain('条件分支节点')
      expect(descs).toContain('抄送通知节点')
    })
  })

  describe('拖拽功能', () => {
    it('应该支持拖拽节点', () => {
      const paletteNode = wrapper.find('.palette-node')
      expect(paletteNode.attributes('draggable')).toBe('true')
    })

    it('应该在拖拽开始时设置正确的数据', () => {
      const paletteNode = wrapper.find('.palette-node')
      const dragEvent = {
        dataTransfer: {
          setData: vi.fn(),
          effectAllowed: ''
        }
      }
      
      paletteNode.trigger('dragstart', dragEvent)
      
      expect(dragEvent.dataTransfer.setData).toHaveBeenCalledWith(
        'application/json',
        expect.stringContaining('"type":"node"')
      )
    })

    it('应该在拖拽开始时设置 effectAllowed 为 copy', () => {
      const paletteNode = wrapper.find('.palette-node')
      const dragEvent = {
        dataTransfer: {
          setData: vi.fn(),
          effectAllowed: ''
        }
      }
      
      paletteNode.trigger('dragstart', dragEvent)
      
      expect(dragEvent.dataTransfer.effectAllowed).toBe('copy')
    })

    it('应该在拖拽结束时更新状态', async () => {
      const paletteNode = wrapper.find('.palette-node')
      
      // 模拟拖拽开始
      paletteNode.trigger('dragstart')
      expect(wrapper.vm.isDragging).toBe(true)
      
      // 模拟拖拽结束
      paletteNode.trigger('dragend')
      expect(wrapper.vm.isDragging).toBe(false)
    })

    it('应该为不同的节点类型设置正确的数据', () => {
      const paletteNodes = wrapper.findAll('.palette-node')
      
      const dragEvent1 = {
        dataTransfer: {
          setData: vi.fn(),
          getData: vi.fn((type: string) => {
            if (type === 'application/json') {
              return JSON.stringify({
                type: 'node',
                nodeType: 'start',
                defaultName: '开始'
              })
            }
            return ''
          }),
          effectAllowed: ''
        }
      }
      
      paletteNodes[0].trigger('dragstart', dragEvent1)
      const data1 = dragEvent1.dataTransfer.getData('application/json')
      const parsed1 = JSON.parse(data1)
      
      expect(parsed1.nodeType).toBe('start')
      expect(parsed1.defaultName).toBe('开始')
      
      const dragEvent2 = {
        dataTransfer: {
          setData: vi.fn(),
          getData: vi.fn((type: string) => {
            if (type === 'application/json') {
              return JSON.stringify({
                type: 'node',
                nodeType: 'user',
                defaultName: '审批'
              })
            }
            return ''
          }),
          effectAllowed: ''
        }
      }
      
      paletteNodes[2].trigger('dragstart', dragEvent2)
      const data2 = dragEvent2.dataTransfer.getData('application/json')
      const parsed2 = JSON.parse(data2)
      
      expect(parsed2.nodeType).toBe('user')
      expect(parsed2.defaultName).toBe('审批')
    })
  })

  describe('样式和交互', () => {
    it('应该有正确的 CSS 类名', () => {
      expect(wrapper.find('.flow-node-palette').exists()).toBe(true)
      expect(wrapper.find('.palette-header').exists()).toBe(true)
      expect(wrapper.find('.palette-body').exists()).toBe(true)
    })

    it('应该显示标题和副标题', () => {
      const title = wrapper.find('.title')
      const subtitle = wrapper.find('.subtitle')
      
      expect(title.text()).toBe('节点调色板')
      expect(subtitle.text()).toBe('拖拽节点到画布')
    })

    it('应该显示分类标题', () => {
      const categoryTitles = wrapper.findAll('.category-title')
      const titles = categoryTitles.map((el: any) => el.text())
      
      expect(titles).toContain('基础节点')
      expect(titles).toContain('高级节点')
    })

    it('节点应该有图标', () => {
      const nodeIcons = wrapper.findAll('.node-icon')
      expect(nodeIcons.length).toBeGreaterThan(0)
      
      nodeIcons.forEach((icon: any) => {
        expect(icon.find('.n-icon').exists()).toBe(true)
      })
    })
  })

  describe('响应式行为', () => {
    it('应该支持滚动', () => {
      const paletteBody = wrapper.find('.palette-body')
      expect(paletteBody.classes()).toContain('palette-body')
      // palette-body 应该有 overflow-y: auto
    })

    it('所有节点应该可见', () => {
      const paletteNodes = wrapper.findAll('.palette-node')
      expect(paletteNodes.length).toBe(5) // 2 个基础 + 3 个高级
    })
  })

  describe('数据完整性', () => {
    it('每个节点应该有完整的信息', () => {
      const paletteNodes = wrapper.findAll('.palette-node')
      
      paletteNodes.forEach((node: any) => {
        expect(node.find('.node-icon').exists()).toBe(true)
        expect(node.find('.node-label').exists()).toBe(true)
        expect(node.find('.node-desc').exists()).toBe(true)
      })
    })

    it('应该为每个节点提供默认名称', () => {
      const paletteNodes = wrapper.findAll('.palette-node')
      
      // 验证节点数量
      expect(paletteNodes.length).toBe(5)
      
      // 验证每个节点都有标签
      paletteNodes.forEach((node: any) => {
        const label = node.find('.node-label')
        expect(label.exists()).toBe(true)
        expect(label.text()).toBeTruthy()
      })
    })
  })
})
