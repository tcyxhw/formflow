import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import NodeTemplateLibrary from '../NodeTemplateLibrary.vue'
import { BUILTIN_NODE_TEMPLATES } from '@/constants/nodeTemplates'
import type { NodeTemplate } from '@/types/nodeTemplate'

describe('NodeTemplateLibrary 集成测试', () => {
  let wrapper: any

  beforeEach(() => {
    wrapper = mount(NodeTemplateLibrary, {
      props: {
        disabled: false
      },
      global: {
        stubs: {
          NInput: true,
          NSelect: true,
          NButton: true,
          NTag: true,
          NIcon: true,
          NEmpty: true,
          NModal: true,
          NDescriptions: true,
          NDescriptionsItem: true,
          NCode: true
        }
      }
    })
  })

  describe('完整工作流', () => {
    it('应该支持完整的模板选择和应用流程', async () => {
      const vm = wrapper.vm
      const template = BUILTIN_NODE_TEMPLATES[0]

      // 1. 选择模板
      vm.selectTemplate(template)
      await wrapper.vm.$nextTick()
      expect(vm.showPreview).toBe(true)
      expect(vm.previewTemplate).toEqual(template)

      // 2. 应用模板
      vm.applyTemplate(template)
      await wrapper.vm.$nextTick()

      // 3. 验证事件发出
      expect(wrapper.emitted('apply-template')).toBeTruthy()
      expect(wrapper.emitted('apply-template')[0][0]).toEqual(template)

      // 4. 验证预览关闭
      expect(vm.showPreview).toBe(false)
    })

    it('应该支持搜索后应用模板', async () => {
      const vm = wrapper.vm

      // 1. 搜索模板
      vm.searchQuery = '经理'
      await wrapper.vm.$nextTick()

      const filtered = vm.filteredTemplates
      expect(filtered.length).toBeGreaterThan(0)

      // 2. 选择搜索结果中的模板
      const template = filtered[0]
      vm.applyTemplate(template)
      await wrapper.vm.$nextTick()

      // 3. 验证事件发出
      expect(wrapper.emitted('apply-template')).toBeTruthy()
    })

    it('应该支持分类筛选后应用模板', async () => {
      const vm = wrapper.vm

      // 1. 按分类筛选
      vm.selectedCategory = 'approval'
      await wrapper.vm.$nextTick()

      const filtered = vm.filteredTemplates
      expect(filtered.length).toBeGreaterThan(0)
      expect(filtered.every((t: any) => t.category === 'approval')).toBe(true)

      // 2. 选择筛选结果中的模板
      const template = filtered[0]
      vm.applyTemplate(template)
      await wrapper.vm.$nextTick()

      // 3. 验证事件发出
      expect(wrapper.emitted('apply-template')).toBeTruthy()
    })
  })

  describe('模板应用场景', () => {
    it('应该能够应用经理审批模板', async () => {
      const vm = wrapper.vm
      const template = BUILTIN_NODE_TEMPLATES.find(t => t.id === 'approval-manager')!

      vm.applyTemplate(template)
      await wrapper.vm.$nextTick()

      const emitted = wrapper.emitted('apply-template')
      expect(emitted).toBeTruthy()
      expect(emitted[0][0].id).toBe('approval-manager')
      expect(emitted[0][0].config.assignee_type).toBe('role')
    })

    it('应该能够应用并行审批模板', async () => {
      const vm = wrapper.vm
      const template = BUILTIN_NODE_TEMPLATES.find(t => t.id === 'approval-parallel')!

      vm.applyTemplate(template)
      await wrapper.vm.$nextTick()

      const emitted = wrapper.emitted('apply-template')
      expect(emitted).toBeTruthy()
      expect(emitted[0][0].id).toBe('approval-parallel')
      expect(emitted[0][0].config.route_mode).toBe('parallel')
    })

    it('应该能够应用条件分支模板', async () => {
      const vm = wrapper.vm
      const template = BUILTIN_NODE_TEMPLATES.find(t => t.id === 'condition-amount')!

      vm.applyTemplate(template)
      await wrapper.vm.$nextTick()

      const emitted = wrapper.emitted('apply-template')
      expect(emitted).toBeTruthy()
      expect(emitted[0][0].type).toBe('condition')
    })

    it('应该能够应用自动节点模板', async () => {
      const vm = wrapper.vm
      const template = BUILTIN_NODE_TEMPLATES.find(t => t.id === 'auto-notification')!

      vm.applyTemplate(template)
      await wrapper.vm.$nextTick()

      const emitted = wrapper.emitted('apply-template')
      expect(emitted).toBeTruthy()
      expect(emitted[0][0].type).toBe('auto')
    })
  })

  describe('搜索和筛选组合', () => {
    it('应该支持多次搜索', async () => {
      const vm = wrapper.vm

      // 第一次搜索
      vm.searchQuery = '经理'
      await wrapper.vm.$nextTick()
      const firstResult = vm.filteredTemplates.length

      // 第二次搜索
      vm.searchQuery = '审批'
      await wrapper.vm.$nextTick()
      const secondResult = vm.filteredTemplates.length

      // 结果应该不同
      expect(firstResult).not.toBe(secondResult)
    })

    it('应该支持搜索和分类的组合', async () => {
      const vm = wrapper.vm

      // 只按分类筛选
      vm.selectedCategory = 'approval'
      await wrapper.vm.$nextTick()
      const categoryOnly = vm.filteredTemplates.length

      // 添加搜索条件
      vm.searchQuery = '经理'
      await wrapper.vm.$nextTick()
      const combined = vm.filteredTemplates.length

      // 组合结果应该小于等于分类结果
      expect(combined).toBeLessThanOrEqual(categoryOnly)
    })

    it('应该支持清除所有筛选条件', async () => {
      const vm = wrapper.vm

      // 设置筛选条件
      vm.selectedCategory = 'approval'
      vm.searchQuery = '经理'
      await wrapper.vm.$nextTick()
      const filtered = vm.filteredTemplates.length

      // 清除筛选条件
      vm.selectedCategory = null
      vm.searchQuery = ''
      await wrapper.vm.$nextTick()

      // 应该显示所有模板
      expect(vm.filteredTemplates.length).toBe(BUILTIN_NODE_TEMPLATES.length)
      expect(vm.filteredTemplates.length).toBeGreaterThan(filtered)
    })
  })

  describe('模板预览和应用流程', () => {
    it('应该能够预览多个模板', async () => {
      const vm = wrapper.vm

      // 预览第一个模板
      const template1 = BUILTIN_NODE_TEMPLATES[0]
      vm.selectTemplate(template1)
      await wrapper.vm.$nextTick()
      expect(vm.previewTemplate).toEqual(template1)

      // 预览第二个模板
      const template2 = BUILTIN_NODE_TEMPLATES[1]
      vm.selectTemplate(template2)
      await wrapper.vm.$nextTick()
      expect(vm.previewTemplate).toEqual(template2)
    })

    it('应该能够在预览后应用模板', async () => {
      const vm = wrapper.vm
      const template = BUILTIN_NODE_TEMPLATES[0]

      // 预览
      vm.selectTemplate(template)
      await wrapper.vm.$nextTick()
      expect(vm.showPreview).toBe(true)

      // 应用
      vm.applyTemplate(template)
      await wrapper.vm.$nextTick()

      // 验证
      expect(wrapper.emitted('apply-template')).toBeTruthy()
      expect(vm.showPreview).toBe(false)
    })

    it('应该能够在预览后关闭而不应用', async () => {
      const vm = wrapper.vm
      const template = BUILTIN_NODE_TEMPLATES[0]

      // 预览
      vm.selectTemplate(template)
      await wrapper.vm.$nextTick()
      expect(vm.showPreview).toBe(true)

      // 关闭预览
      vm.showPreview = false
      await wrapper.vm.$nextTick()

      // 验证没有发出应用事件
      expect(wrapper.emitted('apply-template')).toBeFalsy()
    })
  })

  describe('模板库状态管理', () => {
    it('应该正确维护搜索状态', async () => {
      const vm = wrapper.vm

      vm.searchQuery = '经理'
      await wrapper.vm.$nextTick()
      expect(vm.searchQuery).toBe('经理')

      vm.searchQuery = ''
      await wrapper.vm.$nextTick()
      expect(vm.searchQuery).toBe('')
    })

    it('应该正确维护分类筛选状态', async () => {
      const vm = wrapper.vm

      vm.selectedCategory = 'approval'
      await wrapper.vm.$nextTick()
      expect(vm.selectedCategory).toBe('approval')

      vm.selectedCategory = null
      await wrapper.vm.$nextTick()
      expect(vm.selectedCategory).toBeNull()
    })

    it('应该正确维护预览状态', async () => {
      const vm = wrapper.vm
      const template = BUILTIN_NODE_TEMPLATES[0]

      expect(vm.showPreview).toBe(false)

      vm.selectTemplate(template)
      await wrapper.vm.$nextTick()
      expect(vm.showPreview).toBe(true)

      vm.showPreview = false
      await wrapper.vm.$nextTick()
      expect(vm.showPreview).toBe(false)
    })
  })

  describe('模板库性能', () => {
    it('应该能够快速过滤大量模板', async () => {
      const vm = wrapper.vm

      const startTime = performance.now()
      vm.searchQuery = '审批'
      await wrapper.vm.$nextTick()
      const endTime = performance.now()

      // 过滤应该在 500ms 内完成
      expect(endTime - startTime).toBeLessThan(500)
    })

    it('应该能够快速切换分类', async () => {
      const vm = wrapper.vm

      const startTime = performance.now()
      vm.selectedCategory = 'approval'
      await wrapper.vm.$nextTick()
      vm.selectedCategory = 'condition'
      await wrapper.vm.$nextTick()
      vm.selectedCategory = 'auto'
      await wrapper.vm.$nextTick()
      const endTime = performance.now()

      // 切换应该在 500ms 内完成
      expect(endTime - startTime).toBeLessThan(500)
    })
  })

  describe('模板库可用性', () => {
    it('应该提供足够的模板选择', () => {
      expect(BUILTIN_NODE_TEMPLATES.length).toBeGreaterThanOrEqual(10)
    })

    it('应该覆盖主要的审批场景', () => {
      const approvalTemplates = BUILTIN_NODE_TEMPLATES.filter(t => t.category === 'approval')
      expect(approvalTemplates.length).toBeGreaterThanOrEqual(6)

      // 验证覆盖的场景
      const ids = approvalTemplates.map(t => t.id)
      expect(ids).toContain('approval-manager')
      expect(ids).toContain('approval-parallel')
      expect(ids).toContain('approval-all-agree')
      expect(ids).toContain('approval-percent')
    })

    it('应该覆盖主要的条件分支场景', () => {
      const conditionTemplates = BUILTIN_NODE_TEMPLATES.filter(t => t.category === 'condition')
      expect(conditionTemplates.length).toBeGreaterThanOrEqual(3)

      const ids = conditionTemplates.map(t => t.id)
      expect(ids).toContain('condition-amount')
      expect(ids).toContain('condition-department')
    })
  })
})
