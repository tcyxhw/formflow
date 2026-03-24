/**
 * Expected Behavior 测试 - 提交详情显示修复
 * 
 * **Validates: Requirements 1.2, 1.3**
 * 
 * 此测试验证修复后的正确行为：
 * 1. 前端不显示快照信息卡片
 * 2. 前端不显示流程轨迹卡片
 * 3. 前端基本信息卡片只显示 3 个字段
 * 4. 前端字段标签使用中文标签
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { NMessageProvider, NConfigProvider } from 'naive-ui'
import SubmissionDetailView from '../SubmissionDetailView.vue'
import type { SubmissionDetail } from '@/types/submission'

// Mock API 调用
vi.mock('@/api/submission', () => ({
  getSubmissionDetail: vi.fn()
}))

vi.mock('@/api/approvals', () => ({
  getProcessTimeline: vi.fn()
}))

// Mock vue-router
vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { id: '123' }
  }),
  useRouter: () => ({
    back: vi.fn()
  })
}))

describe('Expected Behavior - 提交详情显示正确', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  /**
   * Property 1: Expected Behavior - 前端不显示快照信息卡片
   */
  it('Property 1: 提交详情页面不显示快照信息卡片', async () => {
    const { getSubmissionDetail } = await import('@/api/submission')
    const { getProcessTimeline } = await import('@/api/approvals')

    const mockSubmission: SubmissionDetail = {
      id: 123,
      form_id: 1,
      form_name: '测试表单',
      form_version_id: 1,
      submitter_user_id: 1,
      submitter_name: '张三',
      data_jsonb: { student_name: '李四', rating: 5, feedback: '很好' },
      snapshot_json: {
        version: 2,
        published_at: '2024-01-01T00:00:00Z',
        field_labels: { student_name: '学生姓名', rating: '评分', feedback: '反馈' }
      },
      status: 'submitted',
      duration: 120,
      source: 'pc',
      ip_address: '192.168.1.1',
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
      process_instance_id: null,
      process_state: null,
      attachments: []
    }

    vi.mocked(getSubmissionDetail).mockResolvedValue({
      code: 200,
      data: mockSubmission,
      message: 'success'
    })

    vi.mocked(getProcessTimeline).mockResolvedValue({
      code: 200,
      data: { state: 'running', entries: [] },
      message: 'success'
    })

    const wrapper = mount(
      {
        components: { SubmissionDetailView, NMessageProvider, NConfigProvider },
        template: '<n-config-provider><n-message-provider><SubmissionDetailView /></n-message-provider></n-config-provider>'
      },
      {
        global: {
          stubs: {
            'n-spin': { template: '<div><slot /></div>', props: ['show'] },
            'n-page-header': { template: '<div><slot name="title" /></div>' },
            'n-card': { template: '<div><slot name="header" /><slot /></div>', props: ['title', 'bordered'] },
            'n-descriptions': { template: '<div><slot /></div>', props: ['label-placement', 'column', 'bordered', 'size'] },
            'n-descriptions-item': { template: '<div><span class="label">{{ label }}</span><slot /></div>', props: ['label'] }
          }
        }
      }
    )

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const component = wrapper.findComponent(SubmissionDetailView)
    const html = component.html()
    const hasSnapshotCard = html.includes('快照信息')
    expect(hasSnapshotCard, '修复后不应该显示快照信息卡片').toBe(false)
  })

  /**
   * Property 1: Expected Behavior - 前端不显示流程轨迹卡片
   */
  it('Property 1: 提交详情页面不显示流程轨迹卡片', async () => {
    const { getSubmissionDetail } = await import('@/api/submission')
    const { getProcessTimeline } = await import('@/api/approvals')

    const mockSubmission: SubmissionDetail = {
      id: 123,
      form_id: 1,
      form_name: '测试表单',
      form_version_id: 1,
      submitter_user_id: 1,
      submitter_name: '张三',
      data_jsonb: { name: '测试' },
      snapshot_json: { version: 1, published_at: '2024-01-01T00:00:00Z', field_labels: { name: '姓名' } },
      status: 'submitted',
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
      process_instance_id: 1,
      process_state: 'running',
      attachments: []
    }

    vi.mocked(getSubmissionDetail).mockResolvedValue({ code: 200, data: mockSubmission, message: 'success' })
    vi.mocked(getProcessTimeline).mockResolvedValue({ code: 200, data: { state: 'running', entries: [] }, message: 'success' })

    const wrapper = mount(
      {
        components: { SubmissionDetailView, NMessageProvider, NConfigProvider },
        template: '<n-config-provider><n-message-provider><SubmissionDetailView /></n-message-provider></n-config-provider>'
      },
      { global: { stubs: { 'n-spin': { template: '<div><slot /></div>', props: ['show'] }, 'n-page-header': { template: '<div><slot name="title" /></div>' }, 'n-card': { template: '<div><slot name="header" /><slot /></div>', props: ['title', 'bordered'] } } } }
    )

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const component = wrapper.findComponent(SubmissionDetailView)
    const html = component.html()
    const hasTimelineCard = html.includes('流程轨迹')
    expect(hasTimelineCard, '修复后不应该显示流程轨迹卡片').toBe(false)
  })

  /**
   * Property 1: Expected Behavior - 基本信息卡片只显示 3 个字段
   */
  it('Property 1: 基本信息卡片只显示 3 个字段', async () => {
    const { getSubmissionDetail } = await import('@/api/submission')
    const { getProcessTimeline } = await import('@/api/approvals')

    const mockSubmission: SubmissionDetail = {
      id: 123,
      form_id: 1,
      form_name: '测试表单',
      form_version_id: 1,
      submitter_user_id: 1,
      submitter_name: '张三',
      data_jsonb: { name: '测试' },
      snapshot_json: { version: 1, published_at: '2024-01-01T00:00:00Z', field_labels: { name: '姓名' } },
      status: 'submitted',
      duration: 120,
      source: 'pc',
      ip_address: '192.168.1.1',
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
      process_instance_id: null,
      process_state: null,
      attachments: []
    }

    vi.mocked(getSubmissionDetail).mockResolvedValue({ code: 200, data: mockSubmission, message: 'success' })
    vi.mocked(getProcessTimeline).mockResolvedValue({ code: 200, data: { state: 'running', entries: [] }, message: 'success' })

    const wrapper = mount(
      {
        components: { SubmissionDetailView, NMessageProvider, NConfigProvider },
        template: '<n-config-provider><n-message-provider><SubmissionDetailView /></n-message-provider></n-config-provider>'
      },
      {
        global: {
          stubs: {
            'n-spin': { template: '<div><slot /></div>', props: ['show'] },
            'n-page-header': { template: '<div><slot name="title" /></div>' },
            'n-card': { template: '<div><slot name="header" /><slot /></div>', props: ['title', 'bordered'] },
            'n-descriptions': { template: '<div><slot /></div>', props: ['label-placement', 'column', 'bordered', 'size'] },
            'n-descriptions-item': { template: '<div><span class="label">{{ label }}</span><slot /></div>', props: ['label'] }
          }
        }
      }
    )

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const component = wrapper.findComponent(SubmissionDetailView)
    const html = component.html()
    
    // 打印 HTML 用于调试
    console.log('基本信息测试 HTML:', html)
    
    // 检查基本信息卡片中的字段 - 使用 label 属性值
    const hasSubmissionId = html.includes('label="提交 ID"') || html.includes("label='提交 ID'")
    const hasFormName = html.includes('label="表单名称"') || html.includes("label='表单名称'")
    const hasSubmitter = html.includes('label="提交人"') || html.includes("label='提交人'")
    const hasStatus = html.includes('label="状态"') || html.includes("label='状态'")
    const hasSubmitTime = html.includes('label="提交时间"') || html.includes("label='提交时间'")
    const hasDuration = html.includes('label="耗时"') || html.includes("label='耗时'")
    const hasSource = html.includes('label="来源"') || html.includes("label='来源'")
    const hasIpAddress = html.includes('label="IP 地址"') || html.includes("label='IP 地址'")

    const fieldCount = [hasSubmissionId, hasFormName, hasSubmitter, hasStatus, hasSubmitTime, hasDuration, hasSource, hasIpAddress].filter(Boolean).length

    expect(fieldCount, '修复后应该只显示 3 个基本信息字段').toBe(3)
  })

  /**
   * Property 1: Expected Behavior - 字段标签使用中文标签
   */
  it('Property 1: 字段标签使用中文标签', async () => {
    const { getSubmissionDetail } = await import('@/api/submission')
    const { getProcessTimeline } = await import('@/api/approvals')

    const mockSubmission: SubmissionDetail = {
      id: 123,
      form_id: 1,
      form_name: '测试表单',
      form_version_id: 1,
      submitter_user_id: 1,
      submitter_name: '张三',
      data_jsonb: { rating: 5, feedback: '很好', course_name: '数学' },
      snapshot_json: {
        version: 1,
        published_at: '2024-01-01T00:00:00Z',
        field_labels: { rating: '评分', feedback: '反馈', course_name: '课程名称' }
      },
      status: 'submitted',
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
      process_instance_id: null,
      process_state: null,
      attachments: []
    }

    vi.mocked(getSubmissionDetail).mockResolvedValue({ code: 200, data: mockSubmission, message: 'success' })
    vi.mocked(getProcessTimeline).mockResolvedValue({ code: 200, data: { state: 'running', entries: [] }, message: 'success' })

    const wrapper = mount(
      {
        components: { SubmissionDetailView, NMessageProvider, NConfigProvider },
        template: '<n-config-provider><n-message-provider><SubmissionDetailView /></n-message-provider></n-config-provider>'
      },
      {
        global: {
          stubs: {
            'n-spin': { template: '<div><slot /></div>', props: ['show'] },
            'n-page-header': { template: '<div><slot name="title" /></div>' },
            'n-card': { template: '<div><slot name="header" /><slot /></div>', props: ['title', 'bordered'] },
            'n-descriptions': { template: '<div><slot /></div>', props: ['label-placement', 'column', 'bordered', 'size'] },
            'n-descriptions-item': { template: '<div><span class="label">{{ label }}</span><slot /></div>', props: ['label'] }
          }
        }
      }
    )

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const component = wrapper.findComponent(SubmissionDetailView)
    const html = component.html()
    
    // 打印 HTML 用于调试
    console.log('字段标签测试 HTML:', html)

    // 关键断言：修复后，应该显示中文标签
    const hasRatingLabel = html.includes('label="评分"') || html.includes("label='评分'")
    const hasFeedbackLabel = html.includes('label="反馈"') || html.includes("label='反馈'")
    const hasCourseNameLabel = html.includes('label="课程名称"') || html.includes("label='课程名称'")

    expect(hasRatingLabel, '修复后应该显示中文标签"评分"').toBe(true)
    expect(hasFeedbackLabel, '修复后应该显示中文标签"反馈"').toBe(true)
    expect(hasCourseNameLabel, '修复后应该显示中文标签"课程名称"').toBe(true)
  })
})