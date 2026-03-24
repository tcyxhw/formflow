/**
 * 条件构造器类型定义
 */

// 字段类型
export type FieldType = 
  | 'TEXT'
  | 'TEXTAREA'
  | 'NUMBER'
  | 'SINGLE_SELECT'
  | 'MULTI_SELECT'
  | 'DATE'
  | 'DATETIME'
  | 'DATE_RANGE'
  | 'USER'
  | 'USER_MULTI'
  | 'DEPARTMENT'
  | 'FILE'

// 运算符
export type Operator =
  | 'EQUALS'
  | 'NOT_EQUALS'
  | 'GREATER_THAN'
  | 'GREATER_EQUAL'
  | 'LESS_THAN'
  | 'LESS_EQUAL'
  | 'BETWEEN'
  | 'CONTAINS'
  | 'NOT_CONTAINS'
  | 'IN'
  | 'NOT_IN'
  | 'HAS_ANY'
  | 'HAS_ALL'
  | 'IS_EMPTY'
  | 'IS_NOT_EMPTY'
  | 'DATE_BEFORE_NOW'
  | 'DATE_AFTER_NOW'

// 逻辑关系
export type LogicType = 'AND' | 'OR'

// 字段定义
export interface FieldDefinition {
  key: string
  name: string
  type: FieldType
  options?: Array<{ label: string; value: string | number }>
  isSystem?: boolean
}

// 条件规则（叶子节点）
export interface ConditionRule {
  type: 'RULE'
  fieldKey: string
  fieldType: FieldType
  operator: Operator
  value: any
}

// 条件组（非叶子节点，可嵌套）
export interface ConditionGroup {
  type: 'GROUP'
  logic: LogicType
  children: (ConditionRule | ConditionGroup)[]
}

// 条件树的根节点
export type ConditionNode = ConditionRule | ConditionGroup

// 运算符配置
export interface OperatorConfig {
  value: Operator
  label: string
  needsValue: boolean
  valueType: 'SINGLE' | 'MULTI' | 'RANGE' | 'NONE'
}

// 运算符中文显示名映射
export const OPERATOR_LABEL_MAP: Record<Operator, string> = {
  'EQUALS': '等于',
  'NOT_EQUALS': '不等于',
  'GREATER_THAN': '大于',
  'GREATER_EQUAL': '大于等于',
  'LESS_THAN': '小于',
  'LESS_EQUAL': '小于等于',
  'BETWEEN': '介于',
  'CONTAINS': '包含',
  'NOT_CONTAINS': '不包含',
  'IN': '属于',
  'NOT_IN': '不属于',
  'HAS_ANY': '包含任一',
  'HAS_ALL': '包含全部',
  'IS_EMPTY': '为空',
  'IS_NOT_EMPTY': '不为空',
  'DATE_BEFORE_NOW': '早于当前时间',
  'DATE_AFTER_NOW': '晚于当前时间',
}

// 日期类型字段的运算符显示名覆盖
export const DATE_OPERATOR_LABEL_MAP: Record<Operator, string> = {
  'EQUALS': '等于',
  'NOT_EQUALS': '不等于',
  'GREATER_THAN': '晚于',
  'GREATER_EQUAL': '不早于',
  'LESS_THAN': '早于',
  'LESS_EQUAL': '不晚于',
  'BETWEEN': '介于',
  'CONTAINS': '包含',
  'NOT_CONTAINS': '不包含',
  'IN': '属于',
  'NOT_IN': '不属于',
  'HAS_ANY': '包含任一',
  'HAS_ALL': '包含全部',
  'IS_EMPTY': '为空',
  'IS_NOT_EMPTY': '不为空',
  'DATE_BEFORE_NOW': '早于当前时间',
  'DATE_AFTER_NOW': '晚于当前时间',
}

// 获取运算符显示名（支持字段类型覆盖）
export function getOperatorLabel(operator: Operator, fieldType?: FieldType): string {
  // 如果是 DATE、DATETIME 或 DATE_RANGE 类型，使用日期类型的显示名
  if (fieldType === 'DATE' || fieldType === 'DATETIME' || fieldType === 'DATE_RANGE') {
    return DATE_OPERATOR_LABEL_MAP[operator] || OPERATOR_LABEL_MAP[operator] || operator
  }
  return OPERATOR_LABEL_MAP[operator] || operator
}

