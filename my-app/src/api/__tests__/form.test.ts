/**
 * 表单 API 测试
 * 测试表单相关的 API 接口，包括字段查询
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as formApi from '../form'
import type { FormFieldsResponse } from '@/types/form'

// Mock request 模块
vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}))

import request from '@/utils/request'

describe('Form API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getFormFields', () => {
    it('应该调用正确的 API 端点', async () => {
      const formId = 123
      const mockResponse = {
        data: {
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
      }

      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await formApi.getFormFields(formId)

      expect(request.get).toHaveBeenCalledWith(`/api/v1/forms/${formId}/fields`)
      expect(result.data.form_id).toBe(formId)
      expect(result.data.fields).toHaveLength(1)
      expect(result.data.system_fields).toHaveLength(1)
    })

    it('应该返回包含表单字段和系统字段的响应', async () => {
      const formId = 456
      const mockResponse = {
        data: {
          form_id: formId,
          form_name: '出差申请',
          fields: [
            {
              key: 'destination',
              name: '目的地',
              type: 'text',
              description: '出差目的地',
              required: true,
              options: null,
              props: {}
            },
            {
              key: 'days',
              name: '天数',
              type: 'number',
              description: '出差天数',
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
              required: false,
              options: null,
              props: {}
            },
            {
              key: 'sys_submit_time',
              name: '提交时间',
              type: 'datetime',
              required: false,
              options: null,
              props: {}
            }
          ]
        }
      }

      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await formApi.getFormFields(formId)

      expect(result.data.fields).toHaveLength(2)
      expect(result.data.system_fields).toHaveLength(2)
      expect(result.data.fields[0].key).toBe('destination')
      expect(result.data.system_fields[0].key).toBe('sys_submitter')
    })

    it('应该处理包含选项的字段', async () => {
      const formId = 789
      const mockResponse = {
        data: {
          form_id: formId,
          form_name: '请假申请',
          fields: [
            {
              key: 'leave_type',
              name: '请假类型',
              type: 'select',
              description: '选择请假类型',
              required: true,
              options: [
                { label: '年假', value: 'annual' },
                { label: '病假', value: 'sick' },
                { label: '事假', value: 'personal' }
              ],
              props: {}
            }
          ],
          system_fields: []
        }
      }

      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await formApi.getFormFields(formId)

      expect(result.data.fields[0].options).toHaveLength(3)
      expect(result.data.fields[0].options?.[0].label).toBe('年假')
    })
  })

  describe('其他表单 API', () => {
    it('getFormDetail 应该调用正确的端点', async () => {
      const formId = 123
      vi.mocked(request.get).mockResolvedValue({ data: {} })

      await formApi.getFormDetail(formId)

      expect(request.get).toHaveBeenCalledWith(`/api/v1/forms/${formId}`)
    })

    it('listForms 应该支持查询参数', async () => {
      vi.mocked(request.get).mockResolvedValue({ data: { items: [], total: 0 } })

      await formApi.listForms({ page: 1, page_size: 10 })

      expect(request.get).toHaveBeenCalledWith('/api/v1/forms', {
        params: { page: 1, page_size: 10 }
      })
    })
  })
})
