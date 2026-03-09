/**
 * 逻辑规则定义
 */

export interface LogicRule {
    id: string
    name?: string
    enabled: boolean
    trigger: LogicTrigger
    conditions: LogicCondition[]
    conditionLogic: 'AND' | 'OR'
    actions: LogicAction[]
  }
  
  export interface LogicTrigger {
    type: 'change' | 'blur' | 'focus' | 'load'
    fields: string[]
  }
  
  export type LogicValue = string | number | boolean | null | string[] | number[]
  
  export interface LogicCondition {
    field: string
    operator: ConditionOperator
    value: LogicValue
    valueType?: 'fixed' | 'field'
  }
  
  export enum ConditionOperator {
    EQUALS = 'equals',
    NOT_EQUALS = 'notEquals',
    GREATER_THAN = 'greaterThan',
    GREATER_OR_EQUAL = 'greaterOrEqual',
    LESS_THAN = 'lessThan',
    LESS_OR_EQUAL = 'lessOrEqual',
    CONTAINS = 'contains',
    NOT_CONTAINS = 'notContains',
    IS_EMPTY = 'isEmpty',
    IS_NOT_EMPTY = 'isNotEmpty',
  }
  
  export interface LogicAction {
    type: ActionType
    target: string
    value?: LogicValue
  }
  
  export enum ActionType {
    SHOW = 'show',
    HIDE = 'hide',
    ENABLE = 'enable',
    DISABLE = 'disable',
    SET_REQUIRED = 'setRequired',
    SET_OPTIONAL = 'setOptional',
    SET_VALUE = 'setValue',
    CLEAR_VALUE = 'clearValue',
  }
  
  export interface LogicSchema {
    rules: LogicRule[]
  }