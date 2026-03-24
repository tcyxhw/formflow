import { describe, it, expect } from 'vitest'
import { FieldLabelService } from '../fieldLabelService'
import type { FormSchema } from '@/types/schema'

describe('FieldLabelService', () => {
  // 测试数据
  const mockFormSchema: FormSchema = {
    version: '1.0',
    fields: [
      {
        id: 'student_id',
        label: '学号',
        type: 'text',
        required: true
      },
      {
        id: 'amount',
        label: '报销金额',
        type: 'number',
        required: true
      },
      {
        id: 'category',
        label: '费用类别',
        type: 'select',
        required: true
      },
      {
        id: 'empty_label',
        label: '',
        type: 'text',
        required: false
      },
      {
        id: 'no_label_field',
        label: '',
        type: 'text',
        required: false
      }
    ],
    fieldOrder: ['student_id', 'amount', 'category']
  }

  describe('getFieldLabel', () => {
    it('应该正确获取字段标签', () => {
      const label = FieldLabelService.getFieldLabel('student_id', mockFormSchema)
      expect(label).toBe('学号')
    })

    it('应该为多个字段返回正确的标签', () => {
      expect(FieldLabelService.getFieldLabel('student_id', mockFormSchema)).toBe('学号')
      expect(FieldLabelService.getFieldLabel('amount', mockFormSchema)).toBe('报销金额')
      expect(FieldLabelService.getFieldLabel('category', mockFormSchema)).toBe('费用类别')
    })

    it('当标签缺失时应该返回字段键', () => {
      const label = FieldLabelService.getFieldLabel('empty_label', mockFormSchema)
      expect(label).toBe('empty_label')
    })

    it('当字段不存在时应该返回字段键', () => {
      const label = FieldLabelService.getFieldLabel('non_existent', mockFormSchema)
      expect(label).toBe('non_existent')
    })

    it('当 formSchema 为 null 时应该返回字段键', () => {
      const label = FieldLabelService.getFieldLabel('student_id', null)
      expect(label).toBe('student_id')
    })

    it('当 formSchema 为 undefined 时应该返回字段键', () => {
      const label = FieldLabelService.getFieldLabel('student_id', undefined)
      expect(label).toBe('student_id')
    })

    it('当 formSchema.fields 为空时应该返回字段键', () => {
      const emptySchema: FormSchema = {
        version: '1.0',
        fields: [],
        fieldOrder: []
      }
      const label = FieldLabelService.getFieldLabel('student_id', emptySchema)
      expect(label).toBe('student_id')
    })

    it('当 formSchema.fields 为 undefined 时应该返回字段键', () => {
      const schemaWithoutFields: FormSchema = {
        version: '1.0',
        fieldOrder: []
      } as any
      const label = FieldLabelService.getFieldLabel('student_id', schemaWithoutFields)
      expect(label).toBe('student_id')
    })
  })

  describe('getFieldLabelWithKey', () => {
    it('应该返回"标签（键）"格式', () => {
      const result = FieldLabelService.getFieldLabelWithKey('student_id', mockFormSchema)
      expect(result).toBe('学号（student_id）')
    })

    it('应该为多个字段返回正确的格式', () => {
      expect(FieldLabelService.getFieldLabelWithKey('student_id', mockFormSchema)).toBe('学号（student_id）')
      expect(FieldLabelService.getFieldLabelWithKey('amount', mockFormSchema)).toBe('报销金额（amount）')
      expect(FieldLabelService.getFieldLabelWithKey('category', mockFormSchema)).toBe('费用类别（category）')
    })

    it('当标签缺失时应该只返回字段键', () => {
      const result = FieldLabelService.getFieldLabelWithKey('empty_label', mockFormSchema)
      expect(result).toBe('empty_label')
    })

    it('当字段不存在时应该只返回字段键', () => {
      const result = FieldLabelService.getFieldLabelWithKey('non_existent', mockFormSchema)
      expect(result).toBe('non_existent')
    })

    it('当 formSchema 为 null 时应该只返回字段键', () => {
      const result = FieldLabelService.getFieldLabelWithKey('student_id', null)
      expect(result).toBe('student_id')
    })
  })

  describe('getFieldLabelMap', () => {
    it('应该返回所有字段的标签映射', () => {
      const map = FieldLabelService.getFieldLabelMap(mockFormSchema)
      expect(map).toEqual({
        'student_id': '学号',
        'amount': '报销金额',
        'category': '费用类别',
        'empty_label': 'empty_label',
        'no_label_field': 'no_label_field'
      })
    })

    it('应该为空 Schema 返回空对象', () => {
      const map = FieldLabelService.getFieldLabelMap(null)
      expect(map).toEqual({})
    })

    it('应该为 undefined Schema 返回空对象', () => {
      const map = FieldLabelService.getFieldLabelMap(undefined)
      expect(map).toEqual({})
    })

    it('应该为空字段列表返回空对象', () => {
      const emptySchema: FormSchema = {
        version: '1.0',
        fields: [],
        fieldOrder: []
      }
      const map = FieldLabelService.getFieldLabelMap(emptySchema)
      expect(map).toEqual({})
    })

    it('应该处理标签缺失的字段', () => {
      const map = FieldLabelService.getFieldLabelMap(mockFormSchema)
      expect(map['empty_label']).toBe('empty_label')
      expect(map['no_label_field']).toBe('no_label_field')
    })

    it('应该支持多字段的标签映射', () => {
      const map = FieldLabelService.getFieldLabelMap(mockFormSchema)
      expect(Object.keys(map).length).toBe(5)
      expect(Object.values(map).every(v => typeof v === 'string')).toBe(true)
    })
  })

  describe('getFieldDefinition', () => {
    it('应该返回字段的完整定义', () => {
      const definition = FieldLabelService.getFieldDefinition('student_id', mockFormSchema)
      expect(definition).not.toBeNull()
      expect(definition?.key).toBe('student_id')
      expect(definition?.label).toBe('学号')
      expect(definition?.type).toBe('text')
    })

    it('应该为多个字段返回正确的定义', () => {
      const def1 = FieldLabelService.getFieldDefinition('student_id', mockFormSchema)
      const def2 = FieldLabelService.getFieldDefinition('amount', mockFormSchema)
      
      expect(def1?.label).toBe('学号')
      expect(def2?.label).toBe('报销金额')
    })

    it('当字段不存在时应该返回 null', () => {
      const definition = FieldLabelService.getFieldDefinition('non_existent', mockFormSchema)
      expect(definition).toBeNull()
    })

    it('当 formSchema 为 null 时应该返回 null', () => {
      const definition = FieldLabelService.getFieldDefinition('student_id', null)
      expect(definition).toBeNull()
    })

    it('当 formSchema 为 undefined 时应该返回 null', () => {
      const definition = FieldLabelService.getFieldDefinition('student_id', undefined)
      expect(definition).toBeNull()
    })

    it('应该包含所有字段属性', () => {
      const definition = FieldLabelService.getFieldDefinition('student_id', mockFormSchema)
      expect(definition).toHaveProperty('key')
      expect(definition).toHaveProperty('label')
      expect(definition).toHaveProperty('type')
      expect(definition).toHaveProperty('required')
    })
  })

  describe('getFieldList', () => {
    it('应该返回所有字段的列表', () => {
      const list = FieldLabelService.getFieldList(mockFormSchema)
      expect(list.length).toBe(5)
      expect(list[0].key).toBe('student_id')
      expect(list[0].label).toBe('学号')
    })

    it('应该为空 Schema 返回空列表', () => {
      const list = FieldLabelService.getFieldList(null)
      expect(list).toEqual([])
    })

    it('应该为 undefined Schema 返回空列表', () => {
      const list = FieldLabelService.getFieldList(undefined)
      expect(list).toEqual([])
    })

    it('应该为空字段列表返回空列表', () => {
      const emptySchema: FormSchema = {
        version: '1.0',
        fields: [],
        fieldOrder: []
      }
      const list = FieldLabelService.getFieldList(emptySchema)
      expect(list).toEqual([])
    })

    it('应该包含所有字段的完整定义', () => {
      const list = FieldLabelService.getFieldList(mockFormSchema)
      list.forEach(field => {
        expect(field).toHaveProperty('key')
        expect(field).toHaveProperty('label')
        expect(field).toHaveProperty('type')
      })
    })
  })

  describe('hasField', () => {
    it('应该检查字段是否存在', () => {
      expect(FieldLabelService.hasField('student_id', mockFormSchema)).toBe(true)
      expect(FieldLabelService.hasField('amount', mockFormSchema)).toBe(true)
    })

    it('应该检查不存在的字段', () => {
      expect(FieldLabelService.hasField('non_existent', mockFormSchema)).toBe(false)
    })

    it('当 formSchema 为 null 时应该返回 false', () => {
      expect(FieldLabelService.hasField('student_id', null)).toBe(false)
    })

    it('当 formSchema 为 undefined 时应该返回 false', () => {
      expect(FieldLabelService.hasField('student_id', undefined)).toBe(false)
    })

    it('应该检查多个字段', () => {
      const fields = ['student_id', 'amount', 'category', 'non_existent']
      const results = fields.map(f => FieldLabelService.hasField(f, mockFormSchema))
      expect(results).toEqual([true, true, true, false])
    })
  })

  describe('边界情况', () => {
    it('应该处理空字符串字段键', () => {
      const label = FieldLabelService.getFieldLabel('', mockFormSchema)
      // 空字符串字段键不会匹配任何字段，所以返回空字符串本身
      expect(label).toBe('')
    })

    it('应该处理特殊字符的字段键', () => {
      const specialSchema: FormSchema = {
        version: '1.0',
        fields: [
          {
            id: 'field-with-dash',
            label: '带破折号的字段',
            type: 'text',
            required: false
          },
          {
            id: 'field_with_underscore',
            label: '带下划线的字段',
            type: 'text',
            required: false
          }
        ],
        fieldOrder: []
      }
      
      expect(FieldLabelService.getFieldLabel('field-with-dash', specialSchema)).toBe('带破折号的字段')
      expect(FieldLabelService.getFieldLabel('field_with_underscore', specialSchema)).toBe('带下划线的字段')
    })

    it('应该处理长标签', () => {
      const longSchema: FormSchema = {
        version: '1.0',
        fields: [
          {
            id: 'long_field',
            label: '这是一个非常长的字段标签，用来测试系统是否能够正确处理长标签',
            type: 'text',
            required: false
          }
        ],
        fieldOrder: []
      }
      
      const label = FieldLabelService.getFieldLabel('long_field', longSchema)
      expect(label).toBe('这是一个非常长的字段标签，用来测试系统是否能够正确处理长标签')
    })

    it('应该处理中文字段键', () => {
      const chineseSchema: FormSchema = {
        version: '1.0',
        fields: [
          {
            id: '学号',
            label: '学生学号',
            type: 'text',
            required: false
          }
        ],
        fieldOrder: []
      }
      
      const label = FieldLabelService.getFieldLabel('学号', chineseSchema)
      expect(label).toBe('学生学号')
    })

    it('应该处理重复的字段键', () => {
      const duplicateSchema: FormSchema = {
        version: '1.0',
        fields: [
          {
            id: 'student_id',
            label: '学号1',
            type: 'text',
            required: false
          },
          {
            id: 'student_id',
            label: '学号2',
            type: 'text',
            required: false
          }
        ],
        fieldOrder: []
      }
      
      // 应该返回第一个匹配的字段
      const label = FieldLabelService.getFieldLabel('student_id', duplicateSchema)
      expect(label).toBe('学号1')
    })
  })

  describe('集成测试', () => {
    it('应该支持完整的字段标签工作流', () => {
      // 1. 获取字段列表
      const fieldList = FieldLabelService.getFieldList(mockFormSchema)
      expect(fieldList.length).toBeGreaterThan(0)

      // 2. 获取字段标签映射
      const labelMap = FieldLabelService.getFieldLabelMap(mockFormSchema)
      expect(Object.keys(labelMap).length).toBe(fieldList.length)

      // 3. 验证每个字段的标签
      fieldList.forEach(field => {
        const label = FieldLabelService.getFieldLabel(field.key, mockFormSchema)
        expect(label).toBe(labelMap[field.key])
      })

      // 4. 验证字段定义
      fieldList.forEach(field => {
        const definition = FieldLabelService.getFieldDefinition(field.key, mockFormSchema)
        expect(definition).not.toBeNull()
        expect(definition?.key).toBe(field.key)
      })
    })

    it('应该支持条件构建中的字段标签查询', () => {
      // 模拟条件构建中的字段查询
      const fieldKeys = ['student_id', 'amount', 'category']
      const labels = fieldKeys.map(key => FieldLabelService.getFieldLabel(key, mockFormSchema))
      
      expect(labels).toEqual(['学号', '报销金额', '费用类别'])
    })

    it('应该支持字段标签的批量查询', () => {
      const labelMap = FieldLabelService.getFieldLabelMap(mockFormSchema)
      const fieldKeys = ['student_id', 'amount', 'category']
      
      const labels = fieldKeys.map(key => labelMap[key] || key)
      expect(labels).toEqual(['学号', '报销金额', '费用类别'])
    })
  })
})
