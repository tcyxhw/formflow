/**
 * FlowDesigner 组件验证脚本
 * 用于验证组件能否正常导入和使用
 */

import FlowDesigner from '../FlowDesigner.vue'
import type { ComponentPublicInstance } from 'vue'

describe('FlowDesigner Component Verification', () => {
  it('应该能正确导入 FlowDesigner 组件', () => {
    expect(FlowDesigner).toBeDefined()
    expect(FlowDesigner.name).toBe('FlowDesigner')
  })

  it('应该有正确的组件结构', () => {
    expect(FlowDesigner.template).toBeDefined()
    expect(FlowDesigner.setup).toBeDefined()
  })

  it('应该导出正确的类型', () => {
    // 验证组件是一个有效的 Vue 组件
    expect(typeof FlowDesigner).toBe('object')
    expect(FlowDesigner.__vccOpts || FlowDesigner).toBeDefined()
  })

  it('应该包含所有必要的子组件导入', () => {
    const componentCode = FlowDesigner.toString()
    expect(componentCode).toContain('FlowCanvas')
    expect(componentCode).toContain('FlowNodePalette')
    expect(componentCode).toContain('FlowNodeEditor')
    expect(componentCode).toContain('FlowRouteEditor')
  })

  it('应该包含所有必要的事件处理器', () => {
    const componentCode = FlowDesigner.toString()
    expect(componentCode).toContain('handleSelectNode')
    expect(componentCode).toContain('handleSelectRoute')
    expect(componentCode).toContain('handleUpdatePosition')
    expect(componentCode).toContain('handleAddRoute')
    expect(componentCode).toContain('handleDeleteNode')
    expect(componentCode).toContain('handleDeleteRoute')
    expect(componentCode).toContain('handleSaveDraft')
    expect(componentCode).toContain('handlePublish')
  })

  it('应该包含所有必要的状态变量', () => {
    const componentCode = FlowDesigner.toString()
    expect(componentCode).toContain('activeTab')
    expect(componentCode).toContain('showPublishDialog')
    expect(componentCode).toContain('publishVersionTag')
    expect(componentCode).toContain('publishChangelog')
  })

  it('应该使用 Pinia store', () => {
    const componentCode = FlowDesigner.toString()
    expect(componentCode).toContain('useFlowDraftStore')
  })

  it('应该使用 Vue Router', () => {
    const componentCode = FlowDesigner.toString()
    expect(componentCode).toContain('useRouter')
    expect(componentCode).toContain('useRoute')
  })

  it('应该使用 Naive UI 组件', () => {
    const componentCode = FlowDesigner.toString()
    expect(componentCode).toContain('NButton')
    expect(componentCode).toContain('NModal')
    expect(componentCode).toContain('NForm')
  })

  it('应该有正确的样式类', () => {
    const componentCode = FlowDesigner.toString()
    expect(componentCode).toContain('flow-designer-container')
    expect(componentCode).toContain('designer-header')
    expect(componentCode).toContain('designer-body')
    expect(componentCode).toContain('designer-sidebar')
  })

  it('应该支持响应式设计', () => {
    const componentCode = FlowDesigner.toString()
    expect(componentCode).toContain('@media')
  })
})
