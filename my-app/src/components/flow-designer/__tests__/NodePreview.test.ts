import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import NodePreview from '../NodePreview.vue'
import type { FlowNodeConfig } from '@/types/flow'

describe('NodePreview', () => {
  let wrapper: any

  beforeEach(() => {
    wrapper = mount(NodePreview, {
      props: {
        node: undefined
      },
      global: {
        stubs: {
          NDescriptions: true,
          NDescriptionsItem: true,
          NTag: true,
          NEmpty: true,
          NCode: true
        }
      }
    })
  })

  describe('组件初始化', () => {
    it('应该能够正确渲染', () => {
      expect(wrapper.exists()).toBe(true)
    })

    it('没有节点时应该显示空状态', () => {
      expect(wrapper.text()).toContain('请选择节点进行预览')
    })

    it('应该能够接收节点 prop', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'node_1',
        name: '测试节点',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('测试节点')
    })
  })

  describe('节点类型显示', () => {
    it('应该能够显示开始节点', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'start',
        name: '开始',
        type: 'start',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('开始')
    })

    it('应该能够显示人工审批节点', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'user',
        name: '审批',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('人工审批')
    })

    it('应该能够显示条件分支节点', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'condition',
        name: '条件分支',
        type: 'condition',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        condition_branches: {
          branches: [],
          default_target_node_id: 2
        },
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('条件分支')
    })

    it('应该能够显示自动节点', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'auto',
        name: '自动通知',
        type: 'auto',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('自动节点')
    })

    it('应该能够显示结束节点', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'end',
        name: '结束',
        type: 'end',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('结束')
    })
  })

  describe('审批配置显示', () => {
    it('应该能够显示审批人类型', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'node_1',
        name: '审批',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('role')
    })

    it('应该能够显示会签策略', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'node_1',
        name: '审批',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'any',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('任意一人')
    })

    it('应该能够显示百分比阈值', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'node_1',
        name: '审批',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'percent',
        approve_threshold: 66,
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('66%')
    })

    it('应该能够显示代理状态', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'node_1',
        name: '审批',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('是')
    })
  })

  describe('SLA 配置显示', () => {
    it('应该能够显示 SLA 时长', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'node_1',
        name: '审批',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        sla_hours: 24,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('24 小时')
    })

    it('应该能够显示未设置 SLA', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'node_1',
        name: '审批',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('未设置')
    })
  })

  describe('自动审批显示', () => {
    it('应该能够显示自动审批状态', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'node_1',
        name: '审批',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: true,
        auto_sample_ratio: 0.1,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('10.0%')
    })
  })

  describe('条件分支显示', () => {
    it('应该能够显示条件分支', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'condition',
        name: '条件分支',
        type: 'condition',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: false,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        condition_branches: {
          branches: [
            {
              priority: 1,
              label: '金额 > 1000',
              condition: { '>': [{ var: 'amount' }, 1000] },
              target_node_id: 2
            }
          ],
          default_target_node_id: 3
        },
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('金额 > 1000')
    })
  })

  describe('元数据显示', () => {
    it('应该能够显示元数据', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'node_1',
        name: '审批',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {
          description: '这是一个测试节点',
          version: '1.0'
        }
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('元数据')
    })

    it('应该能够隐藏空元数据', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'node_1',
        name: '审批',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).not.toContain('元数据')
    })
  })

  describe('节点更新', () => {
    it('应该能够更新节点', async () => {
      const node1: FlowNodeConfig = {
        id: 1,
        temp_id: 'node_1',
        name: '节点 1',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node: node1 })
      expect(wrapper.text()).toContain('节点 1')

      const node2: FlowNodeConfig = {
        id: 2,
        temp_id: 'node_2',
        name: '节点 2',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node: node2 })
      expect(wrapper.text()).toContain('节点 2')
      expect(wrapper.text()).not.toContain('节点 1')
    })

    it('应该能够清除节点', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'node_1',
        name: '节点 1',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('节点 1')

      await wrapper.setProps({ node: undefined })
      expect(wrapper.text()).toContain('请选择节点进行预览')
    })
  })

  describe('特殊情况', () => {
    it('应该能够处理没有 ID 的节点', async () => {
      const node: FlowNodeConfig = {
        temp_id: 'node_1',
        name: '测试节点',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('测试节点')
    })

    it('应该能够处理没有 temp_id 的节点', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        name: '测试节点',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.text()).toContain('测试节点')
    })

    it('应该能够处理长节点名称', async () => {
      const node: FlowNodeConfig = {
        id: 1,
        temp_id: 'node_1',
        name: '这是一个非常长的节点名称，用来测试长文本的显示效果和截断处理',
        type: 'user',
        assignee_type: 'role',
        approve_policy: 'all',
        route_mode: 'exclusive',
        allow_delegate: true,
        auto_approve_enabled: false,
        auto_sample_ratio: 0,
        reject_strategy: 'TO_START',
        metadata: {}
      }

      await wrapper.setProps({ node })
      expect(wrapper.exists()).toBe(true)
    })
  })
})
