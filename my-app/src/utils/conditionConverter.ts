import type { ConditionNode, ConditionRule, ConditionGroup, Operator } from '@/types/condition'

export interface RouteRule {
  [key: string]: any
}

const OPERATOR_TO_JSONLOGIC: Record<Operator, string> = {
  'EQUALS': '==',
  'NOT_EQUALS': '!=',
  'GREATER_THAN': '>',
  'GREATER_EQUAL': '>=',
  'LESS_THAN': '<',
  'LESS_EQUAL': '<=',
  'BETWEEN': 'between',
  'CONTAINS': 'in',
  'NOT_CONTAINS': '!',
  'IN': 'in',
  'NOT_IN': '!',
  'HAS_ANY': 'or',
  'HAS_ALL': 'and',
  'IS_EMPTY': '==',
  'IS_NOT_EMPTY': '!=',
  'DATE_BEFORE_NOW': '<',
  'DATE_AFTER_NOW': '>',
}

const JSONLOGIC_TO_OPERATOR: Record<string, Operator> = {
  '==': 'EQUALS',
  '!=': 'NOT_EQUALS',
  '>': 'GREATER_THAN',
  '>=': 'GREATER_EQUAL',
  '<': 'LESS_THAN',
  '<=': 'LESS_EQUAL',
  'in': 'IN',
}

export function conditionNodeToRouteRule(node: ConditionNode | null): RouteRule | null {
  if (!node) return null

  if (node.type === 'RULE') {
    return ruleToJsonLogic(node)
  }

  if (node.type === 'GROUP') {
    return groupToJsonLogic(node)
  }

  return null
}

function ruleToJsonLogic(rule: ConditionRule): RouteRule {
  const jsonLogicOperator = OPERATOR_TO_JSONLOGIC[rule.operator] || '=='
  
  // 处理特殊操作符
  if (rule.operator === 'IS_EMPTY') {
    return { '==': [{ 'var': rule.fieldKey }, ''] }
  }
  if (rule.operator === 'IS_NOT_EMPTY') {
    return { '!=': [{ 'var': rule.fieldKey }, ''] }
  }
  if (rule.operator === 'NOT_CONTAINS') {
    return { '!': [{ 'in': [rule.value, { 'var': rule.fieldKey }] }] }
  }
  if (rule.operator === 'NOT_IN') {
    return { '!': [{ 'in': [{ 'var': rule.fieldKey }, rule.value] }] }
  }
  if (rule.operator === 'HAS_ANY') {
    return { 'or': rule.value.map((v: any) => ({ 'in': [v, { 'var': rule.fieldKey }] })) }
  }
  if (rule.operator === 'HAS_ALL') {
    return { 'and': rule.value.map((v: any) => ({ 'in': [v, { 'var': rule.fieldKey }] })) }
  }
  
  return { [jsonLogicOperator]: [{ 'var': rule.fieldKey }, rule.value] }
}

function groupToJsonLogic(group: ConditionGroup): RouteRule {
  if (!group.children || group.children.length === 0) {
    return {}
  }

  const rules = group.children
    .map(child => conditionNodeToRouteRule(child))
    .filter((rule): rule is RouteRule => rule !== null && Object.keys(rule).length > 0)

  if (rules.length === 0) {
    return {}
  }

  if (rules.length === 1) {
    return rules[0]
  }

  const logicKey = group.logic === 'AND' ? 'and' : 'or'
  return { [logicKey]: rules }
}

export function routeRuleToConditionNode(rule: RouteRule | null): ConditionNode | null {
  if (!rule || Object.keys(rule).length === 0) return null

  // 处理 and/or
  if (rule.and || rule.or) {
    return routeRuleToConditionGroup(rule)
  }

  // 处理单个规则
  return routeRuleToConditionRule(rule)
}

function routeRuleToConditionRule(rule: RouteRule): ConditionNode | null {
  // 找到操作符和值
  for (const [op, value] of Object.entries(rule)) {
    if (op === 'and' || op === 'or') continue
    
    const values = Array.isArray(value) ? value : []
    if (values.length >= 2) {
      const fieldRef = values[0]
      const fieldValue = values[1]
      
      if (fieldRef && typeof fieldRef === 'object' && 'var' in fieldRef) {
        const operator = JSONLOGIC_TO_OPERATOR[op] || 'EQUALS'
        return {
          type: 'RULE',
          fieldKey: fieldRef.var,
          fieldType: 'TEXT',
          operator,
          value: fieldValue,
        }
      }
    }
  }

  return null
}

function routeRuleToConditionGroup(rule: RouteRule): ConditionNode | null {
  const isAnd = 'and' in rule
  const conditions = isAnd ? rule.and : rule.or
  
  if (!conditions || !Array.isArray(conditions) || conditions.length === 0) {
    return null
  }

  const children = conditions
    .map(c => routeRuleToConditionNode(c))
    .filter((node): node is ConditionNode => node !== null)

  if (children.length === 0) return null

  return {
    type: 'GROUP',
    logic: isAnd ? 'AND' : 'OR',
    children,
  }
}
