import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import NodeTemplateLibrary from '../NodeTemplateLibrary.vue'
import { BUILTIN_NODE_TEMPLATES, getTemplatesByCategory, getAllCategories } from '@/constants/nodeTemplates'

describe('NodeTemplateLibrary', () => {
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

  describe('模板库初始化', () => {
    it('应该正确加载内置模板', () => {
      expect(BUILTIN_NODE_TEMPLATES.length).toBeGreaterThan(0)
    })

    it('应该包含审批类模板', () => {
      const approvalTemplates = getTemplatesByCategory('approval')
      expect(approvalTemplates.length).toBeGreaterThan(0)
    })

    it('应该包含条件分支模板', () => {
      const conditionTemplates = getTemplatesByCategory('condition')
      expect(conditionTemplates.length).toBeGreaterThan(0)
    })

    it('应该包含自动节点模板', () => {
      const autoTemplates = getTemplatesByCategory('auto')
      expect(autoTemplates.length).toBeGreaterThan(0)
    })
  })

  describe('模板搜索功能', () => {
    it('应该能够按名称搜索模板', async () => {
      const vm = wrapper.vm
      vm.searchQuery = '经理'
      await wrapper.vm.$nextTick()

      const filtered = vm.filteredTemplates
      expect(filtered.length).toBeGreaterThan(0)
      expect(filtered.some((t: any) => t.name.includes('经理'))).toBe(true)
    })

    it('应该能够按描述搜索模板', async () => {
      const vm = wrapper.vm
      vm.searchQuery = '审批'
      await wrapper.vm.$nextTick()

      const filtered = vm.filteredTemplates
      expect(filtered.length).toBeGreaterThan(0)
    })

    it('搜索应该不区分大小写', async () => {
      const vm = wrapper.vm
      vm.searchQuery = 'MANAGER'
      await wrapper.vm.$nextTick()

      const filtered = vm.filteredTemplates
      expect(filtered.length).toBeGreaterThan(0)
    })

    it('清空搜索词应该显示所有模板', async () => {
      const vm = wrapper.vm
      vm.searchQuery = '经理'
      await wrapper.vm.$nextTick()
      expect(vm.filteredTemplates.length).toBeLessThan(BUILTIN_NODE_TEMPLATES.length)

      vm.searchQuery = ''
      await wrapper.vm.$nextTick()
      expect(vm.filteredTemplates.length).toBe(BUILTIN_NODE_TEMPLATES.length)
    })
  })

  describe('模板分类筛选', () => {
    it('应该能够按分类筛选模板', async () => {
      const vm = wrapper.vm
      vm.selectedCategory = 'approval'
      await wrapper.vm.$nextTick()

      const filtered = vm.filteredTemplates
      expect(filtered.every((t: any) => t.category === 'approval')).toBe(true)
    })

    it('应该能够清除分类筛选', async () => {
      const vm = wrapper.vm
      vm.selectedCategory = 'approval'
      await wrapper.vm.$nextTick()
      expect(vm.filteredTemplates.length).toBeLessThan(BUILTIN_NODE_TEMPLATES.length)

      vm.selectedCategory = null
      await wrapper.vm.$nextTick()
      expect(vm.filteredTemplates.length).toBe(BUILTIN_NODE_TEMPLATES.length)
    })

    it('应该提供所有可用分类', () => {
      const categories = getAllCategories()
      expect(categories.length).toBeGreaterThan(0)
      expect(categories).toContain('approval')
      expect(categories).toContain('condition')
      expect(categories).toContain('auto')
    })
  })

  describe('模板预览', () => {
    it('应该能够预览模板', async () => {
      const vm = wrapper.vm
      const template = BUILTIN_NODE_TEMPLATES[0]

      vm.selectTemplate(template)
      await wrapper.vm.$nextTick()

      expect(vm.showPreview).toBe(true)
      expect(vm.previewTemplate).toEqual(template)
    })

    it('应该能够关闭预览', async () => {
      const vm = wrapper.vm
      const template = BUILTIN_NODE_TEMPLATES[0]

      vm.selectTemplate(template)
      await wrapper.vm.$nextTick()
      expect(vm.showPreview).toBe(true)

      vm.showPreview = false
      await wrapper.vm.$nextTick()
      expect(vm.showPreview).toBe(false)
    })
  })

  describe('模板应用', () => {
    it('应该能够应用模板', async () => {
      const vm = wrapper.vm
      const template = BUILTIN_NODE_TEMPLATES[0]

      vm.applyTemplate(template)
      await wrapper.vm.$nextTick()

      expect(wrapper.emitted('apply-template')).toBeTruthy()
      expect(wrapper.emitted('apply-template')[0]).toEqual([template])
    })

    it('应用模板后应该关闭预览', async () => {
      const vm = wrapper.vm
      const template = BUILTIN_NODE_TEMPLATES[0]

      vm.selectTemplate(template)
      await wrapper.vm.$nextTick()
      expect(vm.showPreview).toBe(true)

      vm.applyTemplate(template)
      await wrapper.vm.$nextTick()
      expect(vm.showPreview).toBe(false)
    })
  })

  describe('模板配置验证', () => {
    it('经理审批模板应该有正确的配置', () => {
      const template = BUILTIN_NODE_TEMPLATES.find(t => t.id === 'approval-manager')
      expect(template).toBeDefined()
      expect(template?.config.type).toBe('user')
      expect(template?.config.assignee_type).toBe('role')
      expect(template?.config.approve_policy).toBe('all')
    })

    it('并行审批模板应该有正确的配置', () => {
      const template = BUILTIN_NODE_TEMPLATES.find(t => t.id === 'approval-parallel')
      expect(template).toBeDefined()
      expect(template?.config.type).toBe('user')
      expect(template?.config.approve_policy).toBe('any')
      expect(template?.config.route_mode).toBe('parallel')
    })

    it('比例审批模板应该有正确的阈值', () => {
      const template = BUILTIN_NODE_TEMPLATES.find(t => t.id === 'approval-percent')
      expect(template).toBeDefined()
      expect(template?.config.approve_policy).toBe('percent')
      expect(template?.config.approve_threshold).toBe(66)
    })

    it('带 SLA 的审批模板应该有 SLA 时长', () => {
      const template = BUILTIN_NODE_TEMPLATES.find(t => t.id === 'approval-with-sla')
      expect(template).toBeDefined()
      expect(template?.config.sla_hours).toBe(24)
    })

    it('自动抽检审批模板应该启用自动审批', () => {
      const template = BUILTIN_NODE_TEMPLATES.find(t => t.id === 'approval-auto-sample')
      expect(template).toBeDefined()
      expect(template?.config.auto_approve_enabled).toBe(true)
      expect(template?.config.auto_sample_ratio).toBe(0.1)
    })

    it('条件分支模板应该有正确的类型', () => {
      const template = BUILTIN_NODE_TEMPLATES.find(t => t.id === 'condition-amount')
      expect(template).toBeDefined()
      expect(template?.type).toBe('condition')
      expect(template?.config.type).toBe('condition')
    })
  })

  describe('模板元数据', () => {
    it('所有模板应该有 ID', () => {
      BUILTIN_NODE_TEMPLATES.forEach(template => {
        expect(template.id).toBeDefined()
        expect(template.id.length).toBeGreaterThan(0)
      })
    })

    it('所有模板应该有名称', () => {
      BUILTIN_NODE_TEMPLATES.forEach(template => {
        expect(template.name).toBeDefined()
        expect(template.name.length).toBeGreaterThan(0)
      })
    })

    it('所有模板应该有描述', () => {
      BUILTIN_NODE_TEMPLATES.forEach(template => {
        expect(template.description).toBeDefined()
        expect(template.description.length).toBeGreaterThan(0)
      })
    })

    it('所有模板应该标记为内置', () => {
      BUILTIN_NODE_TEMPLATES.forEach(template => {
        expect(template.isBuiltin).toBe(true)
      })
    })

    it('所有模板应该有配置', () => {
      BUILTIN_NODE_TEMPLATES.forEach(template => {
        expect(template.config).toBeDefined()
        expect(Object.keys(template.config).length).toBeGreaterThan(0)
      })
    })
  })

  describe('模板分类统计', () => {
    it('应该有多个审批模板', () => {
      const approvalTemplates = getTemplatesByCategory('approval')
      expect(approvalTemplates.length).toBeGreaterThanOrEqual(6)
    })

    it('应该有多个条件分支模板', () => {
      const conditionTemplates = getTemplatesByCategory('condition')
      expect(conditionTemplates.length).toBeGreaterThanOrEqual(3)
    })

    it('应该有多个自动节点模板', () => {
      const autoTemplates = getTemplatesByCategory('auto')
      expect(autoTemplates.length).toBeGreaterThanOrEqual(2)
    })
  })

  describe('组合搜索和筛选', () => {
    it('应该能够同时按分类和搜索词筛选', async () => {
      const vm = wrapper.vm
      vm.selectedCategory = 'approval'
      vm.searchQuery = '经理'
      await wrapper.vm.$nextTick()

      const filtered = vm.filteredTemplates
      expect(filtered.every((t: any) => t.category === 'approval')).toBe(true)
      expect(filtered.some((t: any) => t.name.includes('经理'))).toBe(true)
    })

    it('组合筛选结果应该是两个条件的交集', async () => {
      const vm = wrapper.vm
      vm.selectedCategory = 'approval'
      vm.searchQuery = '不存在的模板'
      await wrapper.vm.$nextTick()

      expect(vm.filteredTemplates.length).toBe(0)
    })
  })
})
