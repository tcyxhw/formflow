/**
 * Schema定义
 */
import type { FormField } from './field'

export interface FormSchema {
  version: string
  fields: FormField[]
  fieldOrder?: string[]
}

export interface UISchema {
  layout: LayoutConfig
  rows?: RowConfig[]
  groups?: GroupConfig[]
  theme?: ThemeConfig
}

export interface LayoutConfig {
  type: 'vertical' | 'horizontal' | 'grid'
  columns?: number
  gutter?: number
  labelWidth?: string | number
  labelPosition?: 'left' | 'top' | 'right'
  size?: 'small' | 'medium' | 'large'
}

export interface RowConfig {
  fields: FieldInRow[]
  gutter?: number
}

export interface FieldInRow {
  id: string
  span?: number
  offset?: number
}

export interface GroupConfig {
  id: string
  title: string
  description?: string
  fields: string[]
  collapsed?: boolean
  collapsible?: boolean
}

export interface ThemeConfig {
  primaryColor?: string
}