import type { ConditionNode, ConditionRule, ConditionGroup, Operator } from '@/types/condition'

export interface RouteRule {
  logic?: 'and' | 'or'
  rules?: RouteRule[]
  field?: string
  operator?: string
  value?: any
}

const OPERATOR_TO_BACKEND: Record<Operator, string> = {
  'EQUALS': 'equals',
  'NOT_EQUALS': 'not_equals',
  'GREATER_THAN': 'gt',
  'GREATER_EQUAL': 'gte',
  'LESS_THAN': 'lt',
  'LESS_EQUAL': 'lte',
  'BETWEEN': 'between',
  'CONTAINS': 'contains',
  'NOT_CONTAINS': 'not_contains',
  'IN': 'in',
  'NOT_IN': 'not_in',
  'HAS_ANY': 'has_any',
  'HAS_ALL': 'has_all',
  'IS_EMPTY': 'is_empty',
  'IS_NOT_EMPTY': 'is_not_empty',
  'DATE_BEFORE_NOW': 'lt',
  'DATE_AFTER_NOW': 'gt',
}

const BACKEND_TO_OPERATOR: Record<string, Operator> = {
  'equals': 'EQUALS',
  'not_equals': 'NOT_EQUALS',
  'gt': 'GREATER_THAN',
  'gte': 'GREATER_EQUAL',
  'lt': 'LESS_THAN',
  'lte': 'LESS_EQUAL',
  'between': 'BETWEEN',
  'contains': 'CONTAINS',
  'not_contains': 'NOT_CONTAINS',
  'in': 'IN',
  'not_in': 'NOT_IN',
  'has_any': 'HAS_ANY',
  'has_all': 'HAS_ALL',
  'is_empty': 'IS_EMPTY',
  'is_not_empty': 'IS_NOT_EMPTY',
}

export function conditionNodeToRouteRule(node: ConditionNode | null): RouteRule | null {
  if (!node) return null

  if (node.type === 'RULE') {
    return ruleToRouteRule(node)
  }

  if (node.type === 'GROUP') {
    return groupToRouteRule(node)
  }

  return null
}

function ruleToRouteRule(rule: ConditionRule): RouteRule {
  const backendOperator = OPERATOR_TO_BACKEND[rule.operator] || 'equals'
  
  return {
    field: rule.fieldKey,
    operator: backendOperator,
    value: rule.value,
  }
}

function groupToRouteRule(group: ConditionGroup): RouteRule {
  if (!group.children || group.children.length === 0) {
    return {}
  }

  const rules = group.children
    .map(child => conditionNodeToRouteRule(child))
    .filter((rule): rule is RouteRule => rule !== null)

  if (rules.length === 0) {
    return {}
  }

  if (rules.length === 1) {
    return rules[0]
  }

  return {
    logic: group.logic.toLowerCase() as 'and' | 'or',
    rules,
  }
}

export function routeRuleToConditionNode(rule: RouteRule | null): ConditionNode | null {
  if (!rule) return null

  if (rule.rules && rule.rules.length > 0) {
    return routeRuleToConditionGroup(rule)
  }

  if (rule.field && rule.operator) {
    return routeRuleToConditionRule(rule)
  }

  return null
}

function routeRuleToConditionRule(rule: RouteRule): ConditionRule | null {
  if (!rule.field || !rule.operator) return null

  const operator = BACKEND_TO_OPERATOR[rule.operator] || 'EQUALS'

  return {
    type: 'RULE',
    fieldKey: rule.field,
    fieldType: 'TEXT',
    operator,
    value: rule.value,
  }
}

function routeRuleToConditionGroup(rule: RouteRule): ConditionGroup | null {
  if (!rule.rules || rule.rules.length === 0) return null

  const children = rule.rules
    .map(r => routeRuleToConditionNode(r))
    .filter((node): node is ConditionNode => node !== null)

  if (children.length === 0) return null

  return {
    type: 'GROUP',
    logic: (rule.logic?.toUpperCase() as 'AND' | 'OR') || 'AND',
    children,
  }
}
