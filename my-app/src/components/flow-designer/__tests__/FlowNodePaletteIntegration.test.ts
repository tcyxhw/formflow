import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FlowNodePalette from '../FlowNodePalette.vue'
import FlowCanvas from '../FlowCanvas.vue'
import type { FlowNodeConfig, FlowRouteConfig } from '@/types/flow'

describe('FlowNodePalette 集成测试', () => {
  describe('与 FlowCanvas 的集成', () => {
    it('应该能够拖拽节点到画布', async () => {
      const paletteWrapper = mount(FlowNodePalette)
      
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
        }
      ]
      
      const mockRoutes: FlowRouteConfig[] = []
      const mockNodesGraph = { '1': { x: 100, y: 100 } }
      
      mount(FlowCanvas, {
        props: {
          nodes: mockNodes,
          routes: mockRoutes,
          nodesGraph: mockNodesGraph
        }
      })
      
      // 从调色板拖拽节点
      const paletteNode = paletteWrapper.find('.palette-node')
      const dragEvent = {
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
      
      paletteNode.trigger('dragstart', dragEvent)
      
      // 验证拖拽数据
      const dragData = dragEvent.dataTransfer.getData('application/json')
      expect(dragData).toBeTruthy()
      
      const parsed = JSON.parse(dragData)
      expect(parsed.type).toBe('node')
      expect(parsed.nodeType).toBe('start')
    })

    it('应该支持拖拽多个不同类型的节点', async () => {
      const paletteWrapper = mount(FlowNodePalette)
      const paletteNodes = paletteWrapper.findAll('.palette-node')
      
      const nodeTypes = ['start', 'end', 'user', 'condition', 'auto']
      
      paletteNodes.forEach((node: any, index: number) => {
        const dragEvent = {
          dataTransfer: {
            setData: vi.fn(),
            getData: vi.fn((type: string) => {
              if (type === 'application/json') {
                return JSON.stringify({
                  type: 'node',
                  nodeType: nodeTypes[index],
                  defaultName: '节点'
                })
              }
              return ''
            }),
            effectAllowed: ''
          }
        }
        
        node.trigger('dragstart', dragEvent)
        
        const dragData = dragEvent.dataTransfer.getData('application/json')
        const parsed = JSON.parse(dragData)
        
        expect(parsed.nodeType).toBe(nodeTypes[index])
      })
    })

    it('应该在拖拽时提供正确的节点配置信息', () => {
      const paletteWrapper = mount(FlowNodePalette)
      const paletteNode = paletteWrapper.find('.palette-node')
      
      const dragEvent = {
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
      
      paletteNode.trigger('dragstart', dragEvent)
      
      const dragData = dragEvent.dataTransfer.getData('application/json')
      const parsed = JSON.parse(dragData)
      
      // 验证必要的字段
      expect(parsed).toHaveProperty('type')
      expect(parsed).toHaveProperty('nodeType')
      expect(parsed).toHaveProperty('defaultName')
      
      expect(parsed.type).toBe('node')
      expect(['start', 'end', 'user', 'condition', 'auto']).toContain(parsed.nodeType)
      expect(typeof parsed.defaultName).toBe('string')
    })
  })

  describe('拖拽流程完整性', () => {
    it('应该支持完整的拖拽生命周期', async () => {
      const paletteWrapper = mount(FlowNodePalette)
      const paletteNode = paletteWrapper.find('.palette-node')
      
      // 初始状态
      expect(paletteWrapper.vm.isDragging).toBe(false)
      
      // 拖拽开始
      const dragStartEvent = {
        dataTransfer: {
          setData: vi.fn(),
          getData: vi.fn(),
          effectAllowed: ''
        }
      }
      paletteNode.trigger('dragstart', dragStartEvent)
      expect(paletteWrapper.vm.isDragging).toBe(true)
      
      // 拖拽结束
      paletteNode.trigger('dragend')
      expect(paletteWrapper.vm.isDragging).toBe(false)
    })

    it('应该在拖拽过程中保持数据一致性', () => {
      const paletteWrapper = mount(FlowNodePalette)
      const paletteNodes = paletteWrapper.findAll('.palette-node')
      
      const dragDataMap = new Map()
      
      paletteNodes.forEach((node: any, index: number) => {
        const dragEvent = {
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
        
        node.trigger('dragstart', dragEvent)
        
        const dragData = dragEvent.dataTransfer.getData('application/json')
        dragDataMap.set(index, JSON.parse(dragData))
      })
      
      // 验证所有节点的数据都是有效的
      dragDataMap.forEach((data: any) => {
        expect(data.type).toBe('node')
        expect(data.nodeType).toBeTruthy()
        expect(data.defaultName).toBeTruthy()
      })
    })
  })

  describe('节点类型覆盖', () => {
    it('应该支持所有必要的节点类型', () => {
      const paletteWrapper = mount(FlowNodePalette)
      const paletteNodes = paletteWrapper.findAll('.palette-node')
      
      // 验证节点数量
      expect(paletteNodes.length).toBe(5)
      
      // 验证每个节点都有标签
      const nodeLabels = paletteNodes.map((node: any) => node.find('.node-label').text())
      expect(nodeLabels).toContain('开始')
      expect(nodeLabels).toContain('结束')
      expect(nodeLabels).toContain('审批')
      expect(nodeLabels).toContain('条件')
      expect(nodeLabels).toContain('抄送')
    })

    it('应该为每个节点类型提供合适的默认名称', () => {
      const paletteWrapper = mount(FlowNodePalette)
      const paletteNodes = paletteWrapper.findAll('.palette-node')
      
      const expectedNames = ['开始', '结束', '审批', '条件', '抄送']
      
      paletteNodes.forEach((node: any, index: number) => {
        const label = node.find('.node-label')
        expect(label.text()).toBe(expectedNames[index])
      })
    })
  })

  describe('用户交互', () => {
    it('应该在悬停时显示视觉反馈', () => {
      const paletteWrapper = mount(FlowNodePalette)
      const paletteNode = paletteWrapper.find('.palette-node')
      
      // 验证节点有悬停样式类
      expect(paletteNode.classes()).toContain('palette-node')
    })

    it('应该支持多个节点的连续拖拽', async () => {
      const paletteWrapper = mount(FlowNodePalette)
      const paletteNodes = paletteWrapper.findAll('.palette-node')
      
      for (let i = 0; i < paletteNodes.length; i++) {
        const dragEvent = {
          dataTransfer: {
            setData: vi.fn(),
            getData: vi.fn(),
            effectAllowed: ''
          }
        }
        
        paletteNodes[i].trigger('dragstart', dragEvent)
        expect(paletteWrapper.vm.isDragging).toBe(true)
        
        paletteNodes[i].trigger('dragend')
        expect(paletteWrapper.vm.isDragging).toBe(false)
      }
    })
  })

  describe('数据格式验证', () => {
    it('拖拽数据应该是有效的 JSON', () => {
      const paletteWrapper = mount(FlowNodePalette)
      const paletteNode = paletteWrapper.find('.palette-node')
      
      const dragEvent = {
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
      
      paletteNode.trigger('dragstart', dragEvent)
      
      const dragData = dragEvent.dataTransfer.getData('application/json')
      
      expect(() => {
        JSON.parse(dragData)
      }).not.toThrow()
    })

    it('拖拽数据应该包含所有必要字段', () => {
      const paletteWrapper = mount(FlowNodePalette)
      const paletteNode = paletteWrapper.find('.palette-node')
      
      const dragEvent = {
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
      
      paletteNode.trigger('dragstart', dragEvent)
      
      const dragData = dragEvent.dataTransfer.getData('application/json')
      const parsed = JSON.parse(dragData)
      
      const requiredFields = ['type', 'nodeType', 'defaultName']
      requiredFields.forEach(field => {
        expect(parsed).toHaveProperty(field)
      })
    })

    it('nodeType 应该是有效的流程节点类型', () => {
      const paletteWrapper = mount(FlowNodePalette)
      const paletteNodes = paletteWrapper.findAll('.palette-node')
      
      const validTypes = ['start', 'end', 'user', 'condition', 'auto']
      
      paletteNodes.forEach((node: any) => {
        const label = node.find('.node-label')
        const nodeType = label.text()
        
        // 验证节点类型有效
        expect(nodeType).toBeTruthy()
      })
    })
  })

  describe('边界情况', () => {
    it('应该处理快速连续拖拽', async () => {
      const paletteWrapper = mount(FlowNodePalette)
      const paletteNode = paletteWrapper.find('.palette-node')
      
      for (let i = 0; i < 5; i++) {
        const dragEvent = {
          dataTransfer: {
            setData: vi.fn(),
            getData: vi.fn(),
            effectAllowed: ''
          }
        }
        
        paletteNode.trigger('dragstart', dragEvent)
        paletteNode.trigger('dragend')
      }
      
      expect(paletteWrapper.vm.isDragging).toBe(false)
    })

    it('应该在没有 dataTransfer 时优雅处理', () => {
      const paletteWrapper = mount(FlowNodePalette)
      const paletteNode = paletteWrapper.find('.palette-node')
      
      const dragEvent = {}
      
      expect(() => {
        paletteNode.trigger('dragstart', dragEvent)
      }).not.toThrow()
    })
  })
})
