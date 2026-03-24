/**
 * 字段标签映射服务
 * 
 * 职责：
 * - 从表单 Schema 中提取字段标签
 * - 提供字段键到标签的映射
 * - 处理标签缺失的情况
 */

import type { FormSchema } from '@/types/schema'

/**
 * 字段定义接口
 */
export interface FieldDefinition {
  key: string
  label: string
  type?: string
  [key: string]: any
}

/**
 * 字段标签映射服务
 */
export class FieldLabelService {
  /**
   * 获取字段标签
   * 
   * 从表单 Schema 中查找指定字段，返回其标签。
   * 如果字段不存在或标签为空，则返回字段键作为备选。
   * 
   * @param fieldKey 字段键（可能是 key 或 id）
   * @param formSchema 表单 Schema
   * @returns 字段标签，如果不存在则返回字段键
   */
  static getFieldLabel(fieldKey: string, formSchema: FormSchema | null | undefined): string {
    if (!formSchema || !formSchema.fields) {
      return fieldKey
    }

    // 优先按 id 匹配（前端 FormField 类型期望的结构）
    let field = formSchema.fields.find(f => f.id === fieldKey)
    
    // 如果按 id 没找到，尝试按 key 匹配（兼容后端 API 返回的字段结构）
    if (!field) {
      field = formSchema.fields.find((f: any) => f.key === fieldKey)
    }
    
    if (!field) {
      return fieldKey
    }

    // 优先使用 label，如果为空则使用 id/key
    return field.label || field.id || (field as any).key || fieldKey
  }

  /**
   * 获取字段标签和键的组合显示
   * 
   * 返回"标签（键）"格式的字符串，帮助用户识别字段。
   * 如果标签和键相同，则只返回标签。
   * 
   * @param fieldKey 字段键
   * @param formSchema 表单 Schema
   * @returns 格式为 "标签（键）" 的字符串
   */
  static getFieldLabelWithKey(fieldKey: string, formSchema: FormSchema | null | undefined): string {
    const label = this.getFieldLabel(fieldKey, formSchema)
    
    // 如果标签和键相同，只返回标签
    if (label === fieldKey) {
      return fieldKey
    }
    
    return `${label}（${fieldKey}）`
  }

  /**
   * 获取所有字段的标签映射
   * 
   * 返回一个对象，其中键是字段键，值是字段标签。
   * 用于批量获取字段标签映射，提高性能。
   * 
   * @param formSchema 表单 Schema
   * @returns 字段键到标签的映射对象
   */
  static getFieldLabelMap(formSchema: FormSchema | null | undefined): Record<string, string> {
    const map: Record<string, string> = {}
    
    if (!formSchema || !formSchema.fields) {
      return map
    }

    formSchema.fields.forEach(field => {
      const key = field.id || ''
      const label = field.label || key
      map[key] = label
    })

    return map
  }

  /**
   * 获取字段定义
   * 
   * 从表单 Schema 中查找指定字段的完整定义。
   * 
   * @param fieldKey 字段键
   * @param formSchema 表单 Schema
   * @returns 字段定义对象，如果不存在则返回 null
   */
  static getFieldDefinition(fieldKey: string, formSchema: FormSchema | null | undefined): FieldDefinition | null {
    if (!formSchema || !formSchema.fields) {
      return null
    }

    const field = formSchema.fields.find(f => f.id === fieldKey)
    
    if (!field) {
      return null
    }

    return {
      key: field.id || '',
      label: field.label || field.id || '',
      type: field.type,
      required: field.required,
      description: field.description,
      defaultValue: field.defaultValue,
      props: field.props,
      validation: field.validation
    }
  }

  /**
   * 获取字段列表
   * 
   * 返回表单中所有字段的列表。
   * 
   * @param formSchema 表单 Schema
   * @returns 字段定义列表
   */
  static getFieldList(formSchema: FormSchema | null | undefined): FieldDefinition[] {
    if (!formSchema || !formSchema.fields) {
      return []
    }

    return formSchema.fields.map(field => ({
      key: field.id || '',
      label: field.label || field.id || '',
      type: field.type,
      required: field.required,
      description: field.description,
      defaultValue: field.defaultValue,
      props: field.props,
      validation: field.validation
    }))
  }

  /**
   * 检查字段是否存在
   * 
   * @param fieldKey 字段键
   * @param formSchema 表单 Schema
   * @returns 字段是否存在
   */
  static hasField(fieldKey: string, formSchema: FormSchema | null | undefined): boolean {
    if (!formSchema || !formSchema.fields) {
      return false
    }

    return formSchema.fields.some(f => f.id === fieldKey)
  }
}

export default FieldLabelService
