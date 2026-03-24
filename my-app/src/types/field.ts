/**
 * 字段类型定义
 */

export enum FieldType {
    // 文本输入类
    TEXT = 'text',
    TEXTAREA = 'textarea',
    NUMBER = 'number',
    PHONE = 'phone',
    EMAIL = 'email',
    
    // 日期时间类
    DATE = 'date',
    DATE_RANGE = 'date-range',
    TIME = 'time',
    DATETIME = 'datetime',
    
    // 选择类
    SELECT = 'select',
    RADIO = 'radio',
    CHECKBOX = 'checkbox',
    SWITCH = 'switch',
    
    // 评分类
    RATE = 'rate',
    
    // 上传类
    UPLOAD = 'upload',
    
    // 计算类
    CALCULATED = 'calculated',
    
    // 布局类
    DIVIDER = 'divider',
    DESCRIPTION = 'description',
  }
  
  type FieldPropPrimitive = string | number | boolean | null | undefined
export type FieldPropValue =
  | FieldPropPrimitive
  | FieldPropPrimitive[]
  | Record<string, unknown>
  | Array<Record<string, unknown>>
export type FieldProps = Record<string, FieldPropValue>

  export interface FormField {
    id: string
    type: FieldType
    label: string
    description?: string
    required: boolean
    defaultValue?: FieldPropValue
    props: FieldProps
    validation?: FieldValidation
  }
  
  export interface FieldValidation {
    pattern?: string
    min?: number
    max?: number
    message?: string
    trigger?: 'blur' | 'change'
  }
  
  export interface SelectOption {
    label: string
    value: string | number
    disabled?: boolean
    [key: string]: unknown
  }
  
  // 字段属性类型定义
  export interface TextFieldProps {
    placeholder?: string
    maxLength?: number
    minLength?: number
    showWordLimit?: boolean
    clearable?: boolean
    disabled?: boolean
    readonly?: boolean
  }
  
  export interface NumberFieldProps {
    placeholder?: string
    min?: number
    max?: number
    step?: number
    precision?: number
    disabled?: boolean
    readonly?: boolean
  }
  
  export interface SelectFieldProps {
    placeholder?: string
    options: SelectOption[]
    multiple?: boolean
    clearable?: boolean
    filterable?: boolean
    disabled?: boolean
  }
  
  export interface DateFieldProps {
    placeholder?: string
    format?: string
    valueFormat?: string
    type?: 'date' | 'datetime' | 'daterange'
    clearable?: boolean
    disabled?: boolean
  }
  
  export interface UploadFieldProps {
    action: string
    accept?: string
    maxSize?: number
    maxCount?: number
    multiple?: boolean
    disabled?: boolean
  }
  
  export interface CalculatedFieldProps {
    formula: string
    dependencies: string[]
    precision?: number
    readonly: true
  }