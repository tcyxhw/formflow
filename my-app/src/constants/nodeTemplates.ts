/**
 * 节点模板库 - 内置模板定义
 */

import type { NodeTemplate } from '@/types/nodeTemplate'

/**
 * 内置节点模板库
 */
export const BUILTIN_NODE_TEMPLATES: NodeTemplate[] = [
  // 审批类模板
  {
    id: 'approval-manager',
    name: '经理审批',
    description: '由直属经理进行审批',
    type: 'user',
    category: 'approval',
    isBuiltin: true,
    config: {
      name: '经理审批',
      type: 'user',
      assignee_type: 'role',
      assignee_value: { role_id: 'manager' },
      approve_policy: 'all',
      route_mode: 'exclusive',
      allow_delegate: true,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_START',
      metadata: {
        description: '由直属经理进行审批，需要全部同意'
      }
    }
  },
  {
    id: 'approval-department-head',
    name: '部门负责人审批',
    description: '由部门负责人进行审批',
    type: 'user',
    category: 'approval',
    isBuiltin: true,
    config: {
      name: '部门负责人审批',
      type: 'user',
      assignee_type: 'role',
      assignee_value: { role_id: 'department_head' },
      approve_policy: 'all',
      route_mode: 'exclusive',
      allow_delegate: true,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_START',
      metadata: {
        description: '由部门负责人进行审批'
      }
    }
  },
  {
    id: 'approval-parallel',
    name: '并行审批',
    description: '多人并行审批，任意一人同意即可',
    type: 'user',
    category: 'approval',
    isBuiltin: true,
    config: {
      name: '并行审批',
      type: 'user',
      assignee_type: 'group',
      approve_policy: 'any',
      route_mode: 'parallel',
      allow_delegate: true,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_START',
      metadata: {
        description: '多人并行审批，任意一人同意即可通过'
      }
    }
  },
  {
    id: 'approval-all-agree',
    name: '全部同意审批',
    description: '多人审批，全部同意才能通过',
    type: 'user',
    category: 'approval',
    isBuiltin: true,
    config: {
      name: '全部同意审批',
      type: 'user',
      assignee_type: 'group',
      approve_policy: 'all',
      route_mode: 'parallel',
      allow_delegate: true,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_START',
      metadata: {
        description: '多人审批，全部同意才能通过'
      }
    }
  },
  {
    id: 'approval-percent',
    name: '比例审批',
    description: '多人审批，达到指定比例即可通过',
    type: 'user',
    category: 'approval',
    isBuiltin: true,
    config: {
      name: '比例审批',
      type: 'user',
      assignee_type: 'group',
      approve_policy: 'percent',
      approve_threshold: 66,
      route_mode: 'parallel',
      allow_delegate: true,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      reject_strategy: 'TO_START',
      metadata: {
        description: '多人审批，达到 66% 比例即可通过'
      }
    }
  },
  {
    id: 'approval-with-sla',
    name: '带 SLA 的审批',
    description: '带有 SLA 时限的审批节点',
    type: 'user',
    category: 'approval',
    isBuiltin: true,
    config: {
      name: '带 SLA 的审批',
      type: 'user',
      assignee_type: 'role',
      assignee_value: { role_id: 'manager' },
      approve_policy: 'all',
      route_mode: 'exclusive',
      allow_delegate: true,
      auto_approve_enabled: false,
      auto_sample_ratio: 0,
      sla_hours: 24,
      reject_strategy: 'TO_START',
      metadata: {
        description: '24 小时内必须完成审批'
      }
    }
  },
  {
    id: 'approval-auto-sample',
    name: '自动抽检审批',
    description: '启用自动抽检的审批节点',
    type: 'user',
    category: 'approval',
    isBuiltin: true,
    config: {
      name: '自动抽检审批',
      type: 'user',
      assignee_type: 'role',
      assignee_value: { role_id: 'manager' },
      approve_policy: 'all',
      route_mode: 'exclusive',
      allow_delegate: true,
      auto_approve_enabled: true,
      auto_sample_ratio: 0.1,
      reject_strategy: 'TO_START',
      metadata: {
        description: '10% 的请求进行人工审批，其余自动通过'
      }
    }
  },

  // 条件分支模板
  {
    id: 'condition-amount',
    name: '金额条件分支',
    description: '根据金额进行条件分支',
    type: 'condition',
    category: 'condition',
    isBuiltin: true,
    config: {
      name: '金额条件分支',
      type: 'condition',
      route_mode: 'exclusive',
      metadata: {
        description: '根据表单中的金额字段进行条件分支'
      }
    }
  },
  {
    id: 'condition-department',
    name: '部门条件分支',
    description: '根据部门进行条件分支',
    type: 'condition',
    category: 'condition',
    isBuiltin: true,
    config: {
      name: '部门条件分支',
      type: 'condition',
      route_mode: 'exclusive',
      metadata: {
        description: '根据表单中的部门字段进行条件分支'
      }
    }
  },
  {
    id: 'condition-user-type',
    name: '用户类型条件分支',
    description: '根据用户类型进行条件分支',
    type: 'condition',
    category: 'condition',
    isBuiltin: true,
    config: {
      name: '用户类型条件分支',
      type: 'condition',
      route_mode: 'exclusive',
      metadata: {
        description: '根据用户类型进行条件分支'
      }
    }
  },

  // 自动节点模板
  {
    id: 'auto-notification',
    name: '自动通知',
    description: '自动发送通知',
    type: 'auto',
    category: 'auto',
    isBuiltin: true,
    config: {
      name: '自动通知',
      type: 'auto',
      route_mode: 'exclusive',
      metadata: {
        description: '自动发送邮件或短信通知'
      }
    }
  },
  {
    id: 'auto-webhook',
    name: '自动 Webhook',
    description: '调用外部 Webhook',
    type: 'auto',
    category: 'auto',
    isBuiltin: true,
    config: {
      name: '自动 Webhook',
      type: 'auto',
      route_mode: 'exclusive',
      metadata: {
        description: '调用外部系统的 Webhook 接口'
      }
    }
  }
]

/**
 * 按分类获取模板
 */
export function getTemplatesByCategory(category: string): NodeTemplate[] {
  return BUILTIN_NODE_TEMPLATES.filter(t => t.category === category)
}

/**
 * 按类型获取模板
 */
export function getTemplatesByType(type: string): NodeTemplate[] {
  return BUILTIN_NODE_TEMPLATES.filter(t => t.type === type)
}

/**
 * 获取所有分类
 */
export function getAllCategories(): string[] {
  const categories = new Set(BUILTIN_NODE_TEMPLATES.map(t => t.category))
  return Array.from(categories)
}

/**
 * 根据 ID 获取模板
 */
export function getTemplateById(id: string): NodeTemplate | undefined {
  return BUILTIN_NODE_TEMPLATES.find(t => t.id === id)
}
