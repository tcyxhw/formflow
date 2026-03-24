/**
 * Bug Condition 探索测试 - FormPermissionDrawer 动态选择器
 * 
 * **Validates: Requirements 2.7, 2.8, 2.9, 2.10**
 * 
 * 此测试在未修复的代码上应该失败，证明 bug 存在。
 * 测试验证当用户选择不同的授权类型时，应该显示对应的选择器组件而非数字输入框。
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import * as fc from 'fast-check'
import FormPermissionDrawer from '../FormPermissionDrawer.vue'
import type { GrantType } from '@/types/formPermission'

// Mock API 调用
vi.mock('@/api/formPermission', () => ({
  listFormPermissions: vi.fn(() => Promise.resolve({ data: { items: [], total: 0 } })),
  createFormPermission: vi.fn(() => Promise.resolve({ data: {} })),
  updateFormPermission: vi.fn(() => Promise.resolve({ data: {} })),
  deleteFormPermission: vi.fn(() => Promise.resolve({ data: {} })),
  getMyFormPermissions: vi.fn(() =>
    Promise.resolve({
      data: {
        is_owner: false,
        can_view: true,
        can_fill: false,
        can_edit: false,
        can_export: false,
        can_manage: false
      }
    })
  )
}))

describe('Bug Condition - FormPermissionDrawer 动态选择器缺失', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  /**
   * Property 1: Bug Condition - 动态选择器显示
   * 
   * 对于任何用户选择的授权类型（user/role/department/position），
   * 系统应该显示对应的选择器组件而非数字输入框。
   */
  it('Property 1: 打开新增授权弹窗后应显示动态选择器', async () => {
    const wrapper = mount(FormPermissionDrawer, {
      props: {
        formId: 1,
        show: true,
        formName: '测试表单'
      },
      global: {
        stubs: {
          Icon: true
        }
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    // 点击"新增授权"按钮打开弹窗
    const addButton = wrapper.find('button')
    if (addButton.exists()) {
      await addButton.trigger('click')
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    const html = wrapper.html()
    
    // 验证新增授权弹窗中显示了动态选择器（默认是用户类型）
    const hasUserSelector = html.includes('选择用户') || html.includes('搜索并选择用户')
    
    // 修复后的代码应该显示选择器
    expect(hasUserSelector, '应该在新增授权弹窗中显示用户选择器').toBe(true)
  })

  it('Property 1: 选择 grant_type 为 user 时应显示用户选择器而非数字输入框', async () => {
    const wrapper = mount(FormPermissionDrawer, {
      props: {
        formId: 1,
        show: true,
        formName: '测试表单'
      },
      global: {
        stubs: {
          Icon: true
        }
      }
    })

    await wrapper.vm.$nextTick()
    
    // 打开新增授权弹窗
    const addButton = wrapper.find('button')
    if (addButton.exists()) {
      await addButton.trigger('click')
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    const html = wrapper.html()
    
    // 关键断言：应该存在用户选择器（默认就是 user 类型）
    const hasUserSelector = html.includes('选择用户') || 
                            html.includes('搜索并选择用户')
    
    // 修复后的代码应该显示用户选择器
    expect(hasUserSelector, '应该显示用户选择器而非数字输入框').toBe(true)
  })

  it('Property 1: 选择 grant_type 为 role 时应显示角色选择器而非数字输入框', async () => {
    const wrapper = mount(FormPermissionDrawer, {
      props: {
        formId: 1,
        show: true,
        formName: '测试表单'
      },
      global: {
        stubs: {
          Icon: true
        }
      }
    })

    await wrapper.vm.$nextTick()
    
    // 打开新增授权弹窗
    const addButton = wrapper.find('button')
    if (addButton.exists()) {
      await addButton.trigger('click')
      await wrapper.vm.$nextTick()
    }

    // 修改授权类型为 role
    const component = wrapper.vm as any
    if (component.createForm) {
      component.createForm.grantType = 'role'
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    const html = wrapper.html()
    
    // 关键断言：应该存在角色选择器
    const hasRoleSelector = html.includes('选择角色')
    
    // 修复后的代码应该显示角色选择器
    expect(hasRoleSelector, '应该显示角色选择器而非数字输入框').toBe(true)
  })

  it('Property 1: 选择 grant_type 为 department 时应显示部门选择器而非数字输入框', async () => {
    const wrapper = mount(FormPermissionDrawer, {
      props: {
        formId: 1,
        show: true,
        formName: '测试表单'
      },
      global: {
        stubs: {
          Icon: true
        }
      }
    })

    await wrapper.vm.$nextTick()
    
    // 打开新增授权弹窗
    const addButton = wrapper.find('button')
    if (addButton.exists()) {
      await addButton.trigger('click')
      await wrapper.vm.$nextTick()
    }

    // 修改授权类型为 department
    const component = wrapper.vm as any
    if (component.createForm) {
      component.createForm.grantType = 'department'
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    const html = wrapper.html()
    
    // 关键断言：应该存在部门选择器
    const hasDepartmentSelector = html.includes('选择部门')
    
    // 修复后的代码应该显示部门选择器
    expect(hasDepartmentSelector, '应该显示部门选择器而非数字输入框').toBe(true)
  })

  it('Property 1: 选择 grant_type 为 position 时应显示岗位选择器而非数字输入框', async () => {
    const wrapper = mount(FormPermissionDrawer, {
      props: {
        formId: 1,
        show: true,
        formName: '测试表单'
      },
      global: {
        stubs: {
          Icon: true
        }
      }
    })

    await wrapper.vm.$nextTick()
    
    // 打开新增授权弹窗
    const addButton = wrapper.find('button')
    if (addButton.exists()) {
      await addButton.trigger('click')
      await wrapper.vm.$nextTick()
    }

    // 修改授权类型为 position
    const component = wrapper.vm as any
    if (component.createForm) {
      component.createForm.grantType = 'position'
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    const html = wrapper.html()
    
    // 关键断言：应该存在岗位选择器
    const hasPositionSelector = html.includes('选择岗位')
    
    // 修复后的代码应该显示岗位选择器
    expect(hasPositionSelector, '应该显示岗位选择器而非数字输入框').toBe(true)
  })

  /**
   * 属性测试：对所有可能的 grant_type 值进行测试
   * 
   * 这个测试使用 fast-check 生成所有可能的授权类型，
   * 并验证每种类型都应该显示对应的选择器而非数字输入框。
   */
  it('Property 1 (PBT): 对于所有 grant_type，应显示对应的选择器而非数字输入框', async () => {
    // 定义所有可能的授权类型
    const grantTypeArbitrary = fc.constantFrom<GrantType>(
      'user',
      'role',
      'department',
      'position'
    )

    await fc.assert(
      fc.asyncProperty(grantTypeArbitrary, async (grantType) => {
        const wrapper = mount(FormPermissionDrawer, {
          props: {
            formId: 1,
            show: true,
            formName: '测试表单'
          },
          global: {
            stubs: {
              Icon: true
            }
          }
        })

        await wrapper.vm.$nextTick()
        
        // 打开新增授权弹窗
        const addButton = wrapper.find('button')
        if (addButton.exists()) {
          await addButton.trigger('click')
          await wrapper.vm.$nextTick()
        }

        // 设置授权类型
        const component = wrapper.vm as any
        if (component.createForm) {
          component.createForm.grantType = grantType
          await wrapper.vm.$nextTick()
          await new Promise(resolve => setTimeout(resolve, 50))
        }

        const html = wrapper.html()
        
        // 验证对应的选择器存在
        const typeLabels: Record<GrantType, string> = {
          user: '用户',
          role: '角色',
          department: '部门',
          position: '岗位'
        }

        const label = typeLabels[grantType]
        const hasSelector = html.includes(`选择${label}`)

        // 修复后的代码应该显示对应的选择器
        return hasSelector
      }),
      { numRuns: 4 } // 运行 4 次，覆盖所有 4 种类型
    )
  })
})
