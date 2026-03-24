// src/types/ai.ts
/**
 * AI 相关类型定义
 */

import type { FieldProps, FieldPropValue } from './field'
import type { LogicValue } from './logic'

/**
 * AI 思考模式枚举
 */
export enum ThinkingType {
    /** 启用深度思考模式（适用于复杂表单） */
    ENABLED = 'enabled',
    /** 禁用思考模式（适用于简单表单） */
    DISABLED = 'disabled'
  }
  
  /**
   * AI 表单生成请求参数
   */
  export interface AIFormGenerateRequest {
    /** 表单需求描述（5-2000字符） */
    prompt: string
    /** AI 思考模式（可选，默认 enabled） */
    thinking_type?: ThinkingType
  }
  
  /**
   * AI 表单生成响应数据
   */
  export interface AIFormGenerateResponse {
    /** 完整的表单配置 JSON */
    config: FormConfig
    /** 配置说明 */
    summary: string
    /** 字段数量 */
    field_count: number
    /** 逻辑规则数量 */
    rule_count: number
  }
  
  /**
   * 表单配置结构（AI 生成的完整配置）
   */
  export interface FormConfig {
    /** 表单名称 */
    name: string
    /** 表单分类 */
    category: string
    /** 访问模式 */
    accessMode: 'authenticated' | 'public'
    /** 是否允许编辑 */
    allowEdit: boolean
    /** 最大编辑次数（0 表示不限制） */
    maxEditCount: number
    /** 提交截止时间（ISO 格式或 null） */
    submitDeadline: string | null
    /** 表单字段配置 */
    formSchema: FormSchema
    /** UI 布局配置 */
    uiSchema: UISchema
    /** 逻辑规则配置 */
    logicSchema: LogicSchema
  }
  
  /**
   * 表单字段配置
   */
  export interface FormSchema {
    /** 版本号 */
    version: string
    /** 字段列表 */
    fields: FormField[]
    /** 字段顺序 */
    fieldOrder: string[]
  }
  
  /**
   * 表单字段定义
   */
  export interface FormField {
    /** 字段唯一 ID */
    id: string
    /** 字段类型 */
    type: FieldType
    /** 字段标签 */
    label: string
    /** 字段描述（可选） */
    description?: string
    /** 是否必填 */
    required: boolean
    /** 默认值（可选） */
    defaultValue?: FieldPropValue
    /** 字段属性 */
    props?: FieldProps
    /** 验证规则（可选） */
    validation?: FieldValidation
  }
  
  /**
   * 字段类型
   */
  export type FieldType =
    | 'text'
    | 'textarea'
    | 'number'
    | 'phone'
    | 'email'
    | 'select'
    | 'radio'
    | 'checkbox'
    | 'switch'
    | 'date'
    | 'date-range'
    | 'time'
    | 'datetime'
    | 'rate'
    | 'upload'
    | 'calculated'
    | 'divider'
    | 'description'
  
  /**
   * 字段验证规则
   */
  export interface FieldValidation {
    /** 正则表达式 */
    pattern?: string
    /** 最小值 */
    min?: number
    /** 最大值 */
    max?: number
    /** 错误提示 */
    message?: string
    /** 触发时机 */
    trigger?: 'blur' | 'change'
  }
  
  /**
   * UI 布局配置
   */
  export interface UISchema {
    /** 布局设置 */
    layout: {
      /** 布局类型 */
      type: 'vertical' | 'horizontal' | 'grid'
      /** 标签宽度 */
      labelWidth: number
      /** 标签位置 */
      labelPosition: 'left' | 'right' | 'top'
      /** 表单尺寸 */
      size: 'small' | 'medium' | 'large'
    }
    /** 行配置 */
    rows: UIRow[]
    /** 分组配置 */
    groups: UIGroup[]
  }
  
  export interface UIGroup {
    id: string
    title: string
    description?: string
    fields: string[]
  }
  
  /**
   * UI 行配置
   */
  export interface UIRow {
    /** 行内字段 */
    fields: {
      /** 字段 ID */
      id: string
      /** 栅格占位（1-24） */
      span: number
    }[]
  }
  
  /**
   * 逻辑规则配置
   */
  export interface LogicSchema {
    /** 规则列表 */
    rules: LogicRule[]
  }
  
  /**
   * 逻辑规则
   */
  export interface LogicRule {
    /** 规则 ID */
    id: string
    /** 规则名称 */
    name: string
    /** 触发器 */
    trigger: {
      /** 触发类型 */
      type: 'change' | 'blur' | 'init'
      /** 触发字段 */
      fields: string[]
    }
    /** 条件表达式 */
    condition: string
    /** 执行动作 */
    actions: LogicAction[]
  }
  
  /**
   * 逻辑动作
   */
  export interface LogicAction {
    /** 动作类型 */
    type: 'visible' | 'required' | 'disabled' | 'value'
    /** 目标字段 */
    target: string
    /** 动作值 */
    value: LogicValue
  }