// 字段类型对应的运算符
export const OPERATOR_MAP: Record<FieldType, OperatorConfig[]> = {
  TEXT: [
    { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'CONTAINS', label: '包含', needsValue: true, valueType: 'SINGLE' },
    { value: 'NOT_CONTAINS', label: '不包含', needsValue: true, valueType: 'SINGLE' },
    { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
    { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
  ],
  TEXTAREA: [
    { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'CONTAINS', label: '包含', needsValue: true, valueType: 'SINGLE' },
    { value: 'NOT_CONTAINS', label: '不包含', needsValue: true, valueType: 'SINGLE' },
    { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
    { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
  ],
  NUMBER: [
    { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'GREATER_THAN', label: '大于', needsValue: true, valueType: 'SINGLE' },
    { value: 'GREATER_EQUAL', label: '大于等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'LESS_THAN', label: '小于', needsValue: true, valueType: 'SINGLE' },
    { value: 'LESS_EQUAL', label: '小于等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'BETWEEN', label: '介于', needsValue: true, valueType: 'RANGE' },
    { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
    { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
  ],
  SINGLE_SELECT: [
    { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'IN', label: '属于', needsValue: true, valueType: 'MULTI' },
    { value: 'NOT_IN', label: '不属于', needsValue: true, valueType: 'MULTI' },
    { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
    { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
  ],
  MULTI_SELECT: [
    { value: 'HAS_ANY', label: '包含任一', needsValue: true, valueType: 'MULTI' },
    { value: 'HAS_ALL', label: '包含全部', needsValue: true, valueType: 'MULTI' },
    { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
    { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
  ],
  DATE: [
    { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'GREATER_THAN', label: '晚于', needsValue: true, valueType: 'SINGLE' },
    { value: 'GREATER_EQUAL', label: '不早于', needsValue: true, valueType: 'SINGLE' },
    { value: 'LESS_THAN', label: '早于', needsValue: true, valueType: 'SINGLE' },
    { value: 'LESS_EQUAL', label: '不晚于', needsValue: true, valueType: 'SINGLE' },
    { value: 'BETWEEN', label: '介于', needsValue: true, valueType: 'RANGE' },
    { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
    { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
  ],
  DATETIME: [
    { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'GREATER_THAN', label: '晚于', needsValue: true, valueType: 'SINGLE' },
    { value: 'GREATER_EQUAL', label: '不早于', needsValue: true, valueType: 'SINGLE' },
    { value: 'LESS_THAN', label: '早于', needsValue: true, valueType: 'SINGLE' },
    { value: 'LESS_EQUAL', label: '不晚于', needsValue: true, valueType: 'SINGLE' },
    { value: 'BETWEEN', label: '介于', needsValue: true, valueType: 'RANGE' },
    { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
    { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
  ],
  DATE_RANGE: [
    { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'GREATER_THAN', label: '晚于', needsValue: true, valueType: 'SINGLE' },
    { value: 'GREATER_EQUAL', label: '不早于', needsValue: true, valueType: 'SINGLE' },
    { value: 'LESS_THAN', label: '早于', needsValue: true, valueType: 'SINGLE' },
    { value: 'LESS_EQUAL', label: '不晚于', needsValue: true, valueType: 'SINGLE' },
    { value: 'BETWEEN', label: '介于', needsValue: true, valueType: 'RANGE' },
    { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
    { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
  ],
  USER: [
    { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'IN', label: '属于', needsValue: true, valueType: 'MULTI' },
    { value: 'NOT_IN', label: '不属于', needsValue: true, valueType: 'MULTI' },
    { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
    { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
  ],
  USER_MULTI: [
    { value: 'HAS_ANY', label: '包含任一', needsValue: true, valueType: 'MULTI' },
    { value: 'HAS_ALL', label: '包含全部', needsValue: true, valueType: 'MULTI' },
    { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
    { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
  ],
  DEPARTMENT: [
    { value: 'EQUALS', label: '等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'NOT_EQUALS', label: '不等于', needsValue: true, valueType: 'SINGLE' },
    { value: 'IN', label: '属于', needsValue: true, valueType: 'MULTI' },
    { value: 'NOT_IN', label: '不属于', needsValue: true, valueType: 'MULTI' },
    { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
    { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
  ],
  FILE: [
    { value: 'IS_EMPTY', label: '为空', needsValue: false, valueType: 'NONE' },
    { value: 'IS_NOT_EMPTY', label: '不为空', needsValue: false, valueType: 'NONE' },
  ],
}
