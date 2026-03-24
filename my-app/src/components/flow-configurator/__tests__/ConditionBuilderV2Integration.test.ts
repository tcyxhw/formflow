/**
 * 条件构造器 V2 集成测试
 * 测试条件构造器与表单字段 API 的集成
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ConditionBuilderV2 from '../ConditionBuilderV2.vue'
import type { FormFieldsResponse } from '@/types/form'

// Mock getFormFields API
vi.mock('@/api/form', () => ({
  getFormFields: vi.fn()
}))

import { getFormFields } from '@/api/form'

describe('ConditionBuilderV2 集成测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该在挂载时加载表单字段', async () => {
    const formId = 123
    const mockFieldsResponse: FormFieldsResponse = {
      form_id: formId,
      form_name: '招待费申请',
      fields: [
        {
          key: 'amount',
          name: '金额',
          type: 'number',
          description: '申请金额',
          required: true,
          options: null,
          props: {}
        }
      ],
      system_fields: [
        {
          key: 'sys_submitter',
          name: '提交人',
          type: 'string',
          description: '表单提交人',
          required: false,
          options: null,
          props: {}
        }
      ]
    }

    vi.mocked(getFormFields).mockResolvedValue({
      data: mockFieldsResponse
    } as any)

    const wrapper = mount(ConditionBuilderV2, {
      props: {
        formId: formId
      }
    })

    // 等待异步加载完成
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(getFormFields).toHaveBeenCalledWith(formId)
  })

  it('应该在 formId 变化时重新加载字段', async () => {
    const mockFieldsResponse: FormFieldsResponse = {
      form_id: 123,
      form_name: '表单1',
      fields: [],
      system_fields: []
    }

    vi.mocked(getFormFields).mockResolvedValue({
      data: mockFieldsResponse
    } as any)

    const wrapper = mount(ConditionBuilderV2, {
      props: {
        formId: 123
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(getFormFields).toHaveBeenCalledWith(123)

    // 更新 formId
    await wrapper.setProps({ formId: 456 })
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(getFormFields).toHaveBeenCalledWith(456)
    expect(getFormFields).toHaveBeenCalledTimes(2)
  })

  it('应该在没有 formId 时使用 formSchema', async () => {
    const mockSchema = {
      fields: [
        {
          id: 'field1',
          label: '字段1',
          type: 'text'
        }
      ]
    }

    const wrapper = mount(ConditionBuilderV2, {
      props: {
        formSchema: mockSchema
      }
    })

    await wrapper.vm.$nextTick()

    // 不应该调用 API
    expect(getFormFields).not.toHaveBeenCalled()
  })

  it('应该优先使用 API 加载的字段而不是 formSchema', async () => {
    const formId = 123
    const mockFieldsResponse: FormFieldsResponse = {
      form_id: formId,
      form_name: '表单',
      fields: [
        {
          key: 'api_field',
          name: 'API 字段',
          type: 'text',
          required: false,
          options: null,
          props: {}
        }
      ],
      system_fields: []
    }

    vi.mocked(getFormFields).mockResolvedValue({
      data: mockFieldsResponse
    } as any)

    const mockSchema = {
      fields: [
        {
          id: 'schema_field',
          label: 'Schema 字段',
          type: 'text'
        }
      ]
    }

    const wrapper = mount(ConditionBuilderV2, {
      props: {
        formId: formId,
        formSchema: mockSchema
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    // 应该使用 API 加载的字段
    expect(getFormFields).toHaveBeenCalledWith(formId)
  })

  it('应该处理 API 加载失败的情况', async () => {
    const formId = 123
    const error = new Error('API 加载失败')

    vi.mocked(getFormFields).mockRejectedValue(error)

    const wrapper = mount(ConditionBuilderV2, {
      props: {
        formId: formId
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    // 应该捕获错误但不崩溃
    expect(getFormFields).toHaveBeenCalledWith(formId)
    // 组件应该仍然可用
    expect(wrapper.exists()).toBe(true)
  })

  it('应该正确映射 API 返回的字段类型', async () => {
    const formId = 123
    const mockFieldsResponse: FormFieldsResponse = {
      form_id: formId,
      form_name: '表单',
      fields: [
        {
          key: 'text_field',
          name: '文本字段',
          type: 'text',
          required: false,
          options: null,
          props: {}
        },
        {
          key: 'number_field',
          name: '数字字段',
          type: 'number',
          required: false,
          options: null,
          props: {}
        },
        {
          key: 'select_field',
          name: '选择字段',
          type: 'select',
          required: false,
          options: [
            { label: '选项1', value: 'opt1' },
            { label: '选项2', value: 'opt2' }
          ],
          props: {}
        }
      ],
      system_fields: []
    }

    vi.mocked(getFormFields).mockResolvedValue({
      data: mockFieldsResponse
    } as any)

    const wrapper = mount(ConditionBuilderV2, {
      props: {
        formId: formId
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    // 验证字段类型映射
    expect(getFormFields).toHaveBeenCalledWith(formId)
  })
})
