/**
 * 表单验证（与后端保持一致）
 */
import type { FormConfig } from '@/types/form'
import type { FormSchema } from '@/types/schema'
import type { LogicSchema } from '@/types/logic'
import type { FormField } from '@/types/field'

export class FormValidation {
  /**
   * 验证表单配置（发布前）
   */
  static validateFormConfig(config: FormConfig): string[] {
    const errors: string[] = []
    
    // 1. 基础信息验证
    if (!config.name || config.name.trim() === '') {
      errors.push('表单名称不能为空')
    }
    
    // 2. Schema验证
    const schemaErrors = this.validateSchema(config.formSchema)
    errors.push(...schemaErrors)
    
    // 3. Logic验证
    const logicErrors = this.validateLogic(config.logicSchema, config.formSchema)
    errors.push(...logicErrors)
    
    return errors
  }
  
  /**
   * 验证Schema（与后端 _validate_schema 保持一致）
   */
  static validateSchema(schema: FormSchema): string[] {
    const errors: string[] = []
    
    if (!schema.fields || schema.fields.length === 0) {
      errors.push('表单至少需要一个字段')
      return errors
    }
    
    const fieldIds = new Set<string>()
    
    schema.fields.forEach((field, index) => {
      // 必填属性检查
      if (!field.id) {
        errors.push(`第${index + 1}个字段缺少ID`)
      } else if (fieldIds.has(field.id)) {
        errors.push(`字段ID重复: ${field.id}`)
      } else {
        fieldIds.add(field.id)
      }
      
      if (!field.type) {
        errors.push(`字段 ${field.id} 缺少类型`)
      }
      
      if (!field.label) {
        errors.push(`字段 ${field.id} 缺少标签`)
      }
      
      // 选择类字段必须有选项
      if (['select', 'radio', 'checkbox'].includes(field.type)) {
        if (!field.props.options || field.props.options.length === 0) {
          errors.push(`字段 ${field.id} 缺少选项配置`)
        }
      }
      
      // 计算字段必须有公式
      if (field.type === 'calculated') {
        if (!field.props.formula) {
          errors.push(`计算字段 ${field.id} 缺少公式`)
        }
        if (!field.props.dependencies || field.props.dependencies.length === 0) {
          errors.push(`计算字段 ${field.id} 缺少依赖字段`)
        }
      }
    })
    
    // 计算字段循环依赖检查
    const calcFields = schema.fields.filter(f => f.type === 'calculated')
    if (calcFields.length > 0 && this.hasCircularDependency(schema.fields)) {
      errors.push('检测到计算字段循环依赖')
    }
    
    return errors
  }
  
  /**
   * 验证Logic
   */
  static validateLogic(logic: LogicSchema, schema: FormSchema): string[] {
    const errors: string[] = []
    const fieldIds = new Set(schema.fields.map(f => f.id))
    
    logic.rules.forEach(rule => {
      // 触发字段存在性检查
      rule.trigger.fields.forEach(fieldId => {
        if (!fieldIds.has(fieldId)) {
          errors.push(`规则 ${rule.id} 引用了不存在的触发字段: ${fieldId}`)
        }
      })
      
      // 条件字段存在性检查
      rule.conditions.forEach(condition => {
        if (!fieldIds.has(condition.field)) {
          errors.push(`规则 ${rule.id} 引用了不存在的条件字段: ${condition.field}`)
        }
      })
      
      // 动作目标字段存在性检查
      rule.actions.forEach(action => {
        if (action.target && !fieldIds.has(action.target)) {
          errors.push(`规则 ${rule.id} 引用了不存在的目标字段: ${action.target}`)
        }
      })
    })
    
    return errors
  }
  
  /**
   * 检查循环依赖（与后端 check_circular_dependency 保持一致）
   */
  static hasCircularDependency(fields: FormField[]): boolean {
    // 构建依赖图
    const graph = new Map<string, string[]>()
    
    fields.forEach(field => {
      if (field.type === 'calculated') {
        const deps = this.extractDependencies(field.props.formula || '')
        graph.set(field.id, deps)
      }
    })
    
    // DFS检测环
    const visited = new Set<string>()
    const recStack = new Set<string>()
    
    const hasCycle = (node: string): boolean => {
      visited.add(node)
      recStack.add(node)
      
      const deps = graph.get(node) || []
      for (const dep of deps) {
        if (!visited.has(dep)) {
          if (hasCycle(dep)) return true
        } else if (recStack.has(dep)) {
          return true
        }
      }
      
      recStack.delete(node)
      return false
    }
    
    for (const node of graph.keys()) {
      if (!visited.has(node)) {
        if (hasCycle(node)) return true
      }
    }
    
    return false
  }
  
  /**
   * 提取公式中的依赖字段（与后端 extract_dependencies 保持一致）
   */
  private static extractDependencies(formula: string): string[] {
    const pattern = /\$\{(\w+)\}/g
    const matches = formula.matchAll(pattern)
    return Array.from(matches, m => m[1])
  }
